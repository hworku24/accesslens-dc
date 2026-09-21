from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COMPARISON = ROOT / "outputs/pilot_label_pass_comparison.csv"
SOURCE_MANIFEST = ROOT / "data/processed/mapillary_pilot_image_manifest.csv"
TARGET_MANIFEST = ROOT / "data/processed/mapillary_pilot_target_crop_manifest.csv"
OUTPUT = ROOT / "outputs/pilot_manual_adjudication_app.html"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


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


def conflict_records(
    comparison: list[dict], source_rows: list[dict], target_rows: list[dict]
) -> list[dict]:
    source_images = image_index(source_rows)
    target_images = image_index(target_rows)
    return [
        {
            "record_id": row["record_id"],
            "first_pass_truth_label": row["first_pass_truth_label"],
            "target_crop_truth_label": row["target_crop_truth_label"],
            "source_images": source_images.get(row["record_id"], []),
            "target_images": target_images.get(row["record_id"], []),
        }
        for row in comparison
        if row["resolution_status"] == "manual_adjudication_required"
    ]


def main() -> None:
    records = conflict_records(
        read_csv(COMPARISON), read_csv(SOURCE_MANIFEST), read_csv(TARGET_MANIFEST)
    )
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AccessLens DC manual adjudication</title>
<style>
:root{--ink:#14242c;--muted:#60717a;--paper:#f3f0e8;--teal:#075e63;--orange:#d96c22;--line:#d5d9d8}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,system-ui,sans-serif}
header{background:#12343b;color:white;padding:22px 4vw;display:flex;justify-content:space-between;gap:20px}h1{margin:0;font-size:25px}.sub{font-size:13px;color:#c8dcdd;margin-top:5px}
main{padding:24px 4vw 110px;max-width:1500px;margin:auto}.notice{background:#fff6dc;border-left:5px solid #d99b22;padding:13px 16px;margin-bottom:18px}
.record{background:white;border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 5px 18px #14242c12}h2{margin:0}.labels{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 20px}.pill{background:#eef2f2;border-radius:999px;padding:8px 12px;font-size:13px}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}.evidence{border:1px solid var(--line);border-radius:10px;padding:14px}.evidence h3{margin:0 0 12px}.images{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.image{background:#111;border-radius:8px;overflow:hidden}.image img{width:100%;height:300px;object-fit:contain;display:block}.caption{background:#1e292e;color:#dce5e8;padding:7px 9px;font-size:11px}
fieldset{border:0;padding:0;margin:24px 0}legend{font-weight:700;margin-bottom:10px}.choices{display:flex;gap:9px;flex-wrap:wrap}.choice,button{border:1px solid #aab4b7;background:white;color:var(--ink);border-radius:8px;padding:12px 15px;font-weight:650;cursor:pointer}.choice.selected{background:var(--teal);color:white;border-color:var(--teal)}label{display:grid;gap:7px;font-weight:650}textarea{font:inherit;min-height:90px;padding:10px;border:1px solid #aab4b7;border-radius:7px;resize:vertical}
.nav{position:fixed;bottom:0;left:0;right:0;background:white;border-top:1px solid var(--line);padding:13px 4vw;display:flex;justify-content:flex-end}.primary{background:var(--orange);border-color:var(--orange);color:white}
@media(max-width:850px){.columns,.images{grid-template-columns:1fr}.image img{height:260px}}
</style></head><body>
<header><div><h1>AccessLens DC</h1><div class="sub">Manual adjudication · inventory and model outputs remain hidden</div></div><div id="progress"></div></header>
<main><div class="notice"><strong>Decision rule:</strong> review both evidence sets. Choose the label best supported at the mapped corner and write a specific reason. Use cannot determine when neither set supports a reliable decision.</div><div id="app"></div></main>
<div class="nav"><button id="export" class="primary">Export adjudication CSV</button></div>
<script>
const records=__RECORDS__;const key='accesslens-manual-adjudication-v1';let answers=JSON.parse(localStorage.getItem(key)||'{}');let index=0;
const options=[['ramp_present','Ramp present'],['ramp_absent','Ramp absent'],['cannot_determine','Cannot determine']];
function esc(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function label(v){return ({ramp_present:'Ramp present',ramp_absent:'Ramp absent',cannot_determine:'Cannot determine'})[v]||v}
function images(items){return items.length?items.map(i=>`<div class="image"><img src="${esc(i.path)}"><div class="caption">${esc(i.captured_at)} · ${esc(i.image_id)}</div></div>`).join(''):'<p>No usable images.</p>'}
function complete(a){return Boolean(a?.truth_label&&a?.adjudication_reason?.trim())}
function save(){localStorage.setItem(key,JSON.stringify(answers));render()}
function render(){const r=records[index];answers[r.record_id]||={truth_label:'',adjudication_reason:''};const a=answers[r.record_id];document.getElementById('progress').textContent=`${records.filter(x=>complete(answers[x.record_id])).length}/${records.length} complete`;document.getElementById('app').innerHTML=`<section class="record"><h2>${esc(r.record_id)}</h2><div class="labels"><span class="pill">Source-view label: <b>${label(r.first_pass_truth_label)}</b></span><span class="pill">Target-crop label: <b>${label(r.target_crop_truth_label)}</b></span></div><div class="columns"><div class="evidence"><h3>Source views</h3><div class="images">${images(r.source_images)}</div></div><div class="evidence"><h3>Target-centered crops</h3><div class="images">${images(r.target_images)}</div></div></div><fieldset><legend>Final truth label</legend><div class="choices">${options.map(([v,t])=>`<button class="choice ${a.truth_label===v?'selected':''}" data-value="${v}">${t}</button>`).join('')}</div></fieldset><label>Adjudication reason<textarea id="reason" placeholder="State which evidence supports the final label and why.">${esc(a.adjudication_reason)}</textarea></label></section>`;document.querySelectorAll('[data-value]').forEach(b=>b.onclick=()=>{a.truth_label=b.dataset.value;save()});document.getElementById('reason').onchange=e=>{a.adjudication_reason=e.target.value;save()}}
function cell(v){const s=String(v??'');return /[",\\n]/.test(s)?'"'+s.replaceAll('"','""')+'"':s}
document.getElementById('export').onclick=()=>{const incomplete=records.filter(r=>!complete(answers[r.record_id]));if(incomplete.length){alert('Choose a final label and write a reason before export.');return}const fields=['record_id','first_pass_truth_label','target_crop_truth_label','truth_label','adjudication_reason'];const lines=[fields.join(',')];for(const r of records){const row={...r,...answers[r.record_id]};lines.push(fields.map(f=>cell(row[f])).join(','))}const blob=new Blob([lines.join('\\n')+'\\n'],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='accesslens_manual_adjudications.csv';a.click();URL.revokeObjectURL(a.href)};render();
</script></body></html>"""
    OUTPUT.write_text(page.replace("__RECORDS__", json.dumps(records)), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(records)} conflict records")


if __name__ == "__main__":
    main()
