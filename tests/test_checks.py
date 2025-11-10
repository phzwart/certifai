from __future__ import annotations

import json
import os
from pathlib import Path

from certifai.checks import reconcile_registry
from certifai.finalize import finalize
from certifai.registry import load_registry


def _stage_two_source(body: str) -> str:
    return f"""
from certifai.decorators import certifai


@certifai(
    ai_composed="claude-sonnet-4",
    human_certified="peter",
    reviewers=[
        {{"kind": "human", "id": "peter", "scrutiny": "high", "timestamp": "2025-11-08T11:30:00Z"}},
        {{"kind": "agent", "id": "test-suite", "scrutiny": "medium", "timestamp": "2025-11-08T10:00:00Z"}}
    ],
    history=["2025-11-08T09:00:00Z annotated"]
)
def foo():
    {body}
"""


def _prepare_finalized_artifact(tmp_path: Path, filename: str = "drift.py") -> Path:
    module = tmp_path / filename
    module.write_text(_stage_two_source("return 1").strip() + "\n", encoding="utf-8")
    finalized = finalize([module], registry_root=tmp_path)
    assert finalized, "Expected artifact to be finalized"
    assert "@certifai" not in module.read_text(encoding="utf-8")
    return module


def _run_reconcile(tmp_path: Path) -> list[Path]:
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        return reconcile_registry(registry_root=tmp_path)
    finally:
        os.chdir(original_cwd)


def test_check_reopens_with_minimal_decorator(tmp_path: Path) -> None:
    module = _prepare_finalized_artifact(tmp_path, "drift.py")
    original_content = module.read_text(encoding="utf-8")
    module.write_text(original_content.replace("return 1", "return 2"), encoding="utf-8")

    reopened = _run_reconcile(tmp_path)
    assert reopened == [module]

    content = module.read_text(encoding="utf-8")
    assert "@certifai" in content
    assert "ai_composed=\"claude-sonnet-4\"" in content
    assert "reviewers=[]" in content


def test_check_archives_old_registry_entry(tmp_path: Path) -> None:
    module = _prepare_finalized_artifact(tmp_path, "history.py")
    module.write_text(module.read_text(encoding="utf-8").replace("return 1", "return 3"), encoding="utf-8")

    _run_reconcile(tmp_path)

    registry = load_registry(tmp_path)
    assert (str(module), "foo") not in registry
    assert registry.history, "Expected archived history entry"
    archived = registry.history[-1]
    assert archived["reason"] == "code_changed"
    assert archived["old_digest"] != archived["new_digest"]
    assert archived["entry"]["qualified_name"] == "foo"


def test_check_logs_reopening_event(tmp_path: Path) -> None:
    policy_path = tmp_path / ".certifai.yml"
    policy_path.write_text(
        """
integrations:
  audit:
    enabled: true
    log_path: "audit.log"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    module = _prepare_finalized_artifact(tmp_path, "audit.py")
    module.write_text(module.read_text(encoding="utf-8").replace("return 1", "return 5"), encoding="utf-8")

    _run_reconcile(tmp_path)

    log_path = tmp_path / "audit.log"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines, "Expected audit log entries"
    record = json.loads(lines[-1])
    assert record["action"] == "reopen"
    data = record["data"]
    assert data["artifact"] == "foo"
    assert data["reason"] == "digest_mismatch"
    assert data["old_digest"] != data["new_digest"]
