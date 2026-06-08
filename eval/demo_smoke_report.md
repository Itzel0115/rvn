# Demo Smoke Report

- mode: direct
- cases: 60

| Question | Task Family | Key Obs | Table | Headline |
|---|---:|---:|---:|---|
| 總體營收趨勢如何？ | overall_trend_analysis | 1 | yes | 結論：整體營收在 2025-01 至 2026-02 期間呈現上升，最新月份 2026-02 為 32,877,963,113。 |
| 整體庫存各月變化？ | overall_trend_analysis | 1 | yes | 結論：整體庫存金額在 2025-01 至 2026-02 期間呈現上升，最新月份 2026-02 為 102,271,212,123.05。 |
| 請整理最新月份各新事業群的營收與庫存重點 | latest_month_entity_summary | 3 | yes | 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。 |
| 哪個新事業群營收最高？ | entity_ranking | 1 | yes | 結論：最新月份 2026-02 營收最高的事業群是 1網通+技鋼，營收為 24,670,343,477。 |
| 哪個新事業群營收相對庫存效率最低？ | entity_ranking | 1 | yes | 結論：最新月份 2026-02 營收相對庫存效率 proxy最低的事業群是 7製造，營收相對庫存效率 proxy為 -5.20。 |
| 各新事業群近 6 個月營收趨勢 | entity_trend_comparison | 1 | yes | 結論：近月營收成長較明顯的事業群是 1網通+技鋼，變化率為 0.59。 |
| 比較最新月份各五大產品線營收與庫存 | cross_section_compare | 3 | yes | 結論：2026-02 各產品線比較下，Server 營收規模較高，Server 庫存水位較高；但 筆電 的營收相對庫存效率較弱，需搭配庫存壓力判讀。 |
| 哪個產品線庫存壓力較高？ | performance_assessment | 3 | no | 結論：目前表現較弱的產品線優先看 Other，因為其 存在 revenue_only 或 inventory_only grain；產品線營收較前期下降，health_score 為 0.10。 |
| Server 產品線各月營收 | entity_time_series | 1 | yes | 結論：Server各月營收在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 24,670,343,477。 |
| 比較 3通路方案 各月營收 | entity_time_series | 1 | yes | 結論：3通路方案各月營收在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 7,539,188,847。 |
| 1網通+技鋼 各月庫存變化 | entity_time_series | 1 | yes | 結論：1網通+技鋼各月庫存金額在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 73,298,408,408.75。 |
| 比較 2025 年 12 月與 2026 年 1 月營收差別 | period_pair_compare | 1 | yes | 結論：2026-01 營收相較 2025-12 增加 2,812,340,673.00，變化率為 9.28%。 |
| 2026 年 1 月比 2025 年 1 月營收差多少？ | period_pair_compare | 1 | yes | 結論：2026-01 營收相較 2025-01 增加 12,026,989,797.00，變化率為 57.02%。 |
| 2026-01 比 2025-12 成長主要來自哪個新事業群？ | contribution_analysis | 1 | yes | 結論：2026-01 相較 2025-12 的營收變化主要由 3通路方案 貢獻，變化為 4,280,740,458.00。 |
| 有沒有營收下降但庫存上升的新事業群？ | metric_relationship_analysis | 2 | yes | 結論：目前可觀察到事業群存在營收與庫存背離訊號，例如 revenue_up_inventory_up。 |
| 哪些產品線營收相對庫存效率變差？ | metric_relationship_analysis | 2 | yes | 結論：目前可觀察到產品線存在營收與庫存背離訊號，例如 ratio_worsening。 |
| 3通路方案底下哪個產品線表現較差？ | parent_child_drilldown | 3 | yes | 結論：在 3通路方案 底下，專案電腦 產品線表現較弱 / 庫存壓力較高。 |
| 1網通+技鋼底下產品線庫存壓力最高的是誰？ | parent_child_drilldown | 2 | yes | 結論：在 1網通+技鋼 底下，Other 產品線表現較弱 / 庫存壓力較高。 |
| 畫總體營收趨勢 | chart_request | 3 | yes | 結論：已產生 總體營收趨勢（overall_revenue_trend_line），可用於前端圖表渲染與表格檢視。 |
| 畫各新事業群營收排名 | chart_request | 3 | yes | 結論：已產生 2026-02 各事業群營收長條圖（business_group_revenue_bar），可用於前端圖表渲染與表格檢視。 |
| 畫各產品線 health_score 排名 | chart_request | 3 | yes | 結論：已產生 產品線 health_score 排名（product_line_health_score_bar），可用於前端圖表渲染與表格檢視。 |
| 畫 3通路方案各月營收趨勢 | chart_request | 3 | yes | 結論：已產生 3通路方案 各月營收趨勢（entity_time_series_line），可用於前端圖表渲染與表格檢視。 |
| 畫營收與庫存關係圖 | chart_request | 3 | yes | 結論：已產生 事業群營收/庫存金額 proxy 排名（business_group_revenue_inventory_ratio_bar），可用於前端圖表渲染與表格檢視。 |
| 下個月營收會不會改善？ | forecast_unsupported | 2 | no | 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。 |
| 未來哪個事業群會成長？ | forecast_unsupported | 2 | no | 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。 |
| 請整理最新月份各事業群的營收與庫存重點 | latest_month_entity_summary | 3 | yes | 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。 |
| 請整理最新月份各新事業群的營收與庫存重點 | latest_month_entity_summary | 3 | yes | 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。 |
| 請整理最新月份各 BU 營收與庫存重點 | latest_month_entity_summary | 3 | yes | 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。 |
| 列出通路方案 2026/2 最新營收 | metric_lookup | 1 | no | 結論：2026-02 事業群 3通路方案 的營收為 7,539,188,847。 |
| 顯示 1網通+技鋼 2026年2月 庫存金額 | metric_lookup | 1 | no | 結論：2026-02 事業群 1網通+技鋼 的庫存金額為 73,298,408,408.75。 |
| 查詢 Server 2026-02 營收 | metric_lookup | 1 | no | 結論：2026-02 產品線 Server 的營收為 24,670,343,477。 |
| 看一下 IOT 2026/2 庫存 QTY | metric_lookup | 1 | no | 結論：2026-02 產品線 IOT 的庫存數量為 851,291。 |
| 畫出 2025年 2 月 各事業群營收圓餅圖 | chart_request | 3 | yes | 結論：已產生 2025-02 各事業群營收圓餅圖（business_group_revenue_pie），可用於前端圖表渲染與表格檢視。 |
| 畫出 2026年2月 各產品線庫存長條圖 | chart_request | 3 | yes | 結論：已產生 2026-02 各產品線庫存金額長條圖（product_line_inventory_bar），可用於前端圖表渲染與表格檢視。 |
| 列出2025年3月各產品線庫存資料 | entity_month_table_lookup | 1 | yes | 結論：已列出 2025-03 各產品線庫存金額資料，共 10 筆；庫存金額最高的是 Server。 |
| 比較2025年3月各產品線庫存資料 | cross_section_compare | 1 | yes | 結論：2025-03 各產品線庫存金額比較下，庫存金額最高的是 Server，最低的是 IOT。 |
| 比較2025年3月各事業群庫存資料 | cross_section_compare | 1 | yes | 結論：2025-03 各事業群庫存金額比較下，庫存金額最高的是 1網通+技鋼，最低的是 6雲城。 |
| 比較2025年3月各事業群營收資料 | cross_section_compare | 1 | yes | 結論：2025-03 各事業群營收比較下，營收最高的是 3通路方案，最低的是 6雲城。 |
| 顯示2025/3各BU營收資料 | entity_month_table_lookup | 1 | yes | 結論：已列出 2025-03 各事業群營收資料，共 7 筆；營收最高的是 3通路方案。 |
| 查詢2025-03各產品線庫存QTY | entity_month_table_lookup | 1 | yes | 結論：已列出 2025-03 各產品線庫存數量資料，共 10 筆；庫存數量最高的是 顯卡。 |
| 看一下2025年3月各事業群資料 | entity_month_table_lookup | 1 | yes | 結論：已列出 2025-03 各事業群營收資料，共 7 筆；營收最高的是 3通路方案。 |
| 列出 2025/02 與 2025/03 產品線的庫存 | entity_period_pair_table_lookup | 1 | yes | 結論：已列出 2025-02 與 2025-03 各產品線庫存金額資料，共 10 筆；2025-03 最高的是 Server。 |
| 顯示 2025年2月和2025年3月各事業群營收 | entity_period_pair_table_lookup | 1 | yes | 結論：已列出 2025-02 與 2025-03 各事業群營收資料，共 7 筆；2025-03 最高的是 3通路方案。 |
| 列出 2025/01 到 2025/03 各產品線庫存 | entity_multi_month_table_lookup | 1 | yes | 結論：已列出 2025-01 至 2025-03 各產品線庫存金額資料，共 30 筆。 |
| 比較 Server 2025/02 和 2025/03 庫存 | entity_period_pair_metric_lookup | 1 | yes | 結論：Server 2025-03 庫存金額相較 2025-02 增加 6,738,471,043.99。 |
| 畫出 2025/02 與 2025/03 各產品線庫存比較圖 | chart_request | 3 | yes | 結論：已產生 2025-02 與 2025-03 各產品線庫存金額比較圖（entity_period_pair_table_chart），可用於前端圖表渲染與表格檢視。 |
| 比較 2025/02 與 2025/03 各產品線庫存資料 | entity_period_pair_table_lookup | 1 | yes | 結論：已列出 2025-02 與 2025-03 各產品線庫存金額資料，共 10 筆；2025-03 最高的是 Server。 |
| 顯示 2025-02 vs 2025-03 各BU庫存資料 | entity_period_pair_table_lookup | 1 | yes | 結論：已列出 2025-02 與 2025-03 各事業群庫存金額資料，共 8 筆；2025-03 最高的是 1網通+技鋼。 |
| 顯示 2025Q1 各事業群營收 | entity_multi_month_table_lookup | 1 | yes | 結論：已列出 2025-01 至 2025-03 各事業群營收資料，共 21 筆。 |
| 列出 3通路方案 2025/02 與 2025/03 營收 | entity_period_pair_metric_lookup | 1 | yes | 結論：3通路方案 2025-03 營收相較 2025-02 增加 2,882,781,571。 |
| 列出 2025年3月 3通路方案底下各產品線庫存 | entity_month_table_lookup | 1 | yes | 結論：已列出 2025-03 各產品線庫存金額資料，共 5 筆；庫存金額最高的是 顯卡。 |
| 比較 2025/02 與 2025/03 3通路方案底下各產品線營收 | entity_period_pair_table_lookup | 1 | yes | 結論：已列出 2025-02 與 2025-03 各產品線營收資料，共 6 筆；2025-03 最高的是 顯卡。 |
| 畫出 2025/02 與 2025/03 各產品線庫存比較圖 | chart_request | 3 | yes | 結論：已產生 2025-02 與 2025-03 各產品線庫存金額比較圖（entity_period_pair_table_chart），可用於前端圖表渲染與表格檢視。 |
| 畫 2025Q1 各事業群營收趨勢圖 | chart_request | 3 | yes | 結論：已產生 2025-01 至 2025-03 各事業群營收趨勢圖（entity_multi_month_table_line），可用於前端圖表渲染與表格檢視。 |
| 畫 3通路方案 2025/02 到 2025/06 營收折線圖 | chart_request | 3 | yes | 結論：已產生 3通路方案 2025-02 至 2025-06 營收折線圖（entity_time_series_line），可用於前端圖表渲染與表格檢視。 |
| 畫 2025年3月 3通路方案底下各產品線庫存長條圖 | chart_request | 3 | yes | 結論：已產生 2025-03 3通路方案 底下各產品線庫存金額長條圖（entity_month_table_bar），可用於前端圖表渲染與表格檢視。 |
| 列出 2025年3月各產品線資料 | entity_month_table_lookup | 1 | yes | 結論：已列出 2025-03 各產品線營收資料，共 10 筆；營收最高的是 顯卡。 |
| 比較 2025年3月各事業群資料 | cross_section_compare | 2 | yes | 結論：2025-03 各事業群比較下，3通路方案 營收規模較高，1網通+技鋼 庫存水位較高；但 1網通+技鋼 的營收相對庫存效率較弱，需搭配庫存壓力判讀。 |
| 列出 2025年3月產品線庫存 | entity_month_table_lookup | 1 | yes | 結論：已列出 2025-03 各產品線庫存金額資料，共 10 筆；庫存金額最高的是 Server。 |
| 比較 2025年3月事業群營收 | cross_section_compare | 1 | yes | 結論：2025-03 各事業群營收比較下，營收最高的是 3通路方案，最低的是 6雲城。 |

