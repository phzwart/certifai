from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from certifai.audit import Audit
from certifai.cli import cli
from certifai.registry import load_registry
from certifai.decorators import certifai
from certifai.policy import DEFAULT_POLICY, load_policy


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
def test_finalize_command_cleans_decorator(tmp_path: Path) -> None:
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
    assert "@certifai" not in content

    registry = load_registry(tmp_path)
    assert (str(module), "foo") in registry
    entry = registry[(str(module), "foo")]
    assert entry.reviewers == []
    assert entry.lifecycle_history and entry.lifecycle_history[0]["event"] == "finalized"


def test_certify_agent_respects_policy(tmp_path: Path) -> None:
    module = tmp_path / "agent.py"
    module.write_text(
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="pending")
def foo():
    return 1
""".strip()
        + "\n",
        encoding="utf-8",
    )

    policy_file = tmp_path / "policy.yml"
    policy_file.write_text(
        """
integrations:
  agents:
    enabled: true
    reviewers:
      - id: github/app-bot
        max_scrutiny: medium
""".strip()
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "certify-agent",
            str(module),
            "--agent",
            "github/app-bot",
            "--scrutiny",
            "high",
            "--policy",
            str(policy_file),
        ],
    )
    assert result.exit_code != 0
    assert "not allowed" in result.output


def test_certify_agent_disallowed_without_policy(tmp_path: Path) -> None:
    module = tmp_path / "agent_fail.py"
    module.write_text(
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="pending")
def foo():
    return 1
""".strip()
        + "\n",
        encoding="utf-8",
    )

    policy_file = tmp_path / "policy.yml"
    policy_file.write_text("integrations: {}\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "certify",
            str(module),
            "--reviewer",
            "github/app-bot",
            "--scrutiny",
            "medium",
            "--agent",
            "--policy",
            str(policy_file),
        ],
    )
    assert result.exit_code != 0
    assert "Agent-based certification" in result.output


def test_certify_agent_command_updates_metadata(tmp_path: Path) -> None:
    module = tmp_path / "agent.py"
    module.write_text(
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="pending")
def foo():
    return 1
""".strip()
        + "\n",
        encoding="utf-8",
    )

    policy_file = tmp_path / "policy.yml"
    policy_file.write_text(
        """
integrations:
  agents:
    enabled: true
    reviewers:
      - id: bot-1
        max_scrutiny: medium
""".strip()
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "certify-agent",
            str(module),
            "--agent",
            "bot-1",
            "--scrutiny",
            "medium",
            "--policy",
            str(policy_file),
        ],
    )
    assert result.exit_code == 0
    content = module.read_text(encoding="utf-8")
    assert "agent_certified=\"bot-1\"" in content or "agent_certified=\"bot-1\"" in content.replace('"', '\"')


def test_findings_and_review_status_commands(tmp_path: Path) -> None:
    module = tmp_path / "sample.py"
    module.write_text("def stub():\n    return 42\n", encoding="utf-8")

    log_path = tmp_path / "audit.log"
    policy_file = tmp_path / "policy.yml"
    policy_file.write_text(
        f"""
integrations:
  audit:
    enabled: true
    log_path: "{log_path}"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    audit = Audit.load(policy_path=policy_file)
    artifact_id = f"{module}::stub"
    audit.record_review(
        agent_id="agent-one",
        artifact=artifact_id,
        filepath=str(module),
        result="issues_found",
        findings=[
            {
                "severity": "high",
                "category": "correctness",
                "message": "Potential issue detected",
                "line": 1,
                "suggestion": "Add guard clause",
            }
        ],
        model="claude-reviewer",
    )

    runner = CliRunner()
    findings_result = runner.invoke(
        cli,
        [
            "findings",
            str(module),
            "--policy",
            str(policy_file),
            "--days",
            "30",
        ],
    )
    assert findings_result.exit_code == 0
    assert "Potential issue detected" in findings_result.output
    assert "[high]" in findings_result.output

    status_result = runner.invoke(
        cli,
        [
            "review-status",
            artifact_id,
            "--policy",
            str(policy_file),
        ],
    )
    assert status_result.exit_code == 0
    assert "Latest review" in status_result.output
    assert "Blocking issues (high+): yes" in status_result.output
