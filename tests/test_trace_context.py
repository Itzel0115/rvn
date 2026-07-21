from observability.context import TraceContext,current_context,trace_context

def test_context_nests_and_restores():
    base=TraceContext("t",request_id="r")
    with trace_context(base,span_id="child") as active:
        assert active.span_id=="child" and current_context().request_id=="r"
    assert current_context() is None
