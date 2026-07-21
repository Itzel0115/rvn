from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from proactive_workflow.approval import create_approval_request, decide
from proactive_workflow.counter_evidence import CounterEvidenceStatus, assess_counter_evidence
from proactive_workflow.draft_builder import build_draft
from proactive_workflow.models import ApprovalStatus, InvestigationCandidate, InvestigationRun
from proactive_workflow.publisher import publish
from proactive_workflow.revision import create_revision
from proactive_workflow.store import SQLiteProactiveStore

class ProactiveRevisionTest(unittest.TestCase):
    def _seed(self, root):
        store=SQLiteProactiveStore(root/"state.sqlite3")
        candidate=InvestigationCandidate("cand","evt","revenue_inventory_divergence","t","signal only",["revenue_amount","inventory_amount"],["business_group"],{}, {"mode":"period_pair"},"detector","v1",deduplication_key="dedup")
        run=InvestigationRun("inv","cand","evt","req","completed",limitations=["descriptive"])
        draft=build_draft(candidate,run,root/"drafts"); request=create_approval_request(run,draft)
        for item, method in ((candidate,store.save_candidate),(run,store.save_investigation),(draft,store.save_draft),(request,store.save_approval_request)): method(item)
        return store,candidate,run,draft,request
    def test_revision_v1_to_v2_has_new_pending_hash_and_publish_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); store,candidate,run,v1,request=self._seed(root)
            decide(request,v1,run,"request_revision","human",instructions="clarify limitations",identity_source="test")
            store.save_draft(v1); store.save_approval_request(request)
            result=create_revision(store,request.approval_request_id,"reviser","clarify limitations",root/"drafts","test")
            v2=store.load_draft(result["new_draft_id"]); new=store.load_approval_request(result["new_approval_request_id"])
            self.assertEqual(store.load_draft(v1.draft_id).status.value,"superseded"); self.assertEqual(v2.version,2); self.assertEqual(new.status,ApprovalStatus.PENDING); self.assertEqual(new.draft_content_hash,v2.content_hash)
            with self.assertRaises(ValueError): decide(request,v1,run,"approve","human")
            with self.assertRaises(ValueError): publish(request,v1,run,root/"drafts",root/"approved","publisher")
            with self.assertRaises(ValueError): create_revision(store,request.approval_request_id,"reviser","again",root/"drafts","test")
            decide(new,v2,run,"approve","human",identity_source="test"); record=publish(new,v2,run,root/"drafts",root/"approved","publisher")
            self.assertEqual(record.draft_id,v2.draft_id)
    def test_revision_chain_v2_to_v3(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); store,candidate,run,v1,request=self._seed(root)
            decide(request,v1,run,"request_revision","human",instructions="v2",identity_source="test"); store.save_draft(v1); store.save_approval_request(request)
            v2r=create_revision(store,request.approval_request_id,"r","v2",root/"drafts","test"); v2=store.load_draft(v2r["new_draft_id"]); a2=store.load_approval_request(v2r["new_approval_request_id"])
            decide(a2,v2,run,"request_revision","human",instructions="v3",identity_source="test"); store.save_draft(v2); store.save_approval_request(a2)
            v3r=create_revision(store,a2.approval_request_id,"r","v3",root/"drafts","test"); self.assertEqual(store.load_draft(v3r["new_draft_id"]).version,3)
