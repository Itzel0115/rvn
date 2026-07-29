# Agentic Acceptance Report

- Run ID: `20260728T082925Z`
- API URL: `http://10.8.35.35:3000/api/ask`
- Total: 32 PASS: 8 PARTIAL: 23 FAIL: 1
- LLM plan direct-valid rate: 0.29
- Validated repair rate: 0.182
- Replan success rate: 0.0
- Capability gap correctness: 0.25
- Paraphrase stability: 0.4
- Latency average / p95: 27.845s / 43.198s

| Case | Verdict | Request | Elapsed | Planner | Source | Tools | Replan | Stop | Failure |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| A1 | PASS | `req-53955a74` | 23.055 | valid | llm_planner | get_entity_trend_comparison, get_revenue_inventory_relationship | 0 | completed |  |
| A2 | PARTIAL | `req-98afef8d` | 16.375 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed | manifest_operation:cross_check=['trend', 'filter', 'relationship'] |
| B3 | PASS | `req-a8d87293` | 24.88 | called | rejected_llm_then_deterministic | get_entity_period_pair_table, get_entity_performance_snapshot | 0 | completed |  |
| B4 | PARTIAL | `req-0bd23984` | 19.655 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed | manifest_metric:risk_score=['revenue_amount', 'inventory_qty', 'inventory_amount', 'revenue_inventory_amount_ratio'] |
| C5 | PARTIAL | `req-6e8fcebf` | 21.964 | valid | llm_planner | get_entity_trend_comparison, get_anomalies | 0 | completed | manifest_metric:risk_score=['revenue_amount', 'inventory_qty', 'inventory_amount', 'revenue_inventory_amount_ratio']; manifest_operation:cross_check=['trend', 'filter', 'rank', 'anomaly']; manifest_operation:counter_evidence=['trend', 'filter', 'rank', 'anomaly']; top_n=None |
| C6 | PARTIAL | `req-cd4c5e4b` | 69.336 | called | rejected_llm_then_deterministic | get_entity_time_series | 0 | invalid_replan | evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:trend=['filter', 'cross_check']; evidence_dimension=business_group |
| D7 | PASS | `req-ee96709a` | 14.586 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed |  |
| D8 | PARTIAL | `req-b651a4f0` | 20.274 | called | rejected_llm_then_deterministic | get_entity_performance_snapshot, get_inventory_turnover_proxy, get_entity_cross_section_comparison, get_anomalies | 0 | completed | top_n=None; proxy_not_used_when_forbidden=['get_entity_performance_snapshot', 'get_inventory_turnover_proxy', 'get_entity_cross_section_comparison', 'get_anomalies'] |
| D9 | PARTIAL | `req-335065bf` | 21.639 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed | top_n=None |
| D10 | PARTIAL | `req-bf6a3158` | 19.595 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy | 0 | completed | manifest_operation:exclude=['compare', 'cross_check', 'rank', 'proxy'] |
| E11 | PASS | `req-3ef71724` | 20.602 | valid | llm_planner | get_entity_month_table | 0 | completed |  |
| E12 | PARTIAL | `req-57c47f59` | 36.678 | called | rejected_llm_then_deterministic | get_entity_time_series | 0 | invalid_replan | evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:rank=['compare', 'trend', 'filter']; top_n=None |
| E13 | PASS | `req-5681a3c4` | 34.844 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_entity_performance_snapshot | 0 | invalid_replan |  |
| E14 | PASS | `req-cb92abdf` | 20.453 | valid | llm_planner | get_entity_period_pair_value | 0 | completed |  |
| F15 | PARTIAL | `req-5872a0ca` | 26.554 | valid | llm_planner | get_revenue_inventory_relationship, get_anomalies, get_inventory_turnover_proxy, get_entity_performance_snapshot | 0 | completed | manifest_metric:inventory_amount=['inventory_qty', 'risk_score']; manifest_operation:rank=['filter', 'anomaly'] |
| F16 | PARTIAL | `req-edcef487` | 23.327 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed | manifest_operation:cross_check=['filter']; manifest_operation:limitations=['filter'] |
| G17 | PARTIAL | `req-49426d76` | 43.198 | called | rejected_llm_then_deterministic | get_entity_time_series | 0 | invalid_replan | evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:trend=['filter']; manifest_operation:cross_check=['filter'] |
| G18 | PARTIAL | `req-e4c4f317` | 18.145 | called | rejected_llm_then_deterministic | get_revenue_inventory_relationship, get_anomalies, get_inventory_turnover_proxy, get_entity_performance_snapshot | 0 | completed | manifest_metric:revenue_amount=['inventory_qty', 'risk_score']; manifest_metric:inventory_amount=['inventory_qty', 'risk_score']; manifest_operation:filter=['risk_scan']; manifest_operation:trend=['risk_scan']; manifest_operation:cross_check=['risk_scan'] |
| G19 | PARTIAL | `req-cf70ec1a` | 24.805 | called | rejected_llm_then_deterministic | get_entity_metric_ranking | 0 | completed | manifest_metric:risk_score=['revenue_amount', 'inventory_amount', 'inventory_qty', 'revenue_inventory_amount_ratio']; evidence_metric:risk_score=; manifest_operation:cross_check=['trend', 'rank', 'counter_evidence']; manifest_operation:anomaly=['trend', 'rank', 'counter_evidence'] |
| H20 | PARTIAL | `req-9ac5441d` | 22.056 | valid | llm_planner | get_inventory_turnover_proxy | 0 | completed | evidence_dimension=business_group |
| H21 | PARTIAL | `req-688d2763` | 20.943 | called | rejected_llm_then_deterministic | get_entity_contribution_analysis | 0 | invalid_replan | manifest_operation:counter_evidence=['contribution_analysis'] |
| H22 | PASS | `req-574141f3` | 28.753 | called | rejected_llm_then_deterministic |  | 0 | invalid_replan |  |
| B3-P1 | PARTIAL | `req-67aed26e` | 32.471 | valid | llm_planner | get_entity_period_pair_comparison | 0 | completed | evidence_metric:revenue_amount=; manifest_operation:cross_check=['compare', 'trend', 'filter', 'rank']; top_n=None; has_counter_or_risk_context={"headline": "結論：2026-02 庫存金額相較 2026-01 增加 690,150,598.34，變化率為 0.68%。", "key_observations": ["2026-02 相較 2026-01 庫存金額增加 690,150,598.34。", "2026-02 相較 2026-01 庫存數量下降 358,575,423.00。", "2026-02 相較 2026- |
| B3-P2 | PARTIAL | `req-23c5d510` | 33.052 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies | 0 | completed | manifest_metric:inventory_qty=['revenue_amount', 'inventory_amount']; manifest_operation:cross_check=['compare', 'rank']; top_n=None |
| C5-P1 | PARTIAL | `req-d70a8bb3` | 22.891 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot | 0 | completed | manifest_metric:risk_score=['revenue_amount', 'inventory_qty', 'inventory_amount', 'revenue_inventory_amount_ratio']; manifest_operation:cross_check=['trend', 'anomaly']; manifest_operation:rank=['trend', 'anomaly']; manifest_operation:counter_evidence=['trend', 'anomaly']; top_n=None |
| C5-P2 | PARTIAL | `req-ea7f4e1b` | 21.783 | called | rejected_llm_then_deterministic | get_entity_trend_comparison, get_entity_performance_snapshot | 0 | completed | manifest_operation:cross_check=['trend', 'counter_evidence']; manifest_operation:rank=['trend', 'counter_evidence']; manifest_operation:anomaly=['trend', 'counter_evidence']; top_n=None |
| D7-P1 | PASS | `req-c5513b30` | 18.886 | valid | llm_planner | get_entity_cross_section_comparison, get_inventory_turnover_proxy | 0 | completed |  |
| D7-P2 | PARTIAL | `req-79d6c536` | 13.006 | valid | llm_planner | get_entity_performance_snapshot, get_inventory_turnover_proxy | 0 | completed | manifest_operation:exclude=['proxy']; manifest_operation:limitations=['proxy'] |
| E12-P1 | FAIL | `None` | 75.076 | not-called | None |  | 0 | None | http_200=TimeoutError: timed out; manifest_metric:revenue_amount=None; evidence_metric:revenue_amount=; manifest_metric:inventory_amount=None; evidence_metric:inventory_amount= |
| E12-P2 | PARTIAL | `req-07c4f91a` | 29.73 | called | rejected_llm_then_deterministic | get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies | 0 | completed | manifest_operation:trend=['compare', 'rank']; recent_n={'mode': 'latest_month', 'month': None, 'single_month': None, 'period_a': None, 'period_b': None, 'start_month': None, 'end_month': None, 'recent_n': None, 'yoy': False} |
| G17-P1 | PARTIAL | `req-ba498428` | 42.991 | called | rejected_llm_then_deterministic | get_entity_time_series | 0 | invalid_replan | evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:filter=['entity_time_series']; manifest_operation:trend=['entity_time_series'] |
| G17-P2 | PARTIAL | `req-5c70f74c` | 29.442 | called | rejected_llm_then_deterministic | get_metric_table | 0 | invalid_replan | evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; manifest_metric:inventory_qty=['revenue_amount', 'inventory_amount']; evidence_metric:inventory_qty=; manifest_operation:filter=['metric_lookup'] |

## A1 PASS

- Request ID: `req-53955a74`
- Family: `continuous_conditions` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_revenue_inventory_relationship
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "cross_check": true, "rank": true, "relationship": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## A2 PARTIAL

- Request ID: `req-98afef8d`
- Family: `continuous_conditions` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": true, "relationship": false}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"sourc`
- Failure reason: manifest_operation:cross_check=['trend', 'filter', 'relationship']

## B3 PASS

- Request ID: `req-a8d87293`
- Family: `topn_entity_continuity` / Canonical: `entity_period_pair_table_lookup`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_table, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false, "filter": false, "cross_check": true, "rank": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_period_pair_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_period_pair_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}]`
- Failure reason: none

## B4 PARTIAL

- Request ID: `req-0bd23984`
- Family: `topn_entity_continuity` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": false, "filter": true, "cross_check": false, "rank": true, "counter_evidence": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未`
- Failure reason: manifest_metric:risk_score=['revenue_amount', 'inventory_qty', 'inventory_amount', 'revenue_inventory_amount_ratio']

## C5 PARTIAL

- Request ID: `req-6e8fcebf`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "filter": false, "rank": true, "anomaly": true}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}]`
- Failure reason: manifest_metric:risk_score=['revenue_amount', 'inventory_qty', 'inventory_amount', 'revenue_inventory_amount_ratio']; manifest_operation:cross_check=['trend', 'filter', 'rank', 'anomaly']; manifest_operation:counter_evidence=['trend', 'filter', 'rank', 'anomaly']; top_n=None

## C6 PARTIAL

- Request ID: `req-cd4c5e4b`
- Family: `management_judgement` / Canonical: `entity_time_series`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_time_series: ['entity_value']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_time_series
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false, "inventory_qty": false, "inventory_amount": false, "revenue_inventory_amount_ratio": false}, "requested_operations": {"filter": true, "cross_check": true}, "evidence_count": 3}`
- Entity sets: `[]`
- Failure reason: evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:trend=['filter', 'cross_check']; evidence_dimension=business_group

