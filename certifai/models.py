"""Shared data models for the certifai toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from certifai.decorators import certifai
else:
    def certifai(**_: object) -> Callable[[object], object]:
        def _decorator(target: object) -> object:
            return target

        return _decorator

@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.515259+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart",
    ],
)
class ScrutinyLevel(str, Enum):
    """Enumeration of supported scrutiny levels."""

    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.515259+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart",
        ],
    )
    @classmethod
    def from_string(cls, value: str | None) -> ScrutinyLevel | None:
        """Normalize a string into a scrutiny level if recognized."""

        if value is None:
            return None
        normalized = value.strip().lower()
        for candidate in cls:
            if candidate.value == normalized:
                return candidate
        return None


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.515259+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart",
    ],
)
@dataclass(slots=True)
class TagMetadata:
    """Structured representation of provenance metadata associated with code."""

    ai_composed: str | None = None
    human_certified: str | None = None
    scrutiny: ScrutinyLevel | None = None
    date: str | None = None
    notes: str | None = None
    history: list[str] = field(default_factory=list)
    extras: list[str] = field(default_factory=list)
    done: bool = False

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.515259+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:35:22.567845+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart",
        ],
    )
    @classmethod
    def from_decorator_kwargs(
        cls,
        *,
        ai_composed: str | None = None,
        human_certified: str | None = None,
        scrutiny: ScrutinyLevel | str | None = None,
        date: str | None = None,
        notes: str | None = None,
        history: Sequence[str] | None = None,
        extras: Sequence[str] | None = None,
        done: bool | str | None = None,
    ) -> TagMetadata:
        metadata = cls()
        metadata.ai_composed = ai_composed
        metadata.human_certified = human_certified or ("pending" if human_certified == "" else human_certified)
        if isinstance(scrutiny, ScrutinyLevel):
            metadata.scrutiny = scrutiny
        else:
            metadata.scrutiny = ScrutinyLevel.from_string(scrutiny) if isinstance(scrutiny, str) else None
        metadata.date = date
        metadata.notes = notes
        if history:
            metadata.history = list(history)
        if extras:
            metadata.extras = list(extras)
        if isinstance(done, bool):
            metadata.done = done
        elif isinstance(done, str):
            metadata.done = done.strip().lower() in {"true", "1", "yes"}
        return metadata

    def to_decorator_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self.ai_composed:
            payload["ai_composed"] = self.ai_composed
        if self.human_certified:
            payload["human_certified"] = self.human_certified
        if self.scrutiny:
            payload["scrutiny"] = self.scrutiny.value
        if self.date:
            payload["date"] = self.date
        if self.notes:
            payload["notes"] = self.notes
        if self.done:
            payload["done"] = True
        if self.history:
            payload["history"] = list(self.history)
        if self.extras:
            payload["extras"] = list(self.extras)
        return payload

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.515259+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart",
        ],
    )
    def clone(self) -> TagMetadata:
        """Return a deep-ish copy suitable for mutation."""

        return TagMetadata(
            ai_composed=self.ai_composed,
            human_certified=self.human_certified,
            scrutiny=self.scrutiny,
            date=self.date,
            notes=self.notes,
            history=list(self.history),
            extras=list(self.extras),
            done=self.done,
        )

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.515259+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart",
        ],
    )
    @property
    def has_metadata(self) -> bool:
        """Return True when any primary metadata field is populated."""

        return any(
            value
            for value in (
                self.ai_composed,
                self.human_certified,
                self.scrutiny,
                self.date,
                self.notes,
                self.done,
            )
        )

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.515259+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart",
        ],
    )
    @property
    def is_pending_certification(self) -> bool:
        """Return True if the artifact still requires human certification."""

        if self.done:
            return False
        return not self.human_certified or self.human_certified.lower() == "pending"


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.515259+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart",
    ],
)
@dataclass(slots=True)
class DecoratorBlock:
    """Represents a provenance decorator applied to an artifact."""

    start_line: int
    end_line: int
    lines: list[str]


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.515259+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart",
    ],
)
@dataclass(slots=True)
class CodeArtifact:
    """Represents a function or class discovered in a Python module."""

    name: str
    artifact_type: str
    filepath: Path
    lineno: int
    end_lineno: int | None
    start_line: int
    tags: TagMetadata
    indent: str
    decorator: DecoratorBlock | None
