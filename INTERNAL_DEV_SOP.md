# Internal Development SOP

## 目的

本文件說明如何在沒有 GitHub 帳號、只有公司內網的情況下，讓多台 Windows 電腦同步開發這個 repo。

只要內網電腦可以互相連線，並且可存取同一個 Git remote，就可以依照本 SOP 完成：

- 初次建置開發環境
- Clone 專案
- 用 `uv` 同步 Python 環境
- 日常 pull / commit / push
- 多人協作分支開發

本 SOP 以目前專案為例：

- 專案目錄：`營收去識別化先驗測試`
- Python 管理方式：`uv`
- 作業系統假設：Windows

---

## 1. 架構建議

內網協作最建議使用以下架構：

1. 一台電腦或共享資料夾存放 bare Git repo
2. 其他開發電腦透過內網路徑 clone 該 repo
3. 每位開發者在自己的工作目錄修改程式
4. 透過 `git pull` / `git push` 同步

請不要讓兩個人直接共用同一份 working directory。

正確做法是：

- 共用 remote repo
- 各自擁有本機工作目錄

---

## 2. 角色分工

### 2.1 Repo Host

Repo Host 是放 bare repo 的主機，負責：

- 提供共享資料夾
- 存放 bare Git repo
- 作為內網同步中心

### 2.2 Developer Machines

每台開發電腦負責：

- 安裝 Git
- 安裝 Python 3.12
- 安裝 `uv`
- clone repo
- 使用 `uv sync` 建立本機環境
- 日常開發、commit、push

---

## 3. 建立內網 Git Remote

以下方法 3 選 1。

### 3.1 方法 A：使用共享資料夾作為 remote

最簡單，最推薦。

假設你有一個共享資料夾：

```text
\\192.168.1.10\git-share
```

在共享資料夾中建立 bare repo：

```powershell
mkdir \\192.168.1.10\git-share\revenue-poc.git
cd \\192.168.1.10\git-share\revenue-poc.git
git init --bare
```

完成後，這個路徑就是 remote：

```text
\\192.168.1.10\git-share\revenue-poc.git
```

### 3.2 方法 B：用本機磁碟建立 bare repo，再分享資料夾

例如主機上建立：

```text
D:\git\revenue-poc.git
```

初始化：

```powershell
mkdir D:\git\revenue-poc.git
cd D:\git\revenue-poc.git
git init --bare
```

再把 `D:\git` 或 `D:\git\revenue-poc.git` 分享到內網。

### 3.3 方法 C：NAS 作為 remote

若公司已有 NAS，可在 NAS 上建立：

```text
\\NAS\git\revenue-poc.git
```

再用同樣方式初始化 bare repo。

---

## 4. 第一台電腦初始化並推上去

如果目前專案已經在第一台電腦上，請在專案目錄執行：

### 4.1 初始化 Git

```powershell
git init -b main
git config user.name "你的名字"
git config user.email "你的信箱或內部識別"
```

### 4.2 加入檔案並提交

```powershell
git add .
git commit -m "Initial commit"
```

### 4.3 設定 remote

假設 remote 是：

```text
\\192.168.1.10\git-share\revenue-poc.git
```

加入 remote：

```powershell
git remote add origin "\\192.168.1.10\git-share\revenue-poc.git"
```

### 4.4 Push 到內網 remote

```powershell
git push -u origin main
```

完成後，其他電腦即可 clone。

---

## 5. 其他內網電腦第一次加入開發

每台新的開發電腦請照以下步驟進行。

### 5.1 安裝 Git

確認 Git 可用：

```powershell
git --version
```

### 5.2 安裝 Python 3.12

確認 Python 可用：

```powershell
python --version
```

建議版本：

```text
Python 3.12.x
```

### 5.3 安裝 uv

確認 `uv` 可用：

```powershell
uv --version
```

### 5.4 Clone 專案

```powershell
git clone "\\192.168.1.10\git-share\revenue-poc.git"
cd revenue-poc
```

### 5.5 設定個人 Git 身份

```powershell
git config user.name "你的名字"
git config user.email "你的信箱或內部識別"
```

