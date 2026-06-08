from __future__ import annotations

import unittest

from scripts.demo_answer_review import DEMO_REVIEW_QUESTIONS
from tests.support import build_stubbed_assistant


class Phase9BDemoReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-phase9b", use_llm_planner=False, use_llm_rewriter=False)

    def test_demo_answer_review_has_twenty_questions(self) -> None:
        self.assertGreaterEqual(len(DEMO_REVIEW_QUESTIONS), 20)

    def test_performance_weakness_headline_uses_business_group_wording(self) -> None:
        response = self.assistant.answer("請分析哪個事業群表現較差")
        display = response["answer_contract"]["display_blocks"]

        self.assertIn("事業群", display["headline"])
        self.assertNotIn("平台", display["headline"])
        self.assertLessEqual(len(display.get("key_observations") or []), 3)

    def test_cross_section_table_columns_do_not_use_platform_label(self) -> None:
        response = self.assistant.answer("比較最新月份各產品線營收與庫存")
        table = response["answer_contract"]["display_blocks"].get("table") or {}
        columns = [str(column) for column in table.get("columns") or []]

        self.assertNotIn("platform", [column.lower() for column in columns])
        self.assertNotIn("平台", "".join(columns))

    def test_chart_titles_do_not_use_platform_wording(self) -> None:
        response = self.assistant.answer("請畫最新月份各事業群營收圖")
        charts = [
            evidence
            for result in response.get("domain_results") or []
            for evidence in result.get("evidence") or []
            if isinstance(evidence, dict) and evidence.get("chart_key")
        ]

        self.assertTrue(charts)
        for chart in charts:
            visible_chart_text = " ".join(
                str(chart.get(key) or "")
                for key in ("title", "x_label", "y_label")
            )
            self.assertNotIn("平台", visible_chart_text)


if __name__ == "__main__":
    unittest.main()
