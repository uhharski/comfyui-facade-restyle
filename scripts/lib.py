"""Shared helpers for the measurement scripts (see ../workflows/manifest.json).

Only stdlib + Pillow/numpy, and nothing here touches the GPU: reading a ComfyUI output PNG,
a workflow JSON or /object_info must stay possible while ComfyUI is busy or switched off.

Why reading /object_info matters: in a saved graph a widget value can be overridden by an
incoming link (a resize node feeding a sampler), and the leftover number in the widget stays
in the file. Reading the widgets alone therefore states the wrong canvas in some graphs.
The provenance below asks the running server which inputs of a node are real widgets and
drops the ones that are connected — and says plainly when a parameter comes from a link.
"""
from __future__ import annotations

import glob
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / "workflows"
MANIFEST = WORKFLOWS / "manifest.json"
OBJECT_INFO_CACHE = ROOT / ".object_info.json"

MODEL_FILE_RE = re.compile(r"\.(safetensors|pth|ckpt|pt|onnx|gguf|safetensors\.\d+)$", re.I)
SEED_MODES = {"fixed", "increment", "decrement", "randomize", "randomize until change",
              "fixed (keep)", "auto", "manual", "off"}
# ComfyUI has used two counter forms over the versions on this machine: the old
# "prefix-00001.png" and the current "prefix_00001_.png" (note the trailing underscore).
# Both must group into the same pair key, otherwise depth_in and depth_out of one run look
# like two different runs and no measurement is scored at all.
COUNTER_RE = re.compile(r"[-_](\d{4,6})_?\.png$")

# spec input name -> what to call it in the tables (labels only; values come from the graph)
FIELD_LABELS = {
    "unet_name": "diffusion model", "ckpt_name": "checkpoint", "clip_name": "text encoder",
    "vae_name": "vae", "lora_name": "lora", "lora_01": "lora 1", "lora_02": "lora 2",
    "transformer_lora_01_name": "lora 1", "transformer_lora_02_name": "lora 2",
    "strength_model": "lora strength", "strength": "lora strength", "weight_name": "weight",
    "model_name": "model", "clip_type": "clip type", "type": "clip type",
    "base_seed": "base seed", "seed": "seed", "steps": "steps", "total_steps": "steps",
    "detailer_steps": "detailer steps", "cfg": "cfg", "sampler_name": "sampler",
    "scheduler": "scheduler", "denoise": "denoise", "shift": "sigma shift",
    "max_resolution": "max_resolution", "custom_width": "custom width",
    "custom_height": "custom height", "width": "width", "height": "height",
    "proportion": "proportion", "keep_proportion": "keep proportion",
    "megapixels": "megapixels", "resize_to_megapixels": "resize to megapixels",
    "resolution": "depth resolution", "ckpt_name_depth": "depth model",
    "model_name": "model", "filename_prefix": "output prefix", "image": "input image",
    "upscale_method": "resample", "crop_location": "crop position",
    "swap_dimensions": "swap dimensions", "resolution_source": "size source",
    "aspect_ratio": "aspect preset", "grow": "mask grow", "feather": "mask feather",
    "keep": "keep", "value": "value", "preset": "preset", "control_mode": "control mode",
    "strength": "strength", "image_threshold": "image threshold", "laten_threshold": "latent threshold",
}


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_workflow(entry_or_path) -> dict:
    path = WORKFLOWS / entry_or_path["file"] if isinstance(entry_or_path, dict) else Path(entry_or_path)
    return json.loads(path.read_text(encoding="utf-8"))


def scopes_of(graph: dict):
    """Top-level nodes plus the insides of any subgraphs, tagged for the tables."""
    yield "", graph.get("nodes", [])
    for sub in graph.get("definitions", {}).get("subgraphs", []):
        yield f"subgraph: {sub.get('name')}", sub.get("nodes", [])


