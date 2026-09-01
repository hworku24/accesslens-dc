import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.inventory import audit_inventory  # noqa: E402


class InventoryAuditTests(unittest.TestCase):
    def test_audit_counts_and_duplicates(self):
        fixture = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-77.0, 38.9, 1]},
                    "properties": {
                        "GIS_ID": "one",
                        "CONDITION": "Good",
                        "YEAR_INSPECTED": 2016,
                        "STATUS": 1,
                        "INTERSECTION_ID": None,
                        "ESTIMATED_YEAR_OF_IMPROVEMENT": 2030,
                        "LAST_EDITED_DATE": "2024-01-01",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-77.1, 38.8, 2]},
                    "properties": {
                        "GIS_ID": "two",
                        "CONDITION": "Missing",
                        "YEAR_INSPECTED": 2016,
                        "STATUS": 1,
                        "INTERSECTION_ID": None,
                        "ESTIMATED_YEAR_OF_IMPROVEMENT": 2030,
                        "LAST_EDITED_DATE": "2024-01-01",
                    },
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.geojson"
            path.write_text(json.dumps(fixture), encoding="utf-8")
            audit = audit_inventory(path)

        self.assertEqual(audit.feature_count, 2)
        self.assertEqual(audit.condition_counts, {"Good": 1, "Missing": 1})
        self.assertEqual(audit.null_counts["INTERSECTION_ID"], 2)
        self.assertEqual(audit.duplicate_non_null_counts["GIS_ID"], 0)
        self.assertEqual(audit.coordinate_dimensions, {"3": 2})


if __name__ == "__main__":
    unittest.main()
