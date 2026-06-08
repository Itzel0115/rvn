# Query Coverage Matrix

Phase 10F coverage status for temporal entity queries. Status is conservative: `supported` means parser, deterministic tool plan, PlanValidator, and display projection have regression coverage; `partially supported` means parser/tool path is safe but not every action/entity/metric combination has a specialized visualization; `unsupported` means the assistant must state a limitation instead of falling back to latest months or another metric.

| Time scope | Entity scope | Metrics | Actions | Status | Tool used | task_family | Test case |
|---|---|---|---|---|---|---|---|
| latest_month | overall | revenue_amount, inventory_amount, inventory_qty | 顯示/查詢/趨勢 | supported | get_overall_time_series / legacy metric tables | overall_trend_analysis / metric_lookup | 總體營收趨勢如何 |
| latest_month | all business_group | revenue_amount, inventory_amount, inventory_qty, ratio, health_score, risk_score | 列出/比較/排名/畫圖 | supported | get_entity_performance_snapshot, get_entity_metric_ranking, get_chart_payload | latest_month_entity_summary / cross_section_compare / entity_ranking / chart_request | 請整理最新月份各事業群的營收與庫存重點 |
| latest_month | all product_line_5 | revenue_amount, inventory_amount, inventory_qty, ratio, health_score, risk_score | 列出/比較/排名/畫圖 | supported | get_entity_performance_snapshot, get_entity_metric_ranking, get_chart_payload | latest_month_entity_summary / cross_section_compare / entity_ranking / chart_request | 比較最新月份各產品線營收與庫存 |
| single_month | overall | revenue_amount, inventory_amount, inventory_qty | 查詢/趨勢 | partially supported | get_overall_time_series / get_metric_table | overall_trend_analysis / metric_lookup | 2025年3月總體營收 |
| single_month | all business_group | revenue_amount, inventory_amount, inventory_qty | 列出/顯示/查詢/比較 | supported | get_entity_month_table | entity_month_table_lookup / cross_section_compare | 比較2025年3月各事業群庫存資料 |
| single_month | all product_line_5 | revenue_amount, inventory_amount, inventory_qty | 列出/顯示/查詢/比較 | supported | get_entity_month_table | entity_month_table_lookup / cross_section_compare | 列出2025年3月產品線庫存 |
| single_month | single business_group | revenue_amount, inventory_amount, inventory_qty, ratio | 查詢 | supported | get_entity_metric_value | metric_lookup | 2025年3月3通路方案營收 |
| single_month | single product_line_5 | revenue_amount, inventory_amount, inventory_qty, ratio | 查詢 | supported | get_entity_metric_value | metric_lookup | 2025年3月Server庫存 |
| single_month | product_line_5 under business_group | revenue_amount, inventory_amount, inventory_qty | 列出/顯示/查詢/畫圖 | supported | get_entity_month_table(parent_filter) | entity_month_table_lookup / chart_request | 列出 2025年3月 3通路方案底下各產品線庫存 |
| period_pair | overall | revenue_amount, inventory_amount, inventory_qty | 比較 | supported | get_period_pair_metric_comparison | period_pair_compare | 2026年1月以及2026年2月營收有什麼區別 |
| period_pair | all business_group | revenue_amount, inventory_amount, inventory_qty | 列出/顯示/查詢/比較/畫圖 | supported | get_entity_period_pair_table | entity_period_pair_table_lookup / chart_request | 顯示 2025-02 vs 2025-03 各BU庫存資料 |
| period_pair | all product_line_5 | revenue_amount, inventory_amount, inventory_qty | 列出/顯示/查詢/比較/畫圖 | supported | get_entity_period_pair_table | entity_period_pair_table_lookup / chart_request | 列出 2025/02 與 2025/03 產品線的庫存 |
| period_pair | single business_group | revenue_amount, inventory_amount, inventory_qty, ratio | 列出/比較 | supported | get_entity_period_pair_value | entity_period_pair_metric_lookup | 列出 3通路方案 2025/02 與 2025/03 營收 |
| period_pair | single product_line_5 | revenue_amount, inventory_amount, inventory_qty, ratio | 列出/比較 | supported | get_entity_period_pair_value | entity_period_pair_metric_lookup | 比較 Server 2025/02 和 2025/03 庫存 |
| period_pair | product_line_5 under business_group | revenue_amount, inventory_amount, inventory_qty | 列出/比較/畫圖 | supported | get_entity_period_pair_table(parent_filter) | entity_period_pair_table_lookup / chart_request | 比較 2025/02 與 2025/03 3通路方案底下各產品線營收 |
| date_range / multi_month | overall | revenue_amount, inventory_amount, inventory_qty | 趨勢/各月/每月/畫圖 | supported | get_overall_time_series | overall_trend_analysis / chart_request | 總體2025Q1營收趨勢 |
| date_range / multi_month | all business_group | revenue_amount, inventory_amount, inventory_qty | 列出/顯示/查詢/趨勢/畫圖 | supported | get_entity_multi_month_table / get_entity_trend_comparison | entity_multi_month_table_lookup / entity_trend_comparison / chart_request | 顯示 2025Q1 各事業群營收 |
| date_range / multi_month | all product_line_5 | revenue_amount, inventory_amount, inventory_qty | 列出/顯示/查詢/趨勢/畫圖 | supported | get_entity_multi_month_table / get_entity_trend_comparison | entity_multi_month_table_lookup / entity_trend_comparison / chart_request | 列出 2025/01 到 2025/03 各產品線庫存 |
| date_range / multi_month | single business_group | revenue_amount, inventory_amount, inventory_qty, ratio | 趨勢/各月/畫圖 | supported | get_entity_time_series | entity_time_series / chart_request | 畫 3通路方案 2025/02 到 2025/06 營收折線圖 |
| date_range / multi_month | single product_line_5 | revenue_amount, inventory_amount, inventory_qty, ratio | 趨勢/各月 | supported | get_entity_time_series | entity_time_series | IOT 2025年2月到3月庫存變化 |
| date_range / multi_month | product_line_5 under business_group | revenue_amount, inventory_amount, inventory_qty | 列出/趨勢/畫圖 | supported | get_entity_multi_month_table(parent_filter) | entity_multi_month_table_lookup / chart_request | 3通路方案底下產品線2025Q1營收趨勢 |
| all_available_months | overall | revenue_amount, inventory_amount, inventory_qty | 趨勢/各月/每月 | supported | get_overall_time_series | overall_trend_analysis | 總體營收趨勢如何 |
| all_available_months | all business_group | revenue_amount, inventory_amount, inventory_qty, ratio | 趨勢/各月/每月 | supported | get_entity_trend_comparison | entity_trend_comparison | 各事業群各月營收趨勢 |
| all_available_months | all product_line_5 | revenue_amount, inventory_amount, inventory_qty, ratio | 趨勢/各月/每月 | supported | get_entity_trend_comparison | entity_trend_comparison | 各產品線各月庫存趨勢 |
| any | any | formal inventory turnover | any | unsupported | none | unsupported limitation | 不把 proxy 說成正式庫存週轉率 |
| future | any | any | forecast | unsupported | none | forecast_unsupported | 下個月營收會不會改善 |

Notes:

- No-metric entity data requests default to `revenue_amount + inventory_amount + inventory_qty` for single-month table answers. The table exposes all three columns and the headline states that revenue and inventory data were listed.
- Period-pair entity table queries never fall back to latest months. If either explicit period has no data, the affected value remains empty and limitations explain the gap.
- Parent-child queries preserve `parent_filter={"business_group": ...}` through deterministic planning and PlanValidator.
- Ratio/efficiency remains a proxy from revenue and inventory amount, not a formal inventory turnover metric.
