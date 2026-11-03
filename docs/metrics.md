# Measurements (generated table at the bottom)

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
  matched to the depth pair **by save time instead of by counter**, because that graph saves its
  result under a prefix other than its measurement prefix. The second is a naming bug, listed
  per graph in `workflows/manifest.json` (`result_prefix_note`); fix it there or in the graph's
  SaveImage node and the flag goes away
* time comes from the graph's own timer node (`LCTimer` keeps its history inside the
  workflow file); free VRAM is what ComfyUI reported it could see at collection time
* what each method conditions on is described in `workflows/index.md`

The methods are NOT forced to identical settings: samplers, steps and CFG belong to the
method, and the graphs generate at different sizes today — each row states its own canvas
instead of pretending they match.

<!-- MEASUREMENTS:START (scripts/collect_metrics.py) -->
| method | pair | canvas of result | pearson_r | probe 1 % | probe 4 % | edges r | pixels off >0.15 | tile r p10 | tile r med | flat tiles Δ | verdict | steps/cfg | graph timer (s) | free VRAM at collect |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `krea2_edit` | — | — | — | — | — | — | — | — | — | — | **no depth_in/depth_out pair found** (looked for `krea2_edit_depth_*`) | — | — | — |
| `moss_inpaint` | `00001` | 2052×576 | **0.9947** | 0.9894 | 0.946 | 0.6008 | 0.0038 | 0.9252 | 0.9821 | +2 | global geometry held ⚠ result matched by save time, not counter | 25 / 2.5 | — | server not running |
| `qwen_inpaint` | `00001` | 1049×590 | **0.9993** | 0.9895 | 0.9461 | 0.9788 | 0.0001 | 0.9892 | 0.999 | +0 | global geometry held ⚠ result matched by save time, not counter | 25 / 1 | — | server not running |
<!-- MEASUREMENTS:END -->
