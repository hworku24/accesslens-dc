from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


LABEL_FIELDS = [
    "record_id",
    "study_area",
    "latitude",
    "longitude",
    "inventory_condition",
    "year_inspected",
    "image_ids",
    "image_paths",
    "truth_label",
    "image_quality",
    "occlusion",
    "detectable_warning",
    "labeler",
    "label_timestamp",
    "notes",
]


def main() -> None:
    source = ROOT / "data/processed/mapillary_coverage_candidates.csv"
    destination = ROOT / "data/labels/curb_ramp_labels.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(
            f"Refusing to overwrite {destination}. Move it first if you need a fresh template."
        )
    with source.open(newline="", encoding="utf-8") as stream:
        candidates = list(csv.DictReader(stream))
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=LABEL_FIELDS)
        writer.writeheader()
        for row in candidates:
            writer.writerow(
                {
                    "record_id": row["record_id"],
                    "study_area": row["study_area"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "inventory_condition": row["condition"],
                    "year_inspected": row["year_inspected"],
                }
            )
    print(f"Wrote {len(candidates)} labeling rows to {destination}")


if __name__ == "__main__":
    main()
