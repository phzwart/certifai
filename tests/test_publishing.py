from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from certifai.cli import cli
from certifai.policy import PolicyConfig, IntegrationsConfig, PublishingDestination, PublishingSettings, EnforcementSettings
from certifai.publishing import publish_report


def _write_module(path: Path, source: str) -> None:
    path.write_text(source.strip() + "\n", encoding="utf-8")


def test_publish_report_writes_markdown(tmp_path: Path) -> None:
    module = tmp_path / "example.py"
    _write_module(
        module,
        """
from certifai.decorators import certifai


@certifai(done=True, human_certified="Reviewer")
def finalized():
    return 1
""",
    )

    destination = PublishingDestination(type="wiki", path=str(tmp_path / "wiki.md"))
    policy = PolicyConfig(
        enforcement=EnforcementSettings(),
        reviewers=(),
        integrations=IntegrationsConfig(
            publishing=PublishingSettings(enabled=True, destinations=(destination,)),
        ),
    )

    results = publish_report([module], policy)
    assert results
    report_path = tmp_path / "wiki.md"
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "Total functions" in content
    assert "Coverage" in content
    assert "Agent-certified" in content


def test_cli_publish_report_outputs_destinations(tmp_path: Path) -> None:
    policy_file = tmp_path / "policy.yml"
    policy_file.write_text(
        f"""
integrations:
  publishing:
    destinations:
      - type: file
        path: "{tmp_path}/report.md"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["publish", "report", "--policy", str(policy_file), "--output", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] in {"pass", "noop"}
    assert payload["destinations"][0]["type"] == "file"
