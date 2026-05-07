# 開發紀錄

## 2026-04-14

### 文件整理

- 新增 `SDD.md`
- 新增 `PROGRESS_REPORT.md`
- 新增 `strategy.md`
- 新增 `devlog.md`
- 新增 `mid_report.md`
- 新增 `CURRENT_FUTURE_STATUS.md`
- 新增 `WORK_SPLIT.md`

### 環境整理

- 安裝 Python 3.12.10
- 安裝 Git for Windows
- 重建 `.venv`
- 將專案切換為 `uv` 管理
- 新增 `pyproject.toml`
- 新增 `uv.lock`
- 新增 `.python-version`
- 新增 `UV_SETUP.md`
- 新增 `.gitignore`

### 驗證結果

- `uv sync` 成功
- `uv run python main.py` 成功
- `uv run python main.py --project-summary` 成功
- `uv run python main.py --question "請摘要目前專案能力"` 成功
- `uv run python demo_web.py` 可啟動，`/api/summary` 與 `/api/ask` 有成功回應紀錄

### 目前觀察

- 批次主流程在 `uv` 下可跑通
- Agent 問答在 `uv` 下可運作
- Web demo 可啟動
- Ollama 仍可能出現 timeout，但專案保有 fallback
- 專案目前尚未初始化為 Git repo
