# Agentic Acceptance Report

- Run ID: `20260728T090548Z`
- API URL: `http://10.8.35.35:3000/api/ask`
- Total: 32 PASS: 24 PARTIAL: 8 FAIL: 0
- LLM plan direct-valid rate: 0.29
- Validated repair rate: 0.773
- Replan success rate: 0.0
- Capability gap correctness: 1.0
- Paraphrase stability: 0.7
- Latency average / p95: 27.974s / 45.92s

| Case | Verdict | Request | Elapsed | Planner | Source | Tools | Replan | Stop | Failure |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| A1 | PASS | `req-6c248a11` | 27.907 | valid | llm_planner | get_entity_trend_comparison, get_revenue_inventory_relationship, get_entity_performance_snapshot | 0 | completed |  |
| A2 | PASS | `req-3f690cb3` | 24.3 | valid | llm_planner | get_revenue_inventory_relationship, get_entity_trend_comparison | 0 | completed |  |
| B3 | PASS | `req-b5011a58` | 38.282 | called | rejected_llm_then_deterministic | get_entity_period_pair_table, get_entity_performance_snapshot | 0 | completed |  |
| B4 | PASS | `req-13a6e311` | 27.305 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C5 | PASS | `req-e6c8221f` | 29.028 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C6 | PARTIAL | `req-943cec50` | 39.84 | called | rejected_llm_then_deterministic | get_entity_time_series | 0 | invalid_replan | evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:trend=['filter', 'cross_check']; evidence_dimension=business_group |
| D7 | PASS | `req-3681775d` | 20.983 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| D8 | PASS | `req-2c47ec5b` | 41.668 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| D9 | PASS | `req-262fcbfd` | 22.115 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| D10 | PARTIAL | `req-ff84e47c` | 21.641 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed | manifest_operation:exclude=['compare', 'cross_check', 'rank', 'proxy'] |
| E11 | PASS | `req-b918a845` | 18.737 | valid | llm_planner | get_entity_month_table | 0 | completed |  |
| E12 | PASS | `req-9a1027e5` | 29.595 | valid | llm_planner | get_entity_trend_comparison | 0 | completed |  |
| E13 | PASS | `req-238ffdf8` | 46.106 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_performance_snapshot | 0 | invalid_replan |  |
| E14 | PASS | `req-9a448cc8` | 20.42 | valid | llm_planner | get_entity_period_pair_value | 0 | completed |  |
| F15 | PARTIAL | `req-a64cb20b` | 20.653 | valid | llm_planner | get_entity_performance_snapshot, get_anomalies | 0 | completed | manifest_operation:rank=['filter', 'anomaly', 'limitations'] |
| F16 | PARTIAL | `req-65cefa19` | 17.745 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed | manifest_operation:limitations=['filter', 'cross_check'] |
| G17 | PASS | `req-8e9537b6` | 21.237 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| G18 | PASS | `req-795a0c97` | 30.683 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_performance_snapshot, get_anomalies | 0 | invalid_replan |  |
| G19 | PASS | `req-c8e78c38` | 22.615 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies | 0 | completed |  |
| H20 | PASS | `req-551b1b07` | 29.689 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| H21 | PASS | `req-64837a6b` | 21.402 | called | rejected_llm_then_deterministic | get_entity_contribution_analysis | 0 | invalid_replan |  |
| H22 | PASS | `req-ad0aba94` | 23.859 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| B3-P1 | PARTIAL | `req-a04a9f25` | 51.256 | not-called | None |  | 0 | None | evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:cross_check=['compare', 'trend', 'filter', 'rank']; top_n=None; complex_has_planning_or_repair=None |
| B3-P2 | PASS | `req-92f22040` | 26.838 | valid | llm_planner | get_entity_period_pair_table | 0 | completed |  |
| C5-P1 | PASS | `req-016d526b` | 27.4 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C5-P2 | PARTIAL | `req-d0038f28` | 24.118 | valid | llm_planner | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed | manifest_operation:cross_check=['trend', 'filter', 'rank', 'counter_evidence', 'anomaly'] |
| D7-P1 | PASS | `req-3c2b4ded` | 20.527 | valid | llm_planner | get_inventory_turnover_proxy, get_entity_cross_section_comparison | 0 | completed |  |
| D7-P2 | PASS | `req-4a91daf9` | 11.572 | called | rejected_llm_then_deterministic | get_entity_performance_snapshot, get_inventory_turnover_proxy, get_entity_cross_section_comparison, get_anomalies | 0 | completed |  |
| E12-P1 | PARTIAL | `req-e7b9c845` | 45.92 | called | rejected_llm_then_deterministic | get_entity_time_series | 0 | invalid_replan | evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:compare=['trend', 'rank'] |
| E12-P2 | PASS | `req-710f41be` | 21.093 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| G17-P1 | PARTIAL | `req-5217acab` | 36.465 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_performance_snapshot | 0 | invalid_replan | manifest_operation:filter=['trend', 'cross_check', 'relationship'] |
| G17-P2 | PASS | `req-3d3554c9` | 34.176 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_performance_snapshot | 0 | invalid_replan |  |

