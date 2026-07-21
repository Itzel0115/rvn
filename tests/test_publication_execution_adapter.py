from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from evaluation.adapters import EvalEnvironment, PublicationExecutionAdapter
from evaluation.models import EvalCase


def _case(case_id: str, text: str) -> EvalCase:
    return EvalCase(
        case_id=case_id,
        suite="phase4a",
        category="publication",
        description=text,
        input_type="publication_action",
        question_or_event=text,
        execution_adapter="publication",
    )


def _execute(tmp_path: Path, case_id: str, text: str):
    adapter = PublicationExecutionAdapter()
    environment = EvalEnvironment(tmp_path, trace_store_path=tmp_path / "traces.sqlite3")
    return adapter.execute(_case(case_id, text), environment)


def _load_payload(db_path: Path, table: str, key_column: str, key: str) -> dict:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(f"SELECT payload FROM {table} WHERE {key_column}=?", (key,)).fetchone()
    assert row is not None
    return json.loads(row[0])


def _all_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)


def _assert_no_absolute_paths(result):
    values = list(_all_strings(result.normalized_output)) + list(result.artifact_references)
    assert values
    assert all(not Path(value).is_absolute() for value in values if value)
    assert all(not value.startswith(os.getcwd()) for value in values if value)


def test_approved_publish_calls_decide_and_publisher_and_saves_record(tmp_path):
    result = _execute(tmp_path, "publication-approved", "approved publish")

    assert result.execution_status == "completed"
    output = result.normalized_output
    assert output["adapter_id"] == "publication"
    assert output["adapter_status"] == "completed"
    assert output["scenario"] == "approved_publish"
    assert output["approval_status"] == "approved"
    assert output["publication_status"] == "published"
    assert output["security_outcome"] == "published"
    assert output["artifact_exists"] is True
    assert output["artifact_hash_match"] is True
    assert output["publication_id"]
    assert result.trace is not None
    assert result.trace["operation_name"] == "publication.publish"
    assert result.trace["final_status"] == "completed"

    db_path = tmp_path / "approval" / "proactive.sqlite3"
    approval = _load_payload(db_path, "approvals", "approval_request_id", output["approval_request_id"])
    draft = _load_payload(db_path, "drafts", "draft_id", output["draft_id"])
    publication = _load_payload(db_path, "publications", "publication_id", output["publication_id"])
    assert approval["status"] == "approved"
    assert approval["identity_source"] == "test"
    assert approval["identity_verified"] is False
    assert approval["approved_content_hash"] == draft["content_hash"] == publication["content_hash"]
    assert publication["status"] == "published"

    approved_root = tmp_path / "publication" / "approved"
    report = approved_root / "eval-approval-investigation" / "report.md"
    approval_artifact = approved_root / "eval-approval-investigation" / "approval.json"
    assert report.exists()
    assert approval_artifact.exists()
    assert json.loads(approval_artifact.read_text(encoding="utf-8"))["content_hash"] == draft["content_hash"]
    assert all((approved_root / path).exists() for path in publication["artifact_paths"])
    assert output["store_snapshot_summary"]["publication_record_count"] == 1
    assert output["store_snapshot_summary"]["successful_publication_count"] == 1
    _assert_no_absolute_paths(result)


def test_pending_publish_is_blocked_by_formal_publisher_with_trace(tmp_path):
    result = _execute(tmp_path, "publication-pending", "pending publish")

    assert result.execution_status == "completed"
    output = result.normalized_output
    assert output["adapter_status"] == "completed"
    assert output["scenario"] == "pending_publish_blocked"
    assert output["approval_status"] == "pending"
    assert output["publication_status"] == "blocked"
    assert output["security_outcome"] == "expected_rejection"
    assert output["rejection_reason"] == "approval_required"
    assert output["artifact_exists"] is False
    assert output["publication_id"] is None
    assert output["store_snapshot_summary"]["publication_record_count"] == 0
    assert output["store_snapshot_summary"]["successful_publication_count"] == 0
    assert not (tmp_path / "publication" / "approved" / "eval-approval-investigation").exists()
    assert result.trace is not None
    assert result.trace["operation_name"] == "publication.publish"
    assert result.trace["final_status"] == "failed"
    assert result.trace["stop_reason"] == "approval_required"
    _assert_no_absolute_paths(result)


