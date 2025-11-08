"""Provenance tagging and enforcement utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from .history import build_history_entry, compute_digest, extract_digest
from .metadata import MetadataUpdate, update_metadata_blocks
from .models import CodeArtifact, ScrutinyLevel, TagMetadata
from .parser import iter_python_files, parse_file
from .policy import DEFAULT_POLICY, PolicyConfig
from .utils.logging import get_logger

LOGGER = get_logger("provenance")


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.918067+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.276596+00:00 digest=ad25a9fbc9e8fef45e0df3e7c9f4fc1cbbf9f5a8 last_commit=f07d0d9 by phzwart

@dataclass(slots=True)
class ProvenanceResult:
    """Result of running provenance annotation on a set of files."""

    artifacts: list[CodeArtifact]
    updated_files: list[Path]
    policy_violations: list[str]


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.918067+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.276596+00:00 digest=ad25a9fbc9e8fef45e0df3e7c9f4fc1cbbf9f5a8 last_commit=f07d0d9 by phzwart

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

    for path in resolved_paths:
        artifacts = list(parse_file(path))
        needs_update = [artifact for artifact in artifacts if not artifact.tags.has_metadata]
        file_changed = False

        if needs_update:
            LOGGER.debug("Annotating %s with %d metadata blocks", path, len(needs_update))
            if _insert_metadata_blocks(
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

    active_policy = policy or DEFAULT_POLICY
    violations = enforce_policy(collected_artifacts, active_policy)

    return ProvenanceResult(
        artifacts=collected_artifacts,
        updated_files=sorted(updated_paths),
        policy_violations=violations,
    )


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.918067+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.276596+00:00 digest=ad25a9fbc9e8fef45e0df3e7c9f4fc1cbbf9f5a8 last_commit=f07d0d9 by phzwart

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
        total = len(artifacts)
        if total:
            certified = sum(
                1
                for artifact in artifacts
                if artifact.tags.human_certified
                and artifact.tags.human_certified.lower() != "pending"
            )
            coverage = certified / total
            if coverage < policy.enforcement.min_coverage:
                violations.append(
                    f"Coverage {coverage:.2%} below required {policy.enforcement.min_coverage:.0%}"
                )
    return violations


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.918067+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.276596+00:00 digest=ad25a9fbc9e8fef45e0df3e7c9f4fc1cbbf9f5a8 last_commit=f07d0d9 by phzwart

def _insert_metadata_blocks(
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

        block = metadata.to_comment_block()
        if not block:
            continue
        indented_block = [f"{artifact.indent}{line}" for line in block]
        insertion_index = artifact.start_line - 1
        # Avoid duplicating existing blank line: ensure trailing newline between block and code
        indented_block.append(artifact.indent)
        lines[insertion_index:insertion_index] = indented_block
        changed = True

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:54:54.247217+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.247217+00:00 digest=39ce520a0b7bafe0ce44844476d4b4cf86f29900 annotated last_commit=uncommitted

def _refresh_history_blocks(
    path: Path,
    artifacts: Sequence[CodeArtifact],
    timestamp: datetime | None,
) -> bool:
    updates: list[MetadataUpdate] = []
    effective_timestamp = timestamp or datetime.now(timezone.utc)

    for artifact in artifacts:
        if artifact.comment_block is None:
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
