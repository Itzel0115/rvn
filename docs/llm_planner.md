# Phase 7A LLM Planner

## Goal

Phase 7A adds an experimental LLM-guided planner that can suggest a structured tool plan while keeping the final answer deterministic.

This phase does:

- let an LLM propose a JSON tool plan
- validate the plan against a strict allowlist
- fall back to deterministic routing if planning fails
- keep final answer generation inside the existing `answer_contract.py`

This phase does not:

- let the LLM generate the final answer
- let the LLM calculate numbers
- let the LLM claim root cause
- let the LLM forecast future performance

## Planner Scope

The LLM planner only returns structured planning output:

- `question_type`
- `domains`
- `tools`
- `answer_mode`
- `requires_limitations`
- `unsupported_reason`

The planner never answers the user question directly.

## Allowed Tools

The planner is restricted to this allowlist:

- `get_metric_table`
- `get_top_groups`
- `get_platform_ranking`
- `get_platform_ratios`
- `get_anomalies`
- `get_yoy_mom_breakdown`
- `get_contribution_analysis`
- `get_inventory_turnover_proxy`
- `get_root_cause_candidates`
- `get_chart_payload`
- `get_chart_table`
- `get_data_coverage`
- `get_mapping_summary`
- `get_tool_capability_matrix`

Each tool also has validated allowed arguments, metrics, and dimensions.

## Prompt Modes

The planner now supports two prompt modes:

- `slim`
  Default. Uses a compact tool registry, a short rule list, and a single minimal JSON example.
- `full`
  Debug mode. Keeps the longer registry-style prompt for comparison.

You can switch modes with:

- environment variable `LLM_PLANNER_PROMPT_MODE=slim|full`
- or the `LLMToolPlanner(..., prompt_mode=...)` constructor

`slim` is a latency optimization only. It does not change validation, allowlists, or `/api/ask`.

## Dynamic Tool Subset

The prompt no longer shows the full allowlist on every question.

Instead, the planner prompt uses a deterministic subset:

- chart questions
  `get_chart_payload`, `get_chart_table`, `get_data_coverage`
- why / cause / diagnosis questions
  `get_yoy_mom_breakdown`, `get_contribution_analysis`, `get_inventory_turnover_proxy`, `get_root_cause_candidates`, `get_anomalies`, `get_platform_ratios`
- ranking questions
  `get_top_groups`, `get_platform_ranking`, `get_data_coverage`
- data quality questions
  `get_data_coverage`, `get_mapping_summary`, `get_tool_capability_matrix`
- general overview questions
  `get_yoy_mom_breakdown`, `get_contribution_analysis`, `get_inventory_turnover_proxy`, `get_root_cause_candidates`, `get_data_coverage`
- forecast questions
  safe coverage tools only

Validation still uses the full `ALLOWED_TOOL_REGISTRY`. The subset only affects what is shown to the LLM.

## Fallback Strategy

If any of the following happens, the system falls back to the existing deterministic router:

- LLM call fails
- LLM JSON is invalid
- planner returns an unknown tool
- planner returns invalid arguments
- planner violates safety rules

Fallback keeps the existing Phase 1-6 deterministic path unchanged.

## Safety Rules

- planner output must be JSON only
- planner cannot select more than 5 tools
- planner cannot invent tools
- why/cause questions must set `requires_limitations=true`
- forecast questions must return `unsupported` or only use safe coverage tools
- planner output is validated before execution

## Relationship to Deterministic Routing

- deterministic routing remains the default path
- `use_llm_planner=False` by default
- when enabled, the LLM planner acts as a planning overlay
- filters still come from deterministic routing
- final answer still comes from deterministic evidence and `answer_contract.py`

## Current Toggle

Phase 7A is experimental and off by default.

It can be enabled through:

- `MultiAgentAssistant(..., use_llm_planner=True)`
- environment variable `USE_LLM_PLANNER=true`

If no usable LLM is available, the assistant automatically falls back to the deterministic path.

## Planner Evaluation

Phase 7A.5 adds a planner-only evaluation path through:

- [scripts/eval_llm_planner.py](/C:/Users/itzel.hsiao/Desktop/revenue-poc/scripts/eval_llm_planner.py)
- `eval/llm_planner_eval_results.csv`
- `eval/llm_planner_eval_report.md`

This evaluation compares:

- deterministic routing and tools
- planner success or fallback
- planned tools
- overlap with deterministic expected tools
- extra or missing tools
- safety-rule enforcement

Mock mode is supported with `--mock` so evaluation can run even when no real LLM is available.

