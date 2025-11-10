"""Audit logging utilities for certifai."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, TypedDict, Literal, cast

from .models import CodeArtifact
from .policy import AuditSettings, load_policy
from .utils.logging import get_logger

LOGGER = get_logger("audit")

DEFAULT_LOG_PATH = Path(".certifai/audit.log")
_SEVERITY_ORDER: Dict[str, int] = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


class Finding(TypedDict, total=False):
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: str
    message: str
    line: int | None
    suggestion: str | None
    reference: str | None


class FindingsSummary(TypedDict, total=False):
    total_issues: int
    critical: int
    high: int
    medium: int
    low: int
    info: int


@dataclass(slots=True)
class AuditRecord:
    timestamp: str
    action: str
    data: dict[str, object]


def _log_path(settings: AuditSettings, override: Path | None = None) -> Path:
    if override is not None:
        return override
    if settings.log_path:
        return Path(settings.log_path)
    return DEFAULT_LOG_PATH


def _write_records(settings: AuditSettings, records: Iterable[AuditRecord], override: Path | None = None) -> None:
    if not settings.enabled:
        return
    path = _log_path(settings, override)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps({
                "timestamp": record.timestamp,
                "action": record.action,
                "data": record.data,
            }) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _summarize_findings(findings: Sequence[dict[str, Any]]) -> FindingsSummary:
    summary: Dict[str, int] = {
        "total_issues": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    for finding in findings:
        summary["total_issues"] += 1
        severity = str(finding.get("severity", "info")).lower()
        if severity in summary:
            summary[severity] += 1
    return cast(FindingsSummary, {key: value for key, value in summary.items() if value})


class Audit:
    """Structured interface for reading and writing audit log data."""

    def __init__(
        self,
        settings: AuditSettings,
        *,
        registry_root: Path | None = None,
        override_path: Path | None = None,
    ) -> None:
        self.settings = settings
        self._registry_root = Path(registry_root) if registry_root else None
        self._override_path = self._resolve_override(override_path)

    def _resolve_override(self, override: Path | None) -> Path | None:
        if override is not None:
            return override
        if self._registry_root is None:
            return None
        if self.settings.log_path:
            configured = Path(self.settings.log_path)
            if configured.is_absolute():
                return configured
            return self._registry_root / configured
        return self._registry_root / DEFAULT_LOG_PATH

    @property
    def enabled(self) -> bool:
        return self.settings.enabled

    @property
    def log_path(self) -> Path:
        return _log_path(self.settings, override=self._override_path)

    @classmethod
    def load(
        cls,
        registry_root: Path | None = None,
        *,
        policy_path: Path | None = None,
    ) -> "Audit":
        policy_config = load_policy(policy_path)
        configured = policy_config.integrations.audit

        if configured.enabled and configured.log_path is not None:
            settings = configured
        elif configured.enabled:
            settings = AuditSettings(
                enabled=True,
                log_path=str(DEFAULT_LOG_PATH),
                dashboard_url=configured.dashboard_url,
            )
        else:
            settings = AuditSettings(
                enabled=True,
                log_path=configured.log_path or str(DEFAULT_LOG_PATH),
                dashboard_url=configured.dashboard_url,
            )

        return cls(
            settings,
            registry_root=registry_root,
        )

    @classmethod
    def from_settings(
        cls,
        settings: AuditSettings,
        *,
        registry_root: Path | None = None,
    ) -> "Audit":
        return cls(settings, registry_root=registry_root)

    def record_review(
        self,
        agent_id: str,
        artifact: str,
        filepath: str,
        result: Literal["clean", "issues_found", "error"],
        *,
        findings: Sequence[Finding] | None = None,
        summary: FindingsSummary | None = None,
        override: Path | None = None,
        **metadata: Any,
    ) -> None:
        if not self.settings.enabled:
            return

        findings_payload: list[dict[str, Any]] | None = None
        if findings:
            findings_payload = [dict(item) for item in findings]

        summary_payload: FindingsSummary | None = None
        if summary is not None:
            summary_payload = cast(FindingsSummary, dict(summary))
        elif findings_payload:
            summary_payload = _summarize_findings(findings_payload)

        payload: Dict[str, Any] = {
            "agent": agent_id,
            "artifact": artifact,
            "filepath": filepath,
            "result": result,
        }
        if metadata:
            payload.update(metadata)
        if findings_payload:
            payload["findings"] = findings_payload
        if summary_payload:
            payload["summary"] = summary_payload

        record = AuditRecord(
            timestamp=_now_iso(),
            action="agent_review",
            data=payload,
        )
        _write_records(self.settings, [record], override or self._override_path)

    def _read_records(self) -> List[dict[str, Any]]:
        return read_audit_log(self.settings, override=self._override_path)

    def get_findings(
        self,
        *,
        artifact: str | None = None,
        filepath: str | None = None,
        severity: str | None = None,
        since_days: int = 30,
    ) -> List[dict[str, Any]]:
        entries = self._read_records()
        if not entries:
            return []

        minimum_threshold: int | None = None
        if severity:
            minimum_threshold = _SEVERITY_ORDER.get(severity.lower())

        cutoff: datetime | None = None
        if since_days >= 0:
            cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

        findings: list[dict[str, Any]] = []
        for entry in entries:
            if entry.get("action") != "agent_review":
                continue
            timestamp = entry.get("timestamp")
            parsed_ts = _parse_timestamp(timestamp)
            if cutoff and parsed_ts and parsed_ts < cutoff:
                continue
            data = entry.get("data") or {}
            if artifact and data.get("artifact") != artifact:
                continue
            if filepath and data.get("filepath") != filepath:
                continue

            for finding in data.get("findings") or []:
                if not isinstance(finding, dict):
                    continue
                severity_value = _SEVERITY_ORDER.get(
                    str(finding.get("severity", "info")).lower(), 0
                )
                if minimum_threshold is not None and severity_value < minimum_threshold:
                    continue
                findings.append(
                    {
                        "timestamp": timestamp,
                        "agent": data.get("agent"),
                        "artifact": data.get("artifact"),
                        "filepath": data.get("filepath"),
                        "result": data.get("result"),
                        "finding": finding,
                    }
                )
        return findings

    def get_latest_review(self, artifact: str) -> dict[str, Any] | None:
        entries = self._read_records()
        for entry in reversed(entries):
            if entry.get("action") != "agent_review":
                continue
            data = entry.get("data") or {}
            if data.get("artifact") == artifact:
                return entry
        return None

    def has_blocking_issues(
        self,
        artifact: str,
        *,
        min_severity: Literal["critical", "high", "medium"] = "high",
    ) -> bool:
        threshold = _SEVERITY_ORDER[min_severity]
        latest = self.get_latest_review(artifact)
        if latest is None:
            return False
        data = latest.get("data") or {}
        for finding in data.get("findings") or []:
            if not isinstance(finding, dict):
                continue
            severity_value = _SEVERITY_ORDER.get(
                str(finding.get("severity", "info")).lower(), 0
            )
            if severity_value >= threshold:
                return True
        summary = data.get("summary")
        if isinstance(summary, dict):
            for key, amount in summary.items():
                if key == "total_issues":
                    continue
                if _SEVERITY_ORDER.get(str(key).lower(), 0) >= threshold and isinstance(amount, int) and amount > 0:
                    return True
        return False


def record_certification(settings: AuditSettings, artifacts: Iterable[CodeArtifact], reviewer: str, notes: str | None, reviewer_kind: str = "human", override: Path | None = None) -> None:
    records = []
    for artifact in artifacts:
        records.append(AuditRecord(
            timestamp=_now_iso(),
            action="certify",
            data={
                "artifact": artifact.name,
                "filepath": str(artifact.filepath),
                "reviewer": reviewer,
                "kind": reviewer_kind,
                "scrutiny": artifact.tags.scrutiny.value if artifact.tags.scrutiny else None,
                "notes": notes,
                "ai_composed": artifact.tags.ai_composed,
            },
        ))
    _write_records(settings, records, override)


def record_agent_certification(settings: AuditSettings, artifacts: Iterable[CodeArtifact], agent_id: str, notes: str | None, override: Path | None = None) -> None:
    records = []
    for artifact in artifacts:
        records.append(AuditRecord(
            timestamp=_now_iso(),
            action="agent-certify",
            data={
                "artifact": artifact.name,
                "filepath": str(artifact.filepath),
                "agent": agent_id,
                "scrutiny": artifact.tags.scrutiny.value if artifact.tags.scrutiny else None,
                "notes": notes,
                "ai_composed": artifact.tags.ai_composed,
            },
        ))
    _write_records(settings, records, override)


def record_finalization(settings: AuditSettings, artifacts: Iterable[CodeArtifact], override: Path | None = None) -> None:
    records = []
    for artifact in artifacts:
        records.append(AuditRecord(
            timestamp=_now_iso(),
            action="finalize",
            data={
                "artifact": artifact.name,
                "filepath": str(artifact.filepath),
                "human_certified": artifact.tags.human_certified,
                "ai_composed": artifact.tags.ai_composed,
            },
        ))
    _write_records(settings, records, override)


def record_enforcement(settings: AuditSettings, status: str, messages: list[str], override: Path | None = None) -> None:
    record = AuditRecord(
        timestamp=_now_iso(),
        action="enforce",
        data={
            "status": status,
            "messages": messages,
        },
    )
    _write_records(settings, [record], override)


def read_audit_log(settings: AuditSettings, limit: Optional[int] = None, override: Path | None = None) -> List[dict[str, object]]:
    path = _log_path(settings, override)
    if not path.exists():
        return []
    entries: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    if limit is not None and limit >= 0:
        lines = lines[-limit:]
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            LOGGER.warning("Skipping malformed audit log line: %s", line)
    return entries


def record_reopening(
    settings: AuditSettings,
    artifact: CodeArtifact,
    reason: str,
    *,
    old_digest: str | None = None,
    new_digest: str | None = None,
    override: Path | None = None,
) -> None:
    """Record that a finalized artifact has been reopened for review."""

    record_data: dict[str, object] = {
        "artifact": artifact.name,
        "filepath": str(artifact.filepath),
        "reason": reason,
        "ai_composed": artifact.tags.ai_composed,
    }
    if old_digest:
        record_data["old_digest"] = old_digest
    if new_digest:
        record_data["new_digest"] = new_digest

    record = AuditRecord(
        timestamp=_now_iso(),
        action="reopen",
        data=record_data,
    )
    _write_records(settings, [record], override)
