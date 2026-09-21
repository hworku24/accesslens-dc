import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finish_sprint3 import resolve_labels, validate_second_pass  # noqa: E402


def label(record_id: str, truth: str, quality: str = "good") -> dict:
    return {
        "record_id": record_id,
        "truth_label": truth,
        "image_quality": quality,
        "occlusion": "none",
        "detectable_warning": "not_visible",
        "image_ids": "i1",
        "study_area": "area",
        "inventory_condition": "Good",
        "latitude": "38.9",
        "longitude": "-77.0",
        "year_inspected": "2016",
    }


class FinishSprint3Tests(unittest.TestCase):
    def test_second_pass_requires_all_supporting_fields(self):
        first = [label("r1", "ramp_present")]
        second = [label("r1", "ramp_present")]
        second[0]["occlusion"] = ""
        with self.assertRaises(ValueError):
            validate_second_pass(first, second)

    def test_manual_conflict_requires_reason(self):
        first = [label("r1", "ramp_present")]
        second = [label("r1", "ramp_absent")]
        comparison = [
            {
                "record_id": "r1",
                "first_pass_truth_label": "ramp_present",
                "target_crop_truth_label": "ramp_absent",
                "first_pass_image_quality": "good",
                "target_crop_image_quality": "good",
                "passes_agree": "false",
                "provisional_truth_label": "",
                "resolution_status": "manual_adjudication_required",
                "resolution_basis": "direct_truth_conflict",
            }
        ]
        resolved, unresolved = resolve_labels(
            comparison,
            first,
            second,
            [{"record_id": "r1", "truth_label": "ramp_absent", "adjudication_reason": ""}],
        )
        self.assertEqual(resolved, [])
        self.assertEqual(unresolved, ["r1"])

    def test_manual_conflict_with_reason_is_resolved(self):
        first = [label("r1", "ramp_present")]
        second = [label("r1", "ramp_absent")]
        comparison = [
            {
                "record_id": "r1",
                "first_pass_truth_label": "ramp_present",
                "target_crop_truth_label": "ramp_absent",
                "first_pass_image_quality": "good",
                "target_crop_image_quality": "good",
                "passes_agree": "false",
                "provisional_truth_label": "",
                "resolution_status": "manual_adjudication_required",
                "resolution_basis": "direct_truth_conflict",
            }
        ]
        resolved, unresolved = resolve_labels(
            comparison,
            first,
            second,
            [
                {
                    "record_id": "r1",
                    "truth_label": "ramp_absent",
                    "adjudication_reason": "Target-centered view shows the full corner.",
                }
            ],
        )
        self.assertEqual(unresolved, [])
        self.assertEqual(resolved[0]["truth_label"], "ramp_absent")
        self.assertEqual(resolved[0]["resolution_basis"], "manual_adjudication")


if __name__ == "__main__":
    unittest.main()
