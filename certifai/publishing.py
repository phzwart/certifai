"""Publishing helpers for certifai reports."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

from .policy import PolicyConfig, PublishingDestination
from .report import build_summary, emit_markdown_table
from .utils.logging import get_logger

LOGGER = get_logger("publishing")


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _publish_to_wiki(destination: PublishingDestination, content: str) -> None:
    target = destination.path
    if not target:
        raise ValueError("Wiki destination requires 'path'")
    path = Path(target)
    LOGGER.debug("Writing wiki report to %s", path)
    _write_file(path, content)


def _publish_to_docs(destination: PublishingDestination, content: str) -> None:
    target = destination.path or "docs/certifai-report.md"
    branch = destination.branch
    path = Path(target)
    LOGGER.debug("Writing docs report to %s", path)
    _write_file(path, content)
    if branch:
        subprocess.run(["git", "add", str(path)], check=False)


def _publish_to_file(destination: PublishingDestination, content: str) -> None:
    target = destination.path
    if not target:
        raise ValueError("File destination requires 'path'")
    path = Path(target)
    LOGGER.debug("Writing report to %s", path)
    _write_file(path, content)


DESTINATION_HANDLERS = {
    "wiki": _publish_to_wiki,
    "docs": _publish_to_docs,
    "file": _publish_to_file,
}


def publish_report(paths: Sequence[Path], policy: PolicyConfig) -> list[dict[str, str | None]]:
    summary = build_summary(paths)
    markdown = emit_markdown_table(summary)
    destinations = policy.integrations.publishing.destinations
    results: list[dict[str, str | None]] = []

    for destination in destinations:
        handler = DESTINATION_HANDLERS.get(destination.type)
        if not handler:
            LOGGER.warning("Unknown publishing destination type: %s", destination.type)
            continue
        handler(destination, markdown)
        results.append({
            "type": destination.type,
            "path": destination.path,
            "branch": destination.branch,
            "url": destination.url,
        })
    return results
