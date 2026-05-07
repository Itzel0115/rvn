# Eval Report

- router_cases: 66
- answer_cases: 66

## Router Metrics

- question_type_accuracy: 98.48%
- domain_accuracy: 100.00%
- tool_accuracy: 96.97%
- filter_extraction_accuracy: 100.00%
- task_family_accuracy: 100.00%
- answer_plan_score: 100.00%
- display_observation_count_score: 100.00%

## Answer Metrics

- answer_grounding_score: 98.26%
- must_include_score: 95.45%
- must_not_score: 100.00%
- evidence_tools_score: 98.48%
- limitation_score: 100.00%
- answer_filter_accuracy: 100.00%
- hallucination_rate: 0.00%
- unsupported_question_rejection_rate: 100.00%

## Display Quality Metrics

- display_blocks_presence_score: 100.00%
- headline_score: 100.00%
- observation_count_score: 100.00%
- no_background_leakage_score: 100.00%
- table_score: 100.00%
- limitation_preservation_score: 100.00%
- supported_task_family_count: 13
- supported_task_families: chart_request, cross_domain, cross_section_compare, data_quality, decision, diagnosis, executive_summary, metric_lookup, performance_assessment, ranking, risk_scan, time_compare, trend_analysis

## Failed Cases Summary

- answer_046: 比較 8 月各平台營收與庫存 (must_include_score)
- answer_047: 請分析哪個平台表現較佳 (must_include_score)
- answer_048: 請分析哪個平台表現較差 (must_include_score)

## Notes

- Eval runs with a stubbed LLM so routing and answers are measured against deterministic fallback behavior.
- Non-unsupported answers must include both evidence and tools_used.
- Unsupported answers only pass when evidence and tools_used are both empty.
- Why/cause/forecast questions must surface limitation semantics in answer or limitations.
- If the question mentions a month or platform, data_scope.filters must match that scope.