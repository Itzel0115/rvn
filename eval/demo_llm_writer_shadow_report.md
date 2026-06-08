# LLM Writer Shadow Regression

This report exercises LLMEvidenceWriter in shadow mode only. Official display_blocks are not replaced.

## Metrics

- writer_called_count: 60
- writer_valid_count: 57
- writer_invalid_count: 3
- writer_valid_rate: 95.0%
- violation_counts: {'hallucinated_number': 3}
- fallback_reason_counts: {"number_not_in_evidence:['999,999,999']": 3}
- true_positive_reject_count: 3
- likely_false_positive_count: 0
- prompt_gap_count: 0
- evidence_contract_gap_count: 0
- metric_false_positive_count: 0
- recommendation_counts: {'keep rejected': 3}
- hallucinated_number_count: 3
- month_violation_count: 0
- entity_violation_count: 0
- metric_violation_count: 0
- forecast_violation_count: 0
- root_cause_violation_count: 0
- limitation_violation_count: 0
- internal_tool_name_violation_count: 0

## Rejections

- 19: 畫總體營收趨勢 -> number_not_in_evidence:['999,999,999'] (true_positive_reject; keep rejected)
- 38: 比較2025年3月各事業群營收資料 -> number_not_in_evidence:['999,999,999'] (true_positive_reject; keep rejected)
- 57: 列出 2025年3月各產品線資料 -> number_not_in_evidence:['999,999,999'] (true_positive_reject; keep rejected)
