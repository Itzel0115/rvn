from __future__ import annotations

import unittest

from demo_web import APP
from mcp_server.server import mcp

class ProactiveApiTest(unittest.TestCase):
    def test_listing_api_service_is_json_safe_and_lazy(self):
        self.assertIsInstance(APP.proactive_candidates(), list)
        self.assertIsInstance(APP.proactive_approvals(), list)
    def test_mcp_has_no_approval_or_publish_tool(self):
        import asyncio
        tools=asyncio.run(mcp.list_tools())
        names={item.name for item in tools}
        self.assertFalse({"approve","reject","publish","request_revision"} & names)
