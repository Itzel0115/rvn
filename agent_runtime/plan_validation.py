from __future__ import annotations

from typing import Any

from llm_planner import PlannedToolCall, ToolPlan
from plan_validator import PlanValidator

from .models import PlanStep


def validate_stateful_steps(canonical: Any, steps: list[PlanStep], answer_plan: Any) -> dict[str, Any]:
    """Use the existing validator and add runtime-only evidence-role constraints."""
    plan = ToolPlan(
        task_family=canonical.task_family,
        question_type="overview",
        domains=["financial"],
        tools=[PlannedToolCall(step.tool_name, step.tool_args, step.purpose) for step in steps],
        answer_mode=canonical.answer_mode,
        requires_limitations=True,
    )
    result = PlanValidator().validate(canonical, plan, deterministic_answer_plan=answer_plan)
    violations = list(result.get("violations") or [])
    if canonical.task_family == "metric_relationship_analysis":
        for step in steps:
            if step.tool_name == "get_entity_performance_snapshot" and step.purpose.startswith("primary"):
                violations.append("relationship_snapshot_must_be_supporting")
    return {
        **result,
        "valid": not violations,
        "fallback_to_deterministic": bool(violations),
        "reason": "valid" if not violations else violations[0],
        "violations": list(dict.fromkeys(violations)),
    }
