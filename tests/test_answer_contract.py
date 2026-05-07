from __future__ import annotations

import unittest

from tests.support import build_stubbed_assistant


class AnswerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-answer-contract")

    def test_ask_response_includes_evidence_first_contract(self) -> None:
        response = self.assistant.answer("Which business group has the highest revenue?")
        contract = response["answer_contract"]

        self.assertEqual(
            set(contract.keys()),
            {
                "request_id",
                "answer_type",
                "answer",
                "evidence",
                "tools_used",
                "data_scope",
                "limitations",
                "suggested_followups",
                "display_blocks",
                "role_based_evidence",
                "task_profile",
                "answer_plan",
            },
        )
        self.assertEqual(contract["answer_type"], "ranking")
        self.assertIn("18,810.00", contract["answer"])
        self.assertIn("get_top_groups(revenue)", contract["tools_used"])
        self.assertTrue(contract["evidence"])
        self.assertTrue(contract["limitations"])

    def test_summary_is_rendered_from_contract(self) -> None:
        response = self.assistant.answer("What is the revenue trend?")
        summary = response["summary"]

        self.assertIn("Evidence:", summary)
        self.assertIn("Tools used:", summary)
        self.assertIn("Limitations:", summary)

    def test_unsupported_question_returns_rejection_contract(self) -> None:
        response = self.assistant.answer("What is the gross margin trend?")
        contract = response["answer_contract"]

        self.assertEqual(contract["answer_type"], "unsupported")
        self.assertIn("gross margin", contract["answer"])
        self.assertEqual(contract["tools_used"], [])
        self.assertEqual(contract["evidence"], [])
        self.assertTrue(any("gross margin" in item for item in contract["limitations"]))

    def test_data_quality_question_returns_structured_contract(self) -> None:
        response = self.assistant.answer("What data coverage do we have by month?")
        contract = response["answer_contract"]

        self.assertEqual(contract["answer_type"], "data_quality")
        self.assertIn("get_data_coverage", contract["tools_used"])
        self.assertIn("get_mapping_summary", contract["tools_used"])
        self.assertEqual(contract["data_scope"]["latest_month"], "2024-08")
        self.assertTrue(contract["display_blocks"])

    def test_display_blocks_and_role_based_evidence_are_backward_compatible(self) -> None:
        response = self.assistant.answer("\u6bd4\u8f03 8 \u6708\u5404\u5e73\u53f0\u71df\u6536\u8207\u5eab\u5b58")
        contract = response["answer_contract"]

        self.assertIn("display_blocks", contract)
        self.assertIn("role_based_evidence", contract)
        self.assertIn("headline", contract["display_blocks"])
        self.assertIn("key_observations", contract["display_blocks"])
        self.assertIn("table", contract["display_blocks"])
        self.assertIn("limitations", contract["display_blocks"])
        self.assertTrue(contract["role_based_evidence"]["evidence"])

    def test_cross_section_compare_display_blocks_use_projected_conclusion(self) -> None:
        response = self.assistant.answer("\u6bd4\u8f03 8 \u6708\u5404\u5e73\u53f0\u71df\u6536\u8207\u5eab\u5b58")
        contract = response["answer_contract"]
        display_blocks = contract["display_blocks"]

        self.assertEqual(response["task_profile"]["task_family"], "cross_section_compare")
        self.assertIn("get_contribution_analysis(revenue)", response["answer_plan"]["forbidden_primary_tools"])
        self.assertIn("\u5404\u5e73\u53f0\u6bd4\u8f03\u4e0b", display_blocks["headline"])
        self.assertIn("\u71df\u6536\u898f\u6a21\u8f03\u9ad8", display_blocks["headline"])
        self.assertNotIn("MoM contribution", display_blocks["headline"])
        self.assertNotIn("\u4e3b\u8981\u7531", display_blocks["headline"])
        self.assertLessEqual(len(display_blocks["key_observations"]), 3)
        self.assertIsNotNone(display_blocks["table"])

    def test_platform_performance_best_uses_scorecard(self) -> None:
        response = self.assistant.answer("\u8acb\u5206\u6790\u54ea\u500b\u5e73\u53f0\u8868\u73fe\u8f03\u4f73")
        contract = response["answer_contract"]
        headline = contract["display_blocks"]["headline"]

        self.assertEqual(response["task_profile"]["task_family"], "performance_assessment")
        self.assertEqual(response["task_profile"]["polarity"], "best")
        self.assertIn("get_platform_ranking(inventory_amount)", response["answer_plan"]["forbidden_primary_tools"])
        self.assertIn("get_platform_performance_snapshot", contract["tools_used"])
        self.assertIn("\u7d9c\u5408\u8868\u73fe\u8f03\u4f73", headline)
        self.assertIn("health_score", headline)
        self.assertNotIn("\u5c1a\u4e0d\u8db3\u4ee5\u660e\u78ba\u5224\u5b9a\u6700\u4f73\u5e73\u53f0", headline)
        self.assertNotIn("\u5eab\u5b58\u91d1\u984d\u6700\u9ad8", headline)

    def test_platform_performance_worst_uses_proxy_not_inventory_amount_rank(self) -> None:
        response = self.assistant.answer("\u8acb\u5206\u6790\u54ea\u500b\u5e73\u53f0\u8868\u73fe\u8f03\u5dee")
        contract = response["answer_contract"]
        headline = contract["display_blocks"]["headline"]

        self.assertEqual(response["task_profile"]["task_family"], "performance_assessment")
        self.assertEqual(response["task_profile"]["polarity"], "worst")
        self.assertIn("get_platform_performance_snapshot", contract["tools_used"])
        self.assertIn("health_score", headline)
        self.assertNotIn("\u5eab\u5b58\u91d1\u984d\u6700\u9ad8", headline)
        self.assertIn("get_inventory_turnover_proxy", contract["tools_used"])

    def test_time_compare_contribution_is_allowed_for_contribution_question(self) -> None:
        response = self.assistant.answer("8 \u6708\u76f8\u8f03 7 \u6708\u71df\u6536\u8b8a\u5316\u4e3b\u8981\u7531\u8ab0\u8ca2\u737b")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "time_compare")
        self.assertIn("get_contribution_analysis(revenue)", contract["tools_used"])
        self.assertIn("\u4e3b\u8981\u7531", contract["display_blocks"]["headline"])
        self.assertTrue(any("\u4e3b\u8981\u8ca2\u737b\u8005" in item for item in contract["display_blocks"]["key_observations"]))

    def test_background_evidence_stays_out_of_display_blocks(self) -> None:
        response = self.assistant.answer("\u6bd4\u8f03 8 \u6708\u5404\u5e73\u53f0\u71df\u6536\u8207\u5eab\u5b58")
        contract = response["answer_contract"]
        observations = " ".join(contract["display_blocks"]["key_observations"])
        role_items = contract["role_based_evidence"]["evidence"]

        self.assertLessEqual(len(contract["display_blocks"]["key_observations"]), 3)
        self.assertFalse(any(item["role"] == "background" and item["summary"] in observations for item in role_items))

    def test_answer_is_composed_from_display_blocks_for_phase8_tasks(self) -> None:
        response = self.assistant.answer("\u8acb\u5206\u6790\u54ea\u500b\u5e73\u53f0\u8868\u73fe\u8f03\u5dee")
        contract = response["answer_contract"]

        self.assertIn(contract["display_blocks"]["headline"], contract["answer"])
        self.assertIn("\u91cd\u9ede\u89c0\u6e2c", contract["answer"])


if __name__ == "__main__":
    unittest.main()
