from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from observability.store import SQLiteTraceStore

from .models import EvalCase


@dataclass
class EvalEnvironment:
    root: Path
    runtime_mode: str = "stateful"
    trace_store_path: Path | None = None

    @property
    def temp_root(self) -> Path:
        return self.root

    @property
    def temp_output_root(self) -> Path:
        return self.root / "output"

    @property
    def temp_trace_db(self) -> Path:
        return self.trace_store_path or (self.root / "traces.sqlite3")

    @property
    def temp_agent_state_db(self) -> Path:
        return self.root / "agent_state.sqlite3"

    @property
    def temp_proactive_db(self) -> Path:
        return self.root / "approval" / "proactive.sqlite3"

    @property
    def temp_drafts_root(self) -> Path:
        return self.root / "approval" / "drafts"

    @property
    def temp_approved_root(self) -> Path:
        return self.root / "publication" / "approved"


@dataclass
class ExecutionBackedResult:
    execution_status: str
    request_id: str | None
    trace: dict[str, Any] | None
    normalized_output: dict[str, Any] = field(default_factory=dict)
    artifact_references: list[str] = field(default_factory=list)
    error_summary: str | None = None


class EvaluationExecutionAdapter(Protocol):
    adapter_id: str
    def execute(self, case: EvalCase, environment: EvalEnvironment) -> ExecutionBackedResult: ...


