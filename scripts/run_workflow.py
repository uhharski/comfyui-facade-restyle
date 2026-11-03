#!/usr/bin/env python3
"""Run one workflow headless against the already-running ComfyUI and measure it.

Needs the API-format graph at

    workflows/_api/<workflow-file-name>.api.json

which `scripts/import_api_from_history.py` takes out of the server after one UI run (or the UI's
own File → Export (API), see workflows/_api/README.md). Without that file the script refuses; it
does not translate the graph itself, because the frontend's graph→prompt conversion is not
reproducible outside the browser and a hand-written guess would silently measure another
workflow.

    python scripts/run_workflow.py krea2_edit
    python scripts/run_workflow.py moss_inpaint --cold   # defined starting state first

What it records, and why each part exists:

* `files_written` — the images this run wrote, found by listing the output directory before and
  after. This is what ties a measurement to the table row. Neither the SaveImage counters nor the
  timestamps can do it: ComfyUI skips cached nodes (a run may write a depth_out with no
  depth_in), counters of different prefixes drift apart, and UI runs interleave with headless
  ones in the same queue.
* `queue_wait_seconds` / `execution_seconds` — wall time is split, because a submission waits
  behind whatever else is queued. Measured on 04.11: a Qwen submission showed 86.8 s of wall time
  while the server executed it in 2.37 s; the rest was waiting behind a UI generation. Quoting
  wall time as the cost of a method would have been wrong by a factor of ~37.
* `run_status`, `error` — read out of the history entry. A failed run writes no files, and
  without this a failure silently contributes its waiting time and somebody else's memory
  (the Qwen graph's MaskByTouch node refuses picks made on another picture, so its headless
  replay fails: that is a property of the graph, not of the measurement).
* `peak_gpu_used_mib` plus `vram_before` — whole-GPU used memory sampled from outside ComfyUI.
  `vram_before.vram_free_mib` is what makes a peak interpretable: the five runs measured on 04.11
  started with 10980 / 1389 / 4531 / 165 / 841 MiB free, so their peaks are not comparable until
  the starting state is defined. `--cold` asks the server to unload models and free memory first
  (`POST /free`, older servers: `POST /prompt` with the same body); what actually worked is
  recorded.
* `--cold` / warm: a cold run pays for loading the weights (Krea2: 61.5 s cold, 4.2 s warm), so
  both numbers are worth having — the honest cost of a 12 GB card is the cold one, the honest
  cost of "the method" is the warm one, and a single number is one of those two by accident.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
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
        return json.loads(r.read().decode())


def free_memory(url: str) -> dict:
    """Ask ComfyUI to unload models and empty its cache, so a cold run starts from a stated
    state. Two endpoint forms exist across versions; record which one the server accepted."""
    attempts = []
    for path, body in (("/free", {"unload_models": True, "free_memory": True}),
                       ("/prompt", {"unload_models": True, "free_memory": True})):
        try:
            post_json(url + path, body)
            attempts.append({"endpoint": path, "ok": True})
            return {"worked": path, "attempts": attempts}
        except Exception as exc:                                    # noqa: BLE001
            attempts.append({"endpoint": path, "ok": False, "error": str(exc)[:200]})
    return {"worked": None, "attempts": attempts}


def queue_state(url: str) -> tuple[list[str], list[str]]:
    """(prompt ids currently running, prompt ids waiting). Items are lists whose second element
    is the prompt id; parsed defensively because the shape has changed across versions."""
    q = get_json(f"{url}/queue")

    def ids(key: str) -> list[str]:
        out = []
        for item in q.get(key) or []:
            if isinstance(item, list) and len(item) > 1:
                out.append(str(item[1]))
            elif isinstance(item, dict):
                out.append(str(item.get("prompt_id") or ""))
        return [i for i in out if i]

    return ids("queue_running"), ids("queue_pending")


def read_status(entry: dict) -> tuple[str, list[str]]:
    st = entry.get("status") or {}
    messages, errors = [], []
    for msg in st.get("messages") or []:
        if isinstance(msg, list):
            kind, data = (msg + [{}])[:2]
            messages.append(str(kind))
            if kind == "execution_error" and isinstance(data, dict):
                errors.append({"node": data.get("node_id"), "type": data.get("node_type"),
                               "message": str(data.get("exception_message") or "")[:400]})
    return str(st.get("status_str") or ("completed" if entry.get("outputs") else "unknown")), errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow_id")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--cold", action="store_true",
                    help="unload models and clear the cache first, so the starting state is defined")
    ap.add_argument("--note", default="", help="free-text note stored with the record")
    args = ap.parse_args()

    manifest = lib.load_manifest()
    entry = next((w for w in manifest["workflows"] if w["id"] == args.workflow_id), None)
    if entry is None:
        ids = ", ".join(w["id"] for w in manifest["workflows"])
        raise SystemExit(f"unknown workflow id {args.workflow_id!r}; known: {ids}")

    api_path = API_DIR / (Path(entry["file"]).stem + ".api.json")
    if not api_path.exists():
        print(f"no API-format graph at {api_path}\n"
              f"either queue {entry['file']} in the UI once and run\n"
              f"  python scripts/import_api_from_history.py\n"
              f"(that takes the graph that really ran, out of the server history), or export it\n"
              f"by hand: ComfyUI menu File -> Export (API), save into workflows/_api/")
        return 2
    if entry.get("replay", {}).get("headless") == "blocked":
        print(f"{entry['id']} is marked not headless-replayable in workflows/manifest.json:\n"
              f"  {entry['replay'].get('why', 'no reason given')}\n"
              f"Running it anyway — the failure, if any, is recorded in the record.")

    url = manifest["comfyui"]["url"].rstrip("/")
    before_vram = lib.vram_snapshot(url)
    if before_vram.get("error"):            # vram_snapshot catches errors, it does not raise
        raise SystemExit(f"ComfyUI is not reachable at {url}: {before_vram['error']}\n"
                         "the scripts never start the server — start ComfyUI first")

    reset = free_memory(url) if args.cold else {"worked": None, "attempts": [],
                                                "skipped": "no --cold"}
    if args.cold:
        time.sleep(2.0)                      # let the unload settle before sampling
        before_vram = lib.vram_snapshot(url)
    files_before = lib.snapshot_output(manifest)
    graph = json.loads(api_path.read_text(encoding="utf-8"))

    sampler = lib.VramSampler(interval=1.0)
    t0 = time.time()
    started_wall = dt.datetime.now().isoformat(timespec="seconds")
    sampler.start()
    stats, hist, entry_data = {}, {}, {}
    queue_ahead = exec_started = None
    try:
        try:
            submitted = post_json(f"{url}/prompt", {"prompt": graph, "client_id": "measure"})
        except urllib.error.URLError as exc:
            raise SystemExit(f"could not submit to {url}/prompt: {exc}\n"
                             "the graph was not run, so no record was written") from exc
        prompt_id = submitted["prompt_id"]
        try:
            running, pending = queue_state(url)
            queue_ahead = len(running) + pending.index(prompt_id) + 1 if prompt_id in pending \
                else len(running)
        except Exception:
            queue_ahead = None
        while time.time() - t0 < args.timeout:
            time.sleep(2.0)
            if exec_started is None:
                try:
                    if prompt_id in queue_state(url)[0]:
                        exec_started = time.time()
                except Exception:
                    pass
            hist = get_json(f"{url}/history/{prompt_id}")
            if prompt_id in hist:
                entry_data = hist[prompt_id]
                break
        else:
            raise SystemExit(f"timed out after {args.timeout} s; see the ComfyUI console")
    finally:
        stats = sampler.stop()
    wall = round(time.time() - t0, 1)
    after_vram = lib.vram_snapshot(url)
    files_written = lib.new_files(files_before, lib.snapshot_output(manifest))

    run_status, errors = read_status(entry_data)
    queue_wait = round(exec_started - t0, 1) if exec_started else None
    record = {
        "id": entry["id"],
        "api_graph": str(api_path),
        "prompt_id": prompt_id,
        "started_at": started_wall,
        # wall = queue wait + execution. Keep it, but never call it the cost of a method.
        "wall_seconds": wall,
        "queue_wait_seconds": queue_wait,
        "queue_ahead_at_submit": queue_ahead,
        "execution_seconds": round(time.time() - exec_started, 1) if exec_started else None,
        "run_status": run_status,
        "error": errors,
        "cold_start": bool(args.cold),
        "memory_reset": reset,
        "files_written": files_written,
        "vram_before": before_vram, "vram_after": after_vram,
        "peak_gpu_used_mib": stats.get("peak_used_mib"),
        "vram_samples": stats.get("samples", 0),
        "conditions": manifest["conditions"],
        "at": dt.datetime.now().isoformat(timespec="seconds"),
        "note": args.note,
        "outputs": list((entry_data.get("outputs") or {}).keys()),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"run_{entry['id']}_{dt.datetime.now():%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: record[k] for k in
                      ("id", "prompt_id", "run_status", "wall_seconds", "queue_wait_seconds",
                       "execution_seconds", "peak_gpu_used_mib", "files_written")},
                     indent=1, ensure_ascii=False))
    if run_status != "success":
        print(f"\n⚠ the run did not succeed ({run_status}): {errors or 'see the ComfyUI console'}\n"
              f"  it wrote {len(files_written)} file(s); its wall time includes queue waiting and "
              f"its memory peak belongs to whatever was really on the card — do not quote it.")
    if not files_written:
        print("\n⚠ nothing new appeared in the output directory: the run was fully served from "
              "the execution cache, so it produced no new measurement.")
    print(f"wrote {out}\nnow run: python scripts/collect_metrics.py")
    return 0 if run_status == "success" and files_written else 1


if __name__ == "__main__":
    raise SystemExit(main())
