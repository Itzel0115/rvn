from __future__ import annotations

import os
import unittest

from tests.support import build_stubbed_assistant


CASES = [
    "請列出2026年2月各事業群營收",
    "請列出2026年2月各事業群庫存",
    "總體營收趨勢如何？",
    "總體庫存趨勢如何？",
    "哪個產品線營收最高？",
    "3通路方案 2026年2月營收是多少？",
    "有沒有營收下降但庫存上升的事業群？",
    "下個月營收會不會改善？",
]


class AgentRuntimeCompatibilityTest(unittest.TestCase):
    """Both modes must preserve the stable public response envelope without live Ollama."""

    def test_legacy_and_stateful_public_contracts(self) -> None:
        previous = os.environ.get("AGENT_RUNTIME_MODE")
        try:
            for question in CASES:
                for mode in ("legacy", "stateful"):
                    os.environ["AGENT_RUNTIME_MODE"] = mode
                    response = build_stubbed_assistant(f"compat-{mode}-{CASES.index(question)}").answer(question)
                    with self.subTest(mode=mode, question=question):
                        self.assertTrue(response.get("summary"))
                        self.assertIn("answer_contract", response)
                        self.assertIn("domain_results", response)
                        self.assertIn("limitations", response["answer_contract"])
                        if mode == "stateful" and question not in {"下個月營收會不會改善？"}:
                            self.assertIn("agent_runtime", response)
        finally:
            if previous is None:
                os.environ.pop("AGENT_RUNTIME_MODE", None)
            else:
                os.environ["AGENT_RUNTIME_MODE"] = previous
