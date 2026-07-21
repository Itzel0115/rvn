from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


SCHEMA_VERSION = "agent-run-state.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AgentRunStatus(str, Enum):
    INITIALIZED = "initialized"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    STOPPED = "stopped"


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    EMPTY = "empty"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    step_id: str
    plan_version: int
    sequence: int
    tool_name: str
    tool_args: dict[str, Any] = field(default_factory=dict)
    purpose: str = "primary evidence"
    status: PlanStepStatus = PlanStepStatus.PENDING
    attempt_count: int = 0
    started_at: str | None = None
    finished_at: str | None = None
    result_summary: dict[str, Any] = field(default_factory=dict)
    error_type: str | None = None
    error_message: str | None = None
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class ToolExecutionRecord:
    execution_id: str
    step_id: str
    tool_name: str
    tool_args: dict[str, Any]
    started_at: str
    finished_at: str | None = None
    status: PlanStepStatus = PlanStepStatus.RUNNING
    result_type: str | None = None
    result_summary: dict[str, Any] = field(default_factory=dict)
    row_count: int | None = None
    is_empty: bool = False
    error_type: str | None = None
    error_message: str | None = None


@dataclass
class ReplanRecord:
    replan_index: int
    trigger: str
    validation_issues: list[str]
    previous_plan_version: int
    new_plan_version: int | None
    added_steps: list[str] = field(default_factory=list)
    removed_or_skipped_steps: list[str] = field(default_factory=list)
    planning_source: str = "deterministic_repair"
    created_at: str = field(default_factory=utc_now)


@dataclass
class AgentRunState:
    request_id: str
    thread_id: str
    question: str
    canonical_task: dict[str, Any]
    routing_summary: dict[str, Any] = field(default_factory=dict)
    answer_plan_summary: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    status: AgentRunStatus = AgentRunStatus.INITIALIZED
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    current_plan_version: int = 1
    steps: list[PlanStep] = field(default_factory=list)
    current_step_id: str | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    validation_issues: list[str] = field(default_factory=list)
    tool_executions: list[ToolExecutionRecord] = field(default_factory=list)
    replanning_history: list[ReplanRecord] = field(default_factory=list)
    step_count: int = 0
    replan_count: int = 0
    max_steps: int = 8
    max_replans: int = 2
    max_attempts_per_step: int = 2
    planning_source: str = "deterministic"
    stop_reason: str | None = None
    final_answer: str | None = None
    final_confidence: str | None = None

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        for step in value["steps"]:
            step["status"] = step["status"].value if isinstance(step["status"], PlanStepStatus) else step["status"]
        for execution in value["tool_executions"]:
            execution["status"] = execution["status"].value if isinstance(execution["status"], PlanStepStatus) else execution["status"]
        return value

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentRunState":
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported agent state schema: {payload.get('schema_version')}")
        data = dict(payload)
        data["status"] = AgentRunStatus(data.get("status", AgentRunStatus.INITIALIZED.value))
        data["steps"] = [PlanStep(**{**step, "status": PlanStepStatus(step.get("status", "pending"))}) for step in data.get("steps", [])]
        data["tool_executions"] = [
            ToolExecutionRecord(**{**item, "status": PlanStepStatus(item.get("status", "pending"))})
            for item in data.get("tool_executions", [])
        ]
        data["replanning_history"] = [ReplanRecord(**item) for item in data.get("replanning_history", [])]
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> "AgentRunState":
        return cls.from_dict(json.loads(payload))

    def concise_trace(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "step_count": self.step_count,
            "replan_count": self.replan_count,
            "planning_source": self.planning_source,
            "stop_reason": self.stop_reason,
            "steps": [{"step_id": s.step_id, "tool_name": s.tool_name, "status": s.status.value} for s in self.steps],
        }
