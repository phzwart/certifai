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


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the unit test suite."""

    session.install("-e", ".")
    session.install(*TEST_DEPENDENCIES)
    session.run("pytest", "tests")


@nox.session(python=PYTHON_VERSIONS)
def coverage(session: nox.Session) -> None:
    """Run the test suite with coverage reporting."""

    session.install("-e", ".")
    session.install(*TEST_DEPENDENCIES)
    session.run("coverage", "run", "-m", "pytest", "tests")
    session.run("coverage", "xml")
    session.run("coverage", "report", "-m")