## D7 PASS

- Request ID: `req-ee96709a`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "proxy": true, "limitations": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## D8 PARTIAL

- Request ID: `req-b651a4f0`
- Family: `capability_boundary` / Canonical: `performance_assessment`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_performance_snapshot, get_inventory_turnover_proxy, get_entity_cross_section_comparison, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "revenue_amount": true, "inventory_amount": true, "risk_score": true, "health_score": false}, "requested_operations": {"filter": false, "proxy": false, "limitations": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: top_n=None; proxy_not_used_when_forbidden=['get_entity_performance_snapshot', 'get_inventory_turnover_proxy', 'get_entity_cross_section_comparison', 'get_anomalies']

## D9 PARTIAL

- Request ID: `req-335065bf`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "risk_score": true}, "requested_operations": {"compare": false, "filter": false, "cross_check": true, "rank": true, "proxy": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: top_n=None

## D10 PARTIAL

- Request ID: `req-bf6a3158`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "revenue_amount": true, "inventory_amount": true}, "requested_operations": {"compare": false, "cross_check": false, "rank": false, "proxy": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: manifest_operation:exclude=['compare', 'cross_check', 'rank', 'proxy']

## E11 PASS

- Request ID: `req-3ef71724`
- Family: `field_mapping` / Canonical: `entity_month_table_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_month_table
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"filter": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_month_table", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "7製造", "未對應"]}, {"source_tool": "get_entity_month_table", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 7, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造"]}]`
- Failure reason: none

## E12 PARTIAL

- Request ID: `req-57c47f59`
- Family: `dimension_drilldown` / Canonical: `entity_time_series`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:missing_required_metric:inventory_qty
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_time_series
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false, "inventory_qty": false, "inventory_amount": false}, "requested_operations": {"compare": true, "trend": true, "filter": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:rank=['compare', 'trend', 'filter']; top_n=None

## E13 PASS

- Request ID: `req-5681a3c4`
- Family: `dimension_drilldown` / Canonical: `metric_relationship_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:entity_value_missing
- Replan: count=0 stop=invalid_replan
- Tools: get_revenue_inventory_relationship, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"filter": true, "cross_check": true, "relationship": false}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}]`
- Failure reason: none

## E14 PASS

- Request ID: `req-cb92abdf`
- Family: `field_mapping` / Canonical: `entity_period_pair_metric_lookup`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_value
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false}, "evidence_count": 3}`
- Entity sets: `[]`
- Failure reason: none

## F15 PARTIAL

- Request ID: `req-5872a0ca`
- Family: `replan_conflict` / Canonical: `risk_scan`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_anomalies, get_inventory_turnover_proxy, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_qty": true, "risk_score": true}, "requested_operations": {"filter": false, "anomaly": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: manifest_metric:inventory_amount=['inventory_qty', 'risk_score']; manifest_operation:rank=['filter', 'anomaly']

## F16 PARTIAL

- Request ID: `req-edcef487`
- Family: `replan_conflict` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"filter": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: manifest_operation:cross_check=['filter']; manifest_operation:limitations=['filter']

## G17 PARTIAL

- Request ID: `req-49426d76`
- Family: `semantic_generalization` / Canonical: `entity_time_series`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_time_series: ['entity_value']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_time_series
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false, "inventory_qty": false, "inventory_amount": false}, "requested_operations": {"filter": true}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:trend=['filter']; manifest_operation:cross_check=['filter']

## G18 PARTIAL

- Request ID: `req-e4c4f317`
- Family: `semantic_generalization` / Canonical: `risk_scan`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_revenue_inventory_relationship, get_anomalies, get_inventory_turnover_proxy, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"inventory_qty": true, "risk_score": true}, "requested_operations": {"risk_scan": false}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}, {"source_tool": "get_revenue_inventory_relationship", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: manifest_metric:revenue_amount=['inventory_qty', 'risk_score']; manifest_metric:inventory_amount=['inventory_qty', 'risk_score']; manifest_operation:filter=['risk_scan']; manifest_operation:trend=['risk_scan']; manifest_operation:cross_check=['risk_scan']

## G19 PARTIAL

- Request ID: `req-cf70ec1a`
- Family: `semantic_generalization` / Canonical: `entity_ranking`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_metric_ranking
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "rank": true, "counter_evidence": true}, "evidence_count": 4}`
- Entity sets: `[{"source_tool": "get_entity_metric_ranking", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "4筆電+盈嘉"]}, {"source_tool": "get_entity_metric_ranking", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "4筆電+盈嘉"]}, {"source_tool": "get_entity_metric_ranking", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "4筆電+盈嘉"]}, {"source_tool": "get_entity_metric_ranking", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 3, "entities": ["1網通+技鋼", "3通路方案", "5百事益"]}]`
- Failure reason: manifest_metric:risk_score=['revenue_amount', 'inventory_amount', 'inventory_qty', 'revenue_inventory_amount_ratio']; evidence_metric:risk_score=; manifest_operation:cross_check=['trend', 'rank', 'counter_evidence']; manifest_operation:anomaly=['trend', 'rank', 'counter_evidence']

