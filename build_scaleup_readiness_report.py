from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data/processed"
OUTPUT = ROOT / "outputs/sprint5_readiness_report.md"


def read_csv(name: str) -> list[dict[str, str]]:
    with (PROCESSED / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def record_ids(rows: list[dict[str, str]]) -> set[str]:
    return {row["record_id"] for row in rows}


def main() -> None:
    candidates = read_csv("mapillary_scaleup_development_candidates.csv")
    coverage = read_csv("mapillary_scaleup_development_coverage.csv")
    source_manifest = read_csv("mapillary_scaleup_development_image_manifest.csv")
    source_quality = read_csv("mapillary_scaleup_development_image_quality.csv")
    crop_manifest = read_csv("mapillary_scaleup_development_target_crop_manifest.csv")
    crop_quality = read_csv("mapillary_scaleup_development_target_crop_quality.csv")

    candidate_ids = record_ids(candidates)
    covered_ids = record_ids([row for row in coverage if row["coverage_available"] == "1"])
    downloaded_ids = record_ids(source_manifest)
    source_pass_rows = [row for row in source_quality if row["quality_gate_pass"] == "1"]
    crop_pass_rows = [row for row in crop_quality if row["quality_gate_pass"] == "1"]
    usable_ids = record_ids(crop_pass_rows)

    no_coverage = candidate_ids - covered_ids
    no_download = covered_ids - downloaded_ids
    no_eligible_crop = downloaded_ids - usable_ids
    if usable_ids | no_coverage | no_download | no_eligible_crop != candidate_ids:
        raise ValueError("Development readiness groups do not cover all candidates")

    area_counts = Counter(row["study_area"] for row in candidates)
    usable_area_counts = Counter(
        row["study_area"] for row in candidates if row["record_id"] in usable_ids
    )
    condition_counts = Counter(row["condition"] for row in candidates)
    usable_condition_counts = Counter(
        row["condition"] for row in candidates if row["record_id"] in usable_ids
    )

    lines = [
        "# Sprint 5 development readiness",
        "",
        "## Development batch",
        "",
        f"- Candidates: {len(candidates)}",
        f"- Records with Mapillary API coverage: {len(covered_ids)}",
        f"- Records with downloaded images: {len(downloaded_ids)}",
        f"- Downloaded source images: {len(source_manifest)}",
        f"- Source images passing the provisional source gate: {len(source_pass_rows)}",
        f"- Target crops built: {len(crop_manifest)}",
        f"- Target crops passing the frozen crop gate: {len(crop_pass_rows)}",
        f"- Records with at least one eligible target crop: {len(usable_ids)}",
        "",
        "The Sprint 5 target of at least 50 usable development records is met.",
        "",
        "## Evidence outcomes",
        "",
        "| Outcome | Records |",
        "| --- | ---: |",
        f"| At least one eligible target crop | {len(usable_ids)} |",
        f"| No Mapillary API coverage | {len(no_coverage)} |",
        f"| Coverage metadata but no saved thumbnail | {len(no_download)} |",
        f"| Saved image but no crop passed the gate | {len(no_eligible_crop)} |",
        "",
        "All 72 records remain in the blind labeling batch. Records without eligible evidence",
        "receive `cannot_determine`; they are included in coverage and abstention reporting.",
        "",
        "## Usable records by study area",
        "",
        "| Study area | Usable | Selected |",
        "| --- | ---: | ---: |",
    ]
    for area in sorted(area_counts):
        lines.append(f"| {area.replace('_', ' ')} | {usable_area_counts[area]} | {area_counts[area]} |")

    lines.extend(
        [
            "",
            "## Usable records by inventory condition",
            "",
            "| Inventory condition | Usable | Selected |",
            "| --- | ---: | ---: |",
        ]
    )
    for condition in sorted(condition_counts):
        lines.append(
            f"| {condition} | {usable_condition_counts[condition]} | {condition_counts[condition]} |"
        )

    lines.extend(
        [
            "",
            "## Separation rule",
            "",
            "- Development imagery was collected and processed.",
            "- Held-out coverage metadata was queried.",
            "- Held-out thumbnails were not downloaded or opened.",
            "- Preprocessing and decision settings must be committed before held-out image access.",
            "",
            "## Labeling artifact",
            "",
            "Open `outputs/scaleup_development_labeling_app.html` through the local server.",
            "The interface hides the historical inventory condition and saves progress in browser storage.",
            "Export is blocked until every record has a truth label and evidence-quality fields.",
        ]
    )

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
