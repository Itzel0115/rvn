from observability.config import ObservabilityConfig
from observability.store import SQLiteTraceStore
from observability.tracing import TraceRecorder
from semantic_layer import get_catalog

def test_semantic_resolution_emits_span_when_trace_active(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSERVABILITY_ENABLED", "true"); monkeypatch.setenv("TRACE_STORE_PATH", str(tmp_path/"t.sqlite3"))
    store=SQLiteTraceStore(tmp_path/"t.sqlite3"); recorder=TraceRecorder(ObservabilityConfig(enabled=True,database_path=tmp_path/"t.sqlite3"),store)
    with recorder.run("agent.request",request_id="semantic-span"):
        get_catalog().resolve_metric("營收")
    assert "semantic.resolve_metric" in [s["span_name"] for s in store.get_trace("semantic-span")["spans"]]
