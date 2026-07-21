from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from proactive_workflow.approval import create_approval_request, decide
from proactive_workflow.candidate_detector import RelationshipDetector
from proactive_workflow.data_quality import run_data_quality_checks
from proactive_workflow.fingerprint import build_dataset_fingerprint
from proactive_workflow.models import DataRefreshEvent, DraftStatus, InvestigationCandidate, InvestigationRun, Severity, to_dict
from proactive_workflow.policies import ProactivePolicy
from proactive_workflow.publisher import publish
from proactive_workflow.store import SQLiteProactiveStore
from semantic_layer import get_catalog

class Context:
    def __init__(self):
        self.revenue_df=pd.DataFrame({"month_key":["2025-01","2025-02"],"revenue_amount":[100,80],"business_group":["A","A"]})
        self.inventory_df=pd.DataFrame({"month_key":["2025-01","2025-02"],"inventory_amount":[50,70],"inventory_qty":[5,7],"business_group":["A","A"]})
class Toolbox:
    def get_revenue_inventory_relationship(self, **kwargs): return {"rows":[{"entity_value":"A","previous_month":"2025-01","month":"2025-02","revenue_change":-20,"inventory_change":20}],"limitations":["descriptive only"]}
class ProactiveCoreTest(unittest.TestCase):
    def test_fingerprint_stable_and_quality(self):
        context=Context(); first=build_dataset_fingerprint(context); self.assertEqual(first["fingerprint"],build_dataset_fingerprint(context)["fingerprint"])
        findings=run_data_quality_checks(context,get_catalog()); self.assertFalse(any(x.blocks_investigation for x in findings))
    def test_detector_requires_paired_change_and_dedup_key(self):
        event=DataRefreshEvent("evt",["revenue_logical"],"test",{"fingerprint":"same"})
        candidates=RelationshipDetector().detect(Toolbox(),event,get_catalog(),ProactivePolicy(minimum_absolute_change=0))
        divergence=[x for x in candidates if x.candidate_type=="revenue_inventory_divergence"]; self.assertEqual(len(divergence),1); self.assertEqual(divergence[0].semantic_requirement_id,"req.metric_relationship.v1")
    def test_store_unicode_and_approval_publication_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); store=SQLiteProactiveStore(root/"state.sqlite3"); event=DataRefreshEvent("evt",["x"],"test",{"fingerprint":"x"}); store.save_event(event); self.assertEqual(store.load_event("evt").event_id,"evt")
            candidate=InvestigationCandidate("cand","evt","revenue_inventory_divergence","測試","描述",["revenue_amount"],["business_group"],{}, {},"test","v1",deduplication_key="key")
            run=InvestigationRun("inv","cand","evt","req","completed")
            from proactive_workflow.draft_builder import build_draft
            draft=build_draft(candidate,run,root/"drafts"); request=create_approval_request(run,draft)
            with self.assertRaises(ValueError): publish(request,draft,run,root/"drafts",root/"approved","human")
            decide(request,draft,run,"approve","審核者")
            record=publish(request,draft,run,root/"drafts",root/"approved","publisher"); self.assertEqual(record.status,"published")
            self.assertTrue((root/"approved"/"inv"/"report.md").exists())
            revision=__import__("proactive_workflow.draft_builder",fromlist=["create_revision"]).create_revision(candidate,run,draft,root/"drafts")
            self.assertEqual(draft.status.value,"superseded")
            self.assertNotEqual(revision.content_hash,draft.content_hash)
            with self.assertRaises(ValueError): publish(request,draft,run,root/"drafts",root/"approved2","publisher")
            with self.assertRaises(ValueError): decide(request,draft,run,"approve","again")
    def test_json_safe_model_has_no_dataframe(self):
        value=DataRefreshEvent("evt",["資料"],"test",{"fingerprint":"x"}); self.assertEqual(to_dict(value)["dataset_ids"],["資料"])
