from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4
from observability import get_recorder
from .models import ApprovalStatus, ExecutiveDraft, InvestigationRun, PublicationRecord, utc_now

def publish(request, draft: ExecutiveDraft, run: InvestigationRun, drafts_root: Path, approved_root: Path, publisher: str) -> PublicationRecord:
    recorder = get_recorder()
    trace_ref = None
    result: PublicationRecord | None = None
    error: Exception | None = None
    with recorder.run("publication.publish", request_id=request.approval_request_id, runtime_mode="proactive", investigation_id=run.investigation_id) as trace:
        trace_ref = trace
        try:
            result = _publish(request, draft, run, drafts_root, approved_root, publisher)
        except Exception as exc:
            error = exc
            recorder.event("publication.publish.rejected", {"reason": str(exc), "approval_status": request.status.value, "draft_status": draft.status.value})
        else:
            recorder.event("publication.publish.accepted", {"publication_status": result.status, "approval_status": request.status.value, "artifact_count": len(result.artifact_paths)})
    if error is not None:
        recorder.finish_run(trace_ref, status="failed", stop_reason=str(error), failure_category="publication_gate_error")
        raise error
    recorder.finish_run(trace_ref, status="completed", counters={})
    assert result is not None
    return result

def _publish(request, draft: ExecutiveDraft, run: InvestigationRun, drafts_root: Path, approved_root: Path, publisher: str) -> PublicationRecord:
    if request.status is not ApprovalStatus.APPROVED or draft.status.value != "approved": raise ValueError("approval_required")
    if not publisher.strip(): raise ValueError("publisher_required")
    if request.approved_content_hash != draft.content_hash: raise ValueError("approved_hash_mismatch")
    if run.status == "failed": raise ValueError("investigation_not_publishable")
    target=approved_root/run.investigation_id
    if target.exists(): raise ValueError("publication_already_exists")
    source=drafts_root/run.investigation_id
    if not source.exists(): raise ValueError("draft_artifact_missing")
    target.mkdir(parents=True); shutil.copy2(source/f"draft_v{draft.version}.md",target/"report.md"); shutil.copy2(source/f"draft_v{draft.version}.json",target/"report.json")
    (target/"approval.json").write_text(json.dumps({"approval_request_id":request.approval_request_id,"draft_id":draft.draft_id,"content_hash":draft.content_hash,"approver":request.approver},ensure_ascii=False,sort_keys=True),encoding="utf-8")
    return PublicationRecord(publication_id="pub-"+uuid4().hex[:12],approval_request_id=request.approval_request_id,draft_id=draft.draft_id,status="published",content_hash=draft.content_hash,artifact_paths=[f"{run.investigation_id}/report.md",f"{run.investigation_id}/report.json",f"{run.investigation_id}/approval.json"],published_at=utc_now(),publisher=publisher.strip())
