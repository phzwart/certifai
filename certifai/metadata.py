"""Utilities for mutating metadata decorators in source files."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Tuple

from .decorators import certifai, format_metadata_decorator
from .models import CodeArtifact, TagMetadata


MetadataUpdate = Tuple[CodeArtifact, TagMetadata]

__all__ = ["MetadataUpdate", "update_metadata_blocks", "remove_metadata_blocks", "insert_metadata_block"]


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:54:53.797040+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.109022+00:00 digest=32308dcb6c7133adac6a4b400ee1a4fdea89a731 last_commit=97cec9a by phzwart",
    ],
)
def update_metadata_blocks(path: Path, updates: Sequence[MetadataUpdate]) -> bool:
    """Apply updated metadata decorators for the provided artifacts.

    The updates collection should contain ``(artifact, metadata)`` pairs. Each
    metadata instance will be serialized and replace the existing provenance
    decorator preceding the target artifact. Updates are applied in reverse
    order of appearance to avoid shifting subsequent offsets.
    """

    if not updates:
        return False

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    changed = False

    for artifact, metadata in sorted(
        updates, key=lambda item: item[0].start_line, reverse=True
    ):
        if artifact.decorator is None:
            continue
        decorator_lines = format_metadata_decorator(metadata, indent=artifact.indent)
        start_idx = artifact.decorator.start_line - 1
        end_idx = artifact.decorator.end_line
        lines[start_idx:end_idx] = decorator_lines
        changed = True

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def remove_metadata_blocks(path: Path, artifacts: Sequence[CodeArtifact]) -> bool:
    """Completely remove ``@certifai`` decorators for finalized artifacts.

    This helper is used during Stage 3 (finalization) to clean up source files
    while retaining provenance data in the registry.
    """

    if not artifacts:
        return False

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    changed = False

    # Process in reverse order to avoid shifting subsequent offsets
    for artifact in sorted(artifacts, key=lambda item: item.start_line, reverse=True):
        decorator = artifact.decorator
        if decorator is None:
            continue

        start_idx = decorator.start_line - 1
        end_idx = decorator.end_line
        del lines[start_idx:end_idx]
        changed = True

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return changed


def insert_metadata_block(path: Path, artifact: CodeArtifact, metadata: TagMetadata) -> bool:
    """Insert an @certifai decorator for the provided artifact.

    Parameters
    ----------
    path:
        Path to the Python source file containing the artifact.
    artifact:
        Artifact describing where the decorator should be inserted.
    metadata:
        Metadata to serialize into the decorator.

    Returns
    -------
    bool
        ``True`` if the file was modified, ``False`` otherwise.
    """

    decorator_lines = format_metadata_decorator(metadata, indent=artifact.indent)
    if not decorator_lines:
        return False

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    insertion_index = artifact.start_line - 1
    lines[insertion_index:insertion_index] = decorator_lines
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True
