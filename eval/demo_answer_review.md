# Demo Answer Review

- cases: 63
- passed: 63
- failed: 0
- mode: direct deterministic assistant; LLM planner and rewriter disabled

| # | Question | Task Family | Answer Type | Passed | Failures | Headline |
|---:|---|---|---|---:|---|---|
| 1 | 總體營收趨勢如何？ | overall_trend_analysis | overall_trend_analysis | True | - | 結論：整體營收在 2025-01 至 2026-02 期間呈現上升，最新月份 2026-02 為 32,877,963,113。 |
| 2 | 整體庫存各月變化？ | overall_trend_analysis | entity_time_series | True | - | 結論：整體庫存金額在 2025-01 至 2026-02 期間呈現上升，最新月份 2026-02 為 102,271,212,123.05。 |
| 3 | 請整理最新月份各新事業群的營收與庫存重點 | latest_month_entity_summary | latest_month_entity_summary | True | - | 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。 |
| 4 | 哪個新事業群營收最高？ | entity_ranking | ranking | True | - | 結論：最新月份 2026-02 營收最高的事業群是 1網通+技鋼，營收為 24,670,343,477。 |
| 5 | 哪個新事業群營收相對庫存效率最低？ | entity_ranking | ranking | True | - | 結論：最新月份 2026-02 營收相對庫存效率 proxy最低的事業群是 7製造，營收相對庫存效率 proxy為 -5.20。 |
| 6 | 各新事業群近 6 個月營收趨勢 | entity_trend_comparison | entity_time_series | True | - | 結論：近月營收成長較明顯的事業群是 1網通+技鋼，變化率為 0.59。 |
| 7 | 比較最新月份各五大產品線營收與庫存 | cross_section_compare | comparison | True | - | 結論：2026-02 各產品線比較下，Server 營收規模較高，Server 庫存水位較高；但 筆電 的營收相對庫存效率較弱，需搭配庫存壓力判讀。 |
| 8 | 哪個產品線庫存壓力較高？ | performance_assessment | performance_weakness | True | - | 結論：目前表現較弱的產品線優先看 Other，因為其 存在 revenue_only 或 inventory_only grain；產品線營收較前期下降，health_score 為 0.10。 |
| 9 | Server 產品線各月營收 | entity_time_series | entity_time_series | True | - | 結論：Server各月營收在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 24,670,343,477。 |
| 10 | 比較 3通路方案 各月營收 | entity_time_series | entity_time_series | True | - | 結論：3通路方案各月營收在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 7,539,188,847。 |
| 11 | 1網通+技鋼 各月庫存變化 | entity_time_series | entity_time_series | True | - | 結論：1網通+技鋼各月庫存金額在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 73,298,408,408.75。 |
| 12 | 比較 2025 年 12 月與 2026 年 1 月營收差別 | period_pair_compare | period_pair_compare | True | - | 結論：2026-01 營收相較 2025-12 增加 2,812,340,673.00，變化率為 9.28%。 |
| 13 | 2026 年 1 月比 2025 年 1 月營收差多少？ | period_pair_compare | period_pair_compare | True | - | 結論：2026-01 營收相較 2025-01 增加 12,026,989,797.00，變化率為 57.02%。 |
| 14 | 2026-01 比 2025-12 成長主要來自哪個新事業群？ | contribution_analysis | contribution_analysis | True | - | 結論：2026-01 相較 2025-12 的營收變化主要由 3通路方案 貢獻，變化為 4,280,740,458.00。 |
| 15 | 有沒有營收下降但庫存上升的新事業群？ | metric_relationship_analysis | metric_relationship_analysis | True | - | 結論：目前可觀察到事業群存在營收與庫存背離訊號，例如 revenue_up_inventory_up。 |
| 16 | 哪些產品線營收相對庫存效率變差？ | metric_relationship_analysis | metric_query | True | - | 結論：目前可觀察到產品線存在營收與庫存背離訊號，例如 ratio_worsening。 |
| 17 | 3通路方案底下哪個產品線表現較差？ | parent_child_drilldown | parent_child_drilldown | True | - | 結論：在 3通路方案 底下，專案電腦 產品線表現較弱 / 庫存壓力較高。 |
| 18 | 1網通+技鋼底下產品線庫存壓力最高的是誰？ | parent_child_drilldown | parent_child_drilldown | True | - | 結論：在 1網通+技鋼 底下，Other 產品線表現較弱 / 庫存壓力較高。 |
| 19 | 畫總體營收趨勢 | chart_request | chart | True | - | 結論：已產生 總體營收趨勢（overall_revenue_trend_line），可用於前端圖表渲染與表格檢視。 |
| 20 | 畫各新事業群營收排名 | chart_request | chart | True | - | 結論：已產生 2026-02 各事業群營收長條圖（business_group_revenue_bar），可用於前端圖表渲染與表格檢視。 |
| 21 | 畫各產品線 health_score 排名 | chart_request | chart | True | - | 結論：已產生 產品線 health_score 排名（product_line_health_score_bar），可用於前端圖表渲染與表格檢視。 |
| 22 | 畫 3通路方案各月營收趨勢 | chart_request | chart | True | - | 結論：已產生 3通路方案 各月營收趨勢（entity_time_series_line），可用於前端圖表渲染與表格檢視。 |
| 23 | 畫營收與庫存關係圖 | chart_request | chart | True | - | 結論：已產生 事業群營收/庫存金額 proxy 排名（business_group_revenue_inventory_ratio_bar），可用於前端圖表渲染與表格檢視。 |
| 24 | 下個月營收會不會改善？ | forecast_unsupported | unsupported | True | - | 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。 |
| 25 | 未來哪個事業群會成長？ | forecast_unsupported | unsupported | True | - | 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。 |
| 26 | 請整理最新月份各事業群的營收與庫存重點 | latest_month_entity_summary | latest_month_entity_summary | True | - | 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。 |
| 27 | 請整理最新月份各新事業群的營收與庫存重點 | latest_month_entity_summary | latest_month_entity_summary | True | - | 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。 |
| 28 | 請整理最新月份各 BU 營收與庫存重點 | latest_month_entity_summary | metric_query | True | - | 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。 |
| 29 | 列出通路方案 2026/2 最新營收 | metric_lookup | metric_query | True | - | 結論：2026-02 事業群 3通路方案 的營收為 7,539,188,847。 |
| 30 | 顯示 1網通+技鋼 2026年2月 庫存金額 | metric_lookup | metric_query | True | - | 結論：2026-02 事業群 1網通+技鋼 的庫存金額為 73,298,408,408.75。 |
| 31 | 查詢 Server 2026-02 營收 | metric_lookup | metric_query | True | - | 結論：2026-02 產品線 Server 的營收為 24,670,343,477。 |
| 32 | 看一下 IOT 2026/2 庫存 QTY | metric_lookup | metric_query | True | - | 結論：2026-02 產品線 IOT 的庫存數量為 851,291。 |
| 33 | 畫出 2025年 2 月 各事業群營收圓餅圖 | chart_request | chart | True | - | 結論：已產生 2025-02 各事業群營收圓餅圖（business_group_revenue_pie），可用於前端圖表渲染與表格檢視。 |
| 34 | 畫出 2026年2月 各產品線庫存長條圖 | chart_request | chart | True | - | 結論：已產生 2026-02 各產品線庫存金額長條圖（product_line_inventory_bar），可用於前端圖表渲染與表格檢視。 |
| 35 | 列出2025年3月各產品線庫存資料 | entity_month_table_lookup | entity_month_table_lookup | True | - | 結論：已列出 2025-03 各產品線庫存金額資料，共 10 筆；庫存金額最高的是 Server。 |
| 36 | 比較2025年3月各產品線庫存資料 | cross_section_compare | comparison | True | - | 結論：2025-03 各產品線庫存金額比較下，庫存金額最高的是 Server，最低的是 IOT。 |
| 37 | 比較2025年3月各事業群庫存資料 | cross_section_compare | comparison | True | - | 結論：2025-03 各事業群庫存金額比較下，庫存金額最高的是 1網通+技鋼，最低的是 6雲城。 |
| 38 | 比較2025年3月各事業群營收資料 | cross_section_compare | comparison | True | - | 結論：2025-03 各事業群營收比較下，營收最高的是 3通路方案，最低的是 6雲城。 |
| 39 | 顯示2025/3各BU營收資料 | entity_month_table_lookup | entity_month_table_lookup | True | - | 結論：已列出 2025-03 各事業群營收資料，共 7 筆；營收最高的是 3通路方案。 |
| 40 | 查詢2025-03各產品線庫存QTY | entity_month_table_lookup | entity_month_table_lookup | True | - | 結論：已列出 2025-03 各產品線庫存數量資料，共 10 筆；庫存數量最高的是 顯卡。 |
| 41 | 看一下2025年3月各事業群資料 | entity_month_table_lookup | entity_month_table_lookup | True | - | 結論：已列出 2025-03 各事業群營收資料，共 7 筆；營收最高的是 3通路方案。 |
| 42 | 列出 2025/02 與 2025/03 產品線的庫存 | entity_period_pair_table_lookup | period_pair_compare | True | - | 結論：已列出 2025-02 與 2025-03 各產品線庫存金額資料，共 10 筆；2025-03 最高的是 Server。 |
| 43 | 顯示 2025年2月和2025年3月各事業群營收 | entity_period_pair_table_lookup | entity_month_table_lookup | True | - | 結論：已列出 2025-02 與 2025-03 各事業群營收資料，共 7 筆；2025-03 最高的是 3通路方案。 |
| 44 | 列出 2025/01 到 2025/03 各產品線庫存 | entity_multi_month_table_lookup | entity_month_table_lookup | True | - | 結論：已列出 2025-01 至 2025-03 各產品線庫存金額資料，共 30 筆。 |
| 45 | 比較 Server 2025/02 和 2025/03 庫存 | entity_period_pair_metric_lookup | period_pair_compare | True | - | 結論：Server 2025-03 庫存金額相較 2025-02 增加 6,738,471,043.99。 |
| 46 | 畫出 2025/02 與 2025/03 各產品線庫存比較圖 | chart_request | chart | True | - | 結論：已產生 2025-02 與 2025-03 各產品線庫存金額比較圖（entity_period_pair_table_chart），可用於前端圖表渲染與表格檢視。 |
| 47 | 比較 2025/02 與 2025/03 各產品線庫存資料 | entity_period_pair_table_lookup | comparison | True | - | 結論：已列出 2025-02 與 2025-03 各產品線庫存金額資料，共 10 筆；2025-03 最高的是 Server。 |
| 48 | 顯示 2025-02 vs 2025-03 各BU庫存資料 | entity_period_pair_table_lookup | comparison | True | - | 結論：已列出 2025-02 與 2025-03 各事業群庫存金額資料，共 8 筆；2025-03 最高的是 1網通+技鋼。 |
| 49 | 顯示 2025Q1 各事業群營收 | entity_multi_month_table_lookup | metric_query | True | - | 結論：已列出 2025-01 至 2025-03 各事業群營收資料，共 21 筆。 |
| 50 | 列出 3通路方案 2025/02 與 2025/03 營收 | entity_period_pair_metric_lookup | period_pair_compare | True | - | 結論：3通路方案 2025-03 營收相較 2025-02 增加 2,882,781,571。 |
| 51 | 列出 2025年3月 3通路方案底下各產品線庫存 | entity_month_table_lookup | parent_child_drilldown | True | - | 結論：已列出 2025-03 各產品線庫存金額資料，共 5 筆；庫存金額最高的是 顯卡。 |
| 52 | 比較 2025/02 與 2025/03 3通路方案底下各產品線營收 | entity_period_pair_table_lookup | parent_child_drilldown | True | - | 結論：已列出 2025-02 與 2025-03 各產品線營收資料，共 6 筆；2025-03 最高的是 顯卡。 |
| 53 | 畫出 2025/02 與 2025/03 各產品線庫存比較圖 | chart_request | chart | True | - | 結論：已產生 2025-02 與 2025-03 各產品線庫存金額比較圖（entity_period_pair_table_chart），可用於前端圖表渲染與表格檢視。 |
| 54 | 畫 2025Q1 各事業群營收趨勢圖 | chart_request | chart | True | - | 結論：已產生 2025-01 至 2025-03 各事業群營收趨勢圖（entity_multi_month_table_line），可用於前端圖表渲染與表格檢視。 |
| 55 | 畫 3通路方案 2025/02 到 2025/06 營收折線圖 | chart_request | chart | True | - | 結論：已產生 3通路方案 2025-02 至 2025-06 營收折線圖（entity_time_series_line），可用於前端圖表渲染與表格檢視。 |
| 56 | 畫 2025年3月 3通路方案底下各產品線庫存長條圖 | chart_request | chart | True | - | 結論：已產生 2025-03 3通路方案 底下各產品線庫存金額長條圖（entity_month_table_bar），可用於前端圖表渲染與表格檢視。 |
| 57 | 列出 2025年3月各產品線資料 | entity_month_table_lookup | entity_month_table_lookup | True | - | 結論：已列出 2025-03 各產品線營收資料，共 10 筆；營收最高的是 顯卡。 |
| 58 | 比較 2025年3月各事業群資料 | cross_section_compare | comparison | True | - | 結論：2025-03 各事業群比較下，3通路方案 營收規模較高，1網通+技鋼 庫存水位較高；但 1網通+技鋼 的營收相對庫存效率較弱，需搭配庫存壓力判讀。 |
| 59 | 列出 2025年3月產品線庫存 | entity_month_table_lookup | metric_query | True | - | 結論：已列出 2025-03 各產品線庫存金額資料，共 10 筆；庫存金額最高的是 Server。 |
| 60 | 比較 2025年3月事業群營收 | cross_section_compare | period_pair_compare | True | - | 結論：2025-03 各事業群營收比較下，營收最高的是 3通路方案，最低的是 6雲城。 |
| 61 | 列出 2025/09 與 2025/10 產品線的庫存 | entity_period_pair_table_lookup | period_pair_compare | True | - | 結論：已列出 2025-09 與 2025-10 各產品線庫存金額資料，共 9 筆；2025-10 最高的是 Server。 |
| 62 | 列出 2025/11 與 2025/12 產品線的庫存 | entity_period_pair_table_lookup | period_pair_compare | True | - | 結論：已列出 2025-11 與 2025-12 各產品線庫存金額資料，共 9 筆；2025-12 最高的是 Server。 |
| 63 | 列出 2025年2月和2025年3月各事業群營收 | entity_period_pair_table_lookup | entity_month_table_lookup | True | - | 結論：已列出 2025-02 與 2025-03 各事業群營收資料，共 7 筆；2025-03 最高的是 3通路方案。 |

