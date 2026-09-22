from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.evaluation import write_csv, write_json  # noqa: E402
from curb_ramp_eval.screening import (  # noqa: E402
    evaluate_screening,
    inventory_baseline_predictions,
    load_screening_predictions,
)
from make_pilot_result_map import build_points, render  # noqa: E402
from reconcile_label_passes import compare_label_passes  # noqa: E402


FIRST_LABELS = ROOT / "data/labels/accesslens_pilot_labels_adjudicated.csv"
SECOND_LABELS = ROOT / "data/labels/accesslens_target_crop_labels.csv"
RESOLVED_LABELS = ROOT / "data/labels/accesslens_pilot_labels_resolved.csv"
MANUAL_RESOLUTIONS = ROOT / "data/labels/accesslens_manual_adjudications.csv"
COMPARISON_OUTPUT = ROOT / "outputs/pilot_label_pass_comparison.csv"
REPORT_OUTPUT = ROOT / "outputs/sprint3_pilot_report.md"
SOURCE_PREDICTIONS = ROOT / "outputs/project_sidewalk_validator_pilot/predictions.csv"
TARGET_PREDICTIONS = ROOT / "outputs/project_sidewalk_target_crops_pilot/predictions.csv"
PILOT_COVERAGE = ROOT / "data/processed/mapillary_pilot_coverage_results.csv"
RESULT_MAP = ROOT / "outputs/pilot_result_map.html"
STAKEHOLDER_MEMO = ROOT / "outputs/stakeholder_memo_sprint3.md"

VALID_TRUTH = {"ramp_present", "ramp_absent", "cannot_determine"}
VALID_QUALITY = {"good", "usable", "poor", "unusable"}
VALID_OCCLUSION = {"none", "partial", "severe", "unknown"}
VALID_WARNING = {"visible", "not_visible", "cannot_determine"}


def project_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def validate_second_pass(first_rows: list[dict], second_rows: list[dict]) -> None:
    first_ids = {row["record_id"] for row in first_rows}
    second_ids = [row.get("record_id", "") for row in second_rows]
    if len(second_rows) != len(first_rows):
        raise ValueError(
            f"Expected {len(first_rows)} second-pass rows; received {len(second_rows)}"
        )
    if len(set(second_ids)) != len(second_ids):
        raise ValueError("Second-pass labels contain duplicate record IDs")
    if set(second_ids) != first_ids:
        raise ValueError("Second-pass record IDs do not match the first pass")

    allowed = {
        "truth_label": VALID_TRUTH,
        "image_quality": VALID_QUALITY,
        "occlusion": VALID_OCCLUSION,
        "detectable_warning": VALID_WARNING,
    }
    for row in second_rows:
        for field, values in allowed.items():
            if row.get(field, "") not in values:
                raise ValueError(
                    f"Invalid or missing {field} for {row['record_id']}: {row.get(field, '')!r}"
                )


