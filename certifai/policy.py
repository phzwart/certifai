"""Policy configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import yaml


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.083842+00:00 digest=57c5300e54f8f166dbcbe1aa80bb211aa2c21b19 last_commit=f07d0d9 by phzwart

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
class PolicyConfig:
    """Aggregate policy metadata loaded from configuration files."""

    enforcement: EnforcementSettings
    reviewers: Sequence[str]


DEFAULT_POLICY = PolicyConfig(
    enforcement=EnforcementSettings(),
    reviewers=(),
)


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: high
# date: 2025-11-08T01:38:57.409525+00:00
# notes: manual review
# history: 2025-11-08T01:38:57.409525+00:00 digest=249d45b5886b94ad9a37051834d8f85cc1009b22 certified by PHZ (high) last_commit=f07d0d9 by phzwart

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


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: bulk annotation
# history: 2025-11-08T01:22:48.083842+00:00 digest=e125446715dae94eee3b0548947172a586fcc8a8 last_commit=f07d0d9 by phzwart

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


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.623785+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.083842+00:00 digest=57c5300e54f8f166dbcbe1aa80bb211aa2c21b19 last_commit=f07d0d9 by phzwart

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
