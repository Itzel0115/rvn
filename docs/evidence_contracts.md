# Evidence Contracts

Phase 11C-1 introduces `EvidenceContract` as an internal normalization layer for future LLM writer work. Phase 11C-2 adds an experimental `LLMEvidenceWriter` in shadow mode only.

`EvidenceContract` is not a frontend API contract and does not replace `answer_contract.py`, `evidence_projector.py`, or `display_blocks`. Current answers still use the deterministic projector and the existing `/api/ask` response fields.

## Purpose

The contract gives future writer components a clean, verifiable evidence shape:

- canonical task family
- canonical time scope
- canonical entity scope and parent entity
- canonical metric and metric label
- normalized rows and summary
- limitations and data quality flags
- source tool reference

This keeps the deterministic parser as the source of truth while allowing tool outputs with different native schemas to be converted into one writer-friendly format.

## Current Status

The production answer path still uses deterministic `answer_contract.py` / `evidence_projector.py` display blocks. Evidence contracts are built internally and logged:

- `evidence_contract_count`
- evidence types
- unsupported tool outputs

The contracts are not added to `/api/ask` response fields.

## Supported Tool Outputs

The builder currently normalizes these outputs:

- `get_entity_month_table` -> `entity_month_table`
- `get_entity_period_pair_table` -> `entity_period_pair_table`
- `get_entity_multi_month_table` -> `entity_multi_month_table`
- `get_entity_metric_value` -> `entity_metric_lookup`
- `get_entity_metric_ranking` -> `entity_metric_ranking`
- `get_entity_time_series` -> `entity_time_series`
- `get_overall_time_series` -> `overall_time_series`
- `get_period_pair_metric_comparison` / `get_entity_period_pair_comparison` -> `period_pair_comparison`
- `get_entity_cross_section_comparison` -> `cross_section_comparison`
- `get_entity_performance_snapshot` -> `entity_performance_snapshot`
- `get_revenue_inventory_relationship` -> `relationship_analysis`
- `get_entity_contribution_analysis` -> `contribution_analysis`
- chart payload/table outputs -> `chart_payload`
- data coverage/mapping outputs -> `data_quality`

Unsupported outputs are represented as `unsupported_tool_output` with a limitation instead of raising.

## Writer Shadow Mode

`LLMEvidenceWriter` is controlled by `USE_LLM_WRITER`; the default is `false`. This flag is separate from legacy `USE_LLM_REWRITER`, which remains disabled for the recommended demo setup.

When `USE_LLM_WRITER=true`, the orchestrator runs a shadow-only flow:

- build `EvidenceContract` objects from tool outputs
- ask `LLMEvidenceWriter` for candidate `headline`, `key_observations`, `limitations`, `table_caption`, and `confidence_note`
- validate the candidate with `WriterValidator`
- log `writer_called`, `writer_valid`, fallback reason, and violations

The candidate output is not written into `answer_contract`, does not replace `display_blocks`, and is not read by the frontend.

## WriterValidator Guardrails

`WriterValidator` rejects candidate wording that introduces unsupported facts or unsafe claims:

- numbers not present in canonical facts or evidence contracts
- months outside the canonical/evidence time scope
- entity names not present in canonical facts or evidence rows
- metric drift, such as an inventory question answered as revenue
- forecast claims for `forecast_unsupported`
- root-cause claims such as confirmed root cause or "原因就是"
- proxy or score metrics described as formal financial indicators
- dropped limitations
- internal tool names such as `get_entity_month_table` or `source_tool`

## Enablement Criteria

Formal writer enablement should wait until shadow regression has stable validation metrics, known false positives are understood, and the writer output can be compared against deterministic `display_blocks` without schema changes. The recommended GB10 demo setting remains:

```bash
USE_LLM_PLANNER=true
USE_LLM_WRITER=false
USE_LLM_REWRITER=false
```
