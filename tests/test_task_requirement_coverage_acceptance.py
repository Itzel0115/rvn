from __future__ import annotations

import os
import unittest
from typing import Any

from ollama_client import OllamaCallResult
from tests.support import build_stubbed_assistant


class ScriptedPlannerLLM:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def generate(self, **kwargs: Any) -> OllamaCallResult:
        return OllamaCallResult(ok=False, text="", data=None, error="unused")

    def generate_json(self, **kwargs: Any) -> OllamaCallResult:
        return OllamaCallResult(ok=True, text="", data=self.payload, error=None)


def _answer(question: str, planner_payload: dict[str, Any]) -> dict[str, Any]:
    previous = os.environ.get("AGENT_RUNTIME_MODE")
    os.environ["AGENT_RUNTIME_MODE"] = "stateful"
    try:
        assistant = build_stubbed_assistant(
            "coverage-acceptance",
            use_llm_planner=True,
            use_llm_rewriter=False,
            llm_client=ScriptedPlannerLLM(planner_payload),
        )
        return assistant.answer(question)
    finally:
        if previous is None:
            os.environ.pop("AGENT_RUNTIME_MODE", None)
        else:
            os.environ["AGENT_RUNTIME_MODE"] = previous


class TaskRequirementCoverageAcceptanceTest(unittest.TestCase):
    def test_multi_angle_management_question_does_not_stop_at_revenue_trend(self) -> None:
        question = "找出最近月份最需要管理層關注的事業群，至少從營收趨勢、庫存金額、庫存數量與異常指標四個角度調查。如果某個工具沒有結果，請改用其他可用證據完成判斷，不要直接停止。"
        response = _answer(question, {
            "task_family": "entity_trend_comparison",
            "question_type": "trend",
            "domains": ["financial"],
            "answer_mode": "trend",
            "requires_limitations": True,
            "tool_calls": [
                {"tool_name": "get_entity_trend_comparison", "args": {"entity_dimension": "business_group", "metric": "revenue_amount"}, "reason": "insufficient single metric candidate"}
            ],
        })
        tools = [step["tool_name"] for step in response["agent_runtime"]["steps"]]
        metrics = [item.get("details", {}).get("metric") for item in response["answer_contract"]["evidence"]]
        self.assertGreaterEqual(tools.count("get_entity_trend_comparison"), 3)
        self.assertIn("get_anomalies", tools)
        self.assertIn("revenue_amount", metrics)
        self.assertIn("inventory_amount", metrics)
        self.assertIn("inventory_qty", metrics)
        self.assertNotIn("llm_plan_rejected", response["summary"])
        self.assertNotEqual(response["agent_runtime"].get("step_count"), 1)

    def test_period_pair_revenue_decline_top_three_cross_checks_inventory_metrics(self) -> None:
        question = "比較 2026 年 1 月與 2 月各事業群的營收變化，找出營收下降最多的前三名，再檢查它們同期的庫存金額和庫存數量是否上升，最後依風險程度排序。"
        response = _answer(question, {
            "task_family": "entity_period_pair_table_lookup",
            "question_type": "overview",
            "domains": ["financial"],
            "answer_mode": "overview",
            "requires_limitations": True,
            "tool_calls": [
                {"tool_name": "get_entity_period_pair_table", "args": {"entity_dimension": "business_group", "metric": "revenue_amount", "period_a": "2026-01", "period_b": "2026-02"}, "reason": "revenue only candidate"}
            ],
        })
        state_tools = response["agent_state_summary"]["steps"]
        metric_steps = [step["tool_args"].get("metric") for step in state_tools if step["tool_name"] == "get_entity_period_pair_table"]
        self.assertEqual(set(metric_steps), {"revenue_amount", "inventory_amount", "inventory_qty"})
        table = response["answer_contract"]["display_blocks"]["table"]
        self.assertIsNotNone(table)
        self.assertIn("inventory_amount_change", table["columns"])
        self.assertIn("inventory_qty_change", table["columns"])
        self.assertTrue(table["rows"])

    def test_risk_scan_with_two_inventory_indicators_uses_cross_check_evidence(self) -> None:
        question = "哪些事業群表面上營收表現不錯，但庫存風險可能正在惡化？請不要只看營收金額，要用至少兩個庫存相關指標交叉判斷。"
        response = _answer(question, {
            "task_family": "risk_scan",
            "question_type": "risk",
            "domains": ["financial"],
            "answer_mode": "risk",
            "requires_limitations": True,
            "tool_calls": [
                {"tool_name": "get_revenue_inventory_relationship", "args": {"entity_dimension": "business_group"}, "reason": "relationship only candidate"}
            ],
        })
        tools = [step["tool_name"] for step in response["agent_runtime"]["steps"]]
        self.assertIn("get_inventory_turnover_proxy", tools)
        self.assertIn("get_entity_trend_comparison", tools)
        evidence_types = [item.get("details", {}).get("evidence_type") for item in response["answer_contract"]["evidence"]]
        self.assertIn("inventory_turnover_proxy", evidence_types)
        self.assertNotIn("N/A 可觀察到", response["summary"])

    def test_turnover_proxy_answer_includes_formula_and_non_comparable_policy(self) -> None:
        question = "請判斷哪些事業群的庫存週轉狀況最差。如果目前沒有正式庫存週轉率或銷貨成本資料，請自行選擇現有資料中最合理的替代指標，但必須清楚說明計算邏輯與限制。"
        response = _answer(question, {
            "task_family": "performance_assessment",
            "question_type": "overview",
            "domains": ["financial"],
            "answer_mode": "briefing",
            "requires_limitations": True,
            "tool_calls": [
                {"tool_name": "get_inventory_turnover_proxy", "args": {"entity_dimension": "business_group"}, "reason": "proxy candidate"}
            ],
        })
        self.assertIn("proxy 公式", response["summary"])
        self.assertIn("分子", response["summary"])
        self.assertIn("分母", response["summary"])
        self.assertIn("non-comparable", response["summary"])
        self.assertNotIn("目前沒有足夠的 primary evidence", response["summary"])

    def test_recent_relationship_table_maps_latest_month_and_inventory_change_fields(self) -> None:
        question = "請找出最近三個月中，營收連續下降但庫存金額連續上升的事業群。先比較所有事業群，再挑出最異常的一個，檢查它的庫存數量、庫存金額與營收變化是否一致，列出支持這個判斷的證據與可能的反證，最後說明資料限制及使用了哪些代理指標。"
        response = _answer(question, {
            "task_family": "metric_relationship_analysis",
            "question_type": "risk",
            "domains": ["financial"],
            "answer_mode": "risk",
            "requires_limitations": True,
            "tool_calls": [
                {"tool_name": "get_revenue_inventory_relationship", "args": {"entity_dimension": "business_group", "recent_n": 3}, "reason": "relationship"},
                {"tool_name": "get_entity_trend_comparison", "args": {"entity_dimension": "business_group", "metric": "revenue_amount", "recent_n": 3}, "reason": "revenue trend"},
                {"tool_name": "get_entity_trend_comparison", "args": {"entity_dimension": "business_group", "metric": "inventory_amount", "recent_n": 3}, "reason": "inventory amount trend"},
            ],
        })
        table = response["answer_contract"]["display_blocks"]["table"]
        self.assertIsNotNone(table)
        self.assertTrue(table["rows"])
        first = table["rows"][0]
        self.assertIsNotNone(first.get("entity_value"))
        self.assertIsNotNone(first.get("latest_month"))
        self.assertIn("inventory_amount_change", first)
        self.assertIn("inventory_qty_change", first)


if __name__ == "__main__":
    unittest.main()