## Check Details

### 1. 總體營收趨勢如何？

- headline: 結論：整體營收在 2025-01 至 2026-02 期間呈現上升，最新月份 2026-02 為 32,877,963,113。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 2. 整體庫存各月變化？

- headline: 結論：整體庫存金額在 2025-01 至 2026-02 期間呈現上升，最新月份 2026-02 為 102,271,212,123.05。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 3. 請整理最新月份各新事業群的營收與庫存重點

- headline: 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 4. 哪個新事業群營收最高？

- headline: 結論：最新月份 2026-02 營收最高的事業群是 1網通+技鋼，營收為 24,670,343,477。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 5. 哪個新事業群營收相對庫存效率最低？

- headline: 結論：最新月份 2026-02 營收相對庫存效率 proxy最低的事業群是 7製造，營收相對庫存效率 proxy為 -5.20。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 6. 各新事業群近 6 個月營收趨勢

- headline: 結論：近月營收成長較明顯的事業群是 1網通+技鋼，變化率為 0.59。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 7. 比較最新月份各五大產品線營收與庫存

- headline: 結論：2026-02 各產品線比較下，Server 營收規模較高，Server 庫存水位較高；但 筆電 的營收相對庫存效率較弱，需搭配庫存壓力判讀。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 8. 哪個產品線庫存壓力較高？

