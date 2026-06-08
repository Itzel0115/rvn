from __future__ import annotations

import unittest

from analysis_rubrics import assign_evidence_roles
from answer_contract import build_answer_contract
from answer_plan import build_answer_plan
from multi_agent import DomainResult
from task_profile import build_task_profile
from tests.support import build_stubbed_assistant


class AnalysisRubricsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-analysis-rubrics")

    def test_cross_section_compare_does_not_make_contribution_primary(self) -> None:
        routing = self.assistant._plan_and_route("\u6bd4\u8f03 8 \u6708\u5404\u5e73\u53f0\u71df\u6536\u8207\u5eab\u5b58")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_platform_ratio(), _contribution()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertEqual(roles["platform_ratio"], "primary")
        self.assertEqual(roles["contribution_analysis"], "background")

    def test_performance_assessment_does_not_make_inventory_amount_ranking_primary(self) -> None:
        routing = self.assistant._plan_and_route("\u8acb\u5206\u6790\u54ea\u500b\u5e73\u53f0\u8868\u73fe\u8f03\u5dee")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_platform_ratio(), _inventory_amount_ranking()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertIn(roles["platform_ratio"], {"primary", "supporting"})
        self.assertEqual(roles["platform_ranking"], "background")

    def test_performance_assessment_makes_scorecard_primary(self) -> None:
        routing = self.assistant._plan_and_route("\u8acb\u5206\u6790\u54ea\u500b\u5e73\u53f0\u8868\u73fe\u8f03\u4f73")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_performance_snapshot(), _platform_ratio()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertEqual(roles["platform_performance_snapshot"], "primary")
        self.assertIn(roles["platform_ratio"], {"primary", "supporting"})

    def test_cross_section_compare_makes_scorecard_primary(self) -> None:
        routing = self.assistant._plan_and_route("\u6bd4\u8f03 8 \u6708\u5404\u5e73\u53f0\u71df\u6536\u8207\u5eab\u5b58")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_performance_snapshot(), _contribution()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertEqual(roles["platform_performance_snapshot"], "primary")
        self.assertEqual(roles["contribution_analysis"], "background")

    def test_entity_cross_section_comparison_is_primary(self) -> None:
        routing = self.assistant._plan_and_route("比較最新月份各產品線營收與庫存")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_entity_cross_section_comparison()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertEqual(roles["entity_cross_section_comparison"], "primary")

    def test_entity_period_pair_comparison_is_primary(self) -> None:
        routing = self.assistant._plan_and_route("2026年1月以及2026年2月營收有什麼區別？")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_entity_period_pair_comparison()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertEqual(roles["entity_period_pair_comparison"], "primary")

    def test_entity_time_series_is_primary(self) -> None:
        routing = self.assistant._plan_and_route("比較 3通路方案 各月營收")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_entity_time_series()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertEqual(roles["entity_time_series"], "primary")

    def test_overall_time_series_is_primary(self) -> None:
        routing = self.assistant._plan_and_route("總體營收趨勢如何？")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_overall_time_series()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertEqual(roles["overall_time_series"], "primary")

    def test_metric_relationship_and_contribution_are_primary_for_new_families(self) -> None:
        relationship_routing = self.assistant._plan_and_route("有沒有營收下降但庫存上升的事業群？")
        relationship_profile = build_task_profile(relationship_routing.question, relationship_routing)
        relationship_plan = build_answer_plan(relationship_profile, relationship_routing)
        relationship_result = assign_evidence_roles(
            relationship_profile,
            relationship_plan,
            [_domain_result([_metric_relationship(), _platform_ratio()])],
        )
        relationship_roles = {item.evidence_type: item.role for item in relationship_result.evidence}
        self.assertEqual(relationship_roles["metric_relationship"], "primary")

        contribution_routing = self.assistant._plan_and_route("2026-01 比 2025-12 成長主要來自哪個事業群？")
        contribution_profile = build_task_profile(contribution_routing.question, contribution_routing)
        contribution_plan = build_answer_plan(contribution_profile, contribution_routing)
        contribution_result = assign_evidence_roles(
            contribution_profile,
            contribution_plan,
            [_domain_result([_entity_contribution_analysis()])],
        )
        contribution_roles = {item.evidence_type: item.role for item in contribution_result.evidence}
        self.assertEqual(contribution_roles["entity_contribution_analysis"], "primary")

    def test_entity_metric_ranking_is_primary_for_ranking(self) -> None:
        routing = self.assistant._plan_and_route("最新月份營收最高的事業群是誰？")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_entity_metric_ranking(), _inventory_amount_ranking()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertEqual(roles["entity_metric_ranking"], "primary")
        self.assertEqual(roles["platform_ranking"], "background")

    def test_time_compare_makes_contribution_primary(self) -> None:
        routing = self.assistant._plan_and_route("2026-01 比 2025-12 成長主要來自哪個事業群？")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_entity_contribution_analysis()])])

        self.assertEqual(result.evidence[0].evidence_type, "entity_contribution_analysis")
        self.assertEqual(result.evidence[0].role, "primary")

    def test_diagnosis_makes_root_cause_candidates_primary(self) -> None:
        routing = self.assistant._plan_and_route("Why is revenue down?")
        profile = build_task_profile(routing.question, routing)
        plan = build_answer_plan(profile, routing)
        result = assign_evidence_roles(profile, plan, [_domain_result([_root_cause_candidate(), _platform_ratio()])])

        roles = {item.evidence_type: item.role for item in result.evidence}
        self.assertEqual(roles["root_cause_candidate"], "primary")
        self.assertEqual(roles["platform_ratio"], "supporting")

    def test_background_evidence_does_not_enter_display_blocks(self) -> None:
        question = "\u6bd4\u8f03 8 \u6708\u5404\u5e73\u53f0\u71df\u6536\u8207\u5eab\u5b58"
        routing = self.assistant._plan_and_route(question)
        profile = build_task_profile(question, routing)
        plan = build_answer_plan(profile, routing)
        domain_results = [_domain_result([_platform_ratio(), _contribution()])]

        contract = build_answer_contract(
            request_id="test-rubric-contract",
            question=question,
            routing=routing,
            domain_results=domain_results,
            toolbox=self.assistant.toolbox,
            task_profile=profile,
            answer_plan=plan,
        )

        observations = " ".join(contract["display_blocks"]["key_observations"])
        self.assertNotIn("\u4e3b\u8981\u8ca2\u737b\u8005", observations)
        self.assertLessEqual(len(contract["display_blocks"]["key_observations"]), plan.max_key_observations)
        role_map = {item["evidence_type"]: item["role"] for item in contract["role_based_evidence"]["evidence"]}
        self.assertEqual(role_map["contribution_analysis"], "background")


