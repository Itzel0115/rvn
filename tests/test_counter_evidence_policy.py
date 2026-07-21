from __future__ import annotations
import unittest
from proactive_workflow.counter_evidence import CounterEvidenceStatus, assess_counter_evidence
class CounterEvidencePolicyTest(unittest.TestCase):
    def test_not_available_is_limited_not_absent(self):
        value=assess_counter_evidence(CounterEvidenceStatus.NOT_AVAILABLE); self.assertFalse(value.search_performed); self.assertIn("不代表沒有反證",value.limitation)
    def test_not_found_requires_search(self):
        with self.assertRaises(ValueError): assess_counter_evidence(CounterEvidenceStatus.NOT_FOUND)
    def test_contradicted_caps_confidence(self): self.assertEqual(assess_counter_evidence(CounterEvidenceStatus.CONTRADICTED).confidence_cap,"low")
