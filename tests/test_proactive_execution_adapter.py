from __future__ import annotations

import inspect
import os
from pathlib import Path

from evaluation.adapters import ADAPTERS, EvalEnvironment, ProactiveExecutionAdapter
from evaluation.models import EvalCase
from proactive_workflow.store import SQLiteProactiveStore


def _case(case_id: str, text: str, fixture_id: str = "proactive-new-scan-v1") -> EvalCase:
    return EvalCase(
        case_id=case_id,
        suite="phase4a",
        category="proactive",
        description=text,
        input_type="proactive_event",
        question_or_event=text,
        fixture_id=fixture_id,
        execution_adapter="proactive",
    )


def _execute(tmp_path: Path, case_id: str, text: str, fixture_id: str = "proactive-new-scan-v1"):
    return ProactiveExecutionAdapter().execute(
        _case(case_id, text, fixture_id),
        EvalEnvironment(tmp_path, trace_store_path=tmp_path / "traces.sqlite3"),
    )


def _store(tmp_path: Path) -> SQLiteProactiveStore:
    return SQLiteProactiveStore(tmp_path / "approval" / "proactive.sqlite3")


def _span_names(result) -> list[str]:
    return [span.get("span_name") for span in (result.trace or {}).get("spans", [])]


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


def test_new_scan_calls_formal_orchestrator_and_persists_store_records(tmp_path):
    result = _execute(tmp_path, "proactive-new", "new scan")

    assert result.execution_status == "completed"
    output = result.normalized_output
    assert output["adapter_id"] == "proactive"
    assert output["adapter_status"] == "completed"
    assert output["scenario"] == "new_scan"
    assert output["data_changed"] is True
    assert output["quality_status"] == "passed"
    assert output["candidate_count"] >= 1
    assert output["investigation_count"] >= 1
    assert output["draft_count"] >= 1
    assert output["pending_approval_count"] == output["draft_count"]
    assert output["store_snapshot_summary"]["candidate_count"] == output["candidate_count"]
    assert output["store_snapshot_summary"]["investigation_count"] == output["investigation_count"]
    assert output["store_snapshot_summary"]["draft_count"] == output["draft_count"]
    assert output["artifact_summary"]["draft_artifact_count"] >= output["draft_count"] * 2
    assert output["artifact_summary"]["all_under_temporary_root"] is True
    assert output["artifact_summary"]["all_marked_not_approved"] is True
    assert result.trace is not None
    assert {"proactive.scan", "proactive.fingerprint", "proactive.quality_gate", "proactive.detect_candidates", "proactive.prioritize", "proactive.investigate", "proactive.counter_evidence", "proactive.build_draft"}.issubset(set(_span_names(result)))

    store = _store(tmp_path)
    assert store.load_event(output["event_id"]) is not None
    assert len(store.list_candidates(output["event_id"])) == output["candidate_count"]
    assert len(store.list_investigations()) == output["investigation_count"]
    assert len(store.list_drafts()) == output["draft_count"]
    assert len(store.list_pending_approvals()) == output["pending_approval_count"]
    _assert_no_absolute_paths(result)


def test_unchanged_scan_runs_orchestrator_twice_without_duplicate_work(tmp_path):
    result = _execute(tmp_path, "proactive-unchanged", "unchanged scan", "proactive-unchanged-v1")

    assert result.execution_status == "unchanged"
    output = result.normalized_output
    assert output["adapter_status"] == "completed"
    assert output["scenario"] == "unchanged_scan"
    assert output["first_scan"]["data_changed"] is True
    assert output["data_changed"] is False
    assert output["second_scan_deltas"] == {"candidate_count": 0, "investigation_count": 0, "draft_count": 0, "approval_count": 0}
    assert output["duplicates_skipped"] == 0
    assert result.trace is not None
    assert result.trace["operation_name"] == "proactive.scan"
    assert "proactive.fingerprint" in _span_names(result)

    store = _store(tmp_path)
    dedup_keys = [candidate.deduplication_key for candidate in store.list_candidates()]
    assert len(dedup_keys) == len(set(dedup_keys))


