from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AnswerPolicy:
    style: str
    max_key_observations: int
    show_background_findings: bool
    show_agent_debug: bool
    primary_evidence_types: list[str] = field(default_factory=list)
    secondary_evidence_types: list[str] = field(default_factory=list)


def get_answer_policy(routing: Any, question: str) -> AnswerPolicy:
    answer_strategy = getattr(routing, "answer_strategy", None) or getattr(routing, "question_type", "query")
    question_type = getattr(routing, "question_type", "query")
    style_key = answer_strategy or question_type

    if style_key == "performance_weakness":
        return AnswerPolicy(
            style="conclusion_first",
            max_key_observations=3,
            show_background_findings=False,
            show_agent_debug=False,
            primary_evidence_types=["inventory_turnover_proxy", "platform_ratio", "anomaly"],
            secondary_evidence_types=["root_cause_candidate", "contribution"],
        )

    if style_key == "diagnosis":
        return AnswerPolicy(
            style="conclusion_first",
            max_key_observations=4,
            show_background_findings=False,
            show_agent_debug=False,
            primary_evidence_types=["root_cause_candidate", "anomaly", "inventory_turnover_proxy", "contribution"],
            secondary_evidence_types=["yoy_mom", "platform_ratio"],
        )

    if style_key == "ranking":
        return AnswerPolicy(
            style="conclusion_first",
            max_key_observations=2,
            show_background_findings=False,
            show_agent_debug=False,
            primary_evidence_types=["platform_ranking", "group_ranking", "inventory_turnover_proxy"],
            secondary_evidence_types=["yoy_mom"],
        )

    if style_key == "trend":
        return AnswerPolicy(
            style="evidence_first",
            max_key_observations=3,
            show_background_findings=False,
            show_agent_debug=False,
            primary_evidence_types=["yoy_mom", "contribution"],
            secondary_evidence_types=["anomaly", "inventory_turnover_proxy"],
        )

    if style_key == "overview":
        return AnswerPolicy(
            style="summary",
            max_key_observations=3,
            show_background_findings=False,
            show_agent_debug=False,
            primary_evidence_types=[],
            secondary_evidence_types=[],
        )

    if style_key == "unsupported":
        return AnswerPolicy(
            style="refusal",
            max_key_observations=1,
            show_background_findings=False,
            show_agent_debug=False,
            primary_evidence_types=[],
            secondary_evidence_types=[],
        )

    return AnswerPolicy(
        style="evidence_first",
        max_key_observations=3,
        show_background_findings=False,
        show_agent_debug=False,
        primary_evidence_types=["anomaly", "inventory_turnover_proxy", "yoy_mom"],
        secondary_evidence_types=["contribution", "platform_ratio"],
    )
