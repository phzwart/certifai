"""Logging utilities for certifai."""

from __future__ import annotations

import logging


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.110788+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:54.566968+00:00 digest=fd63d4c5534a721c68787805da7504e26b91c90e last_commit=f07d0d9 by phzwart

def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger configured for certifai."""

    logger = logging.getLogger(f"certifai.{name}")
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    return logger
