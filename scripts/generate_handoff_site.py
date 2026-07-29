from __future__ import annotations

import ast
import html
import inspect
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "frontend" / "public" / "handoff"
ASSETS = SITE / "assets"

PAGE_ORDER = [
    ("index.html", "首頁"),
    ("overview.html", "系統總覽"),
    ("question-journey.html", "一題怎麼跑"),
    ("tools.html", "Tool 工具箱"),
    ("architecture.html", "架構與程式地圖"),
    ("operations.html", "展示與操作"),
    ("maintenance.html", "新增與修改"),
    ("appendix.html", "附錄"),
]

IMPORTANT_FILES = [
    "README.md",
    "demo_web.py",
    "frontend/lib/python-api.js",
    "frontend/app/page.js",
    "frontend/app/dashboard/page.js",
    "analysis_pipeline.py",
    "real_data.py",
    "data_loader.py",
    "multi_agent.py",
    "task_profile.py",
    "canonical_task.py",
    "answer_plan.py",
    "plan_validator.py",
    "tool_registry.py",
    "analysis_tools.py",
    "agent_runtime/integration.py",
    "agent_runtime/runtime.py",
    "agent_runtime/evidence_validator.py",
    "agent_runtime/replanner.py",
    "writer_validator.py",
    "semantic_layer/catalog.py",
    "mcp_server/server.py",
    "mcp_server/security.py",
    "proactive_workflow/orchestrator.py",
    "proactive_workflow/approval.py",
    "proactive_workflow/publisher.py",
    "observability/__init__.py",
    "evaluation/cli.py",
    "evaluation/policies/regression_gate.v1.json",
]

MODULE_GROUPS = {
    "frontend": ["frontend/app", "frontend/components", "frontend/lib"],
    "backend／orchestration": ["demo_web.py", "multi_agent.py", "analysis_pipeline.py"],
    "agent_runtime": ["agent_runtime"],
    "semantic_layer": ["semantic_layer"],
    "analysis tools": ["tool_registry.py", "analysis_tools.py", "plan_validator.py"],
    "mcp_server": ["mcp_server"],
    "proactive_workflow": ["proactive_workflow"],
    "observability": ["observability"],
    "evaluation": ["evaluation"],
    "tests": ["tests"],
}

TASK_LABELS = {
    "latest_month_platform_summary": "最新月份平台摘要",
    "latest_month_entity_summary": "最新月份實體摘要",
    "period_pair_compare": "兩期間比較",
    "entity_period_pair_table_lookup": "兩期間實體表格",
    "entity_multi_month_table_lookup": "多月實體表格",
    "entity_period_pair_metric_lookup": "單一實體兩期間數值",
    "entity_time_series": "單一實體時間序列",
    "overall_trend_analysis": "整體趨勢",
    "entity_trend_comparison": "實體趨勢比較",
    "metric_relationship_analysis": "營收與庫存關係",
    "contribution_analysis": "貢獻分析",
    "forecast_unsupported": "預測不支援",
    "parent_child_drilldown": "事業群到產品線鑽取",
    "entity_month_table_lookup": "單月實體表格",
    "cross_section_compare": "同月橫向比較",
    "performance_assessment": "表現評估",
    "risk_scan": "風險訊號掃描",
    "metric_lookup": "單一數值查詢",
    "chart_request": "圖表產生",
    "entity_ranking": "排序排名",
    "time_compare": "時間比較",
    "data_quality": "資料品質",
    "diagnosis": "診斷候選",
}

TOOL_PURPOSES = {
    "get_entity_month_table": "列出某個月份中各事業群或產品線的一個 KPI 數值。",
    "get_entity_metric_value": "查單一事業群或產品線在某月份的一個 KPI。",
    "get_entity_period_pair_table": "列出兩個指定月份中各實體的 KPI 對照表。",
    "get_entity_multi_month_table": "列出一段月份區間內各實體的 KPI 表格。",
    "get_entity_period_pair_value": "查單一實體在兩個指定月份的 KPI 差異。",
    "get_entity_metric_ranking": "依指定 KPI 排出事業群或產品線名次。",
    "get_entity_performance_snapshot": "產生實體表現快照，包含營收、庫存與 proxy 分數。",
    "get_entity_cross_section_comparison": "比較同一月份中多個實體的表現。",
    "get_entity_period_pair_comparison": "比較兩個月份中各實體的變化。",
    "get_period_pair_metric_comparison": "比較整體或彙總維度在兩個月份的 KPI。",
    "get_entity_time_series": "查單一實體的月度趨勢。",
    "get_overall_time_series": "查整體 KPI 的月度趨勢。",
    "get_entity_trend_comparison": "比較多個實體在一段期間中的趨勢。",
    "get_revenue_inventory_relationship": "找營收與庫存是否出現同向、背離或壓力訊號。",
    "get_entity_contribution_analysis": "分析兩期間變化主要由哪些實體貢獻。",
    "get_chart_payload": "產生前端可畫圖的 chart payload。",
    "get_chart_table": "產生與圖表對齊的資料表。",
    "get_data_coverage": "回報可用月份、資料列數與支援 domain。",
    "get_mapping_summary": "回報資料來源對齊與實體 mapping 摘要。",
    "get_tool_capability_matrix": "回報目前工具與資料可用狀態。",
    "get_anomalies": "列出 deterministic anomaly records。",
    "get_yoy_mom_breakdown": "列出月增與年增變化。",
    "get_contribution_analysis": "列出目前與前期的貢獻拆解。",
    "get_inventory_turnover_proxy": "列出營收相對庫存效率 proxy。",
    "get_root_cause_candidates": "列出可能觀察方向，但不宣稱根本原因。",
    "get_platform_ratios": "舊版平台 proxy ratio wrapper。",
    "get_platform_ranking": "舊版平台排名 wrapper。",
    "get_platform_performance_snapshot": "舊版平台表現快照 wrapper。",
    "get_top_groups": "舊版事業群排行 helper。",
    "get_metric_table": "舊版原始 metric table helper。",
}

COMMON_LIMITS = {
    "get_data_coverage": "只回報 coverage，不代表資料品質完整通過。",
    "get_revenue_inventory_relationship": "只描述歷史資料關係，不可寫成因果或預測。",
    "get_inventory_turnover_proxy": "proxy 不是正式庫存週轉率，缺少 COGS 與平均庫存。",
    "get_chart_payload": "供前端渲染使用，不是回答充分性的 primary evidence。",
    "get_chart_table": "與圖表資料對齊，不取代正式分析工具。",
    "get_root_cause_candidates": "只能當候選觀察，不可當作已確認根因。",
}


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def load_json(path: str) -> Any:
    return json.loads(read_text(path))


def source_link(path: str, line: int | None = None) -> str:
    suffix = f":{line}" if line else ""
    return f"{path}{suffix}"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def code_block(code: str, lang: str = "") -> str:
    return f'<div class="code-wrap"><button class="copy-btn" type="button">複製</button><pre><code class="language-{esc(lang)}">{esc(code.rstrip())}</code></pre></div>'



def chips(items: Iterable[Any], limit: int | None = None) -> str:
    values = [str(item) for item in (items or [])]
    if limit is not None:
        values = values[:limit]
    if not values:
        return '<span class="chip">未限制</span>'
    return '<span class="chips">' + ''.join(f'<span class="chip">{esc(value)}</span>' for value in values) + '</span>'


def snippet_block(code: str, lang: str, source: str, symbol: str, focus: str) -> str:
    return (
        code_block(code, lang)
        + f'<p class="code-note"><strong>來源：</strong><code>{esc(source)}</code>　'
        + f'<strong>位置：</strong><code>{esc(symbol)}</code>　'
        + f'<strong>看法：</strong>{esc(focus)}</p>'
    )


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False)


def extract_snippet(path: str, start_pattern: str, end_pattern: str | None = None, max_lines: int = 80) -> str:
    lines = read_text(path).splitlines()
    start = next((i for i, line in enumerate(lines) if start_pattern in line), None)
    if start is None:
        return "目前程式中未確認"
    end = min(len(lines), start + max_lines)
    if end_pattern:
        for idx in range(start + 1, min(len(lines), start + max_lines)):
            if end_pattern in lines[idx]:
                end = idx
                break
    return "\n".join(lines[start:end])


def ast_symbols(path: Path) -> list[str]:
    if path.suffix != ".py":
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except SyntaxError:
        return []
    symbols: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(node.name)
    return symbols[:12]


def line_number_for_symbol(path: str, symbol: str) -> int | None:
    text = read_text(path)
    for idx, line in enumerate(text.splitlines(), 1):
        if re.match(rf"\s*(def|class)\s+{re.escape(symbol)}\b", line):
            return idx
    return None


def load_registry() -> tuple[dict[str, Any], Any]:
    import sys

    sys.path.insert(0, str(ROOT))
    from tool_registry import TOOL_REGISTRY, ToolContract

    payload = {name: contract.to_dict() for name, contract in TOOL_REGISTRY.items()}
    return payload, ToolContract