## A1 PASS

- Request ID: `req-6c248a11`
- Family: `continuous_conditions` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_revenue_inventory_relationship, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "rank": true, "relationship": false}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## A2 PASS

- Request ID: `req-3f690cb3`
- Family: `continuous_conditions` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## B3 PASS

- Request ID: `req-b5011a58`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false, "filter": false, "cross_check": true, "rank": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}]`
- Failure reason: none

## B4 PASS

- Request ID: `req-13a6e311`
- Family: `topn_entity_continuity` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": false, "filter": true, "cross_check": false, "rank": true, "counter_evidence": true, "anomaly": true, "exclude": true, "limitations": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## C5 PASS

- Request ID: `req-e6c8221f`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none

## C6 PARTIAL

- Request ID: `req-943cec50`
- Family: `management_judgement` / Canonical: `entity_time_series`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_time_series: ['entity_value']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_time_series
- Evidence coverage: `{"requested_metrics": {"risk_score": false, "revenue_amount": false, "inventory_qty": false, "inventory_amount": false, "revenue_inventory_amount_ratio": false}, "requested_operations": {"filter": true, "cross_check": true}, "evidence_count": 3}`
- Entity sets: `[]`
- Failure reason: evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:trend=['filter', 'cross_check']; evidence_dimension=business_group

## D7 PASS

- Request ID: `req-3681775d`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## D8 PASS

- Request ID: `req-2c47ec5b`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": false, "revenue_amount": false, "inventory_amount": false, "risk_score": false}, "requested_operations": {"filter": false, "rank": false, "proxy": false, "limitations": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## D9 PASS

- Request ID: `req-262fcbfd`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": false, "filter": false, "cross_check": true, "rank": true, "proxy": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 3, "entities": ["2技宸", "3通路方案", "4筆電+盈嘉"]}]`
- Failure reason: none

## D10 PARTIAL

- Request ID: `req-ff84e47c`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "revenue_amount": true, "inventory_amount": true}, "requested_operations": {"compare": false, "cross_check": false, "rank": false, "proxy": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: manifest_operation:exclude=['compare', 'cross_check', 'rank', 'proxy']

## E11 PASS

- Request ID: `req-b918a845`
- Family: `field_mapping` / Canonical: `entity_month_table_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_month_table
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"filter": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_month_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## E12 PASS

- Request ID: `req-9a1027e5`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": true, "filter": false, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}]`
- Failure reason: none

## E13 PASS

- Request ID: `req-238ffdf8`
- Family: `dimension_drilldown` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:entity_value_missing
- Replan: count=0 stop=invalid_replan
- Tools: get_revenue_inventory_relationship, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"filter": true, "cross_check": true, "relationship": false}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}]`
- Failure reason: none

## E14 PASS

- Request ID: `req-9a448cc8`
- Family: `field_mapping` / Canonical: `entity_period_pair_metric_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_value
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false}, "evidence_count": 3}`
- Entity sets: `[]`
- Failure reason: none

## F15 PARTIAL

- Request ID: `req-a64cb20b`
- Family: `replan_conflict` / Canonical: `risk_scan`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_performance_snapshot, get_anomalies
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"filter": false, "anomaly": true, "limitations": false}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: manifest_operation:rank=['filter', 'anomaly', 'limitations']

## F16 PARTIAL

- Request ID: `req-65cefa19`
- Family: `replan_conflict` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"filter": true, "cross_check": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: manifest_operation:limitations=['filter', 'cross_check']

## G17 PASS

- Request ID: `req-8e9537b6`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"sourc`
- Failure reason: none

