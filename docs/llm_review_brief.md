# Certifai Overview and Workflow Brief

## Core Capabilities (Extended)
- **Decorator-driven provenance**: Every discovered function/class can be annotated with `@certifai(...)`, embedding structured metadata about AI composition, human and agent reviewers, scrutiny level, notes, history, and completion status (`done=True`). Decorator parsing is resilient to both modern `reviewers=[{...}]` payloads and legacy `agents=["id"]` lists by normalising into `TagMetadata.reviewers` entries.
- **Lifecycle automation**:
  - `certifai annotate` discovers Python artifacts via `ast` parsing, injecting new decorator blocks (with configurable AI agent defaults) when missing.
  - `certifai certify` performs in-place metadata rewrites, updating `human_certified`, `scrutiny`, `history`, `reviewers`, and clearing `done` (finalized artifacts are skipped unless `--include-existing` is set).
  - `certifai certify-agent` mirrors the human command but enforces policy-configured agent permissions before appending an agent reviewer entry; both commands use the shared `_rewrite_metadata` pipeline.
  - `certifai finalize` computes AST-stable digests (via `certifai/digest.py`), records registry entries in `.certifai/registry.yml`, prunes inline metadata to minimal `done=True` markers, and preserves detailed history out-of-band.
  - `certifai check` (a.k.a. `reconcile_registry`) reopens artifacts whose digest no longer matches registry entries, rehydrating decorator metadata from registry records and stripping `done=True`.
- **Agent reviewer support**: `TagMetadata` exposes rich reviewer info (`ReviewerInfo`) with `kind` (human/agent), `id`, `scrutiny`, `timestamp`, and optional notes. `agents` properties provide legacy compatibility. Coverage, policy enforcement, PR status, and audit logging natively handle blended human/agent reviewer sets.
- **Coverage & policy enforcement**: `provenance.enforce_policy` evaluates AI scrutiny rules, handles ignore lists, and (with the new logic) credits allowed agents toward coverage thresholds based on their configured `max_scrutiny`. `enforce.enforce_ci` orchestrates coverage evaluation, security scanner results, and PR status computation to produce machine-readable pass/fail payloads and human-readable messages.
- **Security scanner integration**: `integrations/security.py` composes shell commands (with optional `{targets}` placeholder), executes them with environment isolation, and attempts JSON decoding to store findings; non-JSON output is preserved raw. Results feed into CI enforcement and audit logs.
- **Publishing**: `certifai/publishing.py` renders markdown tables (via `emit_markdown_table`) and writes them to wiki/docs paths, optionally staging files with `git add` for documentation branches.
- **PR/CI integrations**:
  - `certifai pr status` outputs JSON detailing status checks, coverage metrics (with agent-adjusted ratios), pending artifact descriptors, and separate lists for AI-pending vs agent-only approvals.
  - `.github/workflows/certifai.yml` demonstrates a minimal GitHub Action running the `enforce` command; more complex pipelines can chain `certify-agent`, scanners, and publishing steps.
- **Audit logging**: Implemented in `certifai/audit.py`, logging functions accept optional overrides for log destination, emit JSONL with consistent keys (`timestamp`, `action`, `data`), and are invoked from human certification, agent certification, finalization, and enforcement pathways. `audit show` surfaces logs for analysts/LLMs.

## Detailed Workflows
### 1. Human Review Lifecycle
1. **Preparation**
   - Run `certifai annotate path/to/module.py --policy .certifai.yml` if metadata blocks are absent. The command respects `ignore_unannotated` policy settings.
2. **Certification**
   - Execute `certifai certify path/to/module.py --reviewer Alice --scrutiny high --notes "Pair reviewed" --policy .certifai.yml`.
   - The command: parses AST, filters eligible artifacts (skipping ones already finalized unless `--include-existing`), updates decorators (adding `reviewers=[{"kind": "human", ...}]`), and logs an audit entry `{"action": "certify", "reviewer": "Alice"}`.
3. **Policy enforcement**
   - `certifai enforce` (in CI) recalculates coverage, ensuring high scrutiny for AI-authored code and evaluating security scanners. Failures surface as GitHub status check errors and CLI non-zero exits.
4. **Finalization**
   - After all conditions satisfied, run `certifai finalize module.py --policy .certifai.yml`. The command updates `.certifai/registry.yml`, writes digests, trims inline metadata to `@certifai(done=True, human_certified="Alice")`, and logs `action="finalize"` entries.
5. **Registry Reconciliation**
   - Pre-commit or CI hook executes `certifai check --registry-root .` to detect drift; reopened artifacts regain full metadata and are removed from registry.

### 2. Agent Review Lifecycle
1. **Configure Agent in Policy**
   ```yaml
   integrations:
     agents:
       enabled: true
       reviewers:
         - id: github/apps/certifai-agent
           max_scrutiny: medium
           allow_finalize: false
           notes: "Runs unit + integration tests"
   ```
   - `max_scrutiny` uses `auto|low|medium|high`. Agents attempting higher scrutiny will be blocked.
   - `allow_finalize` controls whether the agent alone can keep artifacts finalized; if false, human approval is required before finalization.