- headline: 結論：目前表現較弱的產品線優先看 Other，因為其 存在 revenue_only 或 inventory_only grain；產品線營收較前期下降，health_score 為 0.10。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 9. Server 產品線各月營收

- headline: 結論：Server各月營收在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 24,670,343,477。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 10. 比較 3通路方案 各月營收

- headline: 結論：3通路方案各月營收在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 7,539,188,847。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 11. 1網通+技鋼 各月庫存變化

- headline: 結論：1網通+技鋼各月庫存金額在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 73,298,408,408.75。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 12. 比較 2025 年 12 月與 2026 年 1 月營收差別

- headline: 結論：2026-01 營收相較 2025-12 增加 2,812,340,673.00，變化率為 9.28%。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 13. 2026 年 1 月比 2025 年 1 月營收差多少？

- headline: 結論：2026-01 營收相較 2025-01 增加 12,026,989,797.00，變化率為 57.02%。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 14. 2026-01 比 2025-12 成長主要來自哪個新事業群？

- headline: 結論：2026-01 相較 2025-12 的營收變化主要由 3通路方案 貢獻，變化為 4,280,740,458.00。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 15. 有沒有營收下降但庫存上升的新事業群？

- headline: 結論：目前可觀察到事業群存在營收與庫存背離訊號，例如 revenue_up_inventory_up。
- key_observation_count: `2`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 16. 哪些產品線營收相對庫存效率變差？

