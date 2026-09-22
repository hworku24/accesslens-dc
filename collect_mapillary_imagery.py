from __future__ import annotations

import argparse
import csv
import os
import sys
import time
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.mapillary import (  # noqa: E402
    download_image,
    query_images,
    select_images_for_record,
)
from curb_ramp_eval.local_config import load_local_env  # noqa: E402


MANIFEST_FIELDS = [
    "record_id",
    "study_area",
    "inventory_condition",
    "record_latitude",
    "record_longitude",
    "image_id",
    "image_path",
    "image_latitude",
    "image_longitude",
    "captured_at",
    "captured_at_iso",
    "camera_type",
    "is_pano",
    "compass_angle",
    "distance_to_record_m",
    "bearing_to_record_deg",
    "heading_difference_deg",
    "signed_heading_difference_deg",
    "faces_target",
    "source",
    "attribution",
]


def project_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def write_manifest(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=MANIFEST_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    load_local_env(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Select and download Mapillary images for DDOT records")
    parser.add_argument("--max-points", type=int, default=None)
    parser.add_argument("--images-per-point", type=int, default=2)
    parser.add_argument("--radius-meters", type=float, default=50)
    parser.add_argument("--delay-seconds", type=float, default=0.15)
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Discard an existing manifest and query every candidate again",
    )
    parser.add_argument(
        "--candidate-file",
        type=Path,
        default=ROOT / "data/processed/mapillary_coverage_candidates.csv",
    )
    parser.add_argument(
        "--manifest-file",
        type=Path,
        default=ROOT / "data/processed/mapillary_image_manifest.csv",
    )
    parser.add_argument(
        "--image-root",
        type=Path,
        default=ROOT / "data/images/mapillary",
    )
    args = parser.parse_args()

    token = os.environ.get("MAPILLARY_ACCESS_TOKEN")
    if not token:
        raise RuntimeError(
            "MAPILLARY_ACCESS_TOKEN is missing. Export it locally; do not save it in the repository."
        )

    candidate_file = project_path(args.candidate_file)
    manifest_path = project_path(args.manifest_file)
    image_root = project_path(args.image_root)

    with candidate_file.open(newline="", encoding="utf-8") as stream:
        candidates = list(csv.DictReader(stream))
    if args.max_points is not None:
        candidates = candidates[: args.max_points]

    manifest: list[dict] = []
    if not args.no_resume and manifest_path.exists() and manifest_path.stat().st_size:
        with manifest_path.open(newline="", encoding="utf-8") as stream:
            manifest = list(csv.DictReader(stream))
    completed_ids = {row["record_id"] for row in manifest}

    for index, record in enumerate(candidates, start=1):
        if record["record_id"] in completed_ids:
            print(f"[{index}/{len(candidates)}] {record['record_id']}: resumed")
            continue
        if record.get("coverage_available") == "0":
            print(f"[{index}/{len(candidates)}] {record['record_id']}: no coverage")
            continue

        images = None
        for attempt in range(1, 4):
            try:
                images = query_images(
                    float(record["latitude"]),
                    float(record["longitude"]),
                    token,
                    radius_meters=args.radius_meters,
                )
                break
            except (TimeoutError, urllib.error.URLError) as exc:
                if attempt == 3:
                    raise RuntimeError(
                        f"Mapillary collection failed for {record['record_id']} after 3 attempts"
                    ) from exc
                wait_seconds = 2 ** (attempt - 1)
                print(
                    f"[{index}/{len(candidates)}] {record['record_id']}: "
                    f"attempt {attempt} failed; retrying in {wait_seconds}s"
                )
                time.sleep(wait_seconds)
        assert images is not None
        selected = select_images_for_record(record, images, maximum=args.images_per_point)
        saved = 0
        for image in selected:
            if not image.get("thumb_2048_url"):
                print(f"Skipping image {image.get('id', '<unknown>')}: no 2048 thumbnail URL")
                continue
            suffix = ".jpg"
            destination = image_root / record["record_id"] / f"{image['id']}{suffix}"
            download_image(image["thumb_2048_url"], destination)
            manifest.append(
                {
                    "record_id": record["record_id"],
                    "study_area": record["study_area"],
                    "inventory_condition": record["condition"],
                    "record_latitude": record["latitude"],
                    "record_longitude": record["longitude"],
                    "image_id": image["id"],
                    "image_path": destination.relative_to(ROOT),
                    "image_latitude": image["image_latitude"],
                    "image_longitude": image["image_longitude"],
                    "captured_at": image.get("captured_at", ""),
                    "captured_at_iso": image["captured_at_iso"],
                    "camera_type": image.get("camera_type", ""),
                    "is_pano": image.get("is_pano", ""),
                    "compass_angle": image.get("compass_angle", ""),
                    "distance_to_record_m": image["distance_to_record_m"],
                    "bearing_to_record_deg": image["bearing_to_record_deg"],
                    "heading_difference_deg": image["heading_difference_deg"],
                    "signed_heading_difference_deg": image["signed_heading_difference_deg"],
                    "faces_target": image["faces_target"],
                    "source": "Mapillary API",
                    "attribution": "Mapillary",
                }
            )
            saved += 1
        write_manifest(manifest, manifest_path)
        print(f"[{index}/{len(candidates)}] {record['record_id']}: saved {saved} images")
        if args.delay_seconds:
            time.sleep(args.delay_seconds)

    print(f"Wrote {len(manifest)} image records to {manifest_path}")


if __name__ == "__main__":
    main()
