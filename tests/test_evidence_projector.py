from __future__ import annotations

import inspect
import unittest
from types import SimpleNamespace

import answer_contract
from analysis_rubrics import EvidenceItemWithRole, RubricResult
from evidence_projector import build_display_blocks_from_roles


class EvidenceProjectorTest(unittest.TestCase):
    def test_entity_summary_headline_uses_business_group_wording(self) -> None:
        blocks = build_display_blocks_from_roles(
            _profile("latest_month_entity_summary", requires_table=True),
            _plan(requires_table=True),
            _rubric([_entity_snapshot("business_group", "新事業群")]),
            [],
        )

        self.assertIn("新事業群", blocks["headline"])
        self.assertNotIn("各平台", blocks["headline"])
        self.assertIsNotNone(blocks["table"])

    def test_product_line_cross_section_headline_uses_product_line_wording(self) -> None:
        blocks = build_display_blocks_from_roles(
            _profile("cross_section_compare", requires_table=True, time_scope={"month": "2026-02"}),
            _plan(requires_table=True),
            _rubric([_entity_snapshot("product_line_5", "五大產品線")]),
            [],
        )

        self.assertIn("五大產品線", blocks["headline"])
        self.assertIn("health_score", blocks["table"]["columns"])

    def test_key_observations_are_limited(self) -> None:
        blocks = build_display_blocks_from_roles(
            _profile("performance_assessment", polarity="best"),
            _plan(max_key_observations=1),
            _rubric([_entity_snapshot("business_group", "新事業群"), _entity_row("次要")]),
            [],
        )

        self.assertLessEqual(len(blocks["key_observations"]), 1)

    def test_unmapped_entity_is_displayed_as_data_quality_limitation(self) -> None:
        unmapped = _entity_snapshot("business_group", "新事業群")
        rows = unmapped.details["rows"]
        rows[0]["entity_value"] = "未對應"
        rows[0]["platform"] = "未對應"
        rows[0]["health_score"] = 0.9
        rows[1]["health_score"] = 0.2
        unmapped.details["summary"] = {"best_entity": "未對應", "weakest_entity": "B事業群"}

        blocks = build_display_blocks_from_roles(
            _profile("performance_assessment", polarity="best"),
            _plan(),
            _rubric([unmapped]),
            [],
        )

        self.assertNotIn("是 未對應", blocks["headline"])
        self.assertTrue(any("未對應" in item for item in blocks["limitations"]))

    def test_answer_contract_uses_evidence_projector_for_role_based_blocks(self) -> None:
        source = inspect.getsource(answer_contract._build_display_blocks)

        self.assertIn("build_display_blocks_from_roles", source)
        self.assertNotIn("_build_role_based_display_blocks(", source)


def _profile(task_family: str, **overrides) -> SimpleNamespace:
    defaults = {"task_family": task_family, "polarity": None, "time_scope": {}, "requires_table": False}
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _plan(**overrides) -> SimpleNamespace:
    defaults = {"max_key_observations": 3, "requires_table": False}
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _rubric(items: list[EvidenceItemWithRole]) -> RubricResult:
    return RubricResult(
        task_family="test",
        rubric_name="test",
        evidence=items,
        primary_count=sum(1 for item in items if item.role == "primary"),
        supporting_count=sum(1 for item in items if item.role == "supporting"),
        background_count=sum(1 for item in items if item.role == "background"),
        debug_count=sum(1 for item in items if item.role == "debug"),
    )


def _entity_snapshot(dimension: str, label: str) -> EvidenceItemWithRole:
    rows = [
        _row("A事業群" if dimension == "business_group" else "Server", label, dimension, 0.82, 1000, 2000, 0.5),
        _row("B事業群" if dimension == "business_group" else "IOT", label, dimension, 0.22, 500, 3000, 0.1),
    ]
    return EvidenceItemWithRole(
        role="primary",
        evidence_type="entity_performance_snapshot",
        source_tool="get_entity_performance_snapshot",
        summary="entity snapshot",
        details={
            "month": "2026-02",
            "dimension": dimension,
            "entity_dimension": dimension,
            "entity_label": label,
            "rows": rows,
            "summary": {"best_entity": rows[0]["entity_value"], "weakest_entity": rows[1]["entity_value"]},
            "limitations": ["proxy"],
        },
        display_priority=1,
        reason="test",
    )


def _entity_row(name: str) -> EvidenceItemWithRole:
    return EvidenceItemWithRole(
        role="primary",
        evidence_type="entity_performance_row",
        source_tool="get_entity_performance_snapshot",
        summary=name,
        details=_row(name, "新事業群", "business_group", 0.5, 1, 1, 1),
        display_priority=2,
        reason="test",
    )


def _row(name: str, label: str, dimension: str, score: float, revenue: float, inventory: float, ratio: float) -> dict:
    return {
        "month": "2026-02",
        "entity_dimension": dimension,
        "entity_label": label,
        "entity_value": name,
        "platform": name if dimension == "business_group" else None,
        "revenue": revenue,
        "inventory_amount": inventory,
        "inventory_qty": 10,
        "revenue_inventory_amount_ratio": ratio,
        "health_score": score,
        "risk_score": 1 - score,
        "performance_label": "healthy_candidate",
        "primary_strength": "營收相對庫存 proxy 較佳",
        "primary_risk": "資料完整性限制",
    }


if __name__ == "__main__":
    unittest.main()