def _domain_result(evidence: list[dict]) -> DomainResult:
    return DomainResult(
        domain="financial",
        status="success",
        task="test",
        key_findings=["debug finding should not be flattened"],
        evidence=evidence,
        warnings=[],
        confidence="high",
        used_tools=[],
    )


def _platform_ratio() -> dict:
    return {
        "month": "2024-08",
        "platform": "GG-02",
        "group_code": "2",
        "revenue": 730.0,
        "inventory_amount": 1360.0,
        "inventory_qty": 290,
        "revenue_inventory_amount_ratio": 0.5367,
    }


def _contribution() -> dict:
    return {
        "month": "2024-08",
        "previous_month": "2024-07",
        "metric": "revenue",
        "contributors": [{"name": "\u96f2\u7aef\u670d\u52d9", "change": 195.0}],
    }


def _inventory_amount_ranking() -> dict:
    return {
        "dimension": "platform",
        "platform": "GG-01",
        "metric": "inventory_amount",
        "value_text": "8,030.00",
    }


def _root_cause_candidate() -> dict:
    return {
        "root_cause_available": False,
        "metric": "revenue",
        "candidates": [{"candidate_type": "platform_contribution", "title": "GG-02 contribution pressure"}],
    }


def _performance_snapshot() -> dict:
    return {
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
                "primary_strength": "營收相對庫存效率 proxy 較高",
                "primary_risk": "目前 scorecard 未顯示主要風險訊號",
            }
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
    }