### 5.6 建立 Python 環境

```powershell
uv sync
```

### 5.7 驗證專案可跑

```powershell
uv run python main.py --project-summary
```

若能正常輸出 project summary，代表環境可用。

---

## 6. 專案固定規範

### 6.1 Python 與依賴

本專案使用：

- `pyproject.toml`
- `uv.lock`

作為依賴管理基礎。

日常請使用：

```powershell
uv sync
uv run python ...
```

不要優先使用：

```powershell
pip install -r requirements.txt
```

`requirements.txt` 僅保留相容用途。

### 6.2 本機不應提交的內容

以下內容不應提交：

- `.venv/`
- `output/`
- `__pycache__/`

這些已在 `.gitignore` 中排除。

### 6.3 資料檔

目前 repo 內已包含：

- `data/inventory.xlsx`
- `data/revenue.xlsx`
- `data/mapping.xlsx`

若未來資料改為敏感正式資料，建議改成：

- repo 不放正式資料
- 每台電腦從內部安全來源取得資料

---

## 7. 每日開發流程

以下為每位開發者每天的基本 SOP。

### 7.1 開始工作前

先更新主線：

```powershell
git checkout main
git pull origin main
uv sync
```

### 7.2 建立自己的工作分支

分支命名建議：

```text
feature/<name>
fix/<name>
docs/<name>
```

例如：

```powershell
git checkout -b docs/mid-report-update
```

### 7.3 開發與測試

常用命令：

```powershell
uv run python main.py
uv run python main.py --project-summary
uv run python main.py --question "請摘要目前專案能力"
uv run python demo_web.py
```

### 7.4 查看變更

```powershell
git status
git diff
```

### 7.5 提交

```powershell
git add .
git commit -m "Update project docs and analysis flow"
```

### 7.6 Push 到內網 remote

第一次 push 分支：

```powershell
git push -u origin docs/mid-report-update
```

後續同分支：

```powershell
git push
```

---

## 8. 合併流程建議

如果沒有 GitHub / GitLab pull request 介面，建議用以下方式。

### 8.1 簡單做法

開發者 A 完成後：

```powershell
git checkout main
git pull origin main
git merge docs/mid-report-update
git push origin main
```

### 8.2 較安全做法

由一位整合者專門負責 `main`：

- 其他人只 push feature branch
- 整合者負責 pull branch、測試、merge 到 `main`

這樣比較不容易把主線弄亂。

---

## 9. 兩人協作建議

目前專案可依以下方式分工。

### 人員 A：資料分析主線

- `mapping_parser.py`
- `analyzer.py`
- 分析規則
- 異常偵測
- 預測 / 指標擴充

### 人員 B：系統與 Agent 主線

- `multi_agent.py`
- `analysis_tools.py`
- `demo_web.py`
- `frontend/`
- 文件、部署、協作流程

### 每週同步項目

- 新增欄位與輸出格式
- 新增 warning / limitation
- 依賴版本變更
- 文件更新

---

## 10. 新增或更新依賴的 SOP

若要新增套件，請在專案目錄執行：

```powershell
uv add <package-name>
```

例如：

```powershell
uv add pytest
```

完成後請提交：

- `pyproject.toml`
- `uv.lock`

若移除套件：

```powershell
uv remove <package-name>
```

---

## 11. 常見指令速查

### Git

```powershell
git status
git branch
git checkout main
git checkout -b feature/my-work
git pull origin main
git add .
git commit -m "message"
git push
```

### uv

```powershell
uv sync
uv run python main.py
uv run python main.py --project-summary
uv run python main.py --question "請摘要目前專案能力"
uv run python demo_web.py
```

---

## 12. 常見問題排除

### Q1. `uv` 找不到

請先確認：

```powershell
uv --version
```

若失敗：

- 重新開一個 PowerShell 視窗
- 確認 `uv` 已安裝
- 確認 PATH 已包含 `uv.exe` 所在目錄

### Q2. `python` 找不到

請確認：

```powershell
python --version
```

若仍不穩，先直接使用：

```powershell
uv run python ...
```

