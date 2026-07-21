from __future__ import annotations

import os
import traceback
from collections.abc import Callable
from typing import Any

from .evidence_validator import EvidenceValidator
from .models import AgentRunState, AgentRunStatus, PlanStep, PlanStepStatus, ReplanRecord, ToolExecutionRecord, utc_now
from .replanner import DeterministicReplanner, ReplanProposal
from .state_store import AgentStateStore, InMemoryAgentStateStore
from observability import get_recorder, current_context


ToolExecutor = Callable[[str, dict[str, Any]], Any]
AnswerRenderer = Callable[[AgentRunState], tuple[str, str | None]]
ReplanValidator = Callable[[AgentRunState, ReplanProposal], dict[str, Any]]


class StatefulAgentRuntime:
    def __init__(self, *, executor: ToolExecutor, state_store: AgentStateStore | None = None,
                 validator: EvidenceValidator | None = None, replanner: DeterministicReplanner | None = None,
                 replan_validator: ReplanValidator | None = None,
                 logger: Any | None = None) -> None:
        self.executor = executor
        self.store = state_store or InMemoryAgentStateStore()
        self.validator = validator or EvidenceValidator()
        self.replanner = replanner or DeterministicReplanner()
        self.replan_validator = replan_validator
        self.logger = logger

    def run(self, state: AgentRunState, render_answer: AnswerRenderer | None = None) -> AgentRunState:
        recorder = get_recorder()
        if current_context() is not None:
            with recorder.span("agent.run", attributes={"revenue_poc.runtime.mode": "stateful"}):
                return self._run(state, render_answer)
        with recorder.run("agent.run", request_id=state.request_id, runtime_mode="stateful", thread_id=state.thread_id) as trace:
            result = self._run(state, render_answer)
            recorder.finish_run(trace, status=result.status.value, stop_reason=result.stop_reason, failure_category="capability_gap" if result.stop_reason == "capability_gap" else None, counters={"tool_call_count": len(result.tool_executions), "replan_count": result.replan_count})
            return result

    def _run(self, state: AgentRunState, render_answer: AnswerRenderer | None = None) -> AgentRunState:
        self._checkpoint(state, "agent_run.initialized")
        state.status = AgentRunStatus.EXECUTING
        while True:
            pending = next((step for step in state.steps if step.status == PlanStepStatus.PENDING), None)
            if pending is not None:
                if state.step_count >= state.max_steps:
                    return self._stop(state, "max_steps_reached", render_answer)
                self._execute_step(state, pending)
                continue
            state.status = AgentRunStatus.VALIDATING
            self._checkpoint(state, "agent_evidence.validated")
            with get_recorder().span("evidence.validate", attributes={"revenue_poc.evidence.count": len(state.evidence), "revenue_poc.replan.count": state.replan_count}):
                validation = self.validator.validate(state)
            state.validation_issues = validation.issues
            if validation.sufficient:
                return self._finish(state, "completed", render_answer, AgentRunStatus.COMPLETED, validation.confidence)
            if validation.needs_replan:
                state.status = AgentRunStatus.REPLANNING
                self._checkpoint(state, "agent_replan.started")
                with get_recorder().span("agent.replan", attributes={"revenue_poc.replan.count": state.replan_count + 1}):
                    proposal = self.replanner.propose(state, validation.missing_requirements)
                if self._proposal_has_progress(state, proposal):
                    replan_validation = self._validate_replan(state, proposal)
                    if replan_validation["valid"]:
                        self._apply_replan(state, proposal, validation.issues)
                        continue
                    state.validation_issues = [*validation.issues, *(f"invalid_replan:{issue}" for issue in replan_validation.get("violations", []))]
                    state.replanning_history.append(ReplanRecord(
                        replan_index=state.replan_count + 1, trigger="invalid_replan", validation_issues=list(replan_validation.get("violations", [])),
                        previous_plan_version=state.current_plan_version, new_plan_version=None,
                        added_steps=[], planning_source=proposal.source,
                    ))
                    return self._stop(state, "capability_gap" if state.canonical_task.get("semantic_task_requirement_id") and proposal.source == "deterministic_repair" else "invalid_replan", render_answer)
                return self._stop(state, "capability_gap" if state.canonical_task.get("semantic_task_requirement_id") and proposal.reason == "no_legal_non_duplicate_repair" else ("no_progress" if proposal.reason != "max_replans_reached" else "max_replans_reached"), render_answer)
            reason = "max_replans_reached" if state.replan_count >= state.max_replans else "insufficient_evidence"
            return self._stop(state, reason, render_answer)

    def _execute_step(self, state: AgentRunState, step: PlanStep) -> None:
        step.status = PlanStepStatus.RUNNING
        step.started_at = utc_now()
        step.attempt_count += 1
        state.current_step_id = step.step_id
        state.step_count += 1
        record = ToolExecutionRecord(
            execution_id=f"{state.request_id}-e{len(state.tool_executions) + 1}", step_id=step.step_id,
            tool_name=step.tool_name, tool_args=dict(step.tool_args), started_at=step.started_at,
        )
        state.tool_executions.append(record)
        self._checkpoint(state, "agent_step.started", step)
        try:
            with get_recorder().span("tool.execute", attributes={"revenue_poc.step.id": step.step_id, "revenue_poc.tool.name": step.tool_name, "args_fingerprint": repr(sorted(step.tool_args.items()))[:256]}):
                output = self.executor(step.tool_name, dict(step.tool_args))
            summary, evidence, row_count, empty = _summarize_output(output, step.tool_name, len(state.evidence) + 1)
            step.result_summary = summary
            record.result_summary = summary
            record.result_type = type(output).__name__
            record.row_count = row_count
            record.is_empty = empty
            step.finished_at = record.finished_at = utc_now()
            if empty:
                step.status = record.status = PlanStepStatus.EMPTY
                state.validation_issues.append(f"empty_result:{step.tool_name}")
                self._checkpoint(state, "agent_step.empty", step)
            else:
                step.status = record.status = PlanStepStatus.SUCCEEDED
                step.evidence_ids.append(evidence["evidence_id"])
                state.evidence.append(evidence)
                self._checkpoint(state, "agent_step.succeeded", step)
        except (TimeoutError, ValueError, KeyError, TypeError, RuntimeError, OSError) as exc:
            step.status = record.status = PlanStepStatus.FAILED
            step.error_type = record.error_type = type(exc).__name__
            step.error_message = record.error_message = str(exc)
            step.finished_at = record.finished_at = utc_now()
            state.validation_issues.append(f"tool_failure:{step.tool_name}:{type(exc).__name__}")
            self._checkpoint(state, "agent_step.failed", step)
        except Exception as exc:  # boundary: retain unexpected errors for diagnostics, do not crash a user run
            step.status = record.status = PlanStepStatus.FAILED
            step.error_type = record.error_type = type(exc).__name__
            step.error_message = record.error_message = str(exc)
            step.finished_at = record.finished_at = utc_now()
            state.validation_issues.append(f"tool_failure:{step.tool_name}:{type(exc).__name__}")
            self._checkpoint(state, "agent_step.failed", step)

    def _validate_replan(self, state: AgentRunState, proposal: ReplanProposal) -> dict[str, Any]:
        if self.replan_validator is None:
            return {"valid": True, "violations": []}
        return self.replan_validator(state, proposal)

    def _apply_replan(self, state: AgentRunState, proposal: ReplanProposal, issues: list[str]) -> None:
        previous_version = state.current_plan_version
        state.replan_count += 1
        state.current_plan_version += 1
        state.planning_source = "llm_then_deterministic_repair" if state.planning_source.startswith("llm") else proposal.source
        state.steps.extend(proposal.steps)
        state.replanning_history.append(ReplanRecord(
            replan_index=state.replan_count, trigger=proposal.reason, validation_issues=list(issues),
            previous_plan_version=previous_version, new_plan_version=state.current_plan_version,
            added_steps=[step.step_id for step in proposal.steps], planning_source=proposal.source,
        ))
        self._checkpoint(state, "agent_replan.completed")
        state.status = AgentRunStatus.EXECUTING

    @staticmethod
    def _proposal_has_progress(state: AgentRunState, proposal: ReplanProposal) -> bool:
        existing = {(step.tool_name, repr(sorted(step.tool_args.items()))) for step in state.steps}
        return bool(proposal.steps) and any((step.tool_name, repr(sorted(step.tool_args.items()))) not in existing for step in proposal.steps)

    def _finish(self, state: AgentRunState, reason: str, render: AnswerRenderer | None, status: AgentRunStatus, confidence: str) -> AgentRunState:
        state.status, state.stop_reason, state.final_confidence = status, reason, confidence
        if render:
            state.final_answer, rendered_confidence = render(state)
            state.final_confidence = rendered_confidence or state.final_confidence
        self._checkpoint(state, "agent_run.completed")
        return state

    def _stop(self, state: AgentRunState, reason: str, render: AnswerRenderer | None) -> AgentRunState:
        status = AgentRunStatus.PARTIAL if state.evidence else AgentRunStatus.FAILED
        if reason == "capability_gap":
            state.limitations.append("能力缺口：目前 semantic catalog 與 tool registry 沒有合法、非重複的工具可補足缺失 primary evidence。")
        state.limitations.append(f"執行已安全停止：{reason}。")
        return self._finish(state, reason, render, status, "low")

    def _checkpoint(self, state: AgentRunState, event: str, step: PlanStep | None = None) -> None:
        state.touch()
        with get_recorder().span("state.checkpoint", attributes={"event": event, "revenue_poc.plan.version": state.current_plan_version}):
            self.store.save(state)
        if self.logger:
            self.logger.info("%s plan_version=%s step_id=%s tool_name=%s status=%s replan_count=%s stop_reason=%s",
                             event, state.current_plan_version, step.step_id if step else state.current_step_id,
                             step.tool_name if step else None, state.status.value, state.replan_count, state.stop_reason)