def _entity_cross_section_comparison() -> dict:
    return {
        "evidence_type": "entity_cross_section_comparison",
        "source_tool": "get_entity_cross_section_comparison",
        "month": "2026-02",
        "dimension": "product_line_5",
        "entity_dimension": "product_line_5",
        "entity_label": "產品線",
        "rows": [
            {
                "month": "2026-02",
                "entity_value": "Server",
                "entity_dimension": "product_line_5",
                "entity_label": "產品線",
                "revenue_amount": 100.0,
                "inventory_amount": 200.0,
                "inventory_qty": 10.0,
                "revenue_inventory_amount_ratio": 0.5,
                "health_score": 0.4,
                "risk_score": 0.6,
                "performance_label": "watch",
            }
        ],
        "summary": {"top_revenue_entity": "Server", "top_inventory_entity": "Server"},
    }


def _entity_period_pair_comparison() -> dict:
    return {
        "evidence_type": "entity_period_pair_comparison",
        "source_tool": "get_entity_period_pair_comparison",
        "metric": "revenue",
        "period_a": "2026-01",
        "period_b": "2026-02",
        "dimension": "business_group",
        "entity_dimension": "business_group",
        "entity_label": "事業群",
        "overall": {"value_a": 100.0, "value_b": 80.0, "change": -20.0, "change_pct": -0.2},
        "breakdown": [],
    }


def _entity_metric_ranking() -> dict:
    return {
        "evidence_type": "entity_metric_ranking",
        "source_tool": "get_entity_metric_ranking",
        "month": "2026-02",
        "entity_dimension": "business_group",
        "entity_label": "事業群",
        "metric": "revenue_amount",
        "metric_label": "營收",
        "sort_direction": "descending",
        "top_entity": "1網通+技鋼",
        "top_value": 100.0,
        "rows": [
            {
                "rank": 1,
                "entity_value": "1網通+技鋼",
                "value": 100.0,
                "health_score": 0.8,
                "data_presence_flag": "both",
            }
        ],
    }


def _entity_time_series() -> dict:
    return {
        "evidence_type": "entity_time_series",
        "source_tool": "get_entity_time_series",
        "entity_dimension": "business_group",
        "entity_label": "事業群",
        "entity_value": "3通路方案",
        "metric": "revenue_amount",
        "metric_label": "營收",
        "rows": [
            {"month": "2025-12", "value": 80.0, "mom_change": 5.0, "mom_change_pct": 0.0667},
            {"month": "2026-01", "value": 100.0, "mom_change": 20.0, "mom_change_pct": 0.25},
        ],
        "summary": {"latest_month": "2026-01", "latest_value": 100.0, "direction": "up"},
    }


def _overall_time_series() -> dict:
    return {
        "evidence_type": "overall_time_series",
        "source_tool": "get_overall_time_series",
        "metric": "revenue_amount",
        "metric_label": "營收",
        "rows": [
            {"month": "2025-12", "value": 100.0, "mom_change": None, "mom_change_pct": None},
            {"month": "2026-01", "value": 110.0, "mom_change": 10.0, "mom_change_pct": 0.1},
        ],
        "summary": {"latest_month": "2026-01", "latest_value": 110.0, "direction": "up"},
    }


def _metric_relationship() -> dict:
    return {
        "evidence_type": "metric_relationship",
        "source_tool": "get_revenue_inventory_relationship",
        "entity_dimension": "business_group",
        "entity_label": "事業群",
        "rows": [
            {
                "entity_value": "2技宸",
                "month": "2026-02",
                "previous_month": "2026-01",
                "relationship_label": "revenue_down_inventory_up",
            }
        ],
        "summary": {"relationship_counts": {"revenue_down_inventory_up": 1}},
    }


def _entity_contribution_analysis() -> dict:
    return {
        "evidence_type": "entity_contribution_analysis",
        "source_tool": "get_entity_contribution_analysis",
        "entity_dimension": "business_group",
        "entity_label": "事業群",
        "metric": "revenue_amount",
        "metric_label": "營收",
        "period_a": "2025-12",
        "period_b": "2026-01",
        "rows": [
            {"entity_value": "3通路方案", "change": 20.0, "contribution_pct": 0.6, "direction": "up"},
        ],
        "summary": {"top_contributor": "3通路方案", "top_change": 20.0},
    }


if __name__ == "__main__":
    unittest.main()
