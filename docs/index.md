# certifai Technical Guide

`certifai` is a human-in-the-loop certification harness for AI-assisted code. This guide documents the provenance tagging schema, command-line workflows, policy and hook integration, and recommended practices for transparent collaboration between humans and AI systems.

## Tagging Schema

Each function or class is annotated with the `certifai` decorator to describe its provenance and review state:

```
from certifai.decorators import certifai


@certifai(
    ai_composed="gpt-5",
    human_certified="Reviewer",
    scrutiny="high",
    date="2025-11-07",
    notes="logic verified, unit tested, compliant with policy",
    history=[
        "2025-11-07T18:22:06Z digest=abc123... annotated by certifai; last_commit=abc1234 by Reviewer",
    ],
)
def normalize(df):
    ...
```

- `ai_composed` records which AI model or agent proposed the change (defaults to `pending`).
- `human_certified` names the reviewer responsible for human approval (`pending` until certified).
- `scrutiny` captures review depth (`auto`, `low`, `medium`, `high`). Policies can require `high` for AI-authored code.
- `date` is ISO 8601 timestamp of the most recent certification event.
- `notes` stores contextual review comments.
- `history` tracks chronological provenance events, including automated insertions and the latest Git blame metadata.
- `done` marks an artifact as finalized. When present, detailed provenance is stored in the central registry and the inline decorator collapses to a minimal form (for example `@certifai(done=True, human_certified="Reviewer")`).

### Insertion Algorithm

- `certifai annotate` and the pre-commit hook scan Python files for untagged definitions.
- `certifai` decorators are inserted immediately above the first existing decorator (if any) or the definition line, and inherit local indentation.
- Git blame metadata of the definition line is appended to the `history` list for traceability.
- Existing decorators and comments remain in place; metadata decorators are prepended without disturbing surrounding code.

## CLI Overview

All commands are exposed via the `certifai` Click-based interface. Use `--help` with any command to inspect flags.

### Provenance Annotation

```bash
certifai annotate src/ --ai-agent "gpt-5" --notes "auto-tagged during onboarding"
```

Automatically inserts provenance headers for untagged artifacts, respecting `.certifai.yml` policies. Policy violations (e.g., insufficient coverage) surface as non-zero exit codes unless `--no-block` is set on the pre-commit hook.

### Certification Workflow

- **Certify specific files**:

  ```bash
  certifai certify src/package --reviewer "Mentor" --scrutiny high --notes "Paired review"
  ```

  Updates metadata for pending artifacts, adds ISO timestamps, and appends `history` entries. Use `--include-existing` to refresh already certified blocks.

- **Bulk verification**:

  ```bash
  certifai verify all --reviewer "Lead" --scrutiny high
  ```

  Re-certifies all pending artifacts under a single reviewer, useful for final release audits.

- **Finalize artifacts**:

  ```bash
  certifai finalize src/package --registry-root .
  ```

  Moves richly annotated metadata into `.certifai/registry.yml`, rewrites inline decorators to `@certifai(done=True, …)`, and records an implementation digest for each finalized function.

### Reporting & Badges

```bash
certifai report --format text src
certifai report --format json src > certifai_report.json
certifai report --format csv src > certifai_report.csv
certifai report --format md src > certifai_report.md
certifai badge src
certifai pr status --path path/to/changed.py --output pretty
certifai security run --policy .certifai.yml --output pretty
certifai enforce --output pretty
certifai certify-agent src/my_module.py --agent github/apps/certifai-bot --scrutiny medium --policy .certifai.yml
certifai publish report --policy .certifai.yml --output pretty
certifai audit show --limit 10 --output pretty
```

`build_summary` collects artifact-level metrics, while `emit_text_report`, `emit_csv_report`, and `emit_markdown_table` render outputs for console, data pipelines, and dashboards. `certifai badge` prints a Markdown image tag pointing to a Shields.io badge reflecting the latest coverage percentage.

`certifai pr status` emits a JSON payload suitable for GitHub status checks or bot annotations, summarising coverage, policy violations, and pending AI-reviewed sections for the supplied files (or the entire repository when paths are omitted).

`certifai security run` executes the security scanners defined in `.certifai.yml` (see below) and prints a JSON summary of exit codes, stdout, and parsed findings. This is ideal for PR bots or Actions that need to combine provenance checks with vulnerability scanning.

`certifai enforce` is a CI-friendly command that combines coverage checks, policy enforcement, and security scanning. It returns a non-zero exit code if any configured requirement fails, making it suitable for GitHub Actions/GitLab CI merge gates.

`certifai certify-agent` allows trusted review agents to stamp artifacts with their approval while respecting per-agent scrutiny limits defined in `.certifai.yml`. Agent reviews are recorded alongside human reviewers and can satisfy coverage rules when policy permits it.

`certifai audit show` loads the configured audit log (by default `.certifai/audit.log`) and prints the most recent entries, making it easy for compliance teams to review reviewer activity or hand that data to dashboards.

### Policy Inspection

```bash
certifai config show
```

Prints the effective policy in JSON format, combining defaults and values resolved from `.certifai.yml`.

## Policy & Hooks