## Details

### 總體營收趨勢如何？

- task_family: `overall_trend_analysis`
- primary_tools: `get_overall_time_series`
- tools_used: `get_overall_time_series`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：整體營收在 2025-01 至 2026-02 期間呈現上升，最新月份 2026-02 為 32,877,963,113。

### 整體庫存各月變化？

- task_family: `overall_trend_analysis`
- primary_tools: `get_overall_time_series`
- tools_used: `get_overall_time_series`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：整體庫存金額在 2025-01 至 2026-02 期間呈現上升，最新月份 2026-02 為 102,271,212,123.05。

### 請整理最新月份各新事業群的營收與庫存重點

- task_family: `latest_month_entity_summary`
- primary_tools: `get_entity_performance_snapshot`
- tools_used: `get_entity_performance_snapshot, get_entity_cross_section_comparison, get_inventory_turnover_proxy`
- key_observation_count: `3`
- has_table: `True`
- limitations: 此為營收與庫存資料推導的 proxy，非正式周轉指標。 | health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。

### 哪個新事業群營收最高？

- task_family: `entity_ranking`
- primary_tools: `get_entity_metric_ranking`
- tools_used: `get_entity_metric_ranking, get_entity_performance_snapshot`
- key_observation_count: `1`
- has_table: `True`
- limitations: health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：最新月份 2026-02 營收最高的事業群是 1網通+技鋼，營收為 24,670,343,477。

### 哪個新事業群營收相對庫存效率最低？

- task_family: `entity_ranking`
- primary_tools: `get_entity_metric_ranking`
- tools_used: `get_entity_metric_ranking, get_entity_performance_snapshot, get_platform_ratios`
- key_observation_count: `1`
- has_table: `True`
- limitations: health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：最新月份 2026-02 營收相對庫存效率 proxy最低的事業群是 7製造，營收相對庫存效率 proxy為 -5.20。

### 各新事業群近 6 個月營收趨勢

- task_family: `entity_trend_comparison`
- primary_tools: `get_entity_trend_comparison`
- tools_used: `get_entity_trend_comparison`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：近月營收成長較明顯的事業群是 1網通+技鋼，變化率為 0.59。

### 比較最新月份各五大產品線營收與庫存

- task_family: `cross_section_compare`
- primary_tools: `get_entity_cross_section_comparison, get_entity_performance_snapshot`
- tools_used: `get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies`
- key_observation_count: `3`
- has_table: `True`
- limitations: health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。
- headline: 結論：2026-02 各產品線比較下，Server 營收規模較高，Server 庫存水位較高；但 筆電 的營收相對庫存效率較弱，需搭配庫存壓力判讀。

### 哪個產品線庫存壓力較高？

- task_family: `performance_assessment`
- primary_tools: `get_entity_performance_snapshot`
- tools_used: `get_entity_performance_snapshot, get_inventory_turnover_proxy, get_entity_cross_section_comparison, get_anomalies`
- key_observation_count: `3`
- has_table: `False`
- limitations: 目前回答仍以營收、庫存與異常訊號為主，不能直接等同完整因果判斷。 | 此為營收與庫存資料推導的 proxy，非正式周轉指標。 | health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。
- headline: 結論：目前表現較弱的產品線優先看 Other，因為其 存在 revenue_only 或 inventory_only grain；產品線營收較前期下降，health_score 為 0.10。

### Server 產品線各月營收

- task_family: `entity_time_series`
- primary_tools: `get_entity_time_series`
- tools_used: `get_entity_time_series`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：Server各月營收在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 24,670,343,477。

### 比較 3通路方案 各月營收

- task_family: `entity_time_series`
- primary_tools: `get_entity_time_series`
- tools_used: `get_entity_time_series`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：3通路方案各月營收在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 7,539,188,847。

### 1網通+技鋼 各月庫存變化

- task_family: `entity_time_series`
- primary_tools: `get_entity_time_series`
- tools_used: `get_entity_time_series`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：1網通+技鋼各月庫存金額在 2025-01 至 2026-02 期間呈現上升；最新月份 2026-02 為 73,298,408,408.75。

### 比較 2025 年 12 月與 2026 年 1 月營收差別

- task_family: `period_pair_compare`
- primary_tools: `get_entity_period_pair_comparison`
- tools_used: `get_entity_period_pair_comparison(revenue)`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2026-01 營收相較 2025-12 增加 2,812,340,673.00，變化率為 9.28%。

### 2026 年 1 月比 2025 年 1 月營收差多少？

- task_family: `period_pair_compare`
- primary_tools: `get_entity_period_pair_comparison`
- tools_used: `get_entity_period_pair_comparison(revenue)`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2026-01 營收相較 2025-01 增加 12,026,989,797.00，變化率為 57.02%。

