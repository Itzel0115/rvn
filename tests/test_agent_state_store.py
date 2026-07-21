from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_runtime.models import AgentRunState
from agent_runtime.state_store import InMemoryAgentStateStore, SQLiteAgentStateStore


class AgentStateStoreTest(unittest.TestCase):
    def _state(self) -> AgentRunState:
        return AgentRunState(request_id="req-store", thread_id="thread", question="q", canonical_task={"task_family": "metric_lookup"})

    def test_memory_save_load_and_missing(self) -> None:
        store = InMemoryAgentStateStore()
        self.assertFalse(store.exists("missing"))
        self.assertIsNone(store.load("missing"))
        store.save(self._state())
        self.assertTrue(store.exists("req-store"))
        self.assertEqual(store.load("req-store").question, "q")

    def test_sqlite_checkpoint_can_be_reopened(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite3"
            store = SQLiteAgentStateStore(path)
            state = self._state()
            store.save(state)
            state.warnings.append("updated")
            store.save(state)
            restored = SQLiteAgentStateStore(path).load("req-store")
            self.assertEqual(restored.warnings, ["updated"])
            self.assertTrue(SQLiteAgentStateStore(path).exists("req-store"))
