from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASELINE_PATH = ROOT / "outputs/inventory_baseline/metrics.json"
MODEL_PATH = ROOT / "outputs/projectsidewalk_quantized_curb_ramp_dinov2_tiny_onnx/metrics.json"
ADJUDICATION_PATH = ROOT / "outputs/pilot_adjudication.csv"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def metric_row(report: dict, display_name: str) -> dict:
    overall = report["overall"]
    metrics = overall["metrics"]
    counts = overall["counts"]
    return {
        "model": display_name,
        "truth_records": counts["truth_records"],
        "scorable_records": counts["scorable_truth_records"],
        "answered_records": counts["answered"],
        "coverage": metrics["coverage"],
        "abstention_rate": metrics["abstention_rate"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "accuracy": metrics["accuracy"],
        "accuracy_ci_low": overall["intervals_95"]["accuracy"]["low"],
        "accuracy_ci_high": overall["intervals_95"]["accuracy"]["high"],
        "mean_latency_ms": report["latency_ms"]["mean"],
    }


def display(value) -> str:
    return "not estimable" if value is None else f"{float(value):.1%}"


def main() -> None:
    baseline = load_json(BASELINE_PATH)
    model = load_json(MODEL_PATH)
    adjudication = load_csv(ADJUDICATION_PATH)
    comparison = [
        metric_row(baseline, "DDOT 2016 inventory baseline"),
        metric_row(model, "Project Sidewalk DINOv2 validator"),
    ]
    comparison_path = ROOT / "outputs/pilot_model_comparison.csv"
    with comparison_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparison[0]))
        writer.writeheader()
        writer.writerows(comparison)

    primary_counts: dict[str, int] = {}
    for row in adjudication:
        code = row["primary_review_code"]
        primary_counts[code] = primary_counts.get(code, 0) + 1
    inventory_disagreements = [
        row for row in adjudication if row["inventory_agreement"] == "false"
    ]
    changed_labels = [
        row for row in adjudication if row["label_adjudication"] != "retained"
    ]

    baseline_row, model_row = comparison
    report = f"""# Sprint 2: pilot labeling and evaluation

Completed: 2026-09-01  
Evaluation seed: 20260901

## Outcome

The balanced 12-record pilot is complete. Eight records have adjudicated image-based
presence labels and four are `cannot_determine`, producing an imagery-insufficient rate
of 33.3 percent.

## Model comparison

| Model | Answered | Coverage | Precision | Recall | F1 | Accuracy | 95% accuracy interval | Mean latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DDOT 2016 inventory baseline | {baseline_row['answered_records']}/8 | {display(baseline_row['coverage'])} | {display(baseline_row['precision'])} | {display(baseline_row['recall'])} | {display(baseline_row['f1'])} | {display(baseline_row['accuracy'])} | {display(baseline_row['accuracy_ci_low'])} to {display(baseline_row['accuracy_ci_high'])} | 0 ms |
| Project Sidewalk DINOv2 validator | {model_row['answered_records']}/8 | {display(model_row['coverage'])} | {display(model_row['precision'])} | {display(model_row['recall'])} | {display(model_row['f1'])} | {display(model_row['accuracy'])} | {display(model_row['accuracy_ci_low'])} to {display(model_row['accuracy_ci_high'])} | {model_row['mean_latency_ms']:.1f} ms |

The validator answered one scorable record correctly. Its 100 percent answered-case
accuracy is not evidence of deployment performance because coverage was 12.5 percent
and the accuracy interval spans 20.7 to 100 percent. Precision, recall, and F1 cannot be
estimated from the single negative decision.

## Inventory disagreements

Three of eight scorable records disagreed with the 2016 inventory baseline:

{chr(10).join(f"- `{row['record_id']}`: inventory `{row['inventory_condition']}` implied `{row['inventory_prediction']}`, while current imagery was labeled `{row['adjudicated_truth_label']}`." for row in inventory_disagreements)}

These are review candidates. They do not prove an inventory error or physical world
change without an independent source or field inspection.

## Adjudication

- Raw labels received: 12
- Labels changed by the written evidence rule: {len(changed_labels)}
- Imagery insufficient: {primary_counts.get('imagery_insufficient', 0)}
- Possible world-change or inventory-review candidates: {primary_counts.get('possible_world_change', 0)}
- Ambiguous geometry or model abstention: {primary_counts.get('ambiguous_geometry', 0)}
- Records with full agreement: {primary_counts.get('no_disagreement', 0)}

`ADA_CurbRampPt_28492` was changed from `ramp_absent` to `cannot_determine` because the
human quality field was `unusable`. The raw export remains unchanged and the adjudicated
copy records the reason.

## Frozen pilot policy

- OpenCV gate: minimum 640 by 480, blur variance 60, brightness 35 to 220, contrast 25.
- Validator positive threshold: 0.70.
- Validator negative threshold: 0.30.
- Maximum directional heading difference: 35 degrees.
- Maximum camera distance: 35 meters.
- Panoramas abstain until a directional projection step is implemented.

The thresholds are frozen for the next evaluation batch. The high abstention rate will
not be reduced by tuning on held-out records.

## Sprint decision

The historical inventory remains useful as a high-recall baseline, with 62.5 percent
pilot accuracy and three false-positive presence assumptions. The cross-source validator
is not ready for deployment because its conservative eligible-view coverage is too low.
The next sprint should improve target-centered view construction, preserve the current
thresholds for held-out evaluation, and expand the labeled sample.
"""
    report_path = ROOT / "outputs/sprint2_pilot_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote {comparison_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
