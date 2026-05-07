# V2 Plan

## 1. V2 目標

第二版的主軸不是繼續堆更多 AI 功能，而是把目前的 PoC 升級成一個更像企業分析系統的產品雛形。

核心目標如下：

1. 可測：能驗證工具、routing、答案是否正確。
2. 可追：每個回答都能追到資料範圍、工具來源與限制。
3. 可維護：降低重複前端與過度複雜的 multi-agent 維護成本。
4. 可擴充：保留 `AnalysisToolbox` 作為未來能力擴展的基礎。

一句話定義：

> 從「可展示的 AI 問答 POC」，升級為「可驗證、可追溯、可維護的企業營運分析助理」。

## 2. 現況摘要

目前資料流如下：

```text
Excel 原始資料
   ↓
data_loader / preprocess
   ↓
mapping_parser
   ↓
analyzer
   ↓
AnalysisArtifacts / PipelineContext
   ↓
AnalysisToolbox
   ↓
API / Chart / Observe / AI 問答
   ↓
Desktop UI + Mobile UI
```

這個結構裡，最值得保留的是：

- `AnalysisToolbox`
- `PipelineContext`
- `AnalysisArtifacts`
- contract-first 的資料載入方式
- request_id 與 domain log

目前最主要的問題是：

1. AI 問答還缺少完整測試框架。
2. multi-agent 結構對目前資料型問題可能過重。
3. 資料刷新、版本與 health 機制不夠產品化。
4. `frontend/` 與 `mobile-demo/` 重複維護。
5. Excel schema 太硬，缺少 drift 處理。

## 3. 設計原則

第二版實作時，建議遵守以下原則：

1. 先驗證，再擴功能。
2. 先做減法，再做加法。
3. 先穩定 deterministic tools，再優化 AI 回答。
4. 回答必須 evidence-first，而不是語氣優先。
5. 所有新能力都應能被測試與評估。

## 4. 建議修正順序

### Phase 0: Baseline Cleanup

#### 目標

先把目前系統收斂成一個可評估的固定基線。

#### 內容

1. 修正亂碼、過時文件與命名歧義。
2. 固定資料版本與測試資料集。
3. 定義統一回答最小欄位。
4. 清掉舊 demo 與重複入口殘留。

#### 建議輸出

- 穩定的 baseline branch 或 baseline tag
- 文件更新後的啟動與架構說明
- 統一回答欄位草案

#### Done Criteria

- `8765` 只作為 API
- `3000` / `3001` 入口清楚
- 文件不再提到舊版 web demo
- 至少一份固定資料版本可供後續 eval 使用

### Phase 1: Evaluation First

#### 目標

先證明這套系統回答是可測的，不是只會生成看起來合理的句子。

#### 優先度

最高優先。

#### 內容

1. 建立 deterministic tools 測試。
2. 建立 router / intent 測試集。
3. 建立答案正確性測試集。
4. 建立 hallucination 與 unsupported question 測試。

#### 建議新增目錄

```text
eval/
  questions_router.jsonl
  questions_answer.jsonl
  run_eval.py
  eval_report.md
  eval_results.csv

tests/
  test_analysis_tools.py
  test_router.py
  test_answer_contract.py
```

#### 工具層測試範圍

至少覆蓋：

- `get_top_groups`
- `get_anomalies`
- `get_chart_payload`
- `get_observation_table`
- `get_data_coverage`

#### Router 測試欄位建議

每題可記錄：

```json
{
  "id": "sales_001",
  "question": "最新月份哪個新事業群營收最高？",
  "expected_domain": "sales",
  "expected_tools": ["get_top_groups"],
  "expected_filters": {
    "month": "latest"
  }
}
```

#### Answer 測試欄位建議

```json
{
  "id": "answer_001",
  "question": "最新月份哪個新事業群營收最高？",
  "must_include": ["最新月份", "營收", "新事業群"],
  "must_not_include": ["一定會", "因為市場需求", "外部環境"],
  "expected_answer_type": "ranking"
}
```

#### 核心指標

- `tool_correctness`
- `domain_accuracy`
- `tool_accuracy`
- `filter_extraction_accuracy`
- `answer_grounding_score`
- `hallucination_rate`
- `unsupported_question_rejection_rate`

#### 題庫規模建議

- 營收查詢：10 題
- 庫存查詢：10 題
- 異常偵測：10 題
- 圖表問題：5 題
- 資料範圍問題：5 題
- 無法回答問題：5 題

合計先做 45 題左右。

#### Done Criteria

- deterministic tools 有自動化測試
- router 題庫可批次跑
- answer 題庫可批次跑
- 能產出 eval report
- 能列出 hallucination cases 與 routing confusion cases

### Phase 2: Evidence-First Answer Contract

#### 目標

把 AI 回答從自由文字整理成可追溯格式。

#### 內容

每次回答至少統一為以下欄位：

- `answer`
- `evidence`
- `tools_used`
- `data_scope`
- `limitations`
- `suggested_followups`

#### 回答層級建議

1. Level 1：資料可直接回答
2. Level 2：只能觀察，不能主張因果
3. Level 3：資料不足，必須拒答或轉向

#### 範例

Level 1：

> 根據目前資料，最新月份營收最高的是 A 事業群，營收為 xx。

Level 2：

> 資料顯示 A 事業群營收下降且庫存上升，但目前資料不足以判斷原因。

Level 3：

> 目前系統沒有訂單、客戶或市場需求資料，因此無法直接解釋營收下降原因。

#### Done Criteria

- `POST /api/ask` 回傳格式穩定
- 每個回答都附帶 `tools_used` 與 `limitations`
- answer eval 可檢查 must include / must not include
- 明顯降低過度推論

### Phase 3: 收斂 Multi-Agent 為企業型分析流水線

#### 目標

先不要再增加 agent，而是把目前邏輯收斂成清楚分層。

#### 建議邏輯分層

```text
Question Understanding Layer
   ↓
Tool Planning Layer
   ↓
Evidence Execution Layer
   ↓
Answer Generation Layer
   ↓
Evaluation & Logging Layer
```

#### 說明

這不代表一定要把現有 `multi_agent.py` 整個刪掉，而是要先把責任明確化：

- 問題理解
- 工具選擇
- 工具執行
- 回答合成
- 評估與日誌

#### 重構方向

1. 弱化過度擬人化的 agent 邊界。
2. 保留 domain 能力，但不要讓 domain 成為維護負擔。
3. 將 router、tool planning、answer synthesis 日誌清楚分層。
4. 讓評估框架能直接對各層輸出打分。

#### Done Criteria

- 日誌能分辨 question understanding / tool planning / execution / synthesis
- routing 錯誤能快速定位到哪一層
- 問答延遲與 debug 成本下降

### Phase 4: Data Refresh / Data Version / Data Quality

#### 目標

讓系統知道自己在用哪一版資料，並能安全刷新。

#### 建議新增 API

- `/api/data-version`
- `/api/reload-data`
- `/api/health`
- `/api/pipeline-status`
- `/api/data-quality`

#### 回答應附帶資訊

- 資料版本
- 最後更新時間
- 使用資料範圍

#### 資料品質能力

1. schema validation report
2. mapping quality report
3. missing column fallback
4. 欄位別名表

#### 欄位別名示意

```text
實際營收 = ["實際營收", "Revenue", "營收金額", "Actual Revenue"]
新事業群 = ["新事業群", "合併事業群", "BG", "Business Group"]
```

#### Done Criteria

- API 可回傳資料版本資訊
- 可安全 reload pipeline context
- 有 data quality report
- schema drift 不會直接讓系統整體失效

### Phase 5: Frontend Consolidation

#### 目標

將桌機版與手機版前端合併為單一 Next.js app，降低重複程式碼與維護成本。

#### 目標結構

```text
frontend/
  app/
    dashboard/
    mobile/
    api/
  components/
    charts/
    chat/
    kpi/
  lib/
    python-api.js
```

#### 合併方向

1. 共用一份 `package.json`
2. 共用 API proxy
3. 共用 chart component
4. desktop / mobile 用 route 或 responsive layout 區分

#### 不建議

- 繼續維護兩套幾乎相同的 Next.js app
- chart component 各寫一份
- proxy helper 各寫一份

#### Done Criteria

- 只保留一個 Next.js app
- `dashboard` 與 `mobile` 共用 components 與 proxy
- chart rendering 邏輯只保留一份主實作

### Phase 6: 工具層擴充

#### 目標

在評估與資料追溯機制穩定之後，再擴工具層能力。

#### 優先新增順序

1. `get_risk_alerts`
2. `get_root_cause_candidates`
3. `get_yoy_mom_breakdown`
4. `get_contribution_analysis`
5. `get_inventory_turnover_proxy`
6. `get_executive_briefing`

#### 原因

- `get_risk_alerts` 最直接支援主管視角
- `get_root_cause_candidates` 能補強診斷型問答
- `get_yoy_mom_breakdown` 與 `get_contribution_analysis` 提升分析精度
- `get_executive_briefing` 可直接餵給 mobile / executive mode

#### Done Criteria

- 每個新增工具都有 deterministic test
- 每個新增工具都能被 router / answer eval 覆蓋
- 每個新增工具都有明確 supported filters 與 output contract


## 5. 第二版建議里程碑順序

建議依以下順序執行：

1. `Phase 0: Baseline Cleanup`
2. `Phase 1: Evaluation First`
3. `Phase 2: Evidence-First Answer Contract`
4. `Phase 3: 收斂 Multi-Agent 為企業型分析流水線`
5. `Phase 4: Data Refresh / Data Version / Data Quality`
6. `Phase 5: Frontend Consolidation`
7. `Phase 6: 工具層擴充`

## 6. 每階段交付物

### V2-0

- baseline 文件整理
- 穩定啟動流程
- 統一回答欄位草案

### V2-1

- `tests/test_analysis_tools.py`
- `eval/questions_router.jsonl`
- `eval/questions_answer.jsonl`
- `eval/run_eval.py`
- `eval_report.md`

### V2-2

- 新版 answer contract
- 不確定性模板
- grounding / hallucination 規則

### V2-3

- 簡化後的 router / planner / executor / synthesizer 分層
- 分層 log

### V2-4

- `/api/data-version`
- `/api/reload-data`
- `/api/health`
- `/api/pipeline-status`
- `/api/data-quality`
- schema validation report

### V2-5

- 合併後的單一 Next.js app
- 共用 API proxy
- 共用 chart components

### V2-6

- 新增工具與對應測試
- 擴充 chart / observe / answer coverage

### V2-7

- audience-aware answer format
- executive mode / analyst mode

## 7. 驗收指標建議

### Evaluation 指標

- Routing Accuracy
- Tool Accuracy
- Filter Extraction Accuracy
- Answer Grounding Score
- Hallucination Cases
- Unsupported Question Rejection Rate

### 產品化指標

- 回答是否附帶 data scope
- 回答是否附帶 limitations
- 是否能查到 request log
- 是否能知道資料版本
- 是否能安全 reload data

### 維護性指標

- 前端 app 數量是否減少為 1
- chart component 是否共用
- proxy helper 是否共用
- duplicated code 是否下降

