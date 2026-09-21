import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reconcile_label_passes import compare_label_passes  # noqa: E402


def row(record_id: str, label: str, quality: str = "good", image_ids: str = "i1") -> dict:
    return {
        "record_id": record_id,
        "truth_label": label,
        "image_quality": quality,
        "image_ids": image_ids,
        "study_area": "area",
        "inventory_condition": "Good",
    }


class LabelReconciliationTests(unittest.TestCase):
    def test_agreement_is_resolved(self):
        result = compare_label_passes(
            [row("r1", "ramp_present")], [row("r1", "ramp_present")]
        )[0]
        self.assertEqual(result["provisional_truth_label"], "ramp_present")
        self.assertEqual(result["resolution_basis"], "passes_agree")

    def test_direct_truth_conflict_requires_manual_review(self):
        result = compare_label_passes(
            [row("r1", "ramp_present")], [row("r1", "ramp_absent")]
        )[0]
        self.assertEqual(result["provisional_truth_label"], "")
        self.assertEqual(result["resolution_status"], "manual_adjudication_required")

    def test_unusable_evidence_becomes_cannot_determine(self):
        result = compare_label_passes(
            [row("r1", "ramp_absent", quality="unusable")],
            [row("r1", "ramp_present")],
        )[0]
        self.assertEqual(result["provisional_truth_label"], "ramp_present")
        self.assertEqual(result["resolution_basis"], "target_crop_evidence_only")

    def test_record_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            compare_label_passes([row("r1", "ramp_present")], [row("r2", "ramp_present")])


if __name__ == "__main__":
    unittest.main()