def manual_by_id(rows: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        record_id = row.get("record_id", "")
        if not record_id:
            continue
        if record_id in result:
            raise ValueError(f"Duplicate manual adjudication for {record_id}")
        result[record_id] = row
    return result


def resolve_labels(
    comparison: list[dict],
    first_rows: list[dict],
    second_rows: list[dict],
    manual_rows: list[dict],
) -> tuple[list[dict], list[str]]:
    first_by_id = {row["record_id"]: row for row in first_rows}
    second_by_id = {row["record_id"]: row for row in second_rows}
    manual = manual_by_id(manual_rows)
    unresolved: list[str] = []
    resolved: list[dict] = []

    for item in comparison:
        record_id = item["record_id"]
        truth = item["provisional_truth_label"]
        basis = item["resolution_basis"]
        reason = ""
        if item["resolution_status"] == "manual_adjudication_required":
            decision = manual.get(record_id, {})
            truth = decision.get("truth_label", "")
            reason = decision.get("adjudication_reason", "").strip()
            if truth not in VALID_TRUTH or not reason:
                unresolved.append(record_id)
                continue
            basis = "manual_adjudication"

        first = first_by_id[record_id]
        second = second_by_id[record_id]
        resolved.append(
            {
                "record_id": record_id,
                "study_area": first.get("study_area", second.get("study_area", "")),
                "latitude": first.get("latitude", second.get("latitude", "")),
                "longitude": first.get("longitude", second.get("longitude", "")),
                "inventory_condition": first.get("inventory_condition", ""),
                "year_inspected": first.get("year_inspected", ""),
                "truth_label": truth,
                "resolution_basis": basis,
                "adjudication_reason": reason,
                "first_pass_truth_label": item["first_pass_truth_label"],
                "target_crop_truth_label": item["target_crop_truth_label"],
                "first_pass_image_quality": item["first_pass_image_quality"],
                "target_crop_image_quality": item["target_crop_image_quality"],
                "first_pass_image_ids": first.get("image_ids", ""),
                "target_crop_image_ids": second.get("image_ids", ""),
            }
        )
    return resolved, unresolved


def write_evaluation(result: dict, output_dir: Path) -> None:
    report = {
        key: value for key, value in result.items() if key not in {"joined_rows", "review_queue"}
    }
    write_json(report, output_dir / "metrics.json")
    write_csv(result["joined_rows"], output_dir / "scored_records.csv")
    write_csv(result["review_queue"], output_dir / "review_queue.csv")


def display(value: float | None) -> str:
    return "not estimable" if value is None else f"{value:.1%}"


def metric_row(result: dict, name: str) -> str:
    overall = result["overall"]
    counts = overall["counts"]
    metrics = overall["metrics"]
    interval = overall["intervals_95"]["accuracy"]
    return (
        f"| {name} | {counts['answered']}/{counts['scorable_truth_records']} | "
        f"{display(metrics['coverage'])} | {display(metrics['precision'])} | "
        f"{display(metrics['recall'])} | {display(metrics['f1'])} | "
        f"{display(metrics['accuracy'])} | {display(interval['low'])} to "
        f"{display(interval['high'])} |"
    )


def build_report(
    comparison: list[dict], resolved: list[dict], evaluations: list[tuple[str, dict]]
) -> str:
    agreements = sum(row["passes_agree"] == "true" for row in comparison)
    conflicts = sum(
        row["resolution_status"] == "manual_adjudication_required" for row in comparison
    )
    cannot = sum(row["truth_label"] == "cannot_determine" for row in resolved)
    rows = "\n".join(metric_row(result, name) for name, result in evaluations)
    return f"""# Sprint 3: target-centered pilot evaluation

Completed: 2026-09-21

## Label reconciliation

- Records: {len(resolved)}
- Blind-pass agreements: {agreements}
- Direct truth conflicts: {conflicts}
- Final cannot-determine labels: {cannot}
- Scorable records: {len(resolved) - cannot}

Both raw label passes remain unchanged. Direct present-versus-absent conflicts require a
written manual decision under the frozen adjudication protocol.

## Model comparison

| Model | Answered | Coverage | Precision | Recall | F1 | Accuracy | 95% accuracy interval |
|---|---:|---:|---:|---:|---:|---:|---:|
{rows}

These pilot estimates have wide intervals and come from 12 locations. Report coverage,
abstention, and imagery insufficiency beside accuracy.

## Use boundary

The output prioritizes records for human review. It does not determine ADA or PROWAG
compliance. Geometry and tolerance decisions require calibrated measurement, field
inspection, or qualified professional review.
"""


def build_stakeholder_memo(
    comparison: list[dict], resolved: list[dict], baseline: dict, source: dict, target: dict
) -> str:
    agreements = sum(row["passes_agree"] == "true" for row in comparison)
    conflicts = sum(
        row["resolution_status"] == "manual_adjudication_required" for row in comparison
    )
    cannot = sum(row["truth_label"] == "cannot_determine" for row in resolved)
    target_metrics = target["overall"]["metrics"]
    target_counts = target["overall"]["counts"]
    baseline_metrics = baseline["overall"]["metrics"]
    source_metrics = source["overall"]["metrics"]
    return f"""# AccessLens DC stakeholder memo

Date: 2026-09-21

## Decision

AccessLens DC can organize inventory, imagery, quality checks, model decisions, and human
review in one repeatable workflow. The 12-location pilot is too small for an operational
performance claim. A larger labeled evaluation is the next decision point.

## Evidence

- DDOT records audited: 34,859
- Balanced pilot records: {len(resolved)}
- Blind label-pass agreements: {agreements}
- Direct label conflicts adjudicated: {conflicts}
- Final cannot-determine labels: {cannot}
- Final scorable records: {len(resolved) - cannot}
- Target-model answered records: {target_counts['answered']}
- Target-model coverage: {display(target_metrics['coverage'])}
- Target-model accuracy on answered records: {display(target_metrics['accuracy'])}
- Source-view model coverage: {display(source_metrics['coverage'])}
- Inventory baseline accuracy: {display(baseline_metrics['accuracy'])}

Accuracy describes answered, scorable records. Coverage and imagery insufficiency must
appear beside it.

## Use boundary

The output screens records for human review. It does not establish ADA or PROWAG
compliance. Slope, width, drainage, grade breaks, and tolerance decisions require
calibrated measurement, field inspection, or qualified professional review.

## Next work

1. Expand to at least 50 usable labeled locations across the frozen strata.
2. Separate development and held-out records before threshold changes.
3. Add a second reviewer and report agreement.
4. Investigate review-queue records with independent imagery or field evidence.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate labels and finish Sprint 3 scoring")
    parser.add_argument("labels_csv", type=Path, help="Export from the target-crop labeling app")
    parser.add_argument("--manual-resolutions", type=Path, default=MANUAL_RESOLUTIONS)
    args = parser.parse_args()

    first_rows = read_csv(FIRST_LABELS)
    second_rows = read_csv(project_path(args.labels_csv))
    validate_second_pass(first_rows, second_rows)
    write_csv(second_rows, SECOND_LABELS)

    comparison = compare_label_passes(first_rows, second_rows)
    write_csv(comparison, COMPARISON_OUTPUT)
    conflicts = [
        row for row in comparison if row["resolution_status"] == "manual_adjudication_required"
    ]
    manual_path = project_path(args.manual_resolutions)
    manual_rows = read_csv(manual_path) if manual_path.exists() else []
    resolved, unresolved = resolve_labels(comparison, first_rows, second_rows, manual_rows)

    if unresolved:
        if not manual_path.exists():
            write_csv(
                [
                    {
                        "record_id": row["record_id"],
                        "first_pass_truth_label": row["first_pass_truth_label"],
                        "target_crop_truth_label": row["target_crop_truth_label"],
                        "truth_label": "",
                        "adjudication_reason": "",
                    }
                    for row in conflicts
                ],
                manual_path,
            )
        print(f"Manual adjudication required for: {', '.join(unresolved)}")
        print(f"Complete {manual_path} and rerun this command")
        return 2

    write_csv(resolved, RESOLVED_LABELS)
    source_predictions = load_screening_predictions(SOURCE_PREDICTIONS)
    target_predictions = load_screening_predictions(TARGET_PREDICTIONS)
    baseline = evaluate_screening(resolved, inventory_baseline_predictions(resolved))
    source = evaluate_screening(resolved, source_predictions)
    target = evaluate_screening(resolved, target_predictions)
    output_root = ROOT / "outputs/sprint3_resolved"
    write_evaluation(baseline, output_root / "inventory_baseline")
    write_evaluation(source, output_root / "source_view_model")
    write_evaluation(target, output_root / "target_centered_model")
    REPORT_OUTPUT.write_text(
        build_report(
            comparison,
            resolved,
            [
                ("DDOT 2016 inventory baseline", baseline),
                ("Project Sidewalk source-view model", source),
                ("Project Sidewalk target-centered model", target),
            ],
        ),
        encoding="utf-8",
    )
    map_points = build_points(
        read_csv(PILOT_COVERAGE), source_predictions, target_predictions, resolved
    )
    RESULT_MAP.write_text(
        render(
            map_points,
            human_label_name="Resolved human truth",
            human_note=(
                "Human labels shown in popups were reconciled from blind source-view and "
                "target-crop passes under the frozen adjudication protocol."
            ),
        ),
        encoding="utf-8",
    )
    STAKEHOLDER_MEMO.write_text(
        build_stakeholder_memo(comparison, resolved, baseline, source, target),
        encoding="utf-8",
    )
    summary = {
        "records": len(resolved),
        "agreements": sum(row["passes_agree"] == "true" for row in comparison),
        "direct_conflicts": len(conflicts),
        "cannot_determine": sum(row["truth_label"] == "cannot_determine" for row in resolved),
    }
    print(json.dumps(summary, indent=2))
    print(f"Wrote {RESOLVED_LABELS}")
    print(f"Wrote {REPORT_OUTPUT}")
    print(f"Wrote {RESULT_MAP}")
    print(f"Wrote {STAKEHOLDER_MEMO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
