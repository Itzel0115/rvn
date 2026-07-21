from __future__ import annotations
import unittest
from types import SimpleNamespace
from proactive_workflow.candidate_detector import InventoryQuantityDetector, RelationshipDetector
from proactive_workflow.investigator import ProactiveInvestigator
from proactive_workflow.policies import ProactivePolicy
from semantic_layer import get_catalog
class Tools:
    def __init__(self, rows): self.rows=rows
    def get_revenue_inventory_relationship(self, **kwargs): return {"rows":self.rows,"limitations":["descriptive"]}
    def get_entity_time_series(self, **kwargs): return {"rows":[{"month":"2025-01","mom_change":None},{"month":"2025-02","mom_change":10}]}
class CandidateDetectorSemanticsTest(unittest.TestCase):
    def setUp(self): self.event=SimpleNamespace(event_id="evt",current_fingerprint={"fingerprint":"f"})
    def test_singles_and_divergence_keep_metric_and_task_semantics(self):
        rows=[{"entity_value":"A","previous_month":"2025-01","month":"2025-02","revenue_change":-10,"inventory_change":10}]
        values=RelationshipDetector().detect(Tools(rows),self.event,get_catalog(),ProactivePolicy(minimum_absolute_change=1))
        by_type={item.candidate_type:item for item in values}
        self.assertEqual(by_type["revenue_drop"].metric_ids,["revenue_amount"]); self.assertEqual(by_type["revenue_drop"].required_task_type,"entity_time_series"); self.assertIsNone(by_type["revenue_drop"].semantic_requirement_id)
        self.assertEqual(by_type["inventory_increase"].metric_ids,["inventory_amount"])
        self.assertEqual(by_type["revenue_inventory_divergence"].semantic_requirement_id,"req.metric_relationship.v1")
    def test_small_or_unpaired_changes_do_not_create_divergence(self):
        rows=[{"entity_value":"A","previous_month":"2025-01","month":"2025-02","revenue_change":-1,"inventory_change":None}]
        values=RelationshipDetector().detect(Tools(rows),self.event,get_catalog(),ProactivePolicy(minimum_absolute_change=2))
        self.assertFalse(values)
    def test_quantity_candidate_never_uses_amount_metric(self):
        rows=[{"entity_value":"A","previous_month":"2025-01","month":"2025-02","revenue_change":0,"inventory_change":0}]
        values=InventoryQuantityDetector().detect(Tools(rows),self.event,get_catalog(),ProactivePolicy(minimum_absolute_change=1))
        self.assertEqual(values[0].metric_ids,["inventory_qty"])
    def test_question_is_investigative_not_preconfirmed(self):
        row={"entity_value":"A","previous_month":"2025-01","month":"2025-02","revenue_change":-10,"inventory_change":10}
        candidate=next(item for item in RelationshipDetector().detect(Tools([row]),self.event,get_catalog(),ProactivePolicy(minimum_absolute_change=1)) if item.candidate_type=="revenue_inventory_divergence")
        self.assertIn("是否出現",ProactiveInvestigator(lambda _:None)._question(candidate))
