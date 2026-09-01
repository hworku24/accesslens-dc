import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.local_config import load_local_env  # noqa: E402


class LocalConfigTests(unittest.TestCase):
    def test_loads_value_without_overriding_existing_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("ACCESSLENS_TEST_VALUE=from-file\n", encoding="utf-8")
            os.environ["ACCESSLENS_TEST_VALUE"] = "existing"
            load_local_env(path)
            self.assertEqual(os.environ["ACCESSLENS_TEST_VALUE"], "existing")
            del os.environ["ACCESSLENS_TEST_VALUE"]


if __name__ == "__main__":
    unittest.main()
