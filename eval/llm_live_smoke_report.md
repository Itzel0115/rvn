# Live LLM Smoke Report

- live_requested: True
- planner_only: False
- rewriter_only: False
- detected_llm_available: True
- llm_available: True
- model: gemma4:e4b
- timeout_seconds: 90
- warmup_success: True
- warmup_failure_reason: None
- planner_prompt_mode: slim
- compact_registry_tool_count: 5
- prompt_char_count: 794

## Safety Summary

- planner_success_rate: 25.00%
- planner_fallback_rate: 75.00%
- rewrite_success_rate: 0.00%
- rewrite_validation_failure_rate: 12.50%
- timeout_count: 1
- planner_timeout_count: 0
- rewriter_timeout_count: 1
- validation_failure_count: 7
- safety_violation_count: 1
- new_number_violation_count: 1
- forbidden_phrase_violation_count: 0
- limitation_violation_count: 0
- forecast_safety_pass: True
- root_cause_claim_blocked: 0

## Case Summary

- `請整理最新月份各新事業群的營收與庫存重點`
  planner_attempted=True planner_success=False planner_failure_category=planner_validation_failed planner_prompt_mode=slim prompt_char_count=794 planned_tool_count=0 planned_tools=[]
  rewrite_attempted=True rewrite_success=False rewrite_validation_passed=False rewriter_failure_category=invalid_json violations=['Failed to parse JSON from Ollama response.']
- `請分析哪個新事業群表現較佳`
  planner_attempted=True planner_success=False planner_failure_category=planner_validation_failed planner_prompt_mode=slim prompt_char_count=794 planned_tool_count=0 planned_tools=[]
  rewrite_attempted=True rewrite_success=False rewrite_validation_passed=False rewriter_failure_category=invalid_json violations=['Failed to parse JSON from Ollama response.']
- `最新月份營收最高的新事業群是誰？`
  planner_attempted=True planner_success=True planner_failure_category=None planner_prompt_mode=slim prompt_char_count=760 planned_tool_count=1 planned_tools=['get_entity_metric_ranking']
  rewrite_attempted=True rewrite_success=False rewrite_validation_passed=False rewriter_failure_category=llm_timeout violations=["HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=90)"]
- `最新月份庫存最高的新事業群是誰？`
  planner_attempted=True planner_success=False planner_failure_category=planner_validation_failed planner_prompt_mode=slim prompt_char_count=760 planned_tool_count=0 planned_tools=[]
  rewrite_attempted=True rewrite_success=False rewrite_validation_passed=False rewriter_failure_category=invalid_json violations=['Failed to parse JSON from Ollama response.']
- `比較最新月份各五大產品線營收與庫存`
  planner_attempted=True planner_success=False planner_failure_category=planner_validation_failed planner_prompt_mode=slim prompt_char_count=794 planned_tool_count=0 planned_tools=[]
  rewrite_attempted=True rewrite_success=False rewrite_validation_passed=False rewriter_failure_category=invalid_json violations=['Failed to parse JSON from Ollama response.']
- `哪個五大產品線營收最高？`
  planner_attempted=True planner_success=True planner_failure_category=None planner_prompt_mode=slim prompt_char_count=760 planned_tool_count=1 planned_tools=['get_entity_metric_ranking']
  rewrite_attempted=True rewrite_success=False rewrite_validation_passed=False rewriter_failure_category=invalid_json violations=['Failed to parse JSON from Ollama response.']
- `下個月營收會不會改善？`
  planner_attempted=True planner_success=False planner_failure_category=planner_validation_failed planner_prompt_mode=slim prompt_char_count=548 planned_tool_count=0 planned_tools=[]
  rewrite_attempted=True rewrite_success=False rewrite_validation_passed=False rewriter_failure_category=new_number_violation violations=["new_numbers=['1', '2']"]
- `為什麼某新事業群營收下降？`
  planner_attempted=True planner_success=False planner_failure_category=planner_validation_failed planner_prompt_mode=slim prompt_char_count=814 planned_tool_count=0 planned_tools=[]
  rewrite_attempted=True rewrite_success=False rewrite_validation_passed=False rewriter_failure_category=invalid_json violations=['Failed to parse JSON from Ollama response.']

## Notes

- This smoke test checks live planner and rewriter behavior only.
- Timeout and transport failures are tracked separately from validator failures.
- Final product enablement still depends on separate rollout and validation decisions.
- The `/api/ask` response contract is unchanged by this smoke test.