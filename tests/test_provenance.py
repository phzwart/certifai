from __future__ import annotations

from pathlib import Path

from certifai.history import compute_digest, extract_digest
from certifai.models import ScrutinyLevel
from certifai.policy import EnforcementSettings, PolicyConfig
from certifai.provenance import annotate_paths, enforce_policy
from certifai.parser import parse_file


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.195047+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.738190+00:00 digest=77e8f22f971e92daa49c83ac5af9ca62f01466fb last_commit=f07d0d9 by phzwart

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
    assert len(refreshed[0].tags.history) == 1
    history_entry = refreshed[0].tags.history[0]
    digest = extract_digest(history_entry)
    assert digest == compute_digest(refreshed[0].tags)


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:54:54.717034+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.717034+00:00 digest=bbff0beb109ee9b2068f74f83c7e9d8d5f14f63b annotated last_commit=65299e8 by phzwart

def test_history_updates_when_metadata_changes(tmp_path: Path) -> None:
    module = tmp_path / "tracked.py"
    module.write_text(
        """
def target():
    return 0
""".strip()
        + "\n",
        encoding="utf-8",
    )

    annotate_paths([module], ai_agent="gpt-4", default_notes="auto")
    initial = parse_file(module)[0]
    initial_digest = extract_digest(initial.tags.history[0])

    module.write_text(
        module.read_text(encoding="utf-8").replace(
            "@human_certified: pending", "@human_certified: PHZ"
        ),
        encoding="utf-8",
    )

    annotate_paths([module], ai_agent="gpt-4", default_notes="auto")
    updated = parse_file(module)[0]
    updated_digest = extract_digest(updated.tags.history[0])

    assert initial_digest != updated_digest
    assert updated_digest == compute_digest(updated.tags)


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.195047+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.738190+00:00 digest=77e8f22f971e92daa49c83ac5af9ca62f01466fb last_commit=uncommitted

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
