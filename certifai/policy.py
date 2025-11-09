"""Policy configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence, Tuple, Iterable, Mapping

import yaml

from .decorators import certifai
from .models import ScrutinyLevel

@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.623785+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.083842+00:00 digest=57c5300e54f8f166dbcbe1aa80bb211aa2c21b19 last_commit=f07d0d9 by phzwart",
    ],
)
@dataclass(slots=True)
class EnforcementSettings:
    """Configuration flags controlling code certification policies."""

    ai_composed_requires_high_scrutiny: bool = True
    min_coverage: float | None = None
    ignore_unannotated: bool = False


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: bulk annotation
# history: 2025-11-08T01:22:48.083842+00:00 digest=e125446715dae94eee3b0548947172a586fcc8a8 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class PRBotSettings:
    enabled: bool = False
    platforms: Tuple[str, ...] = ()
    reviewer_groups: Tuple[str, ...] = ()
    status_check: str | None = None
    agents_allowed: Tuple[str, ...] = ()


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: bulk annotation
# history: 2025-11-08T01:22:48.083842+00:00 digest=e125446715dae94eee3b0548947172a586fcc8a8 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class AgentPolicy:
    id: str
    allow_risks: Tuple[str, ...] = ()
    max_scrutiny: ScrutinyLevel | None = None
    require_human_followup: bool = False


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: bulk annotation
# history: 2025-11-08T01:22:48.083842+00:00 digest=e125446715dae94eee3b0548947172a586fcc8a8 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class SecurityScannerConfig:
    name: str
    command: str


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.083842+00:00 digest=57c5300e54f8f166dbcbe1aa80bb211aa2c21b19 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class SecurityScannerSettings:
    enabled: bool = False
    scanners: Tuple[SecurityScannerConfig, ...] = ()


@dataclass(slots=True)
class PublishingDestination:
    type: str
    path: str | None = None
    branch: str | None = None
    url: str | None = None


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: bulk annotation
# history: 2025-11-08T01:22:48.083842+00:00 digest=e125446715dae94eee3b0548947172a586fcc8a8 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class PublishingSettings:
    enabled: bool = False
    destinations: Tuple[PublishingDestination, ...] = ()


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.083842+00:00 digest=57c5300e54f8f166dbcbe1aa80bb211aa2c21b19 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class CIEnforcementSettings:
    enabled: bool = False
    min_coverage: float | None = None
    require_human_review: bool = True
    fail_on_vulnerabilities: str | None = None


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: bulk annotation
# history: 2025-11-08T01:22:48.083842+00:00 digest=e125446715dae94eee3b0548947172a586fcc8a8 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class AuditSettings:
    enabled: bool = False
    log_path: str | None = None
    dashboard_url: str | None = None


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.083842+00:00 digest=57c5300e54f8f166dbcbe1aa80bb211aa2c21b19 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class AgentPermission:
    id: str
    max_scrutiny: str | None = None
    allow_finalize: bool = False
    notes: str | None = None


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.083842+00:00 digest=57c5300e54f8f166dbcbe1aa80bb211aa2c21b19 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class AgentSettings:
    enabled: bool = False
    reviewers: Tuple[AgentPermission, ...] = ()


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.083842+00:00 digest=57c5300e54f8f166dbcbe1aa80bb211aa2c21b19 last_commit=f07d0d9 by phzwart
@dataclass(slots=True)
class IntegrationsConfig:
    pr_bot: PRBotSettings = field(default_factory=PRBotSettings)
    security: SecurityScannerSettings = field(default_factory=SecurityScannerSettings)
    publishing: PublishingSettings = field(default_factory=PublishingSettings)
    ci: CIEnforcementSettings = field(default_factory=CIEnforcementSettings)
    audit: AuditSettings = field(default_factory=AuditSettings)
    agents: AgentSettings = field(default_factory=AgentSettings)


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="high",
    date="2025-11-08T01:38:57.409525+00:00",
    notes="manual review",
    history=[
        "2025-11-08T01:38:57.409525+00:00 digest=249d45b5886b94ad9a37051834d8f85cc1009b22 certified by PHZ (high) last_commit=f07d0d9 by phzwart",
    ],
)
@dataclass(slots=True)
class PolicyConfig:
    """Aggregate policy metadata loaded from configuration files."""

    enforcement: EnforcementSettings
    reviewers: Sequence[str]
    integrations: IntegrationsConfig


DEFAULT_POLICY = PolicyConfig(
    enforcement=EnforcementSettings(),
    reviewers=(),
    integrations=IntegrationsConfig(),
)


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.623785+00:00",
    notes="bulk annotation",
    history=[
        "2025-11-08T01:22:48.083842+00:00 digest=e125446715dae94eee3b0548947172a586fcc8a8 last_commit=f07d0d9 by phzwart",
    ],
)
def load_policy(path: Path | None = None) -> PolicyConfig:
    """Load the certifai policy configuration from disk."""

    config_path = _resolve_config_path(path)
    if config_path is None or not config_path.exists():
        return DEFAULT_POLICY

    with config_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    enforcement = _parse_enforcement(raw.get("enforcement", {}))
    reviewers = tuple(raw.get("reviewers", []) or [])
    integrations = _parse_integrations(raw.get("integrations", {}))
    return PolicyConfig(
        enforcement=enforcement,
        reviewers=reviewers,
        integrations=integrations,
    )


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.623785+00:00",
    notes="bulk annotation",
    history=[
        "2025-11-08T01:22:48.083842+00:00 digest=e125446715dae94eee3b0548947172a586fcc8a8 last_commit=f07d0d9 by phzwart",
    ],
)
def _resolve_config_path(path: Path | None) -> Path | None:
    if path is not None:
        return path
    cwd = Path.cwd()
    for candidate in (
        cwd / ".certifai.yml",
        cwd / "certifai.yml",
    ):
        if candidate.exists():
            return candidate
    return None


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.623785+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.083842+00:00 digest=57c5300e54f8f166dbcbe1aa80bb211aa2c21b19 last_commit=f07d0d9 by phzwart",
    ],
)
def _parse_enforcement(data: Any) -> EnforcementSettings:
    if not isinstance(data, dict):
        return EnforcementSettings()
    requires_high_scrutiny = bool(
        data.get("ai_composed_requires_high_scrutiny", True)
    )
    min_coverage = data.get("min_coverage")
    if min_coverage is not None:
        min_coverage = float(min_coverage)
    ignore_unannotated = bool(data.get("ignore_unannotated", False))
    return EnforcementSettings(
        ai_composed_requires_high_scrutiny=requires_high_scrutiny,
        min_coverage=min_coverage,
        ignore_unannotated=ignore_unannotated,
    )


def _parse_integrations(data: Any) -> IntegrationsConfig:
    if not isinstance(data, dict):
        return IntegrationsConfig()

    pr_bot_data = data.get("pr_bot", {})
    pr_bot = PRBotSettings(
        enabled=bool(pr_bot_data.get("enabled", False)),
        platforms=tuple(pr_bot_data.get("platforms", []) or []),
        reviewer_groups=tuple(pr_bot_data.get("reviewer_groups", []) or []),
        status_check=pr_bot_data.get("status_check"),
        agents_allowed=tuple(pr_bot_data.get("agents_allowed", []) or []),
    )

    security_data = data.get("security_scanners", {})
    scanner_items = []
    for item in security_data.get("commands", []) or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        command = str(item.get("run", "")).strip()
        if name and command:
            scanner_items.append(SecurityScannerConfig(name=name, command=command))
    security = SecurityScannerSettings(
        enabled=bool(security_data.get("enabled", bool(scanner_items))),
        scanners=tuple(scanner_items),
    )

    publishing_data = data.get("publishing", {})
    destination_items = []
    for item in publishing_data.get("destinations", []) or []:
        if not isinstance(item, dict):
            continue
        dest_type = str(item.get("type", "")).strip()
        if not dest_type:
            continue
        destination_items.append(
            PublishingDestination(
                type=dest_type,
                path=item.get("path"),
                branch=item.get("branch"),
                url=item.get("url"),
            )
        )
    publishing = PublishingSettings(
        enabled=bool(publishing_data.get("enabled", bool(destination_items))),
        destinations=tuple(destination_items),
    )

    ci_data = data.get("ci", {})
    ci_min_cov = ci_data.get("min_coverage")
    if ci_min_cov is not None:
        try:
            ci_min_cov = float(ci_min_cov)
        except (TypeError, ValueError):
            ci_min_cov = None
    ci = CIEnforcementSettings(
        enabled=bool(ci_data.get("enabled", False)),
        min_coverage=ci_min_cov,
        require_human_review=bool(ci_data.get("require_human_review", True)),
        fail_on_vulnerabilities=ci_data.get("fail_on_vulnerabilities"),
    )

    audit_data = data.get("audit", {})
    audit = AuditSettings(
        enabled=bool(audit_data.get("enabled", False)),
        log_path=audit_data.get("log_path"),
        dashboard_url=audit_data.get("dashboard_url"),
    )

    agents_data = data.get("agents", {})
    agent_permissions: list[AgentPermission] = []
    for item in agents_data.get("reviewers", []) or []:
        if not isinstance(item, dict):
            continue
        agent_id = str(item.get("id", "")).strip()
        if not agent_id:
            continue
        agent_permissions.append(
            AgentPermission(
                id=agent_id,
                max_scrutiny=str(item.get("max_scrutiny")) if item.get("max_scrutiny") else None,
                allow_finalize=bool(item.get("allow_finalize", False)),
                notes=str(item.get("notes")) if item.get("notes") is not None else None,
            )
        )
    agents = AgentSettings(
        enabled=bool(agents_data.get("enabled", bool(agent_permissions))),
        reviewers=tuple(agent_permissions),
    )

    return IntegrationsConfig(
        pr_bot=pr_bot,
        security=security,
        publishing=publishing,
        ci=ci,
        audit=audit,
        agents=agents,
    )


def _parse_agents(source: Any) -> Tuple[AgentPolicy, ...]:
    if not isinstance(source, list):
        return ()
    agents: list[AgentPolicy] = []
    for item in source:
        if not isinstance(item, dict):
            continue
        agent_id = str(item.get("id", "")).strip()
        if not agent_id:
            continue
        max_scrutiny_value = item.get("max_scrutiny")
        max_scrutiny = ScrutinyLevel.from_string(max_scrutiny_value) if isinstance(max_scrutiny_value, str) else None
        allow_finalize = bool(item.get("allow_finalize", False))
        notes_required = bool(item.get("notes_required", False))
        agents.append(
            AgentPolicy(
                identifier=agent_id,
                max_scrutiny=max_scrutiny,
                allow_finalize=allow_finalize,
                notes_required=notes_required,
            )
        )
    return tuple(agents)