## H20 PARTIAL

- Request ID: `req-9ac5441d`
- Family: `capability_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "filter": false, "rank": false, "proxy": false}, "evidence_count": 1}`
- Entity sets: `[{"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 3, "entities": ["2技宸", "3通路方案", "4筆電+盈嘉"]}]`
- Failure reason: evidence_dimension=business_group

## H21 PARTIAL

- Request ID: `req-688d2763`
- Family: `capability_boundary` / Canonical: `contribution_analysis`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_contribution_analysis: ['period_a', 'period_b']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_contribution_analysis
- Evidence coverage: `{"requested_metrics": {"inventory_amount": false}, "requested_operations": {"contribution_analysis": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: manifest_operation:counter_evidence=['contribution_analysis']

## H22 PASS

- Request ID: `req-574141f3`
- Family: `capability_boundary` / Canonical: `forecast_unsupported`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:forecast_became_supported
- Replan: count=0 stop=invalid_replan
- Tools: 
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false}, "requested_operations": {"forecast_unsupported": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: none

## B3-P1 PARTIAL

- Request ID: `req-67aed26e`
- Family: `topn_entity_continuity` / Canonical: `period_pair_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_period_pair_comparison
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false, "inventory_qty": true, "inventory_amount": true}, "requested_operations": {"compare": true, "trend": false, "filter": false, "rank": true}, "evidence_count": 3}`
- Entity sets: `[]`
- Failure reason: evidence_metric:revenue_amount=; manifest_operation:cross_check=['compare', 'trend', 'filter', 'rank']; top_n=None; has_counter_or_risk_context={"headline": "結論：2026-02 庫存金額相較 2026-01 增加 690,150,598.34，變化率為 0.68%。", "key_observations": ["2026-02 相較 2026-01 庫存金額增加 690,150,598.34。", "2026-02 相較 2026-01 庫存數量下降 358,575,423.00。", "2026-02 相較 2026-

## B3-P2 PARTIAL

- Request ID: `req-23c5d510`
- Family: `topn_entity_continuity` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true}, "requested_operations": {"compare": true, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: manifest_metric:inventory_qty=['revenue_amount', 'inventory_amount']; manifest_operation:cross_check=['compare', 'rank']; top_n=None

## C5-P1 PARTIAL

- Request ID: `req-d70a8bb3`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_anomalies, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_qty": true, "inventory_amount": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "anomaly": true}, "evidence_count": 6}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: manifest_metric:risk_score=['revenue_amount', 'inventory_qty', 'inventory_amount', 'revenue_inventory_amount_ratio']; manifest_operation:cross_check=['trend', 'anomaly']; manifest_operation:rank=['trend', 'anomaly']; manifest_operation:counter_evidence=['trend', 'anomaly']; top_n=None

## C5-P2 PARTIAL

- Request ID: `req-ea7f4e1b`
- Family: `management_judgement` / Canonical: `entity_trend_comparison`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_trend_comparison, get_entity_performance_snapshot
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true, "risk_score": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"trend": true, "counter_evidence": true}, "evidence_count": 5}`
- Entity sets: `[{"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "inventory_qty", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_trend_comparison", "metric": "revenue_inventory_amount_ratio", "entity_dimension": "business_group", "count": 2, "entities": ["1網通+技鋼", "2技宸"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}]`
- Failure reason: manifest_operation:cross_check=['trend', 'counter_evidence']; manifest_operation:rank=['trend', 'counter_evidence']; manifest_operation:anomaly=['trend', 'counter_evidence']; top_n=None

