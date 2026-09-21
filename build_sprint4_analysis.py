from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LABELS = ROOT / "data/labels/accesslens_pilot_labels_resolved.csv"
SOURCE_PREDICTIONS = ROOT / "outputs/project_sidewalk_validator_pilot/predictions.csv"
TARGET_PREDICTIONS = ROOT / "outputs/project_sidewalk_target_crops_pilot/predictions.csv"
CSV_OUTPUT = ROOT / "outputs/sprint4_screening_costs.csv"
REPORT_OUTPUT = ROOT / "outputs/sprint4_screening_costs.md"
COST_RATIOS = (1, 5, 10)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def inventory_predictions(labels: list[dict]) -> list[dict]:
    return [
        {
            "record_id": row["record_id"],
            "predicted_label": (
                "ramp_absent" if row["inventory_condition"] == "Missing" else "ramp_present"
            ),
        }
        for row in labels
    ]


def screening_counts(labels: list[dict], predictions: list[dict]) -> dict:
    prediction_by_id = {row["record_id"]: row["predicted_label"] for row in predictions}
    counts = {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "abstentions": 0, "records": 0}
    for row in labels:
        truth = row["truth_label"]
        if truth == "cannot_determine":
            continue
        prediction = prediction_by_id.get(row["record_id"], "abstain")
        counts["records"] += 1
        if prediction == "abstain":
            counts["abstentions"] += 1

        actual_review = truth == "ramp_absent"
        routed_to_review = prediction in {"ramp_absent", "abstain"}
        if actual_review and routed_to_review:
            counts["tp"] += 1
        elif actual_review:
            counts["fn"] += 1
        elif routed_to_review:
            counts["fp"] += 1
        else:
            counts["tn"] += 1
    counts["field_reviews"] = counts["tp"] + counts["fp"]
    return counts


def cost_rows(models: list[tuple[str, dict]]) -> list[dict]:
    rows = []
    for model_name, counts in models:
        for false_negative_cost in COST_RATIOS:
            total_cost = counts["fp"] + false_negative_cost * counts["fn"]
            rows.append(
                {
                    "model": model_name,
                    "records": counts["records"],
                    "field_reviews": counts["field_reviews"],
                    "field_review_rate": counts["field_reviews"] / counts["records"],
                    "abstentions_routed_to_review": counts["abstentions"],
                    "true_review_flags": counts["tp"],
                    "wasted_field_visits_fp": counts["fp"],
                    "missed_absent_ramps_fn": counts["fn"],
                    "cleared_present_ramps_tn": counts["tn"],
                    "false_positive_cost": 1,
                    "false_negative_cost": false_negative_cost,
                    "weighted_cost": total_cost,
                    "weighted_cost_per_record": total_cost / counts["records"],
                }
            )
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_report(models: list[tuple[str, dict]], rows: list[dict]) -> str:
    lines = [
        "# Sprint 4: screening cost analysis",
        "",
        "",
        "## Operating rule",
        "",
        "A resolved `ramp_absent` record needs field review. A `ramp_absent` model decision or",
        "model abstention is routed to field review. A false positive wastes a field visit. A",
        "false negative misses an absent ramp. The cost units below are illustrative ratios, not",
        "dollar estimates.",
        "",
        "## Screening outcomes",
        "",
        "| Predictor | Field reviews | Review rate | True flags | Wasted visits | Missed absent ramps | Abstentions |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, counts in models:
        lines.append(
            f"| {name} | {counts['field_reviews']}/{counts['records']} | "
            f"{counts['field_reviews'] / counts['records']:.1%} | {counts['tp']} | "
            f"{counts['fp']} | {counts['fn']} | {counts['abstentions']} |"
        )
    lines.extend(
        [
            "",
            "## Cost sensitivity",
            "",
            "| Predictor | Miss cost | Weighted cost | Cost per record |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['model']} | {row['false_negative_cost']}x | "
            f"{row['weighted_cost']} | {row['weighted_cost_per_record']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The source-view model avoids missed absent ramps only by sending every scorable record",
            "to field review. The target-centered model reduces field visits but misses five of the",
            "seven absent ramps. The inventory baseline also misses five. None of the tested policies",
            "supports automated clearance on this pilot. Use the workflow to organize evidence and",
            "human review while collecting a larger labeled sample for model selection or training.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    labels = read_csv(LABELS)
    models = [
        ("DDOT 2016 inventory baseline", screening_counts(labels, inventory_predictions(labels))),
        ("Project Sidewalk source-view model", screening_counts(labels, read_csv(SOURCE_PREDICTIONS))),
        ("Project Sidewalk target-centered model", screening_counts(labels, read_csv(TARGET_PREDICTIONS))),
    ]
    rows = cost_rows(models)
    write_csv(rows, CSV_OUTPUT)
    REPORT_OUTPUT.write_text(render_report(models, rows), encoding="utf-8")
    print(f"Wrote {CSV_OUTPUT}")
    print(f"Wrote {REPORT_OUTPUT}")


if __name__ == "__main__":
    main()
