from __future__ import annotations

import csv
import html
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "data/processed/mapillary_pilot_image_manifest.csv"
OUTPUT = ROOT / "outputs/pilot_image_gallery.html"


def main() -> None:
    with MANIFEST.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    by_record: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_record[row["record_id"]].append(row)

    cards: list[str] = []
    for record_id, images in sorted(by_record.items()):
        image_tags = []
        for item in images:
            relative = "../" + item["image_path"]
            metadata = (
                f"Image {html.escape(item['image_id'])} · "
                f"{float(item['distance_to_record_m']):.1f} m · "
                f"heading Δ {item['heading_difference_deg'] or 'n/a'}° · "
                f"{html.escape(item['captured_at_iso'][:10])}"
            )
            image_tags.append(
                f'<figure><img src="{html.escape(relative)}" loading="lazy">'
                f'<figcaption>{metadata}</figcaption></figure>'
            )
        cards.append(
            '<section class="card">'
            f'<h2>{html.escape(record_id)}</h2>'
            f'<p>{html.escape(images[0]["study_area"])} · historical condition hidden during image review</p>'
            f'<div class="images">{"".join(image_tags)}</div>'
            '</section>'
        )

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AccessLens DC pilot imagery</title>
<style>
body{{margin:0;background:#eef1f2;color:#17252d;font-family:Inter,system-ui,sans-serif}}
header{{padding:28px 5vw;background:#143642;color:white}} main{{padding:24px 5vw;display:grid;gap:20px}}
.card{{background:white;border-radius:12px;padding:18px;box-shadow:0 4px 16px #0001}} h1,h2{{margin:0 0 8px}}
.card p{{color:#53636b}} .images{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}
figure{{margin:0}} img{{width:100%;height:330px;object-fit:contain;background:#111;border-radius:8px}}
figcaption{{font-size:12px;color:#53636b;padding-top:7px}} @media(max-width:800px){{.images{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>AccessLens DC</h1><div>Balanced pilot image review · {len(rows)} images · {len(by_record)} records</div></header>
<main>{''.join(cards)}</main></body></html>"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
