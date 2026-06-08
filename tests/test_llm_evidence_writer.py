from __future__ import annotations

import json
import unittest

from llm_evidence_writer import EvidenceWriteRequest, LLMEvidenceWriter
from ollama_client import OllamaCallResult
from tests.test_evidence_contracts import EvidenceContractsTest


class FakeWriterLLM:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def generate_json(self, **kwargs):
        self.calls.append(kwargs)
        return OllamaCallResult(ok=True, text=json.dumps(self.payload, ensure_ascii=False), data=self.payload)


class LLMEvidenceWriterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        EvidenceContractsTest.setUpClass()
        _, cls.contracts = EvidenceContractsTest()._contracts_for("列出2025年3月各產品線庫存資料")

    def test_writer_returns_normalized_shadow_output(self) -> None:
        payload = {
            "headline": "結論：已列出 2025-03 各產品線庫存金額資料。",
            "key_observations": ["Server 為表內第一筆產品線。", "多餘觀察 2", "多餘觀察 3", "多餘觀察 4"],
            "limitations": [],
            "table_caption": "2025-03 各產品線庫存金額",
            "confidence_note": "依 EvidenceContract 產生。",
        }
        llm = FakeWriterLLM(payload)
        writer = LLMEvidenceWriter("test-writer")
        request = EvidenceWriteRequest(
            original_question="列出2025年3月各產品線庫存資料",
            canonical_task_profile={"task_family": "entity_month_table_lookup"},
            evidence_contracts=self.contracts,
            deterministic_display_blocks={},
            required_limitations=[],
            answer_style="concise",
        )

        result = writer.write(request, llm)

        self.assertTrue(result.ok)
        self.assertEqual(result.output["headline"], payload["headline"])
        self.assertEqual(len(result.output["key_observations"]), 3)
        self.assertIn("canonical_task_profile", llm.calls[0]["user_prompt"])
        self.assertIn("EvidenceContract", llm.calls[0]["system_prompt"])
        self.assertIn("Absolutely never output source_tool", llm.calls[0]["system_prompt"])
        self.assertIn("task_family=forecast_unsupported", llm.calls[0]["system_prompt"])

    def test_empty_headline_is_invalid_writer_result(self) -> None:
        llm = FakeWriterLLM({"headline": "", "key_observations": [], "limitations": []})
        writer = LLMEvidenceWriter("test-writer-empty")
        request = EvidenceWriteRequest(
            original_question="列出2025年3月各產品線庫存資料",
            canonical_task_profile={"task_family": "entity_month_table_lookup"},
            evidence_contracts=self.contracts,
        )

        result = writer.write(request, llm)

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "empty_headline")


if __name__ == "__main__":
    unittest.main()
