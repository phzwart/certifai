from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from certifai.cli import cli
from certifai.enforce import enforce_ci
from certifai.certify import certify_agent
from certifai.policy import (
    EnforcementSettings,
    IntegrationsConfig,
    PolicyConfig,
    SecurityScannerSettings,
    AgentPermission,
    AgentSettings,
)
from certifai.integrations.security import SecurityScannerConfig


def _write_module(path: Path, source: str) -> None:
    path.write_text(source.strip() + "\n", encoding="utf-8")


def test_enforce_ci_detects_pending(tmp_path: Path) -> None:
    module = tmp_path / "pending.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


@certifai(ai_composed="gpt-5", human_certified="pending")
def foo():
    return 1
""",
    )

    policy = PolicyConfig(
        enforcement=EnforcementSettings(min_coverage=1.0),
        reviewers=(),
        integrations=IntegrationsConfig(),
    )

    result = enforce_ci([module], policy)
    assert result.status == "fail"
    assert any("Policy" in message or "coverage" in message for message in result.messages)


def test_cli_enforce_runs_successfully(tmp_path: Path) -> None:
    module = tmp_path / "done.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


@certifai(done=True, human_certified="Reviewer")
def foo():
    return 1
""",
    )
    policy_file = tmp_path / "policy.yml"
    policy_file.write_text("""integrations: {}""", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "enforce",
            "--policy",
            str(policy_file),
            "--path",
            str(module),
            "--output",
            "json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] in {"pass", "fail"}


def test_enforce_ci_agent_coverage(tmp_path: Path) -> None:
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

    certify_agent(
        [module],
        agent_id="github/apps/certifai-agent",
        scrutiny="high",
        include_existing=True,
    )

    policy = PolicyConfig(
        enforcement=EnforcementSettings(min_coverage=1.0),
        reviewers=(),
        integrations=IntegrationsConfig(
            agents=AgentSettings(
                enabled=True,
                reviewers=(
                    AgentPermission(
                        id="github/apps/certifai-agent",
                        max_scrutiny="high",
                        allow_finalize=True,
                    ),
                ),
            )
        ),
    )

    result = enforce_ci([module], policy)
    assert result.status == "pass"
