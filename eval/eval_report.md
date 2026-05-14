# Eval Report

- router_cases: 15
- answer_cases: 15

## Router Metrics

- question_type_accuracy: 100.00%
- domain_accuracy: 73.33%
- tool_accuracy: 100.00%
- filter_extraction_accuracy: 100.00%
- task_family_accuracy: 86.67%
- answer_plan_score: 100.00%
- display_observation_count_score: 100.00%

## Answer Metrics

- answer_grounding_score: 98.33%
- must_include_score: 100.00%
- must_not_score: 100.00%
- evidence_tools_score: 100.00%
- limitation_score: 0.00%
- answer_filter_accuracy: 0.00%
- hallucination_rate: 0.00%
- unsupported_question_rejection_rate: 0.00%

## Display Quality Metrics

- display_blocks_presence_score: 100.00%
- headline_score: 100.00%
- observation_count_score: 100.00%
- no_background_leakage_score: 100.00%
- table_score: 100.00%
- limitation_preservation_score: 100.00%
- supported_task_family_count: 6
- supported_task_families: chart_request, cross_section_compare, latest_month_entity_summary, performance_assessment, period_pair_compare, ranking

## Failed Cases Summary

- none

## Notes

- Eval runs with a stubbed LLM so routing and answers are measured against deterministic fallback behavior.
- Non-unsupported answers must include both evidence and tools_used.
- Unsupported answers only pass when evidence and tools_used are both empty.
- Why/cause/forecast questions must surface limitation semantics in answer or limitations.
- If the question mentions a month or platform, data_scope.filters must match that scope.