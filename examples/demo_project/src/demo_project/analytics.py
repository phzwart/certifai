"""Example analytics functions demonstrating certifai metadata."""

from __future__ import annotations

from statistics import mean
from typing import Iterable

from certifai.decorators import certifai


def compute_accuracy(predictions: Iterable[int], labels: Iterable[int]) -> float:
    """Return simple classification accuracy.

    This function represents Stage 3: provenance has been finalized and lives in
    `.certifai/registry.yml`, so no `@certifai` decorator remains in source.
    """

    preds = list(predictions)
    actuals = list(labels)
    if len(preds) != len(actuals):
        raise ValueError("Prediction and label lengths differ")
    matches = sum(1 for pred, actual in zip(preds, actuals, strict=True) if pred == actual)
    return matches / len(preds) if preds else 0.0


@certifai(
    ai_composed="claude-sonnet",
    human_certified="Mentor",
    scrutiny="high",
    date="2025-10-12",
    notes="Benchmarked across synthetic data set",
    history=[
        "2025-11-08T00:54:54.656421+00:00 digest=60d58c981a4e5164c022bddef297273430bd2413 last_commit=f07d0d9 by phzwart",
    ],
)
def compute_macro_f1(scores: Iterable[tuple[float, float]]) -> float:
    """Compute macro-averaged F1 score from (precision, recall) tuples."""

    values = list(scores)
    f1_values = []
    for precision, recall in values:
        if precision + recall == 0:
            f1_values.append(0.0)
        else:
            f1_values.append(2 * precision * recall / (precision + recall))
    return mean(f1_values) if f1_values else 0.0


@certifai(
    ai_composed="gpt-5",
    human_certified="Mentor",
    scrutiny="auto",
    date="2025-11-08T00:34:46.158086+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.538843+00:00 digest=e7539d7b42f4c6352db89a63f86008163dd4b00d last_commit=f07d0d9 by phzwart",
    ],
)
def summarize_predictions(predictions: Iterable[float]) -> dict[str, float]:
    """Return simple summary metrics for model predictions.

    This function stays in Stage 2 so `certifai finalize` can demonstrate the
    transition to Stage 3 (decorator removal + registry entry).
    """

    values = list(predictions)
    if not values:
        return {"count": 0, "average": 0.0}
    return {"count": len(values), "average": mean(values)}
