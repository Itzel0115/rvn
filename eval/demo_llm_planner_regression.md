# Demo LLM Planner Regression

- cases: 60
- passed: 60
- failed: 0
- planner_called_count: 60
- planner_valid_count: 40
- planner_rejected_count: 20
- planner_valid_rate: 66.7%
- fallback_reason_counts: {'Planner changed task_family: overall_trend_analysis != entity_trend_comparison': 1, 'Planner changed task_family: overall_trend_analysis != entity_time_series': 1, 'date_mismatch:period_a': 2, 'Planner changed task_family: overall_trend_analysis != contribution_analysis': 1, 'entity_value_missing': 1, 'chart_type_mismatch': 7, 'entity_value_mismatch': 3, 'date_mismatch:month': 3, 'parent_filter_missing': 1}
- top_rejection_reasons: [('chart_type_mismatch', 7), ('entity_value_mismatch', 3), ('date_mismatch:month', 3), ('date_mismatch:period_a', 2), ('Planner changed task_family: overall_trend_analysis != entity_trend_comparison', 1)]
- mode A: `USE_LLM_PLANNER=false`
- mode B: `USE_LLM_PLANNER=true`, `USE_LLM_REWRITER=false`

| Question | Passed | Planner Valid | Fallback Reason | Mismatches |
|---|---:|---:|---|---|
| 總體營收趨勢如何？ | yes | yes | none | - |
| 整體庫存各月變化？ | yes | yes | none | - |
| 請整理最新月份各新事業群的營收與庫存重點 | yes | yes | none | - |
| 哪個新事業群營收最高？ | yes | yes | none | - |
| 哪個新事業群營收相對庫存效率最低？ | yes | yes | none | - |
| 各新事業群近 6 個月營收趨勢 | yes | no | Planner changed task_family: overall_trend_analysis != entity_trend_comparison | - |
| 比較最新月份各五大產品線營收與庫存 | yes | yes | none | - |
| 哪個產品線庫存壓力較高？ | yes | yes | none | - |
| Server 產品線各月營收 | yes | yes | none | - |
| 比較 3通路方案 各月營收 | yes | no | Planner changed task_family: overall_trend_analysis != entity_time_series | - |
| 1網通+技鋼 各月庫存變化 | yes | yes | none | - |
| 比較 2025 年 12 月與 2026 年 1 月營收差別 | yes | no | date_mismatch:period_a | - |
| 2026 年 1 月比 2025 年 1 月營收差多少？ | yes | no | date_mismatch:period_a | - |
| 2026-01 比 2025-12 成長主要來自哪個新事業群？ | yes | no | Planner changed task_family: overall_trend_analysis != contribution_analysis | - |
| 有沒有營收下降但庫存上升的新事業群？ | yes | yes | none | - |
| 哪些產品線營收相對庫存效率變差？ | yes | no | entity_value_missing | - |
| 3通路方案底下哪個產品線表現較差？ | yes | yes | none | - |
| 1網通+技鋼底下產品線庫存壓力最高的是誰？ | yes | yes | none | - |
| 畫總體營收趨勢 | yes | no | chart_type_mismatch | - |
| 畫各新事業群營收排名 | yes | no | chart_type_mismatch | - |
| 畫各產品線 health_score 排名 | yes | no | chart_type_mismatch | - |
| 畫 3通路方案各月營收趨勢 | yes | no | entity_value_mismatch | - |
| 畫營收與庫存關係圖 | yes | no | chart_type_mismatch | - |
| 下個月營收會不會改善？ | yes | yes | none | - |
| 未來哪個事業群會成長？ | yes | yes | none | - |
| 請整理最新月份各事業群的營收與庫存重點 | yes | yes | none | - |
| 請整理最新月份各新事業群的營收與庫存重點 | yes | yes | none | - |
| 請整理最新月份各 BU 營收與庫存重點 | yes | yes | none | - |
| 列出通路方案 2026/2 最新營收 | yes | no | entity_value_mismatch | - |
| 顯示 1網通+技鋼 2026年2月 庫存金額 | yes | yes | none | - |
| 查詢 Server 2026-02 營收 | yes | yes | none | - |
| 看一下 IOT 2026/2 庫存 QTY | yes | yes | none | - |
| 畫出 2025年 2 月 各事業群營收圓餅圖 | yes | no | chart_type_mismatch | - |
| 畫出 2026年2月 各產品線庫存長條圖 | yes | no | chart_type_mismatch | - |
| 列出2025年3月各產品線庫存資料 | yes | yes | none | - |
| 比較2025年3月各產品線庫存資料 | yes | yes | none | - |
| 比較2025年3月各事業群庫存資料 | yes | yes | none | - |
| 比較2025年3月各事業群營收資料 | yes | yes | none | - |
| 顯示2025/3各BU營收資料 | yes | yes | none | - |
| 查詢2025-03各產品線庫存QTY | yes | yes | none | - |
| 看一下2025年3月各事業群資料 | yes | yes | none | - |
| 列出 2025/02 與 2025/03 產品線的庫存 | yes | yes | none | - |
| 顯示 2025年2月和2025年3月各事業群營收 | yes | yes | none | - |
| 列出 2025/01 到 2025/03 各產品線庫存 | yes | yes | none | - |
| 比較 Server 2025/02 和 2025/03 庫存 | yes | yes | none | - |
| 畫出 2025/02 與 2025/03 各產品線庫存比較圖 | yes | no | date_mismatch:month | - |
| 比較 2025/02 與 2025/03 各產品線庫存資料 | yes | yes | none | - |
| 顯示 2025-02 vs 2025-03 各BU庫存資料 | yes | yes | none | - |
| 顯示 2025Q1 各事業群營收 | yes | yes | none | - |
| 列出 3通路方案 2025/02 與 2025/03 營收 | yes | yes | none | - |
| 列出 2025年3月 3通路方案底下各產品線庫存 | yes | yes | none | - |
| 比較 2025/02 與 2025/03 3通路方案底下各產品線營收 | yes | yes | none | - |
| 畫出 2025/02 與 2025/03 各產品線庫存比較圖 | yes | no | date_mismatch:month | - |
| 畫 2025Q1 各事業群營收趨勢圖 | yes | no | chart_type_mismatch | - |
| 畫 3通路方案 2025/02 到 2025/06 營收折線圖 | yes | no | entity_value_mismatch | - |
| 畫 2025年3月 3通路方案底下各產品線庫存長條圖 | yes | no | parent_filter_missing | - |
| 列出 2025年3月各產品線資料 | yes | yes | none | - |
| 比較 2025年3月各事業群資料 | yes | no | date_mismatch:month | - |
| 列出 2025年3月產品線庫存 | yes | yes | none | - |
| 比較 2025年3月事業群營收 | yes | yes | none | - |