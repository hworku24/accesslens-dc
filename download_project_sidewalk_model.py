from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODEL_ID = "projectsidewalk/quantized_curb_ramp_dinov2_tiny_onnx"
MODEL_REVISION = "a9da393f2b41d72f5252ba9e50291168bdcfd668"
MODEL_ROOT = ROOT / "weights/projectsidewalk/quantized_curb_ramp_dinov2_tiny_onnx"
FILES = {
    "model_quantized.onnx": "onnx/model_quantized.onnx",
    "config.json": "config.json",
    "preprocessor_config.json": "preprocessor_config.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for local_name, remote_name in FILES.items():
        destination = MODEL_ROOT / local_name
        url = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{remote_name}"
        if not destination.exists():
            print(f"Downloading {local_name}")
            request = urllib.request.Request(url, headers={"User-Agent": "AccessLens-DC/0.1"})
            with urllib.request.urlopen(request, timeout=120) as response:
                destination.write_bytes(response.read())
        hashes[local_name] = sha256(destination)

    metadata = {
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "license": "MIT",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "files_sha256": hashes,
        "source": f"https://huggingface.co/{MODEL_ID}",
    }
    provenance_text = json.dumps(metadata, indent=2) + "\n"
    (MODEL_ROOT / "provenance.json").write_text(provenance_text, encoding="utf-8")
    tracked_provenance = ROOT / "data/processed/project_sidewalk_model_provenance.json"
    tracked_provenance.parent.mkdir(parents=True, exist_ok=True)
    tracked_provenance.write_text(provenance_text, encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
