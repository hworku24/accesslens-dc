import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collect_mapillary_imagery import project_path  # noqa: E402


class CollectionTests(unittest.TestCase):
    def test_relative_output_is_resolved_inside_project(self):
        resolved = project_path(Path("data/images/example"))
        self.assertEqual(resolved, ROOT / "data/images/example")


if __name__ == "__main__":
    unittest.main()
