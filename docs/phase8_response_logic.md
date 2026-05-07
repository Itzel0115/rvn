# Phase 8 Response Logic

## Scope

Phase 8A adds a minimal deterministic response-logic skeleton without replacing the existing router, tools, or answer path.

The goal is to make the system carry three new backward-compatible objects:

- `task_profile`
- `answer_plan`
- `answer_contract.display_blocks`

This phase does not enable the LLM planner or rewriter, and it does not let an LLM decide business conclusions.

## TaskProfile

`TaskProfile` is defined in `task_profile.py`.

It describes the business task implied by the question:

- `task_family`
- `business_intent`
- `target_entity`
- `metrics`
- `time_scope`
- `comparison_axis`
- `polarity`
- `analysis_depth`
- `answer_style`
- `requires_table`
- `requires_limitations`

Phase 8A supports these deterministic mappings first:

- `cross_section_compare`: same-month platform comparison, such as comparing August platform revenue and inventory.
- `performance_assessment`: platform best/worst performance questions.
- `time_compare`: period-over-period change and contribution questions.

Other questions fall back to the existing `question_type` / `answer_strategy` mapping.

## AnswerPlan

`AnswerPlan` is defined in `answer_plan.py`.

It records which tool outputs are intended to be primary, supporting, background, or forbidden as primary evidence:

- `primary_tools`
- `supporting_tools`
- `background_tools`
- `forbidden_primary_tools`
- `max_key_observations`
- `requires_table`
- `display_debug_findings`
- `conclusion_policy`

Phase 8A uses the plan mainly as response metadata and display guidance. It also lightly hints existing deterministic tool selection for the three new task families so the current agents can produce the required evidence.

## Display Blocks

`answer_contract.display_blocks` now follows this shape:

```json
{
  "headline": "...",
  "key_observations": [],
  "table": null,
  "limitations": []
}
```

The frontend should treat `display_blocks` as the executive projection of the answer. `domain_results.key_findings` remain available for backward compatibility and debugging, but they should not be flattened into primary highlights when display blocks exist.

## Phase 8B Rubric Registry

Phase 8B adds `analysis_rubrics.py`.

The registry assigns every deterministic evidence item one role:

- `primary`: may support the headline and key observations.
- `supporting`: may support key observations after primary evidence.
- `background`: retained in `role_based_evidence`, but not projected into executive highlights.
- `debug`: retained for trace/debug only.

Each role item records:

- `role`
- `evidence_type`
- `source_tool`
- `summary`
- `details`
- `display_priority`
- `reason`

`answer_contract.role_based_evidence` is backward-compatible metadata. It does not replace existing `evidence`, `tools_used`, or `domain_results`.

## Role-Based Display Projection

`answer_contract.display_blocks.key_observations` is now selected from role-based evidence:

1. take `primary` evidence first
2. then take `supporting` evidence
3. stop at `answer_plan.max_key_observations`
4. never include `background` or `debug`

If there is no primary evidence, the headline must say that there is not enough evidence to form a clear conclusion. The system must not promote background evidence into the headline.

Current rubric behavior:

- `cross_section_compare`: platform same-month revenue/inventory ratio is primary; same-month anomaly is supporting; MoM contribution, overall trend, correlation, and ranking are background.
- `performance_assessment`: inventory turnover proxy and platform ratios are primary; anomalies and momentum are supporting; inventory amount ranking alone is background.
- `time_compare`: YoY/MoM and contribution analysis are primary.
- `diagnosis`: root-cause candidates and contribution analysis are primary; anomaly, turnover proxy, and YoY/MoM are supporting.
- `ranking`: explicitly requested metric ranking is primary.
- `risk_scan`: anomaly and inventory turnover proxy are primary; platform ratios are supporting.

## Why Not Full Rubric Registry Yet

The full Phase 8 design includes a richer Evidence Store, Evidence Interpreter, and Conclusion Builder. Those are intentionally deferred because implementing all of them at once would change too much of the answer path.

Phase 8A established the minimum stable interface:

- classify the business task separately from legacy `question_type`
- carry an answer plan without removing existing routing fields
- project a small number of relevant observations into `display_blocks`
- keep `/api/ask` backward compatible

Phase 8B formalizes the evidence role assignment behind that interface.

## Phase 8C Evidence Projector

Phase 8C adds `evidence_projector.py`.

The projector is the deterministic bridge from role-scored evidence to executive-facing display blocks. `answer_contract.py` still collects evidence, limitations, tools, and role metadata, but it no longer owns the role-based task-specific projection path. It calls:

```python
build_display_blocks_from_roles(task_profile, answer_plan, rubric_result, limitations)
```

The projector returns:

```json
{
  "headline": "...",
  "key_observations": [],
  "table": null,
  "limitations": []
}
```

### Conclusion Builder

Conclusion formation is deterministic and uses only `primary` evidence for the main headline:

- `cross_section_compare`: derives the top revenue platform, top inventory platform, and weakest revenue/inventory proxy platform from same-month primary platform evidence.
- `performance_assessment`: derives weak platform conclusions from the lowest revenue/inventory proxy or anomaly evidence. For best/strong questions, if current evidence only identifies weak-side platforms, the headline must say evidence is insufficient to clearly identify the best platform and only recommend excluding weak candidates.
- `time_compare`: uses contribution evidence first when the question is about who contributed to the change, then period-over-period change evidence.
- `diagnosis`: keeps a conservative wording: root cause is not confirmed, but candidate observation directions can be listed.
- `risk_scan`: uses top anomaly evidence first, falling back to weak inventory-efficiency proxy evidence.

### Observation Projection

`display_blocks.key_observations` are projected analytical sentences rather than raw evidence summaries. They still cannot introduce new facts. For example, a revenue/inventory proxy item can say that a low proxy indicates weaker revenue relative to inventory in the current data, but it cannot claim operational root cause or forecast future results.

Projection rules:

1. take `primary` evidence first
2. then take `supporting` evidence
3. deduplicate display-level repeats
4. stop at `answer_plan.max_key_observations`
5. never project `background` or `debug`

### Table Projection

When `task_profile.requires_table` or `answer_plan.requires_table` is true, the projector builds a table only from primary evidence. The current table columns are:

- `month`
- `platform`
- `revenue`
- `inventory_amount`
- `inventory_qty`
- `revenue_inventory_ratio`

If primary evidence does not contain table-ready platform rows, `table` remains `null`. Background evidence is never used to fill the table.

## Phase 8D Platform Performance Snapshot

Phase 8D adds `get_platform_performance_snapshot` in `analysis_tools.py`.

The tool produces a deterministic platform scorecard for one month. It is designed for `performance_assessment` questions such as "which platform performs better/worse" and can also provide table-ready evidence for same-month platform comparison questions.

Each row includes:

- `month`
- `platform`
- `revenue`
- `revenue_rank`
- `inventory_amount`
- `inventory_rank`
- `inventory_qty`
- `revenue_inventory_amount_ratio`
- `efficiency_rank`
- `revenue_mom_change`
- `revenue_mom_change_pct`
- `anomaly_count`
- `health_score`
- `risk_score`
- `performance_label`
- `primary_strength`
- `primary_risk`

The output also includes a summary:

- `best_platform`
- `weakest_platform`
- `top_revenue_platform`
- `top_inventory_platform`
- `highest_efficiency_platform`
- `lowest_efficiency_platform`

### Score Rubric

The score is deterministic and explainable:

- revenue scale: 30%
- revenue momentum: 20%
- revenue/inventory amount efficiency proxy: 35%
- anomaly score: 15%

The health score is normalized to `0..1`. If one component cannot be computed, the available component weights are renormalized instead of inventing missing facts. `risk_score` is currently `1 - health_score`.

The score intentionally does not treat high inventory amount as healthy. It also does not treat high inventory amount alone as unhealthy; inventory pressure must be interpreted with revenue relative to inventory, momentum, and anomaly evidence.

### Tool Integration

`AnswerPlan` now treats `get_platform_performance_snapshot` as a primary tool for `performance_assessment` and as table-ready primary evidence for `cross_section_compare`.

`multi_agent.py` gives the financial metrics agent this tool first for platform performance questions, followed by existing proxy, ratio, and anomaly tools.

`analysis_rubrics.py` recognizes:

- `platform_performance_snapshot`
- `platform_performance_row`

For `performance_assessment`, scorecard evidence is primary. For `cross_section_compare`, scorecard rows can also be primary and table-ready.

`evidence_projector.py` uses the scorecard to form stronger deterministic conclusions:

- best/healthy questions can name `best_platform` when scorecard evidence exists
- worst/attention questions can name `weakest_platform`
- cross-section questions can project scorecard rows into the display table

### Limitations

The scorecard is not a forecast and does not claim root cause. It is also not a formal inventory turnover metric.

Current limitations are surfaced in tool output:

- deterministic platform performance scorecard only
- no gross margin, orders, shipments, pricing, or customer mix
- revenue/inventory efficiency is a proxy, not formal inventory turnover

## Next Phases

Phase 8E can finish frontend separation between executive display blocks and debug agent traces.

Phase 8F should expand deterministic eval to cover task family, answer plan, display blocks, scorecard evidence, and negative evidence leakage.
