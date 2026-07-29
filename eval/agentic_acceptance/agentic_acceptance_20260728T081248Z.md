# Agentic Acceptance Report

- Run ID: `20260728T081248Z`
- API URL: `http://10.8.35.35:3000/api/ask`
- Total: 1 PASS: 1 PARTIAL: 0 FAIL: 0
- LLM plan direct-valid rate: 1.0
- Validated repair rate: 0.0
- Replan success rate: 0.0
- Capability gap correctness: 0.0
- Paraphrase stability: 0.0
- Latency average / p95: 18.22s / 18.22s

| Case | Verdict | Request | Elapsed | Planner | Source | Tools | Replan | Stop | Failure |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| E11 | PASS | `req-ce0b6b67` | 18.22 | valid | llm_planner | get_entity_month_table | 0 | completed |  |

## E11 PASS

- Request ID: `req-ce0b6b67`
- Family: `field_mapping` / Canonical: `entity_month_table_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_month_table
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"filter": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_month_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none
