from __future__ import annotations

from pathlib import Path

from certifai.decorators import certifai
from certifai.policy import EnforcementSettings, PolicyConfig, load_policy


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:46.249248+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.538630+00:00 digest=479c655323df41ec33e2891fdf5b16a2d7e2b86c last_commit=f07d0d9 by phzwart",
    ],
)
def test_load_policy_defaults_when_missing(tmp_path: Path) -> None:
    policy = load_policy(tmp_path / ".certifai.yml")
    assert isinstance(policy, PolicyConfig)
    assert policy.enforcement.ai_composed_requires_high_scrutiny is True
    assert policy.enforcement.min_coverage is None


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:46.249248+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.538630+00:00 digest=479c655323df41ec33e2891fdf5b16a2d7e2b86c last_commit=f07d0d9 by phzwart",
    ],
)
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
