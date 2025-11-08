"""Logging utilities for certifai."""

from __future__ import annotations

import logging


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:46.110788+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:24:35.336078+00:00 digest=437d114b4c08e30c54b076da04aecbbf0eba362f last_commit=f07d0d9 by phzwart

def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger configured for certifai."""

    logger = logging.getLogger(f"certifai.{name}")
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    return logger
