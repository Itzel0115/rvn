from __future__ import annotations

import unittest
from pathlib import Path


class RealDataContractTest(unittest.TestCase):
    def test_real_data_contract_document_exists_and_names_grain(self) -> None:
        contract = Path("docs/real_data_contract.md")
        text = contract.read_text(encoding="utf-8")

        self.assertIn("data/inventory.xlsx", text)
        self.assertIn("data/revenue.xlsx", text)
        self.assertIn("month_key + business_group + product_line_5", text)
        self.assertIn("`business_group` = `新事業群`", text)
        self.assertIn("`product_line_5` = `五大產品線`", text)
        self.assertIn("Do not join", text)


if __name__ == "__main__":
    unittest.main()
