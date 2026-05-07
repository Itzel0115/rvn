from __future__ import annotations

import unittest

from llm_rewriter import LLMAnswerRewriter, RewriteRequest
from ollama_client import OllamaCallResult
from tests.support import build_stubbed_assistant


class FakeRewriteLLM:
    def __init__(self, *, data=None, ok: bool = True, error: str | None = None) -> None:
        self._data = data
        self._ok = ok
        self._error = error

    def generate_json(self, **kwargs):
        return OllamaCallResult(ok=self._ok, text="", data=self._data, error=self._error)


class LLMRewriterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rewriter = LLMAnswerRewriter("test-llm-rewriter")
        self.request = RewriteRequest(
            question="Why is revenue down?",
            deterministic_answer=(
                "目前尚無法直接判斷營收變化的根本原因。"
                "2024-08 營收相較 2024-07 下降 215.00。"
                "GG-02 / 新事業群 1 的庫存效率 proxy 偏弱。"
            ),
            answer_contract={
                "answer_type": "diagnosis",
                "answer": (
                    "目前尚無法直接判斷營收變化的根本原因。"
                    "2024-08 營收相較 2024-07 下降 215.00。"
                    "GG-02 / 新事業群 1 的庫存效率 proxy 偏弱。"
                ),
            },
            evidence=[
                {
                    "domain": "sales",
                    "summary": "sales: month=2024-08 revenue=6,275.00",
                    "details": {"month": "2024-08", "mom_change": -215.00, "platform": "GG-02"},
                }
            ],
            limitations=[
                "目前尚無法直接判斷營收變化的根本原因。",
                "資料尚未包含訂單、出貨、價格、客戶與市場需求等欄位。",
                "此為營收與庫存資料推導的 proxy，不等於正式庫存週轉率。",
            ],
            tools_used=["get_root_cause_candidates", "get_contribution_analysis(revenue)"],
        )

    def test_valid_rewrite_can_pass(self) -> None:
        llm = FakeRewriteLLM(
            data={
                "rewritten_answer": (
                    "目前尚無法直接判斷營收變化的根本原因。"
                    "依現有資料，2024-08 營收相較 2024-07 下降 215.00，且 GG-02 / 新事業群 1 的庫存效率 proxy 偏弱。"
                    "資料尚未包含訂單、出貨、價格、客戶與市場需求等欄位，且此 proxy 不等於正式庫存週轉率。"
                )
            }
        )
        result = self.rewriter.rewrite(self.request, llm)
        self.assertTrue(result.ok)
        self.assertTrue(result.validation_passed)
        self.assertIn("GG-02", result.rewritten_answer)

    def test_new_number_is_rejected(self) -> None:
        llm = FakeRewriteLLM(
            data={
                "rewritten_answer": (
                    "目前尚無法直接判斷營收變化的根本原因。"
                    "2024-08 營收相較 2024-07 下降 999.00。"
                    "資料尚未包含訂單、出貨、價格、客戶與市場需求等欄位。"
                )
            }
        )
        result = self.rewriter.rewrite(self.request, llm)
        self.assertFalse(result.ok)
        self.assertFalse(result.validation_passed)
        self.assertTrue(any("new_numbers" in violation for violation in result.violations))

    def test_root_cause_claim_is_rejected(self) -> None:
        llm = FakeRewriteLLM(
            data={
                "rewritten_answer": (
                    "原因就是 GG-02 的問題，而且已確認根本原因。"
                    "2024-08 營收相較 2024-07 下降 215.00。"
                )
            }
        )
        result = self.rewriter.rewrite(self.request, llm)
        self.assertFalse(result.ok)
        self.assertTrue(any("forbidden_phrases" in violation for violation in result.violations))

    def test_forecast_phrase_is_rejected(self) -> None:
        llm = FakeRewriteLLM(
            data={
                "rewritten_answer": (
                    "目前尚無法直接判斷營收變化的根本原因，但下個月一定會改善。"
                    "2024-08 營收相較 2024-07 下降 215.00。"
                )
            }
        )
        result = self.rewriter.rewrite(self.request, llm)
        self.assertFalse(result.ok)
        self.assertTrue(any("forbidden_phrases" in violation for violation in result.violations))

    def test_missing_limitation_is_rejected(self) -> None:
        llm = FakeRewriteLLM(
            data={
                "rewritten_answer": "2024-08 營收相較 2024-07 下降 215.00，GG-02 / 新事業群 1 的庫存效率 proxy 偏弱。"
            }
        )
        result = self.rewriter.rewrite(self.request, llm)
        self.assertFalse(result.ok)
        self.assertTrue(any("missing_limitation" in violation for violation in result.violations))

    def test_validation_failure_falls_back_to_original_answer(self) -> None:
        bad_llm = FakeRewriteLLM(
            data={"rewritten_answer": "原因就是 GG-02，而且 999.00 一定是主因。"}
        )
        deterministic = build_stubbed_assistant("test-rewriter-control").answer("Why is revenue down?")
        rewritten = build_stubbed_assistant(
            "test-rewriter-fallback",
            use_llm_rewriter=True,
            llm_client=bad_llm,
        ).answer("Why is revenue down?")

        self.assertEqual(
            rewritten["answer_contract"]["answer"],
            deterministic["answer_contract"]["answer"],
        )

    def test_successful_rewrite_only_replaces_answer_field(self) -> None:
        good_llm = FakeRewriteLLM(
            data={
                "rewritten_answer": (
                    "依目前已載入資料，營收最高的新事業群為代碼 1，數值為 18,810.00。"
                )
            }
        )
        deterministic = build_stubbed_assistant("test-rewriter-success-control").answer(
            "Which business group has the highest revenue?"
        )
        rewritten = build_stubbed_assistant(
            "test-rewriter-success",
            use_llm_rewriter=True,
            llm_client=good_llm,
        ).answer("Which business group has the highest revenue?")

        self.assertNotEqual(
            rewritten["answer_contract"]["answer"],
            deterministic["answer_contract"]["answer"],
        )
        self.assertEqual(
            rewritten["answer_contract"]["tools_used"],
            deterministic["answer_contract"]["tools_used"],
        )
        self.assertEqual(
            rewritten["answer_contract"]["evidence"],
            deterministic["answer_contract"]["evidence"],
        )

    def test_default_use_llm_rewriter_false_preserves_deterministic_path(self) -> None:
        llm = FakeRewriteLLM(
            data={"rewritten_answer": "依目前資料，營收最高的是代碼 1。"}
        )
        deterministic = build_stubbed_assistant("test-rewriter-default-control").answer(
            "Which business group has the highest revenue?"
        )
        unchanged = build_stubbed_assistant(
            "test-rewriter-default",
            use_llm_rewriter=False,
            llm_client=llm,
        ).answer("Which business group has the highest revenue?")

        self.assertEqual(
            unchanged["answer_contract"]["answer"],
            deterministic["answer_contract"]["answer"],
        )


if __name__ == "__main__":
    unittest.main()
