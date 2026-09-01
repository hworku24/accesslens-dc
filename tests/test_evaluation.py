import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.evaluation import (  # noqa: E402
    EvaluationConfig,
    evaluate_records,
    haversine_meters,
    load_ground_truth,
    load_predictions,
)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.truth = load_ground_truth(ROOT / "data/sample/ground_truth.csv")
        self.predictions = load_predictions(ROOT / "data/sample/predictions.csv")

    def test_distance_is_zero_for_identical_points(self):
        self.assertEqual(haversine_meters(38.9, -77.0, 38.9, -77.0), 0.0)

    def test_demo_confusion_counts(self):
        result = evaluate_records(
            self.truth,
            self.predictions,
            EvaluationConfig(match_radius_meters=12, confidence_threshold=0.70),
        )
        counts = result["metrics"]["counts"]
        self.assertEqual(counts["true_positive"], 2)
        self.assertEqual(counts["false_positive"], 1)
        self.assertEqual(counts["false_negative"], 1)
        self.assertEqual(counts["abstained_records"], 1)
        self.assertEqual(counts["matched_records"], 5)

    def test_low_confidence_prediction_enters_review_queue(self):
        result = evaluate_records(self.truth, self.predictions)
        reasons = [row["review_reasons"] for row in result["review_queue"]]
        self.assertTrue(any("low_confidence" in reason for reason in reasons))

    def test_unmatched_records_are_retained(self):
        result = evaluate_records(self.truth, self.predictions)
        self.assertEqual(len(result["unmatched_predictions"]), 1)
        self.assertEqual(len(result["unmatched_truths"]), 1)


if __name__ == "__main__":
    unittest.main()
