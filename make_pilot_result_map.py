from __future__ import annotations

import csv
import html
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "data/processed/mapillary_pilot_coverage_results.csv"
SOURCE_PREDICTIONS = ROOT / "outputs/project_sidewalk_validator_pilot/predictions.csv"
TARGET_PREDICTIONS = ROOT / "outputs/project_sidewalk_target_crops_pilot/predictions.csv"
FIRST_PASS_LABELS = ROOT / "data/labels/accesslens_pilot_labels_adjudicated.csv"
OUTPUT = ROOT / "outputs/pilot_result_map.html"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def inventory_prediction(condition: str) -> str:
    return "ramp_absent" if condition == "Missing" else "ramp_present"


def build_points(
    candidates: list[dict],
    source_predictions: list[dict],
    target_predictions: list[dict],
    first_pass_labels: list[dict],
) -> list[dict]:
    source_by_id = {row["record_id"]: row for row in source_predictions}
    target_by_id = {row["record_id"]: row for row in target_predictions}
    label_by_id = {row["record_id"]: row for row in first_pass_labels}
    points: list[dict] = []

    for row in candidates:
        record_id = row["record_id"]
        source = source_by_id.get(record_id, {})
        target = target_by_id.get(record_id, {})
        label = label_by_id.get(record_id, {})
        target_label = target.get("predicted_label", "abstain")
        inventory_label = inventory_prediction(row["condition"])
        has_coverage = row.get("coverage_available") == "1"

        if not has_coverage:
            review_code = "imagery_unavailable"
        elif target_label == "abstain":
            review_code = "model_abstained"
        elif target_label != inventory_label:
            review_code = "inventory_model_disagreement"
        else:
            review_code = "inventory_model_agreement"

        points.append(
            {
                "record_id": record_id,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "study_area": row["study_area"],
                "inventory_condition": row["condition"],
                "inventory_prediction": inventory_label,
                "year_inspected": row["year_inspected"],
                "candidate_image_count": int(row.get("image_count") or 0),
                "coverage_available": has_coverage,
                "source_model_prediction": source.get("predicted_label", "abstain"),
                "target_model_prediction": target_label,
                "target_model_confidence": float(target.get("confidence") or 0),
                "first_pass_truth": label.get("truth_label", "pending"),
                "review_code": review_code,
                "view_changed_decision": source.get("predicted_label", "abstain")
                != target_label,
            }
        )
    return points


