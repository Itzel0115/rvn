# Pipeline Architecture

## Purpose

本文件記錄目前 `Phase 3A` 完成後的企業型分析流水線架構。這份文件描述的是現在的穩定主線行為，不涉及新功能設計，也不改動 routing、API 欄位、eval 規則或 tools。

## End-to-End Data Flow

系統目前的整體資料流如下：

```text
Excel
  -> data_loader / preprocess
  -> mapping_parser
  -> analyzer
  -> AnalysisArtifacts / PipelineContext
  -> AnalysisToolbox
  -> MultiAgentAssistant
  -> API response
```

### Layer Summary

- `data_loader.py` / `preprocess.py`
  負責 Excel 載入、欄位標準化、數值與日期清理。
- `mapping_parser.py`
  負責將 mapping 檔整理成平台 / 事業群 / HQBU 等可分析結構。
- `analyzer.py`
  負責產生月度彙總、排行、異常、比值與其他分析 artifact。
- `AnalysisArtifacts / PipelineContext`
  作為分析後資料的共享上下文，提供給 toolbox 與 orchestrator。
- `AnalysisToolbox`
  提供 deterministic tools，讓上層問答流程以穩定工具輸出為主。
- `MultiAgentAssistant`
  負責 routing、domain dispatch、answer contract 生成與 API response 組裝。

## Q&A Pipeline Architecture

目前問答主線已整理成以下幾層：

1. `Question Understanding / Routing`
2. `Tool Planning / Evidence Execution`
3. `Answer Contract Generation`
4. `Response Assembly`
5. `Logging`

`MultiAgentAssistant.answer()` 現在是這條流水線的唯一穩定入口。

## Responsibility by Layer

### 1. Question Understanding / Routing

責任：

- 接收使用者問題
- 進行 deterministic + business-profile routing
- 套用必要的隱含篩選條件
- 產生統一的 `RoutingDecision`

對應 function：

- `_run_question_understanding()`
  問答主線的 routing 入口，負責記錄 `question_understanding.start / done` log。
- `_plan_and_route()`
  內部 routing 實作，先走 deterministic fallback，再視情況套 business question profile 或 LLM planning fallback。
- `_apply_implicit_latest_month_filter()`
  若題目明確要求 `最新月份 / 本月 / latest month`，且原始 filter 尚未帶 month，則補上 `latest_month`。

### 2. Tool Planning / Evidence Execution

責任：

- 根據 `routing.domains` 決定要 dispatch 哪些 domain agents
- 依序執行 domain agent，蒐集 evidence 與 warnings
- 維持目前既有 agents 與 tools 行為不變

對應 function：

- `_execute_domain_agents()`
  負責 orchestrator 層的 domain dispatch，記錄 `tool_execution.start / done`。

目前保留的 domain agents：

- `SalesAgent`
- `InventoryAgent`
- `FinancialMetricsAgent`
- `ChartAgent`
- `AssociationAgent`

### 3. Answer Contract Generation

責任：

- 根據不同 path 組裝 `answer_contract`
- 保持 evidence-first contract 結構一致
- 不改變既有 API contract 欄位

對應 function：

- `_build_overview_contract()`
  處理 overview path，回傳 `(contract, summary_payload)`。
- `_build_data_quality_contract()`
  處理 data quality path，內部呼叫 `build_data_quality_answer_contract()`。
- `build_answer_contract()`
  標準分析 path 的主 contract builder，定義在 [answer_contract.py](/C:/Users/itzel.hsiao/Desktop/revenue-poc/answer_contract.py)。

### 4. Response Assembly

責任：

- 統一整理 routing payload
- 將 contract render 成 `summary`
- 保持 API response 欄位穩定

對應 function：

- `_build_routing_payload()`
  將 `RoutingDecision` 轉成 API response 中的 `routing` 欄位。
- `_build_response_payload()`
  組裝最終 API response，包含：
  - `request_id`
  - `routing`
  - `summary`
  - `answer_contract`
  - `domain_results`
  - `project_summary`（僅 overview path）

### 5. Logging

責任：

- 讓 orchestrator 每一層都有明確進出點
- 讓 smoke / local debug / 後續可觀測性更清楚

目前已整理的 log event：

- `question_understanding.start`
- `question_understanding.done`
- `tool_execution.start`
- `tool_execution.done`
- `answer_generation.start`
- `answer_generation.done`
- `response_assembly.done`

## Three Answer Paths

目前 `MultiAgentAssistant.answer()` 內有三條穩定主線：

### 1. Overview Path

條件：

- `routing.question_type == "overview"`

流程：

1. `Question Understanding / Routing`
2. 不 dispatch domain agent
3. `_build_overview_contract()`
4. `_build_response_payload()`

特性：

- `domain_results` 為空
- response 會額外帶 `project_summary`

### 2. Data Quality Path

條件：

- `routing.question_type == "data_quality"`

流程：

1. `Question Understanding / Routing`
2. 不 dispatch domain agent
3. `_build_data_quality_contract()`
4. `_build_response_payload()`

特性：

- `domain_results` 為空
- 以資料涵蓋、mapping 與 pipeline messages 為主

### 3. Standard Analysis Path

條件：

- 除 `overview` 與 `data_quality` 之外的穩定問答主線

流程：

1. `Question Understanding / Routing`
2. `_execute_domain_agents()`
3. `build_answer_contract()`
4. `_build_response_payload()`

特性：

- 會保留各 domain 的 `domain_results`
- answer contract 仍是前端與 smoke 驗證的核心輸出

## answer_contract Field Semantics

目前 evidence-first answer contract 的主要欄位如下：

- `answer`
  產品化主回答，直接面向使用者。
- `evidence`
  支撐回答的結構化證據，供後續驗證與 trace 使用。
- `tools_used`
  這次回答實際依賴的 deterministic tools。
- `data_scope`
  回答所依據的範圍資訊，例如 question type、domains、filters、available months、latest month。
- `limitations`
  明確說明資料、推論與支援邊界。
- `suggested_followups`
  提供下一步可直接追問的問題方向。

## Logging Design

目前 logging 設計聚焦在 orchestrator 的主流程可觀測性。

### question_understanding.start / done

用途：

- 看出問題何時進入 routing
- 追蹤 routing 結果、domains、filters、subtasks

### tool_execution.start / done

用途：

- 看出是否進入 overview、data_quality 或 standard path
- 看出實際 dispatch 多少 domain results

### answer_generation.start / done

用途：

- 看出 contract 生成是否完成
- 看出 answer type、evidence 數量、tools_used 數量

### response_assembly.done

用途：

- 確認最終 response 已組裝完成
- 驗證回傳的 `domain_results` 數量

## Legacy Synthesis Functions

以下 functions 已非穩定主線，但暫時保留作為除錯與舊實驗相容用途：

- `_synthesize_final_answer()`
- `_compose_chart_answer()`
- `_compose_final_answer_fallback()`

目前穩定 answer path 已改以 `answer_contract.py` 與 `_build_response_payload()` 為主，因此這些 legacy functions 不再是 `answer()` 的正式輸出主線。

保留原因：

- 方便回看舊版 orchestration 實驗
- 方便除錯特定 chart / synthesis 行為
- 降低第一輪 refactor 風險，避免大規模刪碼

## Validation Strategy

目前透過三種方式驗證行為穩定：

### 1. Unit Tests

執行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

用途：

- 驗證 toolbox
- 驗證 router
- 驗證 answer contract

### 2. Eval

執行：

```powershell
.\.venv\Scripts\python.exe eval\run_eval.py
```

用途：

- 驗證 routing accuracy
- 驗證 answer grounding
- 驗證 unsupported question rejection
- 驗證 must include / must not include 與 filter scope

### 3. Smoke Test

執行：

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test_api.py
```

用途：

- 透過真實 `/api/ask` 驗證 API response
- 驗證 routing、tools_used、answer_type、limitations 與 answer 是否維持穩定

## Known Limitations

- eval 目前測的是 deterministic fallback 行為，不代表完整 LLM 自由回答能力。
- `multi_agent.py` 目前仍偏大，未來可再拆出 orchestrator / domain_agents / routing 層。
- data version / reload / health API 尚未進入 `Phase 4`。
