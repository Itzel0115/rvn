import json
from evaluation.regression_gate import evaluate_gate

def test_gate_rejects_hard_safety_failure(tmp_path):
    (tmp_path/"aggregate.json").write_text(json.dumps({"safety_invariant_failures_total":1,"hard_invariant_pass_rate":0.9}))
    assert not evaluate_gate(tmp_path)[0]
