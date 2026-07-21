from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .models import SpanRecord, TraceRun


class SQLiteTraceStore:
    """Small local store; failures here are deliberately isolated from business state."""
    def __init__(self, path: Path | str = "output/observability/traces.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with self._connect() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS traces (trace_id TEXT PRIMARY KEY, request_id TEXT, status TEXT, failure_category TEXT, started_at TEXT, finished_at TEXT, payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_traces_request ON traces(request_id);
            CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status, started_at);
            CREATE TABLE IF NOT EXISTS spans (trace_id TEXT NOT NULL, span_id TEXT PRIMARY KEY, parent_span_id TEXT, span_name TEXT, status TEXT, started_at TEXT, payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id, started_at);
            """)

    def save_trace(self, trace: TraceRun) -> None:
        payload = json.dumps(trace.to_dict(), ensure_ascii=False, sort_keys=True, allow_nan=False)
        with self._connect() as con:
            con.execute("INSERT INTO traces(trace_id,request_id,status,failure_category,started_at,finished_at,payload) VALUES(?,?,?,?,?,?,?) ON CONFLICT(trace_id) DO UPDATE SET request_id=excluded.request_id,status=excluded.status,failure_category=excluded.failure_category,started_at=excluded.started_at,finished_at=excluded.finished_at,payload=excluded.payload", (trace.trace_id, trace.request_id, trace.status, trace.failure_category, trace.started_at, trace.finished_at, payload))

    def save_span(self, span: SpanRecord) -> None:
        payload = json.dumps(span.to_dict(), ensure_ascii=False, sort_keys=True, allow_nan=False)
        with self._connect() as con:
            con.execute("INSERT INTO spans(trace_id,span_id,parent_span_id,span_name,status,started_at,payload) VALUES(?,?,?,?,?,?,?) ON CONFLICT(span_id) DO UPDATE SET status=excluded.status,payload=excluded.payload", (span.trace_id, span.span_id, span.parent_span_id, span.span_name, span.status, span.started_at, payload))

    def get_trace(self, request_or_trace_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute("SELECT payload FROM traces WHERE trace_id=? OR request_id=? ORDER BY started_at DESC LIMIT 1", (request_or_trace_id, request_or_trace_id)).fetchone()
            if not row: return None
            trace = json.loads(row["payload"])
            trace["spans"] = [json.loads(item["payload"]) for item in con.execute("SELECT payload FROM spans WHERE trace_id=? ORDER BY started_at", (trace["trace_id"],)).fetchall()]
            return trace

    def list_traces(self, *, status: str | None = None, failure_category: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        clauses: list[str] = []; params: list[Any] = []
        if status: clauses.append("status=?"); params.append(status)
        if failure_category: clauses.append("failure_category=?"); params.append(failure_category)
        query = "SELECT payload FROM traces" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY started_at DESC LIMIT ? OFFSET ?"
        with self._connect() as con:
            return [json.loads(row["payload"]) for row in con.execute(query, [*params, max(1, min(limit, 200)), max(0, offset)]).fetchall()]

    def purge_older_than(self, days: int) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max(1, days))).isoformat().replace("+00:00", "Z")
        with self._connect() as con:
            ids = [row[0] for row in con.execute("SELECT trace_id FROM traces WHERE started_at < ?", (cutoff,)).fetchall()]
            con.executemany("DELETE FROM spans WHERE trace_id=?", [(item,) for item in ids]); con.executemany("DELETE FROM traces WHERE trace_id=?", [(item,) for item in ids])
            return len(ids)

    def summarize(self) -> dict[str, Any]:
        traces = self.list_traces(limit=200)
        statuses: dict[str, int] = {}
        for item in traces: statuses[item.get("status", "unknown")] = statuses.get(item.get("status", "unknown"), 0) + 1
        return {"trace_count": len(traces), "by_status": statuses, "storage": "local_sqlite"}