### 2026-01 比 2025-12 成長主要來自哪個新事業群？

- task_family: `contribution_analysis`
- primary_tools: `get_entity_contribution_analysis`
- tools_used: `get_entity_contribution_analysis`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：2026-01 相較 2025-12 的營收變化主要由 3通路方案 貢獻，變化為 4,280,740,458.00。

### 有沒有營收下降但庫存上升的新事業群？

- task_family: `metric_relationship_analysis`
- primary_tools: `get_revenue_inventory_relationship`
- tools_used: `get_revenue_inventory_relationship, get_entity_performance_snapshot`
- key_observation_count: `2`
- has_table: `True`
- limitations: 這類問題目前只能用營收與庫存的風險訊號訊號回答，不能直接判定根本原因。 | 這是根據目前營收與庫存資料偵測出的風險訊號，尚不能直接代表根本原因。 | health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。
- headline: 結論：目前可觀察到事業群存在營收與庫存背離訊號，例如 revenue_up_inventory_up。

### 哪些產品線營收相對庫存效率變差？

- task_family: `metric_relationship_analysis`
- primary_tools: `get_revenue_inventory_relationship`
- tools_used: `get_revenue_inventory_relationship, get_entity_performance_snapshot`
- key_observation_count: `2`
- has_table: `True`
- limitations: health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。
- headline: 結論：目前可觀察到產品線存在營收與庫存背離訊號，例如 ratio_worsening。

### 3通路方案底下哪個產品線表現較差？

- task_family: `parent_child_drilldown`
- primary_tools: `get_entity_performance_snapshot`
- tools_used: `get_entity_performance_snapshot, get_inventory_turnover_proxy`
- key_observation_count: `3`
- has_table: `True`
- limitations: 此為營收與庫存資料推導的 proxy，非正式周轉指標。 | health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。
- headline: 結論：在 3通路方案 底下，專案電腦 產品線表現較弱 / 庫存壓力較高。

### 1網通+技鋼底下產品線庫存壓力最高的是誰？

