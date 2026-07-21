from __future__ import annotations
import json, unittest
from mcp_server.resources import read_resource

class MCPResourcesTest(unittest.TestCase):
    def test_public_semantic_resources_are_small_and_json_safe(self) -> None:
        payload = read_resource("semantic://metrics/revenue_amount")
        self.assertEqual(payload["metric_id"], "revenue_amount")
        json.dumps(payload, ensure_ascii=False)
        with self.assertRaises(KeyError): read_resource("semantic://metrics/unknown")
