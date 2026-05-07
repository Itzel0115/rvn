# LLM Planner Eval Report

- mode: mock
- cases: 82

## Metrics

- planner_success_rate: 100.00%
- planner_fallback_rate: 0.00%
- invalid_plan_rate: 0.00%
- avg_tool_count: 2.30
- tool_overlap_rate: 89.86%
- unknown_tool_rejection_count: 0
- invalid_args_rejection_count: 0
- why_requires_limitation_pass_rate: 100.00%
- forecast_safety_pass_rate: 100.00%

## Fallback Summary

- No planner fallbacks were recorded.

## Sample Cases

- All planner cases succeeded in this run.

## Notes

- Phase 7A.5 evaluates planner quality only; final answers still come from deterministic answer_contract assembly.
- Tool overlap compares planner output against deterministic expected tools filtered to the planner allowlist.
- Why and forecast metrics count both compliant plans and safely rejected invalid plans as rule enforcement passes.