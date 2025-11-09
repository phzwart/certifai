"""Security scanner integration helpers."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from ..policy import SecurityScannerConfig, SecurityScannerSettings
from ..utils.logging import get_logger

LOGGER = get_logger("security")


@dataclass(slots=True)
class ScannerInvocation:
    name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    findings: Any


def _prepare_command(command: str, targets: Sequence[str]) -> list[str]:
    # Allow commands to reference {targets} as a placeholder, otherwise append targets to the end.
    formatted = command.format(targets=" ".join(shlex.quote(item) for item in targets))
    parts = shlex.split(formatted)
    if "{targets}" not in command and targets:
        parts.extend(targets)
    return parts


def run_scanner(config: SecurityScannerConfig, targets: Sequence[str]) -> ScannerInvocation:
    args = _prepare_command(config.command, targets)
    LOGGER.debug("Running security scanner %s", config.name)

    env = os.environ.copy()
    env.setdefault("CERTIFAI_TARGETS", " ".join(targets))

    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        env=env,
    )

    findings: Any = None
    stdout = completed.stdout.strip()
    if stdout:
        try:
            findings = json.loads(stdout)
        except json.JSONDecodeError:
            findings = stdout

    invocation = ScannerInvocation(
        name=config.name,
        command=" ".join(args),
        exit_code=completed.returncode,
        stdout=stdout,
        stderr=completed.stderr.strip(),
        findings=findings,
    )

    if completed.returncode != 0:
        LOGGER.warning("Security scanner %s exited with %d", config.name, completed.returncode)

    return invocation


def run_all_scanners(settings: SecurityScannerSettings, paths: Iterable[Path | str]) -> list[ScannerInvocation]:
    if not settings.enabled or not settings.scanners:
        LOGGER.debug("Security scanners disabled or not configured")
        return []

    targets = [str(Path(path)) for path in paths]
    results: list[ScannerInvocation] = []
    for scanner in settings.scanners:
        results.append(run_scanner(scanner, targets))
    return results
