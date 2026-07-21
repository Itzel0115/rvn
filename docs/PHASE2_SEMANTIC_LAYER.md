# Phase 2: Semantic Layer and MCP acceptance notes

Phase 2 adds a versioned, framework-neutral semantic catalog and an optional read-only MCP boundary. It does not change the Phase 1 runtime loop or require a running MCP server for CLI, HTTP API, legacy mode, or stateful mode.

## Catalog and coverage

Definitions live in `semantic_layer/definitions/`:

- `metrics.json`: revenue amount, inventory amount, inventory quantity, and a revenue/inventory amount proxy.
- `dimensions.json`: month, business group, and product line 5.
- `task_evidence.json`: semantic requirements for entity-month lookup, revenue/inventory relationship, and performance assessment.
- `glossary.json` and `data_contracts.json`: definitions only; no rows, source paths, or company values.
- `task_coverage.json`: every known canonical task is explicitly `semantic`, `legacy`, or `unsupported`; no task silently falls through.

Trend, ranking, contribution and period change are supported operations on a metric, not invented metrics. The ratio is explicitly a proxy, is not formal turnover, has no COGS/average-inventory basis, and is never causal evidence. Missing values and zero denominators retain the existing toolbox limitation semantics.

Validate and regenerate the reference:

```bash
uv run python -m semantic_layer.validation
uv run python -m semantic_layer.generate_reference
```

`docs/SEMANTIC_CATALOG_REFERENCE.md` is generated and tested for equality with the definitions.

## Runtime integration

For semantic-covered tasks, the canonical profile resolves a concise requirement ID. `semantic_layer.adapters.enrich_answer_plan` projects only IDs, required evidence, partial rule, and limitations into the existing `AnswerPlan`; it never embeds the full catalog in runtime state/API responses. Phase 1 still uses the existing `PlanValidator`, tool registry, toolbox dispatcher, evidence projection, answer contract, and writer validation. Replans are revalidated by the same plan validator.

A successful tool call is insufficient on its own: relationship completion requires paired revenue and inventory change evidence from `get_revenue_inventory_relationship`. `get_entity_performance_snapshot` is supporting/diagnostic only for relationship work. When no legal non-duplicate repair exists, the runtime stops with `capability_gap`, not `invalid_replan`; the answer contract receives the required limitation.

## Optional MCP server

Start only when an MCP client needs it:

```bash
uv run python -m mcp_server.server
```

The server uses official `mcp==1.28.1` stdio transport. stdout is protocol-only; no startup banner or application logging is printed there. It exposes safe catalog resources and six registry-derived low-risk, read-only tools:

- `get_entity_month_table`
- `get_entity_metric_ranking`
- `get_entity_performance_snapshot` (supporting scorecard, not relationship primary evidence)
- `get_overall_time_series`
- `get_revenue_inventory_relationship`
- `get_data_coverage`

Resources: `semantic://catalog/summary`, `semantic://metrics`, `semantic://metrics/{metric_id}`, `semantic://dimensions`, `semantic://dimensions/{dimension_id}`, `semantic://tasks/{task_type}`, `semantic://tools`, `semantic://data-contracts`, and `semantic://data-freshness`.

MCP is default-deny: only registry `mcp_exposable`, `read_only`, `risk_level=low` tools are registered. Inputs are period/metric/dimension/cap checked; outputs are JSON-safe, row-capped at 20, remove source paths/tracebacks, and never expose shell, SQL, Python, filesystem, writes, raw DataFrames, or raw rows beyond the cap. MCP initialization is lazy and core runtime imports do not start a server or load source data.

Known limitations: there is no CLI resume flag, no LLM replan, and performance assessment remains an explicit deterministic heuristic/proxy. Frontend is unchanged by Phase 2.
