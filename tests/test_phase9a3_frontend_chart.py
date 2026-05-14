from __future__ import annotations

import unittest
from pathlib import Path

from multi_agent import ChartAgent
from tests.support import build_stubbed_assistant


ROOT = Path(__file__).resolve().parents[1]


class Phase9A3FrontendChartTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-phase9a3", use_llm_planner=False, use_llm_rewriter=False)

    def test_summary_wording_uses_business_group_not_platform(self) -> None:
        summary = self.assistant.summarize_project()
        latest = summary["latest_month_analysis"]

        self.assertIn("新事業群", latest)
        self.assertNotIn("平台營收", latest)
        self.assertNotIn("平台庫存", latest)
        self.assertNotIn("未標示平台", latest)

    def test_inventory_business_group_finding_uses_business_group_wording(self) -> None:
        routing = self.assistant._plan_and_route("哪個新事業群庫存金額最高？")
        result = self.assistant.agents["inventory"].execute_tools(["get_platform_ranking(inventory_amount)"], routing)
        text = " ".join(result.key_findings)

        self.assertIn("新事業群", text)
        self.assertNotIn("最高的平台", text)

    def test_chart_agent_selects_business_group_chart(self) -> None:
        self.assertEqual(
            ChartAgent._select_chart_key("請畫最新月份各新事業群營收圖"),
            "business_group_revenue_bar",
        )

    def test_chart_agent_selects_product_line_chart(self) -> None:
        self.assertEqual(
            ChartAgent._select_chart_key("請畫五大產品線 health_score 排名"),
            "product_line_health_score_bar",
        )

    def test_frontend_quick_prompts_include_real_entity_questions(self) -> None:
        quick_prompts = (ROOT / "frontend" / "components" / "chat" / "quick-prompts.js").read_text(encoding="utf-8")

        self.assertIn("請整理最新月份各新事業群的營收與庫存重點", quick_prompts)
        self.assertIn("比較最新月份各五大產品線營收與庫存", quick_prompts)
        self.assertIn("2026年1月以及2026年2月營收有什麼區別？", quick_prompts)


if __name__ == "__main__":
    unittest.main()
