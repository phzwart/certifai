from __future__ import annotations

from pathlib import Path

from certifai.decorators import certifai
from certifai.history import compute_digest, extract_digest
from certifai.models import ScrutinyLevel
from certifai.policy import EnforcementSettings, PolicyConfig
from certifai.provenance import annotate_paths, enforce_policy
from certifai.parser import parse_file


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:46.195047+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.575831+00:00 digest=639af9a937d6a9584bd88916db362d52f1313429 last_commit=f07d0d9 by phzwart",
    ],
)
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


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:54:54.717034+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.575831+00:00 digest=d5cc63e098dc5bce0898ee26804712542260c783 last_commit=97cec9a by phzwart",
    ],
)
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
            'human_certified="pending"', 'human_certified="PHZ"'  # this is ok, just a test
        ),
        encoding="utf-8",
    )

    annotate_paths([module], ai_agent="gpt-4", default_notes="auto")
    updated = parse_file(module)[0]
    updated_digest = extract_digest(updated.tags.history[0])

    assert initial_digest != updated_digest
    assert updated_digest == compute_digest(updated.tags)


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:46.195047+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.575831+00:00 digest=639af9a937d6a9584bd88916db362d52f1313429 last_commit=f07d0d9 by phzwart",
    ],
)
def test_enforce_policy_checks_scrutiny(tmp_path: Path) -> None:
    module = tmp_path / "policy_case.py"
    module.write_text(
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="pending")
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


@certifai(
    ai_composed="cursor",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T01:10:38.980744+00:00",
    notes="auto-tagged by certifai",
    history=[
        "2025-11-08T01:35:22.575831+00:00 digest=d0f19a4030babe0a7169859176b39e28e87d84f7 last_commit=uncommitted",
    ],
)
def test_enforce_policy_coverage_ignores_classes(tmp_path: Path) -> None:
    module = tmp_path / "classes_only.py"
    module.write_text(
        """
class Sample:
    pass
""".strip()
        + "\n",
        encoding="utf-8",
    )

    artifacts = parse_file(module)
    policy = PolicyConfig(
        enforcement=EnforcementSettings(
            ai_composed_requires_high_scrutiny=False,
            min_coverage=0.5,
        ),
        reviewers=(),
    )
    violations = enforce_policy(artifacts, policy)
    assert not violations


@certifai(
    ai_composed="cursor",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T01:10:38.980744+00:00",
    notes="auto-tagged by certifai",
    history=[
        "2025-11-08T01:35:22.575831+00:00 digest=d0f19a4030babe0a7169859176b39e28e87d84f7 last_commit=uncommitted",
    ],
)
def test_enforce_policy_coverage_counts_functions(tmp_path: Path) -> None:
    module = tmp_path / "function_only.py"
    module.write_text(
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="pending")
def pending():
    return 1
""".strip()
        + "\n",
        encoding="utf-8",
    )

    artifacts = parse_file(module)
    policy = PolicyConfig(
        enforcement=EnforcementSettings(
            ai_composed_requires_high_scrutiny=False,
            min_coverage=1.0,
        ),
        reviewers=(),
    )
    violations = enforce_policy(artifacts, policy)
    assert violations == ["Coverage 0/1 (0.00%) below required 100%"], violations

    artifacts[0].tags.human_certified = "PHZ"
    violations = enforce_policy(artifacts, policy)
    assert not violations


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="high",
    date="2025-11-08T00:54:54.717034+00:00",
    notes="manual review",
    history=[
        "2025-11-08T01:43:04.837083+00:00 digest=e429bda58461c056c95eb93ab80918c959e5eaa1 last_commit=uncommitted",
    ],
)
def test_ignore_unannotated_skips_auto_tagging(tmp_path: Path) -> None:
    module = tmp_path / "skip.py"
    module.write_text("def pending():\n    return 1\n", encoding="utf-8")

    policy = PolicyConfig(
        enforcement=EnforcementSettings(
            ai_composed_requires_high_scrutiny=False,
            ignore_unannotated=True,
        ),
        reviewers=(),
    )
    result = annotate_paths([module], policy=policy, ai_agent="gpt-4")
    assert not result.updated_files

    artifacts = parse_file(module)
    assert not artifacts[0].tags.has_metadata

    violations = enforce_policy(artifacts, policy)
    assert not violations


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="high",
    date="2025-11-08T00:54:54.717034+00:00",
    notes="manual review",
    history=[
        "2025-11-08T01:43:04.837083+00:00 digest=e429bda58461c056c95eb93ab80918c959e5eaa1 last_commit=uncommitted",
    ],
)
def test_ignore_unannotated_excludes_from_coverage(tmp_path: Path) -> None:
    module = tmp_path / "coverage.py"
    module.write_text("def pending():\n    return 1\n", encoding="utf-8")

    policy = PolicyConfig(
        enforcement=EnforcementSettings(
            ai_composed_requires_high_scrutiny=False,
            min_coverage=1.0,
            ignore_unannotated=True,
        ),
        reviewers=(),
    )

    artifacts = parse_file(module)
    violations = enforce_policy(artifacts, policy)
    assert not violations
