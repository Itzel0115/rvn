from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]

class McpServerIntegrationTest(unittest.TestCase):
    def test_official_stdio_lifecycle(self) -> None:
        async def run() -> None:
            params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"], cwd=ROOT)
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    init = await session.initialize()
                    self.assertEqual(init.serverInfo.name, "revenue-inventory-analytics")
                    tools = await session.list_tools()
                    self.assertIn("get_entity_month_table", {item.name for item in tools.tools})
                    resources = await session.list_resources()
                    self.assertIn("semantic://metrics", {str(item.uri) for item in resources.resources})
                    templates = await session.list_resource_templates()
                    self.assertIn("semantic://metrics/{metric_id}", {str(item.uriTemplate) for item in templates.resourceTemplates})
                    resource = await session.read_resource("semantic://metrics/revenue_amount")
                    self.assertTrue(resource.contents)
                    valid = await session.call_tool("get_data_coverage", {})
                    self.assertFalse(valid.isError)
                    rejected = await session.call_tool("get_entity_month_table", {"entity_dimension":"bad", "metric":"revenue_amount", "month":"2025-01"})
                    self.assertTrue(rejected.isError)
        asyncio.run(run())