def render(
    points: list[dict],
    human_label_name: str = "First human pass",
    human_note: str = (
        "Human labels shown in popups come from the first source-view pass and remain "
        "provisional until target-crop adjudication is complete."
    ),
) -> str:
    counts = Counter(point["target_model_prediction"] for point in points)
    disagreements = sum(
        point["review_code"] == "inventory_model_disagreement" for point in points
    )
    coverage = sum(point["coverage_available"] for point in points)
    point_json = json.dumps(points).replace("</", "<\\/")
    human_label_json = json.dumps(human_label_name)
    human_note_html = html.escape(human_note)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AccessLens DC pilot screening map</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    :root {{ --ink:#14242c; --paper:#f4f1e8; --line:#d8d2c2; --teal:#087f8c; --orange:#d96724; --gray:#64748b; }}
    * {{ box-sizing:border-box; }} html, body {{ height:100%; margin:0; font-family:Inter,system-ui,sans-serif; color:var(--ink); }}
    .layout {{ display:grid; grid-template-columns:360px 1fr; height:100%; }}
    aside {{ padding:24px; overflow:auto; background:var(--paper); border-right:1px solid var(--line); }}
    #map {{ height:100%; }} h1 {{ font-size:26px; margin:0 0 8px; }} h2 {{ font-size:15px; margin:24px 0 10px; }}
    p {{ line-height:1.45; }} .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:20px 0; }}
    .stat {{ background:white; border:1px solid var(--line); border-radius:9px; padding:12px; }}
    .stat strong {{ display:block; font-size:25px; }} .stat span {{ font-size:12px; color:#5b6870; }}
    .legend-row {{ display:flex; gap:9px; align-items:center; margin:9px 0; font-size:14px; }}
    .swatch {{ width:12px; height:12px; border-radius:50%; flex:0 0 auto; }}
    .note {{ font-size:12px; color:#52616b; border-top:1px solid var(--line); padding-top:15px; margin-top:22px; }}
    .leaflet-popup-content {{ line-height:1.5; min-width:230px; }} .code {{ font-family:ui-monospace,monospace; font-size:11px; }}
    @media(max-width:760px) {{ .layout {{ grid-template-columns:1fr; grid-template-rows:auto 65vh; }} aside {{ padding:16px; }} }}
  </style>
</head>
<body>
<div class="layout">
  <aside>
    <h1>AccessLens DC</h1>
    <p>Pilot screening results for 12 DDOT curb-ramp inventory records.</p>
    <div class="grid">
      <div class="stat"><strong>{coverage}/12</strong><span>locations with imagery</span></div>
      <div class="stat"><strong>{counts['ramp_present'] + counts['ramp_absent']}/12</strong><span>target-model decisions</span></div>
      <div class="stat"><strong>{counts['abstain']}</strong><span>model abstentions</span></div>
      <div class="stat"><strong>{disagreements}</strong><span>inventory-model disagreements</span></div>
    </div>
    <h2>Target-centered model decision</h2>
    <div class="legend-row"><span class="swatch" style="background:var(--teal)"></span>Ramp present</div>
    <div class="legend-row"><span class="swatch" style="background:var(--orange)"></span>Ramp absent</div>
    <div class="legend-row"><span class="swatch" style="background:var(--gray)"></span>Abstain</div>
    <p class="note">Historical DDOT conditions were recorded in 2016. Model decisions screen records for review. They do not establish ADA or PROWAG compliance. {human_note_html}</p>
  </aside>
  <div id="map"></div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const points = {point_json};
const humanLabelName = {human_label_json};
const colors = {{ramp_present:'#087f8c', ramp_absent:'#d96724', abstain:'#64748b'}};
const labels = {{ramp_present:'Ramp present', ramp_absent:'Ramp absent', abstain:'Abstain', cannot_determine:'Cannot determine', pending:'Pending'}};
const map = L.map('map').setView([38.90,-77.01],12);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}}).addTo(map);
const bounds = [];
for (const point of points) {{
  const marker = L.circleMarker([point.latitude,point.longitude],{{radius:9,color:'#fff',weight:2,fillColor:colors[point.target_model_prediction],fillOpacity:.92}}).addTo(map);
  const confidence = point.target_model_prediction === 'abstain' ? 'n/a' : `${{(point.target_model_confidence*100).toFixed(1)}}%`;
  marker.bindPopup(`<strong>${{point.record_id}}</strong><br>${{point.study_area.replaceAll('_',' ')}}<br><br><b>DDOT 2016:</b> ${{point.inventory_condition}}<br><b>Candidate images:</b> ${{point.candidate_image_count}}<br><b>Source-view model:</b> ${{labels[point.source_model_prediction]}}<br><b>Target-centered model:</b> ${{labels[point.target_model_prediction]}} (${{confidence}})<br><b>${{humanLabelName}}:</b> ${{labels[point.first_pass_truth]}}<br><b>Review code:</b> <span class="code">${{point.review_code}}</span>`);
  bounds.push([point.latitude,point.longitude]);
}}
if (bounds.length) map.fitBounds(bounds,{{padding:[30,30]}});
</script>
</body>
</html>"""


def main() -> None:
    points = build_points(
        read_csv(CANDIDATES),
        read_csv(SOURCE_PREDICTIONS),
        read_csv(TARGET_PREDICTIONS),
        read_csv(FIRST_PASS_LABELS),
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(points), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(points)} records")


if __name__ == "__main__":
    main()
