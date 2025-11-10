# certifai

`certifai` is a human-in-the-loop certification toolkit that makes AI-assisted code transparent. It tags provenance metadata directly in source files, enforces review policies through pre-commit hooks, and generates certification reports for CI/CD pipelines.

## Installation

```bash
pip install certifai
# or from the repository root
pip install -e .
```

## Quickstart

```bash
# Annotate Python files missing provenance metadata
certifai annotate src/ --ai-agent "gpt-4.1" --notes "initial audit"

# Certify reviewed artifacts
certifai certify src/ --reviewer "Mentor" --scrutiny high

# Finalize reviewed artifacts (Stage 2 → Stage 3)
certifai finalize src/

# Detect drift and reopen changed artifacts for review
certifai check

# Generate reports and badges
certifai report --format md src/ > certifai_report.md
certifai badge src/

# Inspect agent-driven findings and review status
certifai findings src/core/critical.py
certifai review-status src/core/critical.py::calculate_dose
```

## 4-Stage Lifecycle

1. **Stage 0 – Pristine**: No decorator in source, artifact untracked.
2. **Stage 1 – Annotated**: Minimal `@certifai(ai_composed="…", reviewers=[])` marks code pending review.
3. **Stage 2 – Under Review**: Decorator accrues reviewer entries (humans and agents) as approvals arrive.
4. **Stage 3 – Finalized**: Finalization removes decorators from code, persists full provenance to `.certifai/registry.yml`, and starts drift monitoring. Future edits automatically re-open artifacts by restoring the Stage 1 decorator and archiving the previous registry entry.

## Features

- Automatic insertion of provenance headers (`@certifai` metadata such as `ai_composed`, `human_certified`, `scrutiny`, `history`).
- Finalization workflow that removes inline decorators, writes complete provenance (including reviewers and lifecycle history) to `.certifai/registry.yml`, and prepares drift detection to automatically reopen changes.
- Natural alignment with the C.L.E.A.R. review framework for AI-generated code: provenance delivers context, coverage reports support layered examination, registry digests enforce explicit verification, and notes/history preserve alternatives and refactoring follow-ups.
- Flexible reviewer support: humans can certify high-risk code, while approved review agents can record automated checks and (optionally) satisfy lower-risk coverage thresholds.
- Structured agent findings API and CLI tooling (`certifai findings`, `certifai review-status`) for auditing LLM or scanner outputs and gating merges on blocking issues.
- Policy enforcement via `.certifai.yml` (e.g., requiring `high` scrutiny for AI-authored code, minimum coverage thresholds).
- Click-based CLI for annotation, certification, reporting, badge generation, and config inspection.
- Pre-commit hook (`certifai-pre-commit`) for continuous provenance tagging during development.
- Rich reporting utilities: text, JSON, CSV, Markdown tables, and Shields.io-style badges.
- Demo project under `examples/demo_project` illustrating onboarding + GitHub Actions integration.
- Evaluation report (`reports/evaluation.md`) summarising runs on real open-source repositories.

## Configuration

Create a `.certifai.yml` policy file at your repo root:

```yaml
enforcement:
  ai_composed_requires_high_scrutiny: true
  min_coverage: 0.8
reviewers:
  - PZ
  - JD
```

Install the pre-commit hook:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: certifai
        name: certifai provenance annotator
        entry: certifai-pre-commit
        language: system
        types: [python]
```

## Documentation

- Technical guide: `docs/index.md`
- Demo walkthrough: `examples/demo_project/README.md`
- Evaluation findings: `reports/evaluation.md`

## Development

```bash
nox --session=tests
nox --session=coverage
```

## License

MIT © certifai maintainers
