from __future__ import annotations

import math
import time
from collections import defaultdict
from pathlib import Path


MODEL_NAME = "projectsidewalk_quantized_curb_ramp_dinov2_tiny_onnx"


def softmax_pair(first: float, second: float) -> tuple[float, float]:
    offset = max(first, second)
    first_exp = math.exp(first - offset)
    second_exp = math.exp(second - offset)
    denominator = first_exp + second_exp
    return first_exp / denominator, second_exp / denominator


def aggregate_record_scores(
    image_results: list[dict],
    present_probability: float,
    absent_probability: float,
) -> dict:
    usable = [row for row in image_results if row.get("inference_status") == "scored"]
    if not usable:
        return {
            "predicted_label": "abstain",
            "confidence": 0.0,
            "aggregation_reason": "no_eligible_images",
        }
    maximum_present = max(float(row["curb_ramp_probability"]) for row in usable)
    if maximum_present >= present_probability:
        return {
            "predicted_label": "ramp_present",
            "confidence": maximum_present,
            "aggregation_reason": "at_least_one_positive_view",
        }
    if maximum_present <= absent_probability:
        return {
            "predicted_label": "ramp_absent",
            "confidence": 1 - maximum_present,
            "aggregation_reason": "all_views_negative",
        }
    return {
        "predicted_label": "abstain",
        "confidence": max(maximum_present, 1 - maximum_present),
        "aggregation_reason": "probability_in_abstention_band",
    }


class OnnxCurbRampValidator:
    def __init__(self, model_path: str | Path):
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError(
                "ONNX Runtime is missing. Run: .venv/bin/python -m pip install -r requirements.txt"
            ) from exc
        self.session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name

    @staticmethod
    def preprocess(path: str | Path):
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("OpenCV and NumPy are required for inference") from exc

        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Could not read image: {path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image.shape[:2]
        scale = 256 / min(height, width)
        resized_width = round(width * scale)
        resized_height = round(height * scale)
        image = cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_CUBIC)
        left = (resized_width - 224) // 2
        top = (resized_height - 224) // 2
        image = image[top : top + 224, left : left + 224]
        image = image.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        image = (image - mean) / std
        return np.transpose(image, (2, 0, 1))[None, ...].astype(np.float32)

    def predict(self, path: str | Path) -> dict:
        tensor = self.preprocess(path)
        started = time.perf_counter()
        output = self.session.run(None, {self.input_name: tensor})[0]
        latency_ms = (time.perf_counter() - started) * 1000
        correct, incorrect = softmax_pair(float(output[0][0]), float(output[0][1]))
        return {
            "curb_ramp_probability": round(correct, 6),
            "incorrect_label_probability": round(incorrect, 6),
            "latency_ms": round(latency_ms, 3),
        }


def aggregate_all_records(
    candidate_rows: list[dict],
    image_results: list[dict],
    thresholds: dict,
) -> list[dict]:
    by_record: dict[str, list[dict]] = defaultdict(list)
    for row in image_results:
        by_record[row["record_id"]].append(row)
    predictions: list[dict] = []
    for candidate in candidate_rows:
        record_results = by_record.get(candidate["record_id"], [])
        decision = aggregate_record_scores(
            record_results,
            thresholds["present_probability"],
            thresholds["absent_probability"],
        )
        predictions.append(
            {
                "record_id": candidate["record_id"],
                "model_name": MODEL_NAME,
                **decision,
                "latency_ms": round(
                    sum(float(row.get("latency_ms") or 0) for row in record_results), 3
                ),
                "quality_gate_pass": int(
                    any(row.get("inference_status") == "scored" for row in record_results)
                ),
                "image_ids": "|".join(
                    row["image_id"]
                    for row in record_results
                    if row.get("inference_status") == "scored"
                ),
                "threshold_status": thresholds["status"],
            }
        )
    return predictions

