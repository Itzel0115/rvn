# LLM Writer Shadow Failures

This report diagnoses writer shadow rejections. It includes the Phase 11C-2 baseline 16 rejected cases and the current post-tightening rejects.

## Phase 11C-2 Baseline Rejected Cases

### 3. 請整理最新月份各新事業群的營收與庫存重點

- task_family: `latest_month_entity_summary`
- evidence_types: `entity_performance_snapshot, cross_section_comparison, unsupported_tool_output, unsupported_tool_output`
- writer_output: baseline candidate rejected by `metric_violation:revenue_question_mentions_inventory_as_answer`
- violations: `metric_violation:revenue_question_mentions_inventory_as_answer`
- 判斷: `false_positive_reject`
- 建議處理: `adjust validator`
- diagnosis: Question/evidence is multi-metric, but the old validator treated it like a single-metric answer.

### 6. 各新事業群近 6 個月營收趨勢

- task_family: `entity_trend_comparison`
- evidence_types: `unsupported_tool_output`
- writer_output: baseline candidate rejected by `internal_tool_name_violation:['get_entity_trend_comparison']`
- violations: `internal_tool_name_violation:['get_entity_trend_comparison']`
- 判斷: `true_positive_reject`
- 建議處理: `tighten prompt`
- diagnosis: Writer leaked implementation provenance; prompt must forbid source_tool/tool_name/get_* output.

### 15. 有沒有營收下降但庫存上升的新事業群？

- task_family: `metric_relationship_analysis`
- evidence_types: `relationship_analysis, entity_performance_snapshot`
- writer_output: baseline candidate rejected by `metric_violation:revenue_question_mentions_inventory_as_answer`
- violations: `metric_violation:revenue_question_mentions_inventory_as_answer`
- 判斷: `false_positive_reject`
- 建議處理: `adjust validator`
- diagnosis: Question/evidence is multi-metric, but the old validator treated it like a single-metric answer.

### 17. 3通路方案底下哪個產品線表現較差？

- task_family: `parent_child_drilldown`
- evidence_types: `entity_performance_snapshot, unsupported_tool_output, unsupported_tool_output`
- writer_output: baseline candidate rejected by `internal_tool_name_violation:['get_entity_month_table']`
- violations: `internal_tool_name_violation:['get_entity_month_table']`
- 判斷: `true_positive_reject`
- 建議處理: `tighten prompt`
- diagnosis: Writer leaked implementation provenance; prompt must forbid source_tool/tool_name/get_* output.

### 19. 畫總體營收趨勢

- task_family: `chart_request`
- evidence_types: `unsupported_tool_output, unsupported_tool_output`
- writer_output: baseline candidate rejected by `number_not_in_evidence:['999,999,999']`
- violations: `number_not_in_evidence:['999,999,999']`
- 判斷: `true_positive_reject`
- 建議處理: `keep rejected`
- diagnosis: Writer introduced a number not present in evidence; keep the rejection.

### 24. 下個月營收會不會改善？

- task_family: `forecast_unsupported`
- evidence_types: `not available`
- writer_output: baseline candidate rejected by `forecast_violation:unsupported_forecast_claim`
- violations: `forecast_violation:unsupported_forecast_claim`
- 判斷: `true_positive_reject`
- 建議處理: `tighten prompt`
- diagnosis: Writer made a predictive claim for an unsupported forecast task; prompt must force safe refusal.

### 25. 未來哪個事業群會成長？

- task_family: `forecast_unsupported`
- evidence_types: `not available`
- writer_output: baseline candidate rejected by `forecast_violation:unsupported_forecast_claim`
- violations: `forecast_violation:unsupported_forecast_claim`
- 判斷: `true_positive_reject`
- 建議處理: `tighten prompt`
- diagnosis: Writer made a predictive claim for an unsupported forecast task; prompt must force safe refusal.

### 26. 請整理最新月份各事業群的營收與庫存重點

- task_family: `latest_month_entity_summary`
- evidence_types: `entity_performance_snapshot, cross_section_comparison, unsupported_tool_output, unsupported_tool_output`
- writer_output: baseline candidate rejected by `metric_violation:revenue_question_mentions_inventory_as_answer`
- violations: `metric_violation:revenue_question_mentions_inventory_as_answer`
- 判斷: `false_positive_reject`
- 建議處理: `adjust validator`
- diagnosis: Question/evidence is multi-metric, but the old validator treated it like a single-metric answer.

### 27. 請整理最新月份各新事業群的營收與庫存重點

- task_family: `latest_month_entity_summary`
- evidence_types: `entity_performance_snapshot, cross_section_comparison, unsupported_tool_output, unsupported_tool_output`
- writer_output: baseline candidate rejected by `metric_violation:revenue_question_mentions_inventory_as_answer`
- violations: `metric_violation:revenue_question_mentions_inventory_as_answer`
- 判斷: `false_positive_reject`
- 建議處理: `adjust validator`
- diagnosis: Question/evidence is multi-metric, but the old validator treated it like a single-metric answer.

### 28. 請整理最新月份各 BU 營收與庫存重點