## G18 PASS

- Request ID: `req-795a0c97`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:missing_required_trend_metric:inventory_qty
- Replan: count=0 stop=invalid_replan
- Tools: get_revenue_inventory_relationship, get_entity_performance_snapshot, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true, "risk_score": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: none

## G19 PASS

- Request ID: `req-c8e78c38`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "risk_score": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true, "relationship": false}, "evidence_count": 7}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸`
- Failure reason: none

## H20 PASS

- Request ID: `req-551b1b07`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": false, "inventory_amount": false}, "requested_operations": {"compare": false, "filter": false, "rank": false, "proxy": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## H21 PASS

- Request ID: `req-64837a6b`
- Family: `capability_boundary` / Canonical: `contribution_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_contribution_analysis: ['period_a', 'period_b']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_contribution_analysis
- Evidence coverage: `{"requested_metrics": {"inventory_amount": false}, "requested_operations": {"counter_evidence": true}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## H22 PASS

- Request ID: `req-ad0aba94`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false}, "requested_operations": {"forecast_unsupported": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## B3-P1 PARTIAL

- Request ID: `req-a04a9f25`
- Family: `topn_entity_continuity` / Canonical: `period_pair_compare`
- Planner: called=False valid=False source=None fallback=None
- Replan: count=0 stop=None
- Tools: 
- Evidence coverage: `{"requested_metrics": {"risk_score": false, "revenue_amount": true, "inventory_qty": false, "inventory_amount": false}, "requested_operations": {"compare": true, "trend": false, "filter": false, "rank": true}, "evidence_count": 1}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:cross_check=['compare', 'trend', 'filter', 'rank']; top_n=None; complex_has_planning_or_repair=None

## B3-P2 PASS

- Request ID: `req-92f22040`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "cross_check": true, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## C5-P1 PASS

- Request ID: `req-016d526b`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none

## C5-P2 PARTIAL

- Request ID: `req-d0038f28`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "risk_score": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: manifest_operation:cross_check=['trend', 'filter', 'rank', 'counter_evidence', 'anomaly']

## D7-P1 PASS

- Request ID: `req-3c2b4ded`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy, get_entity_cross_section_comparison
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## D7-P2 PASS

- Request ID: `req-4a91daf9`
- Family: `proxy_boundary` / Canonical: `performance_assessment`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_performance_snapshot, get_inventory_turnover_proxy, get_entity_cross_section_comparison, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true, "health_score": false, "risk_score": true, "revenue_amount": true}, "requested_operations": {"cross_check": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: none

## E12-P1 PARTIAL

- Request ID: `req-e7b9c845`
- Family: `dimension_drilldown` / Canonical: `entity_time_series`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:missing_required_metric:inventory_qty
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_time_series
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false, "inventory_qty": false, "inventory_amount": false}, "requested_operations": {"trend": true, "rank": true}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:compare=['trend', 'rank']

## E12-P2 PASS

- Request ID: `req-710f41be`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"compare": true, "trend": true, "filter": false, "rank": true}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 3, "entities": ["Server", "百事益", "顯卡"]}]`
- Failure reason: none

## G17-P1 PARTIAL

- Request ID: `req-5217acab`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:missing_required_trend_metric:inventory_qty
- Replan: count=0 stop=invalid_replan
- Tools: get_revenue_inventory_relationship, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "cross_check": true, "relationship": false}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: manifest_operation:filter=['trend', 'cross_check', 'relationship']

## G17-P2 PASS

- Request ID: `req-3d3554c9`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:missing_required_trend_metric:inventory_qty
- Replan: count=0 stop=invalid_replan
- Tools: get_revenue_inventory_relationship, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: none
