# 去識別化營收與庫存分析專案

## Stateful agent runtime

The default assistant now checkpoints plans, step execution, evidence validation, and deterministic repair. Set `AGENT_RUNTIME_MODE=legacy` for the prior path. See [Phase 1 runtime documentation](docs/PHASE1_STATEFUL_AGENT_RUNTIME.md).

Reproducible tests: `uv sync && uv run pytest -q`.

## Proactive investigation and approval

Phase 3 provides a one-shot proactive scan and a human approval gate: `uv run python -m proactive_workflow.cli scan`. It creates **NOT APPROVED** drafts and pending approvals only; it never auto-approves, publishes, emails, or modifies source Excel files. See [Phase 3 workflow](docs/PHASE3_PROACTIVE_INVESTIGATION.md), [approval policy](docs/HUMAN_APPROVAL_WORKFLOW.md), and [policy reference](docs/INVESTIGATION_POLICY_REFERENCE.md).

Revision is explicit and hash-bound: `create-revision ID --revised-by "name" --instructions "..."` creates a new pending draft version; caller identities are not authenticated. Persistent trend detection and frontend inbox remain intentionally out of scope.

## Semantic catalog and optional MCP

Phase 2 adds a versioned semantic catalog plus an optional, read-only stdio MCP server. It is not required by the CLI, HTTP API, or either agent-runtime mode. Validate it with `uv run python -m semantic_layer.validation`; regenerate its checked-in reference with `uv run python -m semantic_layer.generate_reference`. See [Phase 2 documentation](docs/PHASE2_SEMANTIC_LAYER.md), [catalog reference](docs/SEMANTIC_CATALOG_REFERENCE.md), and [MCP server notes](docs/MCP_SERVER.md).





這是一個可直接放入 Excel 檔後執行的通用 Python 分析框架，用來分析：

- `data/inventory.xlsx`
- `data/revenue.xlsx`
- `data/mapping.xlsx`

專案只根據你提供的欄位結構、格式規則與分類表設計，不預先讀取真實資料內容來反推邏輯，也不包含任何還原原始資料的處理。

## 功能

- 驗證必要欄位
- 將 `YYYYMM` 標準化為 `YYYY-MM`
- 以 A~I 欄位置解析 `mapping.xlsx`
- 整理新事業群、HQBU、平台與去識別化規則說明
- 嘗試建立 HQBU -> 平台候選對應
- 輸出趨勢、月增率、分布與異常偵測
- 輸出營收與庫存之間的關聯性分析
- 產出 Excel、Markdown 報告與 PNG 圖表
- 串接本機 Ollama `llama3.1:8b`
- 支援終端問答模式，回答分成「查找的資料 / 程式分析結果 / AI分析結果」
- 可自動生成一組可驗證趨勢與關聯性的測試 Excel

## 專案結構

```text
.
├─ data/
├─ output/
│  └─ charts/
├─ analyzer.py
├─ config.py
├─ data_loader.py
├─ llm_reporter.py
├─ main.py
├─ mapping_parser.py
├─ preprocess.py
├─ qa_engine.py
├─ requirements.txt
├─ README.md
├─ test_data_generator.py
├─ utils.py
└─ visualizer.py
```

## 安裝

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 執行

把 Excel 檔放到 `data/` 後執行：

```bash
python main.py
```

若要重建測試資料：

```bash
python main.py --generate-test-data
```

若要分析後直接進入終端問答：

```bash
python main.py --chat
```

## 輸出

執行後會產生：

- `output/cleaned_inventory.xlsx`
- `output/cleaned_revenue.xlsx`
- `output/parsed_mapping.xlsx`
- `output/merged_analysis.xlsx`
- `output/summary_metrics.xlsx`
- `output/analysis_report.md`
- `output/llm_explanation.md`
- `output/qa_transcript.md`（若使用 `--chat`）
- `output/charts/*.png`

## Ollama

預設設定：

- Base URL: `http://localhost:11434`
- Model: `llama3.1:8b`

若尚未啟動：

```bash
ollama serve
ollama pull llama3.1:8b
```

若 Ollama 無法連線，系統會自動輸出 fallback 版 `llm_explanation.md`，不會讓主流程崩潰。

## 分析原則

- 資料已去識別化，不能直接視為真實商業規模
- E/F/I 欄位屬於處理方式說明，不會用於還原原始值
- 適合觀察趨勢、相對變化、群組差異與異常訊號
- 若 HQBU 與平台無法可靠整合，報告會明確揭露限制

## 測試資料設計

測試資料包含以下可驗證情境：

- `GG-01`：營收與庫存同步穩定成長，適合測試正相關
- `GG-02`：庫存持續升高、營收走弱，適合測試異常與負向訊號
- `GG-03`：營收與庫存平穩，適合測試低波動案例
- `GG-04`：新品平台快速成長，適合測試強勁上升趨勢
- `GG-05`：季節性高峰，適合測試波峰波谷
- `GG-06`：營收下降但庫存仍高，適合測試風險提示

## Phase 4: Local Traces and Reliability Evaluation

Phase 4 adds optional local-only tracing and deterministic offline reliability evaluation. Content capture is disabled by default; never enable it in a company-data environment unless the privacy policy is reviewed.

```bash
uv run python -m observability.cli list-traces
uv run python -m evaluation.cli validate-datasets
uv run python -m evaluation.cli coverage
uv run python -m evaluation.cli run --suite all
uv run python -m evaluation.cli coverage --run-id EVAL_RUN
uv run python -m evaluation.cli report EVAL_RUN
uv run python -m evaluation.cli gate EVAL_RUN
uv run python -m evaluation.cli compare BASELINE_RUN CANDIDATE_RUN
```

See [Phase 4 trajectory evaluation](docs/PHASE4_TRAJECTORY_EVALUATION.md), [observability and privacy](docs/OBSERVABILITY_AND_PRIVACY.md), and the [reliability scorecard](docs/AGENT_RELIABILITY_SCORECARD.md).
