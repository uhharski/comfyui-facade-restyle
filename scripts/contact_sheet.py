#!/usr/bin/env python3
"""Build a labelled before/after sheet: the source photo and what each method made from it.

This is the human half of the evaluation. geometry_score.py answers "is the geometry still
there"; it cannot answer "is the plaster recognizable as plaster" — that is a look, and the
look should be at the same size, in one image, with the method written under each tile, so
what the README shows and what a reviewer judges are the same pixels.

The source photo and each method's result are the files collect_metrics.py already matched
(docs/metrics/measurements.json -> runs[].files), so the sheet cannot drift away from the
table: it shows exactly the runs the numbers were computed from.

usage:
    python scripts/contact_sheet.py                     # newest scored run per method
    python scripts/contact_sheet.py --out docs/gallery/compare.png
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import lib  # noqa: E401
from PIL import Image, ImageDraw, ImageFont  # noqa: E401

MEAS_JSON = lib.ROOT / "docs" / "metrics" / "measurements.json"
TILE_W = 640          # every tile is resized to this width: the comparison is then honest
LABEL_H = 26


def label_font(size: int = 15):
    for name in ("arial.ttf", "segoeui.ttf", "dejavusans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def tile(path: Path, label: str, font) -> Image.Image:
    img = Image.open(path).convert("RGB")
    w = min(TILE_W, img.width)
    h = round(img.height * w / img.width)
    img = img.resize((w, h), Image.LANCZOS)
    out = Image.new("RGB", (TILE_W, h + LABEL_H), (16, 16, 16))
    out.paste(img, ((TILE_W - w) // 2, 0))
    d = ImageDraw.Draw(out)
    d.text((8, h + 5), f"{label}   [{img.width}x{img.height}]", fill=(235, 235, 235), font=font)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if not MEAS_JSON.exists():
        raise SystemExit(f"no {MEAS_JSON} — run scripts/collect_metrics.py first")
    data = json.loads(MEAS_JSON.read_text(encoding="utf-8"))
    runs = [r for r in data["runs"] if r.get("status") == "scored"]
    if not runs:
        raise SystemExit("no scored runs in measurements.json — nothing to show")

    source = Path(data["conditions"]["source_photo"])
    if not source.is_absolute():
        # the repo keeps its own copy (source/photos/) — prefer it, the sheet must be
        # reproducible after the ComfyUI input folder is cleaned up
        for base in (lib.ROOT / "source" / "photos",
                     Path(lib.load_manifest()["comfyui"]["input_dir"])):
            if (base / source).exists():
                source = base / source
                break
    if not source.exists():
        raise SystemExit(f"source photo not found: {source} (it is an input of the graphs, "
                         "not a generated file)")

    font = label_font()
    cells = [tile(source, f"SOURCE {source.name}", font)]
    notes = []
    for run in runs:
        files = run.get("files", {})
        if "result" not in files:
            notes.append(f"{run['id']}: no result image matched — the canvas/prefix problem in "
                         "collect_metrics, not a missing generation")
            continue
        s = run["scores"]
        cells.append(tile(Path(files["result"]),
                           f"{run['id']}  r={s['pearson_r']} edges={s['grad_r']} "
                           f"off={round(s['bad_frac_gt_0.15'] * 100, 2)}%", font))

    cols = min(2, len(cells)) if len(cells) > 2 else len(cells)
    rows = -(-len(cells) // cols)
    gap = 8
    cw = max(c.width for c in cells)
    ch = max(c.height for c in cells)
    sheet = Image.new("RGB", (cols * cw + (cols - 1) * gap, rows * ch + (rows - 1) * gap + 34),
                     (10, 10, 10))
    d = ImageDraw.Draw(sheet)
    d.text((8, 8), "before / after — tiles come from the runs the numbers in docs/metrics.md "
                   "were computed from", fill=(235, 235, 235), font=font)
    for i, c in enumerate(cells):
        x, y = (i % cols) * (cw + gap), 34 + (i // cols) * (ch + gap)
        sheet.paste(c, (x, y))

    out = Path(args.out) if args.out else (lib.ROOT / "docs" / "gallery" /
                                           f"compare_{dt.datetime.now():%Y%m%d_%H%M}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"wrote {out}  ({sheet.width}x{sheet.height}, {len(cells)} tiles)")
    print("what each tile is: " + "; ".join(
        f"{r['id']} = {r['files'].get('result', 'no result matched')}" for r in runs))
    for n in notes:
        print("note: " + n)
    print("the numbers in the labels are the geometry score of that same run; whether the "
          "material itself reads as real is what a human adds here")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
