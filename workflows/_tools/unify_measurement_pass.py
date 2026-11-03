#!/usr/bin/env python3
"""
unify_measurement_pass.py — make the three workflows comparable as measurements.

The three graphs are different methods (Krea2 edit, MOSS color+depth control, Qwen-Image
inpaint). Comparing them is only meaningful if everything except the METHOD is equal.
This script sets the parts that must be equal, in place, in all three files:

  1. the same source photo        -> DJI_0021.JPG (a real aerial photo of the house)
  2. the same canvas              -> 1024 x 576 (16:9, longer side 1024 = the
                                     "modest hardware" budget on an RTX 5070 12 GB)
  3. the same fixed seed          -> 20261103, control_after_generate = fixed
  4. the same wording of the task -> one shared material-swap instruction; the method's own
                                     negative/grounding wording stays method-specific

What is deliberately NOT unified: sampler, scheduler, steps, CFG and the conditioning
mechanism — that IS the difference between the approaches. VRAM and wall time stay
comparable because resolution, seed and input are equal.

Every change is recorded to _tools/unify_report.txt (node id, type, field, old -> new),
and the untouched originals remain in workflows/_orig/.

Usage:  python _tools/unify_measurement_pass.py [--check]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # workflows/
REPORT = Path(__file__).resolve().parent / "unify_report.txt"

SEED = 20261103
PHOTO = "DJI_0021.JPG"
SIDE_LONG, SIDE_SHORT = 1024, 576                      # 16:9 aerial frame
MEGAPIXELS = round(SIDE_LONG * SIDE_SHORT / 1e6, 3)    # for the Qwen canvas knob

PROMPT = (
    "Same house, same camera angle, same time of day, same weather. Keep the building "
    "exactly as it is: geometry, volume, roofline and slopes, wall proportions, the exact "
    "positions and sizes of every window and door opening, the plot, the ground level and "
    "the surrounding trees. Change only the exterior finishes: light warm-grey plaster on "
    "the main wall volumes, dark graphite window frames and entrance door, a dark "
    "standing-seam metal roof. Photorealistic architectural photography, diffuse overcast "
    "daylight, natural colours, sharp focus."
)
NEGATIVE_KREA2 = ("people, cars, construction site machinery, new openings, extra storeys, "
                  "changed roofline, warped walls, duplicate windows, text, watermark, "
                  "blurry, low quality")
# the Qwen path edits one touched region, so its instruction is one sentence
PROMPT_REGION = ("rebuild the surface here as light warm-grey plaster with a dark graphite "
                 "window frame, photorealistic, keep the exact shape and position of the "
                 "opening and everything around it")

TARGETS = {
    "krea2_edit.json": [
        # (node id, widget index, new value, why)
        (72, 0, PHOTO, "LoadImage #1 (was a ClipSpace painted mask test)"),
        (89, 0, PHOTO, "LoadImage #2 (was 6.jfif, a person reference)"),
        (87, 0, SIDE_LONG, "ImageResizeKJv2 width"),
        (87, 1, SIDE_SHORT, "ImageResizeKJv2 height"),
        (86, 0, SIDE_LONG, "ImageResizeKJv2 width"),
        (86, 1, SIDE_SHORT, "ImageResizeKJv2 height"),
        (53, 0, SEED, "KSampler seed"),
        (53, 1, "fixed", "KSampler control_after_generate"),
        (84, 0, PROMPT, "positive (Krea2 grounded edit encode)"),
        (85, 0, NEGATIVE_KREA2, "negative / groundings"),
    ],
    "moss_inpaint.json": [
        (30, 0, SIDE_LONG, "AspectRatioSimplifier max_resolution (longer side)"),
        (28, 0, SEED, "LCSeed base_seed (feeds LCMOSSBoxEdit seed)"),
        (86, 0, PROMPT, "LCMOSSLayoutPrompt text (was a demo: person on a snowy street)"),
    ],
    "qwenImage_inpaint.json": [
        # this node stores its widgets as a JSON object, not a list
        (2, "resize_to_megapixels", True, "ImageCropRotatePad: enable pixel budget"),
        (2, "megapixels", MEGAPIXELS, f"ImageCropRotatePad: {SIDE_LONG}x{SIDE_SHORT} canvas"),
        (5, 0, SEED, "AUSBOSS Seed value"),
        (5, 1, "fixed", "AUSBOSS Seed control_after_generate"),
        (4, 0, PROMPT_REGION, "text sent into the inpaint subgraph (was a brick-facade test)"),
    ],
}


def main():
    check = "--check" in sys.argv
    lines = []
    for name, edits in TARGETS.items():
        path = HERE / name
        data = json.loads(path.read_text(encoding="utf-8"))
        nodes = {n["id"]: n for n in data["nodes"]}
        print(f"== {name}")
        for node_id, key, new, why in edits:
            node = nodes[node_id]
            wv = node.get("widgets_values")
            if isinstance(wv, dict):
                old = wv.get(key)
                if not check:
                    wv[key] = new
            else:
                # pad the list if a widget was collapsed / not serialized
                while isinstance(wv, list) and len(wv) <= key:
                    wv.append(None)
                old = wv[key] if isinstance(wv, list) else None
                if not check:
                    wv[key] = new
            shown_old = json.dumps(old, ensure_ascii=False)
            shown_new = json.dumps(new, ensure_ascii=False)
            if shown_old == shown_new:
                print(f"   [=] node {node_id:<4} {node['type']:<28} {key}: already set")
                lines.append(f"{name}\t{node_id}\t{node['type']}\t{key}\t{shown_old}\t(no change)")
                continue
            print(f"   [ ] node {node_id:<4} {node['type']:<28} {key}: "
                  f"{shown_old[:60]}{'…' if len(shown_old) > 60 else ''} -> {shown_new[:60]}{'…' if len(shown_new) > 60 else ''}   # {why}")
            lines.append(f"{name}\t{node_id}\t{node['type']}\t{key}\t{shown_old}\t{shown_new}\t# {why}")
        if not check:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    if not check:
        REPORT.write_text(
            "changes made by _tools/unify_measurement_pass.py\n"
            "columns: file \t node \t node type \t widget \t old \t new \t why\n\n"
            + "\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nreport -> {REPORT}")


if __name__ == "__main__":
    main()
