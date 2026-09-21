from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent
CELL_WIDTH = 420
IMAGE_HEIGHT = 300
LABEL_HEIGHT = 66
COLUMNS = 3


def letterbox(image, width: int, height: int):
    scale = min(width / image.shape[1], height / image.shape[0])
    resized = cv2.resize(
        image,
        (max(1, round(image.shape[1] * scale)), max(1, round(image.shape[0] * scale))),
        interpolation=cv2.INTER_AREA,
    )
    canvas = np.full((height, width, 3), 24, dtype=np.uint8)
    top = (height - resized.shape[0]) // 2
    left = (width - resized.shape[1]) // 2
    canvas[top : top + resized.shape[0], left : left + resized.shape[1]] = resized
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a review sheet for derived target crops")
    parser.add_argument(
        "--manifest-file",
        type=Path,
        default=ROOT / "data/processed/mapillary_pilot_target_crop_manifest.csv",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=ROOT / "outputs/pilot_target_crop_contact_sheet.jpg",
    )
    args = parser.parse_args()
    manifest = args.manifest_file if args.manifest_file.is_absolute() else ROOT / args.manifest_file
    output = args.output_file if args.output_file.is_absolute() else ROOT / args.output_file
    with manifest.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    cell_height = IMAGE_HEIGHT + LABEL_HEIGHT
    sheet = np.full(
        (math.ceil(len(rows) / COLUMNS) * cell_height, COLUMNS * CELL_WIDTH, 3),
        245,
        dtype=np.uint8,
    )
    for index, row in enumerate(rows):
        image = cv2.imread(str(ROOT / row["image_path"]))
        if image is None:
            continue
        cell = letterbox(image, CELL_WIDTH, IMAGE_HEIGHT)
        record = row["record_id"].replace("ADA_CurbRampPt_", "Ramp ")
        method = row.get("projection_method", "crop")
        cv2.putText(cell, f"{record} | {row['image_id']}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(cell, method, (8, IMAGE_HEIGHT - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        grid_row = index // COLUMNS
        grid_column = index % COLUMNS
        top = grid_row * cell_height
        left = grid_column * CELL_WIDTH
        sheet[top : top + IMAGE_HEIGHT, left : left + CELL_WIDTH] = cell
        cv2.putText(sheet, f"Crop {index + 1}/{len(rows)}", (left + 8, top + IMAGE_HEIGHT + 34), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (30, 48, 58), 1, cv2.LINE_AA)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), sheet, [cv2.IMWRITE_JPEG_QUALITY, 91])
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
