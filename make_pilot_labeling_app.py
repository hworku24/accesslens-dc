from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "data/processed/mapillary_pilot_candidates.csv"
MANIFEST = ROOT / "data/processed/mapillary_pilot_image_manifest.csv"
OUTPUT = ROOT / "outputs/pilot_labeling_app.html"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def project_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a blind AccessLens labeling app")
    parser.add_argument("--candidate-file", type=Path, default=CANDIDATES)
    parser.add_argument("--manifest-file", type=Path, default=MANIFEST)
    parser.add_argument("--output-file", type=Path, default=OUTPUT)
    parser.add_argument("--storage-key", default="accesslens-pilot-labels-v1")
    parser.add_argument("--export-filename", default="accesslens_pilot_labels.csv")
    parser.add_argument(
        "--quality-passed-only",
        action="store_true",
        help="Include only manifest rows whose quality_gate_pass value is 1",
    )
    parser.add_argument("--title", default="AccessLens DC")
    parser.add_argument(
        "--subtitle",
        default="Blind pilot labeling · historical inventory condition is hidden",
    )
    parser.add_argument(
        "--notice",
        default=(
            "Label the target record only when the corner is visible enough to judge. "
            "Use cannot_determine when the view is distant, blocked, aimed elsewhere, "
            "or geometrically ambiguous."
        ),
    )
    args = parser.parse_args()

    candidate_path = project_path(args.candidate_file)
    manifest_path = project_path(args.manifest_file)
    output_path = project_path(args.output_file)
    candidates = read_csv(candidate_path)
    manifest = read_csv(manifest_path)
    if args.quality_passed_only:
        if manifest and "quality_gate_pass" not in manifest[0]:
            parser.error("--quality-passed-only requires a quality_gate_pass column")
        manifest = [row for row in manifest if row["quality_gate_pass"] == "1"]
    images_by_record: dict[str, list[dict]] = defaultdict(list)
    for row in manifest:
        images_by_record[row["record_id"]].append(
            {
                "image_id": row["image_id"],
                "path": "../" + row["image_path"],
                "captured_at": row["captured_at_iso"],
                "distance_m": row["distance_to_record_m"],
                "heading_difference": row["heading_difference_deg"],
                "is_pano": row["is_pano"],
                "projection_method": row.get("projection_method", "source_image"),
            }
        )
    records = [
        {
            "record_id": row["record_id"],
            "study_area": row["study_area"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "inventory_condition": row["condition"],
            "year_inspected": row["year_inspected"],
            "evidence_status": (
                "usable_target_view"
                if images_by_record.get(row["record_id"], [])
                else "no_eligible_target_view"
            ),
            "images": images_by_record.get(row["record_id"], []),
        }
        for row in candidates
    ]
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__PAGE_TITLE__</title>
<style>
:root{--ink:#14242c;--muted:#60717a;--paper:#f3f0e8;--teal:#075e63;--orange:#d96c22;--line:#d5d9d8}
*{box-sizing:border-box} body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,system-ui,sans-serif}
header{background:#12343b;color:white;padding:22px 4vw;display:flex;justify-content:space-between;gap:20px;align-items:center}
h1{margin:0;font-size:25px}.sub{font-size:13px;color:#c8dcdd;margin-top:5px}.progress{font-weight:700}
main{padding:24px 4vw 100px;max-width:1400px;margin:auto}.notice{background:#fff6dc;border-left:5px solid #d99b22;padding:13px 16px;margin-bottom:18px}
.record{background:white;border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 5px 18px #14242c12}
.record-head{display:flex;justify-content:space-between;gap:16px;align-items:start}.record h2{margin:0 0 4px}.meta{color:var(--muted);font-size:13px}
.images{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:18px 0}.image{background:#111;border-radius:10px;overflow:hidden}.image img{width:100%;height:390px;object-fit:contain;display:block}.caption{background:#1e292e;color:#dce5e8;padding:8px 10px;font-size:12px}
.empty{padding:70px 20px;text-align:center;background:#eef1f1;color:var(--muted);border-radius:10px;margin:18px 0}
fieldset{border:0;padding:0;margin:20px 0}legend{font-weight:700;margin-bottom:10px}.choices{display:flex;flex-wrap:wrap;gap:9px}
button,.choice{border:1px solid #aab4b7;background:white;color:var(--ink);border-radius:8px;padding:11px 14px;font-weight:650;cursor:pointer}.choice.selected{background:var(--teal);color:white;border-color:var(--teal)}
.truth .choice{font-size:16px;padding:14px 18px}.form-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}label{display:grid;gap:6px;font-size:13px;font-weight:650}select,input,textarea{font:inherit;border:1px solid #aab4b7;border-radius:7px;padding:10px;background:white}textarea{width:100%;min-height:75px;resize:vertical}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid var(--line);padding:13px 4vw;display:flex;justify-content:space-between;align-items:center;z-index:5}.nav-group{display:flex;gap:9px}.primary{background:var(--orange);border-color:var(--orange);color:white}.status{font-size:13px;color:var(--muted)}
@media(max-width:800px){.images,.form-grid{grid-template-columns:1fr}.image img{height:280px}header{align-items:start;flex-direction:column}.nav .status{display:none}}
</style></head><body>
<header><div><h1 id="page-title"></h1><div class="sub" id="page-subtitle"></div></div><div class="progress" id="progress"></div></header>
<main><div class="notice"><strong>Evidence rule:</strong> <span id="evidence-rule"></span></div><div id="app"></div></main>
<div class="nav"><div class="nav-group"><button id="previous">← Previous</button><button id="next">Next →</button></div><div class="status" id="save-status">Saved locally in this browser</div><div class="nav-group"><button id="export" class="primary">Export labels CSV</button></div></div>
<script>
const records=__RECORDS__;
const pageConfig=__PAGE_CONFIG__;
const storageKey=pageConfig.storageKey;
document.getElementById('page-title').textContent=pageConfig.title;
document.getElementById('page-subtitle').textContent=pageConfig.subtitle;
document.getElementById('evidence-rule').textContent=pageConfig.notice;
let labels=JSON.parse(localStorage.getItem(storageKey)||'{}'); let index=0;
const truthOptions=[['ramp_present','Ramp present (1)'],['ramp_absent','Ramp absent (2)'],['cannot_determine','Cannot determine (3)']];
function current(){const r=records[index]; labels[r.record_id] ||= {truth_label:'',image_quality:'',occlusion:'',detectable_warning:'',labeler:'',notes:'',label_timestamp:''}; return [r,labels[r.record_id]]}
function save(){localStorage.setItem(storageKey,JSON.stringify(labels)); document.getElementById('save-status').textContent='Saved '+new Date().toLocaleTimeString(); updateProgress()}
function isComplete(l){return Boolean(l?.truth_label&&l?.image_quality&&l?.occlusion&&l?.detectable_warning)}
function updateProgress(){const done=records.filter(r=>isComplete(labels[r.record_id])).length; document.getElementById('progress').textContent=`${done}/${records.length} complete`}
function escapeHtml(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function imageHtml(i){const method=i.projection_method==='source_image'?'source view':i.projection_method.replaceAll('_',' ');return `<div class="image"><img src="${escapeHtml(i.path)}"><div class="caption">${escapeHtml(i.captured_at.slice(0,10))} · ${Number(i.distance_m).toFixed(1)} m · ${escapeHtml(method)}</div></div>`}
function selectHtml(field,values,value){return `<select data-field="${field}"><option value="">Select…</option>${values.map(v=>`<option ${v===value?'selected':''}>${v}</option>`).join('')}</select>`}
function render(){const [r,l]=current(); const images=r.images.length?r.images.map(imageHtml).join(''):'<div class="empty">No target view passed the frozen evidence gate. Label cannot determine.</div>';
document.getElementById('app').innerHTML=`<section class="record"><div class="record-head"><div><h2>${escapeHtml(r.record_id)}</h2><div class="meta">${escapeHtml(r.study_area.replaceAll('_',' '))} · record ${index+1} of ${records.length}</div></div><div class="meta">${r.images.length} image(s)</div></div><div class="images">${images}</div>
<fieldset class="truth"><legend>Truth label</legend><div class="choices">${truthOptions.map(([v,t])=>`<button class="choice ${l.truth_label===v?'selected':''}" data-truth="${v}">${t}</button>`).join('')}</div></fieldset>
<div class="form-grid"><label>Overall image quality${selectHtml('image_quality',['good','usable','poor','unusable'],l.image_quality)}</label><label>Occlusion${selectHtml('occlusion',['none','partial','severe','unknown'],l.occlusion)}</label><label>Detectable warning${selectHtml('detectable_warning',['visible','not_visible','cannot_determine'],l.detectable_warning)}</label></div>
<div class="form-grid" style="margin-top:14px"><label>Labeler<input data-field="labeler" value="${escapeHtml(l.labeler)}" placeholder="Your name"></label></div><label style="margin-top:14px">Notes<textarea data-field="notes" placeholder="What made this decision clear or uncertain?">${escapeHtml(l.notes)}</textarea></label></section>`;
document.querySelectorAll('[data-truth]').forEach(b=>b.onclick=()=>{l.truth_label=b.dataset.truth;l.label_timestamp=new Date().toISOString();save();render()});
document.querySelectorAll('[data-field]').forEach(el=>el.onchange=()=>{l[el.dataset.field]=el.value;save()}); document.getElementById('previous').disabled=index===0;document.getElementById('next').disabled=index===records.length-1;updateProgress()}
function move(delta){index=Math.max(0,Math.min(records.length-1,index+delta));render();scrollTo(0,0)}
document.getElementById('previous').onclick=()=>move(-1);document.getElementById('next').onclick=()=>move(1);
document.addEventListener('keydown',e=>{if(['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName))return;if(e.key==='1'||e.key==='2'||e.key==='3'){const [,l]=current();l.truth_label=truthOptions[Number(e.key)-1][0];l.label_timestamp=new Date().toISOString();save();render()}else if(e.key==='ArrowRight')move(1);else if(e.key==='ArrowLeft')move(-1)});
function csvCell(v){const s=String(v??'');return /[",\\n]/.test(s)?'"'+s.replaceAll('"','""')+'"':s}
document.getElementById('export').onclick=()=>{const incomplete=records.filter(r=>!isComplete(labels[r.record_id]));if(incomplete.length){alert(`Complete truth, image quality, occlusion, and detectable warning for every record before export. Missing: ${incomplete.map(r=>r.record_id).join(', ')}`);return}const fields=['record_id','study_area','latitude','longitude','inventory_condition','year_inspected','evidence_status','eligible_image_count','image_ids','image_paths','truth_label','image_quality','occlusion','detectable_warning','labeler','label_timestamp','notes'];const lines=[fields.join(',')];for(const r of records){const l=labels[r.record_id]||{};const row={...r,...l,eligible_image_count:r.images.length,image_ids:r.images.map(i=>i.image_id).join('|'),image_paths:r.images.map(i=>i.path.startsWith('../')?i.path.slice(3):i.path).join('|')};lines.push(fields.map(f=>csvCell(row[f])).join(','))}const blob=new Blob([lines.join('\\n')+'\\n'],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=pageConfig.exportFilename;a.click();URL.revokeObjectURL(a.href)};
render();
</script></body></html>"""
    page_config = {
        "storageKey": args.storage_key,
        "exportFilename": args.export_filename,
        "title": args.title,
        "subtitle": args.subtitle,
        "notice": args.notice,
    }
    rendered = page.replace("__PAGE_TITLE__", args.title)
    rendered = rendered.replace("__RECORDS__", json.dumps(records))
    rendered = rendered.replace("__PAGE_CONFIG__", json.dumps(page_config))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote {output_path} with {len(records)} records and {len(manifest)} images")


if __name__ == "__main__":
    main()
