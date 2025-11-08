"""nox sessions for certifai."""

from __future__ import annotations

import nox


PYTHON_VERSIONS = ["3.11"]
TEST_DEPENDENCIES = [
    "pytest",
    "coverage[toml]",
    "click",
    "pyyaml",
    "gitpython",
    "rich",
    "regex",
]


# @ai_composed: pending
# @human_certified: PHZ
# scrutiny: high
# date: 2025-11-08T01:38:57.476668+00:00
# notes: manual review
# history: 2025-11-08T01:38:57.476668+00:00 digest=0d0dbbebf6a45e1b4c60034d36bb18c481d4928d certified by PHZ (high) last_commit=f07d0d9 by phzwart

@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the unit test suite."""

    session.install("-e", ".")
    session.install(*TEST_DEPENDENCIES)
    session.run("pytest", "tests")


# @ai_composed: pending
# @human_certified: PHZ
# scrutiny: high
# date: 2025-11-08T01:38:57.476668+00:00
# notes: manual review
# history: 2025-11-08T01:38:57.476668+00:00 digest=0d0dbbebf6a45e1b4c60034d36bb18c481d4928d certified by PHZ (high) last_commit=uncommitted

@nox.session(python=PYTHON_VERSIONS)
def coverage(session: nox.Session) -> None:
    """Run the test suite with coverage reporting."""

    session.install("-e", ".")
    session.install(*TEST_DEPENDENCIES)
    session.run("coverage", "run", "-m", "pytest", "tests")
    session.run("coverage", "xml")
    session.run("coverage", "report", "-m")
