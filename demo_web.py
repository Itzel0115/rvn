"""Dashboard、mobile UI 與 Agent flow 共用的 Python Backend/API 入口.

本模組在啟動時建立共用的 PipelineContext，並將 HTTP request 路由到
deterministic tools 或 MultiAgentAssistant。輕量 metadata endpoint 不需要
LLM；`/api/ask` 才會進入 Agent orchestration。Frontend 不直接讀取 Excel。
"""

from __future__ import annotations

import json
import math
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from analysis_pipeline import PipelineContext, build_pipeline_context
from analysis_tools import AnalysisToolbox, ObservationRequest, QueryFilters
from config import OUTPUT_DIR
from logging_utils import build_request_id, configure_logging, get_logger
from multi_agent import MultiAgentAssistant
from proactive_workflow.orchestrator import ProactiveWorkflowOrchestrator
from proactive_workflow.store import SQLiteProactiveStore
from proactive_workflow.models import to_dict
from proactive_workflow.approval import decide
from proactive_workflow.publisher import publish
from proactive_workflow.revision import create_revision
from utils import MessageCollector


HOST = os.getenv("DEMO_WEB_HOST", "0.0.0.0")
PORT = int(os.getenv("DEMO_WEB_PORT", "8765"))
DEFAULT_CORS_ALLOWED_ORIGINS = "http://10.8.35.35:3000,http://localhost:3000,http://127.0.0.1:3000"
CORS_ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.getenv("DEMO_CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ALLOWED_ORIGINS).split(",")
    if origin.strip()
}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() == "true"


def _coerce_optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return None