- task_family: `parent_child_drilldown`
- primary_tools: `get_entity_performance_snapshot`
- tools_used: `get_entity_performance_snapshot, get_inventory_turnover_proxy`
- key_observation_count: `2`
- has_table: `True`
- limitations: 此為營收與庫存資料推導的 proxy，非正式周轉指標。 | health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。
- headline: 結論：在 1網通+技鋼 底下，Other 產品線表現較弱 / 庫存壓力較高。

### 畫總體營收趨勢

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 總體營收趨勢（overall_revenue_trend_line），可用於前端圖表渲染與表格檢視。

### 畫各新事業群營收排名

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 2026-02 各事業群營收長條圖（business_group_revenue_bar），可用於前端圖表渲染與表格檢視。

### 畫各產品線 health_score 排名

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。
- headline: 結論：已產生 產品線 health_score 排名（product_line_health_score_bar），可用於前端圖表渲染與表格檢視。

### 畫 3通路方案各月營收趨勢

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 3通路方案 各月營收趨勢（entity_time_series_line），可用於前端圖表渲染與表格檢視。

### 畫營收與庫存關係圖

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。
- headline: 結論：已產生 事業群營收/庫存金額 proxy 排名（business_group_revenue_inventory_ratio_bar），可用於前端圖表渲染與表格檢視。

### 下個月營收會不會改善？

- task_family: `forecast_unsupported`
- primary_tools: ``
- tools_used: ``
- key_observation_count: `2`
- has_table: `False`
- limitations: 目前資料無法直接支援 forecast 類問題。 | 目前系統尚未納入預測模型、訂單、出貨、價格或市場需求資料，不能直接預測未來月份。 | 目前尚無法直接判斷原因或預測未來變化，因為資料不包含完整因果所需欄位。
- headline: 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。

### 未來哪個事業群會成長？

- task_family: `forecast_unsupported`
- primary_tools: ``
- tools_used: ``
- key_observation_count: `2`
- has_table: `False`
- limitations: 目前資料無法直接支援 forecast 類問題。 | 目前系統尚未納入預測模型、訂單、出貨、價格或市場需求資料，不能直接預測未來月份。
- headline: 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。

### 請整理最新月份各事業群的營收與庫存重點

- task_family: `latest_month_entity_summary`
- primary_tools: `get_entity_performance_snapshot`
- tools_used: `get_entity_performance_snapshot, get_entity_cross_section_comparison, get_inventory_turnover_proxy`
- key_observation_count: `3`
- has_table: `True`
- limitations: 此為營收與庫存資料推導的 proxy，非正式周轉指標。 | health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。

### 請整理最新月份各新事業群的營收與庫存重點

- task_family: `latest_month_entity_summary`
- primary_tools: `get_entity_performance_snapshot`
- tools_used: `get_entity_performance_snapshot, get_entity_cross_section_comparison, get_inventory_turnover_proxy`
- key_observation_count: `3`
- has_table: `True`
- limitations: 此為營收與庫存資料推導的 proxy，非正式周轉指標。 | health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。

### 請整理最新月份各 BU 營收與庫存重點

- task_family: `latest_month_entity_summary`
- primary_tools: `get_entity_performance_snapshot`
- tools_used: `get_entity_performance_snapshot, get_entity_cross_section_comparison, get_inventory_turnover_proxy`
- key_observation_count: `3`
- has_table: `True`
- limitations: 此為營收與庫存資料推導的 proxy，非正式周轉指標。 | health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：最新月份 2026-02 各事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。

### 列出通路方案 2026/2 最新營收

- task_family: `metric_lookup`
- primary_tools: `get_entity_metric_value`
- tools_used: `get_entity_metric_value`
- key_observation_count: `1`
- has_table: `False`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2026-02 事業群 3通路方案 的營收為 7,539,188,847。

### 顯示 1網通+技鋼 2026年2月 庫存金額

- task_family: `metric_lookup`
- primary_tools: `get_entity_metric_value`
- tools_used: `get_entity_metric_value`
- key_observation_count: `1`
- has_table: `False`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2026-02 事業群 1網通+技鋼 的庫存金額為 73,298,408,408.75。

### 查詢 Server 2026-02 營收

