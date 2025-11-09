from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from certifai.cli import cli
from certifai.integrations.github import build_pr_status
from certifai.policy import DEFAULT_POLICY


def _write_module(path: Path, source: str) -> None:
    path.write_text(source.strip() + "\n", encoding="utf-8")


def test_build_pr_status_detects_pending(tmp_path: Path) -> None:
    module = tmp_path / "sample.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="pending")
def foo():
    return 1
""",
    )

    status = build_pr_status([module], DEFAULT_POLICY)
    assert status["status"] == "fail"
    assert status["counts"]["pending_review"] == 1
    assert status["counts"]["ai_pending"] == 1
    assert status["counts"]["agent_only"] == 0
    assert status["pending_artifacts"]


def test_cli_pr_status_outputs_json(tmp_path: Path) -> None:
    module = tmp_path / "done.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


@certifai(done=True, human_certified="Reviewer")
def foo():
    return 42
""",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["pr", "status", "--path", str(module), "--output", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "pass"
    assert payload["counts"]["finalized"] == 1
    assert payload["counts"]["pending_review"] == 0
    assert payload["counts"]["agent_only"] == 0
