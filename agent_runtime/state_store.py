from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Protocol

from .models import AgentRunState


class AgentStateStore(Protocol):
    def save(self, state: AgentRunState) -> None: ...
    def load(self, request_id: str) -> AgentRunState | None: ...
    def exists(self, request_id: str) -> bool: ...


class InMemoryAgentStateStore:
    def __init__(self) -> None:
        self._states: dict[str, str] = {}

    def save(self, state: AgentRunState) -> None:
        self._states[state.request_id] = state.to_json()

    def load(self, request_id: str) -> AgentRunState | None:
        payload = self._states.get(request_id)
        return AgentRunState.from_json(payload) if payload else None

    def exists(self, request_id: str) -> bool:
        return request_id in self._states


class SQLiteAgentStateStore:
    def __init__(self, database_path: str | Path) -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS agent_run_states (request_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save(self, state: AgentRunState) -> None:
        state.touch()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO agent_run_states(request_id, payload, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(request_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                (state.request_id, state.to_json(), state.updated_at),
            )

    def load(self, request_id: str) -> AgentRunState | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM agent_run_states WHERE request_id = ?", (request_id,)).fetchone()
        return AgentRunState.from_json(row[0]) if row else None

    def exists(self, request_id: str) -> bool:
        with self._connect() as connection:
            return connection.execute("SELECT 1 FROM agent_run_states WHERE request_id = ?", (request_id,)).fetchone() is not None