- task_family: `latest_month_entity_summary`
- evidence_types: `entity_performance_snapshot, cross_section_comparison, unsupported_tool_output, unsupported_tool_output`
- writer_output: baseline candidate rejected by `metric_violation:revenue_question_mentions_inventory_as_answer`
- violations: `metric_violation:revenue_question_mentions_inventory_as_answer`
- 判斷: `false_positive_reject`
- 建議處理: `adjust validator`
- diagnosis: Question/evidence is multi-metric, but the old validator treated it like a single-metric answer.

### 34. 畫出 2026年2月 各產品線庫存長條圖

- task_family: `chart_request`
- evidence_types: `unsupported_tool_output, unsupported_tool_output`
- writer_output: baseline candidate rejected by `internal_tool_name_violation:['get_entity_month_table']`
- violations: `internal_tool_name_violation:['get_entity_month_table']`
- 判斷: `true_positive_reject`
- 建議處理: `tighten prompt`
- diagnosis: Writer leaked implementation provenance; prompt must forbid source_tool/tool_name/get_* output.

### 38. 比較2025年3月各事業群營收資料

- task_family: `cross_section_compare`
- evidence_types: `cross_section_comparison`
- writer_output: baseline candidate rejected by `number_not_in_evidence:['999,999,999']`
- violations: `number_not_in_evidence:['999,999,999']`
- 判斷: `true_positive_reject`
- 建議處理: `keep rejected`
- diagnosis: Writer introduced a number not present in evidence; keep the rejection.

### 45. 比較 Server 2025/02 和 2025/03 庫存

- task_family: `entity_period_pair_metric_lookup`
- evidence_types: `unsupported_tool_output`
- writer_output: baseline candidate rejected by `internal_tool_name_violation:['get_entity_period_pair_value']`
- violations: `internal_tool_name_violation:['get_entity_period_pair_value']`
- 判斷: `true_positive_reject`
- 建議處理: `tighten prompt`
- diagnosis: Writer leaked implementation provenance; prompt must forbid source_tool/tool_name/get_* output.

### 50. 列出 3通路方案 2025/02 與 2025/03 營收

- task_family: `entity_period_pair_metric_lookup`
- evidence_types: `unsupported_tool_output`
- writer_output: baseline candidate rejected by `internal_tool_name_violation:['get_entity_period_pair_value']`
- violations: `internal_tool_name_violation:['get_entity_period_pair_value']`
- 判斷: `true_positive_reject`
- 建議處理: `tighten prompt`
- diagnosis: Writer leaked implementation provenance; prompt must forbid source_tool/tool_name/get_* output.

### 51. 列出 2025年3月 3通路方案底下各產品線庫存

- task_family: `entity_month_table_lookup`
- evidence_types: `entity_month_table`
- writer_output: baseline candidate rejected by `internal_tool_name_violation:['get_entity_month_table']`
- violations: `internal_tool_name_violation:['get_entity_month_table']`
- 判斷: `true_positive_reject`
- 建議處理: `tighten prompt`
- diagnosis: Writer leaked implementation provenance; prompt must forbid source_tool/tool_name/get_* output.

### 57. 列出 2025年3月各產品線資料

- task_family: `entity_month_table_lookup`
- evidence_types: `entity_month_table`
- writer_output: baseline candidate rejected by `number_not_in_evidence:['999,999,999']`
- violations: `number_not_in_evidence:['999,999,999']`
- 判斷: `true_positive_reject`
- 建議處理: `keep rejected`
- diagnosis: Writer introduced a number not present in evidence; keep the rejection.


## Current Post-Tightening Rejected Cases

### 19. 畫總體營收趨勢

- task_family: `chart_request`
- evidence_types: `unsupported_tool_output, unsupported_tool_output`
- writer_output: `{"confidence_note": "shadow mode only", "headline": "結論：已整理 指定期間 整體revenue_amount資料。 另有 999,999,999。", "key_observations": ["候選摘要僅使用 EvidenceContract 中的月份、entity 與 metric。"], "limitations": ["回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。", "部分工具輸出尚未納入標準 evidence normalization，僅作描述性整理。"], "table_caption": "指定期間 整體revenue_amount"}`
- violations: `["number_not_in_evidence:['999,999,999']"]`
- 判斷: `true_positive_reject`
- 建議處理: `keep rejected`

### 38. 比較2025年3月各事業群營收資料

- task_family: `cross_section_compare`
- evidence_types: `cross_section_comparison`
- writer_output: `{"confidence_note": "shadow mode only", "headline": "結論：已整理 2025-03 事業群營收資料。 另有 999,999,999。", "key_observations": ["候選摘要僅使用 EvidenceContract 中的月份、entity 與 metric。"], "limitations": ["回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。"], "table_caption": "2025-03 事業群營收"}`
- violations: `["number_not_in_evidence:['999,999,999']"]`
- 判斷: `true_positive_reject`
- 建議處理: `keep rejected`

### 57. 列出 2025年3月各產品線資料

- task_family: `entity_month_table_lookup`
- evidence_types: `entity_month_table`
- writer_output: `{"confidence_note": "shadow mode only", "headline": "結論：已整理 2025-03 產品線營收資料。 另有 999,999,999。", "key_observations": ["候選摘要僅使用 EvidenceContract 中的月份、entity 與 metric。"], "limitations": ["回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。"], "table_caption": "2025-03 產品線營收"}`
- violations: `["number_not_in_evidence:['999,999,999']"]`
- 判斷: `true_positive_reject`
- 建議處理: `keep rejected`

