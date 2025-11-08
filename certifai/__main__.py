"""Console script entry point for certifai."""

from __future__ import annotations

from .cli import main


def run() -> None:
    """Invoke the primary CLI entry point."""

    raise SystemExit(main())


if __name__ == "__main__":
    run()
