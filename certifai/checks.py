"""Validation helpers to reconcile registry entries with source code."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .digest import compute_artifact_digest
from .metadata import MetadataUpdate, update_metadata_blocks
from .models import ScrutinyLevel, TagMetadata
from .parser import parse_file
from .registry import RegistryEntry, load_registry, save_registry
from .utils.logging import get_logger

LOGGER = get_logger("checks")


def _lookup_artifacts(path: Path) -> Dict[str, CodeArtifact]:
    artifacts = parse_file(path)
    return {artifact.name: artifact for artifact in artifacts}


def _metadata_from_entry(entry: RegistryEntry) -> TagMetadata:
    metadata = TagMetadata(
        ai_composed=entry.ai_composed,
        human_certified=entry.human_certified or "pending",
        notes=entry.notes,
        history=list(entry.history),
        date=entry.date,
    )
    if entry.scrutiny:
        metadata.scrutiny = ScrutinyLevel.from_string(entry.scrutiny)
    metadata.done = False
    return metadata


def reconcile_registry(registry_root: Path | None = None) -> List[Path]:
    """Ensure finalized artifacts still match the registered digests.

    Returns a list of files that were modified during reconciliation.
    """

    registry = load_registry(registry_root)
    if not registry:
        return []

    updated_files: set[Path] = set()
    for key, entry in list(registry.items()):
        filepath_str, qualified_name = key
        path = Path(filepath_str)
        if not path.exists():
            LOGGER.warning("Registered artifact missing: %s", filepath_str)
            registry.pop(key, None)
            continue

        artifacts = _lookup_artifacts(path)
        artifact = artifacts.get(qualified_name)
        if artifact is None:
            LOGGER.info("Artifact %s removed from %s; clearing registry entry", qualified_name, filepath_str)
            registry.pop(key, None)
            continue

        digest = compute_artifact_digest(artifact)
        if digest == entry.digest:
            continue

        LOGGER.info("Artifact %s in %s changed; reverting to certification state", qualified_name, filepath_str)
        metadata = _metadata_from_entry(entry)
        updates: list[MetadataUpdate] = [(artifact, metadata)]
        if update_metadata_blocks(path, updates):
            registry.pop(key, None)
            updated_files.add(path)
        else:
            LOGGER.warning("Failed to update metadata for %s", filepath_str)

    if updated_files:
        save_registry(registry, registry_root)
    return sorted(updated_files)
