from __future__ import annotations

import csv
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .evaluation import haversine_meters


GRAPH_ENDPOINT = "https://graph.mapillary.com/images"


def bbox_around_point(latitude: float, longitude: float, radius_meters: float) -> tuple[float, float, float, float]:
    latitude_delta = radius_meters / 111_320.0
    longitude_delta = radius_meters / (111_320.0 * math.cos(math.radians(latitude)))
    return (
        longitude - longitude_delta,
        latitude - latitude_delta,
        longitude + longitude_delta,
        latitude + latitude_delta,
    )


def _read_csv(path: str | Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return [dict(row) for row in csv.DictReader(stream)]


def _write_csv(rows: list[dict], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output.write_text("", encoding="utf-8")
        return
    fields = list(rows[0])
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def query_images(
    latitude: float,
    longitude: float,
    token: str,
    radius_meters: float = 50,
    limit: int = 100,
    timeout_seconds: int = 30,
) -> list[dict]:
    bbox = bbox_around_point(latitude, longitude, radius_meters)
    params = {
        "access_token": token,
        "bbox": ",".join(f"{value:.7f}" for value in bbox),
        "limit": str(limit),
        "fields": "id,computed_geometry,captured_at,is_pano,compass_angle,camera_type,thumb_2048_url",
    }
    request = urllib.request.Request(
        f"{GRAPH_ENDPOINT}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": "AccessLens-DC/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Mapillary API returned HTTP {exc.code}: {body[:300]}") from exc
    return payload.get("data", [])


def bearing_degrees(
    source_latitude: float,
    source_longitude: float,
    target_latitude: float,
    target_longitude: float,
) -> float:
    source_latitude_rad = math.radians(source_latitude)
    target_latitude_rad = math.radians(target_latitude)
    longitude_delta = math.radians(target_longitude - source_longitude)
    y = math.sin(longitude_delta) * math.cos(target_latitude_rad)
    x = (
        math.cos(source_latitude_rad) * math.sin(target_latitude_rad)
        - math.sin(source_latitude_rad)
        * math.cos(target_latitude_rad)
        * math.cos(longitude_delta)
    )
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def angular_difference(first: float, second: float) -> float:
    return abs((first - second + 180) % 360 - 180)


def signed_angular_difference(target: float, source: float) -> float:
    return (target - source + 180) % 360 - 180


def _capture_iso(value: int | str | None) -> str:
    if value in (None, ""):
        return ""
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).isoformat()


def rank_images_for_record(record: dict, images: list[dict]) -> list[dict]:
    target_latitude = float(record["latitude"])
    target_longitude = float(record["longitude"])
    ranked: list[dict] = []
    for image in images:
        coordinates = (image.get("computed_geometry") or {}).get("coordinates") or []
        if len(coordinates) < 2:
            continue
        image_longitude = float(coordinates[0])
        image_latitude = float(coordinates[1])
        distance = haversine_meters(
            target_latitude,
            target_longitude,
            image_latitude,
            image_longitude,
        )
        target_bearing = bearing_degrees(
            image_latitude,
            image_longitude,
            target_latitude,
            target_longitude,
        )
        is_pano = bool(image.get("is_pano"))
        compass_angle = image.get("compass_angle")
        heading_difference = None
        if compass_angle not in (None, ""):
            heading_difference = angular_difference(float(compass_angle), target_bearing)
            signed_heading_difference = signed_angular_difference(
                target_bearing, float(compass_angle)
            )
        else:
            signed_heading_difference = None
        faces_target = is_pano or (
            heading_difference is not None and heading_difference <= 65
        )
        ranked.append(
            {
                **image,
                "image_latitude": image_latitude,
                "image_longitude": image_longitude,
                "distance_to_record_m": round(distance, 2),
                "bearing_to_record_deg": round(target_bearing, 2),
                "heading_difference_deg": round(heading_difference, 2)
                if heading_difference is not None
                else "",
                "signed_heading_difference_deg": round(signed_heading_difference, 2)
                if signed_heading_difference is not None
                else "",
                "faces_target": int(faces_target),
                "captured_at_iso": _capture_iso(image.get("captured_at")),
            }
        )
    return sorted(
        ranked,
        key=lambda image: (
            -image["faces_target"],
            image["distance_to_record_m"],
            -int(image.get("captured_at") or 0),
        ),
    )


def select_images_for_record(record: dict, images: list[dict], maximum: int = 2) -> list[dict]:
    ranked = rank_images_for_record(record, images)
    return ranked[:maximum]


def download_image(url: str, destination: str | Path, timeout_seconds: int = 45) -> None:
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "AccessLens-DC/0.1"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        output.write_bytes(response.read())


def run_coverage_check(
    candidate_path: str | Path,
    output_path: str | Path,
    token: str | None = None,
    max_points: int | None = None,
    delay_seconds: float = 0.1,
) -> list[dict]:
    token = token or os.environ.get("MAPILLARY_ACCESS_TOKEN")
    if not token:
        raise RuntimeError(
            "MAPILLARY_ACCESS_TOKEN is missing. Create a Mapillary developer token and export it in your shell."
        )

    candidates = _read_csv(candidate_path)
    if max_points is not None:
        candidates = candidates[:max_points]

    results: list[dict] = []
    for index, row in enumerate(candidates, start=1):
        images = query_images(
            float(row["latitude"]),
            float(row["longitude"]),
            token,
        )
        pano_count = sum(bool(image.get("is_pano")) for image in images)
        capture_times = [image.get("captured_at") for image in images if image.get("captured_at")]
        results.append(
            {
                **row,
                "image_count": len(images),
                "pano_count": pano_count,
                "non_pano_count": len(images) - pano_count,
                "newest_captured_at": max(capture_times) if capture_times else "",
                "oldest_captured_at": min(capture_times) if capture_times else "",
                "coverage_available": int(bool(images)),
            }
        )
        print(f"[{index}/{len(candidates)}] {row['record_id']}: {len(images)} images")
        if delay_seconds:
            time.sleep(delay_seconds)

    _write_csv(results, output_path)
    return results
