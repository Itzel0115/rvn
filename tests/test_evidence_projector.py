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
            _rubric([_entity_snapshot("business_group", "事業群")]),
            [],
        )

        self.assertIn("事業群", blocks["headline"])
        self.assertNotIn("各平台", blocks["headline"])
        self.assertIsNotNone(blocks["table"])

    def test_product_line_cross_section_headline_uses_product_line_wording(self) -> None:
        blocks = build_display_blocks_from_roles(
            _profile("cross_section_compare", requires_table=True, time_scope={"month": "2026-02"}),
            _plan(requires_table=True),
            _rubric([_entity_snapshot("product_line_5", "產品線")]),
            [],
        )

        self.assertIn("產品線", blocks["headline"])
        self.assertIn("health_score", blocks["table"]["columns"])

    def test_entity_time_series_headline_preserves_named_entity(self) -> None:
        blocks = build_display_blocks_from_roles(
            _profile("entity_time_series", requires_table=True),
            _plan(requires_table=True),
            _rubric([_series_item("entity_time_series", {"entity_value": "3通路方案", "entity_label": "事業群"})]),
            [],
        )

        self.assertIn("3通路方案", blocks["headline"])
        self.assertIn("2026-01", blocks["headline"])
        self.assertIsNotNone(blocks["table"])

    def test_overall_trend_headline_uses_overall_wording(self) -> None:
        blocks = build_display_blocks_from_roles(
            _profile("overall_trend_analysis", requires_table=True),
            _plan(requires_table=True),
            _rubric([_series_item("overall_time_series", {})]),
            [],
        )

        self.assertIn("整體營收", blocks["headline"])
        self.assertIn("2026-01", blocks["headline"])

    def test_contribution_headline_preserves_period_pair(self) -> None:
        blocks = build_display_blocks_from_roles(
            _profile("contribution_analysis", requires_table=True),
            _plan(requires_table=True),
            _rubric([_contribution_item()]),
            [],
        )

        self.assertIn("2026-01", blocks["headline"])
        self.assertIn("2025-12", blocks["headline"])
        self.assertIn("3通路方案", blocks["headline"])

    def test_key_observations_are_limited(self) -> None:
        blocks = build_display_blocks_from_roles(
            _profile("performance_assessment", polarity="best"),
            _plan(max_key_observations=1),
            _rubric([_entity_snapshot("business_group", "事業群"), _entity_row("次要")]),
            [],
        )

        self.assertLessEqual(len(blocks["key_observations"]), 1)

    def test_unmapped_entity_is_displayed_as_data_quality_limitation(self) -> None:
        unmapped = _entity_snapshot("business_group", "事業群")
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

    def test_phase10f_period_pair_table_projects_headline_and_table(self) -> None:
        blocks = build_display_blocks_from_roles(
            _profile("entity_period_pair_table_lookup", requires_table=True),
            _plan(requires_table=True),
            _rubric([_period_pair_table_item()]),
            [],
        )

        self.assertIn("2025-02", blocks["headline"])
        self.assertIn("2025-03", blocks["headline"])
        self.assertIn("產品線", blocks["headline"])
        self.assertIsNotNone(blocks["table"])
        self.assertIn("change", blocks["table"]["columns"])


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
        details=_row(name, "事業群", "business_group", 0.5, 1, 1, 1),
        display_priority=2,
        reason="test",
    )


def _series_item(evidence_type: str, overrides: dict[str, object]) -> EvidenceItemWithRole:
    details = {
        "metric": "revenue_amount",
        "metric_label": "營收",
        "rows": [
            {"month": "2025-12", "value": 100.0, "mom_change": None, "mom_change_pct": None},
            {"month": "2026-01", "value": 120.0, "mom_change": 20.0, "mom_change_pct": 0.2},
        ],
        "summary": {
            "latest_month": "2026-01",
            "latest_value": 120.0,
            "peak_month": "2026-01",
            "lowest_month": "2025-12",
            "overall_change": 20.0,
            "overall_change_pct": 0.2,
            "direction": "up",
        },
        "limitations": ["歷史描述，不做 forecast。"],
    }
    details.update(overrides)
    return EvidenceItemWithRole(
        role="primary",
        evidence_type=evidence_type,
        source_tool="test",
        summary="series",
        details=details,
        display_priority=1,
        reason="test",
    )


def _contribution_item() -> EvidenceItemWithRole:
    return EvidenceItemWithRole(
        role="primary",
        evidence_type="entity_contribution_analysis",
        source_tool="get_entity_contribution_analysis",
        summary="contribution",
        details={
            "entity_dimension": "business_group",
            "entity_label": "事業群",
            "metric": "revenue_amount",
            "metric_label": "營收",
            "period_a": "2025-12",
            "period_b": "2026-01",
            "rows": [{"entity_value": "3通路方案", "change": 20.0, "contribution_pct": 0.6, "direction": "up"}],
            "summary": {"top_contributor": "3通路方案", "top_change": 20.0},
            "limitations": ["描述性 contribution。"],
        },
        display_priority=1,
        reason="test",
    )


def _period_pair_table_item() -> EvidenceItemWithRole:
    return EvidenceItemWithRole(
        role="primary",
        evidence_type="entity_period_pair_table",
        source_tool="get_entity_period_pair_table",
        summary="period pair table",
        details={
            "period_a": "2025-02",
            "period_b": "2025-03",
            "entity_dimension": "product_line_5",
            "entity_label": "產品線",
            "metric": "inventory_amount",
            "metric_label": "庫存金額",
            "rows": [
                {"entity_value": "Server", "value_a": 100.0, "value_b": 120.0, "change": 20.0, "change_pct": 0.2, "data_presence_flag": "inventory_only"},
            ],
            "summary": {"row_count": 1, "top_entity_period_b": "Server"},
            "limitations": [],
        },
        display_priority=1,
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
