# Agentic Acceptance Report

- Run ID: `20260728T093143Z`
- API URL: `http://10.8.35.35:3000/api/ask`
- Total: 32 PASS: 30 PARTIAL: 2 FAIL: 0
- LLM plan direct-valid rate: 0.281
- Validated repair rate: 1.0
- Replan success rate: 0.0
- Capability gap correctness: 1.0
- Paraphrase stability: 0.7
- Latency average / p95: 24.75s / 36.579s

| Case | Verdict | Request | Elapsed | Planner | Source | Tools | Replan | Stop | Failure |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| A1 | PASS | `req-b233b8c0` | 22.974 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| A2 | PASS | `req-3a0c94e8` | 22.195 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy | 0 | completed |  |
| B3 | PASS | `req-7da00b1a` | 36.579 | called | rejected_llm_then_deterministic | get_entity_period_pair_table, get_entity_performance_snapshot | 0 | completed |  |
| B4 | PASS | `req-499a949e` | 27.38 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C5 | PASS | `req-2985e5cb` | 29.003 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C6 | PASS | `req-588b532b` | 25.547 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| D7 | PARTIAL | `req-bbf0b792` | 20.675 | valid | llm_planner | get_inventory_turnover_proxy | 0 | completed | evidence_dimension=business_group |
| D8 | PASS | `req-5183a53b` | 41.834 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| D9 | PASS | `req-29700078` | 20.383 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| D10 | PASS | `req-ad51ea96` | 24.488 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| E11 | PASS | `req-fd38a1bf` | 16.842 | valid | llm_planner | get_entity_month_table | 0 | completed |  |
| E12 | PASS | `req-3eb26284` | 28.055 | valid | llm_planner | get_entity_trend_comparison | 0 | completed |  |
| E13 | PASS | `req-6bd33baf` | 51.536 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy | 0 | invalid_replan |  |
| E14 | PASS | `req-62bf0f27` | 19.283 | valid | llm_planner | get_entity_period_pair_value | 0 | completed |  |
| F15 | PASS | `req-d0a4e27c` | 21.83 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_anomalies, get_inventory_turnover_proxy, get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| F16 | PASS | `req-8fba60d9` | 19.161 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| G17 | PASS | `req-e8ac0d39` | 23.465 | valid | llm_planner | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| G18 | PASS | `req-f6bb0941` | 19.065 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| G19 | PASS | `req-c1e3766d` | 22.791 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| H20 | PASS | `req-a3a0b8d7` | 29.688 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| H21 | PASS | `req-27fcbd4a` | 21.452 | called | rejected_llm_then_deterministic | get_entity_contribution_analysis | 0 | invalid_replan |  |
| H22 | PASS | `req-2b4b8ad8` | 21.517 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| B3-P1 | PASS | `req-52de2e65` | 31.024 | called | rejected_llm_then_deterministic | get_entity_period_pair_table, get_entity_performance_snapshot | 0 | completed |  |
| B3-P2 | PASS | `req-0b90b470` | 26.815 | valid | llm_planner | get_entity_period_pair_table | 0 | completed |  |
| C5-P1 | PASS | `req-f81bf1d8` | 27.483 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C5-P2 | PASS | `req-b4048d52` | 23.723 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| D7-P1 | PARTIAL | `req-6467f0fb` | 16.768 | valid | llm_planner | get_inventory_turnover_proxy | 0 | completed | evidence_dimension=business_group |
| D7-P2 | PASS | `req-a4dbab1b` | 16.888 | valid | llm_planner | get_inventory_turnover_proxy, get_entity_performance_snapshot | 0 | completed |  |
| E12-P1 | PASS | `req-32039b93` | 22.195 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| E12-P2 | PASS | `req-49141bd2` | 24.093 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| G17-P1 | PASS | `req-aa05c934` | 16.389 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy | 0 | completed |  |
| G17-P2 | PASS | `req-1c8ed7b7` | 20.883 | valid | llm_planner | get_revenue_inventory_relationship, get_entity_trend_comparison | 0 | completed |  |

## A1 PASS

- Request ID: `req-b233b8c0`
- Family: `continuous_conditions` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "rank": true, "relationship": false}, "evidence_count": 8}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount`
- Failure reason: none

## A2 PASS

- Request ID: `req-3a0c94e8`
- Family: `continuous_conditions` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 7}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison",`
- Failure reason: none

## B3 PASS

- Request ID: `req-7da00b1a`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false, "filter": false, "cross_check": true, "rank": true, "relationship": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}]`
- Failure reason: none

## B4 PASS

- Request ID: `req-499a949e`
- Family: `topn_entity_continuity` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": false, "filter": true, "cross_check": false, "rank": true, "counter_evidence": true, "anomaly": true, "exclude": true, "limitations": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## C5 PASS

- Request ID: `req-2985e5cb`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none

## C6 PASS

- Request ID: `req-588b532b`
- Family: `management_judgement` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 8}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "`
- Failure reason: none

