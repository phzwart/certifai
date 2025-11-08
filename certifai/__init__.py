"""Top-level package for certifai."""

from __future__ import annotations

from .provenance import annotate_paths, enforce_policy
from .report import CoverageSummary, build_summary

__all__ = [
    "__version__",
    "annotate_paths",
    "enforce_policy",
    "CoverageSummary",
    "build_summary",
]

__version__ = "0.1.5"
