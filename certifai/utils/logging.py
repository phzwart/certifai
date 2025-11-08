"""Logging utilities for certifai."""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger configured for certifai."""

    logger = logging.getLogger(f"certifai.{name}")
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    return logger
