from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def attach_images(label_rows: list[dict], manifest_rows: list[dict]) -> list[dict]:
    images_by_record: dict[str, list[dict]] = defaultdict(list)
    for row in manifest_rows:
        images_by_record[row["record_id"]].append(row)
    output: list[dict] = []
    for row in label_rows:
        images = images_by_record.get(row["record_id"], [])
        output.append(
            {
                **row,
                "image_ids": "|".join(image["image_id"] for image in images),
                "image_paths": "|".join(image["image_path"] for image in images),
            }
        )
    return output


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    labels_path = ROOT / "data/labels/curb_ramp_labels.csv"
    manifest_path = ROOT / "data/processed/mapillary_image_manifest.csv"
    labels = read_csv(labels_path)
    manifest = read_csv(manifest_path)
    updated = attach_images(labels, manifest)
    temporary_path = labels_path.with_suffix(".csv.tmp")
    with temporary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(updated[0]))
        writer.writeheader()
        writer.writerows(updated)
    temporary_path.replace(labels_path)
    attached = sum(bool(row["image_ids"]) for row in updated)
    print(f"Attached imagery to {attached}/{len(updated)} label rows")


if __name__ == "__main__":
    main()

