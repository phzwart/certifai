from __future__ import annotations

import json
import os
from pathlib import Path

from click.testing import CliRunner

from certifai.cli import cli
from certifai.integrations.security import run_all_scanners
from certifai.policy import SecurityScannerConfig, SecurityScannerSettings


def _create_scanner_script(tmp_path: Path, contents: str) -> Path:
    script = tmp_path / "scanner.py"
    script.write_text(contents, encoding="utf-8")
    os.chmod(script, 0o755)
    return script


def test_run_all_scanners_executes_command(tmp_path: Path) -> None:
    script = _create_scanner_script(
        tmp_path,
        """#!/usr/bin/env python3
import json
import sys
json.dump({"ok": True, "targets": sys.argv[1:]}, sys.stdout)
""",
    )
    settings = SecurityScannerSettings(
        enabled=True,
        scanners=(SecurityScannerConfig(name="demo", command=f"{script}"),),
    )

    paths = [tmp_path / "foo.py"]
    results = run_all_scanners(settings, paths)
    assert len(results) == 1
    result = results[0]
    assert result.exit_code == 0
    assert result.findings["ok"] is True
    assert result.findings["targets"]


def test_cli_security_run_outputs_json(tmp_path: Path) -> None:
    script = _create_scanner_script(
        tmp_path,
        """#!/usr/bin/env python3
import json, sys
json.dump({"issues": 0}, sys.stdout)
""",
    )
    policy_file = tmp_path / "policy.yml"
    policy_file.write_text(
        f"""
integrations:
  security_scanners:
    commands:
      - name: demo
        run: "{script}"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["security", "run", "--policy", str(policy_file), "--output", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "pass"
    assert payload["scanners"][0]["name"] == "demo"
