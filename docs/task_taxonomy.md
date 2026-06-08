# Task Taxonomy

本文件定義 real-data entity dashboard 在 Phase 10C 的 canonical `task_family`。  
原則：

- deterministic parser 是 source of truth
- LLM planner / rewriter 不可改寫日期、entity、metric、task family
- LLM 不可算數字、forecast、root cause claim
- 若 planner / rewriter validation 失敗，必須 fallback deterministic

## Entity Label And Synonym Policy

- Internal canonical dimensions: `business_group`, `product_line_5`, `month`, `overall`
- Display labels: `business_group` -> `事業群`; `product_line_5` -> `產品線`; `month` -> `月份`; `overall` -> `總體`
- Synonyms normalized to `business_group`: `事業群`, `新事業群`, `BU`, `bu`, `Business Unit`, `business unit`, legacy `平台`
- Synonyms normalized to `product_line_5`: `產品線`, `五大產品線`, `product line`, `Product Line`
- Raw Excel column names may remain `新事業群` / `五大產品線`, but UI, answers, charts, and executive-visible table labels must use `事業群` / `產品線`.

## Common Policies

- `target_entity`
  - `overall`
  - `business_group` (`事業群`)
  - `product_line_5` (`產品線`)
  - `product_line_5 + parent_entity.business_group`
- `time_scope`
  - `latest_month`
  - `single_month`
  - `period_pair`
  - `multi_month_series`
  - `recent_n_months`
  - `year_over_year`
  - `future_period`
- canonical metrics
  - `revenue_amount`
  - `inventory_amount`
  - `inventory_qty`
  - `revenue_inventory_amount_ratio`
  - `health_score`
  - `risk_score`

## 1. `metric_lookup`

- Example: `2026 年 1 月營收是多少？`
- target_entity: explicit entity if named, otherwise `overall`
- time_scope: single month or latest month
- required metrics: exactly one requested metric
- allowed tools: `get_metric_table`
- forbidden tools: `get_root_cause_candidates`, `get_entity_contribution_analysis`, forecast tools
- display_blocks headline policy: direct factual lookup, no trend/contribution wording
- table policy: optional, only when lookup rows improve clarity
- limitations policy: keep data coverage / proxy wording when relevant

## 2. `entity_ranking`

- Example: `哪個新事業群營收最高？`
- target_entity: `business_group` or `product_line_5`
- time_scope: latest month or explicit single month
- required metrics: exactly one ranking metric
- allowed tools: `get_entity_metric_ranking`, `get_entity_performance_snapshot`
- forbidden tools: `get_top_groups`, `get_platform_ranking`, trend tools as primary
- display_blocks headline policy: must name winning entity, metric, and month
- table policy: required; include rank rows
- limitations policy: preserve proxy / unmapped-row wording

## 3. `latest_month_entity_summary`

- Example: `請整理最新月份各新事業群的營收與庫存重點`
- target_entity: peer entities under `business_group` or `product_line_5`
- time_scope: `latest_month`
- required metrics: `revenue_amount`, `inventory_amount`, `inventory_qty`, `revenue_inventory_amount_ratio`, `health_score`, `risk_score`
- allowed tools: `get_entity_performance_snapshot`, `get_entity_cross_section_comparison`
- forbidden tools: contribution / root-cause tools as primary
- display_blocks headline policy: latest-month conclusion with entity wording only
- table policy: required scorecard table
- limitations policy: must retain proxy and data-quality caveats

## 4. `cross_section_compare`

- Example: `比較最新月份各五大產品線營收與庫存`
- target_entity: peer entities under `business_group` or `product_line_5`
- time_scope: latest month or explicit single month
- required metrics: revenue + inventory family metrics
- allowed tools: `get_entity_cross_section_comparison`, `get_entity_performance_snapshot`
- forbidden tools: contribution as primary, forecast tools
- display_blocks headline policy: compare same-month peers, not trend
- table policy: required
- limitations policy: keep proxy / mapping limitations

## 5. `period_pair_compare`

- Example: `比較 2025 年 12 月與 2026 年 1 月營收差別`
- target_entity: `overall`, `business_group`, or `product_line_5` peer scope depending on question
- time_scope: explicit `period_pair`
- required metrics: exactly one requested metric
- allowed tools: `get_entity_period_pair_comparison`, `get_period_pair_metric_comparison` if later added
- forbidden tools: generic trend tools, forecast tools
- display_blocks headline policy: preserve `period_a` and `period_b` exactly
- table policy: required; include period pair values and change
- limitations policy: descriptive difference only, no root cause

## 6. `entity_time_series`

- Example: `比較 3通路方案 各月營收`
- target_entity: named `business_group` or named `product_line_5`
- time_scope: `multi_month_series`, `recent_n_months`, or explicit range
- required metrics: exactly one requested metric
- allowed tools: `get_entity_time_series`
- forbidden tools: generic trend substitution, contribution tools, forecast tools
- display_blocks headline policy: must preserve named entity and series range
- table policy: required monthly rows
- limitations policy: historical description only; proxy wording for ratio metrics

## 7. `overall_trend_analysis`