2. **Agent Certification Command**
   - `certifai certify-agent module.py --agent github/apps/certifai-agent --scrutiny medium --policy .certifai.yml`.
   - Policy enforcement ensures the agent is whitelisted and scrutiny does not exceed limits. Metadata gains `agent_certified`, `reviewers=[{"kind": "agent", ...}]`, and history notes such as `"agent github/apps/certifai-agent certified (medium)"`.
   - Audit log entry: `{"action": "certify", "reviewer": "github/apps/certifai-agent"}` (differentiated by `kind` in `data`).
3. **Coverage and PR Status**
   - `certifai pr status` compares agent approvals with policy. If coverage thresholds rely on a mix of human + agent approvals, `coverage` check passes with `agent_ratio` details; pending lists exclude agent-satisfied functions.
4. **Human Escalation**
   - For high-risk modules, configure `require_human_review: true` (in CI settings). Even with agent approval, enforcement will fail until a human reviews or policy is adjusted.
5. **Reports & Dashboards**
   - `certifai publish report` includes counts of human vs agent-certified functions (`Agent-certified` row in markdown table). External dashboards can correlate audit log entries with coverage to verify agent effectiveness.

### 3. PR Workflow Integration (GitHub-centric)
1. GitHub Action runs `certifai pr status` and `certifai enforce`. The check outputs include:
   - `coverage`: pass/fail with `actual`, `required`, and `agent_ratio` fields.
   - `policy`: list of enforce_policy violations (e.g., missing high scrutiny human review).
   - `ai_pending`: count of AI-authored functions lacking permitted reviewers.
2. A GitHub App or bot consumes JSON to annotate PRs:
   - Inline comments for `pending_artifacts` (with file/line info).
   - Summary comment referencing agent-only approvals, encouraging human review if required.
3. Optional: `certifai publish report` in workflow attaches coverage markdown to PR artifacts or pushes it to docs branch.

### 4. Audit & Compliance Review
- `certifai audit show --policy .certifai.yml --limit 50 --output pretty` -> lists chronological entries (`certify`, `finalize`, `enforce`) with actor IDs (human or agent), notes, timestamps, and statuses.
- Build dashboards (e.g., Streamlit, Superset) consuming JSONL for filtering by reviewer type, time windows, or file patterns.
- Audit log structure includes:
  ```json
  {
    "timestamp": "2025-11-08T22:02:51.931248+00:00",
    "action": "certify",
    "data": {
      "artifact": "foo",
      "filepath": "src/module.py",
      "reviewer": "github/apps/certifai-agent",
      "scrutiny": "medium",
      "notes": null,
      "ai_composed": "gpt-5"
    }
  }
  ```

## Technical Architecture Highlights
- **Metadata parsing (`decorators.py`)**: Uses `ast` to detect `@certifai` calls, convert keyword/value pairs (including nested dicts/lists), and produce `TagMetadata`. `_literal_value` is extended to parse dictionaries for structured reviewers.
- **TagMetadata**: Methods like `from_decorator_kwargs`, `to_decorator_payload`, `clone`, `is_pending_certification`, and helper properties manage hybrid states (legacy agent strings + new reviewer entries). `agent_ids` synthesises unique agent IDs from both sources.
- **Policy parsing (`policy.py`)**: `_parse_integrations` now instantiates `AgentSettings`/`AgentPermission`, capturing `id`, `max_scrutiny`, `allow_finalize`, and `notes`. Defaults keep agents disabled unless explicitly enabled.
- **Enforcement logic (`provenance.enforce_policy`)**: Agent approvals counted when ID is in `policy.integrations.agents.reviewers` and reviewer scrutiny <= `max_scrutiny` (falling back to `AUTO` if unspecified). Coverage enforcement respects `ignore_unannotated` toggle.
- **PR status builder (`integrations/github.py`)**: Produces coverage ratios based on `_is_certified` logic shared with enforcement. Adds `agent_only` counts for transparency. Status checks capture coverage, policy, and AI pending states.
- **Audit module (`audit.py`)**: Appends JSON to log file with minimal dependencies (using `datetime` + `pathlib`), enabling external ingestion.
- **Tests**: Agent-specific tests confirm CLI commands, policy gating, coverage credit, and audit logging.

## Adding/Managing Agent Reviewer Groups (Step-by-Step)
1. **Policy Update**: Add agent details under `integrations.agents.reviewers` with appropriate scrutiny limits. Example:
   ```yaml
   integrations:
     agents:
       enabled: true
       reviewers:
         - id: github/apps/doc-reviewer
           max_scrutiny: low
           allow_finalize: false
           notes: "Docs grammar + formatting"
         - id: github/apps/test-suite
           max_scrutiny: high
           allow_finalize: true
           notes: "Runs full test matrix"
   ```
