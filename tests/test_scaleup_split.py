import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from make_scaleup_split import make_split  # noqa: E402


class ScaleupSplitTests(unittest.TestCase):
    def make_rows(self):
        rows = []
        for area in ("a", "b"):
            for condition in ("Good", "Missing"):
                for index in range(10):
                    rows.append(
                        {
                            "record_id": f"{area}-{condition}-{index}",
                            "study_area": area,
                            "condition": condition,
                        }
                    )
        return rows

    def test_split_is_disjoint_balanced_and_excludes_pilot(self):
        rows = self.make_rows()
        pilot_ids = {"a-Good-0", "b-Missing-0"}
        development, held_out = make_split(
            rows,
            pilot_ids,
            seed=7,
            development_per_stratum=4,
            held_out_per_stratum=2,
        )
        development_ids = {row["record_id"] for row in development}
        held_out_ids = {row["record_id"] for row in held_out}
        self.assertFalse(development_ids & held_out_ids)
        self.assertFalse((development_ids | held_out_ids) & pilot_ids)
        self.assertEqual(
            set(Counter((row["study_area"], row["condition"]) for row in development).values()),
            {4},
        )
        self.assertEqual(
            set(Counter((row["study_area"], row["condition"]) for row in held_out).values()),
            {2},
        )

    def test_split_is_repeatable(self):
        first = make_split(self.make_rows(), set(), seed=11, development_per_stratum=3)
        second = make_split(self.make_rows(), set(), seed=11, development_per_stratum=3)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
