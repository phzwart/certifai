"""Policy configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import yaml


@dataclass(slots=True)
class EnforcementSettings:
    """Configuration flags controlling code certification policies."""

    ai_composed_requires_high_scrutiny: bool = True
    min_coverage: float | None = None


@dataclass(slots=True)
class PolicyConfig:
    """Aggregate policy metadata loaded from configuration files."""

    enforcement: EnforcementSettings
    reviewers: Sequence[str]


DEFAULT_POLICY = PolicyConfig(
    enforcement=EnforcementSettings(),
    reviewers=(),
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
    return PolicyConfig(enforcement=enforcement, reviewers=reviewers)


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


def _parse_enforcement(data: Any) -> EnforcementSettings:
    if not isinstance(data, dict):
        return EnforcementSettings()
    requires_high_scrutiny = bool(
        data.get("ai_composed_requires_high_scrutiny", True)
    )
    min_coverage = data.get("min_coverage")
    if min_coverage is not None:
        min_coverage = float(min_coverage)
    return EnforcementSettings(
        ai_composed_requires_high_scrutiny=requires_high_scrutiny,
        min_coverage=min_coverage,
    )
