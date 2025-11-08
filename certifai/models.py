"""Shared data models for the certifai toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.515259+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart

class ScrutinyLevel(str, Enum):
    """Enumeration of supported scrutiny levels."""

    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    # @ai_composed: gpt-5
    # @human_certified: PHZ
    # scrutiny: auto
    # date: 2025-11-08T00:34:45.515259+00:00
    # notes: No obvious issues found.
    # history: 2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart
    
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


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.515259+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart

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

    # @ai_composed: gpt-5
    # @human_certified: PHZ
    # scrutiny: auto
    # date: 2025-11-08T00:34:45.515259+00:00
    # notes: No obvious issues found.
    # history: 2025-11-08T01:35:22.567845+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart
    
    @classmethod
    def from_comment_block(cls, lines: list[str]) -> TagMetadata:
        """Create a metadata object from raw comment lines."""

        metadata = cls()
        for line in lines:
            content = line.lstrip("#").strip()
            if not content:
                continue
            if content.startswith("@"):
                key, _, value = content[1:].partition(":")
                key = key.strip().lower()
                value = value.strip() or None
                if key == "ai_composed":
                    metadata.ai_composed = value
                elif key == "human_certified":
                    metadata.human_certified = value or "pending"
                else:
                    metadata.extras.append(line)
                    continue
            else:
                key, _, value = content.partition(":")
                key = key.strip().lower()
                value = value.strip() or None
                if key == "scrutiny":
                    metadata.scrutiny = ScrutinyLevel.from_string(value)
                elif key == "date":
                    metadata.date = value
                elif key == "notes":
                    metadata.notes = value
                elif key == "history":
                    if value:
                        metadata.history.append(value)
                else:
                    metadata.extras.append(line)
        return metadata

    # @ai_composed: gpt-5
    # @human_certified: PHZ
    # scrutiny: auto
    # date: 2025-11-08T00:34:45.515259+00:00
    # notes: No obvious issues found.
    # history: 2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart
    
    def to_comment_block(self) -> list[str]:
        """Serialize metadata back into a sequence of comment lines."""

        lines: list[str] = []
        if self.ai_composed:
            lines.append(f"# @ai_composed: {self.ai_composed}")
        if self.human_certified:
            lines.append(f"# @human_certified: {self.human_certified}")
        if self.scrutiny:
            lines.append(f"# scrutiny: {self.scrutiny.value}")
        if self.date:
            lines.append(f"# date: {self.date}")
        if self.notes:
            lines.append(f"# notes: {self.notes}")
        for entry in self.history:
            lines.append(f"# history: {entry}")
        lines.extend(self.extras)
        return lines

    # @ai_composed: gpt-5
    # @human_certified: PHZ
    # scrutiny: auto
    # date: 2025-11-08T00:34:45.515259+00:00
    # notes: No obvious issues found.
    # history: 2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart
    
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
        )

    # @ai_composed: gpt-5
    # @human_certified: PHZ
    # scrutiny: auto
    # date: 2025-11-08T00:34:45.515259+00:00
    # notes: No obvious issues found.
    # history: 2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart
    
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
            )
        )

    # @ai_composed: gpt-5
    # @human_certified: PHZ
    # scrutiny: auto
    # date: 2025-11-08T00:34:45.515259+00:00
    # notes: No obvious issues found.
    # history: 2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart
    
    @property
    def is_pending_certification(self) -> bool:
        """Return True if the artifact still requires human certification."""

        return not self.human_certified or self.human_certified.lower() == "pending"


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.515259+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart

@dataclass(slots=True)
class CommentBlock:
    """Represents a contiguous comment block preceding an artifact."""

    start_line: int
    end_line: int
    lines: list[str]


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.515259+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:22:48.177963+00:00 digest=194cdcdbb9a1aa5a6aa59cc2100e953ceee541d3 last_commit=f07d0d9 by phzwart

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
    comment_block: CommentBlock | None
