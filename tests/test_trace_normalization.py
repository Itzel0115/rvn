from evaluation.normalization import normalize_trace,trajectory_fingerprint

def test_normalized_trajectory_excludes_ids_and_timing():
    trace={"trace_id":"random","started_at":"now","spans":[{"span_id":"a","span_name":"tool.execute","status":"ok","attributes":{"revenue_poc.tool.name":"get_x","args_fingerprint":"abc"}}]}
    normalized=normalize_trace(trace)
    assert "random" not in str(normalized) and trajectory_fingerprint(normalized)==trajectory_fingerprint(normalize_trace(trace))
