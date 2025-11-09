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

# Generate reports and badges
certifai report --format md src/ > certifai_report.md
certifai badge src/
```

## Features

- Automatic insertion of provenance headers (`@certifai` metadata such as `ai_composed`, `human_certified`, `scrutiny`, `history`).
- Finalization workflow that collapses inline metadata to `@certifai(done=True, …)` and stores rich provenance + AST digests in `.certifai/registry.yml`.
- Natural alignment with the C.L.E.A.R. review framework for AI-generated code: provenance delivers context, coverage reports support layered examination, registry digests enforce explicit verification, and notes/history preserve alternatives and refactoring follow-ups.
- Flexible reviewer support: humans can certify high-risk code, while approved review agents can record automated checks and (optionally) satisfy lower-risk coverage thresholds.
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