這通常比直接依賴系統 `python` 更穩。

### Q3. `uv sync` 失敗

請先確認：

- 網路可存取 Python 套件來源
- 本機 Python 3.12 可用
- 專案目錄有 `pyproject.toml`

可先刪掉本機 `.venv/` 後重跑：

```powershell
uv sync
```

### Q4. `git push` 失敗

請確認：

- remote 路徑正確
- 共享資料夾有寫入權限
- 內網路徑可存取
- 主機或 NAS 沒被防火牆阻擋

### Q5. `demo_web.py` 能啟動但網頁打不開

請確認：

- `http://127.0.0.1:8765`
- 本機防火牆
- 8765 port 未被其他程式占用

---

## 13. 建議的正式交付規範

若之後要變成正式團隊協作流程，建議再補以下內容：

- 統一 branch naming 規則
- commit message 規則
- 測試清單
- merge checklist
- 文件更新 checklist
- release tagging 規則

---

## 14. 最短版 SOP

如果只想記最短流程，請記這 8 步：

1. 安裝 Git
2. 安裝 Python 3.12
3. 安裝 `uv`
4. `git clone <內網 bare repo 路徑>`
5. `cd <repo>`
6. `uv sync`
7. `git checkout -b <your-branch>`
8. 開發後 `git add .`、`git commit`、`git push`

---

## 15. 結論

只要內網有一個可存取的 bare Git repo，任何內網電腦都可以依照本 SOP：

- clone 此 repo
- 建立 `uv` 開發環境
- 同步更新
- 多人並行開發

也就是說，這個專案已經可以在沒有 GitHub 帳號的情況下，靠內網 Git 正常協作開發。

---

## 16. A/B 合體標準（介面契約）

### 16.1 欄位名稱規則

所有欄位名稱**只能從 `config.py` 的常數 import**，不得在程式碼中直接寫中文字串。

```python
# 正確
from config import COL_REVENUE, COL_MONTH, COL_GROUP_CODE
df.groupby(COL_GROUP_CODE)[COL_REVENUE].sum()

# 禁止
df.groupby("新事業群")["營收"].sum()
```

常數清單定義在 `config.py` 的 `# Column name contract` 區塊。
A 如需新增欄位，在該區塊新增常數，不要在其他地方定義。

---

### 16.2 新增 Artifact 時的 Checklist

A 每次在 `AnalysisArtifacts` 新增欄位或 artifact，**必須完成以下 5 步**，再 push：

- [ ] 在 `analyzer.py` 的 `AnalysisArtifacts` dataclass 宣告新欄位（型別為 `pd.DataFrame`）
- [ ] 在 `config.py` 新增對應欄位名常數（若有新欄位名）
- [ ] 在 `analysis_tools.py` 的 `_METRIC_FILTER_SUPPORT` 登記新 metric 及其支援的 filters
- [ ] 在 `analysis_tools.py` 的 `_empty_metric_frame` 新增對應的空表欄位定義
- [ ] 在 `analysis_pipeline.py` 的 `supported_domains` 確認新 artifact 是否影響 domain 判斷

---

### 16.3 `supported_domains` 異動通知

A 若修改橋接邏輯，導致原本 `False` 的 domain 變為 `True`（例如 `financial` 從不可用變可用），
**必須在 commit message 中明確說明**：

```
fix(mapping): strengthen HQBU-platform bridge

supported_domains["financial"] now returns True when platform_monthly_analysis is non-empty.
B: Financial Agent can now call get_platform_ratios() in production data.
```

B 收到此類 commit 後，需驗證 Financial Agent 的回答是否符合預期。

---

### 16.4 每週同步項目（A/B 共同）

| 項目 | 說明 |
|------|------|
| 新增欄位與輸出格式 | A 說明，B 確認 `analysis_tools.py` 是否需更新 |
| 新增 warning / limitation | 雙方確認是否影響 Agent 回答邏輯 |
| 依賴版本變更 | 提交 `pyproject.toml` + `uv.lock`，對方執行 `uv sync` |
| `supported_domains` 變動 | A 主動通知 B |
