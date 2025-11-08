# certifai Technical Guide

`certifai` is a human-in-the-loop certification harness for AI-assisted code. This guide documents the provenance tagging schema, command-line workflows, policy and hook integration, and recommended practices for transparent collaboration between humans and AI systems.

## Tagging Schema

Each function or class can be prefixed with a metadata header describing its provenance and review state:

```
# @ai_composed: gpt-5
# @human_certified: Reviewer
# scrutiny: high
# date: 2025-11-07
# notes: logic verified, unit tested, compliant with policy
# history: 2025-11-07T18:22:06Z inserted by certifai; last_commit=abc1234 by Reviewer
def normalize(df):
    ...
```

- `@ai_composed` records which AI model or agent proposed the change (defaults to `pending`).
- `@human_certified` names the reviewer responsible for human approval (`pending` until certified).
- `scrutiny` captures review depth (`auto`, `low`, `medium`, `high`). Policies can require `high` for AI-authored code.
- `date` is ISO 8601 timestamp of latest certification event.
- `notes` stores contextual review comments.
- `history` tracks chronological provenance events, including automated insertions and the latest Git blame metadata.

### Insertion Algorithm

- `certifai annotate` and the pre-commit hook scan Python files for untagged definitions.
- Tag blocks are inserted immediately above the first decorator or definition line and inherit local indentation.
- Git blame metadata of the definition line is appended to the `history` comment for traceability.
- Existing developer comments directly above the definition are preserved, and non-schema comments remain in `TagMetadata.extras`.

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

### Reporting & Badges

```bash
certifai report --format text src
certifai report --format json src > certifai_report.json
certifai report --format csv src > certifai_report.csv
certifai report --format md src > certifai_report.md
certifai badge src
```

`build_summary` collects artifact-level metrics, while `emit_text_report`, `emit_csv_report`, and `emit_markdown_table` render outputs for console, data pipelines, and dashboards. `certifai badge` prints a Markdown image tag pointing to a Shields.io badge reflecting the latest coverage percentage.

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
  reviewers:
    - PZ
    - JD
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

## Additional Resources

- The `examples/demo_project` directory illustrates end-to-end onboarding.
- Use `certifai report --format json` to feed dashboards or longitudinal analyses tracking human review coverage over time.
- Extend the schema by appending custom `# notes:` or `# history:` entries—unknown comment lines are preserved for forward compatibility.
