from observability.config import ObservabilityConfig
from observability.store import SQLiteTraceStore
from observability.tracing import TraceRecorder
from writer_validator import WriterValidator

def test_writer_validation_trace_is_safe(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSERVABILITY_ENABLED", "true"); monkeypatch.setenv("TRACE_STORE_PATH", str(tmp_path/"t.sqlite3"))
    store=SQLiteTraceStore(tmp_path/"t.sqlite3"); recorder=TraceRecorder(ObservabilityConfig(enabled=True,database_path=tmp_path/"t.sqlite3"),store)
    with recorder.run("agent.request",request_id="writer-span"):
        WriterValidator().validate({},[],{"headline":"safe","key_observations":[],"limitations":[]})
    span=next(s for s in store.get_trace("writer-span")["spans"] if s["span_name"]=="answer.writer_validate")
    assert "safe" not in str(span["attributes"])
