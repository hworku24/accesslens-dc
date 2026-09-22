from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.image_quality import (  # noqa: E402
    classify_quality,
    inspect_image,
    load_thresholds,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit downloaded imagery with OpenCV")
    parser.add_argument(
        "--manifest-file",
        type=Path,
        default=ROOT / "data/processed/mapillary_image_manifest.csv",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=ROOT / "data/processed/image_quality_audit.csv",
    )
    parser.add_argument(
        "--quality-thresholds",
        type=Path,
        default=ROOT / "config/image_quality_thresholds.json",
    )
    args = parser.parse_args()
    manifest_path = args.manifest_file if args.manifest_file.is_absolute() else ROOT / args.manifest_file
    thresholds_path = (
        args.quality_thresholds
        if args.quality_thresholds.is_absolute()
        else ROOT / args.quality_thresholds
    )
    thresholds = load_thresholds(thresholds_path)
    with manifest_path.open(newline="", encoding="utf-8") as stream:
        manifest = list(csv.DictReader(stream))

    rows: list[dict] = []
    for item in manifest:
        metrics = inspect_image(ROOT / item["image_path"])
        decision = classify_quality(metrics, thresholds)
        rows.append({**item, **metrics, **decision})

    output = args.output_file if args.output_file.is_absolute() else ROOT / args.output_file
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        fields = sorted({field for row in rows for field in row})
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    passed = sum(row["quality_gate_pass"] for row in rows)
    print(f"Audited {len(rows)} images; {passed} passed provisional thresholds")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