- headline: 結論：目前可觀察到產品線存在營收與庫存背離訊號，例如 ratio_worsening。
- key_observation_count: `2`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 17. 3通路方案底下哪個產品線表現較差？

- headline: 結論：在 3通路方案 底下，專案電腦 產品線表現較弱 / 庫存壓力較高。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 18. 1網通+技鋼底下產品線庫存壓力最高的是誰？

- headline: 結論：在 1網通+技鋼 底下，Other 產品線表現較弱 / 庫存壓力較高。
- key_observation_count: `2`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 19. 畫總體營收趨勢

- headline: 結論：已產生 總體營收趨勢（overall_revenue_trend_line），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `overall_revenue_trend_line, overall_revenue_trend_line`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 20. 畫各新事業群營收排名

- headline: 結論：已產生 2026-02 各事業群營收長條圖（business_group_revenue_bar），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `business_group_revenue_bar, business_group_revenue_bar`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 21. 畫各產品線 health_score 排名

- headline: 結論：已產生 產品線 health_score 排名（product_line_health_score_bar），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `product_line_health_score_bar, product_line_health_score_bar`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 22. 畫 3通路方案各月營收趨勢

- headline: 結論：已產生 3通路方案 各月營收趨勢（entity_time_series_line），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `entity_time_series_line, entity_time_series_line`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 23. 畫營收與庫存關係圖

