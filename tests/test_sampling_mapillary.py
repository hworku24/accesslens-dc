import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.mapillary import (  # noqa: E402
    angular_difference,
    bbox_around_point,
    rank_images_for_record,
)
from curb_ramp_eval.sampling import (  # noqa: E402
    point_in_bbox,
    sample_coverage_candidates,
    sample_one_per_stratum,
)


class SamplingAndMapillaryTests(unittest.TestCase):
    def test_point_in_bbox(self):
        self.assertTrue(point_in_bbox(-77.0, 38.9, [-77.1, 38.8, -76.9, 39.0]))
        self.assertFalse(point_in_bbox(-77.2, 38.9, [-77.1, 38.8, -76.9, 39.0]))

    def test_seeded_sample_is_repeatable(self):
        rows = [
            {
                "record_id": f"id-{index}",
                "longitude": -77.0,
                "latitude": 38.9,
                "condition": "Good",
            }
            for index in range(10)
        ]
        areas = {"area": {"bbox_wgs84": [-77.1, 38.8, -76.9, 39.0]}}
        first = sample_coverage_candidates(rows, areas, per_condition_per_area=4, seed=7)
        second = sample_coverage_candidates(rows, areas, per_condition_per_area=4, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 4)

    def test_pilot_has_one_record_per_stratum(self):
        rows = []
        for area in ("a", "b"):
            for condition in ("Good", "Missing"):
                for index in range(3):
                    rows.append(
                        {
                            "record_id": f"{area}-{condition}-{index}",
                            "study_area": area,
                            "condition": condition,
                        }
                    )
        pilot = sample_one_per_stratum(rows, seed=4)
        self.assertEqual(len(pilot), 4)
        self.assertEqual(
            len({(row["study_area"], row["condition"]) for row in pilot}),
            4,
        )

    def test_radius_bbox_contains_source_point(self):
        bbox = bbox_around_point(38.9, -77.0, 50)
        self.assertTrue(point_in_bbox(-77.0, 38.9, list(bbox)))
        self.assertLess(bbox[0], bbox[2])
        self.assertLess(bbox[1], bbox[3])

    def test_angular_difference_wraps_at_north(self):
        self.assertEqual(angular_difference(350, 10), 20)

    def test_facing_image_ranks_before_wrong_heading(self):
        record = {"latitude": 38.9, "longitude": -77.0}
        images = [
            {
                "id": "away",
                "computed_geometry": {"coordinates": [-77.0, 38.8999]},
                "compass_angle": 180,
                "captured_at": 2,
                "is_pano": False,
            },
            {
                "id": "toward",
                "computed_geometry": {"coordinates": [-77.0, 38.8998]},
                "compass_angle": 0,
                "captured_at": 1,
                "is_pano": False,
            },
        ]
        ranked = rank_images_for_record(record, images)
        self.assertEqual(ranked[0]["id"], "toward")
        self.assertEqual(ranked[0]["faces_target"], 1)


if __name__ == "__main__":
    unittest.main()
