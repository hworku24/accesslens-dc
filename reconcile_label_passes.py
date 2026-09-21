from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.evaluation import write_csv  # noqa: E402


FIRST_LABELS = ROOT / "data/labels/accesslens_pilot_labels_adjudicated.csv"
SECOND_LABELS = ROOT / "data/labels/accesslens_target_crop_labels.csv"
COMPARISON_OUTPUT = ROOT / "outputs/pilot_label_pass_comparison.csv"
VALID_LABELS = {"ramp_present", "ramp_absent", "cannot_determine"}


def project_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def evidence_adjusted_label(row: dict) -> str:
    label = row.get("truth_label", "")
    if label not in VALID_LABELS:
        raise ValueError(f"Invalid or missing truth label for {row.get('record_id', '<unknown>')}")
    if not row.get("image_ids") or row.get("image_quality") == "unusable":
        return "cannot_determine"
    return label


def compare_label_passes(first_rows: list[dict], second_rows: list[dict]) -> list[dict]:
    first_by_id = {row["record_id"]: row for row in first_rows}
    second_by_id = {row["record_id"]: row for row in second_rows}
    if set(first_by_id) != set(second_by_id):
        missing_second = sorted(set(first_by_id) - set(second_by_id))
        missing_first = sorted(set(second_by_id) - set(first_by_id))
        raise ValueError(
            f"Label-pass record mismatch; missing_second={missing_second}, "
            f"missing_first={missing_first}"
        )

    comparison: list[dict] = []
    for record_id, first in first_by_id.items():
        second = second_by_id[record_id]
        first_label = evidence_adjusted_label(first)
        second_label = evidence_adjusted_label(second)

        if first_label == second_label:
            provisional = first_label
            status = "resolved"
            basis = "passes_agree"
        elif first_label == "cannot_determine":
            provisional = second_label
            status = "resolved"
            basis = "target_crop_evidence_only"
        elif second_label == "cannot_determine":
            provisional = first_label
            status = "resolved"
            basis = "source_view_evidence_only"
        else:
            provisional = ""
            status = "manual_adjudication_required"
            basis = "direct_truth_conflict"

        comparison.append(
            {
                "record_id": record_id,
                "study_area": first.get("study_area", second.get("study_area", "")),
                "inventory_condition": first.get("inventory_condition", ""),
                "first_pass_truth_label": first_label,
                "first_pass_image_quality": first.get("image_quality", ""),
                "target_crop_truth_label": second_label,
                "target_crop_image_quality": second.get("image_quality", ""),
                "passes_agree": str(first_label == second_label).lower(),
                "provisional_truth_label": provisional,
                "resolution_status": status,
                "resolution_basis": basis,
                "first_pass_notes": first.get("notes", ""),
                "target_crop_notes": second.get("notes", ""),
                "manual_truth_label": "",
                "manual_adjudication_reason": "",
            }
        )
    return comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare blind source-view and target-crop labels")
    parser.add_argument("--first-labels", type=Path, default=FIRST_LABELS)
    parser.add_argument("--second-labels", type=Path, default=SECOND_LABELS)
    parser.add_argument("--output-file", type=Path, default=COMPARISON_OUTPUT)
    args = parser.parse_args()

    comparison = compare_label_passes(
        read_csv(project_path(args.first_labels)), read_csv(project_path(args.second_labels))
    )
    output_path = project_path(args.output_file)
    write_csv(comparison, output_path)
    conflicts = sum(row["resolution_status"] == "manual_adjudication_required" for row in comparison)
    agreement = sum(row["passes_agree"] == "true" for row in comparison)
    print(f"Compared {len(comparison)} records: {agreement} agreements, {conflicts} direct conflicts")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
