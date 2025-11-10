from __future__ import annotations

from pathlib import Path

from certifai.digest import compute_artifact_digest
from certifai.finalize import finalize
from certifai.registry import load_registry
from certifai.parser import parse_file


def _write_module(path: Path, source: str) -> Path:
    path.write_text(source.strip() + "\n", encoding="utf-8")
    return path


def test_finalize_removes_decorator_completely(tmp_path: Path) -> None:
    module = tmp_path / "sample.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


@certifai(
    ai_composed="claude-sonnet-4",
    human_certified="Reviewer",
    reviewers=[
        {"kind": "agent", "id": "tests", "scrutiny": "medium", "timestamp": "2025-11-08T10:00:00Z"},
        {"kind": "human", "id": "Reviewer", "scrutiny": "high", "timestamp": "2025-11-08T11:00:00Z"}
    ],
    history=["2025-11-08T09:00:00Z annotated"]
)
def foo():
    return 1
""",
    )

    finalized = finalize([module], registry_root=tmp_path)
    assert finalized, "Expected artifact to be finalized"

    content = module.read_text(encoding="utf-8")
    assert "@certifai" not in content

    registry = load_registry(tmp_path)
    key = (str(module), "foo")
    assert key in registry
    entry = registry[key]
    reviewer_ids = {item["id"] for item in entry.reviewers}
    assert reviewer_ids == {"tests", "Reviewer"}
    assert entry.lifecycle_history and entry.lifecycle_history[0]["event"] == "finalized"


def test_finalize_preserves_code_structure(tmp_path: Path) -> None:
    module = tmp_path / "structure.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


def instrumentation(func):
    return func


@instrumentation
@certifai(ai_composed="gpt-5", human_certified="Reviewer")
def foo():
    return 1
""",
    )

    finalize([module], registry_root=tmp_path)

    content = module.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert "@certifai" not in content
    idx = lines.index("@instrumentation")
    assert lines[idx + 1].startswith("def foo()")
    assert lines[idx - 1] == ""


def test_finalized_artifact_in_registry_contains_full_provenance(tmp_path: Path) -> None:
    module = tmp_path / "registry.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


@certifai(
    ai_composed="claude-opus",
    human_certified="peter",
    reviewers=[
        {"kind": "human", "id": "peter", "scrutiny": "high", "notes": "Validated", "timestamp": "2025-11-08T11:30:00Z"},
        {"kind": "agent", "id": "test-suite", "scrutiny": "medium", "timestamp": "2025-11-08T10:00:00Z"}
    ],
    history=["2025-11-08T09:00:00Z annotated"]
)
def foo():
    return 1
""",
    )

    finalize([module], registry_root=tmp_path)

    registry = load_registry(tmp_path)
    entry = registry[(str(module), "foo")]
    assert entry.human_certified == "peter"
    assert entry.reviewers == [
        {
            "kind": "human",
            "id": "peter",
            "scrutiny": "high",
            "notes": "Validated",
            "timestamp": "2025-11-08T11:30:00Z",
        },
        {
            "kind": "agent",
            "id": "test-suite",
            "scrutiny": "medium",
            "notes": None,
            "timestamp": "2025-11-08T10:00:00Z",
        },
    ]
    assert entry.lifecycle_history[-1]["event"] == "finalized"
    assert entry.digest


def test_compute_artifact_digest_ignores_formatting(tmp_path: Path) -> None:
    module = tmp_path / "formatting.py"
    module.write_text(
        """
from certifai.decorators import certifai


@certifai()
def foo():
    return 1
""".strip()
        + "\n",
        encoding="utf-8",
    )
    artifact = parse_file(module)[0]
    first = compute_artifact_digest(artifact)

    module.write_text(
        """
from certifai.decorators import certifai


@certifai()
def foo():
    return 1   
""".strip()
        + "\n",
        encoding="utf-8",
    )
    artifact_updated = parse_file(module)[0]
    second = compute_artifact_digest(artifact_updated)
    assert first == second
