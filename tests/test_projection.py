import sys
import unittest
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.projection import panorama_to_perspective, target_crop_directional  # noqa: E402


class ProjectionTests(unittest.TestCase):
    def test_directional_crop_has_expected_size(self):
        image = np.zeros((800, 1200, 3), dtype=np.uint8)
        image[:, :600] = (0, 0, 255)
        crop = target_crop_directional(image, 10, output_size=518)
        self.assertEqual(crop.shape, (518, 518, 3))

    def test_directional_crop_rejects_target_outside_fov(self):
        image = np.zeros((800, 1200, 3), dtype=np.uint8)
        with self.assertRaises(ValueError):
            target_crop_directional(image, 50, assumed_horizontal_fov_degrees=90)

    def test_panorama_projection_has_expected_size(self):
        panorama = np.zeros((512, 1024, 3), dtype=np.uint8)
        panorama[:, :512] = (255, 0, 0)
        projection = panorama_to_perspective(panorama, center_yaw_degrees=0)
        self.assertEqual(projection.shape, (512, 768, 3))


if __name__ == "__main__":
    unittest.main()
