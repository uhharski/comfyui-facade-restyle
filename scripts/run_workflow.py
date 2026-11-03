#!/usr/bin/env python3
"""Run one workflow headless against the already-running ComfyUI and measure it.

Needs the API-format export of the graph, which only ComfyUI's frontend can produce from a
UI-format JSON: in the UI use "Save (API format)" and put the file at

    workflows/_api/<workflow-file-name>.api.json

Without that file the script refuses and says so; it does not try to translate the graph
itself (the frontend's graph→prompt conversion is not reproducible outside the browser,
and a hand-written guess would silently measure a different workflow).

usage: python scripts/run_workflow.py krea2_edit
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

API_DIR = lib.WORKFLOWS / "_api"
OUT_DIR = lib.ROOT / "docs" / "metrics"


def post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow_id")
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()

    manifest = lib.load_manifest()
    entry = next((w for w in manifest["workflows"] if w["id"] == args.workflow_id), None)
    if entry is None:
        ids = ", ".join(w["id"] for w in manifest["workflows"])
        raise SystemExit(f"unknown workflow id {args.workflow_id!r}; known: {ids}")

    api_path = API_DIR / (Path(entry["file"]).stem + ".api.json")
    if not api_path.exists():
        print(f"no API-format export: {api_path}\n"
              f"open {entry['file']} in ComfyUI and use 'Save (API format)' into "
              f"workflows/_api/, then re-run.")
        return 2

    url = manifest["comfyui"]["url"].rstrip("/")
    try:
        before = lib.vram_snapshot(url)
    except Exception as exc:                                    # pragma: no cover
        raise SystemExit(f"ComfyUI is not reachable at {url}: {exc}")

    graph = json.loads(api_path.read_text(encoding="utf-8"))
    sampler = lib.VramSampler(interval=1.0)
    started = time.time()
    sampler.start()
    stats = {}
    hist = {}
    try:
        submitted = post_json(f"{url}/prompt", {"prompt": graph, "client_id": "measure"})
        prompt_id = submitted["prompt_id"]
        while time.time() - started < args.timeout:
            time.sleep(2.0)
            hist = get_json(f"{url}/history/{prompt_id}")
            if prompt_id in hist:
                break
        else:
            raise SystemExit("run timed out; see the ComfyUI console")
    finally:
        stats = sampler.stop()
    wall = round(time.time() - started, 1)
    after = lib.vram_snapshot(url)

    record = {
        "id": entry["id"],
        "api_graph": str(api_path),
        "prompt_id": prompt_id,
        "wall_seconds": wall,
        "vram_before": before, "vram_after": after,
        "conditions": manifest["conditions"],
        "at": dt.datetime.now().isoformat(timespec="seconds"),
        "outputs": list((hist.get(prompt_id, {}).get("outputs") or {}).keys()),
    }
    # peak whole-GPU used memory, sampled outside ComfyUI while it was running
    record["peak_gpu_used_mib"] = stats.get("peak_used_mib")
    record["vram_samples"] = stats.get("samples", 0)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"run_{entry['id']}_{dt.datetime.now():%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(record, indent=1, ensure_ascii=False))
    print(f"wrote {out}\nnow run: python scripts/collect_metrics.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
