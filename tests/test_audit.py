from __future__ import annotations

import json
from pathlib import Path

import pytest

from click.testing import CliRunner

from certifai.audit import Audit
from certifai.cli import cli
from certifai.policy import load_policy


def _write_module(path: Path, source: str) -> None:
    path.write_text(source.strip() + "\n", encoding="utf-8")


def test_certify_and_enforce_log_actions(tmp_path: Path) -> None:
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

    policy_config = load_policy(policy_file)
    assert policy_config.integrations.audit.enabled

    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "certify",
            str(module),
            "--reviewer",
            "Alice",
            "--scrutiny",
            "high",
            "--include-existing",
            "--policy",
            str(policy_file),
        ],
    )
    assert result.exit_code == 0
    assert "Certified" in result.output
    assert "Certified 1" in result.output or "Certified 1 artifact" in result.output or "Certified 1 artifact(s)." in result.output
    content_after = module.read_text(encoding="utf-8")
    assert "Alice" in content_after

    pre_entries = []
    if log_path.exists():
        pre_entries = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    enforce_result = runner.invoke(
        cli,
        [
            "enforce",
            "--policy",
            str(policy_file),
            "--path",
            str(module),
        ],
    )
    assert enforce_result.exit_code in {0, 1}

    show_result = runner.invoke(
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
    assert show_result.exit_code == 0
    payload = json.loads(show_result.output)
    if not payload:
        pytest.fail(f"no audit entries found; pre_entries={pre_entries}")
    assert isinstance(payload, list)
    assert payload
    if not any(entry.get("action") == "certify" for entry in payload):
        pytest.fail(str(payload))
    assert any(entry.get("action") == "enforce" for entry in payload)


def test_audit_record_review_and_query(tmp_path: Path) -> None:
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

    module_path = tmp_path / "tracked.py"
    module_path.write_text("def stub():\n    return 0\n", encoding="utf-8")
    artifact_id = f"{module_path}::stub"

    audit = Audit.load(policy_path=policy_file)
    audit.record_review(
        agent_id="llm-tester",
        artifact=artifact_id,
        filepath=str(module_path),
        result="issues_found",
        findings=[
            {
                "severity": "high",
                "category": "correctness",
                "message": "edge case fails",
                "line": 1,
                "suggestion": "handle negative inputs",
            }
        ],
        model="gpt-5",
    )

    findings = audit.get_findings(filepath=str(module_path), severity="medium", since_days=7)
    assert findings, "expected findings to be returned"
    assert findings[0]["finding"]["severity"] == "high"
    assert "edge case fails" in findings[0]["finding"]["message"]

    latest = audit.get_latest_review(artifact_id)
    assert latest is not None
    assert latest["data"]["result"] == "issues_found"

    assert audit.has_blocking_issues(artifact_id, min_severity="medium")
