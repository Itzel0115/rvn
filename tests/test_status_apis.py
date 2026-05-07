from __future__ import annotations

import unittest

from analysis_tools import AnalysisToolbox
from demo_web import (
    APP,
    build_data_quality_payload,
    build_data_version_payload,
    build_pipeline_status_payload,
    derive_health_status,
)
from tests.support import get_context
from utils import MessageCollector


class StatusApiHelperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = get_context()
        cls.toolbox = AnalysisToolbox(cls.context, "test-status-apis")

    def test_health_api_returns_status_api_and_pipeline_loaded(self) -> None:
        payload = APP.get_health()

        self.assertIn(payload["status"], {"ok", "warning", "error"})
        self.assertEqual(payload["api"], "ok")
        self.assertTrue(payload["pipeline_loaded"])
        self.assertEqual(payload["latest_month"], "2024-08")

    def test_data_version_payload_reports_latest_month_rows_and_mapping(self) -> None:
        payload = build_data_version_payload(self.context, self.toolbox)

        self.assertEqual(payload["latest_month"], "2024-08")
        self.assertEqual(payload["revenue_rows"], 48)
        self.assertEqual(payload["inventory_rows"], 48)
        self.assertEqual(payload["mapping_rows"], 6)
        self.assertTrue(payload["mapping_success"])
        self.assertEqual(payload["data_version"], "months_2024-01_to_2024-08_rev48_inv48_map6")

    def test_pipeline_status_payload_reports_warning_and_error_counts(self) -> None:
        payload = build_pipeline_status_payload(self.context, self.toolbox)

        self.assertEqual(payload["latest_month"], "2024-08")
        self.assertEqual(payload["warning_count"], len(payload["warnings"]))
        self.assertEqual(payload["error_count"], len(payload["errors"]))
        self.assertGreaterEqual(payload["warning_count"], 1)
        self.assertEqual(payload["error_count"], 0)

    def test_data_quality_payload_includes_quality_sections(self) -> None:
        payload = build_data_quality_payload(self.context, self.toolbox)

        self.assertEqual(payload["status"], "warning")
        self.assertEqual(payload["data_version"], "months_2024-01_to_2024-08_rev48_inv48_map6")
        self.assertEqual(payload["row_counts"]["revenue"], 48)
        self.assertEqual(payload["row_counts"]["inventory"], 48)
        self.assertEqual(payload["row_counts"]["mapping"], 6)
        self.assertIn("mapping_success", payload["mapping"])
        self.assertIn("infos", payload["pipeline_messages"])
        self.assertIn("warnings", payload["pipeline_messages"])
        self.assertIn("errors", payload["pipeline_messages"])
        self.assertTrue(payload["quality_checks"])
        self.assertTrue(payload["limitations"])

    def test_derive_health_status_marks_warning_without_error(self) -> None:
        messages = MessageCollector(warnings=["warn"], errors=[], infos=[])
        self.assertEqual(derive_health_status(messages), "warning")

    def test_derive_health_status_prioritizes_error(self) -> None:
        messages = MessageCollector(warnings=["warn"], errors=["err"], infos=[])
        self.assertEqual(derive_health_status(messages), "error")


if __name__ == "__main__":
    unittest.main()
