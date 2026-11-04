# Measurements

Three ComfyUI graphs, **one input photo**, one fixed seed, one GPU. This file says what was
measured, how to read every number, and what the two metrics cannot see.

* input: `source/photos/web/DJI_0021.jpg` (2048×1152 copy of `DJI_0021.JPG`, aerial view of the
  real house, no GPS in the repo copy) — the only image fed into all three graphs
* seed `20261103` in all three graphs (Krea2 KSampler widget · `LCSeed` feeding the MOSS sampler ·
  `AUSBOSS_NODES_Seed` in the Qwen graph). A stale seed still stored in the MOSS sampler widget is
  overridden by its link — a stored widget value is not what ran.
* GPU: RTX 5070 12 GB, ComfyUI 0.43.2. The agent backend *can* hold a model on the same card; each
  run record stores the free VRAM `/system_stats` reported just before that run, so nothing is assumed.
* machine-readable data: `metrics/measurements.json` (geometry rows), `metrics/appearance/*.json`
  (finish rows, one file per row, with the row's own probes inside), `metrics/run_*.json`
  (time + VRAM, one file per headless run). This page is the human-readable view of those files.
* the images these numbers were computed on are in `docs/gallery/`, mapped back to the exact files
  the graphs wrote in `docs/gallery/MANIFEST.md`.

---

## 1. Metric 1 — did the geometry survive (depth map vs depth map)

**Definition.** Each graph saves two depth maps of its own run: `<prefix>_depth_in-*` (from the
source photo) and `<prefix>_depth_out-*` (from its result), both produced by `DepthAnythingV2Preprocessor`
(`depth_anything_v2_vits.pth`, resolution 1024) inside the graph. Both maps are normalised to 0…1 and
resampled to a common small grid (512×288). Then:

| name | what it is |
|---|---|
| `r` | Pearson correlation between the two normalised depth maps — "is the scene still the same shape from the same place" |
| `probe 1%` / `probe 4%` | the same number after shifting one map sideways by 1% / 4% of the width. **This is the scale of the row**: it is what "the camera moved a little" costs, computed from this row's own input, never a constant |
| `edges r` | Pearson correlation of the depth **gradients** — whether the fine structure (roofline, window edges) survived, not just the massing |
| `pixels off` | fraction of pixels whose depth differs by more than 0.15 |
| `flat Δ` | how many of the 8×6 grid areas are flat in the result but full of structure in the input: the numerical shape of "the model smeared the facade over" |

Both metrics run on the CPU after generation; the GPU is never part of a measurement.

**Scale, measured.** On depth maps: identical = 1.00, 1% nudge = 0.99, 4% nudge = 0.95, and the
`pixels off` floor is 0.0 at 0%, 1.5% at 1%, 3.1% at 2%, 5.6% at 4%. On the source **photo** the same
nudges cost much more (1% = 0.81, 4% = 0.56) because photos are not smooth — the two scales must never
be read against each other. Every row is judged against its own `probe` column.

### The rows

| method | pair | r | probe 1% | probe 4% | edges r | pixels off | flat Δ | reading of the row |
|---|---|---|---|---|---|---|---|---|
| `krea2_edit` | 00004 | **0.9967** | 0.99 | 0.9476 | 0.678 | 0.31% | +0 | shape held; local change is under the 1% floor → the depth map cannot see this edit |
| `krea2_edit` | 00003 | **0.9913** | 0.99 | 0.9476 | 0.560 | 0.78% | +0 | shape held, fine structure weaker |
| `krea2_edit` | 00002 | **0.3326** | *0.8082* | *0.5536* | 0.132 | 51.4% | +0 | **the failure row**: the house was redrawn from another position. Its probes are from a different scale (this pair mixes a 4032×2268 and a 1820×1024 map — the run reused a cached source map), so the row is indicative, and it is still a real failure: both readings are true |
| `moss_inpaint` | 00003 | **0.9958** | 0.9894 | 0.946 | 0.653 | 0.31% | **+2** | shape held, but two grid areas became flat texture blobs |
| `moss_inpaint` | 00002 | **0.9947** | 0.9894 | 0.946 | 0.601 | 0.38% | **+2** | same graph, replay |
| `moss_inpaint` | 00001 | **0.9947** | 0.9894 | 0.946 | 0.601 | 0.38% | **+2** | same graph, run from the UI |
| `qwen_inpaint` | 00003 | **0.9996** | 0.9895 | 0.9461 | **0.980** | 0.01% | +0 | shape and every edge held — but outside the mask this is true **by construction** (everything outside is stitched back), so this row says nothing about quality |
| `qwen_inpaint` | 00002 | **0.9993** | 0.9895 | 0.9461 | **0.9788** | 0.01% | +0 | same, second run |
| `qwen_inpaint` | 00001 | **0.9993** | 0.9895 | 0.9461 | **0.9788** | 0.01% | +0 | same, run from the UI |

**How each result image was matched to its depth pair.** The result node and the measurement nodes are
separate `SaveImage` nodes with independent counters, and two graphs save the result under a different
prefix than the measurement nodes. A row therefore matched its result **by save time and aspect ratio**,
which is flagged in `measurements.json` (`pair_note`, `result_candidates` lists everything skipped).
Measured here: a graph writes its result PNG 0–1 s before the depth map made from it and a second later
writes its overlays and stitches — an earlier "nearest in time" rule once picked a 2052×576 stitch
instead of the 1024×576 render, so only candidates with the depth map's aspect are kept and
`result_pick` in `workflows/manifest.json` can pin a file.

---

## 2. Metric 2 — did the finish actually change (colour + surface detail inside a region)

**Why a second metric exists.** Metric 1 is blind to a material swap: the depth of a flat wall does not
change when its finish changes. All three methods scored r ≥ 0.99 while a human looking at the same
files saw three different façades. So the finish needs its own number, with the same discipline: one
formula for every method, computed on the CPU, always read against a floor measured from that row's own
input.

**Definition.** Both images are brought to one common grid — the **smaller** of the two frames, never an
upscale (upscaling a 1024 render to a 4032 photo would report detail the render never had as a loss;
the grid used is printed in every row). Inside a declared region:

| name | what it is |
|---|---|
| `colour EMD` | Earth-Mover distance between the colour histograms inside the region (Hue with the closed-form circular EMD, Sat and Value as ordinary 1-D Wasserstein), averaged over the three channels. This is "the finish changed" |
| `h / s / v` | the same per channel, plus mean hue shift in degrees and mean sat/value deltas, so a change can be described ("warmer, darker") and then checked |
| `detail ×` | mean gradient energy inside the region, result ÷ reference. ≈1 = the surface kept its micro-detail; well below 1 = the finish was painted on flat, which is the usual failure of material work; above 1 = detail was invented |
| `tile p10` | the same ratio for the worst decile of tiles inside the region — one part of a façade can be smeared while the average still looks fine |
| `layout corr` | correlation of a heavily blurred luminance (~1% of the width) inside the region: is the layout of the scene still in the same place? Deliberately **not** the edge measure: a repaint destroys the edge pattern while the roofline stays exactly where it was |
| `edge corr` | correlation of the edge pattern — low here means the fine pattern was repainted, which is what a material change is supposed to do |
| `align search` | the best displacement within ±4% of the width, and how much `layout corr` improves there. This is the number that says what the eye noticed and the global depth `r` did not: the camera moved |
| `floor` | the same measurement between two runs of the same graph with the same prompt and seed. A change is only ever reported as a multiple of that floor |

### The rows

Region used today (all methods, the same pixels): a rectangle `x0.1079 y0.0518 w0.6530 h0.9069`,
**59% of the frame**. It is the MOSS graph's own layout box (node 105), so it is declared, traceable and
for that method the only place an edit is allowed at all — but it is a leftover demo rectangle: sky,
lawn, road and the neighbour's roof are inside it. Until a hand-drawn façade polygon replaces it, every
number below carries that limitation.

| method | result file used | grid | colour EMD | its own floor | ×floor | detail × | tile p10 | layout corr | edge corr |
|---|---|---|---|---|---|---|---|---|---|
| `krea2_edit` | `krea2_edit_00111_.png` | 1024×576 | **0.1208** | 0.00445 | 27× | **0.773** | 0.54 | 0.825 | 0.463 |
| `moss_inpaint` | `Test_2026-11-04_00005_.png` | 1024×576 | **0.1315** | 0.0 (replays byte-identical) | — | 0.952 | 0.61 | 0.752 | 0.116 |
| `moss_inpaint` (not a replay) | `Test_2026-11-04_00007_.png` | 1024×576 | 0.1060 | — | — | 0.707 | 0.43 | **0.368** | 0.191 |
| `qwen_inpaint` (full-frame variant) | `qwen21_inpaint_00039.png` | 2048×1152 | 0.0979 | not measured | — | 1.18 | 0.96 | 0.900 | 0.670 |

Which run-to-run floor was used, and it is itself a result:
* **Krea2**: floor 0.00445, measured against `krea2_edit_00112_.png` — same graph, same prompt, **same
  seed 20261103**, and the distance between them is not zero. That is what "this method is not
  reproducible" means numerically.
* **MOSS**: floor **0.0** — `Test_2026-11-04_00001/00005/00009` are byte-identical files, so this
  method is the deterministic one, and a ratio to its floor is undefined (the colour numbers are still
  55–69× the 1% camera-nudge probe of the same row).
* **Qwen**: the current graph saves a 1049×590 crop chosen around the touched mask, and nothing records
  the crop's position, so no scale relates that crop to the reference frame. The row above is a
  full-frame output of the graph version before the instrumentation pass; the crop rows cannot be
  measured until either the crop is declared or the graph is made to save the stitched full frame.

**Cross-checks that calibrate the scale** (`metrics/appearance/control_*.json`, same code, same region):

| control | colour EMD | detail × | layout corr | what it proves |
|---|---|---|---|---|
| the same file against itself | 0.0000 | 1.000 | 1.000 | the floors are exactly zero/one, or the code has a bug |
| the photo nudged 1% sideways | 0.0021 (aligned 0.0005) | 1.015 | 0.906 → 0.996 after aligning | a camera nudge moves layout, not colour |
| the photo nudged 4% | 0.0068 (aligned 0.0005) | 1.009 | 0.519 → 0.999 | same, harder: raw colour grows, aligned stays at zero |
| the photo turned upside down | 0.0014 | 1.007 | 0.474 | colour statistics alone cannot see that nothing corresponds any more — layout correlation does |
| a flat grey block painted over part of it | 0.0845 | 0.794 (worst tiles 0.21) | 0.803 | what "the model stopped drawing structure there" looks like |
| a different house of the same flight, framed the same | 0.0656 | 0.533 | **−0.108** | the control that has to fire: if a different house did not move these numbers, the region measures nothing |

---

## 3. Cost (time and VRAM), 12 GB card

Headless runs (`POST /prompt` with the API graph in `workflows/_api/`, `nvidia-smi` sampled from
outside ComfyUI every ~1 s; raw records in `metrics/run_*.json`):

| graph | at | free VRAM before the run | wall time | peak GPU used | note |
|---|---|---|---|---|---|
| `krea2_edit` | 04.11 00:25 | 10980 MiB | 61.5 s | 10742 MiB | cold: weights had to be loaded |
| `krea2_edit` | 04.11 00:29 | 1389 MiB | **4.2 s** | 9708 MiB | warm: cached nodes were skipped, only the sampler re-ran |
| `moss_inpaint` | 04.11 00:33 | 4531 MiB | 49.1 s | 10605 MiB | |
| `moss_inpaint` | 04.11 00:34 | 165 MiB | 52.4 s | **11293 MiB** | this graph comes closest to filling the card |
| `qwen_inpaint` | 04.11 00:39 | 841 MiB | 86.8 s (the run itself failed in 2.4 s) | 10070 MiB | **no output**: `MaskByTouch` keeps its touched points as browser state, so the headless replay dies with *"the picks were made on another picture"*. The graph cannot be replayed headless until the mask is saved to a file and loaded instead of touched |

These five numbers are **not yet a ranking**: they started from different free-VRAM states, one is cold
and one warm, and the Qwen row is a failed run. A ranking needs: start the card from a defined state,
3 seeds per method, the same stated material prompt, and nothing else using the card. Two of three
methods can be replayed by a script; one cannot — that is itself a finding.

---

## 4. What these two metrics cannot see (say this before anyone reads the tables as a verdict)

1. **The finish is not judged for quality.** Metric 2 says *that* and *how much* the appearance changed
   and whether detail survived; it does not say whether the plaster looks like plaster. That is a human
   check, and it is part of the method: `docs/gallery/compare.jpg` exists for it.
2. **The region is wrong.** 59% of the frame including sky and lawn. A global light change inside it
   moves the colour number as much as a new façade does.
3. **Global depth `r` is a coarse test.** It gave 0.9947 to a MOSS run that moved the camera to a
   different, closer angle — `edges r`, the tile columns, `layout corr` and the human check all noticed.
   A material-only change is *allowed* to leave depth untouched, and a method that edits inside a small
   mask changes almost no pixels by construction, so "no measurable depth change" means *the geometry
   test cannot see the edit*, not *the edit is wrong*.
4. **The two metrics were not always computed on the same file.** Krea2: geometry 00113, appearance
   00111. MOSS: geometry 00001/00003, appearance 00005 — all replays of one frozen graph, and MOSS is
   deterministic, so the pairs are interchangeable; Krea2 is not, so its two numbers describe two
   sibling samples of the same request. Qwen's appearance row is a different, full-frame graph version.
5. **One run per method is not a comparison.** Variance is unknown; the three prompts are not the same
   request (only the Krea2 and Qwen runs were told what finish to make; the MOSS run was told
   "apply modern façade finishing materials" and it chose).
6. **Canvases differ** (1024×576 for Krea2 and MOSS, a 1049×590 crop for the current Qwen graph). A
   size widget in a saved graph is frequently overridden by an incoming link — the size of the saved
   file is the only trustworthy record, and each row states it. In the MOSS graph specifically, with
   `resolution_source` off and an image linked into `AspectRatioSimplifier`, the node takes the image's
   own aspect and fits the long side to `max_resolution`, ignoring `custom_width/custom_height`.

---

## 5. Reproducing any row

1. Start ComfyUI (`J:/AI/ComfyUI-Easy-Install/ComfyUI`, 0.43.2) with the models and nodes listed in
   the root README.
2. Open the UI graph from `workflows/` (or post `workflows/_api/<graph>.api.json` to `/prompt` for the
   two graphs that support it), check `LoadImage` points at `DJI_0021.JPG`, and run it. The graphs save
   `<prefix>_<n>_.png`, `<prefix>_depth_in-*.png`, `<prefix>_depth_out-*.png`.
3. The scored rows are the runs already recorded in `metrics/`. The measurement code that produced them
   is not in this repo any more (it was reduced on purpose); the definitions in § 1 and § 2 are the
   complete description, and `metrics/*.json` hold every number with its own probes.
