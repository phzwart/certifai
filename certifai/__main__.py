"""Console script entry point for certifai."""

from __future__ import annotations

from .cli import main
from .decorators import certifai


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:46.002131+00:00",
    notes="bulk annotation",
    history=[
        "2025-11-08T00:54:54.366452+00:00 digest=b38f3766b18b2f81ae7b12a2f4ec5f38f3daf320 last_commit=f07d0d9 by phzwart",
    ],
)
def run() -> None:
    """Invoke the primary CLI entry point."""

    raise SystemExit(main())


if __name__ == "__main__":
    run()
