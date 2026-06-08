# Live Writer Shadow Failure Analysis

Phase 11C-4 analyzes the Phase 11C-3 GB10 writer shadow live run.

Scope:

- Official `/api/ask` response was not changed.
- Official `display_blocks` were not replaced.
- Writer output stayed shadow-only.
- Live logs recorded validator summaries but not full writer output. The `writer_output` snippets below were reproduced by replaying LLMEvidenceWriter against the same saved live evidence snapshot from `/tmp/gb10_writer_on.json`.

## Summary

Live 10-question shadow run:

- writer_called_count: 10
- writer_valid_count: 3
- writer_invalid_count: 7
- official answer/display_blocks changed: no

Live violation counts from backend log:

| violation | count |
|---|---:|
| entity_not_in_evidence | 18 |
| limitation_violation | 4 |
| internal_tool_name_violation | 3 |
| debug_string_violation | 1 |
| root_cause_violation | 1 |

Main finding:

- Most `entity_not_in_evidence` live failures are not concrete hallucinated entities. They are generic label phrases such as `期間各產品線`, `表列各事業群`, `此表格列出各產品線`, `下各產品線`, and `所有產品線`.
- `limitation_violation` is mixed. Some are true positives where the writer dropped required limitations. Some are validator strictness around where the limitation appears.
- `internal_tool_name_violation` is a real prompt/input exposure issue: writer input still contains `source_tool`, `raw_reference`, tool-like names, evidence type keys, and chart keys.

## Rejected Cases

### 1. 列出 2025/09 與 2025/10 產品線的庫存

- task_family: `entity_period_pair_table_lookup`
- evidence_types: `entity_period_pair_table`
- canonical entity list: `Server`, `顯卡`, `主板`, `筆電`, `IOT`, `百事益`, `Other`, `專案電腦`, `螢幕`
- live log violations:
  - `entity_not_in_evidence:期間各產品線`
  - `entity_not_in_evidence:個產品線`
  - `limitation_violation:missing_limitation:期間比較為描述性差異，不宣稱 root cause。`
  - `internal_tool_name_violation:['get_entity_period_pair_table']`
- replayed writer_output:

```json
{
  "headline": "結論：已列出 2025-09 與 2025-10 各產品線庫存金額資料，共 9 筆；2025-10 最高的是 Server。",
  "key_observations": ["2025-10 vs 2025-09 各產品線 庫存金額 table rows=9"],
  "limitations": ["回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。"],
  "table_caption": "表列了 2025-09 與 2025-10 期間各產品線的庫存金額（inventory_amount）資料。",
  "confidence_note": "本分析結果完全基於提供的證據資料，數據完整性高，但無法提供業務判斷或預測。"
}
```

Judgment:

- `entity_not_in_evidence`: validator_too_strict / entity_alias_gap. `期間各產品線` and `個產品線` are generic label phrases, not entity claims.
- `debug_string_violation`: true_positive_reject. `table rows=9` is a debug-style phrase.
- `limitation_violation`: true_positive_reject. The specific period-comparison/no-root-cause limitation was dropped from `limitations`.
- `internal_tool_name_violation`: internal_tool_prompt_gap in the live output.

Recommended handling:

- Add entity phrase normalization / allowlist for generic dimension-label phrases.
- Tighten writer prompt to avoid `table rows=N`.
- Build writer-safe evidence view to hide `source_tool`.
- Keep rejected until all non-entity violations are fixed.

### 2. 列出 2025/03 各產品線庫存資料

- task_family: `entity_month_table_lookup`
- evidence_types: `entity_month_table`
- canonical entity list: `Server`, `顯卡`, `主板`, `筆電`, `IOT`, `百事益`, `Other`, `專案電腦`, `螢幕`, `雲城`
- live log violations:
  - `entity_not_in_evidence:本報告的資料來源為單一的產品線`
  - `entity_not_in_evidence:個產品線`
  - `entity_not_in_evidence:為所有產品線`
- replayed writer_output:

```json
{
  "headline": "結論：已列出 2025-03 各產品線庫存金額資料，共 10 筆；庫存金額最高的是 Server。",
  "key_observations": ["2025-03 各產品線庫存金額資料共 10 筆；最高的是 Server。"],
  "limitations": ["回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。"],
  "table_caption": "表為 2025-03 各產品線的庫存金額、庫存數量及相關資料。",
  "confidence_note": "本資料為根據提供的證據合同整理，數據範圍僅限於合同內呈現的產品線和月份。"
}
```

Judgment:

- `entity_not_in_evidence`: validator_too_strict / entity_alias_gap. These are generic references to the product-line dimension, not hallucinated product lines.
- No concrete entity hallucination found.

Recommended handling:

- Allow generic dimension phrases when they do not introduce a concrete entity value.
- Prefer wording like `表格列出產品線維度資料` in prompt, but validator normalization is the main fix.

### 3. 比較 2025/02 與 2025/03 各事業群營收

- task_family: `entity_period_pair_table_lookup`
- evidence_types: `entity_period_pair_table`
- canonical entity list: `1網通+技鋼`, `2技宸`, `3通路方案`, `4筆電+盈嘉`, `5百事益`, `6雲城`, `7製造`
- live log violations:
  - `entity_not_in_evidence:此表列出各事業群`
  - `limitation_violation:missing_limitation:期間比較為描述性差異，不宣稱 root cause。`
  - `debug_string_violation`
- replayed writer_output:

```json
{
  "headline": "已列出 2025-02 與 2025-03 各事業群營收資料，共 7 筆；2025-03 最高的是 3通路方案。",
  "key_observations": [
    "資料涵蓋 2025-02 與 2025-03 兩個期間的各事業群營收，共 7 筆。",
    "在 2025-03 的營收數據中，3通路方案的營收最高。",
    "事業群的營收比較為描述性差異，不宣稱 root cause。"
  ],
  "limitations": ["回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。"],
  "table_caption": "表列各事業群 2025-02 與 2025-03 的營收比較。",
  "confidence_note": "本分析結果完全基於提供的營收數據，不包含外部推論。"
}
```

Judgment:

- `entity_not_in_evidence`: validator_too_strict / entity_alias_gap. `此表列出各事業群` and `兩個期間的各事業群` are generic dimension-label phrases.
- `limitation_violation`: possible validator_too_strict. The limitation meaning appears in `key_observations`, but not in the `limitations` list.
- `debug_string_violation`: live true positive if the live output contained `rows=N`; replay output did not.

Recommended handling:

- Keep limitation preservation guardrail, but consider validating required limitations across full writer output, while still requiring a non-empty `limitations` list.
- Better prompt: required limitations must appear under `limitations`, not only observations.

### 4. 請整理最新月份各事業群的營收與庫存重點

- task_family: `latest_month_entity_summary`
- evidence_types: `entity_performance_snapshot`
- canonical entity list: `1網通+技鋼`, `2技宸`, `3通路方案`, `4筆電+盈嘉`, `5百事益`, `6雲城`, `7製造`, `未對應`
- live log violations:
  - `entity_not_in_evidence:最新月份各事業群`
  - `entity_not_in_evidence:部分事業群`
  - `root_cause_violation:['導致']`
  - `internal_tool_name_violation:['get_entity_performance_snapshot']`
- replayed writer_output:

```json
{
  "headline": "最新月份 2026-02 各事業群表現分析顯示，1網通+技鋼在營收和庫存規模上領先，但需關注未對應資料列的資料完整性。",
  "key_observations": [
    "在 2026-02 的數據中，1網通+技鋼的營收（24670343477）和庫存（73298408408.75099）均位居領先，其綜合分數（health_score）為 0.8338。",
    "「未對應」事業群雖然有庫存數據（11419428.974），但缺乏營收數據，導致其風險分數（risk_score）為 1.0。",
    "分析包含多個 proxy 指標，如營收/庫存比率，且 health_score 為 deterministic scorecard，需搭配多維度指標解讀。"
  ],
  "limitations": [
    "health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料完整性解讀。",
    "營收/庫存比率為 proxy 指標，非正式周轉指標。",
    "部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。"
  ],
  "table_caption": "表列為 2026-02 最新月份各事業群的營收、庫存及相關績效指標。",
  "confidence_note": "本分析基於提供的 entity_performance_snapshot 數據，數據完整性受限於原始資料的可用性。"
}
```

