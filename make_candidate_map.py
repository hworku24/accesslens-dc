from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data/processed/mapillary_coverage_candidates.csv"
OUTPUT = ROOT / "outputs/candidate_map.html"


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    points = [
        {
            "record_id": row["record_id"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "condition": row["condition"],
            "study_area": row["study_area"],
            "year_inspected": row["year_inspected"],
        }
        for row in rows
    ]
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AccessLens DC candidate sample</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    html, body {{ height: 100%; margin: 0; font-family: Inter, system-ui, sans-serif; color: #12212b; }}
    .layout {{ display: grid; grid-template-columns: 320px 1fr; height: 100%; }}
    aside {{ padding: 24px; overflow: auto; background: #f4f1e8; border-right: 1px solid #d8d2c2; }}
    #map {{ height: 100%; }}
    h1 {{ font-size: 25px; margin: 0 0 8px; }}
    p {{ line-height: 1.45; }}
    .stat {{ font-size: 34px; font-weight: 700; margin: 22px 0 0; }}
    .legend-row {{ display: flex; gap: 9px; align-items: center; margin: 9px 0; }}
    .swatch {{ width: 12px; height: 12px; border-radius: 50%; }}
    .note {{ font-size: 12px; color: #52616b; margin-top: 28px; }}
    @media (max-width: 720px) {{ .layout {{ grid-template-columns: 1fr; grid-template-rows: auto 1fr; }} aside {{ padding: 16px; }} }}
  </style>
</head>
<body>
<div class="layout">
  <aside>
    <h1>AccessLens DC</h1>
    <p>Seeded curb-ramp inventory sample prepared for current-imagery QA.</p>
    <div class="stat">{len(points)}</div>
    <div>candidate records</div>
    <h2>2016 inventory condition</h2>
    <div class="legend-row"><span class="swatch" style="background:#15803d"></span>Good</div>
    <div class="legend-row"><span class="swatch" style="background:#dc2626"></span>Non-Compliant</div>
    <div class="legend-row"><span class="swatch" style="background:#d97706"></span>Fair</div>
    <div class="legend-row"><span class="swatch" style="background:#475569"></span>Missing</div>
    <p class="note">These colors describe the historical DDOT field. They are not current compliance findings. Street imagery will be labeled independently.</p>
  </aside>
  <div id="map"></div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const points = {json.dumps(points)};
const colors = {{"Good":"#15803d", "Non-Compliant":"#dc2626", "Fair":"#d97706", "Missing":"#475569"}};
const map = L.map('map').setView([38.90, -77.01], 12);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}}).addTo(map);
const bounds = [];
for (const point of points) {{
  const marker = L.circleMarker([point.latitude, point.longitude], {{
    radius: 5, color: '#fff', weight: 1, fillColor: colors[point.condition], fillOpacity: 0.9
  }}).addTo(map);
  marker.bindPopup(`<strong>${{point.record_id}}</strong><br>${{point.study_area}}<br>Inventory: ${{point.condition}} (${{point.year_inspected}})`);
  bounds.push([point.latitude, point.longitude]);
}}
if (bounds.length) map.fitBounds(bounds, {{padding: [25, 25]}});
</script>
</body>
</html>"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()

