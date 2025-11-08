from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from certifai.cli import cli


def test_report_command_outputs_json(tmp_path: Path) -> None:
    module = tmp_path / "module.py"
    module.write_text("def foo():\n    return 42\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--format", "json", str(module)])

    assert result.exit_code == 0
    assert "total_functions" in result.output


def test_annotate_command_inserts_metadata(tmp_path: Path) -> None:
    module = tmp_path / "module.py"
    module.write_text("def bar():\n    return 1\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["annotate", str(module), "--ai-agent", "gpt-4", "--notes", "demo"],
    )

    assert result.exit_code != 0  # policy violation expected (no high scrutiny)
    assert "Policy violation" in result.output

    content = module.read_text(encoding="utf-8")
    assert "@ai_composed: gpt-4" in content
    assert "@human_certified: pending" in content
    assert "# notes: demo" in content
