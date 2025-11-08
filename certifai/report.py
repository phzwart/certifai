"""Reporting utilities for certifai certification coverage."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .models import CodeArtifact, ScrutinyLevel
from .parser import iter_python_files, parse_file


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.021164+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.386718+00:00 digest=9672b7ccb6fdc538183b7ae9dc19031575a2b0bc last_commit=f07d0d9 by phzwart

@dataclass(slots=True)
class CoverageSummary:
    """A structured summary of certification coverage metrics."""

    artifacts: Sequence[CodeArtifact]
    total_functions: int
    ai_composed: int
    human_certified: int
    pending_review: int
    scrutiny_counts: Mapping[str, int]

    # @ai_composed: gpt-5
    # @human_certified: pending
    # scrutiny: auto
    # date: 2025-11-08T00:34:46.021164+00:00
    # notes: bulk annotation
    # history: 2025-11-08T00:54:54.386718+00:00 digest=9672b7ccb6fdc538183b7ae9dc19031575a2b0bc last_commit=f07d0d9 by phzwart
    
    @property
    def coverage_ratio(self) -> float:
        """Return certified-to-total coverage ratio."""

        if self.total_functions == 0:
            return 0.0
        return self.human_certified / self.total_functions

    # @ai_composed: gpt-5
    # @human_certified: pending
    # scrutiny: auto
    # date: 2025-11-08T00:34:46.021164+00:00
    # notes: bulk annotation
    # history: 2025-11-08T00:54:54.386718+00:00 digest=9672b7ccb6fdc538183b7ae9dc19031575a2b0bc last_commit=f07d0d9 by phzwart
    
    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the summary."""

        return {
            "total_functions": self.total_functions,
            "ai_composed": self.ai_composed,
            "human_certified": self.human_certified,
            "pending_review": self.pending_review,
            "scrutiny_counts": dict(self.scrutiny_counts),
            "coverage_ratio": self.coverage_ratio,
        }


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.021164+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.386718+00:00 digest=9672b7ccb6fdc538183b7ae9dc19031575a2b0bc last_commit=f07d0d9 by phzwart

def build_summary(paths: Iterable[Path | str]) -> CoverageSummary:
    """Inspect project sources and build a coverage summary."""

    artifacts: list[CodeArtifact] = []
    for path in iter_python_files(paths):
        artifacts.extend(parse_file(path))

    total = len(artifacts)
    ai_composed = sum(
        1
        for artifact in artifacts
        if artifact.tags.ai_composed and artifact.tags.ai_composed.lower() != "pending"
    )
    human_certified = sum(
        1
        for artifact in artifacts
        if not artifact.tags.is_pending_certification
        and artifact.tags.human_certified
        and artifact.tags.human_certified.lower() != "pending"
    )
    pending_review = sum(
        1 for artifact in artifacts if artifact.tags.is_pending_certification
    )
    scrutiny_counter: Counter[str] = Counter()
    for artifact in artifacts:
        level = artifact.tags.scrutiny or ScrutinyLevel.AUTO
        value = level.value if isinstance(level, ScrutinyLevel) else str(level)
        scrutiny_counter[value] += 1

    return CoverageSummary(
        artifacts=artifacts,
        total_functions=total,
        ai_composed=ai_composed,
        human_certified=human_certified,
        pending_review=pending_review,
        scrutiny_counts=dict(scrutiny_counter),
    )


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.021164+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.386718+00:00 digest=9672b7ccb6fdc538183b7ae9dc19031575a2b0bc last_commit=f07d0d9 by phzwart

def emit_text_report(summary: CoverageSummary) -> str:
    """Render a human-readable report for console output."""

    coverage_percent = summary.coverage_ratio * 100
    scrutiny_parts = ", ".join(
        f"{level.title()}: {count}" for level, count in sorted(summary.scrutiny_counts.items())
    )
    lines = [
        f"Total functions: {summary.total_functions}",
        f"AI-composed: {summary.ai_composed}",
        f"Human-certified: {summary.human_certified}",
        f"Pending review: {summary.pending_review}",
        f"Scrutiny levels — {scrutiny_parts}",
        f"Certification coverage: {coverage_percent:.1f}%",
    ]
    return "\n".join(lines)


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.021164+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.386718+00:00 digest=9672b7ccb6fdc538183b7ae9dc19031575a2b0bc last_commit=f07d0d9 by phzwart

def emit_csv_report(summary: CoverageSummary) -> str:
    """Return a CSV representation of the coverage metrics."""

    headers = [
        "total_functions",
        "ai_composed",
        "human_certified",
        "pending_review",
        "coverage_ratio",
    ]
    row = [
        str(summary.total_functions),
        str(summary.ai_composed),
        str(summary.human_certified),
        str(summary.pending_review),
        f"{summary.coverage_ratio:.4f}",
    ]
    csv_lines = [",".join(headers), ",".join(row)]
    return "\n".join(csv_lines)


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.021164+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.386718+00:00 digest=9672b7ccb6fdc538183b7ae9dc19031575a2b0bc last_commit=f07d0d9 by phzwart

def emit_markdown_table(summary: CoverageSummary) -> str:
    """Return a markdown table summarising coverage metrics."""

    header = "| Metric | Value |\n| --- | --- |"
    rows = [
        f"| Total functions | {summary.total_functions} |",
        f"| AI-composed | {summary.ai_composed} |",
        f"| Human-certified | {summary.human_certified} |",
        f"| Pending review | {summary.pending_review} |",
        f"| Coverage | {summary.coverage_ratio * 100:.1f}% |",
    ]
    return "\n".join([header, *rows])


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.021164+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.386718+00:00 digest=9672b7ccb6fdc538183b7ae9dc19031575a2b0bc last_commit=f07d0d9 by phzwart

def github_actions_step() -> str:
    """Return a reusable GitHub Actions snippet for running certifai."""

    return (
        "- name: Run certifai report\n"
        "  run: certifai report --format md . > certifai_report.md\n"
    )