2. **CLI Usage**:
   - `certifai certify-agent docs/guide.py --agent github/apps/doc-reviewer --scrutiny low` (for doc updates).
   - `certifai certify-agent src/service.py --agent github/apps/test-suite --scrutiny high` (after automated test run).
   - If an agent is not listed or exceeds `max_scrutiny`, the CLI exits with descriptive errors.
3. **Workflow Automation**:
   - GitHub Actions can call `certifai certify-agent` after successful test jobs, injecting agent approvals before human review.
   - Agents can be scoped by file path (e.g., run for `docs/` only) leveraging workflow conditions.
4. **Reporting**:
   - `certifai report --format json` reveals `agent_certified` counts and coverage ratios.
   - `certifai publish report` surfaces agent numbers in markdown tables.
   - PR status JSON indicates `agent_only` artifacts; bots can comment or set labels (e.g., `needs-human-review`) based on counts.
5. **Audit/Compliance**:
   - Use `certifai audit show` to track agent actions, ensuring change controls capture automated sign-offs.
   - Extend dashboards to differentiate `kind"="agent"` vs `kind"="human"` actions.
6. **Finalization Strategy**:
   - If `allow_finalize` is false, automated pipelines should not call `certifai finalize` until a human review occurs. Finalization logic checks for `done` + registry entry so agents cannot finalize restricted artifacts.

## Reporting & Dashboards (Deep Dive)
- **Markdown/CSV/JSON reports** (from `report.py`) include statistics:
  - `Agent-certified` count (number of artifacts with at least one agent reviewer).
  - `Pending review` count respects both human and agent certification (i.e., functions pending because no allowed reviewer has signed off).
  - `scrutiny_counts` summarise scrutiny levels, showing distribution across artifacts.
- **PR Status Fields**:
  - `counts.agent_only`: artifacts reviewed solely by agents (no human). Useful for highlighting where human action is optional/required.
  - `checks` entries provide structured information for bots to post summary statuses (pass/fail with context).
- **Audit Log Visualization**: Because logs are simple JSONL, external tools (e.g., Elastic/Kibana, BigQuery, or in-house dashboards) can ingest them. Key fields to index: `action`, `data.reviewer`, `data.scrutiny`, `timestamp`.

## Example End-to-End Automation Blueprint
1. Developer pushes commit; GitHub Action triggers.
2. Workflow steps:
   - `certifai annotate` (optional for new files).
   - Run tests and security scanners.
   - `certifai certify-agent ...` for `github/apps/test-suite` after tests succeed.
   - `certifai pr status` to generate JSON; GitHub App posts summary comment with agent coverage vs human requirements.
   - `certifai enforce` as final CI gate; failure stops merge if human review required or coverage thresholds unmet.
   - `certifai publish report` to update wiki/report artifacts.
3. Human reviewer uses CLI or UI to run `certifai certify` (if needed) before merging.
4. Once merged, run `certifai finalize` as part of release or nightly pipeline, storing digests and cleaning metadata.

## Current Test Snapshot
- **Command suite**: `pytest tests/test_cli.py` covers command-line interactions including new `certify-agent` logic.
- **Agent integration**: `tests/test_agent_integration.py` ensures CLI respects policy permissions, audit logs record agent actions, and metadata updates correctly.
- **Enforcement**: `tests/test_enforce.py` verifies agent approvals count towards coverage when policy allows.
- **Model parsing**: `tests/test_models.py` ensures TagMetadata round-trips agents/humans via decorator payloads.
- **Policy parsing**: `tests/test_policy.py` asserts agent configuration parsing and defaults.
- **Full test suite**: `pytest` yields `32 passed` confirming stability after agent integration.

## Review Checklist for External LLM
1. **Validate Schema Consistency**: Ensure all code paths producing/consuming metadata (parser, TagMetadata, registry, report, PR status) handle `reviewers` consistently.
2. **Agent Policy Enforcement**: Confirm CLI and enforcement logic reject unauthorized agents or over-scrutiny attempts with clear messages.
3. **Coverage Calculations**: Double-check that agent approvals adjust `coverage_ratio` and pending counts accurately in both enforcement and reporting.
4. **Audit Completeness**: Evaluate whether actions are sufficiently detailed for compliance (e.g., capturing agent vs human in `data`). Consider recommending additional metadata if needed.
5. **Documentation & UX**: Assess clarity of docs/examples for configuring agents, running commands, and interpreting outputs. Suggest improvements for discoverability.
6. **Security & Safety**: Review whether allowing agents to finalize or certify is properly guarded by policy, and propose enhancements if necessary (e.g., restricting agents by path or requiring multiple approvals).
7. **Extensibility**: Identify how easily the system can integrate with additional SCM platforms, dashboards, or workflow orchestrators. Highlight areas for modularization or API hooks.

This brief aims to equip another LLM with a complete picture of certifai’s current state, especially the new agent reviewer workflow, so it can perform in-depth reviews or propose further improvements. Please request additional sections (e.g., API references, sample PR status payloads, or registry formats) if needed.
