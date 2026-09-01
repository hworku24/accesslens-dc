import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.image_quality import classify_quality, load_thresholds  # noqa: E402


class ImageQualityTests(unittest.TestCase):
    def setUp(self):
        self.thresholds = {
            "status": "test",
            "minimum_width": 640,
            "minimum_height": 480,
            "minimum_blur_variance": 60,
            "minimum_brightness": 35,
            "maximum_brightness": 220,
            "minimum_contrast": 25,
        }

    def test_good_image_passes(self):
        result = classify_quality(
            {"width": 1024, "height": 768, "blur_variance": 100, "mean_brightness": 120, "contrast": 40},
            self.thresholds,
        )
        self.assertEqual(result["quality_gate_pass"], 1)

    def test_multiple_failures_are_retained(self):
        result = classify_quality(
            {"width": 320, "height": 200, "blur_variance": 10, "mean_brightness": 20, "contrast": 5},
            self.thresholds,
        )
        self.assertEqual(result["quality_gate_pass"], 0)
        self.assertIn("blur", result["quality_rejection_reasons"])
        self.assertIn("too_dark", result["quality_rejection_reasons"])

    def test_invalid_brightness_range_is_rejected(self):
        bad = {**self.thresholds, "minimum_brightness": 230}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "thresholds.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_thresholds(path)


if __name__ == "__main__":
    unittest.main()
