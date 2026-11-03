#!/usr/bin/env python3
"""Geometry score between the depth map of the real photo and the depth map of the result.

Both maps come from the SAME Depth-Anything node inside every workflow (the pairs
<prefix>_depth_in-*.png and <prefix>_depth_out-*.png), so this is one identical number for
all three methods, computed on the CPU after the GPU work is done.

What the numbers mean
  pearson_r      correlation of the two depth maps after per-map normalisation. Depth
                 Anything is relative, so each map is normalised on its own first — we
                 compare the SHAPE of the depth, not its absolute scale.
  probe_1pct_r   the INPUT map against itself nudged by 1 % of the width. This is a property
                 of the reference scene, not of the result: it says what "nothing moved but
                 the camera" costs on this particular picture. Without it a correlation like
                 0.78 cannot be read as good or bad.
  probe_4pct_r   the same with a 4 % nudge — roughly what a real change of viewpoint costs.
  grad_r         correlation of gradient magnitude: edges and boundaries, i.e. whether
                 window and roof lines stayed where they were, not only the big masses.
  mad, bad_frac  mean absolute difference, and the fraction of pixels differing by more than
                 0.15 after normalisation (local violations: something moved or appeared).
  tile_r_p10 /   local correlations on an 8x6 grid. The usual failure is not the whole image
  tile_r_median  shifting, but one region repainted as a texture blob: the 10th percentile
                 catches that while the global r still looks fine. Flat tiles (sky, blank
                 wall) carry no information and are counted separately instead:
                 tiles_flat_in_result > tiles_flat_in_input means areas lost their structure.
                 Compare these between methods on the same source photo, not as absolutes.

The verdict separates the two things a material swap affects differently:
  global geometry — is it still the same house in the same place?  (r against probe_1pct_r)
  local change    — was something actually replaced?  bad_frac; for this task a local change
                    is the goal, so it is reported, not punished.

Calibration measured with this exact formula on the aerial photos of this project:
identical = 1.00, nudged 1 % = 0.81, nudged 4 % = 0.56, a different frame of the same
flight = about 0.0. Those are PHOTO numbers. The rows of the comparison table compare DEPTH
maps, which are much smoother, so their probes sit far higher (measured on this source photo:
0.99 at 1 %, 0.95 at 4 %) — the two scales must not be read against each other. This is
exactly why the probes are recomputed for every run instead of hard-coded: each row is judged
by the probe of its own input map.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


def _load_map(path: Path, size: tuple[int, int]) -> np.ndarray:
    """Greyscale map as float32, resized to a common size, normalised to 0..1."""
    img = Image.open(path).convert("L").resize(size, Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    lo, hi = float(arr.min()), float(arr.max())
    if hi - lo < 1e-6:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a.ravel() - a.mean()
    b = b.ravel() - b.mean()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(a @ b / denom) if denom > 1e-9 else 0.0


def _grad_mag(a: np.ndarray) -> np.ndarray:
    dy = np.abs(np.diff(a, axis=0, prepend=a[:1]))
    dx = np.abs(np.diff(a, axis=1, prepend=a[:, :1]))
    return dy + dx


def _tile_scores(a: np.ndarray, b: np.ndarray, cols: int = 8, rows: int = 6) -> tuple[list[float], int, int]:
    """Local correlations on a grid, plus how many tiles went flat in either map.

    The usual failure mode is not the whole picture moving, but one region being repainted as
    a texture blob while everything around it stays. Tiles that are flat (sky, empty wall)
    carry no information, so they are excluded from the correlations — and counted instead,
    because tiles that were full of structure in the photo and became flat in the result are
    exactly what "the model smeared the facade over" looks like in numbers.
    """
    h, w = a.shape
    tw, th = w // cols, h // rows
    scores, flat_in_result, flat_in_input = [], 0, 0
    for y in range(rows):
        for x in range(cols):
            ye = (y + 1) * th if y < rows - 1 else h
            xe = (x + 1) * tw if x < cols - 1 else w
            ta, tb = a[y * th:ye, x * tw:xe], b[y * th:ye, x * tw:xe]
            flat_a, flat_b = ta.std() < 0.01, tb.std() < 0.01
            if flat_a:
                flat_in_input += 1
            if flat_b:
                flat_in_result += 1
            if flat_a or flat_b:
                continue
            scores.append(_pearson(ta, tb))
    return scores, flat_in_result, flat_in_input


def score(depth_in: Path, depth_out: Path, width: int = 512) -> dict:
    """Compare one input/result pair. `width` sets the working resolution (the height
    follows the aspect of the input map); 512 is plenty for a correlation and costs nothing."""
    base = Image.open(depth_in)
    out_base = Image.open(depth_out)
    target_w = min(width, base.width)
    size = (target_w, int(round(target_w * base.height / base.width)))
    aspect_in = base.width / base.height
    aspect_out = out_base.width / out_base.height
    aspect_mismatch = abs(aspect_in - aspect_out) / aspect_in > 0.02

    a = _load_map(depth_in, size)
    b = _load_map(depth_out, size)
    diff = np.abs(a - b)
    tiles, flat_result, flat_input = _tile_scores(a, b)
    tiles_sorted = sorted(tiles)
    shift_1 = max(1, round(size[0] * 0.01))
    shift_4 = max(1, round(size[0] * 0.04))

    result = {
        "size": list(size),
        "depth_in_raw_size": [base.width, base.height],
        "depth_out_raw_size": [out_base.width, out_base.height],
        # different aspect ratios mean one map was squashed to compare: the number is still
        # computed, but it cannot be compared with the rows of the other methods
        "aspect_mismatch": aspect_mismatch,
        "pearson_r": round(_pearson(a, b), 4),
        "probe_1pct_r": round(_pearson(a, np.roll(a, shift_1, axis=1)), 4),
        "probe_4pct_r": round(_pearson(a, np.roll(a, shift_4, axis=1)), 4),
        "grad_r": round(_pearson(_grad_mag(a), _grad_mag(b)), 4),
        "mad": round(float(diff.mean()), 4),
        "bad_frac_gt_0.15": round(float((diff > 0.15).mean()), 4),
        # local structure: the 10th percentile and the median of the tile correlations
        "tile_r_p10": round(tiles_sorted[max(0, int(len(tiles_sorted) * 0.10))], 4) if tiles else None,
        "tile_r_median": round(tiles_sorted[len(tiles_sorted) // 2], 4) if tiles else None,
        "tiles_used": len(tiles),
        "tiles_flat_in_input": flat_input,
        # more flat tiles in the result than in the photo = areas that lost their structure
        "tiles_flat_in_result": flat_result,
    }
    if aspect_mismatch:
        result["warning"] = (
            f"depth maps have different aspect ratios ({base.width}x{base.height} vs "
            f"{out_base.width}x{out_base.height}) — one was resampled to compare, treat the "
            "numbers as indicative")
    return result


def verdict(scores: dict) -> str:
    """Global geometry and local change are different claims: for a material swap a local
    change is the whole point, while the house has to stay exactly where it was."""
    r, probe = scores["pearson_r"], scores["probe_1pct_r"]
    if scores.get("aspect_mismatch"):
        return "not comparable (the two maps have different aspect ratios)"
    # 0.30 is not a guess: a different frame of this same flight scored about 0.0 with this
    # formula, and depth maps are smoother than photos — under 0.30 nothing is shared
    if r < 0.30 or probe <= 0:
        return "global geometry lost"
    if r >= probe - 0.05:
        base = "global geometry held"
    elif r >= 0.6 * probe:
        base = "global geometry drifting"
    else:
        return "global geometry lost"
    if scores["bad_frac_gt_0.15"] > 0.20:
        pct = round(scores["bad_frac_gt_0.15"] * 100)
        base += f" + a large local change ({pct} % of the pixels off by more than 0.15)"
    tile = scores.get("tile_r_p10")
    if tile is not None and tile < 0.0:
        base += f" + at least one region contradicts the input (10th-percentile local r {tile})"
    # 6 % of the grid (3 of 8x6 tiles) is a stated heuristic, to be re-checked on real data:
    # structure that existed in the photo and became flat in the result
    lost = scores.get("tiles_flat_in_result", 0) - scores.get("tiles_flat_in_input", 0)
    if lost >= 0.06 * 48:
        base += f" + {lost} grid areas lost their structure (flat in the result, not in the photo)"
    return base


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__ + "\nusage: geometry_score.py <depth_in.png> <depth_out.png>")
    import json
    s = score(Path(sys.argv[1]), Path(sys.argv[2]))
    s["verdict"] = verdict(s)
    print(json.dumps(s, indent=1, ensure_ascii=False))