- headline: 結論：已產生 事業群營收/庫存金額 proxy 排名（business_group_revenue_inventory_ratio_bar），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `business_group_revenue_inventory_ratio_bar, business_group_revenue_inventory_ratio_bar`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 24. 下個月營收會不會改善？

- headline: 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。
- key_observation_count: `2`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 25. 未來哪個事業群會成長？

- headline: 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。
- key_observation_count: `2`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 26. 請整理最新月份各事業群的營收與庫存重點

- headline: 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 27. 請整理最新月份各新事業群的營收與庫存重點

- headline: 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 28. 請整理最新月份各 BU 營收與庫存重點

- headline: 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 29. 列出通路方案 2026/2 最新營收

- headline: 結論：2026-02 事業群 3通路方案 的營收為 7,539,188,847。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 30. 顯示 1網通+技鋼 2026年2月 庫存金額

- headline: 結論：2026-02 事業群 1網通+技鋼 的庫存金額為 73,298,408,408.75。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 31. 查詢 Server 2026-02 營收

- headline: 結論：2026-02 產品線 Server 的營收為 24,670,343,477。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 32. 看一下 IOT 2026/2 庫存 QTY

- headline: 結論：2026-02 產品線 IOT 的庫存數量為 851,291。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 33. 畫出 2025年 2 月 各事業群營收圓餅圖

- headline: 結論：已產生 2025-02 各事業群營收圓餅圖（business_group_revenue_pie），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `business_group_revenue_pie, business_group_revenue_pie`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 34. 畫出 2026年2月 各產品線庫存長條圖

- headline: 結論：已產生 2026-02 各產品線庫存金額長條圖（product_line_inventory_bar），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `product_line_inventory_bar, product_line_inventory_bar`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 35. 列出2025年3月各產品線庫存資料

- headline: 結論：已列出 2025-03 各產品線庫存金額資料，共 10 筆；庫存金額最高的是 Server。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 36. 比較2025年3月各產品線庫存資料

- headline: 結論：2025-03 各產品線庫存金額比較下，庫存金額最高的是 Server，最低的是 IOT。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 37. 比較2025年3月各事業群庫存資料

- headline: 結論：2025-03 各事業群庫存金額比較下，庫存金額最高的是 1網通+技鋼，最低的是 6雲城。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 38. 比較2025年3月各事業群營收資料

- headline: 結論：2025-03 各事業群營收比較下，營收最高的是 3通路方案，最低的是 6雲城。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 39. 顯示2025/3各BU營收資料

- headline: 結論：已列出 2025-03 各事業群營收資料，共 7 筆；營收最高的是 3通路方案。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 40. 查詢2025-03各產品線庫存QTY

- headline: 結論：已列出 2025-03 各產品線庫存數量資料，共 10 筆；庫存數量最高的是 顯卡。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 41. 看一下2025年3月各事業群資料

- headline: 結論：已列出 2025-03 各事業群營收資料，共 7 筆；營收最高的是 3通路方案。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 42. 列出 2025/02 與 2025/03 產品線的庫存

- headline: 結論：已列出 2025-02 與 2025-03 各產品線庫存金額資料，共 10 筆；2025-03 最高的是 Server。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 43. 顯示 2025年2月和2025年3月各事業群營收

