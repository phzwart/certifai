"""GitHub-oriented helpers for certifai pull request integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from ..models import CodeArtifact, ScrutinyLevel
from ..policy import PolicyConfig
from ..provenance import enforce_policy
from ..report import CoverageSummary, build_summary


def _artifact_descriptor(artifact: CodeArtifact) -> dict[str, object]:
    return {
        "name": artifact.name,
        "filepath": str(artifact.filepath),
        "lineno": artifact.lineno,
        "end_lineno": artifact.end_lineno,
        "ai_composed": artifact.tags.ai_composed,
        "human_certified": artifact.tags.human_certified,
        "scrutiny": artifact.tags.scrutiny.value if artifact.tags.scrutiny else None,
        "done": artifact.tags.done,
        "agents": list(artifact.tags.agents),
    }


def _evaluate_summary(summary: CoverageSummary, policy: PolicyConfig) -> dict[str, object]:
    violations = enforce_policy(summary.artifacts, policy)

    min_coverage = policy.enforcement.min_coverage
    total_functions = summary.total_functions
    allowed_agents = {perm.id: perm for perm in policy.integrations.agents.reviewers}

    def _is_certified(artifact: CodeArtifact) -> bool:
        if artifact.tags.human_certified and artifact.tags.human_certified.lower() != "pending":
            return True
        for reviewer in artifact.tags.reviewers:
            if reviewer.kind == "human" and reviewer.id and reviewer.id.lower() != "pending":
                return True
            if reviewer.kind == "agent" and reviewer.id in allowed_agents:
                perm = allowed_agents[reviewer.id]
                max_level = ScrutinyLevel.from_string(perm.max_scrutiny) if perm.max_scrutiny else None
                if max_level is None:
                    return True
                agent_level = reviewer.scrutiny or ScrutinyLevel.AUTO
                order = [ScrutinyLevel.AUTO, ScrutinyLevel.LOW, ScrutinyLevel.MEDIUM, ScrutinyLevel.HIGH]
                if order.index(agent_level) <= order.index(max_level):
                    return True
        return False

    covered = sum(1 for artifact in summary.artifacts if _is_certified(artifact))
    pending = [artifact for artifact in summary.artifacts if not _is_certified(artifact)]
    ai_pending = [artifact for artifact in pending if artifact.tags.ai_composed]
    agent_only = [
        artifact for artifact in summary.artifacts if artifact.tags.agents and not artifact.tags.human_certified
    ]
    finalized = [artifact for artifact in summary.artifacts if artifact.tags.done]
    coverage_ratio = (covered / total_functions) if total_functions else 1.0
    agent_ratio = summary.agent_certified / total_functions if total_functions else 0.0
    coverage_ok = (
        min_coverage is None
        or total_functions == 0
        or coverage_ratio >= min_coverage
    )

    agents_config = getattr(policy.integrations, "agents", None)
    if (
        not coverage_ok
        and min_coverage is not None
        and agents_config
        and getattr(agents_config, "allow_coverage_credit", False)
        and agent_ratio >= min_coverage
    ):
        coverage_ok = True
        messages = "Agent coverage satisfied minimum threshold"
    else:
        messages = None

    overall_status = "pass"
    checks: list[dict[str, object]] = []

    if not coverage_ok:
        overall_status = "fail"
        checks.append({
            "name": "coverage",
            "status": "fail",
            "actual": coverage_ratio,
            "required": min_coverage,
            "agent_ratio": agent_ratio,
            "note": messages,
        })
    else:
        checks.append({
            "name": "coverage",
            "status": "pass",
            "actual": coverage_ratio,
            "required": min_coverage,
            "agent_ratio": agent_ratio,
            "note": messages,
        })

    if violations:
        overall_status = "fail"
        checks.append({
            "name": "policy",
            "status": "fail",
            "violations": violations,
        })
    else:
        checks.append({
            "name": "policy",
            "status": "pass",
            "violations": [],
        })

    if ai_pending:
        overall_status = "fail"
        checks.append({
            "name": "ai_pending",
            "status": "fail",
            "count": len(ai_pending),
        })
    else:
        checks.append({
            "name": "ai_pending",
            "status": "pass",
            "count": 0,
        })

    return {
        "status": overall_status,
        "summary": {
            **summary.to_dict(),
            "coverage_ratio": coverage_ratio,
            "certified_total": covered,
        },
        "counts": {
            "finalized": len(finalized),
            "pending_review": len(pending),
            "ai_pending": len(ai_pending),
            "agent_only": len(agent_only),
        },
        "violations": violations,
        "pending_artifacts": [_artifact_descriptor(artifact) for artifact in pending],
        "ai_pending_artifacts": [_artifact_descriptor(artifact) for artifact in ai_pending],
        "agent_only_artifacts": [_artifact_descriptor(artifact) for artifact in agent_only],
        "finalized_artifacts": [_artifact_descriptor(artifact) for artifact in finalized],
        "checks": checks,
    }


def build_pr_status(paths: Iterable[Path | str], policy: PolicyConfig) -> dict[str, object]:
    resolved_paths = list(_normalise_paths(paths)) or [Path.cwd()]
    summary = build_summary(resolved_paths)
    evaluation = _evaluate_summary(summary, policy)
    evaluation["paths"] = {
        "evaluated": sorted({str(Path(path)) for path in resolved_paths}),
    }
    return evaluation


def _normalise_paths(paths: Iterable[Path | str]) -> Sequence[Path]:
    resolved: list[Path] = []
    for item in paths:
        path = Path(item)
        if not path.exists():
            # Skip missing paths (e.g., removed files in PR diffs)
            continue
        resolved.append(path)
    return resolved
