from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from certifai.cli import cli
from certifai.parser import parse_file
from certifai.policy import load_policy


def _write_pending_module(path: Path) -> None:
    path.write_text(
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="pending")
def foo():
    return 1
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_agent_certify_updates_metadata(tmp_path: Path) -> None:
    module = tmp_path / "agent.py"
    _write_pending_module(module)

    log_path = tmp_path / "audit.log"
    policy_file = tmp_path / "policy.yml"
    policy_file.write_text(
        f"""
integrations:
  audit:
    enabled: true
    log_path: "{log_path}"
  agents:
    enabled: true
    reviewers:
      - id: github/apps/certifai-agent
        max_scrutiny: high
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
            "github/apps/certifai-agent",
            "--scrutiny",
            "medium",
            "--policy",
            str(policy_file),
        ],
    )
    assert result.exit_code == 0
    artifacts = parse_file(module)
    assert artifacts[0].tags.agents == ["github/apps/certifai-agent"]

    payload = json.loads(
        CliRunner()
        .invoke(
            cli,
            [
                "audit",
                "show",
                "--policy",
                str(policy_file),
                "--output",
                "json",
            ],
        )
        .output
    )
    assert any(entry.get("action") == "certify" and entry.get("data", {}).get("reviewer") == "github/apps/certifai-agent" for entry in payload)


def test_agent_cli_respects_policy(tmp_path: Path) -> None:
    module = tmp_path / "agent.py"
    _write_pending_module(module)

    policy_file = tmp_path / "policy.yml"
    policy_file.write_text("""integrations: { agents: { enabled: false } }""", encoding="utf-8")
    policy = load_policy(policy_file)
    assert not policy.integrations.agents.enabled

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "certify-agent",
            str(module),
            "--agent",
            "unlisted-agent",
            "--scrutiny",
            "medium",
            "--policy",
            str(policy_file),
        ],
    )
    assert result.exit_code != 0
    assert "agent certification is not enabled" in result.output.lower()
