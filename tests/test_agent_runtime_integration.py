from __future__ import annotations

import os
import unittest

from tests.support import build_stubbed_assistant


class AgentRuntimeIntegrationTest(unittest.TestCase):
    def test_stateful_default_returns_compatible_response_and_trace(self) -> None:
        os.environ.pop("AGENT_RUNTIME_MODE", None)
        response = build_stubbed_assistant("runtime-integration").answer("有沒有營收下降但庫存上升的事業群？")
        self.assertIn("summary", response)
        self.assertIn("answer_contract", response)
        self.assertIn("agent_runtime", response)
        self.assertEqual(response["agent_runtime"]["status"], "completed")

    def test_legacy_mode_remains_available(self) -> None:
        previous = os.environ.get("AGENT_RUNTIME_MODE")
        os.environ["AGENT_RUNTIME_MODE"] = "legacy"
        try:
            response = build_stubbed_assistant("runtime-legacy").answer("有沒有營收下降但庫存上升的事業群？")
            self.assertIn("summary", response)
            self.assertNotIn("agent_runtime", response)
        finally:
            if previous is None:
                os.environ.pop("AGENT_RUNTIME_MODE", None)
            else:
                os.environ["AGENT_RUNTIME_MODE"] = previous
