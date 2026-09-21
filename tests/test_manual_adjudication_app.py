import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from make_manual_adjudication_app import conflict_records  # noqa: E402


class ManualAdjudicationAppTests(unittest.TestCase):
    def test_only_direct_conflicts_are_included(self):
        comparison = [
            {
                "record_id": "r1",
                "first_pass_truth_label": "ramp_present",
                "target_crop_truth_label": "ramp_absent",
                "resolution_status": "manual_adjudication_required",
            },
            {
                "record_id": "r2",
                "first_pass_truth_label": "ramp_present",
                "target_crop_truth_label": "ramp_present",
                "resolution_status": "resolved",
            },
        ]
        source = [{"record_id": "r1", "image_id": "s1", "image_path": "s.jpg"}]
        target = [{"record_id": "r1", "image_id": "t1", "image_path": "t.jpg"}]
        records = conflict_records(comparison, source, target)
        self.assertEqual([row["record_id"] for row in records], ["r1"])
        self.assertEqual(records[0]["source_images"][0]["image_id"], "s1")


if __name__ == "__main__":
    unittest.main()