## Metrics

The planner eval report includes:

- `planner_success_rate`
  Share of cases where the planner returned a valid structured plan.
- `planner_fallback_rate`
  Share of cases where the planner failed and the system would rely on deterministic routing.
- `invalid_plan_rate`
  Share of cases rejected because the returned plan violated schema or safety rules.
- `avg_tool_count`
  Average number of planned tools across successful planner outputs.
- `tool_overlap_rate`
  Average overlap between planned tools and deterministic expected tools after filtering to the planner allowlist.
- `unknown_tool_rejection_count`
  Number of planner outputs rejected for inventing tools outside the allowlist.
- `invalid_args_rejection_count`
  Number of planner outputs rejected for invalid args, metrics, or dimensions.
- `why_requires_limitation_pass_rate`
  Pass rate for the rule that why/cause questions must require limitations.
- `forecast_safety_pass_rate`
  Pass rate for the rule that forecast questions must stay unsupported or use only safe coverage tools.

## Debug Trace

Planner validation now records an internal trace for evaluation and debugging only. The trace can include:

- `question`
- `raw_planner_response`
- `validated_plan`
- `rejected_reason`
- `materialized_tools`
- `fallback_reason`

This trace is used by the planner eval script and internal logs. It is not added to the `/api/ask` response contract.

## How To Read The Metrics

- A high `planner_success_rate` means the planner is producing schema-valid plans more often.
- A high `planner_fallback_rate` means the deterministic path is still absorbing planner failures safely.
- A non-zero `invalid_plan_rate` is acceptable during experimentation as long as fallback remains safe.
- `tool_overlap_rate` is a quality signal for planning alignment, not a correctness proof for the final answer.

## Why Phase 7A.5 Still Does Not Let LLM Write Answers

Planner evaluation is isolated from answer generation on purpose:

- the final answer must remain grounded in deterministic evidence
- safety rules are easier to audit when planning and answering stay separate
- planner quality can be improved without changing the stable `/api/ask` output contract

## Live Smoke Test

Phase 7C adds a live smoke test script:

- [scripts/smoke_llm_live.py](/C:/Users/itzel.hsiao/Desktop/revenue-poc/scripts/smoke_llm_live.py)

How to run:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py
```

Default behavior:

- without `--live`, the script writes an availability / skip report only
- this is the safe default for environments where a live model may be unreachable or unstable
- the report still records whether an LLM endpoint was detected

Timeout behavior:

- the live smoke script now uses `--timeout-seconds`, with a default of at least `120`
- it also inherits the configured baseline from [config.py](/C:/Users/itzel.hsiao/Desktop/revenue-poc/config.py)
- timeout failures are reported as `llm_timeout`, not as planner validation failures
- live smoke also records `planner_prompt_mode`, `compact_registry_tool_count`, and `prompt_char_count`

If a live LLM is configured and reachable, you can also run:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py --live
```

Planner-only live smoke:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py --live --planner-only --timeout-seconds 30 --warmup
```

Warmup behavior:

- `--warmup` sends one simple JSON request before the case loop
- if warmup fails, the report records `warmup_failed` and exits cleanly
- warmup failure is diagnostic only; it does not change `/api/ask`

If you want the script to fail when no live LLM is available:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py --live --require-llm
```

The current project uses the existing `OllamaClient` settings from [config.py](/C:/Users/itzel.hsiao/Desktop/revenue-poc/config.py):

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`

## How To Read Live Fallback Rate

- A higher planner fallback rate means the live planner is still often failing validation or connectivity checks.
- A low fallback rate is useful, but it does not automatically mean the planner is safe enough for production rollout.
- Live smoke is a stability check, not a production enablement decision.

Prompt slimming can reduce latency pressure, but it does not by itself justify enabling the planner in production.

## How To Read Timeout vs Validation Failure

- `llm_timeout` means the endpoint was reachable but the model did not respond in time.
- `llm_unavailable` means the endpoint or client was not usable at all.
- `invalid_json` means the model responded, but not with parseable JSON.
- `planner_validation_failed` means the planner returned JSON that violated the allowlist or safety rules.

These should be read differently:

- timeout is an infrastructure or runtime reliability issue
- validation failure is a planner quality or prompt-compliance issue

## Why Live Smoke Does Not Mean Official Enablement

Even if the live planner performs well:

- deterministic routing remains the stable baseline
- planner output is still experimental
- production enablement requires separate rollout decisions, monitoring, and likely more real-question sampling
- live planner success should be verified again after prompt changes, because lower prompt size does not guarantee consistent JSON behavior
