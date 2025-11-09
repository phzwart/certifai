"""Provenance tagging and enforcement utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from .decorators import certifai, format_metadata_decorator
from .history import build_history_entry, compute_digest, extract_digest
from .metadata import MetadataUpdate, update_metadata_blocks
from .models import CodeArtifact, ScrutinyLevel, TagMetadata
from .parser import iter_python_files, parse_file
from .policy import DEFAULT_POLICY, PolicyConfig
from .utils.logging import get_logger

LOGGER = get_logger("provenance")


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.918067+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.035474+00:00 digest=0a2c121eff2c7e10e998652feff8c5c433148750 last_commit=f07d0d9 by phzwart",
    ],
)
@dataclass(slots=True)
class ProvenanceResult:
    """Result of running provenance annotation on a set of files."""

    artifacts: list[CodeArtifact]
    updated_files: list[Path]
    policy_violations: list[str]


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.918067+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.035474+00:00 digest=0a2c121eff2c7e10e998652feff8c5c433148750 last_commit=f07d0d9 by phzwart",
    ],
)
def annotate_paths(
    paths: Iterable[Path | str],
    *,
    ai_agent: str = "pending",
    default_notes: str | None = "auto-tagged by certifai",
    timestamp: datetime | None = None,
    policy: PolicyConfig | None = None,
) -> ProvenanceResult:
    """Ensure metadata headers exist for each discovered artifact."""

    resolved_paths = list(iter_python_files(paths))
    collected_artifacts: list[CodeArtifact] = []
    updated_paths: set[Path] = set()
    active_policy = policy or DEFAULT_POLICY

    for path in resolved_paths:
        artifacts = list(parse_file(path))
        file_changed = False

        needs_update: Sequence[CodeArtifact] = ()
        if not active_policy.enforcement.ignore_unannotated:
            needs_update = [artifact for artifact in artifacts if not artifact.tags.has_metadata]
        if needs_update:
            LOGGER.debug("Annotating %s with %d metadata blocks", path, len(needs_update))
            if _ensure_metadata_decorators(
                path,
                needs_update,
                ai_agent=ai_agent,
                default_notes=default_notes,
                timestamp=timestamp,
            ):
                file_changed = True
        artifacts = list(parse_file(path))
        if _refresh_history_blocks(path, artifacts, timestamp):
            file_changed = True
            artifacts = list(parse_file(path))

        collected_artifacts.extend(artifacts)
        if file_changed:
            updated_paths.add(path)

    violations = enforce_policy(collected_artifacts, active_policy)

    return ProvenanceResult(
        artifacts=collected_artifacts,
        updated_files=sorted(updated_paths),
        policy_violations=violations,
    )


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.918067+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.035474+00:00 digest=0a2c121eff2c7e10e998652feff8c5c433148750 last_commit=f07d0d9 by phzwart",
    ],
)
def enforce_policy(artifacts: Sequence[CodeArtifact], policy: PolicyConfig) -> list[str]:
    """Return a list of policy violations detected for the given artifacts."""

    violations: list[str] = []
    if policy.enforcement.ai_composed_requires_high_scrutiny:
        for artifact in artifacts:
            if artifact.tags.ai_composed and artifact.tags.scrutiny not in {
                ScrutinyLevel.HIGH,
            }:
                violations.append(
                    f"{artifact.filepath}:{artifact.lineno} requires high scrutiny for ai_composed artifacts"
                )
    if policy.enforcement.min_coverage is not None:
        function_artifacts = [
            artifact
            for artifact in artifacts
            if artifact.artifact_type in {"function", "async_function"}
            and (artifact.tags.has_metadata or not policy.enforcement.ignore_unannotated)
        ]
        total = len(function_artifacts)
        if total:
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

            certified = sum(1 for artifact in function_artifacts if _is_certified(artifact))
            coverage = certified / total
            if coverage < policy.enforcement.min_coverage:
                violations.append(
                    "Coverage "
                    f"{certified}/{total} ({coverage:.2%}) below required "
                    f"{policy.enforcement.min_coverage:.0%}"
                )
    return violations


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.918067+00:00",
    notes="bulk annotation",
    history=[
        "2025-11-08T01:22:48.035474+00:00 digest=aff21f4e5f07604c1d3c2dfdc5c8260d91621e0a last_commit=f07d0d9 by phzwart",
    ],
)
def _ensure_metadata_decorators(
    path: Path,
    artifacts: Sequence[CodeArtifact],
    *,
    ai_agent: str,
    default_notes: str | None,
    timestamp: datetime | None,
) -> bool:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    if not lines:
        return False

    effective_timestamp = timestamp or datetime.now(timezone.utc)
    iso_timestamp = effective_timestamp.isoformat()
    changed = False

    for artifact in sorted(artifacts, key=lambda item: item.start_line, reverse=True):
        metadata = TagMetadata(
            ai_composed=ai_agent,
            human_certified="pending",
            scrutiny=ScrutinyLevel.AUTO,
            date=iso_timestamp,
            notes=default_notes,
        )
        metadata.history = [
            build_history_entry(
                artifact,
                metadata,
                timestamp=effective_timestamp,
                action="annotated",
            )
        ]

        decorator_lines = format_metadata_decorator(metadata, indent=artifact.indent)
        if not decorator_lines:
            continue
        insertion_index = artifact.start_line - 1
        lines[insertion_index:insertion_index] = decorator_lines
        changed = True

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:54:54.247217+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.035474+00:00 digest=0002e726fdd176050dec9ac0e6cdf3cd90c641f9 last_commit=97cec9a by phzwart",
    ],
)
def _refresh_history_blocks(
    path: Path,
    artifacts: Sequence[CodeArtifact],
    timestamp: datetime | None,
) -> bool:
    updates: list[MetadataUpdate] = []
    effective_timestamp = timestamp or datetime.now(timezone.utc)

    for artifact in artifacts:
        if artifact.decorator is None:
            continue

        metadata = artifact.tags.clone()
        existing_entry = metadata.history[0] if metadata.history else None
        current_digest = compute_digest(metadata)
        stored_digest = extract_digest(existing_entry)

        if stored_digest == current_digest and existing_entry is not None:
            continue

        metadata.history = [
            build_history_entry(
                artifact,
                metadata,
                timestamp=effective_timestamp,
            )
        ]
        updates.append((artifact, metadata))

    if not updates:
        return False

    return update_metadata_blocks(path, updates)
