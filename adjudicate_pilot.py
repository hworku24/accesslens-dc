from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.evaluation import write_csv  # noqa: E402


RAW_LABELS = ROOT / "data/labels/accesslens_pilot_labels.csv"
MODEL_PREDICTIONS = ROOT / "outputs/project_sidewalk_validator_pilot/predictions.csv"
ADJUDICATED_LABELS = ROOT / "data/labels/accesslens_pilot_labels_adjudicated.csv"
ADJUDICATION_REPORT = ROOT / "outputs/pilot_adjudication.csv"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def inventory_prediction(condition: str) -> str:
    return "ramp_absent" if condition == "Missing" else "ramp_present"


def adjudicate(labels: list[dict], model_predictions: list[dict]) -> tuple[list[dict], list[dict]]:
    model_by_id = {row["record_id"]: row for row in model_predictions}
    adjudicated_labels: list[dict] = []
    report: list[dict] = []

    for raw in labels:
        row = dict(raw)
        raw_truth = row["truth_label"]
        adjudicated_truth = raw_truth
        label_action = "retained"
        label_reason = ""

        if not row.get("image_ids") and raw_truth != "cannot_determine":
            adjudicated_truth = "cannot_determine"
            label_action = "changed_to_cannot_determine"
            label_reason = "no_images"
        elif row.get("image_quality") == "unusable" and raw_truth != "cannot_determine":
            adjudicated_truth = "cannot_determine"
            label_action = "changed_to_cannot_determine"
            label_reason = "unusable_images_cannot_support_presence_or_absence"

        row["raw_truth_label"] = raw_truth
        row["truth_label"] = adjudicated_truth
        row["label_adjudication"] = label_action
        row["label_adjudication_reason"] = label_reason
        adjudicated_labels.append(row)

        inventory_label = inventory_prediction(row["inventory_condition"])
        model = model_by_id.get(row["record_id"], {})
        model_label = model.get("predicted_label", "abstain")
        model_confidence = float(model.get("confidence") or 0)
        if model_confidence < 0.70:
            model_label = "abstain"

        inventory_agrees = (
            "not_scorable"
            if adjudicated_truth == "cannot_determine"
            else str(inventory_label == adjudicated_truth).lower()
        )
        model_agrees = (
            "not_scorable"
            if adjudicated_truth == "cannot_determine"
            else "abstain"
            if model_label == "abstain"
            else str(model_label == adjudicated_truth).lower()
        )

        if adjudicated_truth == "cannot_determine":
            primary_code = "imagery_insufficient"
        elif model_label != "abstain" and model_label != adjudicated_truth:
            primary_code = "model_error"
        elif inventory_label != adjudicated_truth:
            primary_code = "possible_world_change"
        elif model_label == "abstain":
            primary_code = "ambiguous_geometry"
        else:
            primary_code = "no_disagreement"

        report.append(
            {
                "record_id": row["record_id"],
                "study_area": row["study_area"],
                "inventory_condition": row["inventory_condition"],
                "raw_truth_label": raw_truth,
                "adjudicated_truth_label": adjudicated_truth,
                "image_quality": row.get("image_quality", ""),
                "label_adjudication": label_action,
                "label_adjudication_reason": label_reason,
                "inventory_prediction": inventory_label,
                "inventory_agreement": inventory_agrees,
                "model_prediction": model_label,
                "model_confidence": model_confidence,
                "model_agreement": model_agrees,
                "primary_review_code": primary_code,
                "review_qualification": (
                    "Requires independent evidence before asserting inventory error or world change."
                    if primary_code == "possible_world_change"
                    else ""
                ),
            }
        )

    return adjudicated_labels, report


def main() -> None:
    labels = read_csv(RAW_LABELS)
    predictions = read_csv(MODEL_PREDICTIONS)
    adjudicated_labels, report = adjudicate(labels, predictions)
    write_csv(adjudicated_labels, ADJUDICATED_LABELS)
    write_csv(report, ADJUDICATION_REPORT)
    changed = sum(row["label_adjudication"] != "retained" for row in report)
    print(f"Adjudicated {len(labels)} pilot labels; changed {changed}")
    print(f"Wrote {ADJUDICATED_LABELS}")
    print(f"Wrote {ADJUDICATION_REPORT}")


if __name__ == "__main__":
    main()
