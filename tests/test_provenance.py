from __future__ import annotations

from pathlib import Path

from certifai.models import ScrutinyLevel
from certifai.policy import EnforcementSettings, PolicyConfig
from certifai.provenance import annotate_paths, enforce_policy
from certifai.parser import parse_file


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.195047+00:00
# notes: bulk annotation
# history: 2025-11-08T00:34:46.195047+00:00 inserted by certifai; last_commit=f07d0d9 by phzwart

def test_annotate_paths_inserts_metadata(tmp_path: Path) -> None:
    module = tmp_path / "sample.py"
    module.write_text(
        """
def add(a, b):
    return a + b
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = annotate_paths([module], ai_agent="gpt-4", default_notes="auto")

    assert module in result.updated_files
    refreshed = parse_file(module)
    assert refreshed[0].tags.ai_composed == "gpt-4"
    assert refreshed[0].tags.human_certified == "pending"
    assert refreshed[0].tags.notes == "auto"
    assert refreshed[0].tags.history, "history entries should be recorded"


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.195047+00:00
# notes: bulk annotation
# history: 2025-11-08T00:34:46.195047+00:00 inserted by certifai; last_commit=f07d0d9 by phzwart

def test_enforce_policy_checks_scrutiny(tmp_path: Path) -> None:
    module = tmp_path / "policy_case.py"
    module.write_text(
        """
# @ai_composed: gpt-5
# @human_certified: pending
def risky():
    return 42
""".strip()
        + "\n",
        encoding="utf-8",
    )

    artifacts = parse_file(module)
    policy = PolicyConfig(
        enforcement=EnforcementSettings(ai_composed_requires_high_scrutiny=True),
        reviewers=("Reviewer",),
    )
    violations = enforce_policy(artifacts, policy)
    assert violations, "Expected policy violations for missing high scrutiny"

    artifacts[0].tags.scrutiny = ScrutinyLevel.HIGH
    violations = enforce_policy(artifacts, policy)
    assert not violations
