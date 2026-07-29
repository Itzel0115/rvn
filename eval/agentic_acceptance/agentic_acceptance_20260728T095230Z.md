# Agentic Acceptance Report

- Run ID: `20260728T095230Z`
- API URL: `http://10.8.35.35:3000/api/ask`
- Total: 32 PASS: 32 PARTIAL: 0 FAIL: 0
- LLM plan direct-valid rate: 0.281
- Validated repair rate: 1.0
- Replan success rate: 0.0
- Capability gap correctness: 1.0
- Paraphrase stability: 0.7
- Latency average / p95: 24.451s / 31.215s

| Case | Verdict | Request | Elapsed | Planner | Source | Tools | Replan | Stop | Failure |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| A1 | PASS | `req-4c16aee0` | 21.839 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| A2 | PASS | `req-7d8fb131` | 19.899 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy | 0 | completed |  |
| B3 | PASS | `req-7d2ae205` | 25.394 | called | rejected_llm_then_deterministic | get_entity_period_pair_table, get_entity_performance_snapshot | 0 | completed |  |
| B4 | PASS | `req-ecba0b32` | 27.453 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C5 | PASS | `req-f7a03da3` | 29.085 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C6 | PASS | `req-b6b16e5e` | 25.529 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| D7 | PASS | `req-83e6872c` | 20.605 | valid | llm_planner | get_inventory_turnover_proxy | 0 | completed |  |
| D8 | PASS | `req-84d48ffb` | 41.868 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| D9 | PASS | `req-a5e9cbe3` | 20.373 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| D10 | PASS | `req-931ffe3d` | 24.484 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| E11 | PASS | `req-0c658f67` | 19.373 | valid | llm_planner | get_entity_month_table | 0 | completed |  |
| E12 | PASS | `req-11ee58ff` | 22.203 | valid | llm_planner | get_entity_trend_comparison | 0 | completed |  |
| E13 | PASS | `req-2d6fe87a` | 48.522 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy | 0 | invalid_replan |  |
| E14 | PASS | `req-d953ba5c` | 19.628 | valid | llm_planner | get_entity_period_pair_value | 0 | completed |  |
| F15 | PASS | `req-f4765991` | 21.889 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_anomalies, get_inventory_turnover_proxy, get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| F16 | PASS | `req-ed4cb878` | 19.266 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| G17 | PASS | `req-279ddc83` | 19.534 | valid | llm_planner | get_revenue_inventory_relationship, get_entity_trend_comparison | 0 | completed |  |
| G18 | PASS | `req-20a92568` | 19.93 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| G19 | PASS | `req-cebc6066` | 31.215 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| H20 | PASS | `req-5d59994e` | 29.73 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| H21 | PASS | `req-a73a32c4` | 21.455 | called | rejected_llm_then_deterministic | get_entity_contribution_analysis | 0 | invalid_replan |  |
| H22 | PASS | `req-efce45eb` | 21.633 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| B3-P1 | PASS | `req-ac36a182` | 31.047 | called | rejected_llm_then_deterministic | get_entity_period_pair_table, get_entity_performance_snapshot | 0 | completed |  |
| B3-P2 | PASS | `req-bc09f22b` | 26.816 | valid | llm_planner | get_entity_period_pair_table | 0 | completed |  |
| C5-P1 | PASS | `req-3d0eebf6` | 27.418 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C5-P2 | PASS | `req-a76f290a` | 23.815 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| D7-P1 | PASS | `req-097dcd6e` | 16.846 | valid | llm_planner | get_inventory_turnover_proxy | 0 | completed |  |
| D7-P2 | PASS | `req-f8ba6bab` | 16.965 | valid | llm_planner | get_inventory_turnover_proxy, get_entity_performance_snapshot | 0 | completed |  |
| E12-P1 | PASS | `req-424b00d2` | 26.437 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| E12-P2 | PASS | `req-bb341924` | 24.242 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| G17-P1 | PASS | `req-ef45530e` | 16.368 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy | 0 | completed |  |
| G17-P2 | PASS | `req-bab7411f` | 21.563 | valid | llm_planner | get_revenue_inventory_relationship, get_entity_trend_comparison | 0 | completed |  |

## A1 PASS

- Request ID: `req-4c16aee0`
- Family: `continuous_conditions` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "rank": true, "relationship": false}, "evidence_count": 8}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inve`
- Failure reason: none

## A2 PASS

- Request ID: `req-7d8fb131`
- Family: `continuous_conditions` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 7}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_`
- Failure reason: none

## B3 PASS

