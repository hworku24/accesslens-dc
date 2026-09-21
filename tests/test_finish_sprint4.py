import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finish_sprint4 import (  # noqa: E402
    build_split,
    expected_inventory_disagreements,
    validate_inventory_adjudications,
)


class FinishSprint4Tests(unittest.TestCase):
    def setUp(self):
        self.labels = [
            {
                "record_id": "a",
                "inventory_condition": "Good",
                "truth_label": "ramp_absent",
            },
            {
                "record_id": "b",
                "inventory_condition": "Missing",
                "truth_label": "cannot_determine",
            },
        ]

    def test_expected_inventory_disagreements_excludes_unscorable_truth(self):
        self.assertEqual(expected_inventory_disagreements(self.labels), {"a"})

    def test_missing_reason_is_rejected(self):
        rows = [
            {
                "record_id": "a",
                "adjudication_category": "imagery_insufficient",
                "adjudication_reason": "",
            }
        ]
        with self.assertRaises(ValueError):
            validate_inventory_adjudications(self.labels, rows)

    def test_split_separates_model_error_and_evidence_failure(self):
        inventory = [
            {
                "record_id": "a",
                "inventory_condition": "Good",
                "inventory_prediction": "ramp_present",
                "resolved_truth_label": "ramp_absent",
                "earliest_capture_date": "2020-01-01",
                "latest_capture_date": "2021-01-01",
                "adjudication_category": "imagery_insufficient",
                "adjudication_reason": "History unresolved.",
            }
        ]
        predictions = [
            {"record_id": "a", "predicted_label": "ramp_present"},
            {"record_id": "b", "predicted_label": "abstain"},
        ]
        rows = build_split(self.labels, predictions, inventory)
        categories = [row["adjudication_category"] for row in rows]
        self.assertEqual(categories.count("model_wrong"), 1)
        self.assertEqual(categories.count("imagery_insufficient"), 2)


if __name__ == "__main__":
    unittest.main()
