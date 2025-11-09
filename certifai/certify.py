"""Certification workflow helpers for reviewers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from .decorators import certifai
from .history import build_history_entry
from .metadata import MetadataUpdate, update_metadata_blocks
from .models import CodeArtifact, ReviewerInfo, ScrutinyLevel, TagMetadata  # pyright: ignore[reportUnusedImport]
from .parser import iter_python_files, parse_file
from .utils.logging import get_logger
from .policy import AgentPermission, AgentSettings, PolicyConfig

LOGGER = get_logger("certify")


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.964853+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:06:25.558375+00:00 digest=da44edfbd98bb6a3cf9a4b24339b948f4cfeca9c last_commit=f07d0d9 by phzwart",
    ],
)
def certify(
    paths: Iterable[Path | str],
    reviewer: str,
    scrutiny: str,
    *,
    notes: str | None = None,
    include_existing: bool = False,
    reviewer_kind: str = "human",
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
        if _rewrite_metadata_human(path, updates, reviewer, level, notes):
            refreshed = parse_file(path)
            lookup = {(artifact.name, artifact.lineno): artifact for artifact in refreshed}
            lookup_by_name = {artifact.name: artifact for artifact in refreshed}
            for artifact in updates:
                key = (artifact.name, artifact.lineno)
                if key in lookup:
                    updated_artifacts.append(lookup[key])
                elif artifact.name in lookup_by_name:
                    updated_artifacts.append(lookup_by_name[artifact.name])

    return updated_artifacts


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.964853+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:06:25.558375+00:00 digest=da44edfbd98bb6a3cf9a4b24339b948f4cfeca9c last_commit=f07d0d9 by phzwart",
    ],
)
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
    return certify(target_paths, reviewer, level.value, include_existing=False, reviewer_kind="human")


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.964853+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:06:25.558375+00:00 digest=da44edfbd98bb6a3cf9a4b24339b948f4cfeca9c last_commit=f07d0d9 by phzwart",
    ],
)
def certify_agent(
    paths: Iterable[Path | str],
    agent_id: str,
    scrutiny: str,
    *,
    notes: str | None = None,
    include_existing: bool = False,
) -> Sequence[CodeArtifact]:
    """Mark selected artifacts as reviewed by an automated agent."""

    resolved_paths = list(iter_python_files(paths))
    updated_artifacts: list[CodeArtifact] = []
    level = ScrutinyLevel.from_string(scrutiny)
    if level is None:
        raise ValueError(f"Unsupported scrutiny level: {scrutiny}")

    timestamp_dt = datetime.now(timezone.utc)
    timestamp = timestamp_dt.isoformat()

    for path in resolved_paths:
        LOGGER.debug("Agent %s certifying artifacts in %s", agent_id, path)
        artifacts = list(parse_file(path))
        updates = [
            artifact
            for artifact in artifacts
            if include_existing or artifact.tags.is_pending_certification
        ]
        if not updates:
            continue
        updates_payload: list[MetadataUpdate] = []
        for artifact in updates:
            decorator_block = artifact.decorator
            if decorator_block is None:
                LOGGER.warning(
                    "Artifact %s at %s lacks metadata decorator; skipping agent certification",
                    artifact.name,
                    path,
                )
                continue
            metadata = artifact.tags.clone()
            metadata.agent_certified = agent_id
            metadata.scrutiny = level
            metadata.date = timestamp
            if notes:
                metadata.notes = notes
            metadata.done = False
            metadata.reviewers.append(
                ReviewerInfo(
                    kind="agent",
                    id=agent_id,
                    scrutiny=level,
                    notes=notes,
                    timestamp=timestamp,
                )
            )
            metadata.history = [
                build_history_entry(
                    artifact,
                    metadata,
                    timestamp=timestamp_dt,
                    action=f"agent {agent_id} certified ({level.value})",
                )
            ]
            updates_payload.append((artifact, metadata))

        if not updates_payload:
            continue

        if update_metadata_blocks(path, updates_payload):
            refreshed = parse_file(path)
            lookup = {(artifact.name, artifact.lineno): artifact for artifact in refreshed}
            lookup_by_name = {artifact.name: artifact for artifact in refreshed}
            for artifact in updates:
                key = (artifact.name, artifact.lineno)
                if key in lookup:
                    updated_artifacts.append(lookup[key])
                elif artifact.name in lookup_by_name:
                    updated_artifacts.append(lookup_by_name[artifact.name])

    return updated_artifacts


def _rewrite_metadata_human(
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
        decorator_block = artifact.decorator
        if decorator_block is None:
            LOGGER.warning(
                "Artifact %s at %s lacks metadata decorator; skipping certification",
                artifact.name,
                path,
            )
            continue
        metadata = artifact.tags.clone()
        metadata.done = False
        metadata.add_reviewer(
            ReviewerInfo(
                kind="human",
                id=reviewer,
                scrutiny=scrutiny,
                notes=notes,
                timestamp=timestamp,
            )
        )
        metadata.human_certified = reviewer
        metadata.scrutiny = scrutiny
        metadata.date = timestamp
        if notes:
            metadata.notes = notes
        metadata.done = False
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


def _rewrite_metadata_agent(
    path: Path,
    artifacts: Sequence[CodeArtifact],
    agent_id: str,
    scrutiny: ScrutinyLevel,
    notes: str | None,
    permission: AgentPermission,
) -> bool:
    timestamp_dt = datetime.now(timezone.utc)
    timestamp = timestamp_dt.isoformat()

    updates_payload: list[MetadataUpdate] = []

    for artifact in artifacts:
        decorator_block = artifact.decorator
        if decorator_block is None:
            LOGGER.warning(
                "Artifact %s at %s lacks metadata decorator; skipping agent certification",
                artifact.name,
                path,
            )
            continue
        metadata = artifact.tags.clone()
        metadata.agent_certified = agent_id
        metadata.scrutiny = scrutiny
        metadata.date = timestamp
        if notes:
            metadata.notes = notes
        metadata.done = metadata.done and permission.allow_finalize
        metadata.history = [
            build_history_entry(
                artifact,
                metadata,
                timestamp=timestamp_dt,
                action=f"certified by agent {agent_id} ({scrutiny.value})",
            )
        ]
        metadata.add_reviewer(
            ReviewerInfo(
                kind="agent",
                id=agent_id,
                scrutiny=scrutiny,
                notes=notes,
                timestamp=timestamp,
            )
        )
        updates_payload.append((artifact, metadata))

    if not updates_payload:
        return False

    return update_metadata_blocks(path, updates_payload)


def _resolve_agent_permission(settings: AgentSettings, agent_id: str) -> AgentPermission:
    if not settings.enabled:
        raise ValueError(f"Agent certification disabled for {agent_id}")
    for permission in settings.reviewers:
        if permission.id == agent_id:
            return permission
    raise ValueError(f"Agent {agent_id} is not permitted to certify")


def _resolve_agent_scrutiny(scrutiny: str | None, permission: AgentPermission) -> ScrutinyLevel:
    level = ScrutinyLevel.from_string(scrutiny) if scrutiny else None
    if level is None and permission.max_scrutiny:
        level = ScrutinyLevel.from_string(permission.max_scrutiny)
    if level is None:
        level = ScrutinyLevel.AUTO

    if permission.max_scrutiny:
        max_level = ScrutinyLevel.from_string(permission.max_scrutiny)
        if max_level and not _scrutiny_within(level, max_level):
            raise ValueError(
                f"Agent {permission.id} is limited to {permission.max_scrutiny} scrutiny"
            )
    return level


def _scrutiny_within(level: ScrutinyLevel, limit: ScrutinyLevel) -> bool:
    order = [ScrutinyLevel.AUTO, ScrutinyLevel.LOW, ScrutinyLevel.MEDIUM, ScrutinyLevel.HIGH]
    try:
        return order.index(level) <= order.index(limit)
    except ValueError:
        return False
