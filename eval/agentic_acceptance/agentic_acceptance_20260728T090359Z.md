# Agentic Acceptance Report

- Run ID: `20260728T090359Z`
- API URL: `http://10.8.35.35:3000/api/ask`
- Total: 4 PASS: 4 PARTIAL: 0 FAIL: 0
- LLM plan direct-valid rate: 0.5
- Validated repair rate: 1.0
- Replan success rate: 0.0
- Capability gap correctness: 1.0
- Paraphrase stability: 0.0
- Latency average / p95: 24.114s / 24.192s

| Case | Verdict | Request | Elapsed | Planner | Source | Tools | Replan | Stop | Failure |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| E12 | PASS | `req-f1832767` | 24.192 | valid | llm_planner | get_entity_trend_comparison | 0 | completed |  |
| H21 | PASS | `req-f177c399` | 21.5 | called | rejected_llm_then_deterministic | get_entity_contribution_analysis | 0 | invalid_replan |  |
| B3-P2 | PASS | `req-a4c8e05f` | 23.436 | called | rejected_llm_then_deterministic | get_entity_period_pair_table, get_entity_performance_snapshot | 0 | completed |  |
| C5-P1 | PASS | `req-5ccff0f6` | 27.327 | valid | llm_planner | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |

## E12 PASS

- Request ID: `req-f1832767`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": true, "filter": false, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}]`
- Failure reason: none

## H21 PASS

- Request ID: `req-f177c399`
- Family: `capability_boundary` / Canonical: `contribution_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_contribution_analysis: ['period_a', 'period_b']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_contribution_analysis
- Evidence coverage: `{"requested_metrics": {"inventory_amount": false}, "requested_operations": {"counter_evidence": true}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## B3-P2 PASS

- Request ID: `req-a4c8e05f`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "cross_check": true, "rank": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}]`
- Failure reason: none

## C5-P1 PASS

- Request ID: `req-5ccff0f6`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none
