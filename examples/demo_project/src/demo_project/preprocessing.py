"""Example preprocessing helpers."""

from __future__ import annotations

from typing import Iterable, Sequence


# @ai_composed: gpt-4
# @human_certified: Mentor
# scrutiny: auto
# history: 2025-11-08T01:35:22.538537+00:00 digest=92e5fbef3953cdda693bf8143456c9cfdffcf962 last_commit=f07d0d9 by phzwart

def normalize_range(values: Sequence[float]) -> list[float]:
    """Normalize values to the [0, 1] range."""

    if not values:
        return []
    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        return [0.0 for _ in values]
    scale = max_value - min_value
    return [(value - min_value) / scale for value in values]


# @ai_composed: human-crafted
# @human_certified: Reviewer2
# scrutiny: medium
# date: 2025-09-01
# notes: Verified during onboarding workshop
# history: 2025-11-08T00:54:54.624037+00:00 digest=4b76b894f594dcae5564a7d8fa608e6b32b32e4e last_commit=f07d0d9 by phzwart

def bucketize(values: Iterable[float], threshold: float = 0.5) -> list[int]:
    """Convert continuous values to binary classes."""

    return [int(value >= threshold) for value in values]
