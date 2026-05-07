# Demo Smoke Report

- mode: direct
- cases: 8

| Question | Task Family | Key Obs | Table | Headline |
|---|---:|---:|---:|---|
| 請分析哪個平台表現較佳 | performance_assessment | 3 | no | 結論：目前綜合表現較佳的平台是 GG-01，因為其 營收規模排名較高；營收相對庫存效率 proxy 較高；目前未見同月異常訊號，health_score 為 0.97。 |
| 請分析哪個平台表現較差 | performance_assessment | 3 | no | 結論：目前表現較弱的平台優先看 GG-06，因為其 同月異常訊號 1 筆；營收相對庫存效率 proxy 排名偏後；營收動能相對偏弱，health_score 為 0.13。 |
| 比較 8 月各平台營收與庫存 | cross_section_compare | 3 | yes | 結論：2024-08 各平台比較下，GG-01 營收規模較高，GG-02 庫存水位較高；但 GG-02 的營收相對庫存效率較弱，需搭配庫存壓力判讀。 |
| 哪個平台最健康？ | performance_assessment | 3 | no | 結論：目前綜合表現較佳的平台是 GG-01，因為其 營收規模排名較高；營收相對庫存效率 proxy 較高；目前未見同月異常訊號，health_score 為 0.97。 |
| 最近有什麼營運風險？ | risk_scan | 3 | no | 結論：目前最需優先追蹤的是 GG-02 風險訊號，異常類型為 營收/庫存金額比偏低。 |
| 8 月相較 7 月營收變化主要由誰貢獻？ | time_compare | 2 | no | 結論：2024-08 相較 2024-07 的營收變化主要由 雲端服務 貢獻，變化 195.00。 |
| 資料涵蓋哪些月份？ | data_quality | 2 | no | 目前資料涵蓋 8 個月份，最新月份為 2024-08。營收資料 48 筆，庫存資料 48 筆，mapping 資料 6 筆，mapping_success=True。 另外，目前有 1 筆 pipeline warnings。 |
| 下個月營收會不會改善？ | metric_lookup | 3 | no | 結論：sales: metric_table |

## Details

### 請分析哪個平台表現較佳

- task_family: `performance_assessment`
- primary_tools: `get_platform_performance_snapshot, get_inventory_turnover_proxy, get_platform_ratios`
- tools_used: `get_platform_performance_snapshot, get_inventory_turnover_proxy, get_platform_ratios, get_anomalies`
- key_observation_count: `3`
- has_table: `False`
- limitations: 目前回答仍以營收、庫存與異常訊號為主，不能直接等同完整因果判斷。 | 此為營收與庫存資料推導的 proxy，不等於正式庫存週轉率。
- headline: 結論：目前綜合表現較佳的平台是 GG-01，因為其 營收規模排名較高；營收相對庫存效率 proxy 較高；目前未見同月異常訊號，health_score 為 0.97。

### 請分析哪個平台表現較差

- task_family: `performance_assessment`
- primary_tools: `get_platform_performance_snapshot, get_inventory_turnover_proxy, get_platform_ratios`
- tools_used: `get_platform_performance_snapshot, get_inventory_turnover_proxy, get_platform_ratios, get_anomalies`
- key_observation_count: `3`
- has_table: `False`
- limitations: 目前回答仍以營收、庫存與異常訊號為主，不能直接等同完整因果判斷。 | 此為營收與庫存資料推導的 proxy，不等於正式庫存週轉率。
- headline: 結論：目前表現較弱的平台優先看 GG-06，因為其 同月異常訊號 1 筆；營收相對庫存效率 proxy 排名偏後；營收動能相對偏弱，health_score 為 0.13。

### 比較 8 月各平台營收與庫存

- task_family: `cross_section_compare`
- primary_tools: `get_platform_performance_snapshot, get_platform_ratios, get_metric_table(platform_monthly)`
- tools_used: `get_platform_performance_snapshot, get_platform_ratios, get_anomalies`
- key_observation_count: `3`
- has_table: `True`
- limitations: 回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。
- headline: 結論：2024-08 各平台比較下，GG-01 營收規模較高，GG-02 庫存水位較高；但 GG-02 的營收相對庫存效率較弱，需搭配庫存壓力判讀。

### 哪個平台最健康？

- task_family: `performance_assessment`
- primary_tools: `get_platform_performance_snapshot, get_inventory_turnover_proxy, get_platform_ratios`
- tools_used: `get_platform_performance_snapshot, get_inventory_turnover_proxy, get_platform_ratios, get_anomalies`
- key_observation_count: `3`
- has_table: `False`
- limitations: 目前回答仍以營收、庫存與異常訊號為主，不能直接等同完整因果判斷。 | 此為營收與庫存資料推導的 proxy，不等於正式庫存週轉率。
- headline: 結論：目前綜合表現較佳的平台是 GG-01，因為其 營收規模排名較高；營收相對庫存效率 proxy 較高；目前未見同月異常訊號，health_score 為 0.97。

### 最近有什麼營運風險？

- task_family: `risk_scan`
- primary_tools: `get_anomalies`
- tools_used: `get_platform_ratios, get_anomalies, get_inventory_turnover_proxy`
- key_observation_count: `3`
- has_table: `False`
- limitations: 目前回答仍以營收、庫存與異常訊號為主，不能直接等同完整因果判斷。 | 此為營收與庫存資料推導的 proxy，不等於正式庫存週轉率。
- headline: 結論：目前最需優先追蹤的是 GG-02 風險訊號，異常類型為 營收/庫存金額比偏低。

### 8 月相較 7 月營收變化主要由誰貢獻？

- task_family: `time_compare`
- primary_tools: `get_yoy_mom_breakdown, get_contribution_analysis`
- tools_used: `get_yoy_mom_breakdown(revenue), get_contribution_analysis(revenue)`
- key_observation_count: `2`
- has_table: `False`
- limitations: 目前沒有去年同期資料，因此暫時無法提供 YoY。
- headline: 結論：2024-08 相較 2024-07 的營收變化主要由 雲端服務 貢獻，變化 195.00。

### 資料涵蓋哪些月份？

- task_family: `data_quality`
- primary_tools: `get_data_coverage, get_mapping_summary`
- tools_used: `get_data_coverage, get_mapping_summary`
- key_observation_count: `2`
- has_table: `False`
- limitations: 目前資料品質報告僅反映已載入資料與 pipeline 狀態。 | 若 mapping 有 ambiguous candidates，平台層分析需搭配限制解讀。 | 目前仍有 pipeline warnings，解讀結果時需一併納入。
- headline: 目前資料涵蓋 8 個月份，最新月份為 2024-08。營收資料 48 筆，庫存資料 48 筆，mapping 資料 6 筆，mapping_success=True。 另外，目前有 1 筆 pipeline warnings。

### 下個月營收會不會改善？

- task_family: `metric_lookup`
- primary_tools: `get_metric_table`
- tools_used: ``
- key_observation_count: `3`
- has_table: `False`
- limitations: 目前資料無法直接支援 forecast 類問題。 | 目前尚無法直接判斷原因或預測未來變化，因為資料不包含完整因果所需欄位。
- headline: 結論：sales: metric_table
