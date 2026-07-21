from __future__ import annotations

from pathlib import Path
from typing import Any

from .approval import create_approval_request
from .draft_builder import create_revision as build_revision
from .models import ApprovalStatus, DraftStatus, to_dict

def create_revision(store: Any, approval_request_id: str, revised_by: str, instructions: str, drafts_root: Path, identity_source: str) -> dict[str, Any]:
    if not revised_by or not revised_by.strip(): raise ValueError("reviser_required")
    if not instructions or not instructions.strip(): raise ValueError("revision_instructions_required")
    request=store.load_approval_request(approval_request_id)
    if request is None: raise LookupError("approval_not_found")
    if request.status is not ApprovalStatus.REVISION_REQUESTED: raise ValueError("revision_not_requested")
    old=store.load_draft(request.draft_id); run=store.load_investigation(request.investigation_id); candidate=store.load_candidate(run.candidate_id) if run else None
    if old is None or run is None or candidate is None: raise ValueError("revision_references_missing")
    if run.status == "failed": raise ValueError("failed_investigation_not_revisable")
    if old.status is not DraftStatus.REVISION_REQUESTED: raise ValueError("draft_not_revision_requested")
    revised=build_revision(candidate,run,old,drafts_root)
    store.save_draft(old); store.save_draft(revised)
    approval=create_approval_request(run,revised); approval.requested_by=revised_by.strip(); approval.identity_source=identity_source; approval.identity_verified=False; store.save_approval_request(approval)
    store.save_audit({"audit_id":"audit-revision-"+revised.draft_id,"action":"proactive.revision.created","approval_request_id":request.approval_request_id,"old_draft_id":old.draft_id,"new_draft_id":revised.draft_id,"revised_by":revised_by.strip(),"identity_source":identity_source,"identity_verified":False,"instructions":instructions.strip()})
    return {"old_draft_id":old.draft_id,"new_draft_id":revised.draft_id,"new_draft_version":revised.version,"old_approval_status":request.status.value,"new_approval_request_id":approval.approval_request_id,"new_approval_status":approval.status.value}
