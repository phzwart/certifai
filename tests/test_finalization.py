from __future__ import annotations

from pathlib import Path

from certifai.digest import compute_artifact_digest
from certifai.finalize import finalize
from certifai.checks import reconcile_registry
from certifai.registry import load_registry
from certifai.parser import parse_file


def _write_module(path: Path, source: str) -> Path:
    path.write_text(source.strip() + "\n", encoding="utf-8")
    return path


def test_finalize_moves_metadata_and_sets_done(tmp_path: Path) -> None:
    module = tmp_path / "sample.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="Reviewer", scrutiny="high")
def foo():
    return 1
""",
    )

    finalized = finalize([module], registry_root=tmp_path)
    assert finalized, "Expected artifact to be finalized"

    content = module.read_text(encoding="utf-8")
    assert "done=True" in content
    assert "history" not in content

    registry = load_registry(tmp_path)
    key = (str(module), "foo")
    assert key in registry
    entry = registry[key]
    assert entry.human_certified == "Reviewer"
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


def test_reconcile_registry_reopens_modified_artifacts(tmp_path: Path) -> None:
    module = tmp_path / "recheck.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="Reviewer", scrutiny="high")
def foo():
    return 1
""",
    )
    finalize([module], registry_root=tmp_path)

    module.write_text(
        (
            """
from certifai.decorators import certifai


@certifai(done=True, human_certified="Reviewer")
def foo():
    return 2
"""
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    changed = reconcile_registry(registry_root=tmp_path)
    assert module in changed

    content = module.read_text(encoding="utf-8")
    assert "done=True" not in content
    registry = load_registry(tmp_path)
    assert (str(module), "foo") not in registry