def object_info(url: str, refresh: bool = False) -> dict | None:
    """Node definitions of the running ComfyUI, cached in .object_info.json (git-ignored).
    None when the server is unreachable and no cache exists — the scripts then say so."""
    if OBJECT_INFO_CACHE.exists() and not refresh:
        try:
            return json.loads(OBJECT_INFO_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/object_info", timeout=60) as r:
            data = json.load(r)
        OBJECT_INFO_CACHE.write_text(json.dumps(data), encoding="utf-8")
        return data
    except Exception:
        return None


def _spec_of(objinfo: dict | None, node_type: str) -> list[tuple[str, str]]:
    """[(input name, kind)] in the server's declared order. kind is 'link' for a data
    socket (MODEL/IMAGE/CONDITIONING…), otherwise the widget type: 'int', 'float',
    'boolean', 'string', 'combo' (a dropdown of fixed options) or 'other'."""
    if not objinfo:
        return []
    node = objinfo.get(node_type)
    if not node:
        return []
    out = []
    for section in ("required", "optional"):
        for name, decl in (node["input"].get(section) or {}).items():
            head = decl[0] if isinstance(decl, (list, tuple)) and decl else decl
            if isinstance(head, list):
                kind = "combo"
            elif isinstance(head, str) and head.upper() == head and head in (
                    "INT", "FLOAT", "BOOLEAN", "STRING", "COMBO"):
                kind = head.lower()
            elif isinstance(head, str) and head.upper() == head:
                kind = "link"
            else:
                kind = "other"
            out.append((name, kind))
    return out


def _matches(kind: str, value) -> bool:
    if kind in ("int", "float"):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind in ("combo", "string", "other"):
        return isinstance(value, str)
    return False


# what the frontend leaves behind in widgets_values when a socket is fed by a link
INERT = ("", None, [], {})


def _align(spec: list[tuple[str, str]], values: list) -> dict:
    """Put stored values onto the node's declared inputs.

    A saved workflow keeps its values in one flat list aligned with the sockets the node had
    when it was saved — including sockets that are now fed by a link and hold an empty
    placeholder. Matching by position alone shifts every later value by the number of such
    sockets (a seed was printed as a sampler name here), so the alignment is driven by the
    declared type of each input: numbers go to numeric inputs, option strings to combos,
    empty placeholders to link inputs.
    """
    aligned: dict = {}
    i = 0
    for name, kind in spec:
        if i >= len(values):
            continue
        value = values[i]
        if kind == "link":
            if value in INERT and not isinstance(value, (int, float, bool)):
                i += 1                       # placeholder for a value that comes from a link
            continue
        # the frontend stores one extra value after a seed widget: what to do with the seed
        if kind in ("int", "float") and isinstance(value, str) and value in SEED_MODES:
            aligned.setdefault("control_after_generate", value)
            i += 1
            if i >= len(values):
                break
            value = values[i]
        if _matches(kind, value):
            aligned[name] = value
            i += 1
        else:
            aligned.setdefault(name, "<no stored value>")
    return aligned


def node_params(node: dict, objinfo: dict | None) -> dict:
    """Current parameters of one node. Anything fed by a link is listed separately: the
    number left in that widget is inert and must not be reported as the setting used."""
    spec = _spec_of(objinfo, node["type"])
    spec_names = {name for name, _ in spec}
    linked = {i["name"] for i in node.get("inputs", []) if i.get("link")}
    wv = node.get("widgets_values")
    notes: list[str] = []

    if isinstance(wv, dict):                       # newer format: values by name
        params = {FIELD_LABELS.get(k, k): v for k, v in wv.items()
                  if k not in linked and k not in ("upload", "image_upload")}
        if linked:
            notes.append("fed by links (the value stored in the widget of this node is inert): "
                         + ", ".join(FIELD_LABELS.get(n, n) for n in sorted(linked)))
        return {"params": params, "notes": notes}

    if not isinstance(wv, list):
        return {"params": {}, "notes": []}
    if not spec:                                   # no /object_info: values without names
        return {"params": {f"value {i}": v for i, v in enumerate(wv)},
                "notes": ["parameter names unavailable (ComfyUI not reachable, no "
                          ".object_info.json cache) — values are positional"]}

    aligned = _align(spec, wv)
    params = {FIELD_LABELS.get(name, name): value for name, value in aligned.items()
              if value is not None}
    overridden = sorted(n for n in linked if n in spec_names)
    if overridden:
        notes.append("comes from links, the value shown above is the stale widget value: "
                     + ", ".join(FIELD_LABELS.get(n, n) for n in overridden))
    fully_linked = sorted(linked - set(overridden))
    if fully_linked:
        notes.append("inputs with no value in this file (they arrive from links): "
                     + ", ".join(fully_linked))
    return {"params": params, "notes": notes}


def provenance(entry: dict) -> dict:
    """Everything a run needs to be reproducible: models, sizes, seeds, samplers, timers."""
    manifest = load_manifest()
    objinfo = object_info(manifest["comfyui"]["url"])
    graph = load_workflow(entry)
    found, timers = [], []
    for scope, nodes in scopes_of(graph):
        for node in nodes:
            if node.get("type") == "LCTimer":
                timers.append({"scope": scope, "id": node["id"],
                               "runs": (node.get("properties") or {}).get("lc_runs", [])})
                continue
            got = node_params(node, objinfo)
            if not got["params"]:
                continue
            models = sorted({str(v) for v in got["params"].values()
                             if isinstance(v, str) and MODEL_FILE_RE.search(v)})
            found.append({"scope": scope, "id": node["id"], "type": node["type"],
                          "title": node.get("title") or "", "params": got["params"],
                          "notes": got["notes"], "model_files": models})
    return {"nodes": found, "timers": timers,
            "object_info": "cache/live" if objinfo else "UNAVAILABLE"}


def vram_snapshot(url: str) -> dict:
    """How much VRAM the running ComfyUI can actually see — '12 GB' has to be stated as the
    real available number, not the card's."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/system_stats", timeout=10) as r:
            data = json.load(r)
        dev = (data.get("devices") or [{}])[0]
        return {"vram_total_mib": round(dev.get("vram_total", 0) / 2**20),
                "vram_free_mib": round(dev.get("vram_free", 0) / 2**20),
                "comfyui_version": (data.get("system") or {}).get("comfyui_version")}
    except Exception as exc:                                    # server not running
        return {"error": str(exc)}


def nvidia_smi_used_mib() -> int | None:
    """Whole-GPU used memory, sampled from outside ComfyUI (no CUDA context, ~0 % load)."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10).stdout.strip().splitlines()
        return int(out[0])
    except Exception:
        return None


class VramSampler:
    """Peak used-memory watcher for one run."""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.samples: list[tuple[float, int]] = []
        self._stop = False
        self._thread = None

    def start(self):
        import threading

        def loop():
            while not self._stop:
                used = nvidia_smi_used_mib()
                if used is not None:
                    self.samples.append((time.time(), used))
                time.sleep(self.interval)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self) -> dict:
        self._stop = True
        if self._thread:
            self._thread.join(timeout=5)
        if not self.samples:
            return {"peak_used_mib": None, "samples": 0}
        return {"peak_used_mib": max(v for _, v in self.samples),
                "samples": len(self.samples),
                "duration_s": round(self.samples[-1][0] - self.samples[0][0], 1)}


