#!/usr/bin/env python3
"""Collect measurements for every workflow and rewrite the table in docs/metrics.md.

For each workflow in workflows/manifest.json it takes the newest saved depth-map pair
(produced by the instrumentation nodes inside the graphs, see _tools/add_instrumentation.py),
scores it with geometry_score.py, and adds the run time the graph itself recorded plus a
VRAM reading of the machine.

Nothing is generated here — it only reads what is already on disk and what the running
ComfyUI reports, so it can run while ComfyUI is busy or switched off.

usage:
    python scripts/collect_metrics.py            # newest pair per workflow
    python scripts/collect_metrics.py --pairs 3  # keep 3 newest pairs per workflow
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geometry_score  # noqa: E402
import lib  # noqa: E402

DOCS = lib.ROOT / "docs"
MEAS_JSON = DOCS / "metrics" / "measurements.json"
MEAS_MD = DOCS / "metrics.md"
RUN_GLOB = "run_*.json"      # timing/VRAM records written by scripts/run_workflow.py
START = "<!-- MEASUREMENTS:START (scripts/collect_metrics.py) -->"
END = "<!-- MEASUREMENTS:END -->"

HEADER_MD = """# Measurements (generated table at the bottom)

How to read this file
* the scale of these numbers was measured, not guessed — and there are TWO scales, do not mix
  them up:
  - **photos**, with this exact formula on the aerial photos of this project: identical = 1.00,
    nudged 1 % sideways = 0.81, nudged 4 % = 0.56, a different frame of the same flight ≈ 0.0
  - **depth maps**, which is what the rows below actually compare: they are far smoother, so
    the same nudges cost much less — on this source photo the depth probe measures 0.99 at 1 %
    and 0.95 at 4 %
  the `probe` columns are recomputed for every run from the input map itself, which is why the
  two scales do not invalidate each other: a row is read against its own probe, never against
  the other scale
* every row is ONE run whose depth maps were saved by the graph itself:
  `<prefix>_depth_in-*.png` (the real photo) and `<prefix>_depth_out-*.png` (the result)
* the numbers are defined in `scripts/geometry_score.py` — one identical formula for all
  methods, computed on the CPU after the generation, so the GPU is never involved
* the verdict separates the two things that a material swap changes differently:
  **global geometry** (same house, same place — `r` compared with the 1 % probe) and
  **local change** (`pixels off`, and the tile columns which catch a region repainted as a
  texture blob while the global number still looks fine). For this task a local change is
  wanted; held geometry without it means the method did nothing
* `flat tiles Δ` is how many of the 48 grid areas are flat in the result but were full of
  structure in the photo — the numerical shape of “the model smeared the facade over”
* `canvas of result` is read from the saved result image, not from the graph's widgets: a
  width/height widget in a saved workflow is frequently overridden by an incoming link, so
  the file that came out is the only trustworthy record of what was really generated
* ⚠ in the verdict column has two meanings, both spelled out in `docs/metrics/measurements.json`
  under `warning` / `pair_note`: either the two depth maps had different aspect ratios (the row
  is indicative only, not comparable with the other methods), or the result image had to be
  matched to the depth pair **by save time and aspect ratio instead of by counter** — the result
  node and the measurement nodes are separate SaveImage nodes with independent counters, and two
  graphs even save their result under another prefix. Measured here: a graph writes its result
  PNG 0–1 s before the depth map made from it, and a second later writes overlays and stitches
  built from it (once the nearest-in-time match was a 2052x576 stitch, not the 1024x576 render),
  so the choice keeps only candidates with the depth map's aspect ratio and takes the last one
  saved at or before it; `result_candidates` and the full note name everything that was skipped.
  Each graph's case is listed in `workflows/manifest.json` (`result_prefix_note`, and
  `result_pick` to pin a file explicitly)
* `no measurable depth change` in a verdict is judged by that run's own floor, not by a
  constant: the same bad-fraction measure on the input map against itself costs 0.0 at 0 %,
  1.6 % at a 1 % camera nudge, 3.1 % at 2 %, 6.0 % at 4 % (measured on this source photo). A
  method below half of the 1 % figure changed nothing in the depth map that a small viewpoint
  change would not also change. Two honest limits of that: a colour/material-only change is
  allowed to leave depth untouched, and a method that works only inside a small mask changes
  almost no pixels by construction — so this says the geometry test cannot see the edit, not
  that the edit is wrong. Whether the material looks right remains a separate, human check
* `run time (s)` and `peak GPU used` come from `scripts/run_workflow.py`, which posts the graph
    to `/prompt` and samples `nvidia-smi` from outside ComfyUI while it runs. A record is put in
    a row only when its run was going on at the moment that row's files were saved — times of a
    different execution of the same graph are listed in `measurements.json` under
    `other_run_records_of_this_graph`, not in the table. The graphs' own `LCTimer` node has
    recorded nothing (`lc_runs` is empty in all three), so until a headless run exists those two
    columns are dashes — that is a known gap, not a missing file. `peak GPU used` is whole-GPU
    used memory: whatever else was resident during that run counts too, and the conditions block
    of `measurements.json` says plainly that a local chat model sat on the same card
