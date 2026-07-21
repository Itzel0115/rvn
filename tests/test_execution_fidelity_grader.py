from __future__ import annotations

from evaluation.graders import execution_fidelity
from evaluation.models import EvalCase


def _case(adapter: str = "assistant") -> EvalCase:
    return EvalCase("case", "suite", "category", "description", "question", "q", execution_adapter=adapter)


def _assistant_trace(tool_name: str = "get_data_coverage") -> dict:
    return {
        "status": "completed",
        "final_status": "completed",
        "stop_reason": "completed",
        "spans": [{"span_name": "tool.execute", "attributes": {"revenue_poc.tool.name": tool_name}}],
        "_evaluation": {
            "adapter_id": "assistant",
            "adapter_status": "completed",
            "normalized_output": {
                "state": {
                    "available": True,
                    "status": "completed",
                    "stop_reason": "completed",
                    "replan_count": 0,
                    "tool_executions": [{"tool_name": "get_data_coverage", "status": "succeeded"}],
                    "evidence": [],
                },
                "response": {"status": "completed", "stop_reason": "completed", "evidence_types": []},
            },
        },
    }


def test_assistant_fidelity_passes_when_state_response_and_trace_match():
    assert execution_fidelity(_case("assistant"), _assistant_trace()).passed


def test_tool_call_mismatch_is_hard_failure():
    result = execution_fidelity(_case("assistant"), _assistant_trace("wrong_tool"))
    assert not result.passed
    assert result.severity == "hard"
    assert "execution_trace_mismatch" in result.failure_categories


def test_applied_replan_requires_replan_span():
    trace = _assistant_trace()
    trace["_evaluation"]["normalized_output"]["state"]["replan_count"] = 1
    result = execution_fidelity(_case("assistant"), trace)
    assert not result.passed
    assert "execution_trace_mismatch" in result.failure_categories


def test_pending_adapter_is_unimplemented_hard_failure():
    trace = {"spans": [], "_evaluation": {"adapter_id": "approval", "adapter_status": "pending", "normalized_output": {}}}
    result = execution_fidelity(_case("approval"), trace)
    assert not result.passed
    assert "execution_adapter_unimplemented" in result.failure_categories


def test_proactive_count_id_mismatch_is_detected():
    trace = {
        "spans": [{"span_name": "proactive.scan"}],
        "_evaluation": {
            "adapter_id": "proactive",
            "adapter_status": "completed",
            "normalized_output": {"store_snapshot_summary": {"candidate_count": 2}, "candidate_ids": ["cand-1"]},
        },
    }
    assert not execution_fidelity(_case("proactive"), trace).passed


def test_approval_publication_and_mcp_mismatch_checks():
    approval = {"spans": [], "_evaluation": {"adapter_id": "approval", "adapter_status": "completed", "normalized_output": {"final_approval_status": "approved", "content_hash_match": True}}}
    publication = {"spans": [{"span_name": "publication.publish"}], "_evaluation": {"adapter_id": "publication", "adapter_status": "completed", "normalized_output": {"publication_status": "published", "publication_id": "pub-1", "artifact_hash_match": False}}}
    mcp = {"spans": [{"span_name": "mcp.server.request"}], "_evaluation": {"adapter_id": "mcp", "adapter_status": "completed", "normalized_output": {"protocol_completed": True, "called_tool": "get_data_coverage", "security_outcome": "allowed"}}}
    hidden = {"spans": [], "_evaluation": {"adapter_id": "mcp", "adapter_status": "completed", "normalized_output": {"rejection_layer": "framework_tool_lookup"}}}
    assert not execution_fidelity(_case("approval"), approval).passed
    assert not execution_fidelity(_case("publication"), publication).passed
    assert not execution_fidelity(_case("mcp"), mcp).passed
    assert execution_fidelity(_case("mcp"), hidden).passed
