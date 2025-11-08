"""Pre-commit hook integration for certifai."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

from .policy import load_policy
from .provenance import annotate_paths
from .utils.logging import get_logger

LOGGER = get_logger("hooks")


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.475775+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:28.719649+00:00 digest=11391cb64b4371e1ad542ea38854dbfb1145d97a last_commit=f07d0d9 by phzwart

def run_pre_commit(
    paths: Iterable[str],
    *,
    ai_agent: str = "pending",
    block_on_violation: bool = True,
) -> int:
    """Run the certifai pre-commit hook against the supplied paths."""

    policy = load_policy()
    result = annotate_paths(paths, ai_agent=ai_agent, policy=policy)
    for updated in result.updated_files:
        LOGGER.info("certifai auto-tagged %s", updated)
    if result.policy_violations:
        for violation in result.policy_violations:
            LOGGER.error("Policy violation: %s", violation)
        if block_on_violation:
            return 1
    return 0


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.475775+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:28.719649+00:00 digest=11391cb64b4371e1ad542ea38854dbfb1145d97a last_commit=f07d0d9 by phzwart

def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="certifai pre-commit hook")
    parser.add_argument("paths", nargs="*", help="Files to inspect")
    parser.add_argument(
        "--ai-agent",
        default="pending",
        help="Identifier recorded in @ai_composed metadata when annotating.",
    )
    parser.add_argument(
        "--no-block",
        dest="block_on_violation",
        action="store_false",
        help="Do not block the commit even if policy violations are detected.",
    )
    return parser.parse_args(argv)


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:45.475775+00:00
# notes: bulk annotation
# history: 2025-11-08T00:54:28.719649+00:00 digest=11391cb64b4371e1ad542ea38854dbfb1145d97a last_commit=f07d0d9 by phzwart

def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code = run_pre_commit(
        args.paths,
        ai_agent=args.ai_agent,
        block_on_violation=args.block_on_violation,
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
