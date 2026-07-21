from observability.models import SpanRecord,TraceRun
from observability.store import SQLiteTraceStore

def test_sqlite_trace_store_request_lookup_pagination_and_unicode(tmp_path):
    store=SQLiteTraceStore(tmp_path/"nested"/"traces.sqlite3")
    trace=TraceRun(trace_id="trace",root_span_id="root",request_id="req-中文",operation_name="agent.run",status="completed")
    store.save_trace(trace);store.save_span(SpanRecord("trace","root",None,"agent.run",status="ok"))
    loaded=store.get_trace("req-中文")
    assert loaded and loaded["trace_id"]=="trace" and len(loaded["spans"])==1
    assert store.list_traces(limit=1)[0]["request_id"]=="req-中文"
