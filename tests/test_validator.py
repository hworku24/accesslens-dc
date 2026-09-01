import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.validator import aggregate_record_scores, softmax_pair  # noqa: E402


class ValidatorTests(unittest.TestCase):
    def test_softmax_pair(self):
        correct, incorrect = softmax_pair(2, 1)
        self.assertAlmostEqual(correct + incorrect, 1.0)
        self.assertGreater(correct, incorrect)

    def test_any_positive_view_marks_present(self):
        result = aggregate_record_scores(
            [
                {"inference_status": "scored", "curb_ramp_probability": 0.2},
                {"inference_status": "scored", "curb_ramp_probability": 0.9},
            ],
            present_probability=0.7,
            absent_probability=0.3,
        )
        self.assertEqual(result["predicted_label"], "ramp_present")

    def test_uncertain_view_abstains(self):
        result = aggregate_record_scores(
            [{"inference_status": "scored", "curb_ramp_probability": 0.55}],
            present_probability=0.7,
            absent_probability=0.3,
        )
        self.assertEqual(result["predicted_label"], "abstain")

    def test_rejected_views_abstain(self):
        result = aggregate_record_scores(
            [{"inference_status": "rejected"}],
            present_probability=0.7,
            absent_probability=0.3,
        )
        self.assertEqual(result["aggregation_reason"], "no_eligible_images")


if __name__ == "__main__":
    unittest.main()
