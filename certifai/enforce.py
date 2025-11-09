"""CI enforcement helpers for certifai."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .integrations.github import build_pr_status
from .integrations.security import run_all_scanners
from .policy import PolicyConfig
from .provenance import annotate_paths
from .report import build_summary
from .utils.logging import get_logger

LOGGER = get_logger("enforce")


@dataclass(slots=True)
class EnforcementResult:
    status: str
    messages: list[str]
    payload: dict[str, object]


def enforce_ci(paths: Sequence[Path], policy: PolicyConfig) -> EnforcementResult:
    messages: list[str] = []
    status = "pass"

    summary = build_summary(paths)
    pr_status_payload = build_pr_status(paths, policy)

    if pr_status_payload.get("status") != "pass":
        status = "fail"
        messages.append("Policy or coverage requirements not met.")

    security_results = run_all_scanners(policy.integrations.security, paths)
    if any(result.exit_code != 0 for result in security_results):
        status = "fail"
        messages.append("Security scanners reported issues.")

    payload = {
        "pr_status": pr_status_payload,
        "security": [
            {
                "name": result.name,
                "command": result.command,
                "exit_code": result.exit_code,
                "findings": result.findings,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            for result in security_results
        ],
        "summary": summary.to_dict(),
    }

    if status == "pass":
        messages.append("All enforcement checks passed.")

    return EnforcementResult(status=status, messages=messages, payload=payload)
