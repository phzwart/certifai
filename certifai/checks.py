"""Validation helpers to reconcile registry entries with source code."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .audit import record_reopening
from .digest import compute_artifact_digest
from .metadata import MetadataUpdate, insert_metadata_block, update_metadata_blocks
from .models import CodeArtifact, TagMetadata
from .parser import parse_file
from .policy import load_policy
from .registry import (
    RegistryEntry,
    archive_registry_entry,
    load_registry,
    save_registry,
)
from .utils.logging import get_logger

LOGGER = get_logger("checks")


def _metadata_from_entry(entry: RegistryEntry) -> TagMetadata:
    """Create minimal Stage 1 metadata when reopening an artifact."""

    return TagMetadata(
        ai_composed=entry.ai_composed,
        reviewers=[],  # Stage 1: pending human review
    )


def reconcile_registry(registry_root: Path | None = None) -> List[Path]:
    """Ensure finalized artifacts still match registered digests.

    When drift is detected this function:
    1. Re-injects a minimal Stage 1 decorator
    2. Archives the previous registry entry
    3. Logs the reopening event for audit tracking

    Returns the list of modified files.
    """

    registry = load_registry(registry_root)
    if not registry:
        return []

    policy = load_policy()
    audit_settings = policy.integrations.audit

    updated_files: set[Path] = set()
    for key, entry in list(registry.items()):
        filepath_str, qualified_name = key
        path = Path(filepath_str)
        if not path.exists():
            LOGGER.warning("Registered artifact missing: %s", filepath_str)
            registry.pop(key, None)
            continue

        artifacts = parse_file(path)
        artifact_map: Dict[str, CodeArtifact] = {artifact.name: artifact for artifact in artifacts}
        artifact = artifact_map.get(qualified_name)
        if artifact is None:
            LOGGER.info("Artifact %s removed from %s; clearing registry entry", qualified_name, filepath_str)
            registry.pop(key, None)
            continue

        digest = compute_artifact_digest(artifact)
        if digest == entry.digest:
            continue

        LOGGER.info("Artifact %s in %s changed; reopening for review", qualified_name, filepath_str)
        metadata = _metadata_from_entry(entry)
        updates: list[MetadataUpdate] = [(artifact, metadata)]
        if update_metadata_blocks(path, updates):
            archive_registry_entry(
                registry,
                key,
                entry,
                reason="code_changed",
                old_digest=entry.digest,
                new_digest=digest,
            )
            registry.pop(key, None)
            updated_files.add(path)
            record_reopening(
                audit_settings,
                artifact,
                "digest_mismatch",
                old_digest=entry.digest,
                new_digest=digest,
            )
        elif insert_metadata_block(path, artifact, metadata):
            archive_registry_entry(
                registry,
                key,
                entry,
                reason="code_changed",
                old_digest=entry.digest,
                new_digest=digest,
            )
            registry.pop(key, None)
            updated_files.add(path)
            record_reopening(
                audit_settings,
                artifact,
                "digest_mismatch",
                old_digest=entry.digest,
                new_digest=digest,
            )
        else:
            LOGGER.warning("Failed to update metadata for %s", filepath_str)

    if updated_files:
        save_registry(registry, registry_root)
    return sorted(updated_files)
