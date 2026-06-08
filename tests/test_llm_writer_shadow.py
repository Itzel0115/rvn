from __future__ import annotations

import json
import unittest

from ollama_client import OllamaCallResult
from tests.support import build_stubbed_assistant


class ShadowWriterLLM:
    def __init__(self) -> None:
        self.calls = []

    def generate(self, **kwargs):
        return OllamaCallResult(ok=False, text="", data=None, error="stub")

    def generate_json(self, **kwargs):
        self.calls.append(kwargs)
        payload = {
            "headline": "結論：這是 shadow writer 的候選回答，不應進入正式 display_blocks。",
            "key_observations": ["shadow-only"],
            "limitations": [],
            "table_caption": "",
            "confidence_note": "shadow",
        }
        return OllamaCallResult(ok=True, text=json.dumps(payload, ensure_ascii=False), data=payload)


class LLMWriterShadowTest(unittest.TestCase):
    def test_shadow_mode_does_not_alter_official_display_blocks(self) -> None:
        question = "列出2025年3月各產品線庫存資料"
        deterministic = build_stubbed_assistant(
            "test-writer-shadow-off",
            use_llm_planner=False,
            use_llm_rewriter=False,
            use_llm_writer=False,
        ).answer(question)
        llm = ShadowWriterLLM()
        shadow = build_stubbed_assistant(
            "test-writer-shadow-on",
            use_llm_planner=False,
            use_llm_rewriter=False,
            use_llm_writer=True,
            llm_client=llm,
        ).answer(question)

        self.assertTrue(llm.calls)
        self.assertEqual(
            deterministic["answer_contract"]["display_blocks"],
            shadow["answer_contract"]["display_blocks"],
        )
        self.assertNotIn("llm_writer", shadow)
        self.assertNotIn("evidence_contracts", shadow["answer_contract"])


if __name__ == "__main__":
    unittest.main()
