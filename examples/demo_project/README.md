# certifai Demonstration Project

This self-contained demo showcases how to integrate the `certifai` toolkit into a small Python codebase. It walks through annotating AI-assisted code, reviewing changes via pre-commit, and generating certification reports.

## Quickstart

1. Install the package from the project root:

   ```bash
   pip install -e ..
   ```

2. Activate the provided pre-commit configuration:

   ```bash
   pre-commit install --config .pre-commit-config.yaml
   ```

3. Run the provenance annotator on the repo:

   ```bash
   certifai annotate src/demo_project
   ```

4. Review and certify functions as a mentor:

   ```bash
   certifai certify src/demo_project --reviewer "Mentor" --scrutiny high --notes "Walked through as part of onboarding"
   ```

5. Generate a Markdown coverage report for documentation or CI:

   ```bash
   certifai report --format md src/demo_project > certifai_report.md
   ```

## Repository Layout

```
demo_project/
├── .certifai.yml
├── .pre-commit-config.yaml
├── README.md
└── src/
    └── demo_project/
        ├── analytics.py
        └── preprocessing.py
```

## Policy Configuration

The demo uses a sample `.certifai.yml` restricting AI-generated functions to high scrutiny and targeting 80% certification coverage. Adjust reviewer lists and coverage thresholds to match your team's policies.

## GitHub Actions Integration

The root project includes helper utilities to emit reusable GitHub Action steps. For this demo, you can add the following snippet to `.github/workflows/certifai.yml`:

```yaml
name: certifai
on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install certifai
        run: pip install .
      - name: Run certifai report
        run: certifai report --format md src/demo_project > certifai_report.md
      - name: Upload report artifact
        uses: actions/upload-artifact@v4
        with:
          name: certifai-report
          path: certifai_report.md
```

## Next Steps

- Explore `certifai verify all --reviewer "Mentor"` to approve pending metadata in bulk.
- Integrate `certifai badge src/demo_project` into your documentation pipeline to publish up-to-date certification badges.
- Experiment with different scrutiny levels (`low`, `medium`, `high`) to tailor review depth based on module criticality.