- headline: 結論：已列出 2025-02 與 2025-03 各事業群營收資料，共 7 筆；2025-03 最高的是 3通路方案。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 44. 列出 2025/01 到 2025/03 各產品線庫存

- headline: 結論：已列出 2025-01 至 2025-03 各產品線庫存金額資料，共 30 筆。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 45. 比較 Server 2025/02 和 2025/03 庫存

- headline: 結論：Server 2025-03 庫存金額相較 2025-02 增加 6,738,471,043.99。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 46. 畫出 2025/02 與 2025/03 各產品線庫存比較圖

- headline: 結論：已產生 2025-02 與 2025-03 各產品線庫存金額比較圖（entity_period_pair_table_chart），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `entity_period_pair_table_chart`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 47. 比較 2025/02 與 2025/03 各產品線庫存資料

- headline: 結論：已列出 2025-02 與 2025-03 各產品線庫存金額資料，共 10 筆；2025-03 最高的是 Server。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 48. 顯示 2025-02 vs 2025-03 各BU庫存資料

- headline: 結論：已列出 2025-02 與 2025-03 各事業群庫存金額資料，共 8 筆；2025-03 最高的是 1網通+技鋼。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 49. 顯示 2025Q1 各事業群營收

- headline: 結論：已列出 2025-01 至 2025-03 各事業群營收資料，共 21 筆。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 50. 列出 3通路方案 2025/02 與 2025/03 營收

- headline: 結論：3通路方案 2025-03 營收相較 2025-02 增加 2,882,781,571。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 51. 列出 2025年3月 3通路方案底下各產品線庫存

- headline: 結論：已列出 2025-03 各產品線庫存金額資料，共 5 筆；庫存金額最高的是 顯卡。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 52. 比較 2025/02 與 2025/03 3通路方案底下各產品線營收

- headline: 結論：已列出 2025-02 與 2025-03 各產品線營收資料，共 6 筆；2025-03 最高的是 顯卡。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 53. 畫出 2025/02 與 2025/03 各產品線庫存比較圖

- headline: 結論：已產生 2025-02 與 2025-03 各產品線庫存金額比較圖（entity_period_pair_table_chart），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `entity_period_pair_table_chart`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 54. 畫 2025Q1 各事業群營收趨勢圖

- headline: 結論：已產生 2025-01 至 2025-03 各事業群營收趨勢圖（entity_multi_month_table_line），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `entity_multi_month_table_line`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 55. 畫 3通路方案 2025/02 到 2025/06 營收折線圖

- headline: 結論：已產生 3通路方案 2025-02 至 2025-06 營收折線圖（entity_time_series_line），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `entity_time_series_line`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 56. 畫 2025年3月 3通路方案底下各產品線庫存長條圖

- headline: 結論：已產生 2025-03 3通路方案 底下各產品線庫存金額長條圖（entity_month_table_bar），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `entity_month_table_bar`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 57. 列出 2025年3月各產品線資料

- headline: 結論：已列出 2025-03 各產品線營收資料，共 10 筆；營收最高的是 顯卡。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 58. 比較 2025年3月各事業群資料

- headline: 結論：2025-03 各事業群比較下，3通路方案 營收規模較高，1網通+技鋼 庫存水位較高；但 1網通+技鋼 的營收相對庫存效率較弱，需搭配庫存壓力判讀。
- key_observation_count: `2`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 59. 列出 2025年3月產品線庫存

- headline: 結論：已列出 2025-03 各產品線庫存金額資料，共 10 筆；庫存金額最高的是 Server。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 60. 比較 2025年3月事業群營收

- headline: 結論：2025-03 各事業群營收比較下，營收最高的是 3通路方案，最低的是 6雲城。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 61. 列出 2025/09 與 2025/10 產品線的庫存

- headline: 結論：已列出 2025-09 與 2025-10 各產品線庫存金額資料，共 9 筆；2025-10 最高的是 Server。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 62. 列出 2025/11 與 2025/12 產品線的庫存

- headline: 結論：已列出 2025-11 與 2025-12 各產品線庫存金額資料，共 9 筆；2025-12 最高的是 Server。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 63. 列出 2025年2月和2025年3月各事業群營收

- headline: 結論：已列出 2025-02 與 2025-03 各事業群營收資料，共 7 筆；2025-03 最高的是 3通路方案。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_expected": true, "chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "must_include": true, "must_not_include": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "table_expected": true, "table_expected_columns": true, "unmapped_headline_guardrail": true}`
- failures: `-`