def output_dir(manifest: dict) -> Path:
    return Path(manifest["comfyui"]["output_dir"])


RESULT_TIME_WINDOW_S = 1800     # how far apart the save times of one run may be


def find_measurement_pairs(manifest: dict, prefix: str, result_prefix: str | None = None,
                          ) -> list[dict]:
    """Pair what one run saved: the two depth maps (by SaveImage counter suffix) plus the
    result image itself, whose real pixel size is the only trustworthy record of the canvas.

    result_prefix — the prefix the result SaveImage node really uses. It is a separate widget
    in the graph and in two of our graphs it drifted from the measurement prefix (the Qwen
    graph saves results as `qwen21_inpaint_*`, the MOSS graph as the default `ComfyUI_*`).
    Counters restart per prefix, so a matching counter across two different prefixes is not a
    proof of being the same run; the fallback match is therefore made by save time (inside
    RESULT_TIME_WINDOW_S) and is labelled in the returned note, never presented as certain.
    """
    root = output_dir(manifest)
    if not root.exists():
        return []
    if isinstance(result_prefix, str):
        result_prefixes = [result_prefix]
    elif result_prefix:
        result_prefixes = list(result_prefix)
    else:
        result_prefixes = [prefix]
    by_key: dict[str, dict] = {}
    results: list[Path] = []

    for path in sorted(glob.glob(str(root / "**" / "*.png"), recursive=True)):
        p = Path(path)
        name = p.name
        kind = ("depth_in" if f"{prefix}_depth_in" in name or f"{prefix}-depth_in" in name else
                "depth_out" if f"{prefix}_depth_out" in name or f"{prefix}-depth_out" in name
                else None)
        if kind:
            m = COUNTER_RE.search(name)
            key = m.group(1) if m else p.stem
            by_key.setdefault(key, {})[kind] = p
            continue
        if any(name.startswith(f"{rp}-") or name.startswith(f"{rp}_")
               for rp in result_prefixes):
            if COUNTER_RE.search(name):
                results.append(p)        # a real run counter, matched below by time

    ready = []
    for key, found in by_key.items():
        if "depth_in" not in found or "depth_out" not in found:
            continue                     # an interrupted run: not a measurement
        pair_time = max(v.stat().st_mtime for v in found.values())
        notes: list[str] = []

        same_key = [p for p in results if COUNTER_RE.search(p.name).group(1) == key
                    and (p.name.startswith(f"{prefix}_") or p.name.startswith(f"{prefix}-"))]
        if same_key:
            found["result"] = same_key[0]
        else:
            near = [p for p in results
                    if abs(p.stat().st_mtime - pair_time) <= RESULT_TIME_WINDOW_S]
            near.sort(key=lambda p: abs(p.stat().st_mtime - pair_time))
            if near:
                found["result"] = near[0]
                notes.append(
                    "result image matched by save time (within "
                    f"{int(abs(near[0].stat().st_mtime - pair_time))} s), not by counter: this "
                    "graph saves its result under a different prefix, so counters do not line "
                    "up — treat the canvas column as indicative until the graph's result "
                    "SaveImage node is renamed to the graph id")
            else:
                notes.append(
                    "no result image found for this run — the graph's result SaveImage uses a "
                    "different prefix (fix: set it to the graph id, or list it as "
                    "result_prefix in workflows/manifest.json)")
        ready.append({"key": key, **found, "note": "; ".join(notes),
                      "mtime": pair_time})
    return sorted(ready, key=lambda x: x["mtime"], reverse=True)