Judgment:

- `entity_not_in_evidence`: validator_too_strict / entity_alias_gap for generic `最新月份各事業群`.
- `root_cause_violation`: true_positive_reject. `導致` is causal language, even if used casually.
- `limitation_violation`: true_positive_reject. The denominator-validity limitation was not preserved.
- `internal_tool_name_violation`: internal_tool_prompt_gap. `entity_performance_snapshot` leaked from evidence type/source context.

Recommended handling:

- Writer-safe evidence view should replace `entity_performance_snapshot` with a user-safe label such as `績效摘要證據`.
- Prompt should ban `導致` explicitly even for data-quality descriptions.
- Do not relax root-cause guardrail.

### 5. 有沒有營收下降但庫存上升的新事業群？

- task_family: `metric_relationship_analysis`
- evidence_types: `relationship_analysis`
- canonical entity list: `1網通+技鋼`, `2技宸`, `3通路方案`, `4筆電+盈嘉`, `5百事益`, `6雲城`, `7製造`, `未對應`
- live log violations:
  - `entity_not_in_evidence:有數個事業群`
  - `entity_not_in_evidence:此表列出各事業群`
  - `limitation_violation:missing_limitation:營收相對庫存效率為 proxy，非正式庫存週轉率。`
  - `internal_tool_name_violation:['get_revenue_inventory_relationship']`
- replayed writer_output:

```json
{
  "headline": "根據資料，目前可觀察到2技宸、4筆電+盈嘉和7製造這三個事業群符合營收下降但庫存上升的訊號。",
  "key_observations": [
    "2技宸在2026-02月，營收較前月下降-67455815.0，但庫存增加57507890.32。",
    "4筆電+盈嘉在2026-02月，營收較前月下降-36657377.0，但庫存增加328500591.24。",
    "7製造在2026-02月，營收較前月下降-27275880.0，但庫存增加78970.34。"
  ],
  "limitations": [
    "這類問題目前只能用營收與庫存的風險訊號訊號回答，不能直接判定根本原因。",
    "這是根據目前營收與庫存資料偵測出的風險訊號，尚不能直接代表根本原因。"
  ],
  "table_caption": "此表列出各事業群在2026-02月相較於2026-01月的營收、庫存及營收相對庫存效率的變化。",
  "confidence_note": "資訊來源為get_revenue_inventory_relationship，分析基於營收與庫存的歷史變化關係。"
}
```

Judgment:

- `entity_not_in_evidence`: validator_too_strict for generic phrases.
- `internal_tool_name_violation`: true_positive_reject. `get_revenue_inventory_relationship` leaked.
- `limitation_violation`: true_positive_reject. The root-cause limitation was preserved, but the proxy/non-formal-turnover limitation was dropped.
- Replay also produced `number_not_in_evidence:['24', '32']`, likely from parsing decimal fragments or shortened formatted values. This needs separate number-format inspection before changing validator.

Recommended handling:

- Writer-safe evidence view must hide `source_tool`.
- Keep proxy limitation guardrail.
- Add prompt wording: relationship evidence must always keep both limitations: no root cause and proxy/non-formal-turnover.

### 6. 畫出 2025/02 與 2025/03 各產品線庫存比較圖

- task_family: `chart_request`
- evidence_types: `chart_payload`
- canonical entity list: `Server`, `顯卡`, `主板`, `筆電`, `IOT`, `百事益`, `Other`, `專案電腦`, `螢幕`, `雲城`
- live log violations:
  - `entity_not_in_evidence:用於分析產品線`
  - `entity_not_in_evidence:期間各產品線`
  - `entity_not_in_evidence:個產品線`
  - `entity_not_in_evidence:表格詳細列出了各產品線`
- replayed writer_output:

```json
{
  "headline": "已產生 2025-02 與 2025-03 各產品線庫存金額比較圖（entity_period_pair_table_chart），可用於前端圖表渲染與表格檢視。",
  "key_observations": [
    "圖表 key 為 entity_period_pair_table_chart，圖型為 grouped_bar。",
    "圖表包含 2 組資料序列，用於比較 2025-02 與 2025-03 的庫存金額。",
    "表格列出了 10 個產品線的庫存金額（inventory_amount）數據。"
  ],
  "limitations": ["回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。"],
  "table_caption": "此表格列出各產品線在 2025-02 與 2025-03 的庫存金額（inventory_amount）及相關數據。",
  "confidence_note": "所有數據均來自 EvidenceContract 提供的 chart_payload。"
}
```

Judgment:

- `entity_not_in_evidence`: validator_too_strict / entity_alias_gap for generic dimension phrases.
- Writer output exposes internal chart artifacts: `entity_period_pair_table_chart`, `chart key`, `EvidenceContract`, `chart_payload`, `inventory_amount`.
- `limitation_violation` in replay is true positive: required period-comparison/no-root-cause limitation was dropped.

Recommended handling:

- Writer-safe evidence view is high priority for chart payloads. Hide `chart_key`, raw `chart_type`, `EvidenceContract`, and internal metric ids; provide user-safe labels instead.
- Keep rejected until chart artifact leakage is removed.

### 9. 3通路方案底下哪個產品線表現較差？

- task_family: `parent_child_drilldown`
- evidence_types: `entity_performance_snapshot`, `unsupported_tool_output`, `unsupported_tool_output`
- canonical entity list: `3通路方案`, `顯卡`, `主板`, `專案電腦`, `螢幕`, `Other`
- live log violations:
  - `entity_not_in_evidence:下各產品線`
  - `entity_not_in_evidence:的產品線`
  - `entity_not_in_evidence:是目前較需要注意的子層產品線`
  - `limitation_violation:missing_limitation:只在 revenue 與 inventory 同時存在且分母合法時才計算 rat`
- replayed writer_output:

```json
{
  "headline": "結論：在 3通路方案 底下，專案電腦 產品線表現較弱 / 庫存壓力較高。",
  "key_observations": [
    "專案電腦 是目前較需要注意的子層產品線。",
    "3通路方案 的營收/庫存金額 proxy 為 0.17，代表在目前資料中營收相對庫存效率偏弱。",
    "3通路方案 的營收/庫存金額 proxy 為 0.16，代表在目前資料中營收相對庫存效率偏弱。"
  ],
  "limitations": [
    "此為營收與庫存資料推導的 proxy，非正式周轉指標。",
    "health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。"
  ],
  "table_caption": "表列了 2026-02 年 3通路方案 下各產品線的營收、庫存、以及相關的性能指標。",
  "confidence_note": "所有產品線的資料均完整，可依據提供的指標進行分析。"
}
```

Judgment:

- `entity_not_in_evidence`: mixed.
  - `下各產品線`, `的產品線`, `所有產品線`: validator_too_strict / generic label phrase.
  - `是目前較需要注意的子層產品線`: validator_too_strict due greedy phrase capture; actual entity `專案電腦` is present in evidence.
- `limitation_violation`: true_positive_reject. The denominator-validity limitation and unsupported-output limitations were not preserved.
- EvidenceContract gap: two `unsupported_tool_output` contracts expose low-quality limitations and do not give writer a user-safe explanation.

Recommended handling:

- Add generic phrase allowlist, but do not allow unknown concrete product-line names.
- Enrich EvidenceContract for `get_inventory_turnover_proxy` or avoid passing unsupported contracts to writer until normalized.
- Keep rejected until limitation preservation is improved.

## Entity Violation Diagnosis

Observed `entity_not_in_evidence` causes:

