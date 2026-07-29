from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any

from answer_contract import build_answer_contract, render_answer_contract
from answer_plan import build_answer_plan
from analysis_tools import QueryFilters
from canonical_task import CanonicalTaskProfile
from task_profile import build_task_profile
from tool_registry import TOOL_REGISTRY, is_tool_allowed_for_task
from semantic_layer.adapters import enrich_answer_plan
from observability import get_recorder

from .models import AgentRunState, AgentRunStatus, PlanStep, PlanStepStatus
from .plan_validation import validate_stateful_steps
from .runtime import StatefulAgentRuntime
from .state_store import SQLiteAgentStateStore


def attach_stateful_answer(assistant_class: type[Any]) -> None:
    """Attach the runtime without adding a second business implementation to multi_agent.py."""
    legacy_answer = assistant_class.answer

    def answer(self: Any, question: str) -> dict[str, Any]:
        if os.getenv("AGENT_RUNTIME_MODE", "stateful").strip().lower() == "legacy":
            return legacy_answer(self, question)
        return _stateful_answer(self, question, legacy_answer)

    assistant_class.answer = answer


def _stateful_answer_impl(assistant: Any, question: str, legacy_answer: Any) -> dict[str, Any]:
    assistant.logger.info("agent_run.initialized runtime_mode=stateful")
    with get_recorder().span("agent.canonicalize", attributes={}):
        routing = assistant._run_question_understanding(question)
        task_profile = build_task_profile(question, routing)
        canonical = CanonicalTaskProfile.from_task_profile(task_profile, routing)
    with get_recorder().span("agent.answer_plan", attributes={"revenue_poc.task.type": canonical.task_family}):
        answer_plan = enrich_answer_plan(build_answer_plan(task_profile, routing), canonical)
    assistant._apply_phase8a_answer_plan_hints(routing, task_profile, answer_plan)
    routing = assistant._maybe_apply_llm_planner(question, routing, task_profile, answer_plan, canonical)
    # Existing summary/data-quality/chart paths are already deterministic, public contracts.
    # Deterministic period-pair comparison keeps the legacy public tools_used naming;
    # LLM-planned period-pair runs still exercise the stateful runtime for evaluation repair cases.
    if routing.question_type in {"overview", "data_quality"} or canonical.task_family == "chart_request" or (canonical.task_family == "period_pair_compare" and routing.planning_source != "llm_planner"):
        return legacy_answer(assistant, question)

    planned_tool_calls = getattr(routing, "planned_tool_calls", None) if routing.planning_source == "llm_planner" else None
    steps = _materialize_steps(canonical, answer_plan, routing.planned_tools if routing.planning_source == "llm_planner" else None, planned_tool_calls)
    state = AgentRunState(
        request_id=assistant.request_id, thread_id=assistant.request_id, question=question,
        canonical_task=canonical.to_dict(), routing_summary=assistant._build_routing_payload(routing),
        answer_plan_summary=asdict(answer_plan), steps=steps,
        planning_source=routing.planning_source or "deterministic",
        max_steps=_limit("AGENT_MAX_STEPS", 8, minimum=1), max_replans=_limit("AGENT_MAX_REPLANS", 2, minimum=0),
        max_attempts_per_step=_limit("AGENT_MAX_STEP_ATTEMPTS", 2, minimum=1),
    )
    with get_recorder().span("agent.plan.validate", attributes={"revenue_poc.plan.version": 1}):
        validation = validate_stateful_steps(canonical, steps, answer_plan)
    if not validation["valid"]:
        state.status = AgentRunStatus.FAILED
        state.stop_reason = "invalid_replan"
        state.validation_issues = [f"invalid_initial_plan:{item}" for item in validation["violations"]]
        response = legacy_answer(assistant, question)
        response.update({"agent_runtime": state.concise_trace(), "agent_state_summary": state.to_dict(),
                         "execution_trace": [], "replanning": [], "stop_reason": "deterministic_fallback_completed"})
        return response

    output_dir = __import__("config").OUTPUT_DIR
    store = SQLiteAgentStateStore(output_dir / "state" / "agent_runs.sqlite3")
    runtime = StatefulAgentRuntime(
        executor=lambda name, args: _execute_tool(assistant, name, args),
        state_store=store,
        replan_validator=lambda current, proposal: validate_stateful_steps(canonical, [*current.steps, *proposal.steps], answer_plan),
        logger=assistant.logger,
    )
    state = runtime.run(state)
    evidence = [{key: value for key, value in item.items() if key != "evidence_id"} for item in state.evidence]
    domain_result_type = __import__("multi_agent").DomainResult
    domain_result = domain_result_type(
        domain="financial", status="success" if state.status == AgentRunStatus.COMPLETED else "partial",
        task="Stateful deterministic tool execution", key_findings=["已依序執行並驗證工具證據。"], evidence=evidence,
        warnings=list(dict.fromkeys([*routing.warnings, *state.warnings, *state.limitations])),
        confidence=state.final_confidence or "low", used_tools=[s.tool_name for s in state.steps if s.status == PlanStepStatus.SUCCEEDED],
    )
    evidence_contracts = assistant._log_evidence_contracts([domain_result], canonical)
    with get_recorder().span("answer.contract", attributes={"revenue_poc.evidence.count": len(evidence), "revenue_poc.stop.reason": state.stop_reason or ""}):
        contract = build_answer_contract(request_id=assistant.request_id, question=question, routing=routing, domain_results=[domain_result],
                                         toolbox=assistant.toolbox, task_profile=task_profile, answer_plan=answer_plan)
    semantic_limitations = list(answer_plan.required_limitations)
    if state.limitations or semantic_limitations:
        contract["limitations"] = list(dict.fromkeys([*(contract.get("limitations") or []), *semantic_limitations, *state.limitations]))
    assistant._maybe_run_llm_writer_shadow(question=question, canonical_task_profile=canonical, evidence_contracts=evidence_contracts,
                                           contract=contract, task_profile=task_profile)
    contract = assistant._maybe_rewrite_answer_contract(question, contract)
    with get_recorder().span("answer.render", attributes={"revenue_poc.evidence.count": len(contract.get("evidence") or [])}):
        state.final_answer = render_answer_contract(assistant.request_id, contract)
    store.save(state)
    response = assistant._build_response_payload(routing=routing, contract=contract, domain_results=[domain_result],
                                                 task_profile=task_profile, answer_plan=answer_plan)
    response.update({"agent_runtime": state.concise_trace(),
                     "agent_state_summary": {k: v for k, v in state.to_dict().items() if k not in {"evidence", "tool_executions"}},
                     "execution_trace": state.concise_trace()["steps"], "replanning": [asdict(item) for item in state.replanning_history],
                     "stop_reason": state.stop_reason})
    return response


