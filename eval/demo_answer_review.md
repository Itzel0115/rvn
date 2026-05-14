# Demo Answer Review

- cases: 22
- passed: 22
- failed: 0
- mode: direct deterministic assistant; LLM planner and rewriter disabled

| # | Question | Task Family | Answer Type | Passed | Failures | Headline |
|---:|---|---|---|---:|---|---|
| 1 | 請整理最新月份各新事業群的營收與庫存重點 | latest_month_entity_summary | latest_month_entity_summary | True | - | 結論：最新月份 2026-02 各新事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。 |
| 2 | 請分析哪個新事業群表現較佳 | performance_assessment | performance_weakness | True | - | 結論：目前綜合表現較佳的新事業群是 1網通+技鋼，因為其 綜合分數來自營收、庫存 proxy 與資料完整性。，health_score 為 0.82。 |
| 3 | 請分析哪個新事業群表現較差 | performance_assessment | performance_weakness | True | - | 結論：目前未對應資料列在新事業群 scorecard 下風險較高，建議先視為資料對應限制；已對應資料則需搭配表格中的 health_score 與 proxy 判讀。 |
| 4 | 比較最新月份各五大產品線營收與庫存 | cross_section_compare | comparison | True | - | 結論：2026-02 各五大產品線比較下，IOT 營收規模較高，Server 庫存水位較高；但 Server 的營收相對庫存效率較弱，需搭配庫存壓力判讀。 |
| 5 | 哪個產品線庫存壓力較高？ | performance_assessment | performance_weakness | True | - | 結論：目前表現較弱的五大產品線優先看 雲城，因為其 存在 revenue_only 或 inventory_only grain；五大產品線營收較前期下降，health_score 為 0.12。 |
| 6 | 請畫最新月份各新事業群營收圖 | chart_request | chart | True | - | 結論：已產生 最新月份各新事業群營收比較（business_group_revenue_bar），可用於前端圖表渲染與表格檢視。 |
| 7 | 請畫五大產品線 health_score 排名 | chart_request | chart | True | - | 結論：已產生 五大產品線 health_score 排名（product_line_health_score_bar），可用於前端圖表渲染與表格檢視。 |
| 8 | 2026年1月以及2026年2月營收有什麼區別？ | period_pair_compare | period_pair_compare | True | - | 結論：2026-02 營收相較 2026-01 下降 240,587,808.00，變化率為 -0.73%。 |
| 9 | 最新月份營收最高的新事業群是誰？ | ranking | ranking | True | - | 結論：最新月份 2026-02 營收最高的新事業群是 1網通+技鋼，營收為 24,670,343,477.00。 |
| 10 | 最新月份庫存最高的新事業群是誰？ | ranking | ranking | True | - | 結論：最新月份 2026-02 庫存金額最高的新事業群是 1網通+技鋼，庫存金額為 73,298,408,408.75。 |
| 11 | 哪個新事業群營收相對庫存效率較弱？ | performance_assessment | performance_weakness | True | - | 結論：目前未對應資料列在新事業群 scorecard 下風險較高，建議先視為資料對應限制；已對應資料則需搭配表格中的 health_score 與 proxy 判讀。 |
| 12 | 哪個五大產品線營收最高？ | ranking | ranking | True | - | 結論：最新月份 2026-02 營收最高的五大產品線是 IOT，營收為 24,820,989,812.00。 |
| 13 | 哪個五大產品線庫存最高？ | ranking | ranking | True | - | 結論：最新月份 2026-02 庫存金額最高的五大產品線是 Server，庫存金額為 73,165,236,987.41。 |
| 14 | 目前資料涵蓋哪些月份？ | data_quality | data_quality | True | - | 目前真實資料已讀取：營收 1982 筆，庫存 122935 筆；共同月份 14 個，最新共同月份為 2026-02。aligned rows=229，both=148，revenue_only=36，inventory_only=45。 另外，目前有 2 筆 pipeline warnings。 |
| 15 | 下個月營收會不會改善？ | forecast_unsupported | unsupported | True | - | 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。 |
| 16 | 為什麼某新事業群營收下降？ | diagnosis | diagnosis | True | - | 結論：目前不能確認根因，但可整理候選觀察方向，優先檢查 3通路方案 是本月營收變化主要貢獻來源。 |
| 17 | 最近有什麼營運風險？ | risk_scan | risk | True | - | 結論：目前最需優先追蹤的是 7製造 風險訊號，異常類型為 營收/庫存金額 proxy 偏弱。 |
| 18 | 請比較新事業群與五大產品線的重點 | cross_section_compare | comparison | True | - | 結論：2026-02 各五大產品線比較下，IOT 營收規模較高，Server 庫存水位較高；但 Server 的營收相對庫存效率較弱，需搭配庫存壓力判讀。 |
| 19 | 哪個新事業群需要優先注意？ | performance_assessment | performance_weakness | True | - | 結論：目前未對應資料列在新事業群 scorecard 下風險較高，建議先視為資料對應限制；已對應資料則需搭配表格中的 health_score 與 proxy 判讀。 |
| 20 | 請產生主管摘要 | executive_summary | overview | True | - | 目前可先從桌面與手機版分析工作台查看最新月份摘要、圖表與風險訊號。 |
| 21 | 哪個新事業群營收相對庫存效率最高？ | ranking | ranking | True | - | 結論：最新月份 2026-02 營收相對庫存效率 proxy最高的新事業群是 5百事益，營收相對庫存效率 proxy為 1.44。 |
| 22 | 哪個新事業群營收相對庫存效率最低？ | ranking | ranking | True | - | 結論：最新月份 2026-02 營收相對庫存效率 proxy最低的新事業群是 7製造，營收相對庫存效率 proxy為 -5.20。 |

## Check Details

### 1. 請整理最新月份各新事業群的營收與庫存重點

- headline: 結論：最新月份 2026-02 各新事業群比較下，1網通+技鋼 營收規模較高，1網通+技鋼 庫存水位較高，未對應資料列在 scorecard 下需作為資料品質限制追蹤。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 2. 請分析哪個新事業群表現較佳

- headline: 結論：目前綜合表現較佳的新事業群是 1網通+技鋼，因為其 綜合分數來自營收、庫存 proxy 與資料完整性。，health_score 為 0.82。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 3. 請分析哪個新事業群表現較差

- headline: 結論：目前未對應資料列在新事業群 scorecard 下風險較高，建議先視為資料對應限制；已對應資料則需搭配表格中的 health_score 與 proxy 判讀。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 4. 比較最新月份各五大產品線營收與庫存

- headline: 結論：2026-02 各五大產品線比較下，IOT 營收規模較高，Server 庫存水位較高；但 Server 的營收相對庫存效率較弱，需搭配庫存壓力判讀。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 5. 哪個產品線庫存壓力較高？

- headline: 結論：目前表現較弱的五大產品線優先看 雲城，因為其 存在 revenue_only 或 inventory_only grain；五大產品線營收較前期下降，health_score 為 0.12。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 6. 請畫最新月份各新事業群營收圖

- headline: 結論：已產生 最新月份各新事業群營收比較（business_group_revenue_bar），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `business_group_revenue_bar, business_group_revenue_bar, business_group_revenue_bar`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 7. 請畫五大產品線 health_score 排名

- headline: 結論：已產生 五大產品線 health_score 排名（product_line_health_score_bar），可用於前端圖表渲染與表格檢視。
- key_observation_count: `3`
- chart_keys: `product_line_health_score_bar, product_line_health_score_bar, product_line_health_score_bar`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 8. 2026年1月以及2026年2月營收有什麼區別？

- headline: 結論：2026-02 營收相較 2026-01 下降 240,587,808.00，變化率為 -0.73%。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 9. 最新月份營收最高的新事業群是誰？

- headline: 結論：最新月份 2026-02 營收最高的新事業群是 1網通+技鋼，營收為 24,670,343,477.00。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 10. 最新月份庫存最高的新事業群是誰？

- headline: 結論：最新月份 2026-02 庫存金額最高的新事業群是 1網通+技鋼，庫存金額為 73,298,408,408.75。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 11. 哪個新事業群營收相對庫存效率較弱？

- headline: 結論：目前未對應資料列在新事業群 scorecard 下風險較高，建議先視為資料對應限制；已對應資料則需搭配表格中的 health_score 與 proxy 判讀。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 12. 哪個五大產品線營收最高？

- headline: 結論：最新月份 2026-02 營收最高的五大產品線是 IOT，營收為 24,820,989,812.00。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 13. 哪個五大產品線庫存最高？

- headline: 結論：最新月份 2026-02 庫存金額最高的五大產品線是 Server，庫存金額為 73,165,236,987.41。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 14. 目前資料涵蓋哪些月份？

- headline: 目前真實資料已讀取：營收 1982 筆，庫存 122935 筆；共同月份 14 個，最新共同月份為 2026-02。aligned rows=229，both=148，revenue_only=36，inventory_only=45。 另外，目前有 2 筆 pipeline warnings。
- key_observation_count: `2`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 15. 下個月營收會不會改善？

- headline: 結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。
- key_observation_count: `2`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 16. 為什麼某新事業群營收下降？

- headline: 結論：目前不能確認根因，但可整理候選觀察方向，優先檢查 3通路方案 是本月營收變化主要貢獻來源。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 17. 最近有什麼營運風險？

- headline: 結論：目前最需優先追蹤的是 7製造 風險訊號，異常類型為 營收/庫存金額 proxy 偏弱。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 18. 請比較新事業群與五大產品線的重點

- headline: 結論：2026-02 各五大產品線比較下，IOT 營收規模較高，Server 庫存水位較高；但 Server 的營收相對庫存效率較弱，需搭配庫存壓力判讀。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 19. 哪個新事業群需要優先注意？

- headline: 結論：目前未對應資料列在新事業群 scorecard 下風險較高，建議先視為資料對應限制；已對應資料則需搭配表格中的 health_score 與 proxy 判讀。
- key_observation_count: `3`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 20. 請產生主管摘要

- headline: 目前可先從桌面與手機版分析工作台查看最新月份摘要、圖表與風險訊號。
- key_observation_count: `2`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 21. 哪個新事業群營收相對庫存效率最高？

- headline: 結論：最新月份 2026-02 營收相對庫存效率 proxy最高的新事業群是 5百事益，營收相對庫存效率 proxy為 1.44。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`

### 22. 哪個新事業群營收相對庫存效率最低？

- headline: 結論：最新月份 2026-02 營收相對庫存效率 proxy最低的新事業群是 7製造，營收相對庫存效率 proxy為 -5.20。
- key_observation_count: `1`
- chart_keys: `-`
- checks: `{"chart_title_no_platform": true, "forecast_unsupported": true, "headline_no_platform": true, "key_observations_max_3": true, "ranking_answer_has_entity_metric_evidence": true, "root_cause_no_confirmed_claim": true, "table_columns_no_platform": true, "unmapped_headline_guardrail": true}`
- failures: `-`
