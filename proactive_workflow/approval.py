from __future__ import annotations

from observability import get_recorder
from .models import ApprovalRequest, ApprovalStatus, DraftStatus, ExecutiveDraft, InvestigationRun, Severity, utc_now

def create_approval_request(run: InvestigationRun, draft: ExecutiveDraft) -> ApprovalRequest:
    from uuid import uuid4
    return ApprovalRequest(approval_request_id="apr-"+uuid4().hex[:12], investigation_id=run.investigation_id, draft_id=draft.draft_id, risk_level=Severity.MEDIUM, draft_content_hash=draft.content_hash)

def decide(request: ApprovalRequest, draft: ExecutiveDraft, run: InvestigationRun, decision: str, approver: str, reason: str | None = None, instructions: str | None = None, identity_source: str = "cli_supplied") -> ApprovalRequest:
    recorder = get_recorder()
    with recorder.run("approval.decision", request_id=request.approval_request_id, runtime_mode="proactive", investigation_id=run.investigation_id) as trace:
        return _decide(request, draft, run, decision, approver, reason, instructions, identity_source, recorder, trace)

def _decide(request: ApprovalRequest, draft: ExecutiveDraft, run: InvestigationRun, decision: str, approver: str, reason: str | None, instructions: str | None, identity_source: str, recorder, trace) -> ApprovalRequest:
    if request.status is not ApprovalStatus.PENDING: raise ValueError("approval_conflict")
    if not approver.strip(): raise ValueError("approver_required")
    if draft.content_hash != request.draft_content_hash: raise ValueError("draft_hash_changed")
    if draft.status in {DraftStatus.SUPERSEDED, DraftStatus.CANCELLED}: raise ValueError("draft_not_approvable")
    if run.status == "failed" and decision == "approve": raise ValueError("failed_investigation_not_approvable")
    if decision == "approve": request.status=ApprovalStatus.APPROVED; request.approved_content_hash=draft.content_hash; draft.status=DraftStatus.APPROVED
    elif decision == "reject":
        if not reason: raise ValueError("reject_reason_required")
        request.status=ApprovalStatus.REJECTED; draft.status=DraftStatus.REJECTED
    elif decision == "request_revision":
        if not instructions: raise ValueError("revision_instructions_required")
        request.status=ApprovalStatus.REVISION_REQUESTED; draft.status=DraftStatus.REVISION_REQUESTED
    else: raise ValueError("unsupported_decision")
    request.approver=approver.strip(); request.identity_source=identity_source; request.identity_verified=False; request.decision=decision; request.decision_reason=reason; request.revision_instructions=instructions; request.decided_at=utc_now(); recorder.finish_run(trace, status="completed", counters={}); return request
