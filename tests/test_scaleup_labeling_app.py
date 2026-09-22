from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaleupLabelingAppTests(unittest.TestCase):
    def test_quality_filter_keeps_all_candidates_and_only_passing_images(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "scaleup_app.html"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "make_pilot_labeling_app.py"),
                    "--candidate-file",
                    "data/processed/mapillary_scaleup_development_candidates.csv",
                    "--manifest-file",
                    "data/processed/mapillary_scaleup_development_target_crop_quality.csv",
                    "--output-file",
                    str(output),
                    "--quality-passed-only",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            page = output.read_text(encoding="utf-8")
            self.assertIn("with 72 records and 88 images", result.stdout)
            self.assertEqual(page.count('"record_id": "ADA_CurbRampPt_'), 72)
            self.assertEqual(page.count('"image_id": "'), 88)
            self.assertEqual(page.count('"evidence_status": "usable_target_view"'), 55)
            self.assertEqual(page.count('"evidence_status": "no_eligible_target_view"'), 17)
            self.assertIn("eligible_image_count", page)


if __name__ == "__main__":
    unittest.main()
