from __future__ import annotations

import inspect
import unittest
from types import SimpleNamespace

import answer_contract
from analysis_rubrics import EvidenceItemWithRole, RubricResult
from evidence_projector import build_display_blocks_from_roles


class EvidenceProjectorTest(unittest.TestCase):
    def test_cross_section_compare_headline_contains_specific_platform_conclusion(self) -> None:
        profile = _profile("cross_section_compare", requires_table=True, time_scope={"month": "2024-08"})
        plan = _plan(max_key_observations=3, requires_table=True)
        blocks = build_display_blocks_from_roles(
            profile,
            plan,
            _rubric(
                [
                    _ratio("GG-01", revenue=900.0, inventory_amount=3000.0, ratio=0.30),
                    _ratio("GG-02", revenue=1200.0, inventory_amount=2500.0, ratio=0.48),
                    _ratio("GG-03", revenue=700.0, inventory_amount=5000.0, ratio=0.14),
                ]
            ),
            [],
        )

        self.assertIn("GG-02", blocks["headline"])
        self.assertIn("GG-03", blocks["headline"])
        self.assertIn("\u71df\u6536\u898f\u6a21\u8f03\u9ad8", blocks["headline"])
        self.assertNotIn("\u9019\u984c\u61c9\u89e3\u8b80\u70ba", blocks["headline"])
        self.assertIsNotNone(blocks["table"])

    def test_cross_section_compare_does_not_use_background_contribution_headline(self) -> None:
        profile = _profile("cross_section_compare", requires_table=True, time_scope={"month": "2024-08"})
        plan = _plan()
        blocks = build_display_blocks_from_roles(
            profile,
            plan,
            _rubric(
                [
                    _ratio("GG-01", revenue=900.0, inventory_amount=3000.0, ratio=0.30),
                    _contribution(role="background"),
                ]
            ),
            [],
        )

        self.assertNotIn("\u4e3b\u8981\u7531", blocks["headline"])
        self.assertNotIn("\u8ca2\u737b", blocks["headline"])
        self.assertNotIn("\u4e3b\u8981\u8ca2\u737b\u8005", " ".join(blocks["key_observations"]))

    def test_performance_best_is_conservative_when_only_weak_evidence_exists(self) -> None:
        profile = _profile("performance_assessment", polarity="best")
        plan = _plan()
        blocks = build_display_blocks_from_roles(
            profile,
            plan,
            _rubric([_ratio("GG-02", ratio=0.54, source_tool="get_inventory_turnover_proxy")]),
            [],
        )

        self.assertIn("\u5c1a\u4e0d\u8db3\u4ee5\u660e\u78ba\u5224\u5b9a\u6700\u4f73\u5e73\u53f0", blocks["headline"])
        self.assertIn("GG-02", blocks["headline"])
        self.assertNotIn("\u8f03\u4f73\u7684\u5e73\u53f0\u5019\u9078\u662f GG-02", blocks["headline"])

    def test_performance_worst_points_to_lowest_proxy_platform(self) -> None:
        profile = _profile("performance_assessment", polarity="worst")
        plan = _plan()
        blocks = build_display_blocks_from_roles(
            profile,
            plan,
            _rubric([_ratio("GG-01", ratio=0.90), _ratio("GG-02", ratio=0.54)]),
            [],
        )

        self.assertIn("GG-02", blocks["headline"])
        self.assertIn("proxy \u504f\u5f31", blocks["headline"])

    def test_performance_best_uses_scorecard_when_available(self) -> None:
        profile = _profile("performance_assessment", polarity="best")
        plan = _plan()
        blocks = build_display_blocks_from_roles(profile, plan, _rubric([_snapshot()]), [])

        self.assertIn("GG-05", blocks["headline"])
        self.assertIn("health_score", blocks["headline"])
        self.assertNotIn("\u5c1a\u4e0d\u8db3\u4ee5\u660e\u78ba\u5224\u5b9a", blocks["headline"])

    def test_performance_worst_uses_scorecard_when_available(self) -> None:
        profile = _profile("performance_assessment", polarity="worst")
        plan = _plan()
        blocks = build_display_blocks_from_roles(profile, plan, _rubric([_snapshot()]), [])

        self.assertIn("GG-02", blocks["headline"])
        self.assertIn("health_score", blocks["headline"])

    def test_scorecard_can_project_display_table(self) -> None:
        profile = _profile("cross_section_compare", requires_table=True, time_scope={"month": "2024-08"})
        plan = _plan(requires_table=True)
        blocks = build_display_blocks_from_roles(profile, plan, _rubric([_snapshot()]), [])

        self.assertIsNotNone(blocks["table"])
        self.assertIn("health_score", blocks["table"]["columns"])
        self.assertTrue(blocks["table"]["rows"])

    def test_key_observations_are_limited_and_background_is_not_projected(self) -> None:
        profile = _profile("time_compare")
        plan = _plan(max_key_observations=1)
        blocks = build_display_blocks_from_roles(
            profile,
            plan,
            _rubric([_contribution(), _trend(), _ratio("GG-09", role="background", ratio=0.10)]),
            [],
        )

        self.assertLessEqual(len(blocks["key_observations"]), 1)
        self.assertNotIn("GG-09", " ".join(blocks["key_observations"]))

    def test_answer_contract_uses_evidence_projector_for_role_based_blocks(self) -> None:
        source = inspect.getsource(answer_contract._build_display_blocks)

        self.assertIn("build_display_blocks_from_roles", source)
        self.assertNotIn("_build_role_based_display_blocks(", source)