- task_family: `metric_lookup`
- primary_tools: `get_entity_metric_value`
- tools_used: `get_entity_metric_value`
- key_observation_count: `1`
- has_table: `False`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2026-02 產品線 Server 的營收為 24,670,343,477。

### 看一下 IOT 2026/2 庫存 QTY

- task_family: `metric_lookup`
- primary_tools: `get_entity_metric_value`
- tools_used: `get_entity_metric_value`
- key_observation_count: `1`
- has_table: `False`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2026-02 產品線 IOT 的庫存數量為 851,291。

### 畫出 2025年 2 月 各事業群營收圓餅圖

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 2025-02 各事業群營收圓餅圖（business_group_revenue_pie），可用於前端圖表渲染與表格檢視。

### 畫出 2026年2月 各產品線庫存長條圖

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 2026-02 各產品線庫存金額長條圖（product_line_inventory_bar），可用於前端圖表渲染與表格檢視。

### 列出2025年3月各產品線庫存資料

- task_family: `entity_month_table_lookup`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-03 各產品線庫存金額資料，共 10 筆；庫存金額最高的是 Server。

### 比較2025年3月各產品線庫存資料

- task_family: `cross_section_compare`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2025-03 各產品線庫存金額比較下，庫存金額最高的是 Server，最低的是 IOT。

### 比較2025年3月各事業群庫存資料

- task_family: `cross_section_compare`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：2025-03 各事業群庫存金額比較下，庫存金額最高的是 1網通+技鋼，最低的是 6雲城。

### 比較2025年3月各事業群營收資料

- task_family: `cross_section_compare`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2025-03 各事業群營收比較下，營收最高的是 3通路方案，最低的是 6雲城。

### 顯示2025/3各BU營收資料

- task_family: `entity_month_table_lookup`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-03 各事業群營收資料，共 7 筆；營收最高的是 3通路方案。

### 查詢2025-03各產品線庫存QTY

- task_family: `entity_month_table_lookup`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-03 各產品線庫存數量資料，共 10 筆；庫存數量最高的是 顯卡。

### 看一下2025年3月各事業群資料

- task_family: `entity_month_table_lookup`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-03 各事業群營收資料，共 7 筆；營收最高的是 3通路方案。

### 列出 2025/02 與 2025/03 產品線的庫存

- task_family: `entity_period_pair_table_lookup`
- primary_tools: `get_entity_period_pair_table`
- tools_used: `get_entity_period_pair_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-02 與 2025-03 各產品線庫存金額資料，共 10 筆；2025-03 最高的是 Server。

### 顯示 2025年2月和2025年3月各事業群營收

- task_family: `entity_period_pair_table_lookup`
- primary_tools: `get_entity_period_pair_table`
- tools_used: `get_entity_period_pair_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-02 與 2025-03 各事業群營收資料，共 7 筆；2025-03 最高的是 3通路方案。

### 列出 2025/01 到 2025/03 各產品線庫存

- task_family: `entity_multi_month_table_lookup`
- primary_tools: `get_entity_multi_month_table`
- tools_used: `get_entity_multi_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-01 至 2025-03 各產品線庫存金額資料，共 30 筆。

### 比較 Server 2025/02 和 2025/03 庫存

- task_family: `entity_period_pair_metric_lookup`
- primary_tools: `get_entity_period_pair_value`
- tools_used: `get_entity_period_pair_value`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：Server 2025-03 庫存金額相較 2025-02 增加 6,738,471,043.99。

### 畫出 2025/02 與 2025/03 各產品線庫存比較圖

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table, get_entity_period_pair_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 2025-02 與 2025-03 各產品線庫存金額比較圖（entity_period_pair_table_chart），可用於前端圖表渲染與表格檢視。

### 比較 2025/02 與 2025/03 各產品線庫存資料

- task_family: `entity_period_pair_table_lookup`
- primary_tools: `get_entity_period_pair_table`
- tools_used: `get_entity_period_pair_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-02 與 2025-03 各產品線庫存金額資料，共 10 筆；2025-03 最高的是 Server。

