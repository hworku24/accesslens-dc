from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"


def read_csv(name: str) -> list[dict[str, str]]:
    with (PROCESSED / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class ScaleupReadinessTests(unittest.TestCase):
    def test_development_evidence_groups_are_complete_and_disjoint(self) -> None:
        candidates = read_csv("mapillary_scaleup_development_candidates.csv")
        coverage = read_csv("mapillary_scaleup_development_coverage.csv")
        manifest = read_csv("mapillary_scaleup_development_image_manifest.csv")
        crop_quality = read_csv("mapillary_scaleup_development_target_crop_quality.csv")

        candidate_ids = {row["record_id"] for row in candidates}
        covered_ids = {
            row["record_id"] for row in coverage if row["coverage_available"] == "1"
        }
        downloaded_ids = {row["record_id"] for row in manifest}
        usable_ids = {
            row["record_id"]
            for row in crop_quality
            if row["quality_gate_pass"] == "1"
        }
        groups = [
            usable_ids,
            candidate_ids - covered_ids,
            covered_ids - downloaded_ids,
            downloaded_ids - usable_ids,
        ]

        self.assertEqual(len(candidate_ids), 72)
        self.assertEqual(len(usable_ids), 55)
        self.assertEqual(set().union(*groups), candidate_ids)
        for left_index, left in enumerate(groups):
            for right in groups[left_index + 1 :]:
                self.assertFalse(left & right)


if __name__ == "__main__":
    unittest.main()