def test_rejected_publish_is_blocked_without_artifact(tmp_path):
    result = _execute(tmp_path, "publication-rejected", "rejected publish")

    output = result.normalized_output
    assert result.execution_status == "completed"
    assert output["scenario"] == "rejected_publish_blocked"
    assert output["approval_status"] == "rejected"
    assert output["publication_status"] == "blocked"
    assert output["rejection_reason"] == "approval_required"
    assert output["store_snapshot_summary"]["publication_record_count"] == 0
    assert not (tmp_path / "publication" / "approved" / "eval-approval-investigation").exists()
    assert result.trace["operation_name"] == "publication.publish"


def test_superseded_publish_is_blocked_and_v2_is_untouched(tmp_path):
    result = _execute(tmp_path, "publication-superseded", "superseded publish")

    output = result.normalized_output
    assert result.execution_status == "completed"
    assert output["scenario"] == "superseded_publish_blocked"
    assert output["approval_status"] == "revision_requested"
    assert output["publication_status"] == "blocked"
    assert output["store_snapshot_summary"]["draft_status"] == "superseded"
    assert output["store_snapshot_summary"]["audit_event_count"] == 1
    assert output["store_snapshot_summary"]["publication_record_count"] == 0

    db_path = tmp_path / "approval" / "proactive.sqlite3"
    with sqlite3.connect(db_path) as connection:
        drafts = [json.loads(row[0]) for row in connection.execute("SELECT payload FROM drafts").fetchall()]
        approvals = [json.loads(row[0]) for row in connection.execute("SELECT payload FROM approvals").fetchall()]
    assert any(item["version"] == 2 and item["status"] == "draft" for item in drafts)
    assert any(item["status"] == "pending" for item in approvals)
    assert not (tmp_path / "publication" / "approved" / "eval-approval-investigation").exists()
    assert result.trace["operation_name"] == "publication.publish"


def test_hash_mismatch_publish_is_blocked_without_artifact(tmp_path):
    result = _execute(tmp_path, "publication-hash", "hash mismatch publish")

    output = result.normalized_output
    assert result.execution_status == "completed"
    assert output["scenario"] == "hash_mismatch_blocked"
    assert output["approval_status"] == "approved"
    assert output["publication_status"] == "blocked"
    assert output["rejection_reason"] == "approved_hash_mismatch"
    assert output["store_snapshot_summary"]["publication_record_count"] == 0
    assert output["artifact_exists"] is False
    assert output["artifact_hash_match"] is False
    assert not (tmp_path / "publication" / "approved" / "eval-approval-investigation").exists()
    assert result.trace["operation_name"] == "publication.publish"
    assert result.trace["stop_reason"] == "approved_hash_mismatch"


def test_adapter_failure_is_failed_not_pending_or_synthetic(tmp_path):
    blocked_root = tmp_path / "blocked-root"
    blocked_root.write_text("not a directory", encoding="utf-8")

    result = PublicationExecutionAdapter().execute(
        _case("publication-approved", "approved publish"),
        EvalEnvironment(blocked_root, trace_store_path=tmp_path / "traces.sqlite3"),
    )

    assert result.execution_status == "failed"
    assert result.normalized_output["adapter_status"] == "failed"
    assert result.error_summary is not None
    assert "pending" not in result.error_summary.lower()
    assert "synthetic" not in result.error_summary.lower()


def test_adapter_ignores_arbitrary_destination_and_uses_temp_approved_root(tmp_path):
    result = _execute(tmp_path, "publication-approved-path", "approved publish to ../../escape and /tmp/other")

    assert result.execution_status == "completed"
    assert result.normalized_output["publication_status"] == "published"
    assert result.artifact_references
    assert all(item.startswith("approved/") for item in result.artifact_references)
    assert (tmp_path / "publication" / "approved" / "eval-approval-investigation" / "report.md").exists()
    assert not (tmp_path / "escape").exists()
    assert not Path("/tmp/other/eval-approval-investigation/report.md").exists()
    _assert_no_absolute_paths(result)


def test_production_output_is_not_written(tmp_path):
    output_root = Path("output")
    before = sorted(str(path.relative_to(output_root)) for path in output_root.rglob("*")) if output_root.exists() else []

    result = _execute(tmp_path, "publication-approved", "approved publish")

    after = sorted(str(path.relative_to(output_root)) for path in output_root.rglob("*")) if output_root.exists() else []
    assert result.execution_status == "completed"
    assert before == after
    assert (tmp_path / "publication" / "approved" / "eval-approval-investigation" / "report.md").exists()
