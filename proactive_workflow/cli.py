from __future__ import annotations

import argparse
import json
from pathlib import Path

from analysis_pipeline import build_pipeline_context
from config import OUTPUT_DIR
from logging_utils import build_request_id
from multi_agent import MultiAgentAssistant
from .approval import decide
from .models import to_dict
from .orchestrator import ProactiveWorkflowOrchestrator
from .publisher import publish
from .revision import create_revision
from .store import SQLiteProactiveStore

def _service() -> tuple[ProactiveWorkflowOrchestrator, SQLiteProactiveStore]:
    request_id=build_request_id("proactive-cli"); context=build_pipeline_context(request_id); store=SQLiteProactiveStore(OUTPUT_DIR/"state"/"proactive_workflow.sqlite3")
    return ProactiveWorkflowOrchestrator(context, lambda rid: MultiAgentAssistant(context,rid,use_llm_planner=False,use_llm_rewriter=False,use_llm_writer=False),store,OUTPUT_DIR/"investigations"),store

def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description="Read-only proactive scan; approval and local publication require explicit human parameters. No auto-approve, notification, or source-data writes.")
    sub=parser.add_subparsers(dest="command",required=True); scan=sub.add_parser("scan"); scan.add_argument("--force",action="store_true"); revision=sub.add_parser("create-revision"); revision.add_argument("approval_request_id"); revision.add_argument("--revised-by", required=True); revision.add_argument("--instructions", required=True); sub.add_parser("list-candidates"); sub.add_parser("list-investigations"); sub.add_parser("list-approvals"); show=sub.add_parser("show-draft"); show.add_argument("draft_id")
    for name in ("approve","reject","request-revision","publish"):
        item=sub.add_parser(name); item.add_argument("approval_request_id"); item.add_argument("--approver" if name!="publish" else "--publisher",required=True); item.add_argument("--reason"); item.add_argument("--instructions")
    args=parser.parse_args(argv); service,store=_service()
    try:
        if args.command=="scan": result=service.scan(trigger_source="manual_cli",force_scan=args.force)
        elif args.command=="list-candidates": result=[to_dict(x) for x in store.list_candidates()]
        elif args.command=="list-investigations": result=[to_dict(x) for x in store.list_investigations()]
        elif args.command=="list-approvals": result=[to_dict(x) for x in store.list_approvals()]
        elif args.command=="create-revision":
            result=create_revision(store,args.approval_request_id,args.revised_by,args.instructions,OUTPUT_DIR/"investigations"/"drafts","cli_supplied")
        elif args.command=="show-draft":
            draft=store.load_draft(args.draft_id)
            if not draft: raise ValueError("draft_not_found")
            result=to_dict(draft)
        else:
            request=store.load_approval_request(args.approval_request_id)
            if not request: raise ValueError("approval_not_found")
            draft=store.load_draft(request.draft_id); run=store.load_investigation(request.investigation_id)
            if not draft or not run: raise ValueError("approval_references_missing")
            if args.command=="publish":
                record=publish(request,draft,run,OUTPUT_DIR/"investigations"/"drafts",OUTPUT_DIR/"investigations"/"approved",args.publisher); store.save_publication(record); result=to_dict(record)
            else:
                decision=request
                decide(decision,draft,run,"request_revision" if args.command=="request-revision" else args.command,args.approver,args.reason,args.instructions); store.save_draft(draft); store.save_approval_request(decision); result=to_dict(decision)
        print(json.dumps(result,ensure_ascii=False,default=str)); return 0
    except (ValueError, OSError) as exc: print(json.dumps({"error":str(exc)},ensure_ascii=False)); return 2
if __name__ == "__main__": raise SystemExit(main())
