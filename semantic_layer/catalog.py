from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from observability import get_recorder
from .models import (DataContractDefinition, DimensionDefinition, EvidenceRequirementDefinition, GlossaryTerm, MetricDefinition, TaskCoverageDefinition)


class SemanticCatalog:
    def __init__(self, root: Path | None = None) -> None:
        definitions = root or Path(__file__).with_name("definitions")
        metrics_payload = _read(definitions / "metrics.json")
        self._version = str(metrics_payload["version"])
        self._metrics = {item["metric_id"]: MetricDefinition(**item) for item in metrics_payload["metrics"]}
        self._dimensions = {item["dimension_id"]: DimensionDefinition(**item) for item in _read(definitions / "dimensions.json")["dimensions"]}
        self._tasks = {item["task_type"]: EvidenceRequirementDefinition(**item) for item in _read(definitions / "task_evidence.json")["tasks"]}
        self._glossary = {item["term_id"]: GlossaryTerm(**item) for item in _read(definitions / "glossary.json")["glossary"]}
        self._data_contracts = {item["dataset_id"]: DataContractDefinition(**item) for item in _read(definitions / "data_contracts.json")["datasets"]}
        self._coverage = {item["task_type"]: TaskCoverageDefinition(**item) for item in _read(definitions / "task_coverage.json")["active_task_types"]}
        from .validation import validate_catalog
        report = validate_catalog(self)
        if report["errors"]:
            raise ValueError("Invalid semantic catalog: " + "; ".join(report["errors"]))

    def get_metric(self, metric_id: str) -> MetricDefinition: return self._metrics[metric_id]
    def get_dimension(self, dimension_id: str) -> DimensionDefinition: return self._dimensions[dimension_id]
    def get_task_requirement(self, task_type: str) -> EvidenceRequirementDefinition | None:
        with get_recorder().span("semantic.resolve_task_requirement", attributes={"revenue_poc.task.type": task_type}): return self._tasks.get(task_type)
    def list_metrics(self) -> list[MetricDefinition]: return list(self._metrics.values())
    def list_dimensions(self) -> list[DimensionDefinition]: return list(self._dimensions.values())
    def list_task_requirements(self) -> list[EvidenceRequirementDefinition]: return list(self._tasks.values())
    def list_glossary(self) -> list[GlossaryTerm]: return list(self._glossary.values())
    def list_data_contracts(self) -> list[DataContractDefinition]: return list(self._data_contracts.values())
    def list_task_coverage(self) -> list[TaskCoverageDefinition]: return list(self._coverage.values())
    def get_task_coverage(self, task_type: str) -> TaskCoverageDefinition | None: return self._coverage.get(task_type)
    def catalog_version(self) -> str: return self._version
    def resolve_metric(self, value: str | None) -> MetricDefinition | None:
        if value is None: return None
        key = str(value).strip().lower()
        with get_recorder().span("semantic.resolve_metric", attributes={"metric_id": key}):
            return next((item for item in self._metrics.values() if item.metric_id == value or key in {a.lower() for a in item.aliases}), None)
    def resolve_dimension(self, value: str | None) -> DimensionDefinition | None:
        if value is None: return None
        key = str(value).strip().lower()
        with get_recorder().span("semantic.resolve_dimension", attributes={"dimension_id": key}):
            return next((item for item in self._dimensions.values() if item.dimension_id == value or key in {a.lower() for a in item.aliases}), None)
    def resolve_glossary(self, value: str | None) -> GlossaryTerm | None:
        if value is None: return None
        key = str(value).strip().lower()
        return next((item for item in self._glossary.values() if item.term_id == value or key in {item.canonical_term.lower(), *(a.lower() for a in item.aliases)}), None)
    def tools_for_requirement(self, requirement_id: str, role: str) -> list[str]:
        item = next((task for task in self._tasks.values() if task.requirement_id == requirement_id), None)
        if not item: return []
        return item.allowed_primary_tools if role == "primary" else item.allowed_supporting_tools
    def evidence_types_for_task(self, task_type: str) -> list[str]:
        task = self.get_task_requirement(task_type)
        return [] if task is None else [*task.required_primary_evidence, *task.required_supporting_evidence, *task.optional_counter_evidence]
    def validate_metric_dimension(self, metric_id: str, dimension_id: str) -> bool:
        with get_recorder().span("semantic.validate_metric_dimension", attributes={"metric_id": metric_id, "dimension_id": dimension_id}): return dimension_id in self.get_metric(metric_id).allowed_dimensions
    def validate_period_mode(self, metric_id: str, supplied_periods: dict[str, Any]) -> bool:
        mode = self.get_metric(metric_id).required_period_mode
        return mode == "none" or (mode == "single_period" and bool(supplied_periods.get("month"))) or mode in {"time_range", "period_pair"}
    def describe_metric(self, metric_id: str) -> dict[str, Any]: return self.get_metric(metric_id).to_dict()
    def describe_task_requirements(self, task_type: str) -> dict[str, Any] | None:
        task = self.get_task_requirement(task_type); return task.to_dict() if task else None
    def to_public_dict(self) -> dict[str, Any]:
        return {"version": self._version, "metrics": [x.to_dict() for x in self.list_metrics()], "dimensions": [x.to_dict() for x in self.list_dimensions()], "tasks": [x.to_dict() for x in self.list_task_requirements()], "glossary": [x.to_dict() for x in self.list_glossary()], "data_contracts": [x.to_dict() for x in self.list_data_contracts()], "task_coverage": [x.to_dict() for x in self.list_task_coverage()]}


def _read(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle: return json.load(handle)


@lru_cache(maxsize=1)
def get_catalog() -> SemanticCatalog: return SemanticCatalog()
