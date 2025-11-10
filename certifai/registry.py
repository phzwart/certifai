"""Persistence helpers for finalized certifai artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import yaml

from .models import CodeArtifact, TagMetadata

_REGISTRY_DIR = Path(".certifai")
_REGISTRY_FILE = "registry.yml"


@dataclass(slots=True)
class RegistryEntry:
    filepath: str
    qualified_name: str
    digest: str
    human_certified: str
    scrutiny: str | None
    ai_composed: str | None
    finalized_at: str
    date: str | None = None
    notes: str | None = None
    history: list[str] = field(default_factory=list)
    reviewers: list[dict[str, Any]] = field(default_factory=list)
    lifecycle_history: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_artifact(
        cls,
        artifact: CodeArtifact,
        metadata: TagMetadata,
        digest: str,
        *,
        timestamp: datetime | None = None,
    ) -> "RegistryEntry":
        ts = (timestamp or datetime.now(timezone.utc)).isoformat()
        return cls.from_artifact_full(
            artifact,
            metadata,
            digest,
            timestamp=timestamp,
            include_reviewers=False,
        )

    @classmethod
    def from_artifact_full(
        cls,
        artifact: CodeArtifact,
        metadata: TagMetadata,
        digest: str,
        *,
        timestamp: datetime | None = None,
        include_reviewers: bool = True,
    ) -> "RegistryEntry":
        """Create a registry entry capturing full provenance information."""

        ts = (timestamp or datetime.now(timezone.utc)).isoformat()
        reviewers_data: list[dict[str, Any]] = []
        if include_reviewers and metadata.reviewers:
            for reviewer in metadata.reviewers:
                reviewers_data.append(
                    {
                        "kind": reviewer.kind,
                        "id": reviewer.id,
                        "scrutiny": reviewer.scrutiny.value if reviewer.scrutiny else None,
                        "notes": reviewer.notes,
                        "timestamp": reviewer.timestamp,
                    }
                )

        lifecycle_history = [
            {
                "event": "finalized",
                "timestamp": ts,
                "digest": digest,
            }
        ]

        return cls(
            filepath=str(artifact.filepath),
            qualified_name=artifact.name,
            digest=digest,
            human_certified=metadata.human_certified or "",
            scrutiny=metadata.scrutiny.value if metadata.scrutiny else None,
            ai_composed=metadata.ai_composed,
            finalized_at=ts,
            date=metadata.date,
            notes=metadata.notes,
            history=list(metadata.history),
            reviewers=reviewers_data,
            lifecycle_history=lifecycle_history,
        )


class RegistryStore(dict[Tuple[str, str], RegistryEntry]):
    """Mutable mapping of active registry entries with archival history."""

    __slots__ = ("history",)

    def __init__(
        self,
        *args: object,
        history: List[dict[str, Any]] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.history: List[dict[str, Any]] = history or []


def _registry_path(root: Path | None = None) -> Path:
    base = Path.cwd() if root is None else root
    return base / _REGISTRY_DIR / _REGISTRY_FILE


def load_registry(root: Path | None = None) -> RegistryStore:
    path = _registry_path(root)
    if not path.exists():
        return RegistryStore()
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    history = raw.get("history", []) or []
    store = RegistryStore(history=history)
    for item in raw.get("artifacts", []):
        entry = RegistryEntry(
            filepath=item["filepath"],
            qualified_name=item["qualified_name"],
            digest=item["digest"],
            human_certified=item.get("human_certified", ""),
            scrutiny=item.get("scrutiny"),
            ai_composed=item.get("ai_composed"),
            finalized_at=item["finalized_at"],
            date=item.get("date"),
            notes=item.get("notes"),
            history=item.get("history", []) or [],
            reviewers=item.get("reviewers", []) or [],
            lifecycle_history=item.get("lifecycle_history", []) or [],
        )
        store[(entry.filepath, entry.qualified_name)] = entry
    return store


def save_registry(registry: RegistryStore, root: Path | None = None) -> None:
    path = _registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifacts": [
            {
                "filepath": entry.filepath,
                "qualified_name": entry.qualified_name,
                "digest": entry.digest,
                "human_certified": entry.human_certified,
                "scrutiny": entry.scrutiny,
                "ai_composed": entry.ai_composed,
                "finalized_at": entry.finalized_at,
                "date": entry.date,
                "notes": entry.notes,
                "history": entry.history,
                "reviewers": entry.reviewers,
                "lifecycle_history": entry.lifecycle_history,
            }
            for entry in sorted(registry.values(), key=lambda item: (item.filepath, item.qualified_name))
        ]
    }
    if registry.history:
        payload["history"] = list(registry.history)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, default_flow_style=False)


def append_lifecycle_event(
    entry: RegistryEntry,
    event: str,
    *,
    timestamp: datetime | None = None,
    **kwargs: Any,
) -> None:
    """Append an event to the lifecycle history for a registry entry."""

    ts = (timestamp or datetime.now(timezone.utc)).isoformat()
    payload: dict[str, Any] = {"event": event, "timestamp": ts}
    if kwargs:
        payload.update(kwargs)
    entry.lifecycle_history.append(payload)


def registry_key(artifact: CodeArtifact) -> Tuple[str, str]:
    return str(artifact.filepath), artifact.name


def update_registry(
    registry: RegistryStore,
    artifacts: Iterable[Tuple[CodeArtifact, RegistryEntry]],
) -> None:
    for artifact, entry in artifacts:
        registry[registry_key(artifact)] = entry


def remove_from_registry(
    registry: RegistryStore,
    artifacts: Iterable[CodeArtifact],
) -> None:
    for artifact in artifacts:
        registry.pop(registry_key(artifact), None)


def archive_registry_entry(
    registry: RegistryStore,
    key: Tuple[str, str],
    entry: RegistryEntry,
    *,
    reason: str,
    old_digest: str | None,
    new_digest: str | None,
    timestamp: datetime | None = None,
) -> None:
    """Archive an entry into the registry history and record lifecycle changes."""

    append_lifecycle_event(
        entry,
        "reopened",
        timestamp=timestamp,
        reason=reason,
        old_digest=old_digest,
        new_digest=new_digest,
    )

    archived_at = (timestamp or datetime.now(timezone.utc)).isoformat()
    archive_record = {
        "filepath": entry.filepath,
        "qualified_name": entry.qualified_name,
        "archived_at": archived_at,
        "reason": reason,
        "old_digest": old_digest,
        "new_digest": new_digest,
        "entry": asdict(entry),
    }
    registry.history.append(archive_record)
