from __future__ import annotations

import unittest

from semantic_layer import get_catalog
from semantic_layer.validation import validate_catalog


class SemanticValidationTest(unittest.TestCase):
    def test_checked_in_catalog_is_valid(self) -> None:
        self.assertEqual(validate_catalog(get_catalog())["errors"], [])
