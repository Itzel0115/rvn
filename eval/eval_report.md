# Eval Report

- router_cases: 60
- answer_cases: 60

## Router Metrics

- question_type_accuracy: 88.33%
- domain_accuracy: 100.00%
- tool_accuracy: 98.33%
- filter_extraction_accuracy: 100.00%
- task_family_accuracy: 100.00%
- answer_plan_score: 98.28%
- display_observation_count_score: 100.00%

## Answer Metrics

- answer_grounding_score: 93.83%
- must_include_score: 100.00%
- must_not_score: 100.00%
- evidence_tools_score: 100.00%
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
- supported_task_family_count: 18
- supported_task_families: chart_request, contribution_analysis, cross_section_compare, entity_month_table_lookup, entity_multi_month_table_lookup, entity_period_pair_metric_lookup, entity_period_pair_table_lookup, entity_ranking, entity_time_series, entity_trend_comparison, forecast_unsupported, latest_month_entity_summary, metric_lookup, metric_relationship_analysis, overall_trend_analysis, parent_child_drilldown, performance_assessment, period_pair_compare

## Failed Cases Summary

- none

## Notes

- Eval runs with a stubbed LLM so routing and answers are measured against deterministic fallback behavior.
- Non-unsupported answers must include both evidence and tools_used.
- Unsupported answers only pass when evidence and tools_used are both empty.
- Why/cause/forecast questions must surface limitation semantics in answer or limitations.
- If the question mentions a month or platform, data_scope.filters must match that scope.