- `.certifai.yml` controls enforcement:

  ```yaml
  enforcement:
    ai_composed_requires_high_scrutiny: true
    min_coverage: 0.8
    ignore_unannotated: false  # set true to skip coverage checks for files without metadata
  reviewers:
    - PZ
    - JD
  integrations:
    pr_bot:
      enabled: true
      platforms: ["github"]
      reviewer_groups: ["ai-reviewers"]
      status_check: certifai/pr
    security_scanners:
      enabled: true
      commands:
        - name: snyk
          run: snyk test --json
        - name: trivy
          run: trivy fs --format json
    publishing:
      destinations:
        - type: wiki
          path: docs/certifai.md
    ci:
      enabled: true
      min_coverage: 0.9
      require_human_review: true
      fail_on_vulnerabilities: high
    audit:
      enabled: true
      log_path: .certifai/audit.log
      dashboard_url: https://intranet.example.com/certifai
  agents:
    enabled: true
    allowed_ids:
      - github/apps/certifai-agent
    allow_coverage_credit: true
    default_scrutiny: medium
    reviewers:
      - id: github/apps/certifai-agent
        max_scrutiny: medium
        allow_finalize: false
        notes: "Runs lint + unit tests"
  ```

- The pre-commit hook entry point (`certifai-pre-commit`) automatically calls `certifai annotate` on staged files and blocks commits when enforcement rules fail. Configure via `.pre-commit-config.yaml`:

  ```yaml
  repos:
    - repo: local
      hooks:
        - id: certifai
          entry: certifai-pre-commit
          language: system
          pass_filenames: true
          types: [python]
  ```

- After annotation, the hook reconciles the registry: if any `done=True` artifact no longer matches its recorded digest, the entry is removed from `.certifai/registry.yml`, the inline decorator is expanded back to a full `@certifai(...)` block, and the function re-enters the certification queue.

## CI/CD Integration

- Use the helper from `certifai.report.github_actions_step()` or embed manually:

  ```yaml
  - name: Run certifai report
    run: certifai report --format md . > certifai_report.md
  ```

- Upload the Markdown output as an artifact, comment on pull requests, or publish the badge in README.md:

  ```markdown
  ![certifai Coverage](https://img.shields.io/badge/Human_Certified-74%25-green)
  ```

- Optionally fail CI when `min_coverage` is unmet; the policy violation message is surfaced through the pre-commit hook or `annotate` command return code.

## Ethical Framing & Best Practices

1. **Transparency** – Maintain accurate `@ai_composed` labels to disclose AI involvement in critical modules.
2. **Accountability** – Use `@human_certified` to assign responsible reviewers; avoid merging AI-authored changes without human comprehension.
3. **Granular Scrutiny** – Calibrate `scrutiny` levels to match risk. Require `high` for safety-critical or security-sensitive code and integrate additional testing for `medium`/`high` items.
4. **Traceability** – Leverage the `history` field and Git metadata to preserve review narratives and ensure reproducibility across audits.
5. **Education** – Encourage mentors to annotate `notes` detailing their reasoning, promoting knowledge transfer for junior contributors pairing with AI systems.

## Provenance Lifecycle

certifai tracks the entire journey from AI draft to human-approved code:

1. **Untracked** – No decorator present. Reporting surfaces these definitions as "unknown" so they can be queued for provenance tagging.
2. **Pending annotation** – `@certifai(ai_composed=...)` is added automatically by `certifai annotate`. At this stage only the AI agent (and optional notes) are recorded.
3. **Certified** – `certifai certify` updates the decorator with reviewer, scrutiny, notes, timestamps, and history entries. The artifact now meets policy but may still evolve.
4. **Finalized** – `certifai finalize` collapses inline metadata to `@certifai(done=True, human_certified=...)`, stores rich history + a normalized AST digest in `.certifai/registry.yml`, and ensures the pre-commit hook tracks drift. Any future code change invalidates the digest, automatically re-expands the decorator, and re-queues the function for review.
5. **Agent-reviewed (optional)** – `certifai agent certify` allows approved review agents (configured in `.certifai.yml`) to record their verification. Agent reviews keep the artifact pending until a human signs off, but can satisfy lower-risk coverage thresholds when policy allows.

Reports treat pending and finalized artifacts differently, letting teams monitor certification coverage, regression reopenings, and overall review throughput.

## Alignment with the C.L.E.A.R. Review Framework

certifai’s workflows map directly onto the C.L.E.A.R. approach for AI-generated code reviews [^1]:

- **Context Establishment** – Inline provenance captures prompts, reviewers, scrutiny levels, and timestamps so reviewers arrive with complete context.
- **Layered Examination** – Coverage and registry reports enumerate all module artifacts, making it easy to review structure first, then logic, security, performance, and style in focused passes. Review agents can handle the lighter layers, leaving humans to focus on high scrutiny sections.
- **Explicit Verification** – Certification requires explicit reviewer notes and history entries; finalization preserves these in the registry, and any digest mismatch forces another verification cycle.
- **Alternative Consideration** – Notes and history fields double as decision logs, while registry snapshots capture evolution across alternative designs; agent notes and audit logs document automated checks.
- **Refactoring Recommendations** – Reports flag pending items, reopened artifacts, and coverage deltas so teams can turn review findings into actionable follow-ups.

By combining provenance tagging, policy checks, and digest-backed finalization, certifai operationalizes the CLEAR methodology in day-to-day Git workflows.

[^1]: [Vibe Coding Framework – Code Review Guidelines](https://docs.vibe-coding-framework.com/best-practices/code-review-guidelines)

## Additional Resources

- The `.certifai/registry.yml` manifest reflects the current set of finalized artifacts and their digests. Treat it like other provenance files—commit it alongside code changes.
- The `examples/demo_project` directory illustrates end-to-end onboarding.
- Use `certifai report --format json` to feed dashboards or longitudinal analyses tracking human review coverage over time.
- Extend the schema by passing extra keyword arguments to the decorator—unknown keys are preserved via `TagMetadata.extras` for forward compatibility.
