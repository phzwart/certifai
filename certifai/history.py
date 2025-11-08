"""Helpers for building provenance history comment entries."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

from .models import CodeArtifact, TagMetadata
from .utils.git import describe_line, get_repo

_DIGEST_PATTERN = re.compile(r"digest=([0-9a-f]{40})")


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:54:54.476559+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.032195+00:00 digest=9e5b7138788bb22a4cdc4ebbce221f1b187665f2 last_commit=97cec9a by phzwart

def compute_digest(metadata: TagMetadata) -> str:
    """Return a stable digest representing the metadata content."""

    parts: list[str] = [
        metadata.ai_composed or "",
        metadata.human_certified or "",
        metadata.scrutiny.value if metadata.scrutiny else "",
        metadata.date or "",
        metadata.notes or "",
        "\n".join(metadata.extras),
    ]
    joined = "|".join(parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:54:54.476559+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.032195+00:00 digest=9e5b7138788bb22a4cdc4ebbce221f1b187665f2 last_commit=97cec9a by phzwart

def extract_digest(entry: str | None) -> Optional[str]:
    """Extract the stored digest from a history entry if present."""

    if not entry:
        return None
    match = _DIGEST_PATTERN.search(entry)
    if match:
        return match.group(1)
    return None


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:54:54.476559+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.032195+00:00 digest=9e5b7138788bb22a4cdc4ebbce221f1b187665f2 last_commit=97cec9a by phzwart

def build_history_entry(
    artifact: CodeArtifact,
    metadata: TagMetadata,
    *,
    timestamp: datetime | None = None,
    action: str | None = None,
) -> str:
    """Construct a single history entry describing metadata provenance."""

    digest = compute_digest(metadata)
    ts = (timestamp or datetime.now(timezone.utc)).isoformat()
    segments = [ts, f"digest={digest}"]
    if action:
        segments.append(action)

    commit_info = describe_line(artifact.filepath, artifact.lineno)
    if commit_info:
        segments.append(
            f"last_commit={commit_info['commit'][:7]} by {commit_info['author']}"
        )
    else:
        repo = get_repo(artifact.filepath)
        if repo is not None and repo.is_dirty(path=str(artifact.filepath)):
            segments.append("last_commit=uncommitted")
        else:
            segments.append("last_commit=unknown")

    return " ".join(segments)
