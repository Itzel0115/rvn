# Agentic Acceptance Report

- Run ID: `20260728T085325Z`
- API URL: `http://10.8.35.35:3000/api/ask`
- Total: 15 PASS: 11 PARTIAL: 4 FAIL: 0
- LLM plan direct-valid rate: 0.133
- Validated repair rate: 0.692
- Replan success rate: 0.0
- Capability gap correctness: 0.667
- Paraphrase stability: 0.4
- Latency average / p95: 28.524s / 35.572s

| Case | Verdict | Request | Elapsed | Planner | Source | Tools | Replan | Stop | Failure |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| A2 | PASS | `req-444b6cb5` | 26.859 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| B4 | PASS | `req-8f060dc4` | 32.89 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| C5 | PASS | `req-c58e7fc0` | 25.79 | valid | llm_planner | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed |  |
| D8 | PASS | `req-4d3a6e0c` | 32.009 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| E12 | PARTIAL | `req-bcf2a42c` | 34.412 | called | rejected_llm_then_deterministic | get_entity_time_series | 0 | invalid_replan | evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty= |
| G17 | PASS | `req-40d9fd7f` | 18.847 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| G18 | PASS | `req-bb567410` | 35.572 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_performance_snapshot, get_anomalies | 0 | invalid_replan |  |
| G19 | PASS | `req-c56008bd` | 31.814 | valid | llm_planner | get_entity_trend_comparison, get_revenue_inventory_relationship, get_anomalies | 0 | completed |  |
| H20 | PASS | `req-3a6ceab7` | 37.33 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| H21 | PARTIAL | `req-b54bde10` | 31.137 | called | rejected_llm_then_deterministic | get_entity_contribution_analysis | 0 | invalid_replan | manifest_operation:counter_evidence=['contribution_analysis'] |
| B3-P2 | PARTIAL | `req-1038e77f` | 27.617 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies | 0 | completed | manifest_metric:inventory_qty=['revenue_amount', 'inventory_amount']; manifest_operation:cross_check=['compare', 'rank'] |
| C5-P1 | PARTIAL | `req-2f303259` | 25.428 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed | top_n=None |
| D7-P2 | PASS | `req-eada3128` | 19.16 | called | rejected_llm_then_deterministic | get_entity_performance_snapshot, get_inventory_turnover_proxy, get_entity_cross_section_comparison, get_anomalies | 0 | completed |  |
| E12-P2 | PASS | `req-7ab3e69f` | 21.914 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed |  |
| G17-P2 | PASS | `req-baf3fe7d` | 27.083 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_performance_snapshot | 0 | invalid_replan |  |

## A2 PASS

- Request ID: `req-444b6cb5`
- Family: `continuous_conditions` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"sourc`
- Failure reason: none

## B4 PASS

- Request ID: `req-8f060dc4`
- Family: `topn_entity_continuity` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": false, "filter": true, "cross_check": false, "rank": true, "counter_evidence": true, "anomaly": true, "exclude": true, "limitations": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## C5 PASS

- Request ID: `req-c58e7fc0`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "3通路方案"]}]`
- Failure reason: none

## D8 PASS

- Request ID: `req-4d3a6e0c`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": false, "revenue_amount": false, "inventory_amount": false, "risk_score": false}, "requested_operations": {"filter": false, "rank": false, "proxy": false, "limitations": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## E12 PARTIAL

- Request ID: `req-bcf2a42c`
- Family: `dimension_drilldown` / Canonical: `entity_time_series`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:missing_required_metric:inventory_qty
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_time_series
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false, "inventory_qty": false, "inventory_amount": false}, "requested_operations": {"compare": true, "trend": true, "filter": false, "rank": true}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=

## G17 PASS

- Request ID: `req-40d9fd7f`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"sourc`
- Failure reason: none

## G18 PASS

- Request ID: `req-bb567410`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:missing_required_trend_metric:inventory_qty
- Replan: count=0 stop=invalid_replan
- Tools: get_revenue_inventory_relationship, get_entity_performance_snapshot, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true, "risk_score": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: none

## G19 PASS

- Request ID: `req-c56008bd`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_revenue_inventory_relationship, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true, "risk_score": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true, "relationship": false}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}]`
- Failure reason: none

## H20 PASS

- Request ID: `req-3a6ceab7`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": false, "inventory_amount": false}, "requested_operations": {"compare": false, "filter": false, "rank": false, "proxy": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## H21 PARTIAL

- Request ID: `req-b54bde10`
- Family: `capability_boundary` / Canonical: `contribution_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_contribution_analysis: ['period_a', 'period_b']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_contribution_analysis
- Evidence coverage: `{"requested_metrics": {"inventory_amount": false}, "requested_operations": {"contribution_analysis": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: manifest_operation:counter_evidence=['contribution_analysis']

## B3-P2 PARTIAL

- Request ID: `req-1038e77f`
- Family: `topn_entity_continuity` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true}, "requested_operations": {"compare": true, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}]`
- Failure reason: manifest_metric:inventory_qty=['revenue_amount', 'inventory_amount']; manifest_operation:cross_check=['compare', 'rank']

## C5-P1 PARTIAL

- Request ID: `req-2f303259`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"risk_score": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "cross_check": true, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: top_n=None

## D7-P2 PASS

- Request ID: `req-eada3128`
- Family: `proxy_boundary` / Canonical: `performance_assessment`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_performance_snapshot, get_inventory_turnover_proxy, get_entity_cross_section_comparison, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true, "health_score": false, "risk_score": true, "revenue_amount": true}, "requested_operations": {"exclude": true, "proxy": true, "limitations": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: none

## E12-P2 PASS

- Request ID: `req-7ab3e69f`
- Family: `dimension_drilldown` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"compare": true, "trend": true, "filter": false, "rank": true}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "product_line_5", "count": 7, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 3, "entities": ["Server", "百事益", "顯卡"]}]`
- Failure reason: none

## G17-P2 PASS

- Request ID: `req-baf3fe7d`
- Family: `semantic_generalization` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:missing_required_trend_metric:inventory_qty
- Replan: count=0 stop=invalid_replan
- Tools: get_revenue_inventory_relationship, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_amount": true, "revenue_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "relationship": false}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: none
