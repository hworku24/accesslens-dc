from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LABELS = ROOT / "data/labels/accesslens_pilot_labels_resolved.csv"
TARGET_PREDICTIONS = ROOT / "outputs/project_sidewalk_target_crops_pilot/predictions.csv"
INVENTORY_ADJUDICATIONS = ROOT / "data/labels/accesslens_inventory_disagreement_adjudications.csv"
OUTPUT_CSV = ROOT / "outputs/sprint4_adjudication_split.csv"
OUTPUT_REPORT = ROOT / "outputs/sprint4_adjudication_report.md"
ALLOWED_CATEGORIES = {
    "model_wrong",
    "world_changed",
    "inventory_error",
    "imagery_insufficient",
}


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def inventory_prediction(condition: str) -> str:
    return "ramp_absent" if condition == "Missing" else "ramp_present"


def expected_inventory_disagreements(labels: list[dict]) -> set[str]:
    return {
        row["record_id"]
        for row in labels
        if row["truth_label"] != "cannot_determine"
        and inventory_prediction(row["inventory_condition"]) != row["truth_label"]
    }


def validate_inventory_adjudications(labels: list[dict], rows: list[dict]) -> None:
    expected = expected_inventory_disagreements(labels)
    actual = {row["record_id"] for row in rows}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"Inventory adjudication IDs do not match; missing={missing}, extra={extra}")
    if len(actual) != len(rows):
        raise ValueError("Inventory adjudications contain duplicate record IDs")
    for row in rows:
        if row["adjudication_category"] not in ALLOWED_CATEGORIES - {"model_wrong"}:
            raise ValueError(f"Invalid inventory category for {row['record_id']}")
        if not row["adjudication_reason"].strip():
            raise ValueError(f"Missing adjudication reason for {row['record_id']}")


def build_split(
    labels: list[dict], predictions: list[dict], inventory_rows: list[dict]
) -> list[dict]:
    label_by_id = {row["record_id"]: row for row in labels}
    split = []
    for row in inventory_rows:
        split.append(
            {
                "case_id": f"{row['record_id']}::inventory",
                "record_id": row["record_id"],
                "case_type": "inventory_truth_disagreement",
                "adjudication_category": row["adjudication_category"],
                "detail_type": (
                    "historical_cause_unresolved"
                    if row["adjudication_category"] == "imagery_insufficient"
                    else row["adjudication_category"]
                ),
                "inventory_condition": row["inventory_condition"],
                "prediction": row["inventory_prediction"],
                "truth_label": row["resolved_truth_label"],
                "evidence_start": row["earliest_capture_date"],
                "evidence_end": row["latest_capture_date"],
                "adjudication_reason": row["adjudication_reason"],
            }
        )

    for row in predictions:
        label = label_by_id[row["record_id"]]
        truth = label["truth_label"]
        prediction = row["predicted_label"]
        if truth == "cannot_determine" or prediction == "abstain" or prediction == truth:
            continue
        split.append(
            {
                "case_id": f"{row['record_id']}::target_model",
                "record_id": row["record_id"],
                "case_type": "target_model_truth_disagreement",
                "adjudication_category": "model_wrong",
                "detail_type": "model_wrong",
                "inventory_condition": label["inventory_condition"],
                "prediction": prediction,
                "truth_label": truth,
                "evidence_start": "",
                "evidence_end": "",
                "adjudication_reason": (
                    f"Target-centered prediction {prediction} disagreed with resolved human truth {truth}."
                ),
            }
        )

    for row in labels:
        if row["truth_label"] != "cannot_determine":
            continue
        split.append(
            {
                "case_id": f"{row['record_id']}::evidence",
                "record_id": row["record_id"],
                "case_type": "truth_eligibility",
                "adjudication_category": "imagery_insufficient",
                "detail_type": "current_imagery_insufficient",
                "inventory_condition": row["inventory_condition"],
                "prediction": "",
                "truth_label": row["truth_label"],
                "evidence_start": "",
                "evidence_end": "",
                "adjudication_reason": (
                    "Both blind label passes resolved to cannot_determine under the frozen protocol."
                ),
            }
        )
    return sorted(split, key=lambda row: row["case_id"])


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_report(rows: list[dict]) -> str:
    categories = Counter(row["adjudication_category"] for row in rows)
    details = Counter(row["detail_type"] for row in rows)
    inventory_cases = sum(row["case_type"] == "inventory_truth_disagreement" for row in rows)
    model_cases = sum(row["case_type"] == "target_model_truth_disagreement" for row in rows)
    return f'''# Sprint 4: disagreement adjudication


## Review units

- Inventory-truth disagreements: {inventory_cases}
- Target-model errors: {model_cases}
- Current-imagery-insufficient records: {details['current_imagery_insufficient']}

One location can contribute more than one review unit when both the inventory and model
disagree with resolved truth.

## Frozen rubric split

| Category | Count |
|---|---:|
| Model wrong | {categories['model_wrong']} |
| World changed | {categories['world_changed']} |
| Inventory error | {categories['inventory_error']} |
| Imagery insufficient | {categories['imagery_insufficient']} |

The imagery-insufficient total contains {details['historical_cause_unresolved']} cases
where current imagery supports a present or absent label but cannot establish the cause
of a 2016 inventory disagreement. It also contains
{details['current_imagery_insufficient']} records where current imagery cannot support a
reliable present or absent label.

## Historical-cause decision

All five inventory disagreements remain unresolved. Their available captures date from
2019 through 2025, after the 2016 inventory year. No independent 2016 evidence is present,
so the pilot cannot separate later physical change from baseline inventory error.
'''


def main() -> None:
    labels = read_csv(LABELS)
    predictions = read_csv(TARGET_PREDICTIONS)
    inventory_rows = read_csv(INVENTORY_ADJUDICATIONS)
    validate_inventory_adjudications(labels, inventory_rows)
    split = build_split(labels, predictions, inventory_rows)
    write_csv(split, OUTPUT_CSV)
    OUTPUT_REPORT.write_text(render_report(split), encoding="utf-8")
    print(f"Wrote {OUTPUT_CSV} with {len(split)} review units")
    print(f"Wrote {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
