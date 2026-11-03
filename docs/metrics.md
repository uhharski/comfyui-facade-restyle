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

<!-- MEASUREMENTS:START (scripts/collect_metrics.py) -->
## Conditions these rows share (from `workflows/manifest.json`)

* input photo: `DJI_0021.JPG` — the same single image in all three graphs
* fixed seed: `20261103` — fixed in all three graphs (the krea2 KSampler widget, the LCSeed node feeding the MOSS sampler, the Seed node of the Qwen graph); a stale seed number still stored in the MOSS sampler widget is overridden by its link
* GPU: RTX 5070 12 GB — the agent backend CAN run a model on this same card, but whether one was resident during a given run is not assumed either way: every run record stores the free VRAM reported by /system_stats immediately before that run, and `run_workflow.py --cold` can clear the card first to make the starting state defined. Measured on 04.11 the five headless runs began with 10980, 4531, 1389, 841 and 165 MiB free — the largest peak (10742 MiB) happened when the card was empty, so an earlier blanket claim that a chat model was sitting on the GPU during these rows is not true of them and was removed
* **not controlled:** NOT unified today, and this is a real difference in cost. Measured from the saved result images on 03.11 (not from the graphs' widgets): the MOSS graph generated 1024x576 (its aspect node shows custom 1024x1024, but an incoming link overrides that widget — a stored value is not what ran; the 2052x576 file in the same folder is the source+result stitch, not a canvas), the Qwen graph generated 1049x590 (a ~0.59 megapixel crop chosen around the touched mask). The Krea2 graph resizes to 1024x576 before the latent. All three are now close to 1024x576, so the cost comparison is roughly fair — the remaining difference is the Qwen crop. Each row states the real size of the saved result image
* **starting state of the measured runs** (from their own records): `krea2_edit` 1389 MiB free; `krea2_edit` 10980 MiB free; `moss_inpaint` 165 MiB free; `qwen_inpaint` 841 MiB free — a cold start and a warm one are different measurements, and a peak of used memory means nothing without the free memory the run began with
* **cannot be replayed headless** (so no controlled cost row exists for it): `qwen_inpaint`: the MaskByTouch node stores its touched points as UI state, not in the exported graph, so a headless replay of its API graph fails with 'RuntimeError: Mask by Touch: the picks were made on another picture' (measured 04.11 00:39, prompt 590dee99; the run reported status error, executed in 2.37 s and wrote no file). Its rows are produced by UI runs only. To make it measurable like the others: save the mask as a file (the node offers that) and replace the touch node with a mask loader
* ComfyUI was not reachable while collecting, so there is no live reading of its memory state in this run of the script (the columns say so)

| method | pair | canvas of result | pearson_r | probe 1 % | probe 4 % | edges r | pixels off >0.15 | tile r p10 | tile r med | flat tiles Δ | verdict | steps/cfg | run time, s | peak GPU vs starting state |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `krea2_edit` | `00004` | 1024×576 | **0.9967** | 0.99 | 0.9476 | 0.6777 | 0.0031 | 0.9338 | 0.9918 | +0 | global geometry held + no measurable depth change (0.31 % of the pixels off, under half the 1 % camera-nudge floor of 1.47 %) ⚠ result matched by save time, not counter ⚠ the two maps of this pair are 54.4 s apart | 10 / 1 | wall 4.2 / queue/exec not separated (older record — wall may include queue wait) / warm: weights already loaded, cached nodes skipped | 9708 MiB used / 1389 MiB free before |
| `krea2_edit` | `00003` | 1024×576 | **0.9913** | 0.99 | 0.9476 | 0.5598 | 0.0078 | 0.9023 | 0.9904 | +0 | global geometry held ⚠ result matched by save time, not counter ⚠ the two maps of this pair are 32.3 s apart | 10 / 1 | wall 4.2 / queue/exec not separated (older record — wall may include queue wait) / warm: weights already loaded, cached nodes skipped | 9708 MiB used / 1389 MiB free before |
| `krea2_edit` | `00002` | 1024×576 | **0.3326** | 0.8082 | 0.5536 | 0.1317 | 0.514 | -0.5318 | 0.0849 | +0 | global geometry lost ⚠ result matched by save time, not counter ⚠ the two maps of this pair are 69.8 s apart ⚠ the two maps have different working resolutions (4032x2268 vs 1820x1024) | 10 / 1 | wall 61.5 / queue/exec not separated (older record — wall may include queue wait) | 10742 MiB used / 10980 MiB free before |
| `moss_inpaint` | `00003` | 1024×576 | **0.9958** | 0.9894 | 0.946 | 0.6525 | 0.0031 | 0.9298 | 0.9901 | +2 | global geometry held + no measurable depth change (0.31 % of the pixels off, under half the 1 % camera-nudge floor of 1.56 %) ⚠ result matched by save time, not counter ⚠ the two maps of this pair are 277.9 s apart | 25 / 2.5 | — (no run record wrote these files) | — |
| `moss_inpaint` | `00002` | 1024×576 | **0.9947** | 0.9894 | 0.946 | 0.6008 | 0.0038 | 0.9252 | 0.9821 | +2 | global geometry held + no measurable depth change (0.38 % of the pixels off, under half the 1 % camera-nudge floor of 1.56 %) ⚠ result matched by save time, not counter ⚠ the two maps of this pair are 43.6 s apart | 25 / 2.5 | wall 52.4 / queue/exec not separated (older record — wall may include queue wait) | 11293 MiB used / 165 MiB free before |
| `moss_inpaint` | `00001` | 1024×576 | **0.9947** | 0.9894 | 0.946 | 0.6008 | 0.0038 | 0.9252 | 0.9821 | +2 | global geometry held + no measurable depth change (0.38 % of the pixels off, under half the 1 % camera-nudge floor of 1.56 %) ⚠ result matched by save time, not counter ⚠ the two maps of this pair are 42.0 s apart | 25 / 2.5 | — (no run record wrote these files) | — |
| `qwen_inpaint` | `00003` | 1049×590 | **0.9996** | 0.9895 | 0.9461 | 0.98 | 0.0001 | 0.9912 | 0.9991 | +0 | global geometry held + no measurable depth change (0.01 % of the pixels off, under half the 1 % camera-nudge floor of 1.57 %) ⚠ result matched by save time, not counter ⚠ the two maps of this pair are 53.0 s apart | 25 / 1 | wall 86.8 / queue/exec not separated (older record — wall may include queue wait) | 10070 MiB used / 841 MiB free before |
| `qwen_inpaint` | `00002` | 1049×590 | **0.9993** | 0.9895 | 0.9461 | 0.9788 | 0.0001 | 0.9892 | 0.999 | +0 | global geometry held + no measurable depth change (0.01 % of the pixels off, under half the 1 % camera-nudge floor of 1.57 %) ⚠ result matched by save time, not counter ⚠ the two maps of this pair are 8858.7 s apart | 25 / 1 | wall 86.8 / queue/exec not separated (older record — wall may include queue wait) | 10070 MiB used / 841 MiB free before |
| `qwen_inpaint` | `00001` | 1049×590 | **0.9993** | 0.9895 | 0.9461 | 0.9788 | 0.0001 | 0.9892 | 0.999 | +0 | global geometry held + no measurable depth change (0.01 % of the pixels off, under half the 1 % camera-nudge floor of 1.57 %) ⚠ result matched by save time, not counter ⚠ the two maps of this pair are 93.8 s apart | 25 / 1 | — (no run record wrote these files) | — |
<!-- MEASUREMENTS:END -->
