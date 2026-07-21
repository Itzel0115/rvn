from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4
from .models import DraftStatus, ExecutiveDraft, InvestigationCandidate, InvestigationRun

def build_draft(candidate: InvestigationCandidate, run: InvestigationRun, base_dir: Path, version: int = 1, supersedes: str | None = None) -> ExecutiveDraft:
    draft=ExecutiveDraft(draft_id="draft-"+uuid4().hex[:12], investigation_id=run.investigation_id, version=version, title=candidate.title, executive_summary=_summary(candidate,run), key_findings=[candidate.description, f"調查狀態：{run.status}"], evidence_points=run.evidence_summary, counter_evidence=run.counter_evidence_summary, limitations=list(dict.fromkeys(run.limitations)), confidence=run.confidence, recommended_followups=["由人類審閱 primary/supporting/counter evidence 後決定是否發布。"], supersedes_draft_id=supersedes)
    draft.refresh_hash(); directory=base_dir / run.investigation_id; directory.mkdir(parents=True,exist_ok=True); draft.markdown_path=f"{run.investigation_id}/draft_v{version}.md"; draft.json_path=f"{run.investigation_id}/draft_v{version}.json"
    markdown=_markdown(draft,candidate,run); (directory/f"draft_v{version}.md").write_text(markdown,encoding="utf-8"); (directory/f"draft_v{version}.json").write_text(json.dumps({"draft":draft.__dict__,"candidate":candidate.__dict__,"investigation":run.__dict__},ensure_ascii=False,default=lambda item:item.value if hasattr(item,"value") else str(item),sort_keys=True),encoding="utf-8")
    return draft
def create_revision(candidate: InvestigationCandidate, run: InvestigationRun, previous: ExecutiveDraft, base_dir: Path) -> ExecutiveDraft:
    previous.status = DraftStatus.SUPERSEDED
    return build_draft(candidate, run, base_dir, version=previous.version + 1, supersedes=previous.draft_id)

def _summary(candidate: InvestigationCandidate, run: InvestigationRun) -> str: return f"NOT APPROVED — {candidate.description}。調查狀態為 {run.status}，不得視為已證實因果。"
def _markdown(draft: ExecutiveDraft, candidate: InvestigationCandidate, run: InvestigationRun) -> str:
    return "\n".join(["# Investigation Draft", "", "**NOT APPROVED — Human approval required.**", "", "## Status", run.status, "## Trigger", candidate.candidate_type, "## Executive Summary", draft.executive_summary, "## What Changed", candidate.description, "## Primary Evidence", json.dumps(run.evidence_summary,ensure_ascii=False), "## Supporting Evidence", json.dumps(candidate.supporting_signals,ensure_ascii=False), "## Counter Evidence", json.dumps(run.counter_evidence_summary,ensure_ascii=False), "## Confidence", run.confidence, "## Limitations", "\n".join("- "+item for item in run.limitations), "## Recommended Follow-ups", "\n".join("- "+item for item in draft.recommended_followups), "## Approval Status", "pending", "## Audit References", f"candidate={candidate.candidate_id}; investigation={run.investigation_id}; hash={draft.content_hash}", ""])
