import csv
import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.screening import (  # noqa: E402
    evaluate_screening,
    inventory_baseline_predictions,
    load_screening_predictions,
    load_truth_labels,
    wilson_interval,
)


class ScreeningTests(unittest.TestCase):
    def setUp(self):
        self.truth = [
            {"record_id": "1", "study_area": "a", "inventory_condition": "Good", "truth_label": "ramp_present"},
            {"record_id": "2", "study_area": "a", "inventory_condition": "Missing", "truth_label": "ramp_absent"},
            {"record_id": "3", "study_area": "a", "inventory_condition": "Fair", "truth_label": "cannot_determine"},
            {"record_id": "4", "study_area": "a", "inventory_condition": "Good", "truth_label": "ramp_absent"},
        ]

    def test_inventory_baseline_and_insufficient_truth(self):
        predictions = inventory_baseline_predictions(self.truth)
        result = evaluate_screening(self.truth, predictions)
        self.assertEqual(result["overall"]["counts"]["answered"], 3)
        self.assertEqual(result["overall"]["counts"]["cannot_determine"], 1)
        self.assertEqual(result["overall"]["counts"]["false_positive"], 1)
        self.assertAlmostEqual(result["overall"]["metrics"]["accuracy"], 2 / 3, places=4)

    def test_low_confidence_becomes_abstention(self):
        predictions = inventory_baseline_predictions(self.truth)
        predictions[0]["confidence"] = 0.4
        result = evaluate_screening(self.truth, predictions, confidence_threshold=0.7)
        self.assertEqual(result["overall"]["counts"]["abstained"], 1)
        self.assertEqual(result["overall"]["metrics"]["coverage"], 0.6667)

    def test_wilson_interval_contains_observed_rate(self):
        interval = wilson_interval(8, 10)
        self.assertLess(interval["low"], 0.8)
        self.assertGreater(interval["high"], 0.8)

    def test_invalid_label_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labels.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["record_id", "study_area", "inventory_condition", "truth_label"])
                writer.writeheader()
                writer.writerow({"record_id": "1", "study_area": "a", "inventory_condition": "Good", "truth_label": "maybe"})
            with self.assertRaises(ValueError):
                load_truth_labels(path)

    def test_blank_unfinished_rows_are_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labels.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["record_id", "study_area", "inventory_condition", "truth_label"])
                writer.writeheader()
                writer.writerow({"record_id": "1", "study_area": "a", "inventory_condition": "Good", "truth_label": "ramp_present"})
                writer.writerow({"record_id": "2", "study_area": "a", "inventory_condition": "Missing", "truth_label": ""})
            rows = load_truth_labels(path)
            self.assertEqual([row["record_id"] for row in rows], ["1"])

    def test_mixed_model_prediction_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "predictions.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=["record_id", "model_name", "predicted_label", "confidence"],
                )
                writer.writeheader()
                writer.writerow({"record_id": "1", "model_name": "model_a", "predicted_label": "ramp_present", "confidence": "0.9"})
                writer.writerow({"record_id": "2", "model_name": "model_b", "predicted_label": "ramp_absent", "confidence": "0.9"})
            with self.assertRaises(ValueError):
                load_screening_predictions(path)


if __name__ == "__main__":
    unittest.main()