def _json_safe(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


def derive_health_status(messages: MessageCollector) -> str:
    if messages.errors:
        return "error"
    if messages.warnings:
        return "warning"
    return "ok"


def build_data_version_payload(context: PipelineContext, toolbox: AnalysisToolbox) -> dict:
    coverage = toolbox.get_data_coverage()
    months = coverage.get("months", [])
    latest_month = months[-1] if months else None

    if months:
        data_version = (
            f"months_{months[0]}_to_{months[-1]}"
            f"_rev{coverage.get('revenue_rows', 0)}"
            f"_inv{coverage.get('inventory_rows', 0)}"
            f"_map{coverage.get('mapping_rows', 0)}"
        )
    else:
        data_version = "no_data"

    return {
        "data_version": data_version,
        "available_months": months,
        "latest_month": latest_month,
        "revenue_rows": coverage.get("revenue_rows", 0),
        "inventory_rows": coverage.get("inventory_rows", 0),
        "mapping_rows": coverage.get("mapping_rows", 0),
        "mapping_success": coverage.get("mapping_success", False),
        "supported_domains": coverage.get("supported_domains", context.supported_domains),
        "source_files": coverage.get("source_files", context.source_files),
    }


def build_pipeline_status_payload(context: PipelineContext, toolbox: AnalysisToolbox) -> dict:
    coverage = toolbox.get_data_coverage()
    months = coverage.get("months", [])
    messages = context.messages
    return {
        "status": derive_health_status(messages),
        "infos": list(messages.infos),
        "warnings": list(messages.warnings),
        "errors": list(messages.errors),
        "info_count": len(messages.infos),
        "warning_count": len(messages.warnings),
        "error_count": len(messages.errors),
        "latest_month": months[-1] if months else None,
        "available_months": months,
    }


def build_data_quality_payload(context: PipelineContext, toolbox: AnalysisToolbox) -> dict:
    version_payload = build_data_version_payload(context, toolbox)
    pipeline_payload = build_pipeline_status_payload(context, toolbox)
    mapping_summary = toolbox.get_mapping_summary()

    quality_checks = [
        {
            "name": "required_columns",
            "status": "ok" if not context.messages.errors else "error",
            "message": "必要欄位檢查通過" if not context.messages.errors else "必要欄位檢查未通過",
        },
        {
            "name": "mapping_success",
            "status": "ok" if version_payload["mapping_success"] else "error",
            "message": "資料來源對齊摘要可用" if version_payload["mapping_success"] else "資料來源對齊摘要不可用",
        },
    ]
    if pipeline_payload["warning_count"] > 0:
        quality_checks.append(
            {
                "name": "mapping_ambiguity",
                "status": "warning",
                "message": "有 6 個 HQBU 代碼對應到多個平台代碼，需要解讀限制",
            }
        )

    limitations = [
        "目前資料品質報告僅反映已載入資料與 pipeline 狀態。",
    ]
    if mapping_summary.get("bridge_candidate_count", 0) > 0:
        limitations.append("若資料來源對齊存在 ambiguous candidates，平台層分析需搭配限制解讀。")

    return {
        "status": pipeline_payload["status"],
        "data_version": version_payload["data_version"],
        "available_months": version_payload["available_months"],
        "latest_month": version_payload["latest_month"],
        "row_counts": {
            "revenue": version_payload["revenue_rows"],
            "inventory": version_payload["inventory_rows"],
            "mapping": version_payload["mapping_rows"],
        },
        "mapping": {
            "mapping_success": version_payload["mapping_success"],
            "business_group_count": len(mapping_summary.get("business_groups", [])),
            "inventory_hqbu_mapping_count": mapping_summary.get("inventory_hqbu_mapping_count", 0),
            "revenue_platform_mapping_count": mapping_summary.get("revenue_platform_mapping_count", 0),
            "bridge_candidate_count": mapping_summary.get("bridge_candidate_count", 0),
        },
        "pipeline_messages": {
            "infos": pipeline_payload["infos"],
            "warnings": pipeline_payload["warnings"],
            "errors": pipeline_payload["errors"],
        },
        "quality_checks": quality_checks,
        "limitations": limitations,
    }


class DemoApplication:
    def __init__(self) -> None:
        """建立 API 共用的 context、toolbox 與 Agent application state。"""
        server_request_id = configure_logging(OUTPUT_DIR / "logs", request_id="web-server")
        self.logger = get_logger("demo_web", server_request_id, domain="web")
        self.logger.info("Initializing demo web application")
        self.context = build_pipeline_context(server_request_id)
        self.default_use_llm_planner = _env_flag("USE_LLM_PLANNER", default=False)
        self.default_use_llm_rewriter = _env_flag("USE_LLM_REWRITER", default=False)
        self.logger.info(
            "Demo LLM settings planner=%s rewriter=%s",
            self.default_use_llm_planner,
            self.default_use_llm_rewriter,
        )
        self.summary = self._build_assistant(server_request_id).summarize_project()
        self.logger.info("Demo web application ready")

    def _build_assistant(
        self,
        request_id: str,
        *,
        use_llm_planner: bool | None = None,
        use_llm_rewriter: bool | None = None,
    ) -> MultiAgentAssistant:
        return MultiAgentAssistant(
            self.context,
            request_id,
            use_llm_planner=self.default_use_llm_planner if use_llm_planner is None else use_llm_planner,
            use_llm_rewriter=self.default_use_llm_rewriter if use_llm_rewriter is None else use_llm_rewriter,
        )

    def ask(
        self,
        question: str,
        history: list[dict] | None = None,
        chart_context: dict | None = None,
        *,
        use_llm_planner: bool | None = None,
        use_llm_rewriter: bool | None = None,
    ) -> dict:
        """將問題交給 MultiAgentAssistant，並回傳既有 API schema 的回答結果。"""
        request_id = build_request_id()
        assistant = self._build_assistant(
            request_id,
            use_llm_planner=use_llm_planner,
            use_llm_rewriter=use_llm_rewriter,
        )
        contextual_question = self._apply_conversation_context(question, history or [], chart_context or {})
        return assistant.answer(contextual_question)

    def get_chart_catalog(self) -> list[dict]:
        request_id = build_request_id()
        toolbox = AnalysisToolbox(self.context, request_id)
        return toolbox.get_chart_catalog()

    def get_observation_options(self) -> dict:
        request_id = build_request_id()
        toolbox = AnalysisToolbox(self.context, request_id)
        return toolbox.get_observation_options()

    def get_observation_table(self, payload: dict | None = None) -> dict:
        request_id = build_request_id()
        toolbox = AnalysisToolbox(self.context, request_id)
        request = ObservationRequest(**(payload or {}))
        return toolbox.get_observation_table(request)

    def get_chart(
        self,
        chart_key: str,
        filters: dict | None = None,
        render_image: bool = True,
        chart_type: str | None = None,
    ) -> dict:
        request_id = build_request_id()
        toolbox = AnalysisToolbox(self.context, request_id)
        query_filters = QueryFilters(**(filters or {}))
        payload = toolbox.get_chart_payload(chart_key, query_filters, chart_type_override=chart_type, include_table=True)
        image = (
            toolbox.create_chart_image(chart_key, query_filters, chart_type_override=chart_type)
            if render_image
            else None
        )
        return {
            "chart": payload,
            "image": image,
        }

    def get_summary(self) -> dict:
        return self.summary

    def get_health(self) -> dict:
        request_id = build_request_id()
        toolbox = AnalysisToolbox(self.context, request_id)
        version_payload = build_data_version_payload(self.context, toolbox)
        pipeline_payload = build_pipeline_status_payload(self.context, toolbox)
        pipeline_loaded = bool(
            self.context is not None
            and self.context.artifacts is not None
            and (
                version_payload["available_months"]
                or version_payload["revenue_rows"]
                or version_payload["inventory_rows"]
                or version_payload["mapping_rows"]
            )
        )
        return {
            "status": pipeline_payload["status"],
            "api": "ok",
            "pipeline_loaded": pipeline_loaded,
            "supported_domains": version_payload["supported_domains"],
            "latest_month": version_payload["latest_month"],
            "warning_count": pipeline_payload["warning_count"],
            "error_count": pipeline_payload["error_count"],
            "llm_planner_enabled": self.default_use_llm_planner,
            "llm_rewriter_enabled": self.default_use_llm_rewriter,
        }

    def get_data_version(self) -> dict:
        request_id = build_request_id()
        toolbox = AnalysisToolbox(self.context, request_id)
        return build_data_version_payload(self.context, toolbox)

    def get_pipeline_status(self) -> dict:
        request_id = build_request_id()
        toolbox = AnalysisToolbox(self.context, request_id)
        return build_pipeline_status_payload(self.context, toolbox)

    def get_data_quality(self) -> dict:
        request_id = build_request_id()
        toolbox = AnalysisToolbox(self.context, request_id)
        return build_data_quality_payload(self.context, toolbox)

    def _apply_conversation_context(self, question: str, history: list[dict], chart_context: dict) -> str:
        lowered = question.lower()
        needs_context = any(token in question for token in ["此數據", "這個圖", "上述資料", "這份資料", "沿用剛剛"]) or any(
            token in lowered for token in ["this data", "that chart", "previous chart", "same data"]
        )
        if not needs_context:
            return question

        recent_user_questions = [item.get("text", "") for item in history if item.get("role") == "user" and item.get("text")]
        context_lines: list[str] = []
        if recent_user_questions:
            context_lines.append(f"上一輪使用者需求：{recent_user_questions[-1]}")
        if chart_context:
            title = chart_context.get("title")
            filters = chart_context.get("filters", {})
            chart_type = chart_context.get("chart_type")
            pieces = []
            if title:
                pieces.append(f"目前右側圖表：{title}")
            if chart_type:
                pieces.append(f"圖型：{chart_type}")
            if filters.get("month"):
                pieces.append(f"月份：{filters['month']}")
            if filters.get("platform"):
                pieces.append(f"平台：{filters['platform']}")
            if filters.get("group_code"):
                pieces.append(f"事業群：{filters['group_code']}")
            if pieces:
                context_lines.append("；".join(pieces))

        if not context_lines:
            return question

        return f"{question}\n\n參考前文上下文：\n" + "\n".join(context_lines)


APP = DemoApplication()

def _proactive_service(application):
    service = getattr(application, "_proactive_service", None)
    if service is None:
        store = SQLiteProactiveStore(OUTPUT_DIR / "state" / "proactive_workflow.sqlite3")
        service = ProactiveWorkflowOrchestrator(application.context, lambda request_id: application._build_assistant(request_id), store, OUTPUT_DIR / "investigations")
        application._proactive_service = service
    return service

def _proactive_candidates(application): return [to_dict(item) for item in _proactive_service(application).store.list_candidates()]
def _proactive_investigations(application): return [to_dict(item) for item in _proactive_service(application).store.list_investigations()]
def _proactive_approvals(application): return [to_dict(item) for item in _proactive_service(application).store.list_approvals()]
DemoApplication.proactive_scan = lambda self, force=False: _proactive_service(self).scan(trigger_source="api", force_scan=force)
DemoApplication.proactive_candidates = _proactive_candidates
DemoApplication.proactive_investigations = _proactive_investigations
DemoApplication.proactive_approvals = _proactive_approvals


class DemoRequestHandler(BaseHTTPRequestHandler):
    server_version = "MultiAgentDemo/1.0"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """處理 health、summary、chart 與其他唯讀 metadata request。"""
        parsed = urlparse(self.path)
        if parsed.path in {"/", ""}:
            self._send_json(
                {
                    "service": "revenue-intelligence-api",
                    "status": "ok",
                    "web_url": os.getenv("DEMO_WEB_URL", "http://10.8.35.35:3000"),
                    "mobile_url": os.getenv("DEMO_MOBILE_URL", "http://10.8.35.35:3000/mobile"),
                    "endpoints": [
                        "/api/health",
                        "/api/data-version",
                        "/api/pipeline-status",
                        "/api/data-quality",
                        "/api/summary",
                        "/api/chart-catalog",
                        "/api/observe-options",
                        "/api/ask",
                        "/api/chart",
                        "/api/observe",
                    ],
                }
            )
            return
        if parsed.path == "/api/summary":
            self._send_json(APP.get_summary())
            return
        if parsed.path == "/api/health":
            self._send_json(APP.get_health())
            return
        if parsed.path == "/api/data-version":
            self._send_json(APP.get_data_version())
            return
        if parsed.path == "/api/pipeline-status":
            self._send_json(APP.get_pipeline_status())
            return
        if parsed.path == "/api/data-quality":
            self._send_json(APP.get_data_quality())
            return
        if parsed.path == "/api/chart-catalog":
            self._send_json({"charts": APP.get_chart_catalog()})
            return
        if parsed.path == "/api/investigations":
            self._send_json({"investigations": APP.proactive_investigations()})
            return
        if parsed.path == "/api/investigation-candidates":
            self._send_json({"candidates": APP.proactive_candidates()})
            return
        if parsed.path == "/api/approval-requests":
            self._send_json({"approval_requests": APP.proactive_approvals()})
            return
        if parsed.path == "/api/observe-options":
            self._send_json(APP.get_observation_options())
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown API path")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/ask", "/api/chart", "/api/observe", "/api/investigations/scan"} and not parsed.path.startswith("/api/approval-requests/"):
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown API path")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
            if parsed.path.startswith("/api/approval-requests/"):
                pieces = parsed.path.strip("/").split("/")
                if len(pieces) != 4:
                    self._send_json({"error": "Unknown approval action."}, status=HTTPStatus.NOT_FOUND); return
                request = _proactive_service(APP).store.load_approval_request(pieces[2])
                if not request:
                    self._send_json({"error": "approval_not_found"}, status=HTTPStatus.NOT_FOUND); return
                draft = _proactive_service(APP).store.load_draft(request.draft_id); run = _proactive_service(APP).store.load_investigation(request.investigation_id)
                if not draft or not run: raise ValueError("approval_references_missing")
                action = pieces[3]
                if action == "create-revision":
                    response = create_revision(_proactive_service(APP).store, request.approval_request_id, str(payload.get("revised_by", "")), str(payload.get("instructions", "")), OUTPUT_DIR / "investigations" / "drafts", "api_supplied")
                elif action == "publish":
                    record = publish(request, draft, run, OUTPUT_DIR / "investigations" / "drafts", OUTPUT_DIR / "investigations" / "approved", str(payload.get("publisher", "")))
                    _proactive_service(APP).store.save_publication(record); response = to_dict(record)
                else:
                    decision = "request_revision" if action == "request-revision" else action
                    decide(request, draft, run, decision, str(payload.get("approver", "")), payload.get("reason"), payload.get("instructions"), "api_supplied")
                    _proactive_service(APP).store.save_draft(draft); _proactive_service(APP).store.save_approval_request(request); response = to_dict(request)
            elif parsed.path == "/api/investigations/scan":
                response = APP.proactive_scan(bool(payload.get("force", False)))
            elif parsed.path == "/api/ask":
                question = str(payload.get("question", "")).strip()
                if not question:
                    self._send_json({"error": "Question is required."}, status=HTTPStatus.BAD_REQUEST)
                    return
                use_llm_planner = _coerce_optional_bool(payload.get("use_llm_planner"))
                use_llm_rewriter = _coerce_optional_bool(payload.get("use_llm_rewriter"))
                response = APP.ask(
                    question,
                    history=payload.get("history"),
                    chart_context=payload.get("chart_context"),
                    use_llm_planner=use_llm_planner,
                    use_llm_rewriter=use_llm_rewriter,
                )
            elif parsed.path == "/api/chart":
                chart_key = str(payload.get("chart_key", "")).strip()
                if not chart_key:
                    self._send_json({"error": "chart_key is required."}, status=HTTPStatus.BAD_REQUEST)
                    return
                response = APP.get_chart(
                    chart_key=chart_key,
                    filters=payload.get("filters"),
                    render_image=bool(payload.get("render_image", True)),
                    chart_type=payload.get("chart_type"),
                )
            else:
                response = APP.get_observation_table(payload)
            self._send_json(response)
        except Exception as exc:
            APP.logger.exception("Demo web request failed")
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args) -> None:
        APP.logger.info("HTTP %s", format % args)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(_json_safe(payload), ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin.rstrip("/") in CORS_ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), DemoRequestHandler)
    APP.logger.info("Demo server started at http://%s:%s", HOST, PORT)
    print(f"Revenue API running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        APP.logger.info("Demo server stopped by user")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