| cause | present? | examples | recommendation |
|---|---:|---|---|
| Writer used an entity not in evidence | no clear case | none found in the 7 rejected outputs | keep reject if this appears |
| Synonym / dimension label | yes | `各產品線`, `各事業群`, `新事業群`, `子層產品線` | add normalized generic dimension phrase allowlist |
| Field label mistaken as entity | yes | `此表列出各事業群`, `表格列出了各產品線` | strip leading table/context prefixes before entity validation |
| Headline/general phrase mistaken as entity | yes | `最新月份各事業群`, `期間各產品線`, `下各產品線` | allow generic dimension phrases when no concrete value is introduced |
| Evidence aliases insufficient | partly | parent-child drilldown has `3通路方案` plus product lines but no safe label aliases | add writer-safe entity aliases and dimension labels |

Recommended normalization / allowlist:

- Normalize generic dimension phrases to dimension labels:
  - `各產品線`, `所有產品線`, `期間各產品線`, `此表格列出各產品線`, `下各產品線` -> `product_line_5` dimension label
  - `各事業群`, `新事業群`, `最新月份各事業群`, `此表列出各事業群` -> `business_group` dimension label
  - `整體`, `總體`, `全公司` -> `overall`
- Strip context prefixes before entity matching:
  - `此表列出`, `表列`, `表格列出`, `資料涵蓋`, `數據範圍僅限於`, `用於分析`
- Keep strict rejection for unknown concrete names, especially strings not reducible to generic dimension labels.

## Limitation Violation Diagnosis

Observed causes:

| cause | present? | cases | recommendation |
|---|---:|---|---|
| Writer fully deleted required limitation | yes | cases 1, 4, 5, 6, 9 | keep reject |
| Writer preserved semantics outside `limitations` | yes | case 3 | allow semantic scan across full writer output, but still require `limitations` non-empty |
| Task did not need limitation | no | limitations came from evidence contracts / deterministic answer | keep preservation guardrail |

Recommended changes:

- Keep limitation preservation guardrail.
- Prompt: every required limitation must appear in the `limitations` array.
- Validator: consider recognizing a limitation as semantically preserved if it appears anywhere in writer output, while separately warning if it is not placed in `limitations`.
- Do not remove proxy, denominator-validity, root-cause, or forecast limitations.

## Internal Tool Name Diagnosis

Evidence currently visible to writer includes internal fields:

- `source_tool`
- `raw_reference`
- raw `evidence_type`
- chart keys such as `entity_period_pair_table_chart`
- internal metric ids such as `inventory_amount`
- unsupported tool limitation text such as `EvidenceContractBuilder does not yet support tool output: unknown`

This makes prompt-only suppression fragile. The live output leaked tool names even though the prompt already said not to.

Recommended writer-safe evidence view:

- Remove `source_tool`.
- Remove `raw_reference`.
- Replace internal `evidence_type` with user-safe labels:
  - `entity_period_pair_table` -> `期間比較表`
  - `entity_month_table` -> `單月 entity 表`
  - `entity_performance_snapshot` -> `績效摘要`
  - `relationship_analysis` -> `營收與庫存關係分析`
  - `chart_payload` -> `圖表資料`
- Replace metric ids with labels:
  - `revenue_amount` -> `營收`
  - `inventory_amount` -> `庫存金額`
  - `inventory_qty` -> `庫存數量`
  - `revenue_inventory_amount_ratio` -> `營收相對庫存效率 proxy`
- Replace chart keys with chart descriptions:
  - `entity_period_pair_table_chart` -> `兩期 entity 比較圖`
  - `grouped_bar` -> `分組長條圖`
- Either normalize unsupported tool outputs or omit them from writer input with a safe limitation.

## Proposed Phase 11C-5

Recommended Phase 11C-5 scope:

1. Add `WriterSafeEvidenceViewBuilder`.
2. Feed LLMEvidenceWriter only writer-safe evidence, not raw EvidenceContract.
3. Add generic entity label normalization in WriterValidator.
4. Tighten prompt around limitations array placement and chart/internal artifact wording.
5. Preserve all hard guardrails:
   - no new numbers
   - no wrong months
   - no unknown concrete entities
   - no wrong metric
   - no forecast claim
   - no root cause claim
   - no internal tool names

Recommendation:

- Proceed to Phase 11C-5: yes.
- Keep `USE_LLM_WRITER=false` for GB10 official/demo mode.
- Writer may be tested in shadow mode only.
