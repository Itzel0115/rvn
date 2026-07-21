from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION="evaluation.v1"
@dataclass(frozen=True)
class EvalCase:
    case_id: str; suite: str; category: str; description: str; input_type: str; question_or_event: str
    fixture_id: str="synthetic.v1"; execution_mode: str="execution_backed"; execution_adapter: str="assistant"; synthetic_rationale: str | None=None; runtime_mode: str="stateful"; model_mode: str="stub"; random_seed: int=17
    expected_task_type: str | None=None; expected_metric_ids: list[str]=field(default_factory=list); expected_dimension_ids: list[str]=field(default_factory=list); expected_semantic_requirement_id: str | None=None
    required_tools_all: list[str]=field(default_factory=list); required_tools_any: list[str]=field(default_factory=list); allowed_tools: list[str]=field(default_factory=list); forbidden_tools: list[str]=field(default_factory=list)
    required_evidence_types: list[str]=field(default_factory=list); required_primary_evidence: list[str]=field(default_factory=list); allowed_supporting_evidence: list[str]=field(default_factory=list); forbidden_primary_evidence: list[str]=field(default_factory=list)
    expected_statuses: list[str]=field(default_factory=lambda:["completed"]); allowed_stop_reasons: list[str]=field(default_factory=list); forbidden_stop_reasons: list[str]=field(default_factory=list); required_limitations: list[str]=field(default_factory=list); forbidden_claim_patterns: list[str]=field(default_factory=list)
    max_steps: int=8; max_tool_calls: int=8; max_replans: int=2; expected_approval_status: str | None=None; expected_publication_status: str | None=None; security_invariants: list[str]=field(default_factory=list); tags: list[str]=field(default_factory=list); dataset_version: str="v1"; schema_version: str=SCHEMA_VERSION
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls,data:dict[str,Any]): return cls(**data)

@dataclass(frozen=True)
class GraderResult:
    grader_id: str; grader_version: str; score: float; passed: bool; severity: str; explanation: str; evidence_references: list[str]=field(default_factory=list); failure_categories: list[str]=field(default_factory=list)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraderResult": return cls(**data)

@dataclass
class EvalCaseResult:
    case_id: str; trace_id: str | None; execution_status: str; grader_results: list[GraderResult]; hard_invariants_passed: bool; overall_score: float; failure_categories: list[str]; execution_mode: str="synthetic_trajectory"; duration_ms: float=0; tool_call_count: int=0; replan_count: int=0; artifact_references: list[str]=field(default_factory=list)
    suite: str=""; task_type: str | None=None; execution_adapter: str | None=None; actual_execution_mode: str | None=None; adapter_status: str | None=None; actual_execution_attempted: bool=False; actual_execution_completed: bool=False; actual_execution_passed: bool=False; stop_reason: str | None=None; security_outcome: str | None=None
    def to_dict(self): value=asdict(self); value["grader_results"]=[item.to_dict() for item in self.grader_results]; return value
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvalCaseResult":
        value=dict(data); value["grader_results"]=[item if isinstance(item, GraderResult) else GraderResult.from_dict(item) for item in value.get("grader_results", [])]; return cls(**value)
