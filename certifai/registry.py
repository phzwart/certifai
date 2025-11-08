"""Persistence helpers for finalized certifai artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Tuple

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
        )


def _registry_path(root: Path | None = None) -> Path:
    base = Path.cwd() if root is None else root
    return base / _REGISTRY_DIR / _REGISTRY_FILE


def load_registry(root: Path | None = None) -> Dict[Tuple[str, str], RegistryEntry]:
    path = _registry_path(root)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    entries: Dict[Tuple[str, str], RegistryEntry] = {}
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
        )
        entries[(entry.filepath, entry.qualified_name)] = entry
    return entries


def save_registry(entries: Dict[Tuple[str, str], RegistryEntry], root: Path | None = None) -> None:
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
            }
            for entry in sorted(entries.values(), key=lambda item: (item.filepath, item.qualified_name))
        ]
    }
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def registry_key(artifact: CodeArtifact) -> Tuple[str, str]:
    return str(artifact.filepath), artifact.name


def update_registry(
    registry: Dict[Tuple[str, str], RegistryEntry],
    artifacts: Iterable[Tuple[CodeArtifact, RegistryEntry]],
) -> None:
    for artifact, entry in artifacts:
        registry[registry_key(artifact)] = entry


def remove_from_registry(
    registry: Dict[Tuple[str, str], RegistryEntry],
    artifacts: Iterable[CodeArtifact],
) -> None:
    for artifact in artifacts:
        registry.pop(registry_key(artifact), None)
