from __future__ import annotations

import json
from pathlib import Path


def load_thresholds(path: str | Path) -> dict:
    thresholds = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {
        "status",
        "minimum_width",
        "minimum_height",
        "minimum_blur_variance",
        "minimum_brightness",
        "maximum_brightness",
        "minimum_contrast",
    }
    missing = required - set(thresholds)
    if missing:
        raise ValueError(f"Image-quality config is missing: {sorted(missing)}")
    if thresholds["minimum_brightness"] >= thresholds["maximum_brightness"]:
        raise ValueError("Minimum brightness must be below maximum brightness")
    return thresholds


def classify_quality(metrics: dict, thresholds: dict) -> dict:
    reasons: list[str] = []
    if metrics["width"] < thresholds["minimum_width"]:
        reasons.append("width_below_minimum")
    if metrics["height"] < thresholds["minimum_height"]:
        reasons.append("height_below_minimum")
    if metrics["blur_variance"] < thresholds["minimum_blur_variance"]:
        reasons.append("blur")
    if metrics["mean_brightness"] < thresholds["minimum_brightness"]:
        reasons.append("too_dark")
    if metrics["mean_brightness"] > thresholds["maximum_brightness"]:
        reasons.append("too_bright")
    if metrics["contrast"] < thresholds["minimum_contrast"]:
        reasons.append("low_contrast")
    return {
        "quality_gate_pass": int(not reasons),
        "quality_rejection_reasons": "|".join(reasons),
        "threshold_status": thresholds["status"],
    }


def inspect_image(path: str | Path) -> dict:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is not installed. Run: python3 -m pip install -r requirements.txt"
        ) from exc

    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"OpenCV could not read image: {path}")
    height, width = image.shape[:2]
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return {
        "width": int(width),
        "height": int(height),
        "mean_brightness": round(float(grayscale.mean()), 3),
        "contrast": round(float(grayscale.std()), 3),
        "blur_variance": round(float(cv2.Laplacian(grayscale, cv2.CV_64F).var()), 3),
    }

