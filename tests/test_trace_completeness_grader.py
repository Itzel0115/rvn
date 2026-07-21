from evaluation.graders import trace_completeness
from evaluation.models import EvalCase

def test_execution_backed_assistant_requires_agent_span():
    case=EvalCase("c","core","x","x","question","x",execution_mode="execution_backed",execution_adapter="assistant")
    assert not trace_completeness(case,{"spans":[]}).passed
    assert trace_completeness(case,{"spans":[{"span_name":"agent.run"}]}).passed



def _projected_case(adapter: str, scenario: str = "default"):
    return EvalCase("c", "suite", scenario, "x", "question", "x", execution_mode="execution_backed", execution_adapter=adapter)


def _trace(adapter: str, output: dict, spans: list[str]) -> dict:
    return {"spans": [{"span_name": name, "attributes": {}} for name in spans], "_evaluation": {"adapter_id": adapter, "adapter_status": "completed", "normalized_output": output}}


def test_assistant_policy_requires_stateful_runtime_and_answer_spans():
    required = ["agent.request", "agent.canonicalize", "agent.answer_plan", "agent.plan.validate", "agent.run", "tool.execute", "evidence.validate", "answer.contract", "answer.render", "semantic.answer_plan.enrich", "semantic.resolve_task_requirement"]
    output = {"state": {"replan_count": 0}, "response": {"runtime": {"semantic_requirement_id": "req.metric_relationship.v1"}}}
    assert trace_completeness(_projected_case("assistant"), _trace("assistant", output, required)).passed
    missing = trace_completeness(_projected_case("assistant"), _trace("assistant", output, required[:-1]))
    assert not missing.passed
    assert "trace_incomplete" in missing.failure_categories


def test_writer_validation_span_is_required_when_writer_validation_expected():
    spans = ["agent.request", "agent.canonicalize", "agent.answer_plan", "agent.plan.validate", "agent.run", "tool.execute", "evidence.validate", "answer.contract", "answer.render"]
    output = {"state": {}, "response": {"writer_validation_expected": True}}
    result = trace_completeness(_projected_case("assistant"), _trace("assistant", output, spans))
    assert not result.passed
    assert "answer.writer_validate" in result.evidence_references


def test_adapter_specific_trace_policies():
    proactive_output = {"store_snapshot_summary": {"investigation_count": 1, "draft_count": 1}}
    proactive_spans = ["proactive.scan", "proactive.fingerprint", "proactive.quality_gate", "proactive.detect_candidates", "proactive.prioritize", "proactive.investigate", "proactive.counter_evidence", "proactive.build_draft"]
    assert trace_completeness(_projected_case("proactive"), _trace("proactive", proactive_output, proactive_spans)).passed
    assert trace_completeness(_projected_case("approval"), _trace("approval", {"action": "approve"}, ["approval.decision"])).passed
    assert trace_completeness(_projected_case("publication"), _trace("publication", {}, ["publication.publish"])).passed
    assert trace_completeness(_projected_case("mcp"), _trace("mcp", {"scenario": "allowed_tool_call"}, ["mcp.server.request", "mcp.security.validate", "mcp.tool.call"])).passed


def test_policy_rejection_still_requires_trace_except_fastmcp_lookup():
    invalid = trace_completeness(_projected_case("mcp"), _trace("mcp", {"scenario": "invalid_arguments"}, ["mcp.server.request"]))
    assert not invalid.passed
    hidden = trace_completeness(_projected_case("mcp"), _trace("mcp", {"scenario": "hidden_tool_rejection", "rejection_layer": "framework_tool_lookup"}, []))
    assert hidden.passed
