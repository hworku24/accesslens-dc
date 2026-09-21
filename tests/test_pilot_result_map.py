import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from make_pilot_result_map import build_points, render  # noqa: E402


class PilotResultMapTests(unittest.TestCase):
    def test_review_codes_distinguish_disagreement_abstention_and_no_imagery(self):
        candidates = [
            {
                "record_id": "r1",
                "latitude": "38.9",
                "longitude": "-77.0",
                "study_area": "a",
                "condition": "Missing",
                "year_inspected": "2016",
                "image_count": "2",
                "coverage_available": "1",
            },
            {
                "record_id": "r2",
                "latitude": "38.9",
                "longitude": "-77.0",
                "study_area": "a",
                "condition": "Good",
                "year_inspected": "2016",
                "image_count": "2",
                "coverage_available": "1",
            },
            {
                "record_id": "r3",
                "latitude": "38.9",
                "longitude": "-77.0",
                "study_area": "a",
                "condition": "Fair",
                "year_inspected": "2016",
                "image_count": "0",
                "coverage_available": "0",
            },
        ]
        target = [
            {"record_id": "r1", "predicted_label": "ramp_present", "confidence": ".9"},
            {"record_id": "r2", "predicted_label": "abstain", "confidence": "0"},
            {"record_id": "r3", "predicted_label": "abstain", "confidence": "0"},
        ]
        points = build_points(candidates, [], target, [])
        self.assertEqual(points[0]["review_code"], "inventory_model_disagreement")
        self.assertEqual(points[1]["review_code"], "model_abstained")
        self.assertEqual(points[2]["review_code"], "imagery_unavailable")

    def test_render_accepts_resolved_truth_wording(self):
        page = render(
            [],
            human_label_name="Resolved human truth",
            human_note="Labels were reconciled under the frozen protocol.",
        )
        self.assertIn("Resolved human truth", page)
        self.assertIn("Labels were reconciled under the frozen protocol.", page)


if __name__ == "__main__":
    unittest.main()
