"""Small adapters that project catalog requirements into existing contracts."""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from answer_plan import AnswerPlan
from .catalog import get_catalog
from observability import get_recorder

def enrich_answer_plan(plan: AnswerPlan, canonical_task: Any) -> AnswerPlan:
    """Attach concise requirement references; never copy the catalog into a response."""
    with get_recorder().span("semantic.answer_plan.enrich", attributes={"revenue_poc.task.type": str(getattr(canonical_task, "task_family", "") or "")}):
        requirement = get_catalog().get_task_requirement(str(getattr(canonical_task, "task_family", "") or ""))
    if requirement is None:
        return plan
    return replace(plan, semantic_requirement_id=requirement.requirement_id, required_primary_evidence=list(requirement.required_primary_evidence), required_supporting_evidence=list(requirement.required_supporting_evidence), optional_counter_evidence=list(requirement.optional_counter_evidence), required_limitations=list(requirement.required_limitations), partial_completion_rule=dict(requirement.partial_completion_rule))
