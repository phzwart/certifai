"""Finalization workflow for certifai artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from .digest import compute_artifact_digest
from .metadata import MetadataUpdate, update_metadata_blocks
from .models import CodeArtifact, TagMetadata
from .parser import iter_python_files, parse_file
from .registry import RegistryEntry, load_registry, registry_key, save_registry, update_registry
from .utils.logging import get_logger

LOGGER = get_logger("finalize")


def _finalizable(artifact: CodeArtifact) -> bool:
    if artifact.tags.done:
        return False
    if not artifact.tags.human_certified or artifact.tags.human_certified.lower() == "pending":
        return False
    return True


def _finalized_metadata(original: TagMetadata) -> TagMetadata:
    metadata = original.clone()
    metadata.done = True
    # Trim inline metadata to the essentials; detailed history moves to registry.
    metadata.notes = None
    metadata.history = []
    metadata.date = metadata.date or datetime.now(timezone.utc).isoformat()
    return metadata


def finalize(paths: Iterable[Path | str], *, registry_root: Path | None = None) -> Sequence[CodeArtifact]:
    """Finalize certified artifacts and record them in the registry."""

    registry = load_registry(registry_root)
    resolved_paths = list(iter_python_files(paths))
    finalized: list[CodeArtifact] = []
    now = datetime.now(timezone.utc)

    for path in resolved_paths:
        artifacts = list(parse_file(path))
        updates: list[MetadataUpdate] = []
        registry_updates: list[tuple[CodeArtifact, RegistryEntry]] = []

        for artifact in artifacts:
            if not _finalizable(artifact):
                continue
            digest = compute_artifact_digest(artifact)
            metadata = _finalized_metadata(artifact.tags)
            entry = RegistryEntry.from_artifact(artifact, artifact.tags, digest, timestamp=now)
            registry_updates.append((artifact, entry))
            updates.append((artifact, metadata))

        if not updates:
            continue

        if update_metadata_blocks(path, updates):
            finalized.extend([item[0] for item in updates])
            update_registry(registry, registry_updates)
        else:
            LOGGER.warning("Failed to update metadata blocks for %s", path)

    if finalized:
        save_registry(registry, registry_root)
    return finalized
