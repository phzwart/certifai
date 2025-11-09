from __future__ import annotations

from pathlib import Path

from certifai.decorators import certifai
from certifai.policy import EnforcementSettings, PolicyConfig, load_policy, IntegrationsConfig, AgentPolicy
from certifai.policy import ScrutinyLevel


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:46.249248+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.538630+00:00 digest=479c655323df41ec33e2891fdf5b16a2d7e2b86c last_commit=f07d0d9 by phzwart",
    ],
)
def test_load_policy_defaults_when_missing(tmp_path: Path) -> None:
    policy = load_policy(tmp_path / ".certifai.yml")
    assert isinstance(policy, PolicyConfig)
    assert policy.enforcement.ai_composed_requires_high_scrutiny is True
    assert policy.enforcement.min_coverage is None
    assert not policy.integrations.pr_bot.enabled
    assert not policy.integrations.security.enabled
    assert not policy.integrations.publishing.enabled
    assert not policy.integrations.ci.enabled
    assert not policy.integrations.audit.enabled
    assert not policy.integrations.agents.enabled


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:46.249248+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:35:22.538630+00:00 digest=479c655323df41ec33e2891fdf5b16a2d7e2b86c last_commit=f07d0d9 by phzwart",
    ],
)
def test_load_policy_from_file(tmp_path: Path) -> None:
    config = tmp_path / ".certifai.yml"
    config.write_text(
        """
enforcement:
  ai_composed_requires_high_scrutiny: false
  min_coverage: 0.9
reviewers:
  - Mentor
  - Auditor
integrations:
  pr_bot:
    enabled: true
    platforms: ["github"]
    reviewer_groups: ["ai-reviewers"]
    status_check: certifai/pr
    agents_allowed: ["bot-1"]
  security_scanners:
    commands:
      - name: snyk
        run: snyk test --json
  publishing:
    destinations:
      - type: wiki
        path: docs/certifai.md
  ci:
    enabled: true
    min_coverage: 0.95
    require_human_review: true
    fail_on_vulnerabilities: high
  audit:
    enabled: true
    log_path: .certifai/audit.log
    dashboard_url: https://example.com/certifai
  agents:
    enabled: true
    reviewers:
      - id: github/app-bot
        max_scrutiny: medium
        allow_finalize: false
        notes: low risk automation
""".strip()
        + "\n",
        encoding="utf-8",
    )

    policy = load_policy(config)
    assert policy.enforcement.ai_composed_requires_high_scrutiny is False
    assert policy.enforcement.min_coverage == 0.9
    assert policy.reviewers == ("Mentor", "Auditor")
    assert policy.integrations.pr_bot.enabled
    assert policy.integrations.pr_bot.platforms == ("github",)
    assert policy.integrations.pr_bot.reviewer_groups == ("ai-reviewers",)
    assert policy.integrations.pr_bot.status_check == "certifai/pr"
    assert policy.integrations.pr_bot.agents_allowed == ("bot-1",)
    assert policy.integrations.security.enabled
    assert policy.integrations.security.scanners[0].name == "snyk"
    assert policy.integrations.security.scanners[0].command == "snyk test --json"
    assert policy.integrations.publishing.enabled
    assert policy.integrations.publishing.destinations[0].type == "wiki"
    assert policy.integrations.publishing.destinations[0].path == "docs/certifai.md"
    assert policy.integrations.ci.enabled
    assert policy.integrations.ci.min_coverage == 0.95
    assert policy.integrations.ci.fail_on_vulnerabilities == "high"
    assert policy.integrations.audit.enabled
    assert policy.integrations.audit.log_path == ".certifai/audit.log"
    assert policy.integrations.agents.enabled
    assert policy.integrations.agents.reviewers[0].id == "github/app-bot"
    assert policy.integrations.agents.reviewers[0].max_scrutiny == "medium"
    assert not policy.integrations.agents.reviewers[0].allow_finalize
