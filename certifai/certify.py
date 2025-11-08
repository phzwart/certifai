"""Certification workflow helpers for reviewers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from .models import CodeArtifact, CommentBlock, ScrutinyLevel, TagMetadata
from .parser import iter_python_files, parse_file
from .utils.logging import get_logger

LOGGER = get_logger("certify")


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


def _rewrite_metadata(
    path: Path,
    artifacts: Sequence[CodeArtifact],
    reviewer: str,
    scrutiny: ScrutinyLevel,
    notes: str | None,
) -> bool:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    changed = False
    timestamp = datetime.now(timezone.utc).isoformat()

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
        metadata.history.append(f"{timestamp} certified by {reviewer} ({scrutiny.value})")
        block_lines = metadata.to_comment_block()
        indented_block = [f"{artifact.indent}{line}" for line in block_lines]
        start_idx = comment_block.start_line - 1
        end_idx = comment_block.end_line
        lines[start_idx:end_idx] = indented_block
        changed = True

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed
