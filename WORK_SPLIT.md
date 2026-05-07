# 分工表

## 分工原則

以「資料分析主線」與「系統 / Agent 主線」分工，降低互相覆蓋與衝突。

## 人員 A：資料整合與分析深化

### 主要責任

- 維護 `mapping_parser.py`
- 維護 `analyzer.py`
- 擴充資料欄位與分析規則
- 強化 HQBU / 平台橋接邏輯
- 規劃異常偵測與預測模型
- 驗證分析結果合理性

### 交付物

- 新增分析欄位與指標
- 更完整的 mapping 規則
- 分析結果驗證文件
- 分析相關測試案例

## 人員 B：Multi-Agent、前端與平台化

### 主要責任

- 維護 `multi_agent.py`
- 維護 `analysis_tools.py`
- 維護 `demo_web.py` 與 `frontend/`
- 強化 prompt、routing、fallback 與回答整合
- 規劃 Git / 環境 / 文件 / 部署流程
- 補齊前端展示與使用流程

### 交付物

- 更穩定的 Agent 問答流程
- 前端展示優化
- 環境與部署文件
- 測試與協作流程文件

## 共用規範

- 共用 `pyproject.toml` 與 `uv.lock`
- 共用欄位命名與輸出格式
- 每週同步新增指標、限制與 warning
- 透過 Git branch 協作，不直接共用 working tree

---

## 人員 A：完工預期目標與驗收指標

### Milestone 1：HQBU ↔ 平台橋接修復（最高優先）

**完工目標：** `platform_monthly_analysis` 從空表變為有資料，Financial Agent 可正常回答平台相關問題。

**驗收指令：**
```bash
uv run python main.py --project-summary
```

| 驗收項目 | 通過條件 |
|----------|----------|
| `supported_domains["financial"]` | `true` |
| `get_platform_ratios` → `available` | `true` |
| `platform_monthly` artifact 列數 | ≥ 1 |
| warnings 中無「無法可靠對應平台」 | 不出現此訊息 |

**B 的後續動作：** 收到 A 的 commit 說明 `supported_domains["financial"]` 變 `true` 後，驗證 Financial Agent 回答不為空。

---

### Milestone 2：異常偵測完整版

**完工目標：** 異常偵測涵蓋平台層級，可依事業群 / 月份 filter，且至少包含兩種異常類型。

**驗收指令：**
```bash
uv run python main.py --agent-question "哪個事業群最近有異常？"
```

| 驗收項目 | 通過條件 |
|----------|----------|
| `get_anomalies(filters=QueryFilters(group_code="GG-01"))` | 回傳非空結果或明確說明無異常 |
| anomalies artifact 包含的異常類型 | 至少：月增率超標、庫存高但營收低 |
| Financial Agent 回答 | 含具體數字，不出現「資料不足」 |

---

### Milestone 3：分析結果驗證文件

**完工目標：** 提交一份 `ANALYSIS_VALIDATION.md`，說明分析結果與原始 Excel 手算的一致性。

| 驗收項目 | 通過條件 |
|----------|----------|
| 月趨勢方向驗證 | 至少 1 個事業群趨勢與 Excel 手算一致，附截圖或數字說明 |
| 異常偵測誤報檢查 | 抽查 3 筆異常，確認為真實異常並說明原因 |
| 相關係數方向驗證 | 正相關群組在原始資料中可目測確認 |
