# Live LLM Smoke Report

- live_requested: True
- planner_only: True
- rewriter_only: False
- detected_llm_available: True
- llm_available: True
- model: gemma4:e4b
- timeout_seconds: 30
- warmup_success: True
- warmup_failure_reason: None
- planner_prompt_mode: slim
- compact_registry_tool_count: 5
- prompt_char_count: 794

## Safety Summary

- planner_success_rate: 100.00%
- planner_fallback_rate: 0.00%
- rewrite_success_rate: 0.00%
- rewrite_validation_failure_rate: 0.00%
- timeout_count: 0
- planner_timeout_count: 0
- rewriter_timeout_count: 0
- validation_failure_count: 0
- safety_violation_count: 0
- new_number_violation_count: 0
- forbidden_phrase_violation_count: 0
- limitation_violation_count: 0
- forecast_safety_pass: True
- root_cause_claim_blocked: 0

## Case Summary

- `???? MoM ?????`
  planner_attempted=True planner_success=True planner_failure_category=None planner_prompt_mode=slim prompt_char_count=794 planned_tool_count=1 planned_tools=['get_yoy_mom_breakdown(revenue)']
  rewrite_attempted=False rewrite_success=False rewrite_validation_passed=False rewriter_failure_category=None violations=[]

## Notes

- This smoke test checks live planner and rewriter behavior only.
- Timeout and transport failures are tracked separately from validator failures.
- Final product enablement still depends on separate rollout and validation decisions.
- The `/api/ask` response contract is unchanged by this smoke test.