- Example: `總體營收趨勢如何？`
- target_entity: `overall`
- time_scope: `multi_month_series`, `recent_n_months`, or explicit range
- required metrics: exactly one requested metric
- allowed tools: `get_overall_time_series`
- forbidden tools: period-pair tools as primary, contribution tools as primary
- display_blocks headline policy: `整體{metric}` trend summary with latest month
- table policy: required monthly series table
- limitations policy: historical description only

## 8. `entity_trend_comparison`

- Example: `各新事業群近 6 個月營收趨勢`
- target_entity: peer `business_group` or peer `product_line_5`
- time_scope: `recent_n_months` or `multi_month_series`
- required metrics: exactly one requested metric
- allowed tools: `get_entity_trend_comparison`
- forbidden tools: entity_time_series replacement, generic trend downgrade
- display_blocks headline policy: identify strongest growth / clearest change entity with exact window
- table policy: required
- limitations policy: historical description only

## 9. `performance_assessment`

- Example: `哪個產品線庫存壓力較高？`
- target_entity: `business_group` or `product_line_5`
- time_scope: latest month or explicit single month
- required metrics: `health_score`, `risk_score`, performance context metrics
- allowed tools: `get_entity_performance_snapshot`, `get_inventory_turnover_proxy`
- forbidden tools: raw inventory ranking as sole primary evidence
- display_blocks headline policy: conclusion-first, proxy-aware, no raw ranking-only claim
- table policy: optional
- limitations policy: must state scorecard/proxy caveat

## 10. `risk_scan`

- Example: `最近有什麼營運風險？`
- target_entity: usually peer entities
- time_scope: latest month or explicit single month
- required metrics: `risk_score` and supporting revenue/inventory context
- allowed tools: `get_revenue_inventory_relationship`, `get_anomalies`, `get_inventory_turnover_proxy`
- forbidden tools: root-cause confirmation, forecast tools
- display_blocks headline policy: risk signal summary, not diagnosis
- table policy: optional but recommended
- limitations policy: keep proxy / non-causal wording

## 11. `metric_relationship_analysis`

- Example: `有沒有營收下降但庫存上升的新事業群？`
- target_entity: peer `business_group` or peer `product_line_5`
- time_scope: latest month or explicit month pair context
- required metrics: `revenue_amount`, `inventory_amount`, `revenue_inventory_amount_ratio`
- allowed tools: `get_revenue_inventory_relationship`, `get_entity_performance_snapshot`
- forbidden tools: root-cause tools, forecast tools
- display_blocks headline policy: relationship label summary such as `revenue_down_inventory_up`
- table policy: required
- limitations policy: must state relationship labels are descriptive and ratio is proxy

## 12. `contribution_analysis`

- Example: `2026-01 比 2025-12 成長主要來自哪個新事業群？`
- target_entity: peer `business_group` or peer `product_line_5`
- time_scope: explicit `period_pair`
- required metrics: exactly one requested metric
- allowed tools: `get_entity_contribution_analysis`
- forbidden tools: generic trend substitution, root-cause tools
- display_blocks headline policy: preserve both months and top contributor exactly
- table policy: required
- limitations policy: descriptive contribution only, no causal claim

## 13. `parent_child_drilldown`

- Example: `3通路方案底下哪個產品線表現較差？`
- target_entity: `product_line_5`
- time_scope: latest month or explicit single month
- required metrics: scorecard metrics plus requested operational metric
- allowed tools: `get_entity_performance_snapshot` with `parent_filter`
- forbidden tools: losing parent filter, contribution tools as primary
- display_blocks headline policy: must preserve parent entity wording
- table policy: required
- limitations policy: retain parent-filter scope and proxy caveats

## 14. `data_quality`

- Example: `目前資料涵蓋哪些月份？`
- target_entity: none / overall
- time_scope: data coverage scope
- required metrics: none
- allowed tools: `get_data_coverage`, `get_mapping_summary`
- forbidden tools: ranking / trend / forecast tools
- display_blocks headline policy: coverage summary only
- table policy: optional
- limitations policy: must preserve coverage gaps and warnings

## 15. `chart_request`

- Example: `畫總體營收趨勢`
- target_entity: inferred from question and preserved in filters
- time_scope: preserved if explicit
- required metrics: aligned with requested chart metric
- allowed tools: `get_chart_payload`, `get_chart_table`
- forbidden tools: analysis tools as substitutes for chart payload
- display_blocks headline policy: chart title + chart key; preserve named entity if filtered
- table policy: optional preview table
- limitations policy: keep chart availability / filter scope wording

## 16. `forecast_unsupported`

- Example: `下個月營收會不會改善？`
- target_entity: preserve user scope if present
- time_scope: `future_period`
- required metrics: requested metric only for unsupported explanation
- allowed tools: none in final answer; planner may only use safety tools during validation path
- forbidden tools: all forecast / trend / ranking / contribution execution tools
- display_blocks headline policy: unsupported conclusion only
- table policy: no table
- limitations policy: must explicitly say no forecast model / no future answer

## 17. `unsupported`

- Example: `幫我判定根本原因並預測明年需求`
- target_entity: preserve explicit scope if parseable
- time_scope: preserve explicit scope if parseable
- required metrics: only referenced for unsupported explanation
- allowed tools: none or safety-only coverage helpers
- forbidden tools: unsupported execution paths
- display_blocks headline policy: clear unsupported statement
- table policy: no table
- limitations policy: explain unsupported reason without inventing analysis