* `free VRAM at collect` is what ComfyUI reported it could see at collection time
* what each method conditions on is described in `workflows/index.md`

The methods are NOT forced to identical settings: samplers, steps and CFG belong to the
method, and the graphs generate at different sizes today — each row states its own canvas
instead of pretending they match.
"""

WANTED_SETTINGS = ("seed", "seed control", "base seed", "steps", "cfg", "sampler",
                   "scheduler", "denoise", "max_resolution", "custom width",
                   "custom height", "megapixels", "width", "height", "proportion",
                   "sigma shift", "depth resolution", "diffusion model", "checkpoint",
                   "text encoder", "vae", "lora", "lora strength", "input image",
                   "output prefix")


def settings_summary(prov: dict) -> dict:
    """Sampler parameters as the graph really has them (labels from lib.node_params)."""
    out: dict = {}
    for node in prov["nodes"]:
        for key, value in node["params"].items():
            if key in WANTED_SETTINGS:
                out.setdefault(key, value)
    return out


def image_size(path: Path) -> list[int] | None:
    try:
        from PIL import Image
        with Image.open(path) as img:
            return list(img.size)
    except Exception:
        return None


def headless_runs() -> list[dict]:
    """Run records of scripts/run_workflow.py: wall seconds and peak whole-GPU memory, measured
    from outside ComfyUI while that run was going on. Needed because the LCTimer node in the
    graphs has never recorded anything (`lc_runs` stays empty), so without these files the time
    and VRAM columns of the table can only be dashes.

    A record belongs to a table row only if the run was going on when that row's depth pair was
    saved — the timestamps must overlap, otherwise the time belongs to a different execution of
    the same graph and is not put in that row."""
    out = []
    for path in sorted((MEAS_JSON.parent).glob(RUN_GLOB)):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
            rec["_record"] = path.name
            out.append(rec)
        except Exception:
            continue
    return out


def match_timing(recs: list[dict], entry_id: str, captured_at: str) -> tuple[dict | None, list[dict]]:
    """(the record that overlaps this run's saved files, records of the same graph that do not)"""
    import datetime as _dt
    try:
        cap = _dt.datetime.fromisoformat(captured_at)
    except Exception:
        return None, [r for r in recs if r.get("id") == entry_id]
    mine, other = None, []
    for r in recs:
        if r.get("id") != entry_id:
            continue
        try:
            start = _dt.datetime.fromisoformat(r["at"]) - _dt.timedelta(seconds=float(r.get("wall_seconds", 0)))
            end = _dt.datetime.fromisoformat(r["at"])
        except Exception:
            continue
        if start - _dt.timedelta(seconds=120) <= cap <= end + _dt.timedelta(seconds=120):
            mine = r
        else:
            other.append(r)
    return mine, other


def gather(pairs_to_keep: int) -> dict:
    manifest = lib.load_manifest()
    machine = lib.vram_snapshot(manifest["comfyui"]["url"])
    out = {"collected_at": dt.datetime.now().isoformat(timespec="seconds"),
           "machine": machine, "conditions": manifest["conditions"], "runs": []}
    recs = headless_runs()

    for entry in manifest["workflows"]:
        prov = lib.provenance(entry)
        settings = settings_summary(prov)
        timers = [r for t in prov["timers"] for r in t["runs"]]
        found = lib.find_measurement_pairs(manifest, entry["prefix"],
                                           entry.get("result_prefix"),
                                           entry.get("result_pick"))
        if not found:
            out["runs"].append({"id": entry["id"], "status": "no depth_in/depth_out pair found",
                                "searched_prefix": entry["prefix"], "settings": settings,
                                "timer_runs": timers[:5], "object_info": prov["object_info"]})
            continue
        for pair in found[:pairs_to_keep]:
            scores = geometry_score.score(pair["depth_in"], pair["depth_out"])
            files = {k: str(pair[k]) for k in ("depth_in", "depth_out", "result") if k in pair}
            canvas = image_size(pair["result"]) if "result" in pair else None
            captured = dt.datetime.fromtimestamp(pair["mtime"]).isoformat(timespec="seconds")
            timing, unpaired = match_timing(recs, entry["id"], captured)
            out["runs"].append({
                "id": entry["id"], "status": "scored", "pair": pair["key"], "files": files,
                "pair_note": pair.get("note", ""),
                "result_candidates": [str(p) for p in pair.get("candidates", [])],
                "canvas_of_result": canvas,
                "captured_at": captured,
                "scores": scores, "verdict": geometry_score.verdict(scores),
                "settings": settings, "timer_runs": timers[:5],
                "timed_run_record": timing, "other_run_records_of_this_graph": [r["_record"] for r in unpaired],
                "object_info": prov["object_info"],
            })
    return out


def render_rows(data: dict) -> list[str]:
    lines = ["| method | pair | canvas of result | pearson_r | probe 1 % | probe 4 % | edges r | pixels off >0.15 | tile r p10 | tile r med | flat tiles Δ | verdict | steps/cfg | run time (s) | peak GPU used | free VRAM at collect |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for run in data["runs"]:
        if run.get("status") != "scored":
            lines.append(f"| `{run['id']}` | — | — | — | — | — | — | — | — | — | — | **{run['status']}** "
                         f"(looked for `{run['searched_prefix']}_depth_*`) | — | — | — | — |")
            continue
        s, st = run["scores"], run["settings"]
        sampler = " / ".join(str(st[k]) for k in ("steps", "cfg") if k in st) or "—"
        # time: prefer a headless record that was running when this run's files were saved
        # (measured outside ComfyUI, with peak memory), fall back to the graph's own LCTimer
        rec = run.get("timed_run_record")
        if rec:
            time_txt = f"{rec.get('wall_seconds', '—')} (headless run)"
            peak = rec.get("peak_gpu_used_mib")
            peak_txt = f"{peak} MiB" if peak is not None else "—"
        else:
            timer = ", ".join(str(r.get("t")) for r in run["timer_runs"][:3]) or "—"
            time_txt = f"{timer} (graph timer)" if timer != "—" else "—"
            peak_txt = "—"
        free = data["machine"].get("vram_free_mib")
        free_txt = f"{free} MiB" if free is not None else "server not running"
        canvas = "×".join(str(v) for v in run["canvas_of_result"]) if run.get("canvas_of_result") \
            else "result image not matched"
        flag = " ⚠ different aspect" if s.get("aspect_mismatch") else ""
        if run.get("pair_note"):
            flag += " ⚠ result matched by save time, not counter"
        lines.append(
            f"| `{run['id']}` | `{run['pair']}` | {canvas} | **{s['pearson_r']}** | "
            f"{s['probe_1pct_r']} | {s['probe_4pct_r']} | {s['grad_r']} | "
            f"{s['bad_frac_gt_0.15']} | {s['tile_r_p10']} | {s['tile_r_median']} | "
            f"{s['tiles_flat_in_result'] - s['tiles_flat_in_input']:+d} | "
            f"{run['verdict']}{flag} | {sampler} | {time_txt} | {peak_txt} | {free_txt} |")
    return lines


def render_conditions(data: dict) -> list[str]:
    """The conditions these rows share, written out where a reader sees them next to the table —
    a comparison is only fair if the shared input and the machine are stated, and the things that
    are NOT controlled (the canvas of each graph) have to be stated in the same place."""
    c, m = data["conditions"], data["machine"]
    lines = [f"* input photo: `{c.get('source_photo')}` — the same single image in all three graphs",
             f"* fixed seed: `{c.get('seed')}` — {c.get('seed_note', '')}",
             f"* GPU: {c.get('gpu')} — {c.get('note', '')}",
             "* **not controlled:** " + c.get("canvas_note", "")]
    if m.get("error"):
        lines.append("* ComfyUI was not reachable while collecting, so its live VRAM reading is "
                     "absent from this run of the script (the columns say so)")
    else:
        lines.append(f"* ComfyUI {m.get('comfyui_version')} saw {m.get('vram_free_mib')} MiB free "
                     f"of {m.get('vram_total_mib')} MiB at collection time")
    return lines


def write(data: dict) -> None:
    MEAS_JSON.parent.mkdir(parents=True, exist_ok=True)
    MEAS_JSON.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    body = "## Conditions these rows share (from `workflows/manifest.json`)\n\n" + "\n".join(render_conditions(data)) + "\n\n" + "\n".join(render_rows(data))
    if MEAS_MD.exists():
        text = MEAS_MD.read_text(encoding="utf-8")
        if START in text and END in text:
            head, rest = text.split(START, 1)
            _, tail = rest.split(END, 1)
            text = head + START + "\n" + body + "\n" + END + tail
        else:
            text = text.rstrip() + "\n\n" + START + "\n" + body + "\n" + END + "\n"
    else:
        text = HEADER_MD + "\n" + START + "\n" + body + "\n" + END + "\n"
    MEAS_MD.write_text(text, encoding="utf-8")
    print(f"wrote {MEAS_MD}\nwrote {MEAS_JSON}")
    scored = [r for r in data["runs"] if r.get("status") == "scored"]
    print(f"runs: {len(scored)} scored, {len(data['runs']) - len(scored)} waiting for data")
    for run in scored:
        print(f"  {run['id']} pair {run['pair']}: r={run['scores']['pearson_r']} "
              f"(probe 1% {run['scores']['probe_1pct_r']}, edges {run['scores']['grad_r']}, "
              f"local {run['scores']['bad_frac_gt_0.15']}) -> {run['verdict']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=1, help="newest pairs per workflow")
    args = ap.parse_args()
    write(gather(args.pairs))
