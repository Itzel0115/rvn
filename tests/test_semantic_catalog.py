from __future__ import annotations

import unittest

from semantic_layer import get_catalog


class SemanticCatalogTest(unittest.TestCase):
    def test_catalog_resolves_unicode_aliases_and_relationship_contract(self) -> None:
        catalog = get_catalog()
        self.assertEqual(catalog.resolve_metric("營收").metric_id, "revenue_amount")
        self.assertEqual(catalog.resolve_dimension("事業群").dimension_id, "business_group")
        requirement = catalog.get_task_requirement("metric_relationship_analysis")
        self.assertIn("get_revenue_inventory_relationship", requirement.allowed_primary_tools)
        self.assertIn("get_entity_performance_snapshot", requirement.forbidden_as_primary)

    def test_unknown_metric_is_not_resolved(self) -> None:
        self.assertIsNone(get_catalog().resolve_metric("not-a-kpi"))