- Request ID: `req-7d2ae205`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false, "filter": false, "cross_check": true, "rank": true, "relationship": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}]`
- Failure reason: none

## B4 PASS

- Request ID: `req-ecba0b32`
- Family: `topn_entity_continuity` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": false, "filter": true, "cross_check": false, "rank": true, "counter_evidence": true, "anomaly": true, "exclude": true, "limitations": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## C5 PASS

- Request ID: `req-f7a03da3`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none

## C6 PASS

- Request ID: `req-b6b16e5e`
- Family: `management_judgement` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 8}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "`
- Failure reason: none

## D7 PASS

- Request ID: `req-83e6872c`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 1}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## D8 PASS

- Request ID: `req-84d48ffb`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": false, "revenue_amount": false, "inventory_amount": false, "risk_score": false}, "requested_operations": {"filter": false, "rank": false, "proxy": false, "limitations": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## D9 PASS

- Request ID: `req-a5e9cbe3`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": false, "filter": false, "cross_check": true, "rank": true, "proxy": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["2技宸", "3通路方案", "4筆電+盈嘉"]}]`
- Failure reason: none

## D10 PASS

- Request ID: `req-931ffe3d`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "revenue_amount": true, "inventory_amount": true}, "requested_operations": {"compare": false, "cross_check": false, "rank": false, "exclude": true, "proxy": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## E11 PASS

- Request ID: `req-0c658f67`
- Family: `field_mapping` / Canonical: `entity_month_table_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_month_table
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"filter": true, "cross_check": false}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_month_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## E12 PASS

- Request ID: `req-11ee58ff`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": true, "filter": false, "cross_check": false, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}]`
- Failure reason: none

## E13 PASS

- Request ID: `req-2d6fe87a`
- Family: `dimension_drilldown` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:entity_value_missing
- Replan: count=0 stop=invalid_replan
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": false, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}]`
- Failure reason: none

## E14 PASS

- Request ID: `req-d953ba5c`
- Family: `field_mapping` / Canonical: `entity_period_pair_metric_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_value
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false, "cross_check": false}, "evidence_count": 3}`
- Entity sets: `[]`
- Failure reason: none

## F15 PASS

- Request ID: `req-f4765991`
- Family: `replan_conflict` / Canonical: `risk_scan`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_anomalies, get_inventory_turnover_proxy, get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"filter": false, "rank": true, "anomaly": true, "limitations": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}]`
- Failure reason: none

## F16 PASS

- Request ID: `req-ed4cb878`
- Family: `replan_conflict` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"filter": true, "cross_check": true, "limitations": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: none

## G17 PASS

- Request ID: `req-279ddc83`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## G18 PASS

- Request ID: `req-20a92568`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true, "risk_score": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 8}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "`
- Failure reason: none

## G19 PASS

- Request ID: `req-cebc6066`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "risk_score": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true, "relationship": false}, "evidence_count": 8}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["2技宸", "3通路方案", "4筆電+盈嘉"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool`
- Failure reason: none

## H20 PASS

- Request ID: `req-5d59994e`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": false, "inventory_amount": false}, "requested_operations": {"compare": false, "filter": false, "rank": false, "proxy": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## H21 PASS

- Request ID: `req-a73a32c4`
- Family: `capability_boundary` / Canonical: `contribution_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_contribution_analysis: ['period_a', 'period_b']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_contribution_analysis
- Evidence coverage: `{"requested_metrics": {"inventory_amount": false}, "requested_operations": {"counter_evidence": true}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## H22 PASS

- Request ID: `req-efce45eb`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false}, "requested_operations": {"forecast_unsupported": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## B3-P1 PASS

- Request ID: `req-ac36a182`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false, "filter": false, "cross_check": true, "rank": true, "relationship": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}]`
- Failure reason: none

## B3-P2 PASS

- Request ID: `req-bc09f22b`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "cross_check": true, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## C5-P1 PASS

- Request ID: `req-3d0eebf6`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none

## C5-P2 PASS

- Request ID: `req-a76f290a`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "risk_score": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none

## D7-P1 PASS

- Request ID: `req-097dcd6e`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 1}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## D7-P2 PASS

- Request ID: `req-f8ba6bab`
- Family: `proxy_boundary` / Canonical: `performance_assessment`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true, "health_score": false, "risk_score": true, "revenue_amount": true}, "requested_operations": {"cross_check": false, "exclude": true, "proxy": true, "limitations": true}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## E12-P1 PASS

- Request ID: `req-424b00d2`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": true, "cross_check": false, "rank": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 3, "entities": ["Server", "百事益", "顯卡"]}]`
- Failure reason: none

## E12-P2 PASS

- Request ID: `req-bb341924`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"compare": true, "trend": true, "filter": false, "rank": true}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 3, "entities": ["Server", "百事益", "顯卡"]}]`
- Failure reason: none

## G17-P1 PASS

- Request ID: `req-ef45530e`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 7}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "`
- Failure reason: none

## G17-P2 PASS

- Request ID: `req-bab7411f`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}]`
- Failure reason: none