def _stateful_answer(assistant: Any, question: str, legacy_answer: Any) -> dict[str, Any]:
    recorder = get_recorder()
    with recorder.run("agent.request", request_id=assistant.request_id, runtime_mode="stateful", thread_id=assistant.request_id) as trace:
        response = _stateful_answer_impl(assistant, question, legacy_answer)
        runtime = response.get("agent_runtime") or {}
        recorder.finish_run(trace, status=str(runtime.get("status") or "completed"), stop_reason=response.get("stop_reason"), counters={"tool_call_count": int(runtime.get("step_count") or 0), "replan_count": int(runtime.get("replan_count") or 0)})
        return response

def _limit(name: str, default: int, *, minimum: int) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _materialize_steps(
    canonical: CanonicalTaskProfile,
    answer_plan: Any,
    planned_tools: list[str] | None = None,
    planned_tool_calls: list[dict[str, Any]] | None = None,
) -> list[PlanStep]:
    steps: list[PlanStep] = []
    primary_names = {str(tool).split("(", 1)[0] for tool in answer_plan.primary_tools}
    if planned_tool_calls:
        selected: list[tuple[str, dict[str, Any]]] = [
            (str(call.get("tool_name") or ""), dict(call.get("args") or {}))
            for call in planned_tool_calls
        ]
    else:
        selected = [(str(raw).split("(", 1)[0], {}) for raw in (planned_tools or [*answer_plan.primary_tools, *answer_plan.supporting_tools])]
    for tool_name, explicit_args in selected:
        purpose = "primary evidence" if tool_name in primary_names else "supporting evidence"
        if tool_name not in TOOL_REGISTRY or not is_tool_allowed_for_task(tool_name, canonical.task_family):
            continue
        base_args = {**_tool_args(tool_name, canonical), **explicit_args}
        if explicit_args.get("metric") is not None:
            base_args.pop("__default_metric", None)
        for tool_args in _expand_args_for_requirements(tool_name, base_args, canonical):
            fingerprint = (tool_name, repr(sorted(tool_args.items())))
            existing = {(step.tool_name, repr(sorted(step.tool_args.items()))) for step in steps}
            if fingerprint in existing:
                continue
            steps.append(PlanStep(step_id=f"p1-s{len(steps)+1}", plan_version=1, sequence=len(steps)+1,
                                  tool_name=tool_name, tool_args=tool_args, purpose=purpose))
    return steps



