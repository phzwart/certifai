"""Command-line interface helpers for certifai."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .certify import certify as certify_artifacts
from .certify import verify_all as verify_artifacts
from .policy import load_policy
from .provenance import annotate_paths
from .report import (
    build_summary,
    emit_csv_report,
    emit_markdown_table,
    emit_text_report,
)
from .utils.logging import get_logger

LOGGER = get_logger("cli")


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose logging output.")
@click.version_option(version=__version__)
def cli(verbose: bool) -> None:
    """Primary certifai CLI group."""

    _configure_logging(verbose)


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(path_type=Path))
@click.option("--ai-agent", default="pending", show_default=True, help="Label to use for @ai_composed metadata.")
@click.option("--notes", default="auto-tagged by certifai", show_default=True, help="Notes comment to include when inserting metadata.")
@click.option("--policy", type=click.Path(path_type=Path), help="Path to a .certifai.yml policy file.")
def annotate(paths: tuple[Path, ...], ai_agent: str, notes: str, policy: Path | None) -> None:
    """Insert provenance metadata for unannotated artifacts."""

    target_paths = paths or (Path.cwd(),)
    policy_config = load_policy(policy) if policy else load_policy()
    result = annotate_paths(target_paths, ai_agent=ai_agent, default_notes=notes, policy=policy_config)
    click.echo(f"Processed {len(result.artifacts)} artifacts across {len(target_paths)} path(s).")
    if result.updated_files:
        click.echo(f"Updated files: {len(result.updated_files)}")
    if result.policy_violations:
        for violation in result.policy_violations:
            click.echo(f"Policy violation: {violation}", err=True)
        raise SystemExit(1)


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: high
# date: 2025-11-08T01:38:57.432588+00:00
# notes: manual review
# history: 2025-11-08T01:38:57.432588+00:00 digest=139418d81d1ecdc479bcd4da96fbf8c6e10cf5c1 certified by PHZ (high) last_commit=f07d0d9 by phzwart

@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(path_type=Path))
@click.option("--reviewer", required=True, help="Reviewer identifier for certification.")
@click.option("--scrutiny", required=True, help="Target scrutiny level (auto|low|medium|high).")
@click.option("--notes", help="Optional notes appended to metadata.")
@click.option("--include-existing", is_flag=True, help="Also refresh artifacts that are already certified.")
def certify(paths: tuple[Path, ...], reviewer: str, scrutiny: str, notes: str | None, include_existing: bool) -> None:
    """Certify selected artifacts."""

    target_paths = paths or (Path.cwd(),)
    updated = certify_artifacts(target_paths, reviewer, scrutiny, notes=notes, include_existing=include_existing)
    click.echo(f"Certified {len(updated)} artifact(s).")


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

@cli.group()
def verify() -> None:
    """Verification commands."""


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

@verify.command("all")
@click.option("--reviewer", required=True, help="Reviewer identifier for verification.")
@click.option("--scrutiny", help="Optional scrutiny level override.")
def verify_all(reviewer: str, scrutiny: str | None) -> None:
    """Verify all pending artifacts."""

    updated = verify_artifacts(reviewer, scrutiny=scrutiny)
    click.echo(f"Verified {len(updated)} artifact(s).")


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "csv", "md"]),
    default="text",
    show_default=True,
)
def report(paths: tuple[Path, ...], output_format: str) -> None:
    """Generate a certification coverage report."""

    target_paths = paths or (Path.cwd(),)
    summary = build_summary(target_paths)
    if output_format == "json":
        click.echo(json.dumps(summary.to_dict(), indent=2, default=str))
    elif output_format == "csv":
        click.echo(emit_csv_report(summary))
    elif output_format == "md":
        click.echo(emit_markdown_table(summary))
    else:
        click.echo(emit_text_report(summary))


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(path_type=Path))
def badge(paths: tuple[Path, ...]) -> None:
    """Output a Markdown badge for current certification coverage."""

    target_paths = paths or (Path.cwd(),)
    summary = build_summary(target_paths)
    coverage_percent = round(summary.coverage_ratio * 100, 1)
    coverage_str = f"{coverage_percent:.1f}".rstrip("0").rstrip(".")
    color = "green" if coverage_percent >= 80 else "orange" if coverage_percent >= 50 else "red"
    badge_url = (
        "https://img.shields.io/badge/" +
        f"Human_Certified-{coverage_str}%25-{color}"
    )
    click.echo(f"![certifai Coverage]({badge_url})")


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

@cli.group()
def config() -> None:
    """Configuration helpers."""


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

@config.command("show")
@click.option("--path", type=click.Path(path_type=Path), help="Optional path to a policy file.")
def config_show(path: Path | None) -> None:
    """Display the effective policy configuration."""

    policy = load_policy(path)
    click.echo(json.dumps({
        "enforcement": {
            "ai_composed_requires_high_scrutiny": policy.enforcement.ai_composed_requires_high_scrutiny,
            "min_coverage": policy.enforcement.min_coverage,
        },
        "reviewers": list(policy.reviewers),
    }, indent=2))


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: auto
# date: 2025-11-08T00:34:45.799864+00:00
# notes: No obvious issues found.
# history: 2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart

def main(argv: Optional[list[str]] = None) -> int:
    """Entry point used by console script entry point."""

    try:
        args = list(argv) if argv is not None else sys.argv[1:]
        cli.main(args=args, prog_name="certifai")
    except SystemExit as exc:
        return exc.code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