## D7-P1 PASS

- Request ID: `req-c5513b30`
- Family: `proxy_boundary` / Canonical: `cross_section_compare`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true}, "requested_operations": {"compare": false, "proxy": true, "limitations": true}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: none

## D7-P2 PARTIAL

- Request ID: `req-79d6c536`
- Family: `proxy_boundary` / Canonical: `performance_assessment`
- Planner: called=True valid=True source=llm_planner fallback=None
- Replan: count=0 stop=completed
- Tools: get_entity_performance_snapshot, get_inventory_turnover_proxy
- Evidence coverage: `{"requested_metrics": {"revenue_inventory_amount_ratio": true, "inventory_amount": true, "health_score": false, "risk_score": true, "revenue_amount": true}, "requested_operations": {"proxy": true}, "evidence_count": 2}`
- Entity sets: `[{"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "business_group", "count": 8, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益", "6雲城", "7製造", "未對應"]}, {"source_tool": "get_inventory_turnover_proxy", "metric": null, "entity_dimension": null, "count": 5, "entities": ["1網通+技鋼", "2技宸", "3通路方案", "4筆電+盈嘉", "5百事益"]}]`
- Failure reason: manifest_operation:exclude=['proxy']; manifest_operation:limitations=['proxy']

## E12-P1 FAIL