def test_quality_blocker_comes_from_formal_quality_gate(tmp_path):
    result = _execute(tmp_path, "proactive-quality", "quality blocker", "proactive-quality-blocker-v1")

    assert result.execution_status == "completed"
    output = result.normalized_output
    assert output["scenario"] == "quality_blocker"
    assert output["blocked_by_quality"] is True
    assert output["quality_status"] == "blocked"
    assert output["quality_finding_count"] >= 1
    assert set(output["candidate_types"]) == {"data_quality_issue"}
    assert output["draft_count"] >= 1
    assert result.trace is not None
    assert {"proactive.scan", "proactive.quality_gate"}.issubset(set(_span_names(result)))

    store = _store(tmp_path)
    findings = store.list_quality_findings(output["event_id"])
    assert any(finding.severity.value == "critical" and finding.blocks_investigation for finding in findings)
    assert all(candidate.candidate_type == "data_quality_issue" for candidate in store.list_candidates(output["event_id"]))
    assert all(draft.status.value == "draft" for draft in store.list_drafts())


def test_divergence_scan_preserves_relationship_semantics(tmp_path):
    result = _execute(tmp_path, "proactive-divergence", "divergence scan", "proactive-divergence-v1")

    assert result.execution_status == "completed"
    output = result.normalized_output
    assert output["scenario"] == "divergence_scan"
    assert "revenue_inventory_divergence" in output["candidate_types"]

    store = _store(tmp_path)
    divergence = next(candidate for candidate in store.list_candidates(output["event_id"]) if candidate.candidate_type == "revenue_inventory_divergence")
    assert divergence.metric_ids == ["revenue_amount", "inventory_amount"]
    assert "inventory_qty" not in divergence.metric_ids
    assert divergence.entity_scope == {"dimension": "business_group", "value": "Alpha"}
    assert divergence.period_scope["mode"] == "period_pair"
    assert divergence.period_scope["period_a"] == "2025-02"
    assert divergence.period_scope["period_b"] == "2025-03"
    assert divergence.semantic_requirement_id == "req.metric_relationship.v1"
    assert any("root cause" in item or "描述" in item for item in divergence.limitations)

    run = next(item for item in store.list_investigations() if item.candidate_id == divergence.candidate_id)
    assert run.counter_evidence_summary["status"] == "not_available"
    assert any("反證" in item or "root cause" in item for item in run.limitations)
    draft = store.load_draft(run.draft_id)
    assert draft is not None
    assert draft.status.value == "draft"
    assert "NOT APPROVED" in (tmp_path / "approval" / "drafts" / run.investigation_id / f"draft_v{draft.version}.md").read_text(encoding="utf-8")


def test_production_output_is_not_written_and_response_is_path_safe(tmp_path):
    output_root = Path("output")
    before = sorted(str(path.relative_to(output_root)) for path in output_root.rglob("*")) if output_root.exists() else []

    result = _execute(tmp_path, "proactive-new", "new scan")

    after = sorted(str(path.relative_to(output_root)) for path in output_root.rglob("*")) if output_root.exists() else []
    assert result.execution_status == "completed"
    assert before == after
    assert (tmp_path / "approval" / "drafts").exists()
    _assert_no_absolute_paths(result)


def test_adapter_failure_is_failed_not_pending_or_synthetic(tmp_path):
    blocked_root = tmp_path / "blocked-root"
    blocked_root.write_text("not a directory", encoding="utf-8")

    result = ProactiveExecutionAdapter().execute(
        _case("proactive-new", "new scan"),
        EvalEnvironment(blocked_root, trace_store_path=tmp_path / "traces.sqlite3"),
    )

    assert result.execution_status == "failed"
    assert result.normalized_output["adapter_status"] == "failed"
    assert result.error_summary is not None
    assert "pending" not in result.error_summary.lower()
    assert "synthetic" not in result.error_summary.lower()


def test_runner_registry_selects_proactive_adapter():
    assert ADAPTERS["proactive"].adapter_id == "proactive"
    assert isinstance(ADAPTERS["proactive"], ProactiveExecutionAdapter)


def test_adapter_does_not_directly_create_records_or_spans():
    source = inspect.getsource(ProactiveExecutionAdapter)
    forbidden = ["save_event(", "save_candidate(", "save_investigation(", "save_draft(", "save_approval_request(", "recorder.span", "get_recorder"]
    assert not any(item in source for item in forbidden)
