"""Utilities for computing normalized digests of code artifacts."""

from __future__ import annotations

import ast
import hashlib
import textwrap
from pathlib import Path

from .models import CodeArtifact


def _artifact_source(artifact: CodeArtifact, *, source: str | None = None) -> str:
    if source is None:
        source = artifact.filepath.read_text(encoding="utf-8")
    lines = source.splitlines()
    start_index = max(artifact.start_line - 1, 0)
    end_line = artifact.end_lineno or artifact.lineno
    last_line_index = min(len(lines), max(end_line, artifact.lineno)) - 1
    snippet = "\n".join(lines[start_index:last_line_index + 1])
    return textwrap.dedent(snippet).strip()


def compute_artifact_digest(artifact: CodeArtifact, *, source: str | None = None) -> str:
    """Return a stable digest representing the artifact's implementation."""

    snippet = _artifact_source(artifact, source=source)
    if not snippet:
        return hashlib.sha256(b"").hexdigest()
    try:
        tree = ast.parse(snippet)
        normalised = ast.dump(tree, include_attributes=False)
    except SyntaxError:
        normalised = snippet
    digest = hashlib.sha256(normalised.encode("utf-8")).hexdigest()
    return digest