class AssistantExecutionAdapter:
    adapter_id = "assistant"

    def execute(self, case: EvalCase, environment: EvalEnvironment) -> ExecutionBackedResult:
        # Reuse the public assistant entrypoint and the existing deterministic stub harness.
        from tests.support import build_stubbed_assistant
        import config
        original_output = config.OUTPUT_DIR
        trace_path = environment.root / "traces.sqlite3"
        old_env = {key: os.environ.get(key) for key in ("OBSERVABILITY_ENABLED", "TRACE_STORE_PATH", "AGENT_RUNTIME_MODE", "USE_LLM_WRITER")}
        request_id = f"eval-{case.case_id}"
        scenario = self._scenario_for_case(case)
        try:
            config.OUTPUT_DIR = environment.temp_output_root
            environment.temp_output_root.mkdir(parents=True, exist_ok=True)
            os.environ.update({
                "OBSERVABILITY_ENABLED": "true",
                "TRACE_STORE_PATH": str(trace_path),
                "AGENT_RUNTIME_MODE": environment.runtime_mode,
                "USE_LLM_WRITER": "false",
            })
            planner_stub = self._planner_stub_for_scenario(scenario)
            assistant = build_stubbed_assistant(
                request_id,
                use_llm_planner=planner_stub is not None,
                use_llm_rewriter=False,
                use_llm_writer=False,
                llm_client=planner_stub,
            )
            question = self._configure_fixture(case, scenario, assistant)
            response = assistant.answer(question)
            trace = SQLiteTraceStore(trace_path).get_trace(request_id) if trace_path.exists() else None
            state_projection = self._load_state_projection(environment, request_id)
            normalized = {
                "adapter_id": self.adapter_id,
                "adapter_status": "completed",
                "scenario": scenario,
                "question": question,
                "response": self._response_projection(response),
                "state": state_projection,
                "trace_id": (trace or {}).get("trace_id"),
            }
            return ExecutionBackedResult(str((response.get("agent_runtime") or {}).get("status") or "completed"), request_id, trace, normalized)
        except Exception as exc:
            return ExecutionBackedResult(
                "failed",
                None,
                None,
                {"adapter_id": self.adapter_id, "adapter_status": "failed", "scenario": scenario},
                error_summary=type(exc).__name__,
            )
        finally:
            config.OUTPUT_DIR = original_output
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _scenario_for_case(self, case: EvalCase) -> str:
        scenarios={"replan-empty":"valuable_replan","replan-capability":"capability_gap","replan-exception":"tool_exception","replan-invalid-plan":"invalid_plan","replan-no-progress":"no_progress"}
        return scenarios.get(case.case_id,"default")

    def _planner_stub_for_scenario(self, scenario: str) -> Any | None:
        if scenario not in {"valuable_replan","invalid_plan"}:
            return None
        from ollama_client import OllamaCallResult

        if scenario=="invalid_plan":
            class InvalidPlannerStub:
                def generate(self, **_: Any) -> OllamaCallResult:
                    return OllamaCallResult(ok=False,text="",data=None,error="stub")
                def generate_json(self, **_: Any) -> OllamaCallResult:
                    return OllamaCallResult(ok=True,text="",error=None,data={"task_family":"overall_trend_analysis","question_type":"trend","domains":["financial"],"tools":[{"tool_name":"invented_tool","args":{},"reason":"evaluation invalid-plan fixture"}],"answer_mode":"trend","requires_limitations":False,"unsupported_reason":None})
            return InvalidPlannerStub()

        class PrimaryOnlyPlannerStub:
            def generate(self, **_: Any) -> OllamaCallResult:
                return OllamaCallResult(ok=False, text="", data=None, error="stub")

            def generate_json(self, **_: Any) -> OllamaCallResult:
                return OllamaCallResult(
                    ok=True,
                    text="",
                    error=None,
                    data={
                        "task_family": "period_pair_compare",
                        "question_type": "comparison",
                        "domains": ["financial"],
                        "tools": [
                            {
                                "tool_name": "get_entity_period_pair_comparison",
                                "args": {
                                    "entity_dimension": "business_group",
                                    "metric": "revenue",
                                    "period_a": "2026-01",
                                    "period_b": "2026-02",
                                },
                                "reason": "Initial primary evidence only; supporting repair is reserved for runtime replanning.",
                            }
                        ],
                        "answer_mode": "comparison",
                        "requires_limitations": True,
                        "unsupported_reason": None,
                    },
                )

        return PrimaryOnlyPlannerStub()

    def _configure_fixture(self, case: EvalCase, scenario: str, assistant: Any) -> str:
        if scenario == "valuable_replan":
            self._install_valuable_replan_tools(assistant)
            return "2026年1月以及2026年2月營收有什麼區別？"
        if scenario == "capability_gap":
            self._install_capability_gap_tools(assistant)
            return "有沒有營收下降但庫存上升的事業群？"
        if scenario == "tool_exception":
            self._install_tool_exception(assistant)
            return "總體營收趨勢如何？"
        if scenario == "invalid_plan":
            return "總體營收趨勢如何？"
        if scenario == "no_progress":
            self._install_no_progress_tools(assistant)
            return "總體營收趨勢如何？"
        questions={
            "core-revenue-month":"請列出2026年2月各事業群營收",
            "core-inventory-amount":"請列出2026年2月各事業群庫存金額",
            "core-inventory-qty":"請列出2026年2月各事業群庫存數量",
            "core-entity":"3通路方案 2026年2月營收是多少？",
            "core-relationship":"有沒有營收下降但庫存上升的事業群？",
            "core-unsupported":"請預測未來三個月營收",
            "replan-incomplete":"有沒有營收下降但庫存上升的事業群？",
            "semantic-alias":"請列出2026年2月各事業群 revenue",
            "semantic-qty":"請列出2026年2月各事業群庫存數量",
            "semantic-proxy":"請比較各事業群 revenue inventory turnover proxy",
            "semantic-relationship":"有沒有營收下降但庫存上升的事業群？",
        }
        return questions.get(case.case_id,case.question_or_event)

    def _install_tool_exception(self, assistant: Any) -> None:
        def raise_tool_error(**_: Any) -> dict[str, Any]:
            raise RuntimeError("evaluation_tool_failure")
        assistant.toolbox.get_overall_time_series=raise_tool_error

    def _install_no_progress_tools(self, assistant: Any) -> None:
        def empty_time_series(**_: Any) -> dict[str, Any]:
            return {"evidence_type":"overall_time_series","source_tool":"get_overall_time_series","metric":"revenue_amount","rows":[],"limitations":["evaluation fixture: no evidence progress"]}
        assistant.toolbox.get_overall_time_series=empty_time_series

    def _install_valuable_replan_tools(self, assistant: Any) -> None:
        def empty_entity_period_pair(*, entity_dimension: str = "business_group", metric: str = "revenue_amount", period_a: str | None = None, period_b: str | None = None, parent_filter: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
            return {
                "evidence_type": "entity_period_pair_table",
                "source_tool": "get_entity_period_pair_comparison",
                "entity_dimension": entity_dimension,
                "entity_label": "事業群",
                "metric": metric,
                "period_a": period_a or "2026-01",
                "period_b": period_b or "2026-02",
                "rows": [],
                "limitations": ["evaluation fixture: initial period-pair entity comparison intentionally empty."],
            }

        def repair_period_pair_metric(*, metric: str = "revenue_amount", period_a: str | None = None, period_b: str | None = None, dimension: str | None = None, top_n: int | None = None, **_: Any) -> dict[str, Any]:
            return {
                "evidence_type": "period_pair_metric_comparison",
                "source_tool": "get_period_pair_metric_comparison",
                "metric": metric,
                "period_a": period_a or "2026-01",
                "period_b": period_b or "2026-02",
                "dimension": dimension or "overall",
                "rows": [
                    {"metric": metric, "period": period_a or "2026-01", "value": 100.0},
                    {"metric": metric, "period": period_b or "2026-02", "value": 92.0},
                ],
                "summary": {"row_count": 2, "change": -8.0, "direction": "down"},
                "limitations": ["evaluation fixture: deterministic repair used an allowed aggregate period-pair tool."],
            }

        assistant.toolbox.get_entity_period_pair_comparison = empty_entity_period_pair
        assistant.toolbox.get_period_pair_metric_comparison = repair_period_pair_metric

    def _install_capability_gap_tools(self, assistant: Any) -> None:
        def empty_relationship(*, entity_dimension: str = "business_group", recent_n: int | None = None, month: str | None = None, parent_filter: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
            return {
                "evidence_type": "metric_relationship",
                "source_tool": "get_revenue_inventory_relationship",
                "entity_dimension": entity_dimension,
                "entity_label": "事業群",
                "rows": [],
                "limitations": ["evaluation fixture: primary relationship evidence unavailable."],
            }

        assistant.toolbox.get_revenue_inventory_relationship = empty_relationship

    def _load_state_projection(self, environment: EvalEnvironment, request_id: str) -> dict[str, Any]:
        from agent_runtime.state_store import SQLiteAgentStateStore

        db_path = environment.temp_output_root / "state" / "agent_runs.sqlite3"
        if not db_path.exists():
            return {"available": False}
        state = SQLiteAgentStateStore(db_path).load(request_id)
        if state is None:
            return {"available": False}
        return {
            "available": True,
            "status": state.status.value,
            "stop_reason": state.stop_reason,
            "step_count": state.step_count,
            "replan_count": state.replan_count,
            "planning_source": state.planning_source,
            "steps": [
                {
                    "step_id": step.step_id,
                    "plan_version": step.plan_version,
                    "tool_name": step.tool_name,
                    "status": step.status.value,
                    "evidence_ids": list(step.evidence_ids),
                }
                for step in state.steps
            ],
            "tool_executions": [
                {
                    "execution_id": item.execution_id,
                    "step_id": item.step_id,
                    "tool_name": item.tool_name,
                    "status": item.status.value,
                    "row_count": item.row_count,
                    "is_empty": item.is_empty,
                }
                for item in state.tool_executions
            ],
            "replanning_history": [
                {
                    "replan_index": item.replan_index,
                    "trigger": item.trigger,
                    "previous_plan_version": item.previous_plan_version,
                    "new_plan_version": item.new_plan_version,
                    "added_steps": list(item.added_steps),
                    "planning_source": item.planning_source,
                }
                for item in state.replanning_history
            ],
            "evidence": [
                {
                    "evidence_id": item.get("evidence_id"),
                    "source_tool": item.get("source_tool"),
                    "evidence_type": item.get("evidence_type"),
                    "row_count": len(item.get("rows") or item.get("contributors") or item.get("candidates") or []),
                }
                for item in state.evidence
            ],
            "validation_issues": list(state.validation_issues),
            "limitations": list(state.limitations),
        }

    def _response_projection(self, response: dict[str, Any]) -> dict[str, Any]:
        contract = response.get("answer_contract") or {}
        runtime = response.get("agent_runtime") or {}
        return {
            "status": runtime.get("status") or contract.get("status"),
            "stop_reason": response.get("stop_reason") or runtime.get("stop_reason"),
            "has_summary": bool(response.get("summary")),
            "limitations": list(contract.get("limitations") or []),
            "tools_used": list(contract.get("tools_used") or []),
            "evidence_types": [item.get("evidence_type") for item in (contract.get("evidence") or []) if isinstance(item, dict)],
            "runtime": runtime,
        }


class ProactiveExecutionAdapter:
    adapter_id = "proactive"

    def execute(self, case: EvalCase, environment: EvalEnvironment) -> ExecutionBackedResult:
        scenario = self._scenario_for_case(case)
        trace_path = environment.temp_trace_db
        old_env = {key: os.environ.get(key) for key in ("OBSERVABILITY_ENABLED", "TRACE_STORE_PATH")}
        try:
            environment.root.mkdir(parents=True, exist_ok=True)
            environment.temp_output_root.mkdir(parents=True, exist_ok=True)
            os.environ.update({"OBSERVABILITY_ENABLED": "true", "TRACE_STORE_PATH": str(trace_path)})
            from evaluation.fixtures import build_proactive_fixture
            from proactive_workflow.orchestrator import ProactiveWorkflowOrchestrator
            from proactive_workflow.store import SQLiteProactiveStore

            fixture = build_proactive_fixture(self._fixture_id_for_scenario(scenario))
            store = SQLiteProactiveStore(environment.temp_proactive_db)
            workflow = ProactiveWorkflowOrchestrator(fixture.context, fixture.assistant_factory, store, environment.temp_drafts_root.parent)
            if scenario == "unchanged_scan":
                first = workflow.scan(trigger_source="eval-proactive", mode="scan_and_investigate")
                before_second = self._snapshot_counts(store)
                summary = workflow.scan(trigger_source="eval-proactive", mode="scan_and_investigate")
                after_second = self._snapshot_counts(store)
                deltas = {key: after_second[key] - before_second[key] for key in before_second}
                first_summary = first
            else:
                summary = workflow.scan(trigger_source="eval-proactive", mode="scan_and_investigate")
                first_summary = None
                deltas = None
            snapshot = self._snapshot(store, summary, environment)
            self._validate_summary(summary, snapshot, scenario, deltas)
            trace = SQLiteTraceStore(trace_path).get_trace("proactive-eval-proactive") if trace_path.exists() else None
            if trace is None or trace.get("operation_name") != "proactive.scan":
                raise RuntimeError("proactive_trace_missing")
            normalized = {
                "adapter_id": self.adapter_id,
                "adapter_status": "completed",
                "scenario": scenario,
                "execution_status": str(summary.get("status") or "completed"),
                "event_id": summary.get("event_id"),
                "data_changed": bool(summary.get("data_changed")),
                "quality_status": snapshot["quality_status"],
                "blocked_by_quality": bool(summary.get("blocked_by_quality")),
                "candidate_ids": snapshot["candidate_ids"],
                "candidate_types": snapshot["candidate_types"],
                "investigation_ids": snapshot["investigation_ids"],
                "draft_ids": snapshot["draft_ids"],
                "approval_request_ids": snapshot["approval_request_ids"],
                "quality_finding_count": snapshot["store_snapshot_summary"]["finding_count"],
                "candidate_count": snapshot["store_snapshot_summary"]["candidate_count"],
                "investigation_count": snapshot["store_snapshot_summary"]["investigation_count"],
                "draft_count": snapshot["store_snapshot_summary"]["draft_count"],
                "pending_approval_count": snapshot["pending_approval_count"],
                "duplicates_skipped": int(summary.get("duplicates_skipped") or 0),
                "trace_id": trace.get("trace_id"),
                "store_snapshot_summary": snapshot["store_snapshot_summary"],
                "artifact_summary": snapshot["artifact_summary"],
                "limitations": snapshot["limitations"],
            }
            if deltas is not None:
                normalized["first_scan"] = {"data_changed": bool(first_summary.get("data_changed")), "event_id": first_summary.get("event_id")}
                normalized["second_scan_deltas"] = deltas
            return ExecutionBackedResult(str(summary.get("status") or "completed"), str(summary.get("event_id")), trace, normalized, snapshot["artifact_references"])
        except Exception as exc:
            return ExecutionBackedResult(
                "failed",
                None,
                None,
                {"adapter_id": self.adapter_id, "adapter_status": "failed", "scenario": scenario},
                error_summary=type(exc).__name__,
            )
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _scenario_for_case(self, case: EvalCase) -> str:
        text = " ".join([case.fixture_id, case.case_id, case.category, case.description, case.question_or_event]).lower()
        if "quality" in text or "blocker" in text:
            return "quality_blocker"
        if "unchanged" in text:
            return "unchanged_scan"
        if "divergence" in text:
            return "divergence_scan"
        return "new_scan"

    def _fixture_id_for_scenario(self, scenario: str) -> str:
        return {
            "new_scan": "proactive-new-scan-v1",
            "unchanged_scan": "proactive-unchanged-v1",
            "quality_blocker": "proactive-quality-blocker-v1",
            "divergence_scan": "proactive-divergence-v1",
        }[scenario]

    def _snapshot_counts(self, store: Any) -> dict[str, int]:
        return {
            "candidate_count": len(store.list_candidates()),
            "investigation_count": len(store.list_investigations()),
            "draft_count": len(store.list_drafts()),
            "approval_count": len(store.list_approvals()),
        }

    def _snapshot(self, store: Any, summary: dict[str, Any], environment: EvalEnvironment) -> dict[str, Any]:
        import sqlite3

        event = store.load_event(str(summary.get("event_id"))) if summary.get("event_id") else None
        findings = store.list_quality_findings(summary.get("event_id"))
        candidates = store.list_candidates(summary.get("event_id"))
        investigations = store.list_investigations()
        drafts = store.list_drafts()
        approvals = store.list_approvals()
        with sqlite3.connect(store.path) as connection:
            event_count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            audit_event_count = connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        artifact_summary, artifact_references = self._artifact_summary(environment.temp_drafts_root)
        return {
            "quality_status": event.quality_status if event else None,
            "candidate_ids": [item.candidate_id for item in candidates],
            "candidate_types": [item.candidate_type for item in candidates],
            "investigation_ids": [item.investigation_id for item in investigations],
            "draft_ids": [item.draft_id for item in drafts],
            "approval_request_ids": [item.approval_request_id for item in approvals],
            "pending_approval_count": len([item for item in approvals if item.status.value == "pending"]),
            "store_snapshot_summary": {
                "event_count": event_count,
                "finding_count": len(findings),
                "candidate_count": len(candidates),
                "investigation_count": len(investigations),
                "draft_count": len(drafts),
                "approval_count": len(approvals),
                "audit_event_count": audit_event_count,
            },
            "artifact_summary": artifact_summary,
            "artifact_references": artifact_references,
            "limitations": list(dict.fromkeys(limit for collection in (findings,candidates,investigations,drafts) for item in collection for limit in (getattr(item,"limitations",[]) or []))),
            "candidates": candidates,
            "drafts": drafts,
            "findings": findings,
        }

    def _artifact_summary(self, drafts_root: Path) -> tuple[dict[str, Any], list[str]]:
        files = sorted(path for path in drafts_root.rglob("*") if path.is_file()) if drafts_root.exists() else []
        markdown = [path for path in files if path.suffix == ".md"]
        references = ["drafts/" + str(path.relative_to(drafts_root)) for path in files]
        all_under_temporary_root = all(not path.is_absolute() or drafts_root in path.parents for path in files)
        all_marked_not_approved = all("NOT APPROVED" in path.read_text(encoding="utf-8") for path in markdown) if markdown else True
        return {
            "draft_artifact_count": len(files),
            "all_under_temporary_root": all_under_temporary_root,
            "all_marked_not_approved": all_marked_not_approved,
        }, references

    def _validate_summary(self, summary: dict[str, Any], snapshot: dict[str, Any], scenario: str, deltas: dict[str, int] | None) -> None:
        counts = snapshot["store_snapshot_summary"]
        if scenario == "unchanged_scan":
            if summary.get("status") != "unchanged" or summary.get("data_changed") is not False:
                raise RuntimeError("proactive_unchanged_status_mismatch")
            if deltas != {"candidate_count": 0, "investigation_count": 0, "draft_count": 0, "approval_count": 0}:
                raise RuntimeError("proactive_unchanged_duplicate_work")
            return
        if int(summary.get("quality_findings") or 0) != counts["finding_count"]:
            raise RuntimeError("proactive_quality_count_mismatch")
        if int(summary.get("candidates_detected") or 0) != counts["candidate_count"]:
            raise RuntimeError("proactive_candidate_count_mismatch")
        if int(summary.get("candidates_investigated") or 0) != counts["investigation_count"]:
            raise RuntimeError("proactive_investigation_count_mismatch")
        if int(summary.get("drafts_created") or 0) != counts["draft_count"]:
            raise RuntimeError("proactive_draft_count_mismatch")


class MCPExecutionAdapter:
    adapter_id = "mcp"
    timeout_seconds = 20.0

    def execute(self, case: EvalCase, environment: EvalEnvironment) -> ExecutionBackedResult:
        scenario = self._scenario_for_case(case)
        try:
            environment.root.mkdir(parents=True, exist_ok=True)
            result = self._run_async(self._execute_protocol(case, environment, scenario))
            trace = self._latest_mcp_trace(environment.temp_trace_db)
            span_names = [span.get("span_name") for span in (trace or {}).get("spans", [])]
            result["trace_id"] = (trace or {}).get("trace_id")
            result["mcp_span_names"] = span_names
            result["adapter_id"] = self.adapter_id
            result["adapter_status"] = "completed"
            execution_status = str(result.get("execution_status") or "completed")
            return ExecutionBackedResult(execution_status, result.get("trace_id"), trace, result)
        except Exception as exc:
            return ExecutionBackedResult(
                "failed",
                None,
                None,
                {"adapter_id": self.adapter_id, "adapter_status": "failed", "scenario": scenario},
                error_summary=type(exc).__name__,
            )

    def _run_async(self, coroutine: Any) -> Any:
        import asyncio

        return asyncio.run(asyncio.wait_for(coroutine, timeout=self.timeout_seconds))

    async def _execute_protocol(self, case: EvalCase, environment: EvalEnvironment, scenario: str) -> dict[str, Any]:
        import asyncio
        import sys
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        root = Path(__file__).resolve().parents[1]
        fixture_id = self._fixture_id_for_case(case, scenario)
        env = dict(os.environ)
        env.update({
            "OBSERVABILITY_ENABLED": "true",
            "TRACE_STORE_PATH": str(environment.temp_trace_db),
            "REVENUE_POC_TRACE_DB": str(environment.temp_trace_db),
            "REVENUE_POC_EVAL_FIXTURE_ID": fixture_id,
        })
        params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"], cwd=root, env=env)
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                init = await asyncio.wait_for(session.initialize(), timeout=self.timeout_seconds)
                tools_result = await asyncio.wait_for(session.list_tools(), timeout=self.timeout_seconds)
                resources_result = await asyncio.wait_for(session.list_resources(), timeout=self.timeout_seconds)
                templates_result = await asyncio.wait_for(session.list_resource_templates(), timeout=self.timeout_seconds)
                tool_names = [item.name for item in tools_result.tools]
                self._validate_tool_boundary(tool_names)
                base = {
                    "scenario": scenario,
                    "server_initialized": bool(init.serverInfo.name),
                    "protocol_completed": True,
                    "tool_names": tool_names,
                    "resource_count": len(resources_result.resources),
                    "resource_template_count": len(templates_result.resourceTemplates),
                    "called_tool": None,
                    "called_resource": None,
                    "evidence_type": None,
                    "safe_result_item_count": None,
                    "row_cap": 20,
                    "validation_error_type": None,
                    "security_rejection": False,
                    "security_outcome": "allowed",
                    "subprocess_exit_status": "clean",
                    "subprocess_cleaned_up": True,
                }
                if scenario == "resource_read":
                    resource_uri = "semantic://metrics/revenue_amount"
                    payload = await asyncio.wait_for(session.read_resource(resource_uri), timeout=self.timeout_seconds)
                    base.update({
                        "execution_status": "completed",
                        "called_resource": resource_uri,
                        "safe_result_item_count": len(payload.contents),
                    })
                    return base
                if scenario == "invalid_arguments":
                    result = await asyncio.wait_for(session.call_tool("get_entity_month_table", {"entity_dimension": "bad", "metric": "revenue_amount", "month": "2025-01"}), timeout=self.timeout_seconds)
                    if not result.isError:
                        raise RuntimeError("mcp_invalid_arguments_not_rejected")
                    base.update({
                        "execution_status": "rejected",
                        "called_tool": "get_entity_month_table",
                        "validation_error_type": self._safe_error_type(result),
                        "security_rejection": True,
                        "security_outcome": "expected_rejection",
                    })
                    return base
                if scenario == "hidden_tool_rejection":
                    result = await asyncio.wait_for(session.call_tool("approve_report", {}), timeout=self.timeout_seconds)
                    if not result.isError:
                        raise RuntimeError("mcp_hidden_tool_not_rejected")
                    base.update({
                        "execution_status": "rejected",
                        "called_tool": "approve_report",
                        "validation_error_type": self._safe_error_type(result),
                        "security_rejection": True,
                        "security_outcome": "expected_rejection",
                        "rejection_layer": "framework_tool_lookup",
                    })
                    return base
                if scenario == "output_cap":
                    result = await asyncio.wait_for(session.call_tool("get_entity_month_table", {"entity_dimension": "business_group", "metric": "revenue_amount", "month": "2025-03"}), timeout=self.timeout_seconds)
                    if result.isError:
                        raise RuntimeError("mcp_output_cap_call_failed")
                    payload = self._tool_payload(result)
                    rows = ((payload.get("result") or {}).get("rows") or []) if isinstance(payload.get("result"), dict) else []
                    if len(rows) > 20:
                        raise RuntimeError("mcp_row_cap_exceeded")
                    base.update({
                        "execution_status": "completed",
                        "called_tool": "get_entity_month_table",
                        "evidence_type": payload.get("evidence_type"),
                        "safe_result_item_count": len(rows),
                    })
                    return base
                result = await asyncio.wait_for(session.call_tool("get_data_coverage", {}), timeout=self.timeout_seconds)
                if result.isError:
                    raise RuntimeError("mcp_allowed_tool_call_failed")
                payload = self._tool_payload(result)
                base.update({
                    "execution_status": "completed",
                    "called_tool": "get_data_coverage",
                    "evidence_type": payload.get("evidence_type"),
                    "safe_result_item_count": self._safe_count(payload.get("result")),
                })
                return base

    def _scenario_for_case(self, case: EvalCase) -> str:
        text = " ".join([case.fixture_id, case.case_id, case.category, case.description, case.question_or_event]).lower()
        if "resource" in text:
            return "resource_read"
        if "invalid" in text or "argument" in text:
            return "invalid_arguments"
        if "hidden" in text or "approve_report" in text:
            return "hidden_tool_rejection"
        if "cap" in text or "row" in text:
            return "output_cap"
        return "allowed_tool_call"

    def _fixture_id_for_case(self, case: EvalCase, scenario: str) -> str:
        if case.fixture_id.startswith("mcp-"):
            if case.fixture_id not in {"mcp-basic-v1", "mcp-row-cap-v1"}:
                raise ValueError("unsupported_mcp_fixture")
            return case.fixture_id
        return "mcp-row-cap-v1" if scenario == "output_cap" else "mcp-basic-v1"

    def _tool_payload(self, result: Any) -> dict[str, Any]:
        import json

        if getattr(result, "structuredContent", None):
            return dict(result.structuredContent)
        for item in getattr(result, "content", []) or []:
            text = getattr(item, "text", None)
            if text:
                parsed = json.loads(text)
                return parsed if isinstance(parsed, dict) else {"value": parsed}
        return {}

    def _safe_error_type(self, result: Any) -> str:
        text = " ".join(str(getattr(item, "text", "")) for item in (getattr(result, "content", []) or []))
        for token in ("mcp_tool_rejected", "ToolError", "not found", "Unknown tool", "ValueError"):
            if token.lower() in text.lower():
                return token.replace(" ", "_").lower()[:64]
        return "protocol_rejection"

    def _safe_count(self, value: Any) -> int:
        if isinstance(value, dict):
            if isinstance(value.get("rows"), list):
                return len(value["rows"])
            return len(value)
        if isinstance(value, list):
            return len(value)
        return 1 if value is not None else 0

    def _latest_mcp_trace(self, trace_path: Path) -> dict[str, Any] | None:
        if not trace_path.exists():
            return None
        store = SQLiteTraceStore(trace_path)
        for item in store.list_traces(limit=20):
            if item.get("operation_name") == "mcp.server.request":
                return store.get_trace(item.get("trace_id"))
        return None

    def _validate_tool_boundary(self, tool_names: list[str]) -> None:
        from tool_registry import TOOL_REGISTRY

        forbidden_tokens = {"approve", "reject", "revision", "publish", "write", "write_back", "python", "run_python", "sql", "execute_sql", "shell", "execute_shell", "filesystem", "delete", "update", "send", "email", "slack", "webhook"}
        for name in tool_names:
            lowered = name.lower()
            tokens = {part for chunk in lowered.split("-") for part in chunk.split("_")}
            if tokens & forbidden_tokens:
                raise RuntimeError("mcp_forbidden_tool_exposed")
            contract = TOOL_REGISTRY.get(name)
            if contract is None or not contract.read_only or contract.risk_level != "low" or not contract.mcp_exposable:
                raise RuntimeError("mcp_registry_boundary_mismatch")


class ApprovalExecutionAdapter:
    adapter_id = "approval"

    def execute(self, case: EvalCase, environment: EvalEnvironment) -> ExecutionBackedResult:
        action = self._action_for_case(case)
        trace_path = environment.trace_store_path or (environment.root / "traces.sqlite3")
        old_env = {key: os.environ.get(key) for key in ("OBSERVABILITY_ENABLED", "TRACE_STORE_PATH")}
        try:
            environment.root.mkdir(parents=True, exist_ok=True)
            os.environ.update({"OBSERVABILITY_ENABLED": "true", "TRACE_STORE_PATH": str(trace_path)})
            store, run, draft, request = self._seed_pending_request(environment.root)
            if action == "approve":
                normalized = self._approve(store, run, draft, request)
            elif action == "reject":
                normalized = self._reject(store, run, draft, request)
            elif action == "revision":
                normalized = self._revision(store, run, draft, request, environment.root)
            else:
                raise ValueError(f"unsupported_approval_adapter_action:{action}")
            trace = SQLiteTraceStore(trace_path).get_trace(request.approval_request_id) if trace_path.exists() else None
            if trace is None:
                raise RuntimeError("approval_trace_missing")
            normalized["trace_id"] = trace.get("trace_id")
            normalized["adapter_id"] = self.adapter_id
            normalized["adapter_status"] = "completed"
            return ExecutionBackedResult("completed", request.approval_request_id, trace, normalized)
        except Exception as exc:
            return ExecutionBackedResult(
                "failed",
                None,
                None,
                {"adapter_id": self.adapter_id, "adapter_status": "failed", "action": action},
                error_summary=type(exc).__name__,
            )
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _action_for_case(self, case: EvalCase) -> str:
        text = " ".join([case.case_id, case.category, case.description, case.question_or_event]).lower()
        if "revision" in text or "revise" in text:
            return "revision"
        if "reject" in text:
            return "reject"
        return "approve"

    def _seed_pending_request(self, root: Path):
        from proactive_workflow.approval import create_approval_request
        from proactive_workflow.draft_builder import build_draft
        from proactive_workflow.models import InvestigationCandidate, InvestigationRun, Severity
        from proactive_workflow.store import SQLiteProactiveStore

        store = SQLiteProactiveStore(root / "approval" / "proactive.sqlite3")
        drafts_root = root / "approval" / "drafts"
        (root / "approval" / "output").mkdir(parents=True, exist_ok=True)
        candidate = InvestigationCandidate(
            "eval-approval-candidate",
            "eval-approval-event",
            "revenue_inventory_divergence",
            "Approval adapter fixture",
            "Synthetic approval fixture generated for isolated adapter execution.",
            ["revenue_amount", "inventory_amount"],
            ["business_group"],
            {"business_group": "fixture"},
            {"mode": "period_pair", "periods": ["2024-01", "2024-02"]},
            "evaluation.approval",
            "v1",
            severity=Severity.MEDIUM,
            confidence="medium",
            supporting_signals=[{"evidence_type": "relationship_signal", "summary": "fixture only"}],
            deduplication_key="eval-approval-dedup",
            limitations=["Synthetic evaluation fixture; not real company data."],
        )
        run = InvestigationRun(
            "eval-approval-investigation",
            candidate.candidate_id,
            candidate.event_id,
            "eval-approval-request",
            "completed",
            semantic_requirement_id="metric_relationship_analysis.v1",
            evidence_summary=[{"evidence_type": "relationship_signal", "summary": "fixture only"}],
            counter_evidence_summary={"status": "not_available"},
            limitations=["Synthetic evaluation fixture; not real company data."],
            confidence="medium",
        )
        draft = build_draft(candidate, run, drafts_root)
        request = create_approval_request(run, draft)
        run.draft_id = draft.draft_id
        run.approval_request_id = request.approval_request_id
        store.save_candidate(candidate)
        store.save_investigation(run)
        store.save_draft(draft)
        store.save_approval_request(request)
        return store, run, draft, request

    def _approve(self, store: Any, run: Any, draft: Any, request: Any) -> dict[str, Any]:
        from proactive_workflow.approval import decide

        decided = decide(request, draft, run, "approve", "eval-reviewer", identity_source="test")
        store.save_draft(draft)
        store.save_approval_request(decided)
        loaded_request = store.load_approval_request(request.approval_request_id)
        loaded_draft = store.load_draft(draft.draft_id)
        if loaded_request is None or loaded_draft is None:
            raise RuntimeError("approval_store_reload_failed")
        content_hash_match = loaded_request.approved_content_hash == loaded_draft.content_hash == loaded_request.draft_content_hash
        if loaded_request.status.value != "approved" or not content_hash_match or loaded_request.identity_source != "test" or loaded_request.identity_verified:
            raise RuntimeError("approval_store_mismatch")
        return {
            "action": "approve",
            "old_approval_request_id": loaded_request.approval_request_id,
            "new_approval_request_id": None,
            "old_draft_id": loaded_draft.draft_id,
            "new_draft_id": None,
            "final_approval_status": loaded_request.status.value,
            "draft_version": loaded_draft.version,
            "content_hash_match": content_hash_match,
        }

    def _reject(self, store: Any, run: Any, draft: Any, request: Any) -> dict[str, Any]:
        from proactive_workflow.approval import decide

        decided = decide(request, draft, run, "reject", "eval-reviewer", reason="evaluation rejection", identity_source="test")
        store.save_draft(draft)
        store.save_approval_request(decided)
        loaded_request = store.load_approval_request(request.approval_request_id)
        loaded_draft = store.load_draft(draft.draft_id)
        if loaded_request is None or loaded_draft is None:
            raise RuntimeError("approval_store_reload_failed")
        if loaded_request.status.value != "rejected" or not loaded_request.decision_reason:
            raise RuntimeError("approval_reject_store_mismatch")
        return {
            "action": "reject",
            "old_approval_request_id": loaded_request.approval_request_id,
            "new_approval_request_id": None,
            "old_draft_id": loaded_draft.draft_id,
            "new_draft_id": None,
            "final_approval_status": loaded_request.status.value,
            "draft_version": loaded_draft.version,
            "content_hash_match": loaded_request.draft_content_hash == loaded_draft.content_hash,
        }

    def _revision(self, store: Any, run: Any, draft: Any, request: Any, root: Path) -> dict[str, Any]:
        from proactive_workflow.approval import decide
        from proactive_workflow.revision import create_revision

        decided = decide(
            request,
            draft,
            run,
            "request_revision",
            "eval-reviewer",
            instructions="clarify limitations",
            identity_source="test",
        )
        store.save_draft(draft)
        store.save_approval_request(decided)
        revision = create_revision(
            store,
            request.approval_request_id,
            "eval-reviser",
            "clarify limitations",
            root / "approval" / "drafts",
            "test",
        )
        old_request = store.load_approval_request(request.approval_request_id)
        old_draft = store.load_draft(draft.draft_id)
        new_request = store.load_approval_request(revision["new_approval_request_id"])
        new_draft = store.load_draft(revision["new_draft_id"])
        if old_request is None or old_draft is None or new_request is None or new_draft is None:
            raise RuntimeError("approval_revision_store_reload_failed")
        content_hash_match = new_request.draft_content_hash == new_draft.content_hash
        if old_request.status.value != "revision_requested" or old_draft.status.value != "superseded" or new_request.status.value != "pending" or not content_hash_match:
            raise RuntimeError("approval_revision_store_mismatch")
        return {
            "action": "revision",
            "old_approval_request_id": old_request.approval_request_id,
            "new_approval_request_id": new_request.approval_request_id,
            "old_draft_id": old_draft.draft_id,
            "new_draft_id": new_draft.draft_id,
            "final_approval_status": new_request.status.value,
            "draft_version": new_draft.version,
            "content_hash_match": content_hash_match,
        }


class PublicationExecutionAdapter(ApprovalExecutionAdapter):
    adapter_id = "publication"

    def execute(self, case: EvalCase, environment: EvalEnvironment) -> ExecutionBackedResult:
        scenario = self._scenario_for_case(case)
        trace_path = environment.trace_store_path or (environment.root / "traces.sqlite3")
        old_env = {key: os.environ.get(key) for key in ("OBSERVABILITY_ENABLED", "TRACE_STORE_PATH")}
        try:
            environment.root.mkdir(parents=True, exist_ok=True)
            environment.temp_output_root.mkdir(parents=True, exist_ok=True)
            os.environ.update({"OBSERVABILITY_ENABLED": "true", "TRACE_STORE_PATH": str(trace_path)})
            store, run, draft, request = self._seed_pending_request(environment.root)
            if scenario == "approved_publish":
                normalized = self._approved_publish(store, run, draft, request, environment)
            elif scenario == "pending_publish_blocked":
                normalized = self._blocked_publish(store, run, draft, request, environment, "approval_required")
            elif scenario == "rejected_publish_blocked":
                self._reject(store, run, draft, request)
                request = store.load_approval_request(request.approval_request_id)
                draft = store.load_draft(draft.draft_id)
                normalized = self._blocked_publish(store, run, draft, request, environment, "approval_required")
            elif scenario == "superseded_publish_blocked":
                self._revision(store, run, draft, request, environment.root)
                old_request = store.load_approval_request(request.approval_request_id)
                old_draft = store.load_draft(draft.draft_id)
                normalized = self._blocked_publish(store, run, old_draft, old_request, environment, "approval_required")
            elif scenario == "hash_mismatch_blocked":
                self._approve(store, run, draft, request)
                request = store.load_approval_request(request.approval_request_id)
                draft = store.load_draft(draft.draft_id)
                draft.content_hash = "mismatch-" + draft.content_hash
                store.save_draft(draft)
                normalized = self._blocked_publish(store, run, draft, request, environment, "approved_hash_mismatch")
            else:
                raise ValueError(f"unsupported_publication_adapter_scenario:{scenario}")
            trace = SQLiteTraceStore(trace_path).get_trace(request.approval_request_id) if trace_path.exists() else None
            if trace is None or trace.get("operation_name") != "publication.publish":
                raise RuntimeError("publication_trace_missing")
            normalized["trace_id"] = trace.get("trace_id")
            normalized["adapter_id"] = self.adapter_id
            normalized["adapter_status"] = "completed"
            return ExecutionBackedResult("completed", request.approval_request_id, trace, normalized, self._artifact_references(normalized))
        except Exception as exc:
            return ExecutionBackedResult(
                "failed",
                None,
                None,
                {"adapter_id": self.adapter_id, "adapter_status": "failed", "scenario": scenario},
                error_summary=type(exc).__name__,
            )
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _scenario_for_case(self, case: EvalCase) -> str:
        text = " ".join([case.case_id, case.category, case.description, case.question_or_event]).lower()
        if "hash" in text:
            return "hash_mismatch_blocked"
        if "superseded" in text:
            return "superseded_publish_blocked"
        if "reject" in text or "rejected" in text:
            return "rejected_publish_blocked"
        if "pending" in text:
            return "pending_publish_blocked"
        return "approved_publish"

    def _approved_publish(self, store: Any, run: Any, draft: Any, request: Any, environment: EvalEnvironment) -> dict[str, Any]:
        from proactive_workflow.publisher import publish

        self._approve(store, run, draft, request)
        loaded_request = store.load_approval_request(request.approval_request_id)
        loaded_draft = store.load_draft(draft.draft_id)
        if loaded_request is None or loaded_draft is None:
            raise RuntimeError("publication_approval_reload_failed")
        record = publish(loaded_request, loaded_draft, run, environment.temp_drafts_root, environment.temp_approved_root, "eval-publisher")
        store.save_publication(record)
        loaded_record = store.load_publication(record.publication_id)
        if loaded_record is None:
            raise RuntimeError("publication_record_missing")
        artifact_exists = all((environment.temp_approved_root / path).exists() for path in loaded_record.artifact_paths)
        approval_json = environment.temp_approved_root / run.investigation_id / "approval.json"
        artifact_hash_match = loaded_record.content_hash == loaded_draft.content_hash == loaded_request.approved_content_hash
        if approval_json.exists():
            import json
            artifact_hash_match = artifact_hash_match and json.loads(approval_json.read_text(encoding="utf-8"))["content_hash"] == loaded_draft.content_hash
        if loaded_record.status != "published" or not artifact_exists or not artifact_hash_match:
            raise RuntimeError("publication_store_or_artifact_mismatch")
        return self._publication_output(
            scenario="approved_publish",
            request=loaded_request,
            draft=loaded_draft,
            publication_id=loaded_record.publication_id,
            publication_status=loaded_record.status,
            security_outcome="published",
            artifact_exists=artifact_exists,
            artifact_hash_match=artifact_hash_match,
            store=store,
            artifact_paths=loaded_record.artifact_paths,
        )

    def _blocked_publish(self, store: Any, run: Any, draft: Any, request: Any, environment: EvalEnvironment, expected_reason: str) -> dict[str, Any]:
        from proactive_workflow.publisher import publish

        if request is None or draft is None:
            raise RuntimeError("publication_block_fixture_missing")
        rejection_reason = None
        try:
            record = publish(request, draft, run, environment.temp_drafts_root, environment.temp_approved_root, "eval-publisher")
        except ValueError as exc:
            rejection_reason = str(exc)
        else:
            store.save_publication(record)
            raise RuntimeError("publication_block_expected")
        if rejection_reason != expected_reason:
            raise RuntimeError(f"publication_unexpected_rejection:{rejection_reason}")
        artifact_root = environment.temp_approved_root / run.investigation_id
        if artifact_root.exists() and any(artifact_root.iterdir()):
            raise RuntimeError("publication_block_artifact_created")
        return self._publication_output(
            scenario=self._blocked_scenario_name(expected_reason, request, draft),
            request=request,
            draft=draft,
            publication_id=None,
            publication_status="blocked",
            security_outcome="expected_rejection",
            artifact_exists=False,
            artifact_hash_match=False,
            store=store,
            artifact_paths=[],
            rejection_reason=rejection_reason,
        )

    def _blocked_scenario_name(self, expected_reason: str, request: Any, draft: Any) -> str:
        if expected_reason == "approved_hash_mismatch":
            return "hash_mismatch_blocked"
        if getattr(draft, "status", None) is not None and draft.status.value == "superseded":
            return "superseded_publish_blocked"
        if getattr(request, "status", None) is not None and request.status.value == "rejected":
            return "rejected_publish_blocked"
        return "pending_publish_blocked"

    def _publication_output(
        self,
        *,
        scenario: str,
        request: Any,
        draft: Any,
        publication_id: str | None,
        publication_status: str,
        security_outcome: str,
        artifact_exists: bool,
        artifact_hash_match: bool,
        store: Any,
        artifact_paths: list[str],
        rejection_reason: str | None = None,
    ) -> dict[str, Any]:
        return {
            "scenario": scenario,
            "approval_request_id": request.approval_request_id,
            "draft_id": draft.draft_id,
            "publication_id": publication_id,
            "approval_status": request.status.value,
            "publication_status": publication_status,
            "security_outcome": security_outcome,
            "artifact_exists": artifact_exists,
            "artifact_hash_match": artifact_hash_match,
            "rejection_reason": rejection_reason,
            "artifact_references": [f"approved/{path}" for path in artifact_paths],
            "store_snapshot_summary": self._store_snapshot(store, draft, request),
        }

    def _store_snapshot(self, store: Any, draft: Any, request: Any) -> dict[str, Any]:
        import sqlite3

        with sqlite3.connect(store.path) as connection:
            publication_record_count = connection.execute("SELECT COUNT(*) FROM publications").fetchone()[0]
            successful_publication_count = connection.execute("SELECT COUNT(*) FROM publications WHERE json_extract(payload, '$.status') = 'published'").fetchone()[0]
            audit_event_count = connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        return {
            "publication_record_count": publication_record_count,
            "successful_publication_count": successful_publication_count,
            "draft_status": draft.status.value,
            "approval_status": request.status.value,
            "audit_event_count": audit_event_count,
        }

    def _artifact_references(self, normalized: dict[str, Any]) -> list[str]:
        refs = normalized.get("artifact_references") or []
        return [str(item) for item in refs if isinstance(item, str) and not str(item).startswith("/")]


class RecordedTraceAdapter:
    adapter_id = "trace_only"
    def execute(self, case: EvalCase, environment: EvalEnvironment) -> ExecutionBackedResult:
        return ExecutionBackedResult("failed", None, None, error_summary="recorded_trace_reference_required")


class SyntheticTrajectoryAdapter:
    adapter_id = "trace_only"
    def execute(self, case: EvalCase, environment: EvalEnvironment) -> ExecutionBackedResult:
        raise RuntimeError("synthetic adapter is handled explicitly by EvaluationRunner")


ADAPTERS: dict[str, EvaluationExecutionAdapter] = {
    "assistant": AssistantExecutionAdapter(), "proactive": ProactiveExecutionAdapter(), "mcp": MCPExecutionAdapter(),
    "approval": ApprovalExecutionAdapter(), "publication": PublicationExecutionAdapter(), "trace_only": RecordedTraceAdapter(),
}
