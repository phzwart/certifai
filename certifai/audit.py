"""Audit logging utilities for certifai."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

from .models import CodeArtifact
from .policy import AuditSettings
from .utils.logging import get_logger

LOGGER = get_logger("audit")

DEFAULT_LOG_PATH = Path(".certifai/audit.log")


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
