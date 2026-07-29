# Agentic Acceptance Report

- Run ID: `20260728T094747Z`
- API URL: `http://10.8.35.35:3000/api/ask`
- Total: 2 PASS: 0 PARTIAL: 2 FAIL: 0
- LLM plan direct-valid rate: 1.0
- Validated repair rate: 0.0
- Replan success rate: 0.0
- Capability gap correctness: 0.0
- Paraphrase stability: 1.0
- Latency average / p95: 18.573s / 16.664s

| Case | Verdict | Request | Elapsed | Planner | Source | Tools | Replan | Stop | Failure |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| D7 | PARTIAL | `req-a1df13b0` | 20.482 | valid | llm_planner | get_inventory_turnover_proxy | 0 | completed | evidence_dimension=business_group |
| D7-P1 | PARTIAL | `req-ba40ceda` | 16.664 | valid | llm_planner | get_inventory_turnover_proxy | 0 | completed | evidence_dimension=business_group |

## D7 PARTIAL

- Request ID: `req-a1df13b0`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 1}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: evidence_dimension=business_group

## D7-P1 PARTIAL

- Request ID: `req-ba40ceda`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 1}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: evidence_dimension=business_group
