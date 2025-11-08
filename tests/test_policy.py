from __future__ import annotations

from pathlib import Path

from certifai.policy import EnforcementSettings, PolicyConfig, load_policy


def test_load_policy_defaults_when_missing(tmp_path: Path) -> None:
    policy = load_policy(tmp_path / ".certifai.yml")
    assert isinstance(policy, PolicyConfig)
    assert policy.enforcement.ai_composed_requires_high_scrutiny is True
    assert policy.enforcement.min_coverage is None


def test_load_policy_from_file(tmp_path: Path) -> None:
    config = tmp_path / ".certifai.yml"
    config.write_text(
        """
enforcement:
  ai_composed_requires_high_scrutiny: false
  min_coverage: 0.9
reviewers:
  - Mentor
  - Auditor
""".strip()
        + "\n",
        encoding="utf-8",
    )

    policy = load_policy(config)
    assert policy.enforcement.ai_composed_requires_high_scrutiny is False
    assert policy.enforcement.min_coverage == 0.9
    assert policy.reviewers == ("Mentor", "Auditor")
