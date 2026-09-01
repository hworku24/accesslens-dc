import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from attach_images_to_labels import attach_images  # noqa: E402


class LabelingTests(unittest.TestCase):
    def test_attachment_preserves_existing_labels(self):
        labels = [
            {
                "record_id": "r1",
                "image_ids": "",
                "image_paths": "",
                "truth_label": "ramp_present",
            }
        ]
        manifest = [
            {"record_id": "r1", "image_id": "i1", "image_path": "data/images/i1.jpg"},
            {"record_id": "r1", "image_id": "i2", "image_path": "data/images/i2.jpg"},
        ]
        updated = attach_images(labels, manifest)
        self.assertEqual(updated[0]["image_ids"], "i1|i2")
        self.assertEqual(updated[0]["truth_label"], "ramp_present")


if __name__ == "__main__":
    unittest.main()