- Request ID: `None`
- Family: `dimension_drilldown` / Canonical: `None`
- Planner: called=False valid=False source=None fallback=None
- Replan: count=0 stop=None
- Tools: 
- Evidence coverage: `{"requested_metrics": {}, "requested_operations": {}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: http_200=TimeoutError: timed out; manifest_metric:revenue_amount=None; evidence_metric:revenue_amount=; manifest_metric:inventory_amount=None; evidence_metric:inventory_amount=

## E12-P2 PARTIAL

- Request ID: `req-07c4f91a`
- Family: `dimension_drilldown` / Canonical: `cross_section_compare`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=planner_or_evidence_repair
- Replan: count=0 stop=completed
- Tools: get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies
- Evidence coverage: `{"requested_metrics": {"revenue_amount": true, "inventory_amount": true, "inventory_qty": true, "revenue_inventory_amount_ratio": true}, "requested_operations": {"compare": true, "rank": true}, "evidence_count": 3}`
- Entity sets: `[{"source_tool": "get_entity_cross_section_comparison", "metric": null, "entity_dimension": "product_line_5", "count": 10, "entities": ["IOT", "Other", "Server", "主板", "專案電腦", "百事益", "筆電", "螢幕", "雲城", "顯卡"]}, {"source_tool": "get_entity_performance_snapshot", "metric": null, "entity_dimension": "product_line_5", "count": 3, "entities": ["Server", "百事益", "顯卡"]}]`
- Failure reason: manifest_operation:trend=['compare', 'rank']; recent_n={'mode': 'latest_month', 'month': None, 'single_month': None, 'period_a': None, 'period_b': None, 'start_month': None, 'end_month': None, 'recent_n': None, 'yoy': False}

## G17-P1 PARTIAL

- Request ID: `req-ba498428`
- Family: `semantic_generalization` / Canonical: `entity_time_series`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner omitted required args for get_entity_time_series: ['entity_value']
- Replan: count=0 stop=invalid_replan
- Tools: get_entity_time_series
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false, "inventory_qty": false, "inventory_amount": false}, "requested_operations": {"entity_time_series": false}, "evidence_count": 0}`
- Entity sets: `[]`
- Failure reason: evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; evidence_metric:inventory_qty=; manifest_operation:filter=['entity_time_series']; manifest_operation:trend=['entity_time_series']

## G17-P2 PARTIAL

- Request ID: `req-5c70f74c`
- Family: `semantic_generalization` / Canonical: `metric_lookup`
- Planner: called=True valid=False source=rejected_llm_then_deterministic fallback=invalid_initial_plan:Planner returned unsupported metric for get_metric_table: revenue_amount
- Replan: count=0 stop=invalid_replan
- Tools: get_metric_table
- Evidence coverage: `{"requested_metrics": {"revenue_amount": false, "inventory_amount": false}, "requested_operations": {"metric_lookup": false}, "evidence_count": 6}`
- Entity sets: `[]`
- Failure reason: evidence_metric:revenue_amount=; evidence_metric:inventory_amount=; manifest_metric:inventory_qty=['revenue_amount', 'inventory_amount']; evidence_metric:inventory_qty=; manifest_operation:filter=['metric_lookup']
