#!/usr/bin/env python3
"""Generate workflows/index.md from workflows/manifest.json + the workflow files.

Why generated: the point of index.md is that it cannot drift from the graphs. Anything
written by hand here would be wrong the next time a widget changes. Edit the manifest or
the graphs, then re-run this script.

usage: python scripts/make_index.py [--refresh-object-info]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

OUT = lib.WORKFLOWS / "index.md"
MODEL_FILE_RE = re.compile(r"\.(safetensors|pth|ckpt|pt|onnx|gguf)$", re.I)

RUN_KEYS = ("seed", "seed control", "base seed", "steps", "cfg", "sampler", "scheduler",
            "denoise", "max_resolution", "custom width", "custom height", "proportion",
            "width", "height", "megapixels", "resize to megapixels", "sigma shift",
            "depth resolution", "depth model", "resample", "crop position",
            "keep proportion", "swap dimensions", "size source", "aspect preset",
            "mask grow", "mask feather", "keep", "value", "preset", "control mode",
            "strength", "lora strength", "detailer steps")
INPUT_KEYS = ("input image", "output prefix", "upload")
PLACEHOLDER = "_(заполняется после прогона / to fill after the run)_"


def _fmt(v) -> str:
    if isinstance(v, (dict, list)):
        import json
        s = json.dumps(v, ensure_ascii=False)
    else:
        s = str(v)
    return s if len(s) < 160 else s[:157] + "…"


def table(title: str, rows: list[tuple[str, str, str]]) -> list[str]:
    if not rows:
        return []
    out = [f"**{title}**", "", "| field | value | where |", "|---|---|---|"]
    out += [f"| {k} | `{v}` | {w} |" for k, v, w in rows]
    out.append("")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh-object-info", action="store_true",
                    help="re-read node definitions from the running ComfyUI")
    args = ap.parse_args()

    if args.refresh_object_info:
        manifest = lib.load_manifest()
        lib.OBJECT_INFO_CACHE.unlink(missing_ok=True)

    manifest = lib.load_manifest()
    conditions = manifest["conditions"]
    lines = [
        "# Workflow index (generated)",
        "",
        "`python scripts/make_index.py` writes this file — do not edit it by hand.",
        "It is the readable printout of what each graph contains right now: models, sizes,",
        "seeds, samplers, and the run times the graph itself recorded.",
        "",
        "A value that is overridden by an incoming link is listed under “parameters that do",
        "not come from widgets” — an old number left in a widget of a saved workflow does",
        "not mean the graph uses it. The canvas that was really generated is recorded per",
        "run in `docs/metrics.md`, read from the saved result image.",
        "",
        f"Common measurement input: `{conditions['source_photo']}`; GPU `{conditions['gpu']}`. "
        f"{conditions['note']}.",
        "",
    ]
    for entry in manifest["workflows"]:
        prov = lib.provenance(entry)
        api_graph = lib.WORKFLOWS / "_api" / (Path(entry["file"]).stem + ".api.json")
        replay = entry.get("replay") or {}
        replay_txt = (("**blocked** — " + replay["why"]) if replay.get("headless") == "blocked"
                      else (f"possible with `python scripts/run_workflow.py {entry['id']}`"
                            if api_graph.exists() else
                            f"not set up yet: no {api_graph.relative_to(lib.ROOT).as_posix()} "
                            "(queue the graph once in the UI, then run "
                            "`python scripts/import_api_from_history.py`)"))
        lines += [f"## `{entry['file']}`  (id `{entry['id']}`)", "",
                  f"- method: {entry['method']}",
                  f"- control signal: {entry['control']}",
                  f"- what we expect to see: {entry['expect']}",
                  f"- measurement outputs: `{entry['prefix']}_depth_in-*.png`, "
                  f"`{entry['prefix']}_depth_out-*.png`, plus the result image itself",
                  f"- headless replay: {replay_txt}"] + (
            [f"- repeating the same graph gives: {replay['determinism']}"]
            if replay.get("determinism") else []) + [""]
        if prov["object_info"] == "UNAVAILABLE":
            lines += ["_(parameter names could not be resolved: ComfyUI was not reachable and "
                      "there is no `.object_info.json` cache, so the values below are positional)_",
                      ""]

        models, run_settings, inputs, notes = [], [], [], []
        for node in prov["nodes"]:
            where = f"node {node['id']} `{node['type']}`"
            if node.get("title"):
                where += f" “{node['title']}”"
            if node["scope"]:
                where += f" ({node['scope']})"
            for key, value in node["params"].items():
                row = (key, _fmt(value), where)
                if isinstance(value, str) and MODEL_FILE_RE.search(value):
                    models.append(row)
                elif key in INPUT_KEYS:
                    inputs.append(row)
                elif key in RUN_KEYS:
                    run_settings.append(row)
            notes += [f"{where}: {n}" for n in node["notes"]]

        lines += table("Models and weights in this graph", models)
        lines += table("Run settings", run_settings)
        lines += table("Inputs and output prefixes", inputs)
        if notes:
            lines += ["**Parameters that do not come from widgets**", ""]
            lines += [f"- {n}" for n in notes]
            lines.append("")

        for timer in prov["timers"]:
            runs = timer["runs"]
            if runs:
                lines += [f"**Run times recorded in the graph** (node {timer['id']} "
                          f"`LCTimer`, newest first)", "",
                          "| at | seconds | ok |", "|---|---|---|"]
                lines += [f"| {r.get('at')} | {r.get('t')} | {r.get('ok')} |" for r in runs]
                lines.append("")
            else:
                lines += [f"_(node {timer['id']} `LCTimer` has recorded no run yet — the times "
                          "appear in the graph after the first run in the UI)_", ""]

        lines += ["**Verdict / status**", "", PLACEHOLDER, "---", ""]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