## D7 PARTIAL

- Request ID: `req-bbf0b792`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 1}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: evidence_dimension=business_group

## D8 PASS

- Request ID: `req-5183a53b`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": false, "revenue_amount": false, "inventory_amount": false, "risk_score": false}, "requested_operations": {"filter": false, "rank": false, "proxy": false, "limitations": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## D9 PASS

- Request ID: `req-29700078`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": false, "filter": false, "cross_check": true, "rank": true, "proxy": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 3, "entities": ["2技宸", "3通路方案", "4筆電+盈嘉"]}]`
- Failure reason: none

## D10 PASS

- Request ID: `req-ad51ea96`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "revenue_amount": true, "inventory_amount": true}, "requested_operations": {"compare": false, "cross_check": false, "rank": false, "exclude": true, "proxy": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## E11 PASS

- Request ID: `req-fd38a1bf`
- Family: `field_mapping` / Canonical: `entity_month_table_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_month_table
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"filter": true, "cross_check": false}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_month_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## E12 PASS

- Request ID: `req-3eb26284`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": true, "filter": false, "cross_check": false, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}]`
- Failure reason: none

## E13 PASS

- Request ID: `req-6bd33baf`
- Family: `dimension_drilldown` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:entity_value_missing
- Replan: count=0 stop=invalid_replan
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": false, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}]`
- Failure reason: none

## E14 PASS

- Request ID: `req-62bf0f27`
- Family: `field_mapping` / Canonical: `entity_period_pair_metric_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_value
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false, "cross_check": false}, "evidence_count": 3}`
- Entity sets: `[]`
- Failure reason: none

## F15 PASS

- Request ID: `req-d0a4e27c`
- Family: `replan_conflict` / Canonical: `risk_scan`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_anomalies, get_inventory_turnover_proxy, get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"filter": false, "rank": true, "anomaly": true, "limitations": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}]`
- Failure reason: none

## F16 PASS

- Request ID: `req-8fba60d9`
- Family: `replan_conflict` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"filter": true, "cross_check": true, "limitations": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: none

## G17 PASS

- Request ID: `req-e8ac0d39`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## G18 PASS

- Request ID: `req-f6bb0941`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true, "risk_score": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 8}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "`
- Failure reason: none

## G19 PASS

- Request ID: `req-c1e3766d`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "risk_score": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true, "relationship": false}, "evidence_count": 8}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 3, "entities": ["2技宸", "3通路方案", "4筆電+盈嘉"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_enti`
- Failure reason: none

## H20 PASS

- Request ID: `req-a3a0b8d7`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": false, "inventory_amount": false}, "requested_operations": {"compare": false, "filter": false, "rank": false, "proxy": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## H21 PASS

- Request ID: `req-27fcbd4a`
- Family: `capability_boundary` / Canonical: `contribution_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_contribution_analysis: ['period_a', 'period_b']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_contribution_analysis
- Evidence coverage: `{"requested_metrics": {"inventory_amount": false}, "requested_operations": {"counter_evidence": true}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## H22 PASS

- Request ID: `req-2b4b8ad8`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false}, "requested_operations": {"forecast_unsupported": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## B3-P1 PASS

- Request ID: `req-52de2e65`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false, "filter": false, "cross_check": true, "rank": true, "relationship": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}]`
- Failure reason: none

## B3-P2 PASS

- Request ID: `req-0b90b470`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "cross_check": true, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## C5-P1 PASS

- Request ID: `req-f81bf1d8`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none

## C5-P2 PASS

- Request ID: `req-b4048d52`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "risk_score": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none

## D7-P1 PARTIAL

- Request ID: `req-6467f0fb`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 1}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: evidence_dimension=business_group

## D7-P2 PASS

- Request ID: `req-a4dbab1b`
- Family: `proxy_boundary` / Canonical: `performance_assessment`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true, "health_score": false, "risk_score": true, "revenue_amount": true}, "requested_operations": {"cross_check": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## E12-P1 PASS

- Request ID: `req-32039b93`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": true, "cross_check": false, "rank": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 3, "entities": ["Server", "百事益", "顯卡"]}]`
- Failure reason: none

## E12-P2 PASS

- Request ID: `req-49141bd2`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"compare": true, "trend": true, "filter": false, "rank": true}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 3, "entities": ["Server", "百事益", "顯卡"]}]`
- Failure reason: none

## G17-P1 PASS

- Request ID: `req-aa05c934`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 7}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "`
- Failure reason: none

## G17-P2 PASS

- Request ID: `req-1c8ed7b7`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}]`
- Failure reason: none
