import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from build_sprint4_analysis import cost_rows, screening_counts  # noqa: E402


class Sprint4AnalysisTests(unittest.TestCase):
    def test_abstentions_route_to_review(self):
        labels = [
            {"record_id": "a", "truth_label": "ramp_absent"},
            {"record_id": "b", "truth_label": "ramp_present"},
            {"record_id": "c", "truth_label": "cannot_determine"},
        ]
        predictions = [
            {"record_id": "a", "predicted_label": "abstain"},
            {"record_id": "b", "predicted_label": "abstain"},
            {"record_id": "c", "predicted_label": "ramp_present"},
        ]
        counts = screening_counts(labels, predictions)
        self.assertEqual(counts["tp"], 1)
        self.assertEqual(counts["fp"], 1)
        self.assertEqual(counts["records"], 2)
        self.assertEqual(counts["field_reviews"], 2)

    def test_cost_ratio_penalizes_missed_absent_ramps(self):
        rows = cost_rows(
            [
                (
                    "m",
                    {
                        "records": 4,
                        "field_reviews": 2,
                        "abstentions": 0,
                        "tp": 1,
                        "fp": 1,
                        "fn": 2,
                        "tn": 0,
                    },
                )
            ]
        )
        by_cost = {row["false_negative_cost"]: row["weighted_cost"] for row in rows}
        self.assertEqual(by_cost, {1: 3, 5: 11, 10: 21})


if __name__ == "__main__":
    unittest.main()
