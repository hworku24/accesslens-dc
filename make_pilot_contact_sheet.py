from __future__ import annotations

import csv
import math
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "data/processed/mapillary_pilot_image_manifest.csv"
OUTPUT = ROOT / "outputs/pilot_contact_sheet.jpg"
CELL_WIDTH = 420
IMAGE_HEIGHT = 270
LABEL_HEIGHT = 72
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
    with MANIFEST.open(newline="", encoding="utf-8") as stream:
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
        line_one = f"{row['record_id'].replace('ADA_CurbRampPt_', 'Ramp ')} | {row['image_id']}"
        line_two = (
            f"{float(row['distance_to_record_m']):.1f}m | heading {row['heading_difference_deg'] or 'pano'} | "
            f"{row['captured_at_iso'][:10]}"
        )
        cv2.putText(cell, line_one, (8, IMAGE_HEIGHT - 42), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(cell, line_two, (8, IMAGE_HEIGHT - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        row_index = index // COLUMNS
        column_index = index % COLUMNS
        top = row_index * cell_height
        left = column_index * CELL_WIDTH
        sheet[top : top + IMAGE_HEIGHT, left : left + CELL_WIDTH] = cell
        cv2.putText(
            sheet,
            f"Pilot image {index + 1}/{len(rows)}",
            (left + 8, top + IMAGE_HEIGHT + 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (30, 48, 58),
            1,
            cv2.LINE_AA,
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUTPUT), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
