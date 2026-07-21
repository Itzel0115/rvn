# Phase 3: Proactive Investigation Workflow

Phase 3 adds a one-shot, default-deny workflow:

```text
refresh fingerprint → quality gate → deterministic candidates → Phase 1 investigation
→ NOT APPROVED draft → human approval → fixed local approved artifact
```

It reuses canonical tasks, AnswerPlan, PlanValidator, StatefulAgentRuntime, evidence validation, replanning, semantic catalog, deterministic tools, and answer/writer contracts. It does not run a daemon, send notifications, modify source data, or auto-approve.

## Data refresh and quality

`proactive_workflow.fingerprint` produces `logical-metadata-sha256.v1` from logical dataset IDs, sorted schema, row count, period bounds, and stable aggregates—never raw rows. `data_quality` validates contracts, empty data, periods, overlap, numeric missing values, duplicate logical keys, entity availability, continuity, and schema failures. Critical blockers create quality candidates and prevent business investigations.

## Candidates and investigation

The relationship detector calls the existing `get_revenue_inventory_relationship` tool. A divergence requires paired revenue decrease and inventory increase for the same entity and period pair. It is descriptive only; scorecards are supporting context, never relationship primary evidence. The candidate is converted to a structured question and executed through the existing stateful assistant path. Counter evidence is explicitly `not_available` unless a dedicated result exists.

## Draft, approval, publication

Drafts are deterministic, Markdown/JSON, content-hashed, versioned; revisions create a new draft version and mark the previous version superseded, and visibly `NOT APPROVED`. They are stored below `output/investigations/drafts/`. Approval requires an explicit human approver and binds to the exact content hash. Only approved, hash-matching drafts can be copied to `output/investigations/approved/`; existing artifacts are never overwritten.

## CLI

```bash
uv run python -m proactive_workflow.cli scan
uv run python -m proactive_workflow.cli scan --force
uv run python -m proactive_workflow.cli list-candidates
uv run python -m proactive_workflow.cli list-approvals
uv run python -m proactive_workflow.cli approve ID --approver "name"
uv run python -m proactive_workflow.cli publish ID --publisher "name"
```

The CLI is cron-friendly one-shot. There is no `--auto-approve`.

## Known limitations

Only relationship and quality candidates are currently enabled; persistent-trend and performance-risk candidates remain future extensions. No CLI resume, LLM replanning, dashboard inbox, remote publication, email, Slack, Teams, webhook, or write-back is implemented. Phase 4 can add observability from the SQLite audit records.


## Closure audit additions

### Revision lifecycle

```text
pending v1 → request_revision → revision_requested v1
→ create-revision (explicit revised_by + instructions)
→ v1 superseded + new v2 draft + new pending approval bound to v2 hash
→ explicit human approve v2 → local approved artifact
```

`create-revision` accepts instructions, not arbitrary rewritten report text. It rebuilds from the existing investigation evidence/limitations, so it cannot inject unsupported numbers or turn descriptive/proxy evidence into causal/formal KPI claims. CLI: `uv run python -m proactive_workflow.cli create-revision ID --revised-by "name" --instructions "..."`; API: `POST /api/approval-requests/{id}/create-revision`.

### Detector/evidence matrix

| Candidate | Initial signal | Investigation task / primary evidence | Metrics | Period | Limitation |
|---|---|---|---|---|---|
| revenue_drop | relationship data source only | entity time series / revenue evidence | revenue_amount | entity period pair | does not require inventory evidence |
| inventory_increase | relationship data source only | entity time series / inventory amount | inventory_amount | entity period pair | amount is not quantity |
| inventory_quantity_increase | entity time series | entity time series / inventory quantity | inventory_qty | entity period pair | quantity is not amount |
| revenue_inventory_divergence | paired relationship row | metric relationship / paired changes | revenue_amount + inventory_amount | same entity, same pair | descriptive; snapshot supporting only |
| data_quality_issue | quality gate | data quality | none | n/a | not a business conclusion |

### Counter evidence and identity

Counter statuses are typed: `not_found`, `not_available`, `inconclusive`, `contradicted`, `weakened`, and `confirmed`. `not_available` explicitly means the search cannot be performed and **does not mean no counterevidence**; it cannot raise confidence. Contradicted/weakened/inconclusive results cap confidence.

CLI/API identities are application-layer caller strings with `identity_source=cli_supplied` or `api_supplied` and `identity_verified=false`. They are not authenticated identities, and this POC is not a SSO/RBAC or compliance-signoff system. Persistent trend and frontend inbox remain unimplemented.
