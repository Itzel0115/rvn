from __future__ import annotations

import math
import unittest
from unittest.mock import patch

from mcp_server import server
from mcp_server.resources import read_resource
from mcp_server.security import validate_tool_arguments
from tool_registry import TOOL_REGISTRY

class ToolboxStub:
    def __init__(self): self.calls = []
    def get_entity_month_table(self, **kwargs):
        self.calls.append(("get_entity_month_table", kwargs))
        return {"evidence_type":"entity_month_table", "rows":[{"entity_value":"A", "value":math.nan}] * 30, "source_files":["/secret/path"]}

class McpToolsTest(unittest.TestCase):
    def test_resources_are_safe(self) -> None:
        for uri in ("semantic://catalog/summary", "semantic://metrics", "semantic://metrics/revenue_amount", "semantic://dimensions", "semantic://dimensions/business_group", "semantic://tasks/metric_relationship_analysis", "semantic://tools", "semantic://data-contracts", "semantic://data-freshness"):
            payload = read_resource(uri)
            self.assertNotIn("source_files", repr(payload))
            self.assertNotIn("/home/", repr(payload))

    def test_allowlisted_tool_calls_existing_toolbox_and_caps_output(self) -> None:
        toolbox = ToolboxStub()
        with patch.object(server, "_get_toolbox", return_value=toolbox):
            payload = server._call("get_entity_month_table", {"entity_dimension":"business_group", "metric":"revenue_amount", "month":"2025-01"})
        self.assertEqual(toolbox.calls[0][0], "get_entity_month_table")
        self.assertEqual(len(payload["result"]["rows"]), 20)
        self.assertIsNone(payload["result"]["rows"][0]["value"])
        self.assertNotIn("source_files", payload["result"])

    def test_invalid_and_unknown_arguments_are_denied(self) -> None:
        invalids = [("unknown", {}), ("get_entity_month_table", {"entity_dimension":"bad", "metric":"revenue_amount", "month":"2025-01"}), ("get_entity_month_table", {"entity_dimension":"business_group", "metric":"bad", "month":"2025-01"}), ("get_entity_month_table", {"entity_dimension":"business_group", "metric":"revenue_amount", "month":"202501"}), ("get_entity_metric_ranking", {"entity_dimension":"business_group", "metric":"revenue_amount", "top_n":99})]
        for name, arguments in invalids:
            with self.assertRaises(ValueError): validate_tool_arguments(name, arguments)

    def test_public_tools_match_registry_allowlist(self) -> None:
        expected = {item.mcp_name or item.tool_name for item in TOOL_REGISTRY.values() if item.mcp_exposable and item.read_only and item.risk_level == "low"}
        self.assertEqual(expected, {"get_entity_month_table", "get_entity_metric_ranking", "get_entity_performance_snapshot", "get_overall_time_series", "get_revenue_inventory_relationship", "get_data_coverage"})