def _expand_args_for_requirements(tool_name: str, base_args: dict[str, Any], canonical: CanonicalTaskProfile) -> list[dict[str, Any]]:
    requirements = getattr(canonical, "task_requirements", {}) or {}
    requested_metrics = [str(item) for item in (requirements.get("requested_metrics") or []) if item]
    allowed = set(TOOL_REGISTRY[tool_name].allowed_args)
    if "top_n" in allowed and requirements.get("top_n") is not None and "top_n" not in base_args:
        base_args = {**base_args, "top_n": requirements.get("top_n")}
    explicit_metric = base_args.get("metric") is not None and not base_args.pop("__default_metric", False)
    if "metric" not in allowed or explicit_metric:
        return [base_args]
    expandable: list[str] = []
    if tool_name == "get_entity_period_pair_table":
        expandable = [metric for metric in requested_metrics if metric in {"revenue_amount", "inventory_amount", "inventory_qty"}]
    elif tool_name == "get_entity_trend_comparison":
        expandable = [metric for metric in requested_metrics if metric in {"revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"}]
    elif tool_name == "get_entity_metric_ranking":
        expandable = [metric for metric in requested_metrics if metric in TOOL_REGISTRY[tool_name].supported_metrics and metric not in {"risk_score"}]
    if not expandable:
        return [base_args]
    expanded: list[dict[str, Any]] = []
    for metric in dict.fromkeys(expandable):
        args = dict(base_args)
        args["metric"] = metric
        expanded.append(args)
    return expanded

def _tool_args(tool_name: str, canonical: CanonicalTaskProfile) -> dict[str, Any]:
    allowed = set(TOOL_REGISTRY[tool_name].allowed_args)
    scope, target, parent = canonical.time_scope, canonical.target_entity, canonical.parent_entity
    args: dict[str, Any] = {}
    if "metric" in allowed and canonical.metric:
        period_pair_revenue_tools = {"get_entity_period_pair_comparison", "get_period_pair_metric_comparison"}
        args["metric"] = "revenue" if tool_name in period_pair_revenue_tools and canonical.metric == "revenue_amount" else canonical.metric
        args["__default_metric"] = True
    selected_dimension = target.get("dimension") if target.get("dimension") not in {None, "overall"} else "business_group"
    if "entity_dimension" in allowed:
        args["entity_dimension"] = selected_dimension
    if "dimension" in allowed and "entity_dimension" not in allowed:
        args["dimension"] = selected_dimension
    if "entity_value" in allowed and target.get("value"):
        args["entity_value"] = target["value"]
    for field in ("month", "period_a", "period_b", "start_month", "end_month", "recent_n"):
        if field in allowed and scope.get(field) is not None:
            args[field] = scope[field]
    requirements = getattr(canonical, "task_requirements", {}) or {}
    if "top_n" in allowed and requirements.get("top_n") is not None:
        top_n = int(requirements.get("top_n"))
        if tool_name == "get_anomalies" and (requirements.get("requires_named_selection") or requirements.get("requires_counter_evidence")):
            top_n = max(top_n, 10)
        args["top_n"] = top_n
    if "parent_filter" in allowed and parent.get("value"):
        args["parent_filter"] = {str(parent.get("dimension") or "business_group"): parent["value"]}
    return args


def _execute_tool(assistant: Any, tool_name: str, args: dict[str, Any]) -> Any:
    if tool_name == "get_anomalies":
        call_args = {k: v for k, v in args.items() if k not in {"month"} and v is not None}
        return assistant.toolbox.get_anomalies(filters=QueryFilters(month=args.get("month")), **call_args)
    if tool_name in {"get_inventory_turnover_proxy", "get_root_cause_candidates", "get_yoy_mom_breakdown", "get_contribution_analysis"}:
        return getattr(assistant.toolbox, tool_name)(filters=QueryFilters(month=args.get("month")), **{k: v for k, v in args.items() if k != "month" and v is not None})
    return getattr(assistant.toolbox, tool_name)(**args)