### 顯示 2025-02 vs 2025-03 各BU庫存資料

- task_family: `entity_period_pair_table_lookup`
- primary_tools: `get_entity_period_pair_table`
- tools_used: `get_entity_period_pair_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：已列出 2025-02 與 2025-03 各事業群庫存金額資料，共 8 筆；2025-03 最高的是 1網通+技鋼。

### 顯示 2025Q1 各事業群營收

- task_family: `entity_multi_month_table_lookup`
- primary_tools: `get_entity_multi_month_table`
- tools_used: `get_entity_multi_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-01 至 2025-03 各事業群營收資料，共 21 筆。

### 列出 3通路方案 2025/02 與 2025/03 營收

- task_family: `entity_period_pair_metric_lookup`
- primary_tools: `get_entity_period_pair_value`
- tools_used: `get_entity_period_pair_value`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：3通路方案 2025-03 營收相較 2025-02 增加 2,882,781,571。

### 列出 2025年3月 3通路方案底下各產品線庫存

- task_family: `entity_month_table_lookup`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-03 各產品線庫存金額資料，共 5 筆；庫存金額最高的是 顯卡。

### 比較 2025/02 與 2025/03 3通路方案底下各產品線營收

- task_family: `entity_period_pair_table_lookup`
- primary_tools: `get_entity_period_pair_table`
- tools_used: `get_entity_period_pair_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-02 與 2025-03 各產品線營收資料，共 6 筆；2025-03 最高的是 顯卡。

### 畫出 2025/02 與 2025/03 各產品線庫存比較圖

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table, get_entity_period_pair_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 2025-02 與 2025-03 各產品線庫存金額比較圖（entity_period_pair_table_chart），可用於前端圖表渲染與表格檢視。

### 畫 2025Q1 各事業群營收趨勢圖

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table, get_entity_multi_month_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 2025-01 至 2025-03 各事業群營收趨勢圖（entity_multi_month_table_line），可用於前端圖表渲染與表格檢視。

### 畫 3通路方案 2025/02 到 2025/06 營收折線圖

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table, get_entity_time_series`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 3通路方案 2025-02 至 2025-06 營收折線圖（entity_time_series_line），可用於前端圖表渲染與表格檢視。

### 畫 2025年3月 3通路方案底下各產品線庫存長條圖

- task_family: `chart_request`
- primary_tools: `get_chart_payload`
- tools_used: `get_chart_payload, get_chart_table, get_entity_month_table`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已產生 2025-03 3通路方案 底下各產品線庫存金額長條圖（entity_month_table_bar），可用於前端圖表渲染與表格檢視。

### 列出 2025年3月各產品線資料

- task_family: `entity_month_table_lookup`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-03 各產品線營收資料，共 10 筆；營收最高的是 顯卡。

### 比較 2025年3月各事業群資料

- task_family: `cross_section_compare`
- primary_tools: `get_entity_cross_section_comparison, get_entity_performance_snapshot`
- tools_used: `get_entity_cross_section_comparison, get_entity_performance_snapshot, get_anomalies`
- key_observation_count: `2`
- has_table: `True`
- limitations: 目前沒有符合條件的異常偵測結果。 | health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。 | 部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。
- headline: 結論：2025-03 各事業群比較下，3通路方案 營收規模較高，1網通+技鋼 庫存水位較高；但 1網通+技鋼 的營收相對庫存效率較弱，需搭配庫存壓力判讀。

### 列出 2025年3月產品線庫存

- task_family: `entity_month_table_lookup`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：已列出 2025-03 各產品線庫存金額資料，共 10 筆；庫存金額最高的是 Server。

### 比較 2025年3月事業群營收

- task_family: `cross_section_compare`
- primary_tools: `get_entity_month_table`
- tools_used: `get_entity_month_table`
- key_observation_count: `1`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2025-03 各事業群營收比較下，營收最高的是 3通路方案，最低的是 6雲城。
