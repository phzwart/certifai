"""Certification workflow helpers for reviewers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from .history import build_history_entry
from .metadata import MetadataUpdate, update_metadata_blocks
from .models import CodeArtifact, CommentBlock, ScrutinyLevel, TagMetadata
from .parser import iter_python_files, parse_file
from .utils.logging import get_logger

LOGGER = get_logger("certify")


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.964853+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.326786+00:00 digest=e402cfa510f6bb78119b6fdaa342147464e60a2b last_commit=f07d0d9 by phzwart

def certify(
    paths: Iterable[Path | str],
    reviewer: str,
    scrutiny: str,
    *,
    notes: str | None = None,
    include_existing: bool = False,
) -> Sequence[CodeArtifact]:
    """Mark selected artifacts as certified by the given reviewer."""

    resolved_paths = list(iter_python_files(paths))
    updated_artifacts: list[CodeArtifact] = []
    level = ScrutinyLevel.from_string(scrutiny)
    if level is None:
        raise ValueError(f"Unsupported scrutiny level: {scrutiny}")

    for path in resolved_paths:
        LOGGER.debug("Certifying artifacts in %s", path)
        artifacts = list(parse_file(path))
        updates = [
            artifact
            for artifact in artifacts
            if include_existing or artifact.tags.is_pending_certification
        ]
        if not updates:
            continue
        if _rewrite_metadata(path, updates, reviewer, level, notes):
            refreshed = parse_file(path)
            lookup = {(artifact.name, artifact.lineno): artifact for artifact in refreshed}
            for artifact in updates:
                key = (artifact.name, artifact.lineno)
                if key in lookup:
                    updated_artifacts.append(lookup[key])

    return updated_artifacts


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.964853+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.326786+00:00 digest=e402cfa510f6bb78119b6fdaa342147464e60a2b last_commit=f07d0d9 by phzwart

def verify_all(
    reviewer: str,
    *,
    scrutiny: str | None = None,
    paths: Iterable[Path | str] | None = None,
) -> Sequence[CodeArtifact]:
    """Mark all pending artifacts as verified by the given reviewer."""

    target_paths: Iterable[Path | str] = paths or [Path.cwd()]
    level = ScrutinyLevel.from_string(scrutiny) if scrutiny else None
    if level is None:
        level = ScrutinyLevel.HIGH
    return certify(target_paths, reviewer, level.value, include_existing=False)


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.964853+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.326786+00:00 digest=e402cfa510f6bb78119b6fdaa342147464e60a2b last_commit=f07d0d9 by phzwart

def _rewrite_metadata(
    path: Path,
    artifacts: Sequence[CodeArtifact],
    reviewer: str,
    scrutiny: ScrutinyLevel,
    notes: str | None,
) -> bool:
    timestamp_dt = datetime.now(timezone.utc)
    timestamp = timestamp_dt.isoformat()

    updates_payload: list[MetadataUpdate] = []

    for artifact in artifacts:
        comment_block = artifact.comment_block
        if comment_block is None:
            LOGGER.warning(
                "Artifact %s at %s lacks metadata block; skipping certification",
                artifact.name,
                path,
            )
            continue
        metadata = artifact.tags.clone()
        metadata.human_certified = reviewer
        metadata.scrutiny = scrutiny
        metadata.date = timestamp
        if notes:
            metadata.notes = notes
        metadata.history = [
            build_history_entry(
                artifact,
                metadata,
                timestamp=timestamp_dt,
                action=f"certified by {reviewer} ({scrutiny.value})",
            )
        ]
        updates_payload.append((artifact, metadata))

    if not updates_payload:
        return False

    return update_metadata_blocks(path, updates_payload)
