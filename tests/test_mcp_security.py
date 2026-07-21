from __future__ import annotations
import unittest
from mcp_server.security import enforce_row_limit, is_mcp_exposable, validate_tool_arguments

class MCPSecurityTest(unittest.TestCase):
    def test_default_deny_and_row_cap(self) -> None:
        self.assertTrue(is_mcp_exposable("get_entity_month_table"))
        self.assertFalse(is_mcp_exposable("get_chart_payload"))
        with self.assertRaises(ValueError): validate_tool_arguments("get_chart_payload", {})
        self.assertEqual(len(enforce_row_limit({"rows": list(range(100))})["rows"]), 20)
    def test_period_and_unknown_argument_are_rejected(self) -> None:
        with self.assertRaises(ValueError): validate_tool_arguments("get_entity_month_table", {"month": "bad"})
        with self.assertRaises(ValueError): validate_tool_arguments("get_entity_month_table", {"path": "/tmp/a"})
