# Eval Report

- router_cases: 71
- answer_cases: 71

## Router Metrics

- question_type_accuracy: 97.18%
- domain_accuracy: 98.59%
- tool_accuracy: 97.18%
- filter_extraction_accuracy: 100.00%
- task_family_accuracy: 100.00%
- answer_plan_score: 100.00%
- display_observation_count_score: 100.00%

## Answer Metrics

- answer_grounding_score: 99.37%
- must_include_score: 100.00%
- must_not_score: 100.00%
- evidence_tools_score: 98.59%
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
- supported_task_family_count: 15
- supported_task_families: chart_request, cross_section_compare, data_quality, decision, diagnosis, executive_summary, forecast_unsupported, latest_month_platform_summary, metric_lookup, performance_assessment, period_pair_compare, ranking, risk_scan, time_compare, trend_analysis

## Failed Cases Summary

- none

## Notes

- Eval runs with a stubbed LLM so routing and answers are measured against deterministic fallback behavior.
- Non-unsupported answers must include both evidence and tools_used.
- Unsupported answers only pass when evidence and tools_used are both empty.
- Why/cause/forecast questions must surface limitation semantics in answer or limitations.
- If the question mentions a month or platform, data_scope.filters must match that scope.