from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from evaluation.adapters import ApprovalExecutionAdapter, EvalEnvironment
from evaluation.models import EvalCase
from proactive_workflow.approval import decide


def _case(case_id: str, text: str) -> EvalCase:
    return EvalCase(
        case_id=case_id,
        suite="phase4a",
        category="approval",
        description=text,
        input_type="approval_action",
        question_or_event=text,
        execution_adapter="approval",
    )


def _execute(tmp_path: Path, case_id: str, text: str):
    adapter = ApprovalExecutionAdapter()
    environment = EvalEnvironment(tmp_path, trace_store_path=tmp_path / "traces.sqlite3")
    return adapter.execute(_case(case_id, text), environment)


def _load_payload(db_path: Path, table: str, key_column: str, key: str) -> dict:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(f"SELECT payload FROM {table} WHERE {key_column}=?", (key,)).fetchone()
    assert row is not None
    return json.loads(row[0])


def _audit_payloads(db_path: Path) -> list[dict]:
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute("SELECT payload FROM audit_events ORDER BY updated_at").fetchall()
    return [json.loads(row[0]) for row in rows]


def test_approve_uses_formal_service_and_reloads_store(tmp_path):
    result = _execute(tmp_path, "approval-approve", "approve pending request")

    assert result.execution_status == "completed"
    assert result.error_summary is None
    assert result.normalized_output["adapter_status"] == "completed"
    assert result.normalized_output["action"] == "approve"
    assert result.normalized_output["final_approval_status"] == "approved"
    assert result.normalized_output["content_hash_match"] is True
    assert result.trace is not None
    assert result.trace["operation_name"] == "approval.decision"

    db_path = tmp_path / "approval" / "proactive.sqlite3"
    approval = _load_payload(db_path, "approvals", "approval_request_id", result.normalized_output["old_approval_request_id"])
    draft = _load_payload(db_path, "drafts", "draft_id", result.normalized_output["old_draft_id"])
    assert approval["status"] == "approved"
    assert approval["approved_content_hash"] == draft["content_hash"]
    assert approval["identity_source"] == "test"
    assert approval["identity_verified"] is False


def test_reject_uses_formal_service_and_reason(tmp_path):
    result = _execute(tmp_path, "approval-reject", "reject pending request")

    assert result.execution_status == "completed"
    assert result.normalized_output["adapter_status"] == "completed"
    assert result.normalized_output["action"] == "reject"
    assert result.normalized_output["final_approval_status"] == "rejected"
    assert result.normalized_output["content_hash_match"] is True

    approval = _load_payload(
        tmp_path / "approval" / "proactive.sqlite3",
        "approvals",
        "approval_request_id",
        result.normalized_output["old_approval_request_id"],
    )
    assert approval["status"] == "rejected"
    assert approval["decision_reason"] == "evaluation rejection"
    assert approval["identity_source"] == "test"
    assert approval["identity_verified"] is False


def test_revision_v1_to_v2_uses_services_hash_binding_and_audit(tmp_path):
    result = _execute(tmp_path, "approval-revision", "request revision for pending approval")

    assert result.execution_status == "completed"
    output = result.normalized_output
    assert output["adapter_status"] == "completed"
    assert output["action"] == "revision"
    assert output["final_approval_status"] == "pending"
    assert output["draft_version"] == 2
    assert output["content_hash_match"] is True
    assert output["new_approval_request_id"]
    assert output["new_draft_id"]

    db_path = tmp_path / "approval" / "proactive.sqlite3"
    old_request = _load_payload(db_path, "approvals", "approval_request_id", output["old_approval_request_id"])
    old_draft = _load_payload(db_path, "drafts", "draft_id", output["old_draft_id"])
    new_request = _load_payload(db_path, "approvals", "approval_request_id", output["new_approval_request_id"])
    new_draft = _load_payload(db_path, "drafts", "draft_id", output["new_draft_id"])
    assert old_request["status"] == "revision_requested"
    assert old_draft["status"] == "superseded"
    assert new_request["status"] == "pending"
    assert new_request["draft_content_hash"] == new_draft["content_hash"]
    assert new_request["identity_source"] == "test"
    assert new_request["identity_verified"] is False
    assert any(item["action"] == "proactive.revision.created" for item in _audit_payloads(db_path))


def test_empty_identity_is_rejected_by_formal_service(tmp_path):
    adapter = ApprovalExecutionAdapter()
    store, run, draft, request = adapter._seed_pending_request(tmp_path)

    with pytest.raises(ValueError, match="approver_required"):
        decide(request, draft, run, "approve", "   ", identity_source="test")

    loaded = store.load_approval_request(request.approval_request_id)
    assert loaded is not None
    assert loaded.status.value == "pending"


def test_adapter_failure_is_failed_not_pending_or_synthetic(tmp_path):
    blocked_root = tmp_path / "blocked-root"
    blocked_root.write_text("not a directory", encoding="utf-8")

    result = ApprovalExecutionAdapter().execute(
        _case("approval-approve", "approve pending request"),
        EvalEnvironment(blocked_root, trace_store_path=tmp_path / "traces.sqlite3"),
    )

    assert result.execution_status == "failed"
    assert result.normalized_output["adapter_status"] == "failed"
    assert result.error_summary is not None
    assert "pending" not in result.error_summary.lower()
    assert "synthetic" not in result.error_summary.lower()


def test_production_output_is_not_written(tmp_path):
    output_root = Path("output")
    before = sorted(str(path.relative_to(output_root)) for path in output_root.rglob("*")) if output_root.exists() else []

    result = _execute(tmp_path, "approval-approve", "approve pending request")

    after = sorted(str(path.relative_to(output_root)) for path in output_root.rglob("*")) if output_root.exists() else []
    assert result.execution_status == "completed"
    assert before == after
    assert (tmp_path / "approval" / "output").exists()
    assert all(not str(value).startswith(os.getcwd()) for value in result.normalized_output.values() if isinstance(value, str))