def _profile(task_family: str, **overrides) -> SimpleNamespace:
    defaults = {
        "task_family": task_family,
        "polarity": None,
        "time_scope": {},
        "requires_table": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _plan(**overrides) -> SimpleNamespace:
    defaults = {
        "max_key_observations": 3,
        "requires_table": False,
    }
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


def _ratio(
    platform: str,
    *,
    role: str = "primary",
    revenue: float = 730.0,
    inventory_amount: float = 1360.0,
    inventory_qty: float = 290.0,
    ratio: float = 0.54,
    source_tool: str = "get_platform_ratios",
) -> EvidenceItemWithRole:
    return EvidenceItemWithRole(
        role=role,
        evidence_type="platform_ratio",
        source_tool=source_tool,
        summary=f"{platform} ratio",
        details={
            "month": "2024-08",
            "platform": platform,
            "revenue": revenue,
            "inventory_amount": inventory_amount,
            "inventory_qty": inventory_qty,
            "revenue_inventory_amount_ratio": ratio,
        },
        display_priority=1,
        reason="test",
    )


def _contribution(role: str = "primary") -> EvidenceItemWithRole:
    return EvidenceItemWithRole(
        role=role,
        evidence_type="contribution_analysis",
        source_tool="get_contribution_analysis(revenue)",
        summary="contribution",
        details={
            "month": "2024-08",
            "previous_month": "2024-07",
            "metric": "revenue",
            "contributors": [{"name": "\u96f2\u7aef\u670d\u52d9", "change": 195.0}],
        },
        display_priority=1,
        reason="test",
    )


def _trend() -> EvidenceItemWithRole:
    return EvidenceItemWithRole(
        role="primary",
        evidence_type="yoy_mom_breakdown",
        source_tool="get_yoy_mom_breakdown(revenue)",
        summary="trend",
        details={"month": "2024-08", "previous_month": "2024-07", "metric": "revenue", "mom_change": 215.0},
        display_priority=2,
        reason="test",
    )


def _snapshot() -> EvidenceItemWithRole:
    return EvidenceItemWithRole(
        role="primary",
        evidence_type="platform_performance_snapshot",
        source_tool="get_platform_performance_snapshot",
        summary="snapshot",
        details={
            "month": "2024-08",
            "dimension": "platform",
            "rows": [
                {
                    "month": "2024-08",
                    "platform": "GG-05",
                    "revenue": 1385.0,
                    "inventory_amount": 980.0,
                    "inventory_qty": 200,
                    "revenue_inventory_amount_ratio": 1.41,
                    "health_score": 0.82,
                    "risk_score": 0.18,
                    "performance_label": "healthy_candidate",
                    "primary_strength": "\u71df\u6536\u76f8\u5c0d\u5eab\u5b58\u6548\u7387 proxy \u8f03\u9ad8",
                    "primary_risk": "\u76ee\u524d scorecard \u672a\u986f\u793a\u4e3b\u8981\u98a8\u96aa\u8a0a\u865f",
                },
                {
                    "month": "2024-08",
                    "platform": "GG-02",
                    "revenue": 730.0,
                    "inventory_amount": 1360.0,
                    "inventory_qty": 290,
                    "revenue_inventory_amount_ratio": 0.54,
                    "health_score": 0.22,
                    "risk_score": 0.78,
                    "performance_label": "risk_candidate",
                    "primary_strength": "\u7d9c\u5408\u5206\u6578\u4f86\u81ea\u71df\u6536\u898f\u6a21\u3001\u52d5\u80fd\u3001\u6548\u7387 proxy \u8207\u7570\u5e38\u8a0a\u865f",
                    "primary_risk": "\u71df\u6536\u76f8\u5c0d\u5eab\u5b58\u6548\u7387 proxy \u6392\u540d\u504f\u5f8c",
                },
            ],
            "summary": {
                "best_platform": "GG-05",
                "weakest_platform": "GG-02",
                "top_revenue_platform": "GG-05",
                "top_inventory_platform": "GG-02",
                "highest_efficiency_platform": "GG-05",
                "lowest_efficiency_platform": "GG-02",
            },
            "rubric": {},
            "limitations": [],
        },
        display_priority=1,
        reason="test",
    )


if __name__ == "__main__":
    unittest.main()