def collect_tests_for_tools(tool_names: list[str]) -> dict[str, list[str]]:
    tests: dict[str, list[str]] = {name: [] for name in tool_names}
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8-sig")
        rel = path.relative_to(ROOT).as_posix()
        for name in tool_names:
            if name in text:
                tests[name].append(rel)
    for path in sorted((ROOT / "evaluation" / "datasets").glob("*.jsonl")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        for name in tool_names:
            if name in text:
                tests[name].append(rel)
    return tests


def collect_methods() -> dict[str, dict[str, Any]]:
    tree = ast.parse(read_text("analysis_tools.py"))
    result: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "AnalysisToolbox":
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    args = [arg.arg for arg in item.args.args if arg.arg != "self"]
                    result[item.name] = {
                        "path": "analysis_tools.py",
                        "line": item.lineno,
                        "function": f"AnalysisToolbox.{item.name}({', '.join(args)})",
                    }
    return result


def collect_mcp_server_tools() -> set[str]:
    text = read_text("mcp_server/server.py")
    return set(re.findall(r'_call\("([^"]+)"', text))


def collect_semantic() -> dict[str, Any]:
    metrics = load_json("semantic_layer/definitions/metrics.json")["metrics"]
    dimensions = load_json("semantic_layer/definitions/dimensions.json")["dimensions"]
    task_evidence = load_json("semantic_layer/definitions/task_evidence.json")["tasks"]
    task_coverage = load_json("semantic_layer/definitions/task_coverage.json")["active_task_types"]
    return {
        "metrics": metrics,
        "dimensions": dimensions,
        "task_evidence": task_evidence,
        "task_coverage": task_coverage,
    }


def collect_eval() -> dict[str, Any]:
    suites: list[dict[str, Any]] = []
    for path in sorted((ROOT / "evaluation" / "datasets").glob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        suites.append(
            {
                "suite": path.name.replace(".v1.jsonl", ""),
                "path": path.relative_to(ROOT).as_posix(),
                "total": len(rows),
                "execution_backed": sum(row.get("execution_mode") == "execution_backed" for row in rows),
                "synthetic": sum(row.get("execution_mode") == "synthetic_trajectory" for row in rows),
                "adapters": sorted({row.get("execution_adapter") for row in rows if row.get("execution_adapter")}),
            }
        )
    policy = load_json("evaluation/policies/regression_gate.v1.json")
    return {"suites": suites, "policy": policy, "case_count": sum(s["total"] for s in suites)}


def build_tool_catalog() -> dict[str, Any]:
    registry, contract_cls = load_registry()
    methods = collect_methods()
    mcp_registered = collect_mcp_server_tools()
    tests = collect_tests_for_tools(list(registry))
    by_family: dict[str, int] = Counter()
    by_metric: dict[str, int] = Counter()
    by_evidence: dict[str, int] = Counter()
    tools: list[dict[str, Any]] = []
    for name, contract in registry.items():
        for family in contract.get("allowed_task_families") or ["未限制"]:
            by_family[family] += 1
        for metric in contract.get("supported_metrics") or contract.get("supported_metric_ids") or ["未限制"]:
            by_metric[metric] += 1
        evidence = contract.get("output_evidence_type") or "未指定"
        by_evidence[evidence] += 1
        method = methods.get(name, {})
        tools.append(
            {
                **contract,
                "zh_purpose": TOOL_PURPOSES.get(name, "目前程式中未確認中文用途，請閱讀 description。"),
                "good_for": infer_good_for(contract),
                "allowed_args": [*contract.get("required_args", []), *contract.get("optional_args", [])],
                "implementation_path": method.get("path", "analysis_tools.py"),
                "implementation_line": method.get("line"),
                "implementation_function": method.get("function", f"AnalysisToolbox.{name}"),
                "tests": tests.get(name, []),
                "common_limitations": list(contract.get("known_limitations") or [])
                or [COMMON_LIMITS.get(name, "依資料可用月份、實體 mapping 與 ToolContract 參數限制。")],
                "mcp_registered": name in mcp_registered,
            }
        )
    return {
        "schema_version": "handoff-tool-catalog.v1",
        "generated_from": ["tool_registry.py", "analysis_tools.py", "mcp_server/server.py", "mcp_server/security.py", "tests/", "evaluation/datasets/"],
        "tool_contract_fields": [field for field in contract_cls.__dataclass_fields__],
        "tools": tools,
        "stats": {
            "total": len(tools),
            "mcp_exposable": sum(1 for item in tools if item.get("mcp_exposable")),
            "mcp_registered": sum(1 for item in tools if item.get("mcp_registered")),
            "read_only": sum(1 for item in tools if item.get("read_only")),
            "internal": sum(1 for item in tools if not item.get("mcp_exposable")),
            "task_families": dict(sorted(by_family.items())),
            "metrics": dict(sorted(by_metric.items())),
            "evidence_types": dict(sorted(by_evidence.items())),
        },
    }


def infer_good_for(contract: dict[str, Any]) -> str:
    families = [TASK_LABELS.get(item, item) for item in contract.get("allowed_task_families") or []]
    metrics = contract.get("supported_metrics") or []
    if not families and not metrics:
        return "資料品質、coverage 或相容性用途。"
    family_text = "、".join(families[:4]) if families else "一般查詢"
    metric_text = "；KPI：" + "、".join(metrics[:4]) if metrics else ""
    return f"適合：{family_text}{metric_text}。"


def collect_routes() -> dict[str, Any]:
    backend = read_text("demo_web.py")
    get_routes = sorted(set(re.findall(r'parsed\.path == "([^"]+)"', backend)))
    post_routes = sorted(set(re.findall(r'parsed\.path(?: not in \{|\s*== )"?([^"}]+)', backend)))
    return {
        "frontend": ["/", "/dashboard", "/mobile", "/api/ask", "/api/health", "/api/summary", "/api/chart", "/api/observe"],
        "backend_get": get_routes,
        "backend_post_source_confirmed": ["/api/ask", "/api/chart", "/api/observe", "/api/investigations/scan", "/api/approval-requests/{id}/{action}"],
    }


def collect_file_index() -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    interesting_dirs = {
        "root": ["*.py", "*.md", "*.toml", "*.json"],
        "agent_runtime": ["agent_runtime/*.py"],
        "semantic_layer": ["semantic_layer/*.py", "semantic_layer/definitions/*.json"],
        "proactive_workflow": ["proactive_workflow/*.py"],
        "mcp_server": ["mcp_server/*.py"],
        "observability": ["observability/*.py"],
        "evaluation": ["evaluation/*.py", "evaluation/datasets/*.jsonl", "evaluation/policies/*.json"],
        "frontend": ["frontend/app/**/*.js", "frontend/components/**/*.jsx", "frontend/lib/*.js", "frontend/package.json", "frontend/next.config.mjs"],
        "tests": ["tests/test_*.py"],
    }
    for group, patterns in interesting_dirs.items():
        paths: set[Path] = set()
        for pattern in patterns:
            paths.update(ROOT.glob(pattern))
        for path in sorted(paths):
            if path.is_dir() or "__pycache__" in path.parts:
                continue
            rel = path.relative_to(ROOT).as_posix()
            symbols = ast_symbols(path)
            groups[group].append(
                {
                    "path": rel,
                    "purpose": file_purpose(rel),
                    "symbols": symbols,
                    "caller": infer_caller(rel),
                    "callee": infer_callee(rel),
                    "sync": infer_sync(rel),
                    "tests": infer_tests(rel),
                }
            )
    return groups


def file_purpose(path: str) -> str:
    mapping = {
        "README.md": "專案總覽與正式啟動方式，先確認資料來源、服務入口與交接網站路徑。",
        "demo_web.py": "Python Backend/API 入口，建立共用分析環境，接 Dashboard 問答、圖表、health 與主動流程 API。",
        "frontend/app/page.js": "Frontend 首頁轉址到 Dashboard，讓使用者進入主要工作台。",
        "frontend/app/dashboard/page.js": "Dashboard route，載入 InsightConsole 作為主要 Demo 介面。",
        "frontend/lib/python-api.js": "Next.js API route 轉送 Python backend 的共用 helper，集中處理 backend URL 與 JSON 錯誤。",
        "analysis_pipeline.py": "把資料讀取、清理、正規化與分析表建立成 PipelineContext，供所有工具共用。",
        "real_data.py": "定義真實 Excel 資料的讀取、欄位檢查、月份與實體對齊規則。",
        "data_loader.py": "低階資料載入與欄位標準化 helper，避免各工具各自讀 Excel。",
        "multi_agent.py": "Agent orchestration 主體，負責理解問題、規劃工具、執行分析與組裝回答。",
        "task_profile.py": "把中文問題歸類成 task family，抽出時間、KPI、實體與回答需求。",
        "canonical_task.py": "把 TaskProfile 整理成穩定 schema，保留月份、實體、KPI 與 semantic reference。",
        "answer_plan.py": "依 task family 決定主要工具、輔助工具、背景工具與禁止當主要證據的工具。",
        "plan_validator.py": "檢查 planner 產生的 tool call 是否符合 registry、task、時間、實體與 KPI 限制。",
        "tool_registry.py": "所有正式 ToolContract 的登記處，定義工具參數、支援 KPI、evidence type 與 MCP exposure。",
        "analysis_tools.py": "受控分析工具的實作位置，所有營收、庫存、排名、趨勢與圖表計算都從這裡出來。",
        "agent_runtime/integration.py": "把 Stateful Runtime 接進 MultiAgentAssistant.answer，並決定何時走 legacy 或 stateful path。",
        "agent_runtime/runtime.py": "可 checkpoint 的執行迴圈，依序跑工具、收 evidence、驗證、不足時 replan。",
        "agent_runtime/evidence_validator.py": "檢查回答證據是否真的涵蓋 KPI、月份、實體、rows 與 semantic requirement。",
        "agent_runtime/replanner.py": "保守補證工具，只能新增 registry 允許且未重複的合法工具呼叫。",
        "agent_runtime/state_store.py": "Agent run state 的記憶體與 SQLite 儲存實作，用於 checkpoint 與排錯。",
        "agent_runtime/models.py": "AgentRunState、PlanStep、ToolExecutionRecord 等 runtime 狀態資料模型。",
        "writer_validator.py": "回答文字安全檢查，避免新數字、錯月份、因果宣稱、forecast 外推與 debug 洩漏。",
        "semantic_layer/catalog.py": "載入 KPI、dimension、task evidence 與 data contract 定義，提供查詢與驗證入口。",
        "semantic_layer/definitions/metrics.json": "KPI 定義檔，描述顯示名稱、公式、來源欄位、proxy 與限制。",
        "semantic_layer/definitions/dimensions.json": "維度定義檔，描述月份、事業群、產品線與可用 KPI。",
        "semantic_layer/definitions/task_evidence.json": "回答某些 task family 時需要哪些 primary/supporting evidence 的規則。",
        "semantic_layer/definitions/task_coverage.json": "目前 task family 的功能狀態與執行方式來源。",
        "mcp_server/server.py": "MCP stdio server，公開少量 allowlisted read-only tools 與 semantic resources。",
        "mcp_server/security.py": "MCP 安全層，負責 hidden tool rejection、argument validation、row cap 與 sanitization。",
        "mcp_server/resources.py": "MCP semantic resources 的讀取入口，例如 metrics、dimensions、tools 與 data contracts。",
        "proactive_workflow/orchestrator.py": "資料刷新後串起 fingerprint、data quality、candidate、investigation、draft 與 approval。",
        "proactive_workflow/approval.py": "人工核准流程，檢查 approver、draft hash、狀態衝突與 revision/reject 條件。",
        "proactive_workflow/publisher.py": "發布 gate，只有 approved draft 且 hash 一致時才寫出正式 publication artifacts。",
        "observability/__init__.py": "Observability 對外入口，匯出 trace context、recorder、SQLite store 與 instrumentation。",
        "observability/config.py": "Trace 設定來源，包含預設 SQLite trace store path 與環境變數讀取。",
        "observability/store.py": "SQLite trace store 實作，用於保存與查詢本地執行軌跡。",
        "observability/tracing.py": "TraceRecorder 實作，讓 agent、tool、MCP、approval、publication 產生 span。",
        "observability/redaction.py": "Trace 與輸出 redaction helper，避免敏感值或路徑外洩。",
        "evaluation/cli.py": "離線 evaluation、coverage、report、compare 與 regression gate CLI。",
        "evaluation/policies/regression_gate.v1.json": "交付前 gate policy，定義 execution-backed、trace、安全與 publication 門檻。",
    }
    if path in mapping:
        return mapping[path]
    if path.startswith("tests/"):
        return "針對特定功能或安全邊界的 regression / acceptance test。"
    if path.startswith("evaluation/datasets/"):
        return "Evaluation suite case 定義，用來重跑交付前驗收。"
    if path.startswith("semantic_layer/definitions/"):
        return "Semantic catalog definition。"
    if path.startswith("frontend/app/api/"):
        return "Next.js API proxy route，將前端請求轉送到 Python backend。"
    if path.startswith("frontend/components/"):
        return "Dashboard 或 mobile UI 元件。"
    if path.startswith("proactive_workflow/"):
        return "主動洞察流程的其中一個步驟或資料模型。"
    if path.startswith("observability/"):
        return "本地 trace、redaction 或 metrics 的輔助模組。"
    if path.startswith("evaluation/"):
        return "Evaluation runner、grader、report 或資料集處理模組。"
    return "協助定位的檔案，請搭配實際 source code 閱讀。"

def infer_caller(path: str) -> str:
    if path == "analysis_tools.py":
        return "multi_agent.py、demo_web.py、mcp_server/server.py、proactive_workflow"
    if path == "tool_registry.py":
        return "PlanValidator、Stateful Runtime、MCP security、LLM planner"
    if path.startswith("agent_runtime"):
        return "agent_runtime/integration.py、tests、evaluation adapters"
    if path.startswith("proactive_workflow"):
        return "demo_web.py、proactive_workflow/cli.py、evaluation adapters"
    if path.startswith("frontend"):
        return "Next.js runtime"
    return "目前程式中未確認主要 caller"


def infer_callee(path: str) -> str:
    if path == "demo_web.py":
        return "analysis_pipeline、AnalysisToolbox、MultiAgentAssistant、ProactiveWorkflowOrchestrator"
    if path == "multi_agent.py":
        return "task_profile、canonical_task、answer_plan、AnalysisToolbox、WriterValidator"
    if path == "agent_runtime/runtime.py":
        return "EvidenceValidator、DeterministicReplanner、AgentStateStore、tool executor"
    if path == "mcp_server/server.py":
        return "mcp_server/security、AnalysisToolbox、observability"
    return "目前程式中未確認主要 callee"


def infer_sync(path: str) -> str:
    if path in {"tool_registry.py", "analysis_tools.py"}:
        return "同步 tests/test_tool_registry.py、tests/test_mcp_security.py、PlanValidator 與 evaluation datasets。"
    if path.startswith("semantic_layer"):
        return "同步 task_coverage、task_evidence、tool registry、answer_plan 與 semantic tests。"
    if path.startswith("frontend"):
        return "同步 frontend API routes、Dashboard smoke 與 build。"
    return "依修改範圍同步 focused tests。"


def infer_tests(path: str) -> list[str]:
    rel_name = Path(path).stem.replace("-", "_")
    tests = []
    for test in sorted((ROOT / "tests").glob("test_*.py")):
        text = test.read_text(encoding="utf-8-sig")
        if Path(path).stem in text or path in text or rel_name in test.stem:
            tests.append(test.relative_to(ROOT).as_posix())
    return tests[:8]


def nav(active: str) -> str:
    items = []
    for href, label in PAGE_ORDER:
        cls = "active" if href == active else ""
        url = "./" if href == "index.html" else href
        items.append(f'<a class="{cls}" href="{url}">{label}</a>')
    return "\n".join(items)


def layout(filename: str, title: str, subtitle: str, body: str, toc: list[tuple[str, str]] | None = None) -> str:
    toc_html = ""
    toc_controls = ""
    if toc:
        links = "".join(f'<a class="page-toc-link" href="#{esc(anchor)}">{esc(label)}</a>' for anchor, label in toc)
        toc_html = f"""<aside class="page-toc" aria-label="本頁導覽" data-page-toc>
        <div class="page-toc-header">
          <strong>本頁導覽</strong>
          <button class="toc-collapse-button" type="button" aria-label="收起本頁導覽" aria-expanded="true" data-toc-collapse>收起導覽 ◀</button>
        </div>
        <nav class="page-toc-links" aria-label="本頁章節">{links}</nav>
      </aside>"""
        toc_controls = """<button class="toc-expand-button" type="button" aria-label="展開本頁導覽" aria-expanded="false" data-toc-expand>▶</button>
      <button class="toc-mobile-button" type="button" aria-label="開啟本頁導覽" aria-expanded="false" data-toc-mobile-open>本頁導覽</button>
      <div class="toc-backdrop" data-toc-backdrop hidden></div>"""
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}｜Revenue Intelligence POC</title>
  <link rel="stylesheet" href="assets/css/style.css">
  <script defer src="assets/js/app.js"></script>
</head>
<body data-page="{esc(filename)}">
  <header class="topbar">
    <a class="brand" href="./"><span>Revenue Intelligence POC</span><small>Handoff</small></a>
    <button class="nav-toggle" type="button" aria-label="開關全站導覽">☰</button>
    <nav class="main-nav" aria-label="全站導覽">{nav(filename)}</nav>
    <button class="theme-toggle" type="button" aria-label="切換日間或夜間模式" data-theme-toggle>日間</button>
  </header>
  <main class="page-shell">
    <section class="page-hero">
      <p class="eyebrow">新人可直接閱讀的交接網站</p>
      <h1>{esc(title)}</h1>
      <p>{esc(subtitle)}</p>
    </section>
    <div class="content-layout" data-toc-layout>
      {toc_html}
      {toc_controls}
      <article class="content">
        {body}
      </article>
    </div>
  </main>
  <footer class="footer">本網站由 repository source code、設定、測試與 evaluation datasets 產生；不包含真實營收或庫存數字。</footer>
</body>
</html>
"""


def build_index(data: dict[str, Any]) -> str:
    toc = [("quick", "快速入口"), ("path", "10 分鐘路徑"), ("principles", "核心原則"), ("urls", "正式入口")]
    body = f"""
<section id="quick">
  <h2>交接開始</h2>
  <p>使用者可以直接用中文詢問營收與庫存問題。Agent 會判斷問題、選擇受控分析工具、檢查證據是否足夠，再產生回答、表格與圖表。資料不足時，系統會嘗試合法的補充分析，或清楚說明目前無法完整回答。</p>
  <div class="quick-grid">
    <a class="quick-card" href="overview.html"><strong>第一次接觸系統</strong><span>先理解它能做什麼、資料怎麼進來、哪些邊界不能越過。</span></a>
    <a class="quick-card" href="operations.html"><strong>我要現場展示</strong><span>照五分鐘 Demo 腳本開 Dashboard、問問題、看 Tool 與 health。</span></a>
    <a class="quick-card" href="maintenance.html"><strong>我要接手修改</strong><span>從新增 Tool、KPI、問題類型三個配方開始。</span></a>
  </div>
</section>
<section id="path">
  <h2>10 分鐘最短閱讀路徑</h2>
  <ol class="steps">
    <li><a href="overview.html">系統總覽</a><span>知道支援能力與刻意不做的事。</span></li>
    <li><a href="question-journey.html">一題怎麼跑</a><span>看懂一個問題如何變成工具執行與受限回答。</span></li>
    <li><a href="tools.html">Tool 工具箱</a><span>查完整 ToolContract、參數、evidence 與測試。</span></li>
    <li><a href="operations.html">展示與操作</a><span>照腳本實際啟動與展示。</span></li>
  </ol>
</section>
<section id="principles">
  <h2>系統核心原則</h2>
  <div class="principle-grid">
    <div><strong>Agent 負責規劃</strong><p>Agent 判斷現在該查什麼，不直接任意計算或讀檔。</p></div>
    <div><strong>Tool 負責計算</strong><p>營收、庫存、趨勢、排名與圖表由 deterministic tools 執行。</p></div>
    <div><strong>Registry 是邊界</strong><p>每個工具的 args、KPI、task family、evidence type 與 MCP exposure 都在 ToolContract 中定義。</p></div>
    <div><strong>證據不足不硬湊</strong><p>Evidence Validator 會要求 primary evidence；合法補證失敗時回 partial 或 capability gap。</p></div>
    <div><strong>主動洞察需人工核准</strong><p>Proactive draft 只有經 approval 與 publication gate 才能發布 artifact。</p></div>
  </div>
</section>
<section id="urls">
  <h2>正式網址與系統入口</h2>
  <div class="url-list">
    <div><span>Handoff URL</span><code data-url-template="handoff">由目前 host 產生</code></div>
    <div><span>Dashboard URL</span><code data-url-template="dashboard">由目前 host 產生</code></div>
    <div><span>Backend health URL</span><code data-url-template="health">由目前 host 產生</code></div>
  </div>
  <details><summary>工程細節</summary>
    <p>Next.js 靜態 public route 會把 <code>frontend/public/handoff/index.html</code> 提供為 <code>/handoff/</code>；Frontend API proxy 由 <code>frontend/lib/python-api.js</code> 的 <code>PYTHON_API_BASE</code> 指到 Python backend。</p>
  </details>
</section>
"""
    return layout("index.html", "Revenue Intelligence POC 營收與庫存 Agentic AI 分析系統交接", "先理解系統，再看一次問答、工具、安全邊界與修改配方。", body, toc)




def stat_cards(items: Iterable[tuple[str, Any, str]]) -> str:
    cards = []
    for label, value, note in items:
        cards.append(f'<div class="stat"><strong>{esc(value)}</strong><span>{esc(label)}</span><p>{esc(note)}</p></div>')
    return '<div class="stats-grid">' + ''.join(cards) + '</div>'


def status_badge(status: str) -> str:
    mapping = {
        "full": ("可使用", "ok"),
        "intentional_legacy": ("可使用", "ok"),
        "unsupported": ("不支援", "bad"),
    }
    label, cls = mapping.get(status, ("有限制", "warn"))
    return f'<span class="status {cls}">{esc(label)}</span>'


def execution_badge(status: str) -> str:
    mapping = {
        "full": ("Agentic evidence-validated", "ok"),
        "intentional_legacy": ("受控 deterministic", "ok"),
        "unsupported": ("安全拒絕", "bad"),
    }
    label, cls = mapping.get(status, ("有明確限制", "warn"))
    return f'<span class="status {cls}">{esc(label)}</span>'

def build_overview(data: dict[str, Any]) -> str:
    semantic = data["semantic"]
    coverage_rows = "".join(
        f"<tr><td>{esc(TASK_LABELS.get(item['task_type'], item['task_type']))}</td>"
        f"<td><code>{esc(item['task_type'])}</code></td>"
        f"<td>{status_badge(item['coverage_status'])}</td>"
        f"<td>{execution_badge(item['coverage_status'])}</td>"
        f"<td>{esc(item.get('required_limitation',''))}</td></tr>"
        for item in semantic["task_coverage"]
    )
    metrics = "".join(
        f"<tr><td>{esc(m['display_name'])}</td><td><code>{esc(m['metric_id'])}</code></td><td>{esc(m['formula_description'])}</td><td>{'是' if m.get('is_proxy') else '否'}</td><td>{chips(m.get('supported_operations', []), 5)}</td></tr>"
        for m in semantic["metrics"]
    )
    dims = "".join(
        f"<tr><td>{esc(d['display_name'])}</td><td><code>{esc(d['dimension_id'])}</code></td><td>{esc(d['description'])}</td><td>{chips(d.get('allowed_metrics', []), 4)}</td></tr>"
        for d in semantic["dimensions"]
    )
    toc = [("questions", "能回答什麼"), ("boundaries", "刻意不做"), ("data", "資料來源"), ("outputs", "輸出"), ("map", "總圖")]
    body = f"""
<section id="questions">
  <h2>系統能回答哪些問題</h2>
  <p>這套系統可以用中文查營收與庫存。它不是讓 Agent 自由寫程式，而是讓 Agent 選擇受控的分析工具（Tool），再用回答證據（Evidence）決定能不能完整回答。</p>
  <p>下表把「能不能用」和「怎麼執行」拆開看：走固定規則、可重現的 deterministic 流程，不代表功能沒完成；它表示這題不需要 LLM 才能穩定回答。</p>
  <div class="table-wrap"><table><thead><tr><th>中文用途</th><th>task family</th><th>功能狀態</th><th>執行方式</th><th>限制</th></tr></thead><tbody>{coverage_rows}</tbody></table></div>
  <div class="callout">穩定展示題型包含：查詢某月營收或庫存、比較兩個月份、比較事業群或產品線、查看排名、查看趨勢、找異常或風險訊號、分析營收與庫存的描述性關係、產生圖表，以及資料更新後產生待審查主動洞察。</div>
</section>
<section id="boundaries">
  <h2>系統刻意不做什麼</h2>
  <ul class="check-list">
    <li>不提供任意 Python、SQL 或 shell；Agent 只能選 registry 中的工具。</li>
    <li>不允許任意檔案路徑；MCP arguments 出現 <code>/</code>、<code>\\</code> 或 <code>..</code> 會被拒絕。</li>
    <li>不將描述性關係寫成因果；Writer Validator 會抓「導致」等根因宣稱。</li>
    <li>不把 <code>revenue_inventory_amount_ratio</code> 說成正式 turnover；semantic catalog 明確標示為 proxy。</li>
    <li>沒有 primary evidence 時不假裝完整回答；runtime 會重新規劃（Replan）或安全停止。</li>
    <li>主動草稿不自動發布；必須先 approve，再 publish。</li>
    <li>MCP 不可操作 approval 或 publication，只公開 allowlisted read-only tools。</li>
  </ul>
</section>
<section id="data">
  <h2>使用哪些資料</h2>
  <div class="diagram-card"><img src="assets/diagrams/data-flow.svg" alt="資料流圖"></div>
  <p>正式資料來源由 <code>config.py</code> 定義為 <code>data/inventory.xlsx</code> 與 <code>data/revenue.xlsx</code>。<code>analysis_pipeline.build_pipeline_context()</code> 負責建立共用 context，<code>real_data.py</code> 與 <code>data_loader.py</code> 負責正規化與對齊；Frontend 不直接讀 Excel。</p>
  <h3>KPI</h3><div class="table-wrap"><table><thead><tr><th>名稱</th><th>metric_id</th><th>計算口徑</th><th>proxy</th><th>操作</th></tr></thead><tbody>{metrics}</tbody></table></div>
  <h3>Dimension</h3><div class="table-wrap"><table><thead><tr><th>名稱</th><th>dimension_id</th><th>說明</th><th>允許 KPI</th></tr></thead><tbody>{dims}</tbody></table></div>
</section>
<section id="outputs">
  <h2>系統可能產生哪些輸出</h2>
  <div class="term-grid">
    <div><strong>文字回答</strong><p>由 answer contract render，受 Evidence 與 validator 限制。</p></div>
    <div><strong>表格</strong><p>Tool result 或 display block，可供 Dashboard 顯示。</p></div>
    <div><strong>圖表</strong><p><code>get_chart_payload</code> 回傳 chart-ready JSON，必要時可輸出 PNG 到 <code>output/charts</code>。</p></div>
    <div><strong>Partial answer</strong><p>有部分證據，但不足以完整回答。</p></div>
    <div><strong>Limitation</strong><p>資料、proxy、coverage 或工具能力限制。</p></div>
    <div><strong>Capability gap</strong><p>沒有合法工具能補足缺失證據。</p></div>
    <div><strong>Trace</strong><p>本地 SQLite trace，預設 <code>output/observability/traces.sqlite3</code>。</p></div>
    <div><strong>Proactive draft</strong><p>主動偵測後產生的待審查草稿。</p></div>
    <div><strong>Approval／publication artifact</strong><p>核准與發布後寫入 <code>output/investigations</code>。</p></div>
  </div>
  <details><summary>工程細節：輸出與 state 儲存位置</summary><p><code>config.py</code> 定義 <code>OUTPUT_DIR = BASE_DIR / "output"</code>、<code>CHART_DIR = OUTPUT_DIR / "charts"</code>。Stateful Agent runs 寫入 <code>output/state/agent_runs.sqlite3</code>；Proactive workflow 寫入 <code>output/state/proactive_workflow.sqlite3</code>；trace 預設寫入 <code>output/observability/traces.sqlite3</code>。</p></details>
</section>
<section id="map">
  <h2>簡化系統總圖</h2>
  <div class="diagram-card"><img src="assets/diagrams/system-overview.svg" alt="簡化系統總圖"></div>
</section>
"""
    return layout("overview.html", "系統總覽", "先用業務語言理解能力、資料、輸出與安全邊界。", body, toc)


def plain_code_snippets() -> dict[str, str]:
    return {
        "task_profile": """@dataclass(frozen=True)
class TaskProfile:
    task_type: str
    months: list[str]
    metrics: list[str]
    entity_scope: str | None = None


def build_task_profile(question: str) -> TaskProfile:
    months = extract_months(question)
    metrics = detect_metrics(question)
    task_type = detect_task_family(question)
    # ...其餘邏輯省略
    return TaskProfile(task_type=task_type, months=months, metrics=metrics)
""".strip(),
        "canonical": """@dataclass(frozen=True)
class CanonicalTaskProfile:
    task_family: str
    periods: tuple[str, ...]
    metrics: tuple[str, ...]
    dimensions: tuple[str, ...]

    @classmethod
    def from_task_profile(cls, profile: TaskProfile) -> "CanonicalTaskProfile":
        # ...其餘邏輯省略
        return cls(
            task_family=profile.task_type,
            periods=tuple(profile.months),
            metrics=tuple(profile.metrics),
            dimensions=tuple(_normalize_dimensions(profile)),
        )
""".strip(),
        "answer_plan": """AnswerPlan(
    task_family="metric_relationship_analysis",
    primary_evidence=["metric_relationship"],
    supporting_evidence=["entity_period_pair_table"],
    allowed_tools=["get_revenue_inventory_relationship"],
    forbidden_tools=["forecast", "arbitrary_python"],
    # ...其餘邏輯省略
)
""".strip(),
        "evidence_validator": """def validate(self, records: list[ToolExecutionRecord], requirement: SemanticRequirement):
    evidence_types = {record.evidence_type for record in records}
    missing = set(requirement.primary_evidence) - evidence_types
    if missing:
        return EvidenceValidationResult(
            status="insufficient",
            missing_primary_evidence=sorted(missing),
        )
    # ...其餘邏輯省略
    return EvidenceValidationResult(status="sufficient")
""".strip(),
        "writer_validator": """def validate_answer(answer: AnswerContract) -> WriterValidationResult:
    checks = [
        validate_numbers(answer),
        validate_months(answer),
        validate_proxy_language(answer),
        validate_forecast_boundary(answer),
        validate_debug_redaction(answer),
    ]
    # ...其餘邏輯省略
    return combine_checks(checks)
""".strip(),
        "ranking_method": """def get_entity_metric_ranking(self, period: str, metric: str, entity: str = "business_group"):
    period = normalize_period(period)
    metric = normalize_metric(metric)
    snapshot = self.get_entity_performance_snapshot(period=period, entity=entity)
    rows = _rank_rows_from_snapshot(snapshot, metric)
    result = {
        "period": period,
        "metric": metric,
        "entity": entity,
        "rows": rows,
        "limitations": snapshot.get("limitations", []),
    }
    # ...其餘邏輯省略
    return make_json_safe(result)
""".strip(),
        "ranking_contract": """"get_entity_metric_ranking": ToolContract(
    name="get_entity_metric_ranking",
    description="Rank entities by a supported metric for one period.",
    allowed_arguments=("period", "metric", "entity", "limit"),
    required_arguments=("period", "metric"),
    supported_metrics=("revenue_amount", "inventory_amount", "inventory_qty"),
    supported_task_families=("entity_ranking", "cross_section_compare"),
    evidence_type="entity_metric_ranking",
    read_only=True,
    risk=ToolRisk.LOW,
    mcp_exposable=True,
),
""".strip(),
        "task_detection": """def build_task_profile(question: str) -> TaskProfile:
    if _is_entity_period_pair_table_lookup(question):
        task_type = "entity_period_pair_table_lookup"
    elif _is_ranking_request(question):
        task_type = "entity_ranking"
    elif _is_forecast_request(question):
        task_type = "forecast_unsupported"
    else:
        task_type = "metric_lookup"
    # ...其餘邏輯省略
    return TaskProfile(task_type=task_type, months=extract_months(question))
""".strip(),
    }


def build_question_journey(data: dict[str, Any]) -> str:
    snippets = plain_code_snippets()
    toc = [("step1", "看懂問題"), ("step2", "需要證據"), ("step3", "執行工具"), ("step4", "檢查證據"), ("step5", "驗證回答")]
    body = f"""
<section class="notice">
  <strong>教學問題</strong>
  <p>「2025 年 2 月到 3 月，某事業群是否出現營收下降、庫存上升？」以下所有數字都是教學用虛構資料，不是公司真實數據；JSON 結構依目前程式欄位整理。</p>
</section>
<section id="step1">
  <h2>第一步：看懂問題</h2>
  <p>系統先把中文問題拆成幾個交接時最重要的欄位：時間、對象、KPI、問題類型。這一步不是計算，而是把自然語言整理成後面可驗證的任務。</p>
  <div class="mini-grid"><div><strong>時間</strong><code>2025-02 → 2025-03</code></div><div><strong>對象</strong><code>business_group</code></div><div><strong>KPI</strong><code>revenue_amount, inventory_amount</code></div><div><strong>問題類型</strong><code>metric_relationship_analysis</code></div></div>
  <details><summary>工程細節：TaskProfile 與 CanonicalTaskProfile</summary>{snippet_block(snippets['task_profile'], "python", "task_profile.py", "TaskProfile / build_task_profile()", "看它如何保存 task family、時間、實體與 KPI。")}{snippet_block(snippets['canonical'], "python", "canonical_task.py", "CanonicalTaskProfile.from_task_profile()", "看它如何把問題整理成後續驗證可使用的穩定 schema。")}</details>
</section>
<section id="step2">
  <h2>第二步：決定需要哪些證據</h2>
  <p>要回答這題，不能只看到單一月份或單一 KPI。系統需要能比較兩個月份的營收與庫存，並且要把這些資料當成主要回答證據（primary evidence）。</p>
  <details open><summary>這題需要的回答證據（Evidence）</summary>
    <ul class="check-list"><li>主要證據：<code>metric_relationship</code></li><li>輔助證據：表現快照、趨勢或 anomaly，可用來補充，但不能取代主要證據。</li><li>禁止當主要證據的工具：<code>get_root_cause_candidates</code>、<code>get_contribution_analysis(revenue)</code>。</li></ul>
  </details>
  <details><summary>工程細節：AnswerPlan 節錄</summary>{snippet_block(snippets['answer_plan'], "python", "answer_plan.py", "build_answer_plan() / metric_relationship_analysis", "看 primary/supporting/background/forbidden tools 如何被固定下來。")}</details>
</section>
<section id="step3">
  <h2>第三步：選擇並執行工具</h2>
  <p>Agent 決定要用哪個分析工具（Tool），真正計算由 <code>AnalysisToolbox</code> 執行。執行前，Plan Validator 會先確認工具名稱、允許參數、KPI、時間與 entity 都合法。</p>
  <div class="tool-call-demo">
    <div><h3>Agent 產生 Tool Call</h3>{code_block(json.dumps({"tool_name":"get_revenue_inventory_relationship","args":{"entity_dimension":"business_group","recent_n":2},"reason":"需要成對比較營收與庫存變化"}, ensure_ascii=False, indent=2), "json")}<p class="code-note"><strong>重點：</strong>這是教學用虛構 tool call；欄位名稱依目前 planner/tool call 結構整理。</p></div>
    <div><h3>Tool Result 範例</h3>{code_block(json.dumps({"source_tool":"get_revenue_inventory_relationship","evidence_type":"metric_relationship","entity_dimension":"business_group","rows":[{"entity_value":"教學事業群 A","revenue_change":-1200,"inventory_change":830,"relationship_label":"營收下降、庫存上升","period_start":"2025-02","period_end":"2025-03"}],"limitations":["僅描述歷史資料，不做 root cause claim。"]}, ensure_ascii=False, indent=2), "json")}<p class="code-note"><strong>重點：</strong>數字為教學虛構資料，不是公司真實數據。</p></div>
  </div>
</section>
<section id="step4">
  <h2>第四步：檢查證據是否足夠</h2>
  <div class="flow-three">
    <div><strong>證據足夠</strong><span>→ 產生回答</span></div>
    <div><strong>證據不足，但有合法替代工具</strong><span>→ 重新規劃（Replan）→ 再執行工具</span></div>
    <div><strong>沒有合法工具能補足</strong><span>→ Partial Answer → Capability Gap</span></div>
  </div>
  <p>Replan 和 Retry 不一樣：Retry 是同一步重試；Replan 是因為缺少回答證據，新增一個 registry 允許且尚未重複的工具。這個 repo 的 replanner 是保守修補，不會任意發明工具。</p>
  <details><summary>工程細節：Evidence Validator 節錄</summary>{snippet_block(snippets['evidence_validator'], "python", "agent_runtime/evidence_validator.py", "EvidenceValidator.validate()", "看關係分析如何要求成對營收與庫存 evidence。")}</details>
</section>
<section id="step5">
  <h2>第五步：產生並驗證回答</h2>
  <p>回答產生後還會再檢查一次：數字、月份、實體與 KPI 必須來自證據；proxy 不能說成正式指標；描述性關係不能寫成因果；不支援的 forecast 不能偷渡成預測。</p>
  <div class="example-stack">
    <div class="example ok"><strong>正常完成案例</strong><p>主要 relationship evidence 有 rows，月份與 KPI 都涵蓋，回答以「描述性關係」呈現。</p></div>
    <details><summary>valuable replan 案例</summary><p>初次工具結果缺少庫存數量的補充觀察；Evidence Validator 標示缺口，Replanner 補上 <code>get_entity_trend_comparison</code>。</p></details>
    <details><summary>capability gap 案例</summary><p>使用者要求預測下個月是否改善。<code>forecast_unsupported</code> 沒有合法 primary tool，系統應清楚說明目前不支援預測，而不是硬湊答案。</p></details>
  </div>
  <details><summary>工程細節：Writer Validator 節錄</summary>{snippet_block(snippets['writer_validator'], "python", "writer_validator.py", "WriterValidator._validate()", "看回答文字會被哪些安全規則擋下。")}</details>
</section>
"""
    return layout("question-journey.html", "一題怎麼跑", "用一個虛構問題看懂 Agent、分析工具、回答證據、重新規劃與回答驗證。", body, toc)

def build_tools(data: dict[str, Any]) -> str:
    catalog = data["catalog"]
    stats = catalog["stats"]
    family_options = "".join(f'<option value="{esc(k)}">{esc(TASK_LABELS.get(k,k))} ({v})</option>' for k, v in stats["task_families"].items())
    metric_options = "".join(f'<option value="{esc(k)}">{esc(k)} ({v})</option>' for k, v in stats["metrics"].items())
    evidence_options = "".join(f'<option value="{esc(k)}">{esc(k)} ({v})</option>' for k, v in stats["evidence_types"].items())
    cards = []
    for tool in catalog["tools"]:
        data_attrs = {
            "family": " ".join(tool.get("allowed_task_families") or []),
            "metric": " ".join(tool.get("supported_metrics") or tool.get("supported_metric_ids") or []),
            "evidence": tool.get("output_evidence_type") or "",
            "mcp": "yes" if tool.get("mcp_exposable") else "no",
            "legacy": "yes" if tool.get("is_legacy") else "no",
        }
        attr = " ".join(f'data-{k}="{esc(v)}"' for k, v in data_attrs.items())
        tests = tool.get("tests") or ["目前測試中未直接提及此 Tool 名稱"]
        cards.append(
            f"""
<article class="tool-card" {attr}>
  <div class="tool-card-head">
    <div><h3><code>{esc(tool['tool_name'])}</code></h3><p>{esc(tool['zh_purpose'])}</p></div>
    <div>{'<span class="badge ok">MCP</span>' if tool.get('mcp_exposable') else '<span class="badge muted">Internal</span>'}{'<span class="badge warn">Legacy</span>' if tool.get('is_legacy') else ''}</div>
  </div>
  <div class="tool-meta">
    <div><span>allowed arguments</span>{chips(tool.get('allowed_args', []))}</div>
    <div><span>required arguments</span>{chips(tool.get('required_args', []))}</div>
    <div><span>supported metrics</span>{chips(tool.get('supported_metrics', []), 8)}</div>
    <div><span>task families</span>{chips([TASK_LABELS.get(x, x) for x in tool.get('allowed_task_families', [])], 8)}</div>
    <div><span>evidence type</span><code>{esc(tool.get('output_evidence_type') or '未指定')}</code></div>
    <div><span>read-only／risk</span><code>{esc(tool.get('read_only'))} / {esc(tool.get('risk_level'))}</code></div>
    <div><span>MCP exposure</span><code>{esc(tool.get('mcp_exposable'))}</code>{'，server registered' if tool.get('mcp_registered') else ''}</div>
    <div><span>實作</span><code>{esc(source_link(tool.get('implementation_path'), tool.get('implementation_line')))}</code><br><code>{esc(tool.get('implementation_function'))}</code></div>
  </div>
  <details><summary>適合回答的問題、限制與測試</summary>
    <p>{esc(tool.get('good_for'))}</p>
    <p><strong>常見錯誤或限制：</strong>{esc('；'.join(tool.get('common_limitations') or []))}</p>
    <p><strong>對應測試：</strong>{chips(tests, 10)}</p>
    {f'<p><strong>Replacement：</strong><code>{esc(tool.get("replacement_tool"))}</code></p>' if tool.get('replacement_tool') else ''}
  </details>
</article>"""
        )
    contract_snippet = extract_snippet("tool_registry.py", '"get_entity_month_table": ToolContract', '    "get_entity_metric_value"', 60)
    mcp_tools = [tool for tool in catalog["tools"] if tool.get("mcp_exposable")]
    mcp_list = "".join(f"<li><code>{esc(t['tool_name'])}</code>：{esc(t['zh_purpose'])}</li>" for t in mcp_tools)
    toc = [("definition", "白話定義"), ("stats", "統計"), ("catalog", "完整清單"), ("contract", "ToolContract"), ("call", "Tool Call"), ("mcp", "MCP"), ("add", "新增七步")]
    body = f"""
<section id="definition"><h2>Tool 的白話定義</h2>
  <div class="term-grid"><div><strong>Agent</strong><p>決定現在該做什麼。</p></div><div><strong>Tool</strong><p>執行一次明確、受控的查詢或計算。</p></div><div><strong>Tool Registry</strong><p>規定 Tool 可以接受什麼、輸出什麼，以及能否對外開放。</p></div></div>
</section>
<section id="stats"><h2>Tool 統計</h2>
{stat_cards([("正式註冊 Tool 總數", stats["total"], "來自 TOOL_REGISTRY"), ("內部 Tool 數", stats["internal"], "mcp_exposable=false"), ("MCP 可用 Tool 數", stats["mcp_exposable"], "registry 標示可公開"), ("read-only Tool 數", stats["read_only"], "目前全部 read-only"), ("MCP server registered", stats["mcp_registered"], "server.py 實際包裝")])}
</section>
<section id="catalog"><h2>完整工具清單</h2>
  <div class="filters">
    <input id="toolSearch" type="search" placeholder="搜尋 Tool 名稱、用途、限制">
    <select id="familyFilter"><option value="">全部 task family</option>{family_options}</select>
    <select id="metricFilter"><option value="">全部 metric</option>{metric_options}</select>
    <select id="evidenceFilter"><option value="">全部 evidence type</option>{evidence_options}</select>
    <label><input id="mcpOnly" type="checkbox"> 只顯示 MCP Tool</label>
    <label><input id="internalOnly" type="checkbox"> 只顯示內部 Tool</label>
  </div>
  <div id="toolCount" class="muted"></div>
  <div class="tool-list">{''.join(cards)}</div>
</section>
<section id="contract"><h2>實際 ToolContract 程式碼</h2>
  <div class="split"><div>{code_block(contract_snippet, "python")}</div><div class="explain"><p><strong>description</strong> 是給 planner 的用途描述。</p><p><strong>required_args / optional_args</strong> 會合併成 allowed arguments。</p><p><strong>supported_metrics</strong> 與 <strong>allowed_task_families</strong> 決定這個工具能回答哪些問題。</p><p><strong>output_evidence_type</strong> 是 Evidence Validator 判斷證據的核心欄位。</p><p><strong>read_only / risk_level / mcp_exposable</strong> 決定是否能被 MCP 對外公開。</p></div></div>
</section>
<section id="call"><h2>一次 Tool Call 實例</h2>
  {code_block(json.dumps({"plan_validator":"確認 get_entity_month_table 屬於 entity_month_table_lookup，args 只含 allowed_args，metric/month/entity_dimension 合法。","tool_call":{"tool_name":"get_entity_month_table","args":{"entity_dimension":"business_group","metric":"revenue_amount","month":"2025-03"}},"tool_result":{"source_tool":"get_entity_month_table","evidence_type":"entity_month_table","metric":"revenue_amount","month":"2025-03","rows":[{"entity_value":"教學事業群 A","value":12345}],"row_count":1},"evidence_validator":"檢查 primary evidence type、metric、month 與 rows。"}, ensure_ascii=False, indent=2), "json")}
</section>
<section id="mcp"><h2>MCP Tool 子集合</h2>
  <ul>{mcp_list}</ul>
  <p>MCP 只公開 registry 中 <code>mcp_exposable=true</code>、<code>read_only=true</code>、<code>risk_level=low</code> 的工具。<code>mcp_server/security.py</code> 會拒絕 hidden tool、未知參數、缺少 required args、不合法月份、不合法 dimension/metric、<code>top_n</code> 超過 row cap、以及像檔案路徑的 unsafe argument。MCP 是外部 Agent 的受控入口，不是一般 Dashboard 問答的必經路徑。</p>
</section>
<section id="add"><h2>新增 Tool 的七步摘要</h2>
  <ol class="steps"><li>實作分析函式</li><li>登記 Tool Contract</li><li>定義 evidence type</li><li>設定 task family 與 metric</li><li>決定是否對 MCP 開放</li><li>新增 focused tests</li><li>執行 validation 與 evaluation gate</li></ol>
  <p><a class="button" href="maintenance.html">前往新增與修改配方</a></p>
</section>
"""
    return layout("tools.html", "Tool 工具箱", "完整盤點目前正式註冊工具、參數、evidence、MCP exposure 與測試。", body, toc)


def build_architecture(data: dict[str, Any]) -> str:
    file_index = data["file_index"]
    module_cards = [
        {
            "name": "Frontend",
            "purpose": "Dashboard 與靜態交接網站的使用者入口，負責把問題送到後端並呈現回答。",
            "entry": ["frontend/app/dashboard/page.js", "frontend/app/api/ask/route.js"],
            "core": ["frontend/components/insight-console.jsx", "frontend/lib/python-api.js"],
            "model": ["frontend/package.json", "frontend/next.config.mjs"],
            "upstream": "使用者瀏覽器。",
            "downstream": "Backend API。",
            "errors": "常見是 API base URL、Next 靜態資源或 dev server 快取問題。",
            "tests": ["frontend npm run build", "HTTP /dashboard"],
        },
        {
            "name": "Backend / Orchestration",
            "purpose": "接住前端問題，載入資料管線，交給 MultiAgentAssistant 產生可驗證回答。",
            "entry": ["demo_web.py", "MultiAgentAssistant.answer"],
            "core": ["analysis_pipeline.py", "multi_agent.py", "real_data.py"],
            "model": ["config.py", "PipelineContext"],
            "upstream": "Frontend API route 或直接 HTTP request。",
            "downstream": "Agent Runtime、Analysis Toolbox、health endpoint。",
            "errors": "資料檔案缺漏、pipeline 尚未載入、planner 環境變數未開。",
            "tests": ["tests/test_phase9b_demo_readiness.py", "tests/test_real_data_contract.py"],
        },
        {
            "name": "Agent Runtime",
            "purpose": "把計畫拆成可追蹤步驟，執行工具、保存狀態，並在證據不足時處理重新規劃。",
            "entry": ["agent_runtime/integration.py"],
            "core": ["agent_runtime/runtime.py", "agent_runtime/evidence_validator.py", "agent_runtime/replanner.py", "agent_runtime/state_store.py"],
            "model": ["agent_runtime/models.py"],
            "upstream": "MultiAgentAssistant 與 AnswerPlan。",
            "downstream": "Tool Registry、Evidence Validator、Writer Validator。",
            "errors": "plan step 不合法、primary evidence 不足、state checkpoint 無法寫入。",
            "tests": ["tests/test_agent_runtime.py", "tests/test_evidence_validator.py", "tests/test_agent_replanner.py"],
        },
        {
            "name": "Semantic Layer",
            "purpose": "定義 KPI、維度與每種問題需要哪些回答證據，讓 Agent 不用猜規則。",
            "entry": ["semantic_layer/catalog.py"],
            "core": ["semantic_layer/adapters.py", "semantic_layer/validation.py"],
            "model": ["semantic_layer/definitions/metrics.json", "semantic_layer/definitions/dimensions.json", "semantic_layer/definitions/task_evidence.json", "semantic_layer/definitions/task_coverage.json"],
            "upstream": "TaskProfile / CanonicalTaskProfile。",
            "downstream": "AnswerPlan、Plan Validator、Evidence Validator。",
            "errors": "metric id 拼錯、維度不相容、task evidence 沒補齊。",
            "tests": ["tests/test_semantic_catalog.py", "tests/test_semantic_validation.py"],
        },
        {
            "name": "Analysis Tools",
            "purpose": "真正讀取正規化資料並做受控計算；Agent 只能呼叫登記過的工具。",
            "entry": ["tool_registry.py", "AnalysisToolbox"],
            "core": ["analysis_tools.py", "plan_validator.py"],
            "model": ["ToolContract", "ToolRisk"],
            "upstream": "Stateful Runtime 或 MCP Server。",
            "downstream": "Revenue / Inventory Data、Evidence Validator。",
            "errors": "allowed arguments 不一致、supported metrics 未列、回傳不是 JSON-safe。",
            "tests": ["tests/test_tool_registry.py", "tests/test_analysis_tools.py", "tests/test_plan_validator.py"],
        },
        {
            "name": "MCP Server",
            "purpose": "讓外部 Agent 走受控入口查詢少數 read-only 工具，不是一般 Dashboard 問答必經路徑。",
            "entry": ["mcp_server/server.py"],
            "core": ["mcp_server/security.py"],
            "model": ["mcp_server/resources.py", "mcp_server/security.py"],
            "upstream": "外部 MCP client。",
            "downstream": "MCP allowlist、Tool Registry、AnalysisToolbox。",
            "errors": "hidden tool 被拒絕、參數未通過 schema、row cap 截斷。",
            "tests": ["tests/test_mcp_server_integration.py", "tests/test_mcp_security.py"],
        },
        {
            "name": "Proactive Workflow",
            "purpose": "資料刷新後產生待審查洞察草稿，經人工核准後才可發布。",
            "entry": ["proactive_workflow/orchestrator.py"],
            "core": ["proactive_workflow/candidate_detector.py", "proactive_workflow/investigator.py", "proactive_workflow/approval.py", "proactive_workflow/publisher.py"],
            "model": ["proactive_workflow/models.py"],
            "upstream": "資料 fingerprint 與 quality report。",
            "downstream": "Draft、Approval、Publication artifact。",
            "errors": "品質警告未審、hash chain 不符、未核准就嘗試發布。",
            "tests": ["tests/test_proactive_workflow.py", "tests/test_publication_execution_adapter.py"],
        },
        {
            "name": "Observability",
            "purpose": "保存 trace、state 與健康檢查線索，讓排錯能回到具體步驟。",
            "entry": ["observability/tracing.py"],
            "core": ["observability/store.py", "observability/metrics.py"],
            "model": ["observability/models.py"],
            "upstream": "Runtime、Backend、Evaluation。",
            "downstream": "Trace store、health response、evaluation artifact。",
            "errors": "trace 沒寫入、state 與 request id 對不起來、健康狀態警告未解讀。",
            "tests": ["tests/test_trace_store.py", "tests/test_status_apis.py"],
        },
        {
            "name": "Evaluation",
            "purpose": "用可重跑的測試題與門檻確認回答、工具使用與安全拒絕沒有退化。",
            "entry": ["evaluation/cli.py"],
            "core": ["evaluation/runner.py", "evaluation/scorecard.py"],
            "model": ["evaluation/policies/regression_gate.v1.json", "evaluation/suites"],
            "upstream": "正式服務或 execution-backed adapter。",
            "downstream": "Scorecard、Regression Gate。",
            "errors": "artifact 路徑不對、suite case 未更新、gate threshold 未通過。",
            "tests": ["uv run python -m evaluation.run_evaluation --help", "tests/test_regression_gate.py"],
        },
    ]
    def section(label: str, items: list[str]) -> str:
        if not items:
            return ""
        return f"<div class='module-section'><span>{esc(label)}</span>{chips(items, 4)}</div>"
    cards = "".join(
        "<div class='module-card'>"
        f"<h3>{esc(card['name'])}</h3><p>{esc(card['purpose'])}</p>"
        + section("正式入口", card["entry"])
        + section("核心實作", card["core"])
        + section("設定／資料模型", card["model"])
        + f"<p><strong>上游：</strong>{esc(card['upstream'])}</p>"
        + f"<p><strong>下游：</strong>{esc(card['downstream'])}</p>"
        + f"<p><strong>常見錯誤：</strong>{esc(card['errors'])}</p>"
        + f"<p><strong>focused tests：</strong>{chips(card['tests'], 4)}</p>"
        + "</div>"
        for card in module_cards
    )
    core_files = [
        "README.md", "demo_web.py", "analysis_pipeline.py", "real_data.py", "data_loader.py",
        "task_profile.py", "canonical_task.py", "multi_agent.py", "tool_registry.py", "analysis_tools.py",
        "agent_runtime/runtime.py", "agent_runtime/evidence_validator.py", "agent_runtime/replanner.py",
        "semantic_layer/catalog.py", "proactive_workflow/approval.py", "proactive_workflow/publisher.py",
        "observability/tracing.py", "evaluation/policies/regression_gate.v1.json",
    ]
    file_lookup = {f["path"]: f for group in file_index.values() for f in group}
    core_rows = "".join(
        f"<tr><td><code>{esc(path)}</code></td><td>{esc(file_lookup.get(path, {}).get('purpose', file_purpose(path)))}</td><td>{chips(file_lookup.get(path, {}).get('tests', []), 3)}</td></tr>"
        for path in core_files
    )
    toc = [("main", "主架構圖"), ("flow", "小流程圖"), ("boundary", "Tool 邊界"), ("proactive", "主動流程"), ("modules", "模組地圖"), ("files", "核心檔案")]
    body = f"""
<section id="main"><h2>真正的主架構圖</h2>
  <p>先看中央主線：使用者從 Dashboard 提問，後端把問題交給 Agent，Agent 用受控的分析工具（Tool）取得回答證據（Evidence），最後才產生回答。</p>
  <p class="diagram-caption">這張圖只畫交接最需要理解的主路徑；其他像 MCP、Observability、Evaluation 都是旁支支援模組，不是每次問答都會完整經過。</p>
  <div class="diagram-card"><img src="assets/diagrams/system-architecture.svg" alt="Revenue Intelligence POC 主架構圖"></div>
  <details><summary>工程細節：如何讀這張圖</summary><ul><li>實線是 Dashboard 問答最常走的 runtime 主線。</li><li>虛線是 MCP、Proactive、Observability、Evaluation 這類旁支或離線支援。</li><li>資料只供給 Analysis Toolbox；Agent 不直接讀任意檔案。</li><li>Evidence Validator 不通過時，才會進入 Replanner 或產生 capability gap。</li></ul></details>
</section>
<section id="flow"><h2>問答小流程圖</h2><p>這張圖適合現場口頭說明：問題先被理解，再規劃、選工具、執行、檢查證據，最後回答。</p><div class="diagram-card"><img src="assets/diagrams/question-flow.svg" alt="問答流程圖"></div></section>
<section id="boundary"><h2>Tool 安全邊界圖</h2><p>Agent 不能任意執行 Python、SQL 或 shell。它只能提出 Tool Call，並通過 Tool Registry 與參數驗證。</p><div class="diagram-card"><img src="assets/diagrams/tool-boundary.svg" alt="Tool 安全邊界圖"></div></section>
<section id="proactive"><h2>Proactive Workflow 圖</h2><p>主動洞察是另一條流程：資料刷新後產生草稿，但草稿不會自動發布，必須經人工核准。</p><div class="diagram-card"><img src="assets/diagrams/proactive-flow.svg" alt="主動洞察流程圖"></div></section>
<section id="modules"><h2>程式模組地圖</h2><p>以下只列新人最需要先認得的入口與核心實作；完整檔案搜尋放在附錄。</p><div class="module-grid">{cards}</div></section>
<section id="files"><h2>核心檔案</h2><p>這些檔案足以串起 Demo、問答主流程、Tool 安全邊界與驗收流程。</p><div class="table-wrap"><table><thead><tr><th>檔案</th><th>交接時要知道什麼</th><th>相關測試</th></tr></thead><tbody>{core_rows}</tbody></table></div></section>
"""
    return layout("architecture.html", "架構與程式地圖", "從新人視角理解主線、旁支與核心檔案。", body, toc)

def module_purpose(group: str) -> str:
    return {
        "frontend": "Dashboard、mobile UI 與 Next.js proxy route。",
        "backend／orchestration": "HTTP API、pipeline context 與 MultiAgentAssistant。",
        "agent_runtime": "checkpoint、tool execution、evidence validation、replanning 與 state store。",
        "semantic_layer": "KPI、dimension、task evidence 與 coverage 定義。",
        "analysis tools": "受控工具契約與 deterministic 計算。",
        "mcp_server": "外部 Agent 可用的 read-only allowlisted tool/resource 入口。",
        "proactive_workflow": "資料刷新後的候選偵測、調查、草稿、核准與發布。",
        "observability": "本地 trace、span、redaction 與 metrics。",
        "evaluation": "離線 suites、runner、scorecard 與 regression gate。",
        "tests": "單元、整合、acceptance 與安全邊界測試。",
    }.get(group, "目前程式中未確認")


def module_upstream(group: str) -> str:
    return {
        "frontend": "瀏覽器使用者",
        "backend／orchestration": "Frontend proxy、CLI",
        "agent_runtime": "MultiAgentAssistant.answer",
        "semantic_layer": "TaskProfile、AnswerPlan、MCP resources",
        "analysis tools": "AnswerPlan、MCP server、Proactive Workflow",
        "mcp_server": "外部 MCP client",
        "proactive_workflow": "資料刷新或 API scan",
        "observability": "runtime、MCP、approval、publication",
        "evaluation": "CLI 或交付前驗收",
        "tests": "開發者執行 pytest",
    }.get(group, "目前程式中未確認")


def module_downstream(group: str) -> str:
    return {
        "frontend": "Python backend API",
        "backend／orchestration": "AnalysisToolbox、Agent runtime、Proactive workflow",
        "agent_runtime": "AnalysisToolbox executor、state store、observability",
        "semantic_layer": "Plan/Evidence validation、MCP resources",
        "analysis tools": "Evidence、answer contract、frontend chart/table",
        "mcp_server": "AnalysisToolbox 與 observability",
        "proactive_workflow": "output/investigations、approval/publication artifacts",
        "observability": "output/observability/traces.sqlite3",
        "evaluation": "output/evaluations/runs",
        "tests": "修改回饋",
    }.get(group, "目前程式中未確認")


def module_errors(group: str) -> str:
    return {
        "frontend": "PYTHON_API_BASE 錯誤、static asset 404、build cache 未重啟。",
        "analysis tools": "ToolContract 與 method signature 不一致、metric alias 混用。",
        "semantic_layer": "新增 task/KPI 後未同步 evidence requirement。",
        "mcp_server": "registry 標示可公開但 server 未註冊，或 args validation 未涵蓋。",
        "evaluation": "run_id 不存在、gate policy threshold 未達。",
    }.get(group, "修改後 focused tests 未同步。")


def module_tests(group: str) -> list[str]:
    return {
        "analysis tools": ["tests/test_tool_registry.py", "tests/test_mcp_security.py", "tests/test_plan_validator.py"],
        "semantic_layer": ["tests/test_semantic_catalog.py", "tests/test_semantic_validation.py", "tests/test_tool_registry_semantics.py"],
        "agent_runtime": ["tests/test_agent_runtime.py", "tests/test_evidence_validator.py", "tests/test_agent_replanner.py"],
        "mcp_server": ["tests/test_mcp_security.py", "tests/test_mcp_server_integration.py", "tests/test_mcp_execution_adapter.py"],
        "proactive_workflow": ["tests/test_proactive_api.py", "tests/test_proactive_execution_adapter.py", "tests/test_approval_execution_adapter.py"],
        "evaluation": ["tests/test_regression_gate.py", "tests/test_strict_regression_gate.py", "tests/test_eval_scorecard.py"],
    }.get(group, ["依修改範圍選擇 focused tests"])


def build_operations(data: dict[str, Any]) -> str:
    eval_data = data["eval"]
    suite_rows = "".join(f"<tr><td><code>{esc(s['suite'])}</code></td><td>{s['total']}</td><td>{s['execution_backed']}</td><td>{s['synthetic']}</td><td>{chips(s['adapters'])}</td></tr>" for s in eval_data["suites"])
    toc = [("demo", "五分鐘 Demo"), ("start", "啟動方式"), ("health-warning", "health warning"), ("windows", "PowerShell"), ("linux", "Linux"), ("tests", "測試與 Evaluation"), ("troubleshoot", "排錯")]
    body = f"""
<section id="demo"><h2>五分鐘交接 Demo 腳本</h2>
  <ol class="demo-steps">
    <li><strong>開 <code>/dashboard</code></strong><span>說明這是使用者主要工作台。正常會看到摘要區、分析對話輸入框與資料觀察區。</span></li>
    <li><strong>問單月查詢</strong><span>輸入：<code>2025-03 各事業群營收</code>。觀察回答是否能列出 2025-03 的事業群營收表格。</span></li>
    <li><strong>問兩期間比較</strong><span>輸入：<code>比較 2025-02 和 2025-03 各事業群營收變化</code>。這題適合說明系統會走固定規則、可重現的 deterministic 流程，取得兩個月份可比較資料。</span></li>
    <li><strong>開 Tool 工具箱</strong><span>開 <code data-url-template="handoffTools">/handoff/tools.html</code>。如果 Dashboard 沒有顯示 trace 或 tool 區塊，就從工具箱說明這題會用到哪種工具。</span></li>
    <li><strong>搜尋 Tool</strong><span>在工具箱搜尋：<code>get_entity_period_pair_table</code>。說明它適合支援兩期間、依 entity 分組的比較表。</span></li>
    <li><strong>展示安全拒絕</strong><span>回 Dashboard 問：<code>預測下個月營收會不會改善</code>。正常情況會說明目前不支援預測，而不是硬湊答案。</span></li>
    <li><strong>開健康檢查</strong><span>開 <code data-url-template="health">/api/health</code>。若 status 是 warning，請看下一段說明，不要只用顏色判斷系統壞掉。</span></li>
  </ol>
</section>
<section id="start"><h2>正式啟動方式</h2>
  <div class="split"><div><h3>Backend</h3>{code_block('USE_LLM_PLANNER=true uv run python demo_web.py', 'bash')}<p>若展示希望讓 LLM Planner 保持開啟，啟動後端時要帶 <code>USE_LLM_PLANNER=true</code>。一般 deterministic Demo 不依賴 LLM Planner，但開著可以展示 Agentic planning 路徑。</p></div><div><h3>Frontend</h3>{code_block('cd frontend\nnpm run dev -- --hostname 0.0.0.0 --port 3000', 'bash')}<p>Handoff site 由 <code>frontend/public/handoff/</code> 提供，不需要另一個 handoff server。</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>入口</th><th>URL</th><th>用途</th></tr></thead><tbody>
    <tr><td>Dashboard</td><td><code data-url-template="dashboard">/dashboard</code></td><td>現場 Demo 與一般問答。</td></tr>
    <tr><td>Handoff</td><td><code data-url-template="handoff">/handoff/</code></td><td>新人交接教材。</td></tr>
    <tr><td>Backend health</td><td><code data-url-template="health">/api/health</code></td><td>確認 API、pipeline 與 planner 狀態。</td></tr>
  </tbody></table></div>
</section>
<section id="health-warning"><h2>health warning 怎麼看</h2>
  <div class="callout"><p>目前 <code>/api/health</code> 可以是 HTTP 200，但 <code>status=warning</code>。這代表服務有回應、pipeline 已載入，但資料品質檢查提醒維護者要注意解讀限制。</p></div>
  <ul>
    <li><strong>warning 原因：</strong>目前 <code>/api/pipeline-status</code> 回報兩個資料對齊提醒：「有新事業群只出現在庫存：未對應」，以及存在 revenue-only / inventory-only rows。</li>
    <li><strong>對 deterministic Demo 的影響：</strong>不影響本次交接展示中的單月營收、兩期間比較與預測安全拒絕。</li>
    <li><strong>對 LLM Planner 的影響：</strong>LLM Planner 可以開啟並回答，但回答仍要遵守證據檢查與限制描述。</li>
    <li><strong>對 Proactive 的影響：</strong>可以產生草稿，但發布前應特別看資料品質 warning；主動草稿仍需人工核准。</li>
  </ul>
</section>
<section id="windows"><h2>Windows PowerShell 常用命令</h2>{code_block('netstat -ano | findstr :3000\nGet-Process -Id <PID> | Select-Object Id,ProcessName,StartTime,Path\nStop-Process -Id <PID>\n$env:USE_LLM_PLANNER="true"\nuv run python demo_web.py', 'powershell')}</section>
<section id="linux"><h2>Server / Linux 常用命令</h2>{code_block('ss -ltnp | grep -E ":(3000|8765)"\nps -eo pid,ppid,etime,cmd | grep -E "demo_web|next dev"\ntmux new -s revenue-poc\n# backend\nUSE_LLM_PLANNER=true uv run python demo_web.py\n# frontend\ncd frontend && npm run dev -- --hostname 0.0.0.0 --port 3000\ntail -f /tmp/rvn_frontend.log', 'bash')}<p>停止服務前先確認 PID、啟動時間與命令內容；不要直接對不明 process 使用強制停止。</p></section>
<section id="tests"><h2>測試與 Evaluation</h2>
  <div class="table-wrap"><table><thead><tr><th>時機</th><th>命令</th><th>預期</th></tr></thead><tbody>
    <tr><td>最快健康檢查</td><td><code>uv run python scripts/validate_handoff_site.py</code></td><td>靜態網站連結、資源與 Tool catalog 一致。</td></tr>
    <tr><td>修改 Tool 後</td><td><code>uv run pytest tests/test_tool_registry.py tests/test_analysis_tools.py</code></td><td>Registry 與工具輸出契約不退化。</td></tr>
    <tr><td>修改 Semantic Layer 後</td><td><code>uv run pytest tests/test_semantic_catalog.py tests/test_semantic_validation.py</code></td><td>KPI、維度與 evidence 定義可載入。</td></tr>
    <tr><td>修改 Runtime 後</td><td><code>uv run pytest tests/test_agent_runtime.py tests/test_evidence_validator.py tests/test_agent_replanner.py</code></td><td>執行、證據檢查與重新規劃正常。</td></tr>
    <tr><td>完整交付前</td><td><code>uv run python -m evaluation.run_evaluation --help</code></td><td>確認 evaluation CLI 可用，再依政策執行指定 suite。</td></tr>
  </tbody></table></div>
  <details><summary>目前 evaluation suite 摘要</summary><div class="table-wrap"><table><thead><tr><th>suite</th><th>cases</th><th>execution-backed</th><th>synthetic</th><th>adapters</th></tr></thead><tbody>{suite_rows}</tbody></table></div></details>
</section>
<section id="troubleshoot"><h2>常見故障排除</h2>
  <div class="faq-grid">
    <details><summary>port already in use</summary><p>用 <code>ss -ltnp</code> 或 PowerShell <code>netstat -ano</code> 找 PID，再確認 process start time。只停止自己啟動的服務。</p></details>
    <details><summary>Frontend 連不到 Backend</summary><p>檢查 <code>PYTHON_API_BASE</code>、<code>/api/health</code>、backend port 8765 是否在聽。</p></details>
    <details><summary>原始碼已改但頁面仍是舊版</summary><p>重新執行 generator，必要時重啟 Next dev server；build 後若 chunk 不一致，也要重啟 frontend。</p></details>
    <details><summary>缺少資料檔案</summary><p>看 <code>config.py</code> 與 health response 的 data path / warning。不要在 handoff site 放真實資料。</p></details>
    <details><summary>Tool 沒出現在 Registry</summary><p>確認 <code>tool_registry.py</code> 有 ToolContract，且測試更新。</p></details>
    <details><summary>MCP Tool 沒出現</summary><p>確認 ToolContract 允許 MCP exposure，並與 <code>mcp_server/server.py</code> registration 一致。</p></details>
    <details><summary>semantic validation fail</summary><p>通常是 metric、dimension 或 task evidence 定義不一致；先查 Semantic Layer 定義檔。</p></details>
    <details><summary>evaluation run 找不到</summary><p>確認 evaluation output path 與 generated artifacts。artifact 是驗收結果，不是 production source。</p></details>
    <details><summary>static handoff 某頁 404</summary><p>確認檔案在 <code>frontend/public/handoff/</code>，內部連結使用 <code>.html</code> 或 <code>/handoff/</code>。</p></details>
    <details><summary>CSS / JS 路徑錯誤</summary><p>所有資源應使用相對路徑 <code>assets/...</code>；不要使用 <code>file scheme</code>、外部 CDN 或 localhost 靜態資源。</p></details>
  </div>
</section>
"""
    return layout("operations.html", "展示與操作", "五分鐘 Demo、啟動方式、健康檢查與排錯。", body, toc)

def trouble(title: str, body: str) -> str:
    return f"<details><summary>{esc(title)}</summary><p>{esc(body)}</p></details>"


def build_maintenance(data: dict[str, Any]) -> str:
    snippets = plain_code_snippets()
    metric_example = compact_json({
        "metric_id": "revenue_inventory_amount_ratio",
        "display_name_zh": "營收庫存金額比",
        "category": "relationship",
        "semantic_type": "ratio",
        "supported_dimensions": ["business_group", "product_line"],
        "proxy_warning": "這是描述性 proxy，不是正式 turnover。",
    })
    toc = [("recipes", "情境入口"), ("tool", "新增 Tool"), ("kpi", "新增 KPI"), ("task", "新增問題類型"), ("advanced", "進階")]
    body = f"""
<section id="recipes"><h2>我想做什麼？</h2>
  <div class="table-wrap"><table><thead><tr><th>我想做什麼</th><th>應從哪個配方開始</th></tr></thead><tbody>
    <tr><td>新增一種分析計算</td><td><a href="#tool">新增 Tool</a></td></tr>
    <tr><td>新增 KPI</td><td><a href="#kpi">新增 Metric + 更新 Tool</a></td></tr>
    <tr><td>支援新的問題型態</td><td><a href="#task">新增 Task Family</a></td></tr>
    <tr><td>對外部 Agent 開放工具</td><td><a href="#advanced">MCP Exposure</a></td></tr>
    <tr><td>新增主動偵測規則</td><td><a href="#advanced">Proactive Detector</a></td></tr>
    <tr><td>修改品質門檻</td><td><a href="#advanced">Evaluation Gate</a></td></tr>
  </tbody></table></div>
</section>
<section id="tool"><h2>配方一：新增分析工具（Tool）</h2>
  <p>當既有 Tool 無法取得某種受控分析結果時，才新增 Tool。不要把自由 Python、SQL 或任意檔案讀取包成 Tool。</p>
  <ol>
    <li>在 <code>analysis_tools.py</code> 加一個明確、read-only、JSON-safe 的 method。</li>
    <li>在 <code>tool_registry.py</code> 登記 ToolContract，列出 allowed arguments、supported metrics、task families 與 evidence type。</li>
    <li>確認 <code>plan_validator.py</code> 能用 ToolContract 檢查這個 call。</li>
    <li>決定是否 MCP exposable；預設不要公開，除非參數和輸出都能安全控管。</li>
    <li>補 focused tests，再跑 handoff validator 與相關 evaluation gate。</li>
  </ol>
  {snippet_block(snippets['ranking_method'], 'python', 'analysis_tools.py（簡化示意碼；保留交接重點）', 'AnalysisToolbox.get_entity_metric_ranking', '看 input normalization、snapshot 取得、result 結構與 limitations 概念。')}
  {snippet_block(snippets['ranking_contract'], 'python', 'tool_registry.py（原始 ToolContract 節錄）', 'TOOL_REGISTRY["get_entity_metric_ranking"]', '看 Tool Registry 如何限制參數、metric、task family、evidence type、read-only 與 MCP exposure。')}
  <details><summary>不能破壞的契約</summary><ul><li>Tool result 必須 JSON-safe。</li><li>不要回傳未 redaction 的 raw trace 或真實敏感資料。</li><li>沒有 primary evidence 時，不要讓回答看起來完整。</li><li>MCP Tool 必須通過 allowlist、argument validation、row cap 與 sanitization。</li></ul></details>
  <details><summary>最少測試與完整驗收</summary>{code_block('uv run pytest tests/test_tool_registry.py tests/test_analysis_tools.py tests/test_plan_validator.py\nuv run python scripts/generate_handoff_site.py\nuv run python scripts/validate_handoff_site.py', 'bash')}</details>
</section>
<section id="kpi"><h2>配方二：新增 KPI</h2>
  <p>新增 KPI 不是只加一個欄位名稱。你要同時確認資料有來源、維度能相容、Tool 支援查詢，以及回答證據規則知道怎麼驗證它。</p>
  {snippet_block(metric_example, 'json', 'semantic_layer/definitions/metrics.json（簡化示意碼）', 'metric definition', '看 metric id、中文名稱、語意類型、可用維度與 proxy 限制如何寫清楚。')}
  <ul><li><strong>資料與計算：</strong>確認 <code>data_loader.py</code> / <code>real_data.py</code> 能產生需要的欄位或計算。</li><li><strong>Tool 支援：</strong>把 metric 加到相關 ToolContract 的 supported metrics。</li><li><strong>證據需求：</strong>若 KPI 會改變回答條件，更新 <code>task_evidence.json</code>。</li><li><strong>回答格式：</strong>需要 proxy warning 時，Writer Validator 不能把它寫成正式財務結論。</li></ul>
  <details><summary>最少測試</summary>{code_block('uv run pytest tests/test_semantic_catalog.py tests/test_semantic_validation.py tests/test_tool_registry.py', 'bash')}</details>
</section>
<section id="task"><h2>配方三：新增問題類型</h2>
  <p>問題類型（task family）決定系統如何理解問題、需要哪些證據、可以用哪些 Tool，以及證據不足時要補問、重新規劃或標示 capability gap。</p>
  {snippet_block(snippets['task_detection'], 'python', 'task_profile.py（節錄後省略非重點邏輯）', 'build_task_profile', '看自然語句如何被歸類成 task family。')}
  {snippet_block(snippets['answer_plan'], 'python', 'semantic_layer/catalog.py（節錄後省略非重點邏輯）', 'AnswerPlan / Semantic Requirement', '看 task family 如何連到可用 Tool 與 primary evidence。')}
  <ul><li><strong>Detection：</strong>在 TaskProfile / Canonical Task 補上辨識規則。</li><li><strong>AnswerPlan：</strong>定義允許的 Tool、metric、維度與 evidence requirement。</li><li><strong>Partial / Unsupported：</strong>沒有合法 Tool 時應回 capability gap，不要硬湊答案。</li><li><strong>Tests：</strong>補 detection、plan validation、evidence validation 與 writer validation。</li></ul>
</section>
<section id="advanced"><h2>進階修改</h2>
  <div class="faq-grid">
    <details><summary>MCP Exposure</summary><p>先確認 Tool 是 read-only、參數可完整驗證、輸出可 sanitization 且有 row cap。再同步 <code>tool_registry.py</code> 與 <code>mcp_server/server.py</code>。</p></details>
    <details><summary>Proactive Detector</summary><p>新增偵測規則後，要讓 Candidate、Investigation、Draft、Approval 都能留下可追蹤 artifact；不能繞過人工核准。</p></details>
    <details><summary>Evaluation Gate</summary><p>修改 <code>evaluation/policies/regression_gate.v1.json</code> 前，要確認 threshold 是正式門檻，不是為了讓一次結果過關而放寬。</p></details>
  </div>
</section>
"""
    return layout("maintenance.html", "新增與修改", "新增 Tool、KPI 與問題類型的安全配方。", body, toc)

def build_appendix(data: dict[str, Any]) -> str:
    eval_data = data["eval"]
    file_index = data["file_index"]
    terms = [
        ("LLM vs Agent", "LLM 是文字模型；Agent 是會規劃、選工具、檢查證據的流程。", "OllamaClient / MultiAgentAssistant", "LLM 不等於可以任意動作。"),
        ("Agent vs Tool", "Agent 決定做什麼；分析工具（Tool）做一次受控計算。", "MultiAgentAssistant / AnalysisToolbox", "Tool 不是自由執行器。"),
        ("State vs Trace", "State 是一次回答的可恢復狀態；Trace 是排錯與觀測紀錄。", "AgentRunState / SQLiteTraceStore", "State 給 runtime，trace 給排錯和 evaluation。"),
        ("Plan vs AnswerPlan", "Plan 是具體 Tool calls；AnswerPlan 是問題類型的工具邊界。", "PlanStep / AnswerPlan", "LLM plan 必須符合 deterministic AnswerPlan。"),
        ("Tool Result vs Evidence", "Tool result 是原始回傳；回答證據（Evidence）是整理後給 validator 判斷的材料。", "ToolExecutionRecord / evidence", "有 result 不代表 evidence 足夠。"),
        ("Primary vs Supporting Evidence", "Primary 是回答必需證據；Supporting 是輔助補充。", "SemanticRequirement", "缺 primary 時要 partial 或 capability gap。"),
        ("Replan vs Retry", "重新規劃（Replan）是換合法工具補證據；Retry 是同一步重試。", "Replanner", "證據不足通常不是單純 retry。"),
        ("Capability Gap vs Error", "Capability gap 是目前能力邊界；Error 是執行失敗。", "AnswerContract", "能力不足要說清楚，不要偽裝成完整回答。"),
        ("Approval vs Publication", "Approval 是核准草稿；Publication 是產生正式發布 artifact。", "ApprovalDecision / PublicationArtifact", "核准不等於已發布。"),
        ("MCP vs Demo HTTP API", "MCP 是外部 Agent 的受控工具入口；Demo API 是 Dashboard 問答入口。", "mcp_server / demo_web", "MCP 不是一般問答必經路徑。"),
    ]
    term_rows = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td><code>{esc(c)}</code></td><td>{esc(d)}</td></tr>" for a,b,c,d in terms)
    suite_rows = "".join(f"<tr><td><code>{esc(s['suite'])}</code></td><td>{s['total']}</td><td>{s['execution_backed']}</td><td>{s['synthetic']}</td><td>{chips(s['adapters'])}</td></tr>" for s in eval_data["suites"])
    categories = [(group, len(items)) for group, items in file_index.items()]
    category_cards = "".join(f"<div class='category-card'><strong>{esc(group)}</strong><span>{count} 個檔案</span></div>" for group, count in categories)
    must_read = [
        "README.md", "demo_web.py", "analysis_pipeline.py", "real_data.py", "task_profile.py", "canonical_task.py",
        "tool_registry.py", "analysis_tools.py", "agent_runtime/evidence_validator.py", "semantic_layer/catalog.py",
        "proactive_workflow/approval.py", "evaluation/policies/regression_gate.v1.json",
    ]
    lookup = {f["path"]: f for group in file_index.values() for f in group}
    must_read_items = "".join(
        f"<li><code>{esc(path)}</code><span>{esc(lookup.get(path, {}).get('purpose', file_purpose(path)))}</span></li>"
        for path in must_read
    )
    toc = [("terms", "名詞表"), ("quality", "品質與安全"), ("eval", "Evaluation"), ("limits", "已知限制"), ("files", "檔案索引")]
    body = f"""
<section id="terms"><h2>名詞表</h2><p>先用白話理解，再對照程式名稱。不要把英文名詞當成已經理解系統。</p><div class="table-wrap"><table><thead><tr><th>名詞</th><th>一句白話</th><th>程式名稱</th><th>容易混淆</th></tr></thead><tbody>{term_rows}</tbody></table></div></section>
<section id="quality"><h2>品質與安全</h2>
  <div class="principle-grid">
    <div class="principle-card"><h3>Writer Validator</h3><p>檢查數字、月份、實體、KPI、proxy、因果描述、forecast 限制與 debug 外洩。</p></div>
    <div class="principle-card"><h3>Evidence Validation</h3><p>確認 primary evidence 足夠；不足時才走重新規劃或 partial answer。</p></div>
    <div class="principle-card"><h3>MCP allowlist</h3><p>外部 Agent 只能使用明確公開的 read-only 工具。</p></div>
    <div class="principle-card"><h3>Approval gate</h3><p>主動洞察草稿必須核准，publication artifact 才能產生。</p></div>
  </div>
  <details><summary>工程細節</summary><ul><li>argument validation：ToolContract allowed arguments 與 MCP schema。</li><li>row cap：MCP 回傳限制筆數，避免大量資料外洩。</li><li>redaction：不要把未處理 trace 或敏感欄位放入回應。</li><li>expected security rejection：任意 Python / SQL / shell、hidden MCP tool、forecast unsupported。</li></ul></details>
</section>
<section id="eval"><h2>Evaluation 與 Gate</h2><p>以下來自目前 repository 的 evaluation 設定與 suite 掃描；若要最新成績，請重跑正式 evaluation，不要引用過期 artifact。</p><div class="table-wrap"><table><thead><tr><th>suite</th><th>cases</th><th>execution-backed</th><th>synthetic</th><th>adapters</th></tr></thead><tbody>{suite_rows}</tbody></table></div><details><summary>Gate policy</summary><p><code>evaluation/policies/regression_gate.v1.json</code>。threshold 必須以目前 policy 為準，不能為了單次 Demo 放寬。</p>{code_block('uv run python -m evaluation.run_evaluation --help', 'bash')}</details></section>
<section id="limits"><h2>已知限制</h2>
  <div class="split"><div><h3>刻意設計邊界</h3><ul><li>不提供任意 Python、SQL、shell。</li><li>不把描述性 proxy 寫成因果或正式 turnover。</li><li>預測問題目前安全拒絕。</li><li>MCP 不可操作 approval / publication。</li></ul></div><div><h3>尚未產品化</h3><ul><li>Dashboard 是 POC 工作台，不是完整權限與多租戶產品。</li><li>主動洞察需要人工 review，不自動發布。</li><li>資料 mapping warning 需要維護者在正式展示前檢查。</li></ul></div></div>
</section>
<section id="files"><h2>完整檔案索引</h2>
  <p class="notice">此區協助定位，不取代實際程式碼閱讀。</p>
  <div class="search-panel"><label for="fileSearch">搜尋檔案、symbol 或用途</label><input id="fileSearch" type="search" placeholder="至少輸入 2 個字，例如 registry、validator、approval" autocomplete="off"><p id="fileSearchHint">輸入至少 2 個字後，才會在本頁用本地 JSON 顯示結果。</p></div>
  <h3>類別目錄</h3><div class="category-grid">{category_cards}</div>
  <h3>交接必讀檔</h3><ul class="must-read-list">{must_read_items}</ul>
  <div id="fileResults" class="file-results" aria-live="polite"></div>
  <details><summary>工程細節：索引資料來源</summary><p>搜尋資料來自 <code>assets/data/file-index.json</code>，由 <code>scripts/generate_handoff_site.py</code> 於 build-time 產生，不會呼叫 Backend。</p></details>
</section>
"""
    return layout("appendix.html", "附錄", "名詞、安全、Evaluation、限制與可搜尋檔案索引。", body, toc)

def write_assets() -> None:
    (ASSETS / "css").mkdir(parents=True, exist_ok=True)
    (ASSETS / "js").mkdir(parents=True, exist_ok=True)
    (ASSETS / "diagrams").mkdir(parents=True, exist_ok=True)
    (ASSETS / "css" / "style.css").write_text(CSS, encoding="utf-8")
    (ASSETS / "js" / "app.js").write_text(JS, encoding="utf-8")
    for name, content in DIAGRAMS.items():
        (ASSETS / "diagrams" / name).write_text(content, encoding="utf-8")


CSS = r"""
:root,html[data-theme="light"]{--bg:#f7f9fc;--surface:#ffffff;--surface-2:#f2f6fb;--ink:#172033;--muted:#5f6b7a;--line:#d8e1ec;--brand:#1f5f8b;--brand-strong:#17476d;--brand-soft:#e7f1f8;--ok:#067647;--warn:#946200;--bad:#b42318;--chip:#eef4fb;--code-bg:#f8fafc;--code-ink:#182230;--shadow:0 10px 30px rgba(16,24,40,.08);--radius:8px;--topbar-height:68px}
html[data-theme="dark"]{--bg:#18212c;--surface:#222d3a;--surface-2:#1d2733;--ink:#eef4fb;--muted:#b5c0cd;--line:#405064;--brand:#8cc5f0;--brand-strong:#b7dcf7;--brand-soft:#25394b;--ok:#7dd3a8;--warn:#f5c56b;--bad:#fda29b;--chip:#2b3948;--code-bg:#141c26;--code-ink:#eef4fb;--shadow:0 10px 28px rgba(0,0,0,.25)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;overflow-x:hidden}body.toc-drawer-open{overflow:hidden}a{color:var(--brand-strong);text-decoration:none}a:hover{text-decoration:underline}button,input,select{font:inherit}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid color-mix(in srgb,var(--brand) 55%,transparent);outline-offset:2px}code,kbd{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.92em}img{max-width:100%;height:auto}.topbar{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:18px;padding:14px 24px;background:color-mix(in srgb,var(--surface) 94%,transparent);border-bottom:1px solid var(--line);backdrop-filter:blur(14px)}.brand{display:flex;flex-direction:column;gap:0;font-weight:750;color:var(--ink);letter-spacing:0}.brand small{font-size:12px;color:var(--muted);font-weight:650}.nav-toggle{display:none}.main-nav{display:flex;gap:6px;flex:1;overflow:auto}.main-nav a{padding:8px 10px;border-radius:7px;color:var(--muted);white-space:nowrap}.main-nav a.active,.main-nav a:hover{background:var(--brand-soft);color:var(--brand-strong);text-decoration:none}.theme-toggle{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:7px 12px;font-weight:650;cursor:pointer;white-space:nowrap}.theme-toggle:hover{border-color:var(--brand);color:var(--brand-strong)}.page-shell{max-width:1440px;margin:0 auto;padding:30px 24px}.page-hero{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:34px 36px;margin-bottom:22px;box-shadow:var(--shadow)}.page-hero h1{font-size:clamp(30px,4vw,50px);line-height:1.12;margin:0 0 14px;letter-spacing:0}.page-hero p{max-width:880px;color:var(--muted);font-size:18px;margin:0}.eyebrow{font-size:13px!important;font-weight:800;color:var(--brand-strong)!important;letter-spacing:.04em;margin-bottom:8px!important}.content-layout{display:grid;grid-template-columns:248px minmax(0,1fr);gap:24px;align-items:start;transition:grid-template-columns .18s ease}.content-layout.toc-collapsed{grid-template-columns:52px minmax(0,1fr)}.content{min-width:0}.page-toc{position:sticky;top:calc(var(--topbar-height) + 16px);max-height:calc(100vh - var(--topbar-height) - 28px);overflow:auto;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:12px;box-shadow:none;z-index:10}.page-toc-header{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:3px 2px 10px;border-bottom:1px solid var(--line);margin-bottom:8px}.page-toc-header strong{font-size:14px;color:var(--ink)}.toc-collapse-button,.toc-expand-button,.toc-mobile-button{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:7px;cursor:pointer;font-weight:700}.toc-collapse-button{padding:5px 8px;font-size:12px;white-space:nowrap}.toc-expand-button{display:none;position:sticky;top:calc(var(--topbar-height) + 16px);width:44px;height:44px;align-items:center;justify-content:center;z-index:9}.toc-mobile-button{display:none}.content-layout.toc-collapsed .page-toc{display:none}.content-layout.toc-collapsed .toc-expand-button{display:flex}.page-toc-links{display:grid;gap:3px}.page-toc-link{display:block;min-height:34px;padding:7px 10px 7px 12px;border-radius:7px;border-left:3px solid transparent;color:var(--muted);font-size:14px;line-height:1.35;overflow-wrap:anywhere}.page-toc-link:hover{background:var(--surface-2);color:var(--brand-strong);text-decoration:none}.page-toc-link.active{background:var(--brand-soft);border-left-color:var(--brand);color:var(--brand-strong);font-weight:750}.content>section,.content-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:28px;margin:0 0 22px;box-shadow:var(--shadow)}section[id]{scroll-margin-top:calc(var(--topbar-height) + 18px)}section h2{margin:0 0 12px;font-size:26px;letter-spacing:0}section h3{margin:18px 0 8px;font-size:18px}.lead{font-size:18px;color:var(--muted)}.quick-grid,.principle-grid,.module-grid,.stats-grid,.tool-grid,.faq-grid,.category-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}.quick-card,.principle-card,.stat,.module-card,.tool-card,.category-card{background:var(--surface-2);border:1px solid var(--line);border-radius:var(--radius);padding:16px}.quick-card h3,.principle-card h3,.module-card h3,.tool-card h3{margin-top:0}.status{display:inline-flex;align-items:center;padding:3px 9px;border-radius:999px;font-weight:700;font-size:12px;border:1px solid var(--line);background:var(--chip);color:var(--ink)}.status.ok{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 35%,var(--line));background:color-mix(in srgb,var(--ok) 12%,var(--surface))}.status.warn{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 35%,var(--line));background:color-mix(in srgb,var(--warn) 13%,var(--surface))}.status.bad{color:var(--bad);border-color:color-mix(in srgb,var(--bad) 35%,var(--line));background:color-mix(in srgb,var(--bad) 10%,var(--surface))}.chips{display:flex;flex-wrap:wrap;gap:6px}.chip{display:inline-flex;align-items:center;max-width:100%;padding:3px 8px;border-radius:999px;background:var(--chip);border:1px solid var(--line);font-size:12px;color:var(--ink);overflow-wrap:anywhere}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:var(--radius);background:var(--surface)}table{border-collapse:collapse;width:100%;min-width:760px}th,td{padding:11px 13px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:var(--surface-2);font-size:13px;color:var(--muted);font-weight:750}tr:last-child td{border-bottom:0}.callout,.notice{border-left:4px solid var(--brand);background:var(--brand-soft);padding:12px 14px;border-radius:0 var(--radius) var(--radius) 0;color:var(--ink)}details{border:1px solid var(--line);border-radius:var(--radius);background:var(--surface-2);padding:12px 14px;margin:12px 0}summary{cursor:pointer;font-weight:750;color:var(--ink)}pre{margin:0;overflow:auto;background:var(--code-bg);color:var(--code-ink);border:1px solid var(--line);border-radius:var(--radius);padding:16px;font-size:13px;line-height:1.55}.code-wrap{position:relative;margin:14px 0}.copy-btn{position:absolute;top:8px;right:8px;border:1px solid var(--line);background:var(--surface);color:var(--muted);border-radius:6px;padding:4px 8px;cursor:pointer}.copy-btn:hover{color:var(--brand-strong);border-color:var(--brand)}.code-note{margin:-4px 0 16px;color:var(--muted);font-size:13px}.diagram-card{background:var(--surface-2);border:1px solid var(--line);border-radius:var(--radius);padding:14px;overflow:auto}.diagram-caption{color:var(--muted);margin-top:-4px}.split{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.demo-steps{display:grid;gap:12px;padding-left:24px}.demo-steps li{background:var(--surface-2);border:1px solid var(--line);border-radius:var(--radius);padding:12px}.demo-steps strong{display:block;margin-bottom:4px}.filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:14px 0}.filters input,.filters select,.search-panel input{width:100%;border:1px solid var(--line);border-radius:7px;background:var(--surface);color:var(--ink);padding:10px}.tool-meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;font-size:14px}.tool-meta div{background:var(--surface);border:1px solid var(--line);border-radius:7px;padding:8px}.module-section{margin:10px 0}.module-section>span{display:block;color:var(--muted);font-size:13px;font-weight:750;margin-bottom:6px}.search-panel{background:var(--surface-2);border:1px solid var(--line);border-radius:var(--radius);padding:16px;margin:12px 0}.search-panel label{display:block;font-weight:750;margin-bottom:8px}.category-card{display:flex;justify-content:space-between;gap:10px}.category-card span{color:var(--muted)}.must-read-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:10px;padding-left:0;list-style:none}.must-read-list li,.file-result{background:var(--surface-2);border:1px solid var(--line);border-radius:var(--radius);padding:12px}.must-read-list code{display:block;margin-bottom:4px}.must-read-list span{color:var(--muted)}.file-results{display:grid;gap:10px;margin-top:16px}.file-result h3{margin:0 0 4px;font-size:16px}.footer{padding:28px 24px;color:var(--muted);text-align:center}.hidden{display:none!important}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}.content-layout,.page-toc{transition:none!important}}
@media (max-width:900px){.topbar{align-items:flex-start;flex-wrap:wrap;padding:12px 14px}.nav-toggle{display:inline-flex;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:7px;padding:7px 10px}.main-nav{display:none;flex-basis:100%;flex-direction:column;max-height:50vh}.main-nav.open{display:flex}.page-shell{padding:18px 14px}.page-hero,.content>section{padding:20px}.content-layout,.content-layout.toc-collapsed{display:block}.toc-expand-button{display:none!important}.toc-mobile-button{display:inline-flex;align-items:center;gap:8px;position:sticky;top:calc(var(--topbar-height) + 8px);z-index:18;margin:0 0 14px;padding:8px 11px;background:var(--surface);box-shadow:0 4px 14px rgba(16,24,40,.08)}.page-toc{position:fixed;top:var(--topbar-height);left:0;bottom:0;width:min(84vw,310px);max-height:none;border-radius:0 10px 0 0;border-left:0;border-bottom:0;padding:14px;transform:translateX(-105%);transition:transform .18s ease;z-index:35;box-shadow:12px 0 26px rgba(16,24,40,.18)}body.toc-drawer-open .page-toc{transform:translateX(0)}.content-layout.toc-collapsed .page-toc{display:block}.toc-backdrop{position:fixed;inset:var(--topbar-height) 0 0 0;background:rgba(15,23,42,.36);z-index:30}.toc-backdrop[hidden]{display:none}.toc-collapse-button{padding:6px 8px}.tool-meta{grid-template-columns:1fr}table{min-width:680px}.quick-grid,.principle-grid,.module-grid,.stats-grid,.tool-grid,.faq-grid,.category-grid{grid-template-columns:1fr}}
"""
JS = r"""
(function(){
  const root=document.documentElement;
  const themeBtn=document.querySelector('[data-theme-toggle]');
  function applyTheme(theme){
    root.setAttribute('data-theme',theme);
    if(themeBtn){themeBtn.textContent=theme==='dark'?'夜間':'日間';themeBtn.setAttribute('aria-pressed',theme==='dark'?'true':'false');}
  }
  applyTheme(localStorage.getItem('handoff-theme')||'light');
  if(themeBtn){themeBtn.addEventListener('click',()=>{const next=root.getAttribute('data-theme')==='dark'?'light':'dark';localStorage.setItem('handoff-theme',next);applyTheme(next);});}

  const topbar=document.querySelector('.topbar');
  function updateTopbarHeight(){ if(topbar){root.style.setProperty('--topbar-height',Math.ceil(topbar.getBoundingClientRect().height)+'px');} }
  updateTopbarHeight(); window.addEventListener('resize',updateTopbarHeight,{passive:true});
  if('ResizeObserver' in window && topbar){new ResizeObserver(updateTopbarHeight).observe(topbar);}

  const navToggle=document.querySelector('.nav-toggle');
  const nav=document.querySelector('.main-nav');
  if(navToggle&&nav){navToggle.addEventListener('click',()=>nav.classList.toggle('open'));}

  const tocLayout=document.querySelector('[data-toc-layout]');
  const pageToc=document.querySelector('[data-page-toc]');
  const collapseBtn=document.querySelector('[data-toc-collapse]');
  const expandBtn=document.querySelector('[data-toc-expand]');
  const mobileOpenBtn=document.querySelector('[data-toc-mobile-open]');
  const backdrop=document.querySelector('[data-toc-backdrop]');
  const tocLinks=[...document.querySelectorAll('.page-toc-link')];
  const mobileQuery=window.matchMedia('(max-width: 900px)');
  function isMobile(){return mobileQuery.matches;}
  function setDesktopCollapsed(collapsed){
    if(!tocLayout) return;
    localStorage.setItem('handoff-toc-collapsed',collapsed?'true':'false');
    syncTocState();
  }
  function syncTocState(){
    if(!tocLayout) return;
    const collapsed=localStorage.getItem('handoff-toc-collapsed')==='true';
    tocLayout.classList.toggle('toc-collapsed',collapsed && !isMobile());
    if(collapseBtn){collapseBtn.setAttribute('aria-expanded',collapsed && !isMobile()?'false':'true');collapseBtn.textContent=isMobile()?'關閉導覽':'收起導覽 ◀';collapseBtn.setAttribute('aria-label',isMobile()?'關閉本頁導覽':'收起本頁導覽');}
    if(expandBtn){expandBtn.setAttribute('aria-expanded',collapsed && !isMobile()?'false':'true');}
    if(mobileOpenBtn){mobileOpenBtn.setAttribute('aria-expanded',document.body.classList.contains('toc-drawer-open')?'true':'false');}
    updateTopbarHeight();
  }
  function openDrawer(){ if(!pageToc) return; document.body.classList.add('toc-drawer-open'); if(backdrop) backdrop.hidden=false; if(mobileOpenBtn) mobileOpenBtn.setAttribute('aria-expanded','true'); if(collapseBtn) collapseBtn.setAttribute('aria-expanded','true'); }
  function closeDrawer(){ document.body.classList.remove('toc-drawer-open'); if(backdrop) backdrop.hidden=true; if(mobileOpenBtn) mobileOpenBtn.setAttribute('aria-expanded','false'); }
  if(collapseBtn){collapseBtn.addEventListener('click',()=>{isMobile()?closeDrawer():setDesktopCollapsed(true);});}
  if(expandBtn){expandBtn.addEventListener('click',()=>setDesktopCollapsed(false));}
  if(mobileOpenBtn){mobileOpenBtn.addEventListener('click',()=>openDrawer());}
  if(backdrop){backdrop.addEventListener('click',()=>closeDrawer());}
  document.addEventListener('keydown',event=>{if(event.key==='Escape' && document.body.classList.contains('toc-drawer-open')) closeDrawer();});
  mobileQuery.addEventListener?.('change',()=>{closeDrawer();syncTocState();});
  syncTocState();

  function setActiveToc(id){
    tocLinks.forEach(link=>link.classList.toggle('active',link.getAttribute('href')==='#'+id));
  }
  const tocSections=tocLinks.map(link=>document.getElementById((link.getAttribute('href')||'').slice(1))).filter(Boolean);
  if(tocLinks.length && tocSections.length){
    setActiveToc(tocSections[0].id);
    tocLinks.forEach(link=>link.addEventListener('click',()=>{setActiveToc((link.getAttribute('href')||'').slice(1)); if(isMobile()) closeDrawer();}));
    if('IntersectionObserver' in window){
      const visible=new Map();
      const observer=new IntersectionObserver(entries=>{
        entries.forEach(entry=>{entry.isIntersecting?visible.set(entry.target.id,entry.boundingClientRect.top):visible.delete(entry.target.id);});
        if(visible.size){
          const active=[...visible.entries()].sort((a,b)=>Math.abs(a[1])-Math.abs(b[1]))[0][0];
          setActiveToc(active);
        }
      },{root:null,rootMargin:'-22% 0px -62% 0px',threshold:[0,0.12,0.35]});
      tocSections.forEach(section=>observer.observe(section));
    }
  }

  document.querySelectorAll('.copy-btn').forEach(btn=>{
    btn.addEventListener('click',async()=>{
      const code=btn.parentElement.querySelector('code')?.innerText||'';
      try{await navigator.clipboard.writeText(code);btn.textContent='已複製';setTimeout(()=>btn.textContent='複製',1200);}catch(e){btn.textContent='無法複製';}
    });
  });

  const origin=window.location.origin;
  const urlMap={handoff:origin+'/handoff/',handoffTools:origin+'/handoff/tools.html',dashboard:origin+'/dashboard',health:origin+'/api/health'};
  document.querySelectorAll('[data-url-template]').forEach(el=>{const key=el.getAttribute('data-url-template');if(urlMap[key]) el.textContent=urlMap[key];});

  const toolSearch=document.getElementById('toolSearch');
  const familyFilter=document.getElementById('familyFilter');
  const metricFilter=document.getElementById('metricFilter');
  const evidenceFilter=document.getElementById('evidenceFilter');
  const exposureFilter=document.getElementById('exposureFilter');
  const toolCards=[...document.querySelectorAll('[data-tool-card]')];
  function matchesList(value, selected){return !selected || (value||'').split('|').includes(selected)}
  function applyToolFilters(){
    const q=(toolSearch?.value||'').trim().toLowerCase();
    const fam=familyFilter?.value||''; const metric=metricFilter?.value||''; const evidence=evidenceFilter?.value||''; const exposure=exposureFilter?.value||'';
    toolCards.forEach(card=>{
      const text=card.innerText.toLowerCase();
      const show=(!q||text.includes(q)) && matchesList(card.dataset.families,fam) && matchesList(card.dataset.metrics,metric) && (!evidence||card.dataset.evidence===evidence) && (!exposure||card.dataset.exposure===exposure);
      card.classList.toggle('hidden',!show);
    });
  }
  [toolSearch,familyFilter,metricFilter,evidenceFilter,exposureFilter].forEach(el=>el&&el.addEventListener('input',applyToolFilters));

  const fileSearch=document.getElementById('fileSearch');
  const fileResults=document.getElementById('fileResults');
  const fileHint=document.getElementById('fileSearchHint');
  let fileRows=null;
  function flattenFileIndex(index){const rows=[];Object.entries(index||{}).forEach(([group,items])=>(items||[]).forEach(item=>rows.push({...item,group})));return rows;}
  function cleanList(items){return (items||[]).filter(Boolean).filter(v=>!String(v).startsWith('目前程式中未確認'));}
  function renderFileResults(q){
    if(!fileResults) return;
    if(!q || q.length<2){fileResults.innerHTML=''; if(fileHint) fileHint.textContent='輸入至少 2 個字後，才會在本頁用本地 JSON 顯示結果。'; return;}
    if(!fileRows){ if(fileHint) fileHint.textContent='正在載入本地索引...'; return; }
    const needle=q.toLowerCase();
    const matched=fileRows.filter(row=>[row.path,row.group,row.purpose,...(row.symbols||[]),...(row.tests||[]),...(row.sync||[])].join(' ').toLowerCase().includes(needle)).slice(0,40);
    if(fileHint) fileHint.textContent=matched.length?`顯示 ${matched.length} 筆結果；請輸入更精準關鍵字縮小範圍。`:'沒有符合結果。';
    fileResults.innerHTML=matched.map(row=>{const symbols=cleanList(row.symbols); const tests=cleanList(row.tests); const sync=cleanList(row.sync);return `<article class="file-result"><h3><code>${escapeHtml(row.path||'')}</code></h3><p>${escapeHtml(row.purpose||'')}</p><p><span class="status">${escapeHtml(row.group||'')}</span></p>${symbols.length?`<p><strong>主要 symbols：</strong>${symbols.map(v=>`<code>${escapeHtml(v)}</code>`).join(' ')}</p>`:''}${tests.length?`<p><strong>相關測試：</strong>${tests.map(v=>`<code>${escapeHtml(v)}</code>`).join(' ')}</p>`:''}${sync.length?`<p><strong>修改時同步：</strong>${sync.map(v=>`<code>${escapeHtml(v)}</code>`).join(' ')}</p>`:''}</article>`;}).join('');
  }
  function escapeHtml(value){return String(value).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));}
  if(fileSearch&&fileResults){
    fetch('assets/data/file-index.json').then(r=>r.json()).then(data=>{fileRows=flattenFileIndex(data); renderFileResults(fileSearch.value.trim());}).catch(()=>{if(fileHint) fileHint.textContent='本地索引載入失敗，請確認 assets/data/file-index.json 存在。';});
    fileSearch.addEventListener('input',()=>renderFileResults(fileSearch.value.trim()));
  }
})();
"""
DIAGRAMS = {
    "data-flow.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 260" role="img"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#1f5f8b"/></marker></defs><style>text{font:16px system-ui,sans-serif;fill:#172033}.s{fill:#f5f7fb;stroke:#1f5f8b;stroke-width:1.5}.l{stroke:#1f5f8b;stroke-width:2;marker-end:url(#a)}</style><rect class="s" x="40" y="45" width="160" height="56" rx="8"/><text x="120" y="78" text-anchor="middle">inventory.xlsx</text><rect class="s" x="40" y="150" width="160" height="56" rx="8"/><text x="120" y="183" text-anchor="middle">revenue.xlsx</text><line class="l" x1="205" y1="73" x2="310" y2="128"/><line class="l" x1="205" y1="178" x2="310" y2="145"/><rect class="s" x="320" y="100" width="180" height="70" rx="8"/><text x="410" y="129" text-anchor="middle">資料讀取與正規化</text><text x="410" y="151" text-anchor="middle">build_pipeline_context</text><line class="l" x1="500" y1="135" x2="590" y2="135"/><rect class="s" x="600" y="100" width="150" height="70" rx="8"/><text x="675" y="129" text-anchor="middle">分析資料表</text><text x="675" y="151" text-anchor="middle">PipelineContext</text><line class="l" x1="750" y1="135" x2="820" y2="135"/><rect class="s" x="830" y="100" width="120" height="70" rx="8"/><text x="890" y="128" text-anchor="middle">Analysis</text><text x="890" y="150" text-anchor="middle">Tools</text></svg>""",
    "system-overview.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1040 360" role="img"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#1f5f8b"/></marker></defs><style>text{font:15px system-ui,sans-serif;fill:#172033}.b{fill:#fff;stroke:#1f5f8b;stroke-width:1.5}.g{fill:#f5f7fb}.l{stroke:#1f5f8b;stroke-width:2;marker-end:url(#a)}</style><rect class="b" x="35" y="145" width="110" height="55" rx="8"/><text x="90" y="178" text-anchor="middle">使用者</text><line class="l" x1="145" y1="172" x2="230" y2="172"/><rect class="b g" x="240" y="135" width="130" height="75" rx="8"/><text x="305" y="165" text-anchor="middle">Frontend</text><text x="305" y="188" text-anchor="middle">Dashboard</text><line class="l" x1="370" y1="172" x2="450" y2="172"/><rect class="b" x="460" y="135" width="130" height="75" rx="8"/><text x="525" y="165" text-anchor="middle">Backend API</text><text x="525" y="188" text-anchor="middle">demo_web.py</text><line class="l" x1="590" y1="172" x2="670" y2="172"/><rect class="b g" x="680" y="135" width="150" height="75" rx="8"/><text x="755" y="162" text-anchor="middle">Agent</text><text x="755" y="186" text-anchor="middle">規劃與驗證</text><line class="l" x1="830" y1="172" x2="900" y2="172"/><rect class="b" x="910" y="135" width="100" height="75" rx="8"/><text x="960" y="165" text-anchor="middle">Tool</text><text x="960" y="188" text-anchor="middle">計算</text><rect class="b" x="680" y="260" width="150" height="55" rx="8"/><text x="755" y="293" text-anchor="middle">Evidence / Replan</text><line class="l" x1="755" y1="210" x2="755" y2="260"/><rect class="b" x="900" y="260" width="110" height="55" rx="8"/><text x="955" y="293" text-anchor="middle">資料表</text><line class="l" x1="960" y1="210" x2="955" y2="260"/><rect class="b" x="460" y="35" width="150" height="55" rx="8"/><text x="535" y="68" text-anchor="middle">Proactive Workflow</text><line class="l" x1="535" y1="90" x2="535" y2="135"/><rect class="b" x="700" y="35" width="130" height="55" rx="8"/><text x="765" y="68" text-anchor="middle">MCP 入口</text><line class="l" x1="765" y1="90" x2="765" y2="135"/></svg>""",
    "system-architecture.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 760" role="img" aria-labelledby="title desc">
<title id="title">Revenue Intelligence POC 主架構圖</title><desc id="desc">以一般問答主流程為中央，MCP、Proactive、Observability、Evaluation 作為側邊支援模組。</desc>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#1f5f8b"/></marker><marker id="arrowSoft" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#7b8da3"/></marker></defs>
<style>
.bg{fill:#f7f9fc}.lane{fill:#ffffff;stroke:#d8e1ec;stroke-width:1.4}.side{fill:#eef4fb;stroke:#c9d7e6;stroke-width:1.4}.box{fill:#ffffff;stroke:#1f5f8b;stroke-width:1.7}.box2{fill:#f2f7fb;stroke:#1f5f8b;stroke-width:1.5}.data{fill:#fff8e6;stroke:#946200;stroke-width:1.5}.support{fill:#f6f8fb;stroke:#7b8da3;stroke-width:1.4}.main{stroke:#1f5f8b;stroke-width:2.4;fill:none;marker-end:url(#arrow)}.soft{stroke:#7b8da3;stroke-width:1.8;fill:none;stroke-dasharray:7 7;marker-end:url(#arrowSoft)}.loop{stroke:#946200;stroke-width:1.9;fill:none;marker-end:url(#arrowSoft)}text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;fill:#172033}.t{font-size:18px;font-weight:760}.s{font-size:13px;fill:#5f6b7a}.lane-title{font-size:15px;font-weight:760;fill:#1f5f8b}.small{font-size:12px;fill:#5f6b7a}
@media (prefers-color-scheme:dark){.bg{fill:#18212c}.lane{fill:#222d3a;stroke:#405064}.side{fill:#1d2733;stroke:#405064}.box{fill:#263447;stroke:#8cc5f0}.box2{fill:#223042;stroke:#8cc5f0}.data{fill:#332b18;stroke:#f5c56b}.support{fill:#243041;stroke:#7b8da3}.main{stroke:#8cc5f0}.soft{stroke:#9fb0c4}.loop{stroke:#f5c56b}text{fill:#eef4fb}.s,.small{fill:#b5c0cd}.lane-title{fill:#8cc5f0}}</style>
<rect class="bg" width="1280" height="760" rx="0"/>
<text x="40" y="42" class="t">Revenue Intelligence POC：交接主路徑</text><text x="40" y="66" class="s">中央是一般問答最常走的路；側邊模組是受控入口、主動流程、觀測與離線驗收。</text>
<rect class="lane" x="40" y="92" width="1200" height="112" rx="12"/><text x="60" y="120" class="lane-title">第一層：使用入口</text>
<rect class="box" x="90" y="138" width="170" height="46" rx="8"/><text x="175" y="158" text-anchor="middle" class="t">使用者</text><text x="175" y="176" text-anchor="middle" class="s">中文提問</text>
<rect class="box" x="360" y="132" width="210" height="58" rx="8"/><text x="465" y="154" text-anchor="middle" class="t">Frontend Dashboard</text><text x="465" y="174" text-anchor="middle" class="s">/dashboard</text>
<rect class="box" x="680" y="132" width="210" height="58" rx="8"/><text x="785" y="154" text-anchor="middle" class="t">Backend API</text><text x="785" y="174" text-anchor="middle" class="s">demo_web.py</text>
<path class="main" d="M260 161 H360"/><path class="main" d="M570 161 H680"/>
<rect class="lane" x="40" y="232" width="1200" height="126" rx="12"/><text x="60" y="260" class="lane-title">第二層：問答理解與規劃</text>
<rect class="box" x="150" y="282" width="230" height="58" rx="8"/><text x="265" y="304" text-anchor="middle" class="t">MultiAgentAssistant</text><text x="265" y="324" text-anchor="middle" class="s">問題理解 / TaskProfile</text>
<rect class="box" x="500" y="282" width="230" height="58" rx="8"/><text x="615" y="304" text-anchor="middle" class="t">Semantic Layer</text><text x="615" y="324" text-anchor="middle" class="s">KPI / Evidence 規則</text>
<rect class="box" x="850" y="282" width="230" height="58" rx="8"/><text x="965" y="304" text-anchor="middle" class="t">AnswerPlan</text><text x="965" y="324" text-anchor="middle" class="s">PlanValidator</text>
<path class="main" d="M785 190 V218 H265 V282"/><path class="main" d="M380 311 H500"/><path class="main" d="M730 311 H850"/>
<rect class="lane" x="40" y="386" width="1200" height="150" rx="12"/><text x="60" y="414" class="lane-title">第三層：執行與驗證主循環</text>
<rect class="box" x="90" y="442" width="210" height="62" rx="8"/><text x="195" y="464" text-anchor="middle" class="t">Stateful Runtime</text><text x="195" y="484" text-anchor="middle" class="s">PlanStep / Checkpoint</text>
<rect class="box" x="390" y="442" width="230" height="62" rx="8"/><text x="505" y="464" text-anchor="middle" class="t">Analysis Toolbox</text><text x="505" y="484" text-anchor="middle" class="s">Tool Registry</text>
<rect class="box" x="710" y="442" width="210" height="62" rx="8"/><text x="815" y="464" text-anchor="middle" class="t">Evidence Validator</text><text x="815" y="484" text-anchor="middle" class="s">Primary evidence</text>
<rect class="box" x="1010" y="442" width="190" height="62" rx="8"/><text x="1105" y="464" text-anchor="middle" class="t">Answer Contract</text><text x="1105" y="484" text-anchor="middle" class="s">Writer Validator</text>
<path class="main" d="M965 340 V372 H195 V442"/><path class="main" d="M300 473 H390"/><path class="main" d="M620 473 H710"/><path class="main" d="M920 473 H1010"/>
<rect class="support" x="710" y="548" width="210" height="56" rx="8"/><text x="815" y="570" text-anchor="middle" class="t">Replanner</text><text x="815" y="590" text-anchor="middle" class="s">或 Capability Gap</text>
<path class="loop" d="M815 504 V548"/><path class="loop" d="M710 576 H650 V512 H300"/>
<rect class="lane" x="40" y="620" width="1200" height="92" rx="12"/><text x="60" y="648" class="lane-title">第四層：資料來源</text>
<rect class="data" x="390" y="654" width="230" height="42" rx="8"/><text x="505" y="681" text-anchor="middle" class="t">Revenue / Inventory Data</text>
<path class="main" d="M505 654 V504"/>
<rect class="side" x="40" y="548" width="250" height="56" rx="10"/><text x="165" y="570" text-anchor="middle" class="t">MCP Server</text><text x="165" y="590" text-anchor="middle" class="s">外部 Agent 的受控入口</text><path class="soft" d="M290 576 H390"/>
<rect class="side" x="970" y="548" width="270" height="56" rx="10"/><text x="1105" y="570" text-anchor="middle" class="t">Proactive Workflow</text><text x="1105" y="590" text-anchor="middle" class="s">Draft / Approval / Publication</text><path class="soft" d="M1105 548 V516"/>
<rect class="side" x="930" y="638" width="150" height="48" rx="10"/><text x="1005" y="657" text-anchor="middle" class="t">Observability</text><text x="1005" y="676" text-anchor="middle" class="s">Trace / State</text><path class="soft" d="M1005 638 V516"/>
<rect class="side" x="1090" y="638" width="150" height="48" rx="10"/><text x="1165" y="657" text-anchor="middle" class="t">Evaluation</text><text x="1165" y="676" text-anchor="middle" class="s">Regression Gate</text><path class="soft" d="M1165 638 V604"/>
<text x="60" y="732" class="small">實線：一般問答主線。虛線：旁支支援或離線驗收。證據不足時先重新規劃；沒有合法工具才回 partial / capability gap。</text>
</svg>""",
    "question-flow.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 150" role="img"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#1f5f8b"/></marker></defs><style>text{font:15px system-ui,sans-serif;fill:#172033}.b{fill:#fff;stroke:#1f5f8b;stroke-width:1.5}.l{stroke:#1f5f8b;stroke-width:2;marker-end:url(#a)}</style><g><rect class="b" x="25" y="50" width="105" height="50" rx="8"/><text x="77" y="80" text-anchor="middle">問題</text></g><line class="l" x1="130" y1="75" x2="170" y2="75"/><rect class="b" x="180" y="50" width="105" height="50" rx="8"/><text x="232" y="80" text-anchor="middle">理解</text><line class="l" x1="285" y1="75" x2="325" y2="75"/><rect class="b" x="335" y="50" width="105" height="50" rx="8"/><text x="387" y="80" text-anchor="middle">規劃</text><line class="l" x1="440" y1="75" x2="480" y2="75"/><rect class="b" x="490" y="50" width="105" height="50" rx="8"/><text x="542" y="80" text-anchor="middle">選工具</text><line class="l" x1="595" y1="75" x2="635" y2="75"/><rect class="b" x="645" y="50" width="105" height="50" rx="8"/><text x="697" y="80" text-anchor="middle">執行</text><line class="l" x1="750" y1="75" x2="790" y2="75"/><rect class="b" x="800" y="50" width="130" height="50" rx="8"/><text x="865" y="80" text-anchor="middle">檢查證據→回答</text></svg>""",
    "tool-boundary.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1040 210" role="img"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#1f5f8b"/></marker></defs><style>text{font:15px system-ui,sans-serif;fill:#172033}.b{fill:#fff;stroke:#1f5f8b;stroke-width:1.5}.safe{fill:#f0fdfa}.l{stroke:#1f5f8b;stroke-width:2;marker-end:url(#a)}</style><rect class="b" x="30" y="80" width="125" height="55" rx="8"/><text x="92" y="113" text-anchor="middle">Agent Plan</text><line class="l" x1="155" y1="108" x2="210" y2="108"/><rect class="b safe" x="220" y="80" width="135" height="55" rx="8"/><text x="287" y="113" text-anchor="middle">Tool Registry</text><line class="l" x1="355" y1="108" x2="410" y2="108"/><rect class="b safe" x="420" y="80" width="165" height="55" rx="8"/><text x="502" y="113" text-anchor="middle">Arguments Validation</text><line class="l" x1="585" y1="108" x2="640" y2="108"/><rect class="b" x="650" y="80" width="135" height="55" rx="8"/><text x="717" y="113" text-anchor="middle">Tool Execution</text><line class="l" x1="785" y1="108" x2="840" y2="108"/><rect class="b safe" x="850" y="80" width="135" height="55" rx="8"/><text x="917" y="101" text-anchor="middle">Evidence Type</text><text x="917" y="122" text-anchor="middle">Validation</text></svg>""",
    "proactive-flow.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 170" role="img"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#1f5f8b"/></marker></defs><style>text{font:14px system-ui,sans-serif;fill:#172033}.b{fill:#fff;stroke:#1f5f8b;stroke-width:1.5}.g{fill:#f5f7fb}.l{stroke:#1f5f8b;stroke-width:2;marker-end:url(#a)}</style><rect class="b" x="20" y="60" width="105" height="50" rx="8"/><text x="72" y="90" text-anchor="middle">資料刷新</text><line class="l" x1="125" y1="85" x2="170" y2="85"/><rect class="b g" x="180" y="60" width="105" height="50" rx="8"/><text x="232" y="90" text-anchor="middle">Fingerprint</text><line class="l" x1="285" y1="85" x2="330" y2="85"/><rect class="b" x="340" y="60" width="110" height="50" rx="8"/><text x="395" y="90" text-anchor="middle">Data Quality</text><line class="l" x1="450" y1="85" x2="495" y2="85"/><rect class="b g" x="505" y="60" width="100" height="50" rx="8"/><text x="555" y="90" text-anchor="middle">Candidate</text><line class="l" x1="605" y1="85" x2="650" y2="85"/><rect class="b" x="660" y="60" width="115" height="50" rx="8"/><text x="717" y="90" text-anchor="middle">Investigation</text><line class="l" x1="775" y1="85" x2="820" y2="85"/><rect class="b g" x="830" y="60" width="85" height="50" rx="8"/><text x="872" y="90" text-anchor="middle">Draft</text><line class="l" x1="915" y1="85" x2="960" y2="85"/><rect class="b" x="970" y="50" width="180" height="70" rx="8"/><text x="1060" y="79" text-anchor="middle">Approval / Reject</text><text x="1060" y="101" text-anchor="middle">Revision / Publication</text></svg>""",
}


def write_readme(catalog: dict[str, Any]) -> None:
    (SITE / "README.md").write_text(
        f"""# Revenue Intelligence POC Handoff Site

This static site is served by the existing Next.js frontend from `frontend/public/handoff/`.

- Formal entry: `/handoff/`
- Direct entry: `/handoff/index.html`
- Generated source: `scripts/generate_handoff_site.py`
- Validator: `scripts/validate_handoff_site.py`
- Tool catalog count: {catalog['stats']['total']}
- MCP catalog count: {catalog['stats']['mcp_exposable']}

Regenerate after tool registry, semantic definitions, evaluation datasets, or core startup docs change:

```bash
uv run python scripts/generate_handoff_site.py
uv run python scripts/validate_handoff_site.py
```
""",
        encoding="utf-8",
    )


def main() -> int:
    SITE.mkdir(parents=True, exist_ok=True)
    catalog = build_tool_catalog()
    data = {
        "catalog": catalog,
        "semantic": collect_semantic(),
        "eval": collect_eval(),
        "routes": collect_routes(),
        "file_index": collect_file_index(),
    }
    write_assets()
    pages = {
        "index.html": build_index(data),
        "overview.html": build_overview(data),
        "question-journey.html": build_question_journey(data),
        "tools.html": build_tools(data),
        "architecture.html": build_architecture(data),
        "operations.html": build_operations(data),
        "maintenance.html": build_maintenance(data),
        "appendix.html": build_appendix(data),
    }
    for filename, content in pages.items():
        (SITE / filename).write_text(content, encoding="utf-8")
    (ASSETS / "data").mkdir(parents=True, exist_ok=True)
    (ASSETS / "data" / "tool-catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (ASSETS / "data" / "file-index.json").write_text(json.dumps(data["file_index"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    write_readme(catalog)
    print(json.dumps({"site": SITE.relative_to(ROOT).as_posix(), "pages": list(pages), "tool_count": catalog["stats"]["total"], "mcp_tools": catalog["stats"]["mcp_exposable"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
