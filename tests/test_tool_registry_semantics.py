from __future__ import annotations

import unittest

from semantic_layer import get_catalog
from semantic_layer.generate_reference import render_reference
from semantic_layer.validation import validate_catalog
from tool_registry import TOOL_REGISTRY

class ToolRegistrySemanticsTest(unittest.TestCase):
    def test_catalog_coverage_has_no_silent_task(self) -> None:
        catalog = get_catalog()
        self.assertEqual(validate_catalog(catalog)["errors"], [])
        self.assertTrue(catalog.list_task_coverage())
        self.assertFalse([item for item in catalog.list_task_coverage() if item.coverage_status == "missing"])

    def test_snapshot_is_supporting_only_for_relationship(self) -> None:
        requirement = get_catalog().get_task_requirement("metric_relationship_analysis")
        self.assertIn("get_entity_performance_snapshot", requirement.forbidden_as_primary)
        self.assertNotIn("get_entity_performance_snapshot", requirement.allowed_primary_tools)

    def test_exposed_tools_are_safe_and_unique(self) -> None:
        exposed = [item for item in TOOL_REGISTRY.values() if item.mcp_exposable]
        self.assertEqual(len({item.mcp_name or item.tool_name for item in exposed}), len(exposed))
        for item in exposed:
            self.assertTrue(item.read_only)
            self.assertEqual(item.risk_level, "low")
            self.assertGreater(item.max_output_rows, 0)
            self.assertTrue(item.output_evidence_type or item.output_evidence_types)

    def test_reference_is_generated(self) -> None:
        with open("docs/SEMANTIC_CATALOG_REFERENCE.md", encoding="utf-8") as handle:
            self.assertEqual(handle.read(), render_reference())
