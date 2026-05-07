# API Status Endpoints

## Purpose

`Phase 4A` 與 `Phase 4B` 提供一組唯讀狀態 API，讓系統可以說明：

- API 是否正常提供服務
- 目前載入的是哪一版資料
- pipeline 是否有 warnings / errors
- 目前資料品質與 mapping 狀態如何

本輪仍然是 read-only status/report endpoints，不包含 `/api/reload-data`、schema drift 大重構或前端整合調整。

## Endpoints

### `GET /api/health`

用途：

- 回報 API 是否正常
- 回報 pipeline 是否已載入
- 提供簡短健康摘要

回傳欄位：

- `status`
  `ok | warning | error`
- `api`
  固定為 `"ok"`
- `pipeline_loaded`
  `true / false`
- `supported_domains`
- `latest_month`
- `warning_count`
- `error_count`

### `GET /api/data-version`

用途：

- 回報目前資料版本的 deterministic 描述
- 提供月份範圍、列數與 mapping 基本狀態

回傳欄位：

- `data_version`
  例如：`months_2024-01_to_2024-08_rev48_inv48_map6`
  若沒有月份資料，則回傳 `no_data`
- `available_months`
- `latest_month`
- `revenue_rows`
- `inventory_rows`
- `mapping_rows`
- `mapping_success`
- `supported_domains`
- `source_files`

### `GET /api/pipeline-status`

用途：

- 提供 pipeline messages 的原始狀態
- 讓外部直接檢查 infos / warnings / errors 與數量

回傳欄位：

- `status`
- `infos`
- `warnings`
- `errors`
- `info_count`
- `warning_count`
- `error_count`
- `latest_month`
- `available_months`

### `GET /api/data-quality`

用途：

- 用更產品化的格式整理資料品質狀態
- 同時整合資料版本、row counts、mapping 狀態、pipeline messages、quality checks 與 limitations

回傳欄位：

- `status`
- `data_version`
- `available_months`
- `latest_month`
- `row_counts`
  - `revenue`
  - `inventory`
  - `mapping`
- `mapping`
  - `mapping_success`
  - `business_group_count`
  - `inventory_hqbu_mapping_count`
  - `revenue_platform_mapping_count`
  - `bridge_candidate_count`
- `pipeline_messages`
  - `infos`
  - `warnings`
  - `errors`
- `quality_checks`
  每筆包含：
  - `name`
  - `status`
  - `message`
- `limitations`

## Status Derivation Logic

狀態判斷邏輯如下：

1. 若有 `errors`，則 `status = "error"`
2. 若沒有 `errors`，但有 `warnings`，則 `status = "warning"`
3. 若都沒有，則 `status = "ok"`

這個邏輯適用於：

- `/api/health`
- `/api/pipeline-status`
- `/api/data-quality`

## Shared Helper Logic

目前後端將共用狀態計算整理成 helper，定義在 [demo_web.py](/C:/Users/itzel.hsiao/Desktop/revenue-poc/demo_web.py)：

- `derive_health_status(messages)`
- `build_data_version_payload(context, toolbox)`
- `build_pipeline_status_payload(context, toolbox)`
- `build_data_quality_payload(context, toolbox)`

這樣可以避免每個 endpoint 重複計算 coverage、message counts 與 status。

## Difference Between `/api/pipeline-status` and `/api/data-quality`

`/api/pipeline-status` 偏向原始系統狀態：

- 保留 `infos / warnings / errors`
- 著重 pipeline 執行訊息與數量

`/api/data-quality` 偏向產品化資料品質報告：

- 除了 pipeline messages，還加入
  - `data_version`
  - `row_counts`
  - `mapping` 摘要
  - `quality_checks`
  - `limitations`

換句話說：

- `/api/pipeline-status` 比較像工程狀態頁
- `/api/data-quality` 比較像可直接給分析使用者閱讀的資料品質摘要

## Why This Round Still Does Not Include Reload

本輪刻意不做 `/api/reload-data`，原因如下：

- 先把唯讀狀態與資料品質查詢穩定化，降低 Phase 4 風險
- reload 會牽涉 pipeline context 生命週期、同步性、錯誤恢復與資料版本切換
- 目前優先需求是讓系統知道「自己載入了什麼資料」以及「資料品質是否有風險」

因此目前優先完成的是：

- 看得見資料版本
- 看得見 pipeline health
- 看得見 warnings / errors
- 看得見產品化 data quality report

後續若進入下一階段，再處理 reload-data、schema drift 與更完整的健康檢查能力。