def _summarize_output(output: Any, tool_name: str, evidence_index: int) -> tuple[dict[str, Any], dict[str, Any], int, bool]:
    if output is None:
        return {"kind": "none"}, {"evidence_id": f"ev-{evidence_index}", "source_tool": tool_name}, 0, True
    if isinstance(output, list):
        safe = _json_safe(output[:20])
        return {"kind": "list", "row_count": len(output)}, {"evidence_id": f"ev-{evidence_index}", "source_tool": tool_name, "rows": safe}, len(output), not bool(output)
    if isinstance(output, dict):
        safe = _json_safe(output)
        row_count = _extract_row_count(safe)
        has_scalar = any(safe.get(key) is not None for key in ("value", "overall", "summary", "chart_type"))
        empty = row_count == 0 and not has_scalar
        return {"kind": "dict", "keys": sorted(safe.keys())[:20], "row_count": row_count}, {"evidence_id": f"ev-{evidence_index}", "source_tool": tool_name, **safe}, row_count, empty
    safe = _json_safe(output)
    return {"kind": type(output).__name__}, {"evidence_id": f"ev-{evidence_index}", "source_tool": tool_name, "value": safe}, 1, False


def _extract_row_count(output: dict[str, Any]) -> int:
    for key in ("rows", "breakdown", "contributors", "candidates"):
        if isinstance(output.get(key), list):
            return len(output[key])
    return int(output.get("row_count") or (output.get("summary") or {}).get("row_count") or 0)


def _json_safe(value: Any, *, depth: int = 0) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if depth >= 5:
        return "<truncated>"
    if isinstance(value, dict):
        return {str(key): _json_safe(item, depth=depth + 1) for key, item in list(value.items())[:40]}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, depth=depth + 1) for item in value[:20]]
    if hasattr(value, "item"):
        return _json_safe(value.item(), depth=depth + 1)
    return str(value)
