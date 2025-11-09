"""Command-line interface helpers for certifai."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .decorators import certifai
from .certify import certify as certify_artifacts
from .certify import certify_agent as certify_artifacts_agent
from .certify import verify_all as verify_artifacts
from .finalize import finalize as finalize_artifacts
from .integrations.github import build_pr_status
from .integrations.security import run_all_scanners
from .publishing import publish_report
from .audit import (
    record_certification,
    record_agent_certification,
    record_finalization,
    record_enforcement,
    read_audit_log,
)
from .enforce import enforce_ci
from .policy import load_policy
from .provenance import annotate_paths
from .report import (
    build_summary,
    emit_csv_report,
    emit_markdown_table,
    emit_text_report,
)
from .utils.logging import get_logger
from .models import ScrutinyLevel

LOGGER = get_logger("cli")


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose logging output.")
@click.version_option(version=__version__)
def cli(verbose: bool) -> None:
    """Primary certifai CLI group."""

    _configure_logging(verbose)


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(path_type=Path))
@click.option("--ai-agent", default="pending", show_default=True, help="Label to use for @ai_composed metadata.")
@click.option("--notes", default="auto-tagged by certifai", show_default=True, help="Notes text to include when inserting metadata.")
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


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="high",
    date="2025-11-08T01:38:57.432588+00:00",
    notes="manual review",
    history=[
        "2025-11-08T01:38:57.432588+00:00 digest=139418d81d1ecdc479bcd4da96fbf8c6e10cf5c1 certified by PHZ (high) last_commit=f07d0d9 by phzwart",
    ],
)
@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(path_type=Path))
@click.option("--reviewer", required=True, help="Reviewer identifier (human or agent).")
@click.option("--scrutiny", required=True, help="Target scrutiny level (auto|low|medium|high).")
@click.option("--notes", help="Optional notes appended to metadata.")
@click.option("--include-existing", is_flag=True, help="Also refresh artifacts that are already certified.")
@click.option("--policy", type=click.Path(path_type=Path), help="Optional path to a policy file.")
@click.option("--agent", is_flag=True, help="Treat the reviewer as a configured review agent." )
def certify(paths: tuple[Path, ...], reviewer: str, scrutiny: str, notes: str | None, include_existing: bool, policy: Path | None, agent: bool) -> None:
    """Certify selected artifacts."""

    target_paths = paths or (Path.cwd(),)
    policy_config = load_policy(policy)
    reviewer_kind = "agent" if agent else "human"

    requested_level = ScrutinyLevel.from_string(scrutiny)
    if requested_level is None:
        raise click.ClickException(f"Unsupported scrutiny level: {scrutiny}")

    if reviewer_kind == "agent":
        agent_settings = policy_config.integrations.agents
        if not agent_settings.enabled:
            raise click.ClickException("Agent-based certification is disabled in the current policy.")
        permission = next((item for item in agent_settings.reviewers if item.id == reviewer), None)
        if permission is None:
            raise click.ClickException(f"Agent '{reviewer}' is not registered in policy integrations.agents.reviewers.")
        if permission.max_scrutiny:
            allowed_level = ScrutinyLevel.from_string(permission.max_scrutiny)
            if allowed_level is None:
                raise click.ClickException(f"Invalid max_scrutiny '{permission.max_scrutiny}' configured for agent {reviewer}.")
            order = {ScrutinyLevel.AUTO: 0, ScrutinyLevel.LOW: 1, ScrutinyLevel.MEDIUM: 2, ScrutinyLevel.HIGH: 3}
            if order[requested_level] > order[allowed_level]:
                raise click.ClickException(
                    f"Agent '{reviewer}' may not certify '{scrutiny}' scrutiny (max allowed: {permission.max_scrutiny})."
                )

    updated = certify_artifacts(
        target_paths,
        reviewer,
        scrutiny,
        notes=notes,
        include_existing=include_existing,
        reviewer_kind=reviewer_kind,
    )
    click.echo(f"Certified {len(updated)} artifact(s).")
    record_certification(policy_config.integrations.audit, updated, reviewer, notes, reviewer_kind=reviewer_kind)


@cli.command("certify-agent")
@click.argument("paths", nargs=-1, type=click.Path(path_type=Path))
@click.option("--agent", "agent_id", required=True, help="Agent identifier for certification.")
@click.option("--scrutiny", required=True, help="Target scrutiny level (auto|low|medium|high).")
@click.option("--notes", help="Optional notes appended to metadata.")
@click.option("--include-existing", is_flag=True, help="Also refresh artifacts that are already certified.")
@click.option("--policy", type=click.Path(path_type=Path), help="Optional path to a policy file.")
def certify_agent_cmd(paths: tuple[Path, ...], agent_id: str, scrutiny: str, notes: str | None, include_existing: bool, policy: Path | None) -> None:
    """Certify selected artifacts using a trusted agent."""

    target_paths = paths or (Path.cwd(),)
    policy_config = load_policy(policy)
    if not policy_config.integrations.agents.enabled:
        raise SystemExit("Agent certification is not enabled in the current policy.")
    allowed_agents = {perm.id: perm for perm in policy_config.integrations.agents.reviewers}
    if agent_id not in allowed_agents:
        raise SystemExit(f"Agent {agent_id} is not permitted by policy.")
    max_scrutiny = allowed_agents[agent_id].max_scrutiny
    if max_scrutiny:
        level = ScrutinyLevel.from_string(scrutiny)
        max_level = ScrutinyLevel.from_string(max_scrutiny)
        if level is None or max_level is None:
            raise SystemExit("Invalid scrutiny level in agent policy configuration.")
        order = [ScrutinyLevel.AUTO, ScrutinyLevel.LOW, ScrutinyLevel.MEDIUM, ScrutinyLevel.HIGH]
        if order.index(level) > order.index(max_level):
            raise SystemExit(f"Agent {agent_id} is not allowed to certify at {scrutiny} scrutiny (max {max_scrutiny}).")

    updated = certify_artifacts_agent(target_paths, agent_id, scrutiny, notes=notes, include_existing=include_existing)
    click.echo(f"Agent {agent_id} certified {len(updated)} artifact(s).")
    record_certification(policy_config.integrations.audit, updated, agent_id, notes)


@cli.group()
def agent() -> None:
    """Agent review helpers."""


@agent.command("certify")
@click.argument("paths", nargs=-1, type=click.Path(path_type=Path))
@click.option("--agent-id", required=True, help="Identifier for the review agent.")
@click.option("--scrutiny", required=True, help="Scrutiny level applied by the agent (auto|low|medium|high).")
@click.option("--notes", help="Optional notes recorded for this agent review.")
@click.option("--include-existing", is_flag=True, help="Also update artifacts already reviewed by this agent.")
@click.option("--policy", type=click.Path(path_type=Path), help="Optional path to a policy file.")
def agent_certify(paths: tuple[Path, ...], agent_id: str, scrutiny: str, notes: str | None, include_existing: bool, policy: Path | None) -> None:
    """Record agent certification for selected artifacts."""

    target_paths = paths or (Path.cwd(),)
    policy_config = load_policy(policy)
    updated = certify_agent_artifacts(target_paths, agent_id, scrutiny, notes=notes, include_existing=include_existing)
    click.echo(f"Agent {agent_id} certified {len(updated)} artifact(s).")
    record_agent_certification(policy_config.integrations.audit, updated, agent_id, notes)


@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(path_type=Path))
@click.option("--registry-root", type=click.Path(path_type=Path), help="Optional base path for the registry manifest.")
@click.option("--policy", type=click.Path(path_type=Path), help="Optional path to a policy file.")
def finalize(paths: tuple[Path, ...], registry_root: Path | None, policy: Path | None) -> None:
    """Finalize certified artifacts and move provenance to the registry."""

    target_paths = paths or (Path.cwd(),)
    policy_config = load_policy(policy)
    finalized = finalize_artifacts(target_paths, registry_root=registry_root)
    click.echo(f"Finalized {len(finalized)} artifact(s).")
    record_finalization(policy_config.integrations.audit, finalized)


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
@cli.group()
def verify() -> None:
    """Verification commands."""


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
@verify.command("all")
@click.option("--reviewer", required=True, help="Reviewer identifier for verification.")
@click.option("--scrutiny", help="Optional scrutiny level override.")
def verify_all(reviewer: str, scrutiny: str | None) -> None:
    """Verify all pending artifacts."""

    updated = verify_artifacts(reviewer, scrutiny=scrutiny)
    click.echo(f"Verified {len(updated)} artifact(s).")


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
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


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
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


@cli.group()
def pr() -> None:
    """Pull request integrations and helpers."""


@pr.command("status")
@click.option("--path", "paths", multiple=True, type=click.Path(path_type=Path), help="File or directory to analyse (repeatable). Defaults to repository root.")
@click.option("--paths-file", type=click.Path(path_type=Path), help="File containing newline-delimited paths to include. Use '-' to read from stdin.")
@click.option("--policy", type=click.Path(path_type=Path), help="Optional path to policy file.")
@click.option("--output", type=click.Choice(["json", "pretty"]), default="json", show_default=True, help="Output format.")
def pr_status(paths: tuple[Path, ...], paths_file: Path | None, policy: Path | None, output: str) -> None:
    """Emit a JSON status summary for pull request automation."""

    aggregated_paths: list[Path | str] = list(paths)

    if paths_file is not None:
        if str(paths_file) == "-":
            content = sys.stdin.read().splitlines()
        else:
            content = paths_file.read_text(encoding="utf-8").splitlines()
        aggregated_paths.extend(line.strip() for line in content if line.strip())

    if not aggregated_paths:
        aggregated_paths = [Path.cwd()]

    policy_config = load_policy(policy)
    status_payload = build_pr_status(aggregated_paths, policy_config)

    indent = 2 if output == "pretty" else None
    click.echo(json.dumps(status_payload, indent=indent, sort_keys=output == "pretty"))


@cli.group()
def security() -> None:
    """Security scanner integrations."""


@security.command("run")
@click.option("--path", "paths", multiple=True, type=click.Path(path_type=Path), help="File or directory to scan (repeatable).")
@click.option("--paths-file", type=click.Path(path_type=Path), help="File containing newline-delimited paths to scan. Use '-' to read from stdin.")
@click.option("--policy", type=click.Path(path_type=Path), help="Optional path to policy file.")
@click.option("--output", type=click.Choice(["json", "pretty"]), default="json", show_default=True, help="Output format.")
def security_run(paths: tuple[Path, ...], paths_file: Path | None, policy: Path | None, output: str) -> None:
    """Run configured security scanners and emit a JSON summary."""

    policy_config = load_policy(policy)
    settings = policy_config.integrations.security
    aggregated_paths: list[Path | str] = list(paths)

    if paths_file is not None:
        if str(paths_file) == "-":
            content = sys.stdin.read().splitlines()
        else:
            content = paths_file.read_text(encoding="utf-8").splitlines()
        aggregated_paths.extend(line.strip() for line in content if line.strip())

    if not aggregated_paths:
        aggregated_paths = [Path.cwd()]

    results = run_all_scanners(settings, aggregated_paths)
    payload = {
        "scanners": [
            {
                "name": result.name,
                "command": result.command,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "findings": result.findings,
            }
            for result in results
        ],
        "status": "pass" if all(result.exit_code == 0 for result in results) else "fail",
    }

    indent = 2 if output == "pretty" else None
    click.echo(json.dumps(payload, indent=indent, sort_keys=output == "pretty"))


@cli.group()
def publish() -> None:
    """Report publishing commands."""


@publish.command("report")
@click.option("--path", "paths", multiple=True, type=click.Path(path_type=Path), help="File or directory to include in the report (repeatable). Defaults to repository root.")
@click.option("--policy", type=click.Path(path_type=Path), help="Optional path to policy file.")
@click.option("--output", type=click.Choice(["json", "pretty"]), default="json", show_default=True, help="Output format.")
def publish_report_cmd(paths: tuple[Path, ...], policy: Path | None, output: str) -> None:
    """Publish coverage reports to configured destinations."""

    target_paths = list(paths) or [Path.cwd()]
    policy_config = load_policy(policy)
    results = publish_report([Path(p) for p in target_paths], policy_config)

    payload = {
        "status": "pass" if results else "noop",
        "destinations": results,
    }

    indent = 2 if output == "pretty" else None
    click.echo(json.dumps(payload, indent=indent, sort_keys=output == "pretty"))


@cli.command()
@click.option("--path", "paths", multiple=True, type=click.Path(path_type=Path), help="File or directory to evaluate (repeatable). Defaults to repository root.")
@click.option("--policy", type=click.Path(path_type=Path), help="Optional path to policy file.")
@click.option("--output", type=click.Choice(["json", "pretty"]), default="json", show_default=True, help="Output format.")
def enforce(paths: tuple[Path, ...], policy: Path | None, output: str) -> None:
    """Run CI enforcement checks (coverage, policy, security)."""

    target_paths = list(paths) or [Path.cwd()]
    policy_config = load_policy(policy)
    result = enforce_ci([Path(p) for p in target_paths], policy_config)

    indent = 2 if output == "pretty" else None
    click.echo(json.dumps({
        "status": result.status,
        "messages": result.messages,
        "payload": result.payload,
    }, indent=indent, sort_keys=output == "pretty"))

    record_enforcement(policy_config.integrations.audit, result.status, result.messages)
    if result.status != "pass":
        raise SystemExit(1)


@cli.group()
def audit() -> None:
    """Audit log utilities."""


@audit.command("show")
@click.option("--policy", type=click.Path(path_type=Path), help="Optional path to policy file.")
@click.option("--log-path", type=click.Path(path_type=Path), help="Override audit log path.")
@click.option("--limit", type=int, default=-1, show_default=True, help="Number of most recent entries to display (-1 for all).")
@click.option("--output", type=click.Choice(["json", "pretty"]), default="json", show_default=True, help="Output format.")
def audit_show(policy: Path | None, log_path: Path | None, limit: int, output: str) -> None:
    """Show audit log entries."""

    policy_config = load_policy(policy)
    effective_limit = None if limit < 0 else limit
    entries = read_audit_log(policy_config.integrations.audit, limit=effective_limit, override=log_path)
    indent = 2 if output == "pretty" else None
    click.echo(json.dumps(entries, indent=indent, sort_keys=output == "pretty"))


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
@cli.group()
def config() -> None:
    """Configuration helpers."""


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
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


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.799864+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:10:38.983420+00:00 digest=1d01aa11423a60429ad5a390a99e2b8535830afd last_commit=f07d0d9 by phzwart",
    ],
)
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
