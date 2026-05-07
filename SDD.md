# Software Design Description

## 1. 文件目的

本文件描述「營收去識別化先驗測試」專案目前可觀察到的實作設計，並在此基礎上補上兩個未來延伸方向：

- 依 `CEO iPhone 營運儀表板 PRD（含 Semantic KPI Layer 設計）` 推導較正式的 API 形式
- 評估未來導入 NVIDIA GB10 / DGX Spark 等桌上型 Grace Blackwell 環境時，哪些元件適合搬移、如何驗證效益

本文件以目前 repo 內程式碼為主，不把尚未落地的理想架構誤寫成既有能力。

## 2. 系統目標

本專案目前是一套以 Excel 為輸入、以 Python 分析管線為核心、並提供問答與 Web Demo 的去識別化營收/庫存分析系統。其主要目標為：

- 將 `inventory.xlsx`、`revenue.xlsx`、`mapping.xlsx` 轉為可分析資料集
- 在資料去識別化前提下輸出趨勢、排行、異常、相關分析
- 將分析結果封裝為可重用的 Tool Layer
- 透過 multi-agent 與 Web UI 讓使用者以自然語言取得分析結論
- 保持 LLM 不可用時的 deterministic fallback 能力

## 3. 目前系統邊界

### 3.1 In Scope

- Excel 匯入與欄位檢核
- 日期與數值清洗
- mapping 結構化解析
- 事業群 / HQBU / 平台對應整理
- 匿名化規則摘要
- 月營收、月庫存金額、月庫存 QTY 分析
- 事業群排行
- 平台層級的部分整合分析
- 規則式異常偵測
- 相關分析
- Markdown / Excel / 圖表輸出
- CLI 問答
- Multi-agent 問答
- 本機 Python HTTP API 與前端 Demo

### 3.2 Out of Scope

- 正式生產級 API gateway
- 正式認證授權與多租戶
- 交易明細層級 association rules
- SKU / 商品粒度分析
- 完整財報、毛利、費用、現金流分析
- SLA、HA、監控告警、正式部署腳本

## 4. 原始碼與責任分層

目前程式實際上可分成 5 層：

1. Data Ingestion Layer
2. Analysis Layer
3. Tool Layer
4. Orchestration Layer
5. Delivery Layer

### 4.1 Data Ingestion Layer

負責讀取與標準化原始 Excel。

- `data_loader.py`
- `mapping_parser.py`
- `preprocess.py`
- `config.py`

核心責任：

- 驗證必要欄位存在
- 將日期標準化為月份欄位
- 解析 mapping A~I 欄位位置語意
- 建立事業群、HQBU、平台與規則資料表
- 嘗試建立 HQBU -> 平台 bridge candidates

### 4.2 Analysis Layer

負責分析資料與產出 artifacts。

- `analyzer.py`
- `visualizer.py`
- `qa_engine.py`

核心責任：

- enrich inventory / revenue
- 月彙總
- 群組彙總
- 平台整合
- 異常偵測
- 相關分析
- 報表上下文與圖表資料生成

### 4.3 Tool Layer

負責把 artifacts 轉成穩定查詢工具。

- `analysis_pipeline.py`
- `analysis_tools.py`

核心責任：

- 建立 `PipelineContext`
- 封裝資料涵蓋範圍、表格、排行、異常、相關與圖表查詢
- 對外暴露一致的輸入輸出格式

### 4.4 Orchestration Layer

負責理解問題、路由到對應 agent、彙整答案。

- `multi_agent.py`
- `ollama_client.py`
- `llm_reporter.py`

核心責任：

- 問題分類與 routing
- 條件抽取
- domain agent tool planning
- domain result synthesis
- LLM fallback

### 4.5 Delivery Layer

負責 CLI 與 Web 交付。

- `main.py`
- `demo_web.py`
- `frontend/app/*`
- `frontend/components/*`
- `frontend/lib/python-api.js`

核心責任：

- CLI 模式啟動
- 本機 HTTP API
- Next.js proxy route
- Dashboard / chat UI 呈現

## 5. 主要資料契約

### 5.1 輸入檔案

- `data/inventory.xlsx`
- `data/revenue.xlsx`
- `data/mapping.xlsx`

### 5.2 主要欄位契約

`config.py` 已集中管理欄位常數，這是目前 repo 內少數已明確成形的 schema contract。

Inventory 必要欄位：

- `日期`
- `HQBU`
- `金額`
- `QTY`
- `新事業群`

Revenue 必要欄位：

- `日期`
- `平台`
- `營收`
- `新事業群`

Mapping A~I 位置契約：

- `事業群名稱`
- `事業群代碼`
- `庫存HQBU分類名稱`
- `庫存HQBU代碼`
- `金額處理方式`
- `QTY處理方式`
- `營收平台分類名稱`
- `營收平台代碼`
- `實際營收處理方式`

### 5.3 主要分析 artifacts

`AnalysisArtifacts` 目前包含：

- `inventory_enriched`
- `revenue_enriched`
- `monthly_revenue`
- `monthly_inventory_amount`
- `monthly_inventory_qty`
- `revenue_by_group`
- `inventory_by_group`
- `merged_analysis`
- `platform_monthly_analysis`
- `anomalies`
- `correlation_analysis`
- `summary_metrics`
- `report_context`

### 5.4 PipelineContext

`PipelineContext` 是目前系統最接近 application state container 的物件，包含：

- inventory / revenue 欄位檢查結果
- 原始 DataFrame
- `ParsedMapping`
- `AnalysisArtifacts`
- message collector
- supported domains
- source files

## 6. 執行流程

目前主流程可描述如下：

1. `main.py` 建立輸出目錄並解析 CLI 參數
2. `data_loader.py` 讀取 inventory / revenue / mapping
3. `mapping_parser.py` 解析 mapping 並建立 bridge candidates
4. `analyzer.py` 建立 enrich 後資料與分析 artifacts
5. `visualizer.py` 產出圖表
6. `main.py` 輸出 Excel / Markdown / chart 檔案
7. `llm_reporter.py` 嘗試產出 LLM 解說，失敗則 fallback
8. 若為 agent/web 模式，`analysis_pipeline.py` 建立可重用 context
9. `analysis_tools.py` 提供 table / chart / anomaly / correlation 等工具
10. `multi_agent.py` 根據問題路由到 Sales / Inventory / Financial / Association 等 agent

## 7. 目前對外介面

### 7.1 CLI 介面

`main.py` 支援：

- `python main.py`
- `python main.py --chat`
- `python main.py --agent-question "..."`
- `python main.py --agent-project-summary`
- `python main.py --agent-json`

### 7.2 Python HTTP API

`demo_web.py` 目前提供：

- `GET /api/summary`
- `GET /api/chart-catalog`
- `POST /api/chart`
- `POST /api/ask`

這組 API 的定位仍是 PoC backend for frontend，不是正式產品 API。

### 7.3 Next.js BFF Proxy

`frontend/app/api/*/route.js` 只是把 request proxy 到 `http://127.0.0.1:8765`，因此現況其實是雙層 API：

- Next.js route 作為 browser 端入口
- Python server 作為真正分析執行端

## 8. 目前架構優點

- 核心分析流程與問答流程已分層，便於重用
- `PipelineContext` 與 `AnalysisToolbox` 已形成可再封裝 API 的基礎
- multi-agent 與 deterministic fallback 並存，適合 PoC 與展示
- 前端已與 Python 分離，未來可更換成正式 API service
- 欄位常數集中於 `config.py`，避免 schema 漂移完全失控

## 9. 目前架構缺口

### 9.1 缺正式 API 契約

現在的 `/api/summary`、`/api/chart`、`/api/ask` 比較像畫面服務，不是產品層 API。若要接 CEO iPhone dashboard，還缺：

- KPI card contract
- metric summary contract
- trend contract
- breakdown contract
- metadata / dimension registry
- auth / audit / versioning

### 9.2 缺真正的 Semantic KPI Layer

目前專案有：

- 欄位契約
- 分析 artifacts
- tool abstraction

但尚未有：

- 統一 KPI registry
- KPI 定義版本
- KPI 計算口徑 metadata
- dimension dictionary
- drill-down hierarchy
- SSOT 對外查詢層

### 9.3 Web 仍偏 Demo

前端已可展示摘要、圖表、問答，但仍偏向「分析工作台」，不是為 CEO iPhone dashboard 設計的 product surface。缺少：

- 手機導向資訊密度控制
- KPI first 的卡片化資料模型
- 快速 drill-down navigation
- 固定 latency 預算
- 使用者權限與快取策略

## 10. 依 PRD 推導的未來目標架構

根據你提供的 PRD，可推導出未來較合理的目標是：

1. Excel / upstream data 經 ETL 後進入標準化分析層
2. 在標準化分析層之上建立 Semantic KPI Layer
3. iPhone App、Power BI、LLM Agent 共用同一個 KPI 語意層
4. App 走低延遲 API，Power BI 走 semantic model / BI route，LLM 走 metric registry + tool adapter

這會把目前「analysis artifacts + toolbox」提升為更正式的「semantic service」。

## 11. 建議的 API 形式

### 11.1 API 設計原則

- API 不直接暴露原始 Excel 欄位語意
- 對外以 metric、dimension、period、comparison 為核心
- KPI 卡片與趨勢資料分離
- 所有 response 帶 `definition_version` 與 `last_updated_at`
- 所有 metric 可追到定義、公式、限制與 drill-down 支援範圍

### 11.2 建議的資源模型

核心資源：

- `metrics`
- `dimensions`
- `kpi_cards`
- `timeseries`
- `breakdowns`
- `anomalies`
- `insights`
- `definitions`

### 11.3 建議的 REST API

首頁與卡片：

- `GET /v1/dashboard/home`
- `GET /v1/kpi/cards`
- `GET /v1/kpi/{metric_key}/summary`

趨勢與拆解：

- `GET /v1/kpi/{metric_key}/trend`
- `GET /v1/kpi/{metric_key}/breakdown`
- `GET /v1/kpi/{metric_key}/distribution`

異常與洞察：

- `GET /v1/anomalies`
- `GET /v1/insights/executive`
- `POST /v1/ask`

語意層 metadata：

- `GET /v1/metrics`
- `GET /v1/metrics/{metric_key}`
- `GET /v1/dimensions`
- `GET /v1/dimensions/{dimension_key}`

### 11.4 建議 request 參數

共用查詢參數建議為：

- `period=2026-04`
- `from=2025-01`
- `to=2026-04`
- `grain=month`
- `group_by=platform`
- `group_code=12`
- `platform=P01`
- `comparison=prev_month|prev_year|target`
- `limit=10`

### 11.5 建議 response contract

KPI card：

```json
{
  "metric_key": "monthly_revenue",
  "label": "Monthly Revenue",
  "period": "2026-04",
  "value": 123456.0,
  "formatted_value": "123,456",
  "unit": "currency_proxy",
  "delta": {
    "vs_prev_month": 0.082,
    "vs_prev_year": 0.153,
    "absolute": 9370.0
  },
  "sparkline": [110000, 112500, 123456],
  "status": "normal",
  "definition_version": "2026.04.1",
  "last_updated_at": "2026-04-16T10:30:00+08:00"
}
```

Trend：

```json
{
  "metric_key": "monthly_revenue",
  "grain": "month",
  "series": [
    { "period": "2026-02", "value": 110000.0 },
    { "period": "2026-03", "value": 112500.0 },
    { "period": "2026-04", "value": 123456.0 }
  ],
  "comparison": {
    "mode": "prev_month",
    "series": [null, 0.023, 0.097]
  },
  "definition_version": "2026.04.1"
}
```

Breakdown：

```json
{
  "metric_key": "monthly_revenue",
  "period": "2026-04",
  "group_by": "platform",
  "items": [
    { "key": "P01", "label": "平台 A", "value": 42000.0, "share": 0.34 },
    { "key": "P02", "label": "平台 B", "value": 31500.0, "share": 0.25 }
  ],
  "definition_version": "2026.04.1"
}
```

Metric definition：

```json
{
  "metric_key": "monthly_revenue",
  "label": "Monthly Revenue",
  "description": "依月份彙總之營收代理指標",
  "owner": "finance-analytics",
  "unit": "currency_proxy",
  "grain": ["month"],
  "dimensions": ["group_code", "platform"],
  "formula": "sum(revenue)",
  "limitations": [
    "資料已去識別化，不代表真實商業規模",
    "部分平台與 HQBU 對應可能非一對一"
  ],
  "definition_version": "2026.04.1"
}
```

## 12. 建議的 Semantic KPI Layer

### 12.1 最小可行結構

先不要一次導入大型 semantic platform，可先在現有 repo 上建立三層：

1. `metric_registry`
2. `query_service`
3. `presentation_api`

`metric_registry` 建議欄位：

- `metric_key`
- `label`
- `description`
- `owner`
- `source_artifact`
- `aggregation`
- `grain`
- `supported_dimensions`
- `comparison_modes`
- `formula_note`
- `definition_version`
- `limitations`

### 12.2 與現有程式的映射

現有元件可直接映射為：

- `AnalysisArtifacts` -> semantic source tables
- `AnalysisToolbox.get_metric_table()` -> query service prototype
- `get_chart_catalog()` / `get_chart_payload()` -> presentation service prototype
- `MultiAgentAssistant` -> semantic-aware insight layer

### 12.3 不建議直接沿用的部分

以下元件不應直接當正式產品 API：

- `demo_web.py` 的單體 HTTP handler
- `summary` 類 response 的自由格式文字
- domain agent 直接輸出的 narrative 結果

原因是這些輸出對前端穩定性與版本控制不夠友善。

## 13. 對 CEO iPhone dashboard 的落地建議

### 13.1 建議首頁資料組合

首頁只保留 3 到 5 張 KPI cards：

- `monthly_revenue`
- `ytd_revenue`
- `revenue_vs_target`（若未來有 target）
- `inventory_value`
- `inventory_turn_proxy` 或 `revenue_inventory_ratio`

### 13.2 建議 drill-down 路徑

- Home
- KPI Summary
- Trend
- Breakdown by platform
- Breakdown by group
- Anomaly detail

### 13.3 建議查詢策略

- KPI cards 預先計算並快取
- Trend / breakdown 允許即時計算
- 問答與 insight 走較慢路徑，與首頁卡片分流

## 14. GB10 導入規劃

### 14.1 我對 GB10 的假設

此處以 NVIDIA GB10 Grace Blackwell Superchip / DGX Spark 類桌上型 AI 設備為前提。NVIDIA 官方目前描述 DGX Spark 搭載 GB10、128 GB 記憶體，定位為本地原型、微調與推論設備。[來源 1](https://www.nvidia.com/en-eu/project-digits/)

### 14.2 適合搬到 GB10 的元件

最適合搬移的是「模型推論與模型輔助處理」，不是整個專案一次硬搬。

優先搬移：

- `ollama_client.py` 背後的本地模型推論
- `llm_reporter.py` 的報告生成
- `multi_agent.py` 中的 tool planning / result synthesis
- 未來的 anomaly summarization / narrative insight generation
- 未來的 embedding / reranking / semantic retrieval

可視情況搬移：

- pandas 分析前處理中的部分向量化運算
- 圖表渲染前的高成本資料轉換

不建議優先搬移：

- 純 Excel 讀取
- 純 pandas groupby aggregation
- HTTP routing / BFF
- 一般 metadata API

原因是這些部分的瓶頸大多不在 GPU。

### 14.3 導入後可能改善的面向

速度可能改善：

- 本地較大模型的 token/sec
- agent routing 與多輪摘要延遲
- 長報告生成
- 問答中多次工具結果整合

品質可能改善：

- 可從更小的 `gemma4:e4b` / 8B 級模型升到更強的本地模型
- 更穩定的 structured output
- 更好的中文摘要與跨工具整合能力
- 更好的 anomaly explanation 與 executive tone

### 14.4 速度不一定會變快的部分

- 小資料量 pandas 分析
- 單次簡短問答
- 純規則式 anomalies
- 單純 chart catalog 查詢

如果工作負載主要在 CPU / I/O，GB10 不會自然帶來明顯收益。

## 15. 更好模型是否一定提升速度與品質

不一定，需拆開看：

- 更大模型通常提升答案品質、穩定性與推理能力
- 更大模型可能提高單次延遲與記憶體壓力
- 若 GB10 讓更大模型可在本地順暢推論，則可能同時提升品質，並把原本「不可用」變成「可接受延遲」

因此正確問題不是「更好的模型會不會更快」，而是：

- 在你的工作負載下，最佳的 quality/latency/cost 組合是什麼

## 16. GB10 驗證方法

### 16.1 建議建立三組 benchmark

1. Pipeline benchmark
2. API benchmark
3. LLM benchmark

### 16.2 Pipeline benchmark

量測：

- `build_pipeline_context()` 總耗時
- `analyze_data()` 耗時
- 各 artifacts 產出耗時
- chart render 耗時

目的：

- 確認哪些部分其實不是 LLM bottleneck

### 16.3 API benchmark

量測：

- `/api/summary` p50 / p95
- `/api/chart` p50 / p95
- 未來 `/v1/kpi/cards`、`/trend`、`/breakdown` p50 / p95

目的：

- 確認行動端首頁是否能穩定壓在目標延遲

### 16.4 LLM benchmark

固定同一批 prompt：

- project summary
- anomaly explanation
- executive insight
- chart-aware QA

量測：

- first token latency
- total latency
- token/sec
- JSON parse success rate
- hallucination / unsupported claim rate
- answer completeness

比較矩陣建議：

- 現行本機模型
- GB10 上較大模型
- 必要時再加雲端模型作上限基準

### 16.5 驗收標準建議

- 首頁 KPI API p95 < 1 秒
- trend / breakdown API p95 < 2 秒
- 一般問答 p95 < 5 秒
- 結構化 JSON 成功率 >= 95%
- 針對同一批題目，人工評分品質提升達可感知門檻

## 17. 建議的分階段落地路徑

### Phase 1：整理現況

- 固化 `metric_registry`
- 將 `AnalysisToolbox` 拆成 query service
- 將 `demo_web.py` API 與產品 API 分離

### Phase 2：做正式 KPI API

- 新增 `/v1/kpi/cards`
- 新增 `/v1/kpi/{metric}/summary|trend|breakdown`
- 統一定義版本與 metadata contract

### Phase 3：做 CEO iPhone surface

- 手機導向首頁
- 卡片快取
- anomaly 與 trend drill-down

### Phase 4：導入 GB10

- 先搬 LLM 推論
- 再評估 embedding / reranking / summarization
- 最後才考慮更深的加速與本地模型治理

## 18. 結論

目前專案已具備從 Excel 到分析 artifacts、再到 Tool Layer、multi-agent、Web Demo 的完整 PoC 鏈路。若要走向 CEO iPhone dashboard，真正需要補的不是更多圖表，而是：

- 正式化的 KPI API 契約
- 可版本化的 Semantic KPI Layer
- 卡片化、低延遲、可 drill-down 的 delivery model

GB10 的最佳切入點則是 LLM 與 semantic insight 相關工作負載，而非整個 pandas/Excel 分析流程。先把 API 與 KPI registry 做乾淨，再導入更強本地模型，效益會最大。
