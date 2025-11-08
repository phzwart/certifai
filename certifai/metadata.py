"""Utilities for mutating metadata comment blocks in source files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence, Tuple

from .models import CodeArtifact, TagMetadata


MetadataUpdate = Tuple[CodeArtifact, TagMetadata]


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:54:53.797040+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:53.797040+00:00 digest=4ea0e501803e22523823c1cd7f86b56aa0925017 annotated last_commit=unknown

def update_metadata_blocks(path: Path, updates: Sequence[MetadataUpdate]) -> bool:
    """Apply updated metadata blocks for the provided artifacts.

    The updates collection should contain ``(artifact, metadata)`` pairs. Each
    metadata instance will be serialized and replace the existing comment block
    preceding the target artifact. Updates are applied in reverse order of
    appearance to avoid shifting subsequent offsets.
    """

    if not updates:
        return False

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    changed = False

    for artifact, metadata in sorted(
        updates, key=lambda item: item[0].start_line, reverse=True
    ):
        if artifact.comment_block is None:
            continue
        block_lines = metadata.to_comment_block()
        indented_block = [f"{artifact.indent}{line}" for line in block_lines]
        indented_block.append(artifact.indent)

        start_idx = artifact.comment_block.start_line - 1
        end_idx = artifact.comment_block.end_line
        lines[start_idx:end_idx] = indented_block
        changed = True

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed
