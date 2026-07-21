from __future__ import annotations
import unittest
from proactive_workflow.approval import create_approval_request, decide
from proactive_workflow.models import ExecutiveDraft, InvestigationRun
class ApprovalIdentityTest(unittest.TestCase):
    def test_cli_identity_is_unverified_and_nonblank(self):
        run=InvestigationRun("inv","cand","evt","req","completed"); draft=ExecutiveDraft("draft","inv",1,"t","s"); draft.refresh_hash(); request=create_approval_request(run,draft)
        decide(request,draft,run,"approve","person",identity_source="cli_supplied")
        self.assertEqual(request.identity_source,"cli_supplied"); self.assertFalse(request.identity_verified)
    def test_blank_identity_rejected(self):
        run=InvestigationRun("inv","cand","evt","req","completed"); draft=ExecutiveDraft("draft","inv",1,"t","s"); draft.refresh_hash(); request=create_approval_request(run,draft)
        with self.assertRaises(ValueError): decide(request,draft,run,"approve","   ")
