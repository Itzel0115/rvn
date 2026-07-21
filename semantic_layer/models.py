from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str; display_name: str; description: str; metric_kind: str; unit: str; value_type: str
    grain: str; formula_expression: str; formula_description: str; calculation_owner: str
    source_fields: list[str]; allowed_dimensions: list[str]; required_dimensions: list[str]
    required_period_mode: str; aliases: list[str]; is_proxy: bool; proxy_for: str | None
    limitations: list[str]; null_semantics: str; directionality: str; supported_operations: list[str]
    primary_tools: list[str]; supporting_tools: list[str]; evidence_types: list[str]; status: str = "active"; version: str = "1"
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class DimensionDefinition:
    dimension_id: str; display_name: str; description: str; aliases: list[str]; source_fields: list[str]
    grain: str; hierarchy: list[str]; parent_dimension: str | None; allowed_metrics: list[str]
    allowed_operations: list[str]; unknown_value_policy: str; status: str = "active"
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class EvidenceRequirementDefinition:
    requirement_id: str; task_type: str; description: str; required_primary_evidence: list[str]
    required_supporting_evidence: list[str]; optional_counter_evidence: list[str]; required_metrics: list[str]
    required_dimensions: list[str]; required_period_mode: str; minimum_rows: int; minimum_periods: int
    completion_rule: dict[str, Any]; partial_completion_rule: dict[str, Any]; allowed_primary_tools: list[str]
    allowed_supporting_tools: list[str]; forbidden_as_primary: list[str]; required_limitations: list[str]
    causal_claim_policy: str; empty_result_policy: str; status: str = "active"
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class GlossaryTerm:
    term_id: str; canonical_term: str; display_name: str; definition: str; aliases: list[str]
    related_metrics: list[str]; related_dimensions: list[str]; ambiguity_notes: str; status: str = "active"
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class DataContractDefinition:
    dataset_id: str; display_name: str; required_columns: list[str]; optional_columns: list[str]
    period_field: str; entity_fields: list[str]; numeric_fields: list[str]; refresh_semantics: str
    freshness_policy: str; available_period_semantics: str; known_limitations: list[str]; sensitive_fields: list[str]; exposable_via_mcp: bool
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class TaskCoverageDefinition:
    task_type: str; runtime_path: str; coverage_status: str; required_limitation: str
    def to_dict(self) -> dict[str, Any]: return asdict(self)
