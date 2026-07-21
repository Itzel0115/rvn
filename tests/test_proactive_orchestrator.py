from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from proactive_workflow.orchestrator import ProactiveWorkflowOrchestrator
from proactive_workflow.store import SQLiteProactiveStore
from tests.support import get_context

class Assistant:
    def answer(self, question): return {"summary":"ok", "answer_contract":{"limitations":["test"]}, "domain_results":[], "agent_runtime":{"status":"completed","stop_reason":"completed"}}

class ProactiveOrchestratorTest(unittest.TestCase):
    def test_new_then_unchanged_fingerprint_deduplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            store=SQLiteProactiveStore(Path(temp)/"workflow.sqlite3")
            workflow=ProactiveWorkflowOrchestrator(get_context(),lambda request_id: Assistant(),store,Path(temp)/"artifacts")
            first=workflow.scan(trigger_source="test"); second=workflow.scan(trigger_source="test")
            self.assertTrue(first["data_changed"])
            self.assertEqual(second["status"],"unchanged")
            self.assertEqual(second["candidates_investigated"],0)
            self.assertTrue(store.list_pending_approvals() or first["candidates_detected"] == 0)
