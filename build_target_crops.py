from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from curb_ramp_eval.mapillary import signed_angular_difference  # noqa: E402
from curb_ramp_eval.projection import (  # noqa: E402
    panorama_to_perspective,
    target_crop_directional,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Run this script with the project virtual environment") from exc

    parser = argparse.ArgumentParser(description="Build target-centered crops from Mapillary images")
    parser.add_argument(
        "--manifest-file",
        type=Path,
        default=ROOT / "data/processed/mapillary_pilot_image_manifest.csv",
    )
    parser.add_argument(
        "--output-manifest",
        type=Path,
        default=ROOT / "data/processed/mapillary_pilot_target_crop_manifest.csv",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "data/images/mapillary_pilot_target_crops",
    )
    parser.add_argument("--assumed-directional-hfov", type=float, default=90.0)
    parser.add_argument("--panorama-hfov", type=float, default=90.0)
    args = parser.parse_args()

    manifest_path = project_path(args.manifest_file)
    output_manifest = project_path(args.output_manifest)
    output_root = project_path(args.output_root)
    with manifest_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    crops: list[dict] = []
    rejected = 0
    for row in rows:
        source_path = ROOT / row["image_path"]
        image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
        if image is None:
            rejected += 1
            continue
        signed_heading = row.get("signed_heading_difference_deg")
        if signed_heading in (None, ""):
            if row.get("compass_angle") in (None, ""):
                rejected += 1
                continue
            signed_heading = signed_angular_difference(
                float(row["bearing_to_record_deg"]), float(row["compass_angle"])
            )
        signed_heading = float(signed_heading)
        source_is_pano = str(row.get("is_pano", "")).lower() in {"true", "1"}
        try:
            if source_is_pano:
                crop = panorama_to_perspective(
                    image,
                    center_yaw_degrees=signed_heading,
                    horizontal_fov_degrees=args.panorama_hfov,
                )
                method = "equirectangular_to_perspective"
                assumed_hfov = args.panorama_hfov
            else:
                crop = target_crop_directional(
                    image,
                    signed_heading_difference_degrees=signed_heading,
                    assumed_horizontal_fov_degrees=args.assumed_directional_hfov,
                )
                method = "directional_bearing_crop"
                assumed_hfov = args.assumed_directional_hfov
        except ValueError:
            rejected += 1
            continue

        destination = output_root / row["record_id"] / f"{row['image_id']}.jpg"
        destination.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(destination), crop, [cv2.IMWRITE_JPEG_QUALITY, 94])
        crops.append(
            {
                **row,
                "source_image_path": row["image_path"],
                "source_image_sha256": sha256(source_path),
                "image_path": str(destination.relative_to(ROOT)),
                "crop_sha256": sha256(destination),
                "projection_method": method,
                "assumed_horizontal_fov_degrees": assumed_hfov,
                "source_is_pano": int(source_is_pano),
                "is_pano": 0,
                "heading_difference_deg": 0,
                "signed_heading_difference_deg": 0,
            }
        )

    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    with output_manifest.open("w", newline="", encoding="utf-8") as stream:
        fields = sorted({field for row in crops for field in row})
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(crops)
    print(f"Wrote {len(crops)} target-centered crops to {output_manifest}; rejected {rejected}")


if __name__ == "__main__":
    main()
