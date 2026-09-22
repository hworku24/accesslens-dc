import csv
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.mapillary import run_coverage_check  # noqa: E402


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class CoverageResumeTests(unittest.TestCase):
    def test_partial_output_is_checkpointed_and_resumed(self):
        candidates = [
            {
                "record_id": "a",
                "study_area": "x",
                "condition": "Good",
                "latitude": "38.9",
                "longitude": "-77.0",
            },
            {
                "record_id": "b",
                "study_area": "x",
                "condition": "Missing",
                "latitude": "38.9",
                "longitude": "-77.0",
            },
        ]
        image = {
            "id": "image",
            "computed_geometry": {"coordinates": [-77.0, 38.9]},
            "captured_at": 1,
            "is_pano": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            candidate_path = Path(directory) / "candidates.csv"
            output_path = Path(directory) / "coverage.csv"
            write_csv(candidate_path, candidates)
            with patch(
                "curb_ramp_eval.mapillary.query_images",
                side_effect=[[image], TimeoutError("stop")],
            ):
                with self.assertRaises(RuntimeError):
                    run_coverage_check(
                        candidate_path,
                        output_path,
                        token="test",
                        delay_seconds=0,
                        retry_attempts=1,
                    )
            with output_path.open(newline="", encoding="utf-8") as stream:
                partial = list(csv.DictReader(stream))
            self.assertEqual([row["record_id"] for row in partial], ["a"])

            with patch("curb_ramp_eval.mapillary.query_images", return_value=[] ) as query:
                result = run_coverage_check(
                    candidate_path,
                    output_path,
                    token="test",
                    delay_seconds=0,
                )
            self.assertEqual([row["record_id"] for row in result], ["a", "b"])
            self.assertEqual(query.call_count, 1)


if __name__ == "__main__":
    unittest.main()
