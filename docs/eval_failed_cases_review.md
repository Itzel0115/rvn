# Phase 8F-2 Eval Failed Cases Review

Date: 2026-05-08

Scope: review answer eval cases with `must_include_score < 1.0` after Phase 8F-1. This review does not add product behavior, does not change the `/api/ask` contract, and does not enable LLM planner or rewriter.

## Summary

- Failed / partial `must_include_score` cases: 5
- Core routing/tooling status: all 5 cases routed to the expected task family and avoided forbidden tool leakage.
- Primary failure pattern: exact-string expectation mismatch after display wording was improved.
- Code changes recommended: none for this round.
- Eval expectation changes applied: yes, limited to wording alignment in `eval/questions_answer.jsonl`.

## Case Reviews

### answer_010

- Question: `Will next month revenue improve?`
- Task family: `forecast_unsupported`
- Expected must_include before review: `預測`, `下個月營收是否改善`
- Actual headline: `結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。`
- Actual key observations:
  - `目前資料可用於觀察歷史營收與庫存變化，但不足以直接預測下個月。`
  - `若要評估改善機率，需補充訂單、出貨、價格、客戶需求或正式 forecast model。`
- Missing item: `下個月營收是否改善`
- Failure reason: wording mismatch. The answer says `下個月營收是否會改善`, which is semantically equivalent and clearer.
- Suggested handling: fix eval expectation.
- Applied change: `下個月營收是否改善` -> `下個月營收是否會改善`

### answer_015

- Question: `What is the market demand forecast?`
- Task family: `forecast_unsupported`
- Expected must_include before review: `market demand`, `forecast`, `無法直接回答`
- Actual headline: `結論：目前無法判斷下個月營收是否會改善，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。`
- Actual key observations:
  - `目前資料可用於觀察歷史營收與庫存變化，但不足以直接預測下個月。`
  - `若要評估改善機率，需補充訂單、出貨、價格、客戶需求或正式 forecast model。`
- Actual answer / limitations include: `目前資料無法直接支援 market demand 類問題。 目前資料無法直接支援 forecast 類問題。`
- Missing item: `無法直接回答`
- Failure reason: wording mismatch. Current unsupported wording uses `無法直接支援` rather than `無法直接回答`.
- Suggested handling: fix eval expectation.
- Applied change: `無法直接回答` -> `無法直接支援`

### answer_046

- Question: `比較 8 月各平台營收與庫存`
- Task family: `cross_section_compare`
- Expected must_include before review: `同月份平台橫向比較`, `GG-02`
- Actual headline: `結論：2024-08 各平台比較下，GG-01 營收規模較高，GG-02 庫存水位較高；但 GG-02 的營收相對庫存效率較弱，需搭配庫存壓力判讀。`
- Actual key observations:
  - `平台 scorecard 綜合營收規模、營收動能、營收相對庫存效率 proxy 與異常訊號；最佳候選為 GG-01，health_score=0.97，需優先注意 GG-06。`
  - `GG-02 的營收/庫存金額 proxy 為 0.54，代表在目前資料中營收相對庫存效率偏弱。`
  - `GG-05 的營收/庫存金額 proxy 為 1.41，可作為營收相對庫存效率的比較依據。`
- Missing item: `同月份平台橫向比較`
- Failure reason: wording mismatch. The actual headline uses `各平台比較下`, and the filters/task family already verify the same-month cross-section behavior.
- Suggested handling: fix eval expectation.
- Applied change: `同月份平台橫向比較` -> `各平台比較下`

### answer_047

- Question: `請分析哪個平台表現較佳`
- Task family: `performance_assessment`
- Expected must_include before review: `不應以庫存金額最高`, `營收/庫存`
- Actual headline: `結論：目前綜合表現較佳的平台是 GG-01，因為其 營收規模排名較高；營收相對庫存效率 proxy 較高；目前未見同月異常訊號，health_score 為 0.97。`
- Actual key observations:
  - `平台 scorecard 綜合營收規模、營收動能、營收相對庫存效率 proxy 與異常訊號；最佳候選為 GG-01，health_score=0.97，需優先注意 GG-06。`
  - `GG-02 的營收/庫存金額 proxy 為 0.63，代表在目前資料中營收相對庫存效率偏弱。`
  - `GG-02 的營收/庫存金額 proxy 為 0.54，代表在目前資料中營收相對庫存效率偏弱。`
- Missing item: `不應以庫存金額最高`
- Failure reason: wording mismatch / overly prescriptive expectation. The answer avoids the forbidden inventory-only rationale and positively states the scorecard basis instead.
- Suggested handling: fix eval expectation.
- Applied change: `不應以庫存金額最高` -> `綜合表現較佳`

### answer_048

- Question: `請分析哪個平台表現較差`
- Task family: `performance_assessment`
- Expected must_include before review: `GG-02`, `營收/庫存效率 proxy`
- Actual headline: `結論：目前表現較弱的平台優先看 GG-06，因為其 同月異常訊號 1 筆；營收相對庫存效率 proxy 排名偏後；營收動能相對偏弱，health_score 為 0.13。`
- Actual key observations:
  - `平台 scorecard 綜合營收規模、營收動能、營收相對庫存效率 proxy 與異常訊號；最佳候選為 GG-01，health_score=0.97，需優先注意 GG-06。`
  - `GG-02 的營收/庫存金額 proxy 為 0.63，代表在目前資料中營收相對庫存效率偏弱。`
  - `GG-02 的營收/庫存金額 proxy 為 0.54，代表在目前資料中營收相對庫存效率偏弱。`
- Missing item: `營收/庫存效率 proxy`
- Failure reason: wording mismatch. The current answer uses `營收相對庫存效率 proxy`, which is more explicit and avoids presenting the proxy as formal turnover.
- Suggested handling: fix eval expectation.
- Applied change: `營收/庫存效率 proxy` -> `營收相對庫存效率 proxy`

## Recommendation

No core logic change is recommended in Phase 8F-2. The five failures were all exact-token mismatches where the answer already followed the intended routing, tool, and display-block behavior. Keep monitoring the duplicated performance-assessment cases because older expectations mix ratio-only wording with the newer scorecard framing.
