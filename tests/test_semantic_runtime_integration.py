from __future__ import annotations

import unittest

from canonical_task import CanonicalTaskProfile
from tests.support import build_stubbed_assistant


class SemanticRuntimeIntegrationTest(unittest.TestCase):
    def test_canonical_task_carries_concise_semantic_references(self) -> None:
        assistant = build_stubbed_assistant("semantic-runtime")
        routing = assistant._run_question_understanding("有沒有營收下降但庫存上升的事業群？")
        profile = __import__("task_profile").build_task_profile(routing.question, routing)
        canonical = CanonicalTaskProfile.from_task_profile(profile, routing)
        self.assertEqual(canonical.semantic_task_requirement_id, "req.metric_relationship.v1")
        self.assertIn("revenue_amount", canonical.resolved_metric_ids)
