# certifai Evaluation Report – November 2025

## Overview

We evaluated `certifai` on two public Python repositories to gauge annotation coverage, policy enforcement, and review ergonomics:

1. [karpathy/micrograd](https://github.com/karpathy/micrograd)
2. [pallets/click](https://github.com/pallets/click)

All commands were executed from the project root using the `ssbc` conda environment. Metrics were collected via `python -m certifai.cli report --format json ...` with `PYTHONPATH` set to the local checkout.

## Repository Metrics

| Repository | Total Functions | AI-Composed | Human-Certified | Pending Review | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| micrograd | 40 | 0 → **40** | 0 | 40 | 0.0% |
| click | 1544 | 0 → **1544** | 0 | 1544 | 0.0% |

- Initial scans reported zero provenance metadata. Running `certifai annotate` with `--ai-agent gpt-4o --notes "initial provenance audit"` auto-tagged all discovered functions/classes.
- Policy enforcement surfaced violations because the default `.certifai.yml` (none provided) enforces `ai_composed_requires_high_scrutiny=True`. This behaviour is desirable: teams must explicitly certify AI-authored code with `high` scrutiny before merging.
- Coverage remains at 0% until reviewers run `certifai certify ...` to replace `@human_certified: pending` with an approved reviewer handle.

## Workflow Observations

### micrograd

- Annotation touched three files (`micrograd/engine.py`, `micrograd/nn.py`, `test/test_engine.py`).
- Git blame integration appended short commit hashes to the `history:` entries, enabling reviewers to trace prior authorship.
- Recommended next step: run `certifai certify micrograd --reviewer "Maintainer" --scrutiny high` after manual reasoning to reach 100% coverage.

### click

- Annotation spanned the entire codebase (over 1500 artifacts), illustrating scalability. Execution completed in under two minutes on macOS ARM (M3) with policy violations reported for each function lacking `high` scrutiny.
- Large output suggests adding `--no-block` for exploratory annotation or configuring `.certifai.yml` to relax scrutiny for legacy modules during phased adoption.

## Human–AI Collaboration Insights

1. **Visibility vs. Noise** – Auto-tagging legacy repositories generates a surge of metadata. Pairing with incremental rollout (e.g., module-by-module) keeps pull requests reviewable.
2. **Reviewer Accountability** – Persistent `pending` entries clearly mark action items. Adding `certifai verify all --reviewer "Maintainer" --scrutiny high` to release branches formalises sign-off.
3. **Scrutiny Calibration** – Enforcing `high` scrutiny for AI-composed functions ensures deep reviews but may stall teams with limited reviewers. Consider allowing `medium` scrutiny plus mandatory tests for low-risk tooling modules.
4. **Ethics & Transparency** – Recording machine authorship by default surfaces AI contributions that might otherwise slip through code review, supporting organisational transparency commitments.

## Recommendations

- **CI Integration** – Add `certifai report --format md` to GitHub Actions and fail builds when `coverage_ratio` drops below policy-defined thresholds.
- **Reviewer Rotation** – Leverage the reviewer list in `.certifai.yml` to automate assignment (e.g., rotate `@human_certified` suggestions based on Git blame).
- **Education** – Encourage reviewers to populate `notes` with rationale, especially when downgrading scrutiny for low-risk modules.
- **Future Work** – Explore exporting provenance as JSON-LD for SBOM pipelines and integrate with LLM output classifiers to auto-detect AI-generated diffs pre-merge.
