from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LABELS = ROOT / "data/labels/accesslens_pilot_labels_resolved.csv"
SOURCE_MANIFEST = ROOT / "data/processed/mapillary_pilot_image_manifest.csv"
TARGET_MANIFEST = ROOT / "data/processed/mapillary_pilot_target_crop_manifest.csv"
OUTPUT = ROOT / "outputs/sprint4_inventory_adjudication_app.html"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def inventory_prediction(condition: str) -> str:
    return "ramp_absent" if condition == "Missing" else "ramp_present"


def image_index(rows: list[dict]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        result[row["record_id"]].append(
            {
                "image_id": row["image_id"],
                "path": "../" + row["image_path"],
                "captured_at": row.get("captured_at_iso", "")[:10],
            }
        )
    return result


def disagreement_records(
    labels: list[dict], source_rows: list[dict], target_rows: list[dict]
) -> list[dict]:
    source_images = image_index(source_rows)
    target_images = image_index(target_rows)
    records = []
    for row in labels:
        truth = row["truth_label"]
        prediction = inventory_prediction(row["inventory_condition"])
        if truth == "cannot_determine" or prediction == truth:
            continue
        all_images = source_images.get(row["record_id"], []) + target_images.get(
            row["record_id"], []
        )
        dates = sorted({item["captured_at"] for item in all_images if item["captured_at"]})
        records.append(
            {
                "record_id": row["record_id"],
                "study_area": row["study_area"],
                "year_inspected": row["year_inspected"],
                "inventory_condition": row["inventory_condition"],
                "inventory_prediction": prediction,
                "resolved_truth_label": truth,
                "earliest_capture_date": dates[0] if dates else "",
                "latest_capture_date": dates[-1] if dates else "",
                "source_images": source_images.get(row["record_id"], []),
                "target_images": target_images.get(row["record_id"], []),
            }
        )
    return records


def render(records: list[dict]) -> str:
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AccessLens DC inventory disagreement review</title>
<style>
:root{--ink:#14242c;--muted:#60717a;--paper:#f3f0e8;--teal:#075e63;--orange:#d96c22;--line:#d5d9d8;--blue:#245a78}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,system-ui,sans-serif}
header{background:#12343b;color:white;padding:22px 4vw;display:flex;justify-content:space-between;gap:20px}h1{margin:0;font-size:25px}.sub{font-size:13px;color:#c8dcdd;margin-top:5px}
main{padding:24px 4vw 116px;max-width:1500px;margin:auto}.notice{background:#fff6dc;border-left:5px solid #d99b22;padding:13px 16px;margin-bottom:18px;line-height:1.45}
.record{background:white;border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 5px 18px #14242c12}h2{margin:0}.labels{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 20px}.pill{background:#eef2f2;border-radius:999px;padding:8px 12px;font-size:13px}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}.evidence{border:1px solid var(--line);border-radius:10px;padding:14px}.evidence h3{margin:0 0 12px}.images{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.image{background:#111;border-radius:8px;overflow:hidden}.image img{width:100%;height:300px;object-fit:contain;display:block}.caption{background:#1e292e;color:#dce5e8;padding:7px 9px;font-size:11px}
fieldset{border:0;padding:0;margin:24px 0}legend{font-weight:700;margin-bottom:10px}.guidance{font-size:13px;color:var(--muted);margin:0 0 12px}.choices{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.choice,button{border:1px solid #aab4b7;background:white;color:var(--ink);border-radius:8px;padding:12px 15px;font-weight:650;cursor:pointer;text-align:left}.choice small{display:block;font-weight:400;line-height:1.35;margin-top:5px;color:var(--muted)}.choice.selected{background:var(--teal);color:white;border-color:var(--teal)}.choice.selected small{color:#d7eeee}
label{display:grid;gap:7px;font-weight:650}textarea{font:inherit;min-height:90px;padding:10px;border:1px solid #aab4b7;border-radius:7px;resize:vertical}.nav{position:fixed;bottom:0;left:0;right:0;background:white;border-top:1px solid var(--line);padding:13px 4vw;display:flex;justify-content:space-between;gap:12px}.nav-group{display:flex;gap:8px}.primary{background:var(--orange);border-color:var(--orange);color:white}.nav button{text-align:center}
@media(max-width:900px){.columns,.images,.choices{grid-template-columns:1fr}.image img{height:260px}}
</style></head><body>
<header><div><h1>AccessLens DC</h1><div class="sub">Sprint 4 · inventory disagreement adjudication</div></div><div id="progress"></div></header>
<main><div class="notice"><strong>Evidence rule:</strong> current imagery supports the resolved present or absent label. It rarely proves why the 2016 inventory differs. Choose world changed or inventory error only when the images or independent dated evidence support that history. Otherwise choose historical cause unresolved.</div><div id="app"></div></main>
<div class="nav"><div class="nav-group"><button id="previous">Previous</button><button id="next">Next</button></div><button id="export" class="primary">Export adjudication CSV</button></div>
<script>
const records=__RECORDS__;const key='accesslens-inventory-adjudication-v1';let answers=JSON.parse(localStorage.getItem(key)||'{}');let index=0;
const options=[
 ['world_changed','World changed','Dated evidence supports a physical change after the 2016 inspection.'],
 ['inventory_error','Inventory error','Independent evidence supports a mismatch at the time of the 2016 record.'],
 ['imagery_insufficient','Historical cause unresolved','Current imagery supports the truth label but cannot establish the 2016 history.']
];
function esc(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function label(v){return ({ramp_present:'Ramp present',ramp_absent:'Ramp absent'})[v]||v}
function images(items){return items.length?items.map(i=>`<div class="image"><img src="${esc(i.path)}"><div class="caption">${esc(i.captured_at)} · ${esc(i.image_id)}</div></div>`).join(''):'<p>No images.</p>'}
function complete(a){return Boolean(a?.adjudication_category&&a?.adjudication_reason?.trim())}
function save(){localStorage.setItem(key,JSON.stringify(answers));render()}
function render(){const r=records[index];answers[r.record_id]||={adjudication_category:'',adjudication_reason:''};const a=answers[r.record_id];document.getElementById('progress').textContent=`${records.filter(x=>complete(answers[x.record_id])).length}/${records.length} complete · case ${index+1}`;document.getElementById('previous').disabled=index===0;document.getElementById('next').disabled=index===records.length-1;document.getElementById('app').innerHTML=`<section class="record"><h2>${esc(r.record_id)}</h2><div class="labels"><span class="pill">DDOT ${esc(r.year_inspected)}: <b>${esc(r.inventory_condition)}</b> (${label(r.inventory_prediction)})</span><span class="pill">Resolved truth: <b>${label(r.resolved_truth_label)}</b></span><span class="pill">Image dates: <b>${esc(r.earliest_capture_date)} to ${esc(r.latest_capture_date)}</b></span></div><div class="columns"><div class="evidence"><h3>Source views</h3><div class="images">${images(r.source_images)}</div></div><div class="evidence"><h3>Target-centered crops</h3><div class="images">${images(r.target_images)}</div></div></div><fieldset><legend>Why does the current truth differ from the 2016 inventory?</legend><p class="guidance">Use the conservative unresolved choice when the historical cause is not visible.</p><div class="choices">${options.map(([v,t,d])=>`<button class="choice ${a.adjudication_category===v?'selected':''}" data-value="${v}">${t}<small>${d}</small></button>`).join('')}</div></fieldset><label>Evidence note<textarea id="reason" placeholder="Name the visible evidence, relevant capture date, and any remaining uncertainty.">${esc(a.adjudication_reason)}</textarea></label></section>`;document.querySelectorAll('[data-value]').forEach(b=>b.onclick=()=>{a.adjudication_category=b.dataset.value;save()});document.getElementById('reason').onchange=e=>{a.adjudication_reason=e.target.value;save()}}
function cell(v){const s=String(v??'');return /[",\\n]/.test(s)?'"'+s.replaceAll('"','""')+'"':s}
document.getElementById('previous').onclick=()=>{if(index>0){index--;render()}};document.getElementById('next').onclick=()=>{if(index<records.length-1){index++;render()}};
document.getElementById('export').onclick=()=>{const incomplete=records.filter(r=>!complete(answers[r.record_id]));if(incomplete.length){alert('Choose a category and write an evidence note for every case before export.');return}const fields=['record_id','study_area','year_inspected','inventory_condition','inventory_prediction','resolved_truth_label','earliest_capture_date','latest_capture_date','adjudication_category','adjudication_reason'];const lines=[fields.join(',')];for(const r of records){const row={...r,...answers[r.record_id]};lines.push(fields.map(f=>cell(row[f])).join(','))}const blob=new Blob([lines.join('\\n')+'\\n'],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='accesslens_inventory_disagreement_adjudications.csv';a.click();URL.revokeObjectURL(a.href)};render();
</script></body></html>"""
    return page.replace("__RECORDS__", json.dumps(records).replace("</", "<\\/"))


def main() -> None:
    records = disagreement_records(
        read_csv(LABELS), read_csv(SOURCE_MANIFEST), read_csv(TARGET_MANIFEST)
    )
    OUTPUT.write_text(render(records), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(records)} inventory disagreement records")


if __name__ == "__main__":
    main()
