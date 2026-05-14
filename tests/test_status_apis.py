from __future__ import annotations

import unittest

from analysis_tools import AnalysisToolbox
from demo_web import APP, build_data_quality_payload, build_data_version_payload, build_pipeline_status_payload, derive_health_status
from tests.support import get_context
from utils import MessageCollector


class StatusApiHelperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = get_context()
        cls.toolbox = AnalysisToolbox(cls.context, "test-status-apis")

    def test_health_api_returns_real_latest_month(self) -> None:
        payload = APP.get_health()

        self.assertIn(payload["status"], {"ok", "warning", "error"})
        self.assertTrue(payload["pipeline_loaded"])
        self.assertEqual(payload["latest_month"], "2026-02")

    def test_data_version_payload_reports_real_rows(self) -> None:
        payload = build_data_version_payload(self.context, self.toolbox)

        self.assertEqual(payload["latest_month"], "2026-02")
        self.assertEqual(payload["revenue_rows"], 1982)
        self.assertEqual(payload["inventory_rows"], 122935)
        self.assertIn("2025-01", payload["data_version"])
        self.assertIn("2026-02", payload["data_version"])

    def test_pipeline_status_payload_reports_message_counts(self) -> None:
        payload = build_pipeline_status_payload(self.context, self.toolbox)

        self.assertEqual(payload["latest_month"], "2026-02")
        self.assertEqual(payload["warning_count"], len(payload["warnings"]))
        self.assertEqual(payload["error_count"], len(payload["errors"]))

    def test_data_quality_payload_includes_quality_sections(self) -> None:
        payload = build_data_quality_payload(self.context, self.toolbox)

        self.assertIn(payload["status"], {"ok", "warning", "error"})
        self.assertEqual(payload["row_counts"]["revenue"], 1982)
        self.assertEqual(payload["row_counts"]["inventory"], 122935)
        self.assertIn("quality_checks", payload)
        self.assertTrue(payload["limitations"])

    def test_derive_health_status_marks_warning_without_error(self) -> None:
        messages = MessageCollector(warnings=["warn"], errors=[], infos=[])
        self.assertEqual(derive_health_status(messages), "warning")

    def test_derive_health_status_prioritizes_error(self) -> None:
        messages = MessageCollector(warnings=["warn"], errors=["err"], infos=[])
        self.assertEqual(derive_health_status(messages), "error")


if __name__ == "__main__":
    unittest.main()
