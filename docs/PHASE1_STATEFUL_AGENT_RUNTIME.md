# Phase 1: Stateful Agent Runtime

Phase 1 adds an inspectable, recoverable run loop without replacing the Excel pipeline, canonical task, answer plan, PlanValidator, toolbox, evidence contracts, writer validation, or deterministic fallback.

## Flow

```text
Before: question -> classify/canonicalize -> one plan -> tools -> answer
Now:   initialize -> plan -> PlanValidator -> one step -> evidence validation
       -> next step | deterministic repair -> answer contract -> checkpoint
```

`AgentRunState` has schema `agent-run-state.v1` and only JSON-safe data: request, canonical task, plan, compact execution summaries, evidence excerpts, validation, replan history, limits, and final metadata. It never stores DataFrames, clients, toolboxes, source Excel content, or full large outputs; checkpoint rows and nested collections are capped. The SQLite database may still contain compact analysis evidence and must remain local.

`PlanStep` lifecycle is `pending -> running -> succeeded|empty|failed|skipped`. The post-execution validator separately checks successful execution, empty/warning-only outputs, requested metric/month/period/entity coverage, trends, ranking/contribution rows, diagnosis support, and exhausted duplicate calls. Existing contracts continue to prevent causal claims from candidate evidence.

## Repair, limits, and storage

The deterministic replanner only selects registry-permitted tools declared by the answer plan, uses canonical arguments, and will not repeat failed/empty tool+argument pairs. Every proposed repair is revalidated with the existing `PlanValidator`; invalid repairs stop safely. In revenue/inventory relationship analysis, `get_entity_performance_snapshot` is supporting context only and can never replace paired relationship evidence. Every repair gets a new plan version and `ReplanRecord`.

Defaults: `AGENT_MAX_STEPS=8`, `AGENT_MAX_REPLANS=2`, `AGENT_MAX_STEP_ATTEMPTS=2`. Guards stop with `completed`, `insufficient_evidence`, `max_steps_reached`, `max_replans_reached`, `no_progress`, or `invalid_replan`.

Checkpoint database: `output/state/agent_runs.sqlite3` (Git-ignored). `SQLiteAgentStateStore.load(request_id)` supports a future resume command; tests demonstrate reopening it from another store instance.

## Reproducible test environment

The project manages pytest in its uv `dev` dependency group. From a clean checkout run:

```bash
uv sync
uv run pytest -q
```

Supported stateful task paths are registry-backed standard analysis tasks (for example entity tables, lookups, rankings, trends, period comparisons, contribution, relationship, risk, and performance assessment). Overview, data-quality, and chart requests intentionally retain their existing deterministic response paths.

## Compatibility

Stateful is the default; legacy remains available:

```bash
AGENT_RUNTIME_MODE=stateful .venv/bin/python main.py --question "有沒有營收下降但庫存上升的事業群？" --agent-json
AGENT_RUNTIME_MODE=legacy .venv/bin/python main.py --question "有沒有營收下降但庫存上升的事業群？" --agent-json
```

CLI/API response fields remain compatible. Stateful responses additionally expose concise `agent_runtime`, `agent_state_summary`, `execution_trace`, `replanning`, and `stop_reason`:

```json
{"status":"completed","step_count":1,"replan_count":0,"stop_reason":"completed","steps":[{"step_id":"p1-s1","tool_name":"get_revenue_inventory_relationship","status":"succeeded"}]}
```

## Limits and Semantic KPI Layer

Phase 1 deliberately uses deterministic repair rather than free-form LLM replan. LLM plan rejection is retained as `rejected_llm_then_deterministic` provenance. Summary, data-quality, and chart contracts stay on their existing deterministic paths. There is no CLI resume flag yet, although the store supports `load(request_id)`. The frontend production build was verified with `npm run build`; no frontend changes are required. A Semantic KPI Layer can later enrich canonical metrics and evidence requirements without changing this state schema.
