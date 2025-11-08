from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from certifai.cli import cli
from certifai.registry import load_registry
from certifai.decorators import certifai


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:46.222693+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.538516+00:00 digest=664a9d19cca744eee705a85c3200e70d5a63bdf4 last_commit=f07d0d9 by phzwart",
    ],
)
def test_report_command_outputs_json(tmp_path: Path) -> None:
    module = tmp_path / "module.py"
    module.write_text("def foo():\n    return 42\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--format", "json", str(module)])

    assert result.exit_code == 0
    assert "total_functions" in result.output


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:46.222693+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.538516+00:00 digest=664a9d19cca744eee705a85c3200e70d5a63bdf4 last_commit=f07d0d9 by phzwart",
    ],
)
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
    assert "@certifai" in content
    assert 'ai_composed="gpt-4"' in content
    assert 'human_certified="pending"' in content
    assert 'notes="demo"' in content


def test_finalize_command_sets_done_flag(tmp_path: Path) -> None:
    module = tmp_path / "module.py"
    module.write_text(
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="Reviewer", scrutiny="high")
def foo():
    return 1
""".strip()
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "finalize",
            str(module),
            "--registry-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    content = module.read_text(encoding="utf-8")
    assert "done=True" in content
    registry = load_registry(tmp_path)
    assert (str(module), "foo") in registry
