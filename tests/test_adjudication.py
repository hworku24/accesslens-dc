import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adjudicate_pilot import adjudicate  # noqa: E402


class AdjudicationTests(unittest.TestCase):
    def test_unusable_evidence_becomes_cannot_determine(self):
        labels = [
            {
                "record_id": "r1",
                "study_area": "a",
                "inventory_condition": "Good",
                "truth_label": "ramp_absent",
                "image_quality": "unusable",
                "image_ids": "i1",
            }
        ]
        predictions = [
            {"record_id": "r1", "predicted_label": "abstain", "confidence": "0"}
        ]
        adjudicated, report = adjudicate(labels, predictions)
        self.assertEqual(adjudicated[0]["truth_label"], "cannot_determine")
        self.assertEqual(report[0]["primary_review_code"], "imagery_insufficient")

    def test_inventory_disagreement_remains_qualified(self):
        labels = [
            {
                "record_id": "r1",
                "study_area": "a",
                "inventory_condition": "Fair",
                "truth_label": "ramp_absent",
                "image_quality": "good",
                "image_ids": "i1",
            }
        ]
        predictions = [
            {"record_id": "r1", "predicted_label": "abstain", "confidence": "0"}
        ]
        _, report = adjudicate(labels, predictions)
        self.assertEqual(report[0]["primary_review_code"], "possible_world_change")
        self.assertIn("independent evidence", report[0]["review_qualification"])


if __name__ == "__main__":
    unittest.main()
