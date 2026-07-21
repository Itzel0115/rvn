from observability.models import SpanRecord, TraceRun

def test_trace_models_are_json_safe_and_versioned():
    trace=TraceRun(trace_id="t",root_span_id="s",request_id="中文",operation_name="agent.run")
    assert "agent.run" in trace.to_json()
    span=SpanRecord("t","s",None,"tool.execute",attributes={"n":1})
    assert span.to_dict()["attributes"]["n"]==1
