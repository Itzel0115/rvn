from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from typing import Any

from analysis_tools import AnalysisToolbox
from semantic_layer import get_catalog
from observability import get_recorder
from .approval import create_approval_request
from .candidate_detector import detect_candidates
from .data_quality import run_data_quality_checks
from .draft_builder import build_draft
from .fingerprint import build_dataset_fingerprint, compare_fingerprints
from .investigator import ProactiveInvestigator
from .models import DataRefreshEvent, to_dict
from .policies import ProactivePolicy, load_policy
from .prioritizer import prioritize
from .store import SQLiteProactiveStore

class ProactiveWorkflowOrchestrator:
    def __init__(self, context: Any, assistant_factory: Any, store: SQLiteProactiveStore, output_dir: Path, policy: ProactivePolicy | None = None) -> None:
        self.context=context; self.assistant_factory=assistant_factory; self.store=store; self.output_dir=output_dir; self.policy=policy or load_policy(); self.catalog=get_catalog()
    def scan(self, trigger_source: str = "python", force_scan: bool = False, mode: str = "scan_and_investigate") -> dict[str, Any]:
        recorder = get_recorder()
        with recorder.run("proactive.scan", request_id="proactive-" + trigger_source, runtime_mode="proactive") as trace:
            result = self._scan(trigger_source, force_scan, mode)
            recorder.finish_run(trace, status=str(result.get("status", "completed")), counters={"tool_call_count": int(result.get("candidates_detected", 0))})
            return result

    def _scan(self, trigger_source: str = "python", force_scan: bool = False, mode: str = "scan_and_investigate") -> dict[str, Any]:
        recorder = get_recorder()
        with recorder.span("proactive.fingerprint"):
            fingerprint = build_dataset_fingerprint(self.context, self.catalog)
            prior = self.store.find_event_by_fingerprint(fingerprint["fingerprint"])
        if prior and not force_scan:
            return {"event_id": prior.event_id, "data_changed": False, "quality_findings": 0, "candidates_detected": 0, "candidates_investigated": 0, "drafts_created": 0, "pending_approvals": len(self.store.list_pending_approvals()), "duplicates_skipped": 0, "blocked_by_quality": False, "status": "unchanged"}

        latest = self.store.get_latest_event()
        comparison = compare_fingerprints(latest.current_fingerprint if latest else None, fingerprint)
        periods = sorted({str(x) for frame in (self.context.revenue_df, self.context.inventory_df) for x in (frame["month_key"].dropna().unique() if "month_key" in frame.columns else [])})
        event = DataRefreshEvent(event_id="evt-" + uuid4().hex[:12], dataset_ids=["revenue_logical", "inventory_logical"], trigger_source=trigger_source, current_fingerprint=fingerprint, previous_fingerprint=latest.current_fingerprint if latest else None, changed=comparison["changed"], change_summary=comparison, available_period_start=periods[0] if periods else None, available_period_end=periods[-1] if periods else None, latest_available_period=periods[-1] if periods else None, data_contract_ids=[item.dataset_id for item in self.catalog.list_data_contracts()])
        self.store.save_event(event)
        self.store.save_audit({"audit_id": "audit-" + uuid4().hex[:12], "action": "proactive.scan.started", "event_id": event.event_id, "status": "created"})

        with recorder.span("proactive.quality_gate"):
            findings = run_data_quality_checks(self.context, self.catalog)
            for finding in findings:
                self.store.save_quality_finding(finding)
            blocked = any(item.blocks_investigation for item in findings)
            event.quality_status = "blocked" if blocked else "passed"
            event.status = "quality_checked"
            self.store.save_event(event)

        toolbox = AnalysisToolbox(self.context, "proactive-" + event.event_id[-8:])
        with recorder.span("proactive.detect_candidates"):
            candidates = detect_candidates(toolbox, event, self.catalog, self.policy, findings)
            if blocked:
                candidates = [item for item in candidates if item.candidate_type == "data_quality_issue"]
        with recorder.span("proactive.prioritize"):
            candidates = prioritize(candidates, self.policy, blocked)

        created = []
        skipped = 0
        for candidate in candidates:
            if self.store.find_candidate_by_deduplication_key(candidate.deduplication_key):
                skipped += 1
                continue
            self.store.save_candidate(candidate)
            self.store.save_audit({"audit_id": "audit-" + uuid4().hex[:12], "action": "proactive.candidate.detected", "event_id": event.event_id, "candidate_id": candidate.candidate_id, "severity": candidate.severity.value})
            created.append(candidate)

        investigated = 0
        drafts = 0
        if mode == "scan_and_investigate":
            investigator = ProactiveInvestigator(self.assistant_factory)
            for candidate in created[:self.policy.candidate_limit_per_scan]:
                with recorder.span("proactive.investigate"):
                    run = investigator.investigate(candidate)
                self.store.save_investigation(run)
                investigated += 1
                if run.status != "failed":
                    with recorder.span("proactive.build_draft"):
                        draft = build_draft(candidate, run, self.output_dir / "drafts")
                        self.store.save_draft(draft)
                        run.draft_id = draft.draft_id
                        approval = create_approval_request(run, draft)
                        self.store.save_approval_request(approval)
                        run.approval_request_id = approval.approval_request_id
                        self.store.save_investigation(run)
                    drafts += 1
        return {"event_id": event.event_id, "data_changed": comparison["changed"], "quality_findings": len(findings), "candidates_detected": len(created), "candidates_investigated": investigated, "drafts_created": drafts, "pending_approvals": len(self.store.list_pending_approvals()), "duplicates_skipped": skipped, "blocked_by_quality": blocked, "status": "completed"}
    def list_summary(self, values: list[Any]) -> list[dict[str,Any]]: return [to_dict(item) for item in values]
