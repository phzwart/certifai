"""Console script entry point for certifai."""

from __future__ import annotations

from .cli import main


# @ai_composed: gpt-5
# @human_certified: pending
# scrutiny: auto
# date: 2025-11-08T00:34:46.002131+00:00
# notes: bulk annotation
# history: 2025-11-08T00:34:46.002131+00:00 inserted by certifai; last_commit=f07d0d9 by phzwart

def run() -> None:
    """Invoke the primary CLI entry point."""

    raise SystemExit(main())


if __name__ == "__main__":
    run()
