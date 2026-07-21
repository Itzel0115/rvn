from __future__ import annotations

import os
import subprocess
from pathlib import Path

from evaluation.adapters import ADAPTERS, EvalEnvironment, MCPExecutionAdapter
from evaluation.models import EvalCase
from tool_registry import TOOL_REGISTRY


def _case(case_id: str, text: str, fixture_id: str = "mcp-basic-v1") -> EvalCase:
    return EvalCase(
        case_id=case_id,
        suite="phase4a",
        category="mcp",
        description=text,
        input_type="mcp_call",
        question_or_event=text,
        fixture_id=fixture_id,
        execution_adapter="mcp",
    )


def _execute(tmp_path: Path, case_id: str, text: str, fixture_id: str = "mcp-basic-v1"):
    return MCPExecutionAdapter().execute(
        _case(case_id, text, fixture_id),
        EvalEnvironment(tmp_path, trace_store_path=tmp_path / "traces.sqlite3"),
    )


def _process_lines() -> set[str]:
    try:
        output = subprocess.check_output(["ps", "-ef"], text=True)
    except (OSError, subprocess.SubprocessError):
        return set()
    return {line for line in output.splitlines() if "mcp_server" in line or "revenue-inventory-analytics" in line}


def _all_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)


def _assert_response_safe(result):
    values = list(_all_strings(result.normalized_output)) + list(result.artifact_references)
    assert values
    assert all(not Path(value).is_absolute() for value in values if value)
    assert all(not value.startswith(os.getcwd()) for value in values if value)
    assert "traceback" not in repr(result.normalized_output).lower()
    assert "source_files" not in repr(result.normalized_output)
    assert "rows" not in result.normalized_output


def test_allowed_tool_protocol_call_and_trace(tmp_path):
    before = _process_lines()
    result = _execute(tmp_path, "mcp-allowed", "allowed tool call")
    after = _process_lines()

    assert result.execution_status == "completed"
    output = result.normalized_output
    assert output["adapter_id"] == "mcp"
    assert output["adapter_status"] == "completed"
    assert output["scenario"] == "allowed_tool_call"
    assert output["server_initialized"] is True
    assert output["protocol_completed"] is True
    assert output["called_tool"] == "get_data_coverage"
    assert output["evidence_type"] == "data_coverage"
    assert {"mcp.server.request", "mcp.security.validate", "mcp.tool.call"}.issubset(set(output["mcp_span_names"]))
    contract = TOOL_REGISTRY[output["called_tool"]]
    assert contract.read_only and contract.risk_level == "low" and contract.mcp_exposable
    assert output["subprocess_cleaned_up"] is True
    assert before == after
    _assert_response_safe(result)


def test_resource_read_protocol_and_trace(tmp_path):
    result = _execute(tmp_path, "mcp-resource", "resource read")

    output = result.normalized_output
    assert result.execution_status == "completed"
    assert output["scenario"] == "resource_read"
    assert output["called_resource"] == "semantic://metrics/revenue_amount"
    assert output["resource_count"] >= 1
    assert output["resource_template_count"] >= 1
    assert {"mcp.server.request", "mcp.resource.read"}.issubset(set(output["mcp_span_names"]))
    _assert_response_safe(result)


def test_invalid_arguments_are_protocol_rejected_and_sanitized(tmp_path):
    result = _execute(tmp_path, "mcp-invalid", "invalid arguments")

    output = result.normalized_output
    assert result.execution_status == "rejected"
    assert output["adapter_status"] == "completed"
    assert output["security_outcome"] == "expected_rejection"
    assert output["security_rejection"] is True
    assert output["validation_error_type"]
    assert "traceback" not in output["validation_error_type"].lower()
    assert {"mcp.server.request", "mcp.security.validate"}.issubset(set(output["mcp_span_names"]))
    _assert_response_safe(result)


def test_hidden_tool_is_protocol_rejected_without_side_effects(tmp_path):
    result = _execute(tmp_path, "mcp-hidden", "hidden approve_report")

    output = result.normalized_output
    assert result.execution_status == "rejected"
    assert output["adapter_status"] == "completed"
    assert output["called_tool"] == "approve_report"
    assert output["security_outcome"] == "expected_rejection"
    assert output["security_rejection"] is True
    assert output["validation_error_type"] in {"unknown_tool", "protocol_rejection"}
    assert not (tmp_path / "approval").exists()
    assert not (tmp_path / "publication").exists()
    _assert_response_safe(result)


def test_output_cap_comes_from_formal_server_not_adapter_truncation(tmp_path):
    result = _execute(tmp_path, "mcp-cap", "row cap", "mcp-row-cap-v1")

    output = result.normalized_output
    assert result.execution_status == "completed"
    assert output["scenario"] == "output_cap"
    assert output["called_tool"] == "get_entity_month_table"
    assert output["evidence_type"] == "entity_month_table"
    assert output["safe_result_item_count"] == output["row_cap"] == 20
    assert {"mcp.server.request", "mcp.security.validate", "mcp.tool.call"}.issubset(set(output["mcp_span_names"]))
    _assert_response_safe(result)


def test_tool_list_boundary_matches_read_only_low_risk_registry(tmp_path):
    result = _execute(tmp_path, "mcp-allowed", "allowed tool call")
    tool_names = result.normalized_output["tool_names"]

    assert tool_names
    forbidden = {"approve", "reject", "revision", "publish", "write", "write_back", "python", "run_python", "sql", "execute_sql", "shell", "execute_shell", "filesystem", "delete", "update", "send", "email", "slack", "webhook"}
    for name in tool_names:
        tokens = {part for chunk in name.lower().split("-") for part in chunk.split("_")}
        assert not (tokens & forbidden)
        contract = TOOL_REGISTRY[name]
        assert contract.read_only
        assert contract.risk_level == "low"
        assert contract.mcp_exposable


def test_fixture_allowlist_and_failure_no_synthetic_fallback(tmp_path):
    result = _execute(tmp_path, "mcp-unknown", "allowed tool", "mcp-unknown-v1")

    assert result.execution_status == "failed"
    assert result.normalized_output["adapter_status"] == "failed"
    assert result.error_summary is not None
    assert "pending" not in result.error_summary.lower()
    assert "synthetic" not in result.error_summary.lower()


def test_production_output_is_not_written_and_trace_is_temporary(tmp_path):
    output_root = Path("output")
    before = sorted(str(path.relative_to(output_root)) for path in output_root.rglob("*")) if output_root.exists() else []

    result = _execute(tmp_path, "mcp-allowed", "allowed tool call")

    after = sorted(str(path.relative_to(output_root)) for path in output_root.rglob("*")) if output_root.exists() else []
    assert result.execution_status == "completed"
    assert before == after
    assert (tmp_path / "traces.sqlite3").exists()
    _assert_response_safe(result)


def test_runner_registry_selects_mcp_adapter():
    assert ADAPTERS["mcp"].adapter_id == "mcp"
    assert isinstance(ADAPTERS["mcp"], MCPExecutionAdapter)
