import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from make_inventory_adjudication_app import disagreement_records, render  # noqa: E402


class InventoryAdjudicationAppTests(unittest.TestCase):
    def test_includes_only_scorable_inventory_disagreements(self):
        labels = [
            {
                "record_id": "r1",
                "study_area": "a",
                "year_inspected": "2016",
                "inventory_condition": "Fair",
                "truth_label": "ramp_absent",
            },
            {
                "record_id": "r2",
                "study_area": "a",
                "year_inspected": "2016",
                "inventory_condition": "Missing",
                "truth_label": "ramp_absent",
            },
            {
                "record_id": "r3",
                "study_area": "a",
                "year_inspected": "2016",
                "inventory_condition": "Good",
                "truth_label": "cannot_determine",
            },
        ]
        source = [
            {
                "record_id": "r1",
                "image_id": "i1",
                "image_path": "data/images/i1.jpg",
                "captured_at_iso": "2024-01-02T10:00:00+00:00",
            }
        ]
        records = disagreement_records(labels, source, [])
        self.assertEqual([row["record_id"] for row in records], ["r1"])
        self.assertEqual(records[0]["earliest_capture_date"], "2024-01-02")

    def test_render_keeps_unresolved_historical_cause(self):
        page = render([])
        self.assertIn("Historical cause unresolved", page)
        self.assertIn("imagery_insufficient", page)


if __name__ == "__main__":
    unittest.main()
