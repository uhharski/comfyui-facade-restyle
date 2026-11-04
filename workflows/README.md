# Workflows — the reproducible part

Three graphs, one input photo, one seed. Each graph is saved twice on purpose:

| file | format | what it is for |
|---|---|---|
| `<id>.json` | ComfyUI UI format | the graph you open, look at and edit. Drag it onto the canvas |
| `_api/<id>.api.json` | API format (`Save (API export)`) | the same graph posted to `POST /prompt` by a script. **Frozen**: it is the exact thing a headless run used |
| `manifest.json` | — | machine-readable record of *what was set* in each graph: models, steps/cfg, seed, canvas size as executed, the region used by the appearance metric, and whether the graph can be replayed headless (`replay`) |

Ids: `krea2_edit` (image-edit, no control) · `moss_inpaint` (depth+colour control, layout box) ·
`qwenImage_inpaint` (inpaint mask, stitched back). The three ids match the rows in
[`../docs/metrics.md`](../docs/metrics.md) and the `id` field of `../docs/metrics/measurements.json`.

## What to check before running one

1. `LoadImage` → `DJI_0021.JPG` (the input photo, in the ComfyUI `input/` folder; the repo copy of it
   is `../source/photos/web/DJI_0021.jpg`).
2. The seed node: `KSampler.seed` (A), `LCSeed.base_seed` (B), `AUSBOSS_NODES_Seed.seed` (C) — all
   `20261103` in the saved graphs.
3. **A widget is not what ran.** In these graphs several size/seed widgets are overridden by an incoming
   link (the MOSS sampler's stored seed, and `AspectRatioSimplifier.custom_width/height` which the node
   ignores when an image is linked in and `resolution_source` is off). `manifest.json` records the size
   **as executed**, taken from the saved output files, not from the widgets.
4. Graph C needs a browser: `MaskByTouch` keeps its clicked points as browser state, so a headless
   replay fails with *"the picks were made on another picture"*. To replay it unattended, save its `MASK`
   output and feed `LoadMask` instead. See `manifest.json → replay`.

## Every output image carries its graph

The saved PNGs keep the full workflow in their file metadata (that is ComfyUI's default), so any output
file can be dragged back onto the canvas and the graph comes with it. The prompts, seeds, steps and cfg
of the 20 gallery images are extracted in [`../docs/gallery/prompts.json`](../docs/gallery/prompts.json);
which file each gallery image came from is in
[`../docs/gallery/MANIFEST.md`](../docs/gallery/MANIFEST.md).

## The measurement nodes inside the graphs

Each graph contains, next to the sampler, the nodes that make the run measurable:

* `DepthAnythingV2Preprocessor` (`depth_anything_v2_vits.pth`, res 1024) on the **input** and on the
  **result**, saved as `<prefix>_depth_in-*` / `<prefix>_depth_out-*` — these two images are what
  metric 1 compares;
* overlay/compare nodes (`LCBatchImageComparer`, `LCImageStitchMulti`, `LCImageAddAlphaText`), saved to
  a separate prefix, so the plain result stays clean.

The result node and the measurement nodes are separate `SaveImage` nodes with independent counters, and
two graphs save the result under a different prefix than the measurement nodes — which is why rows are
matched by save time + aspect ratio, and why `manifest.json` can pin a file with `result_pick`.

## Removed from this folder

`index.md` (a generated table) is gone — the same information now lives in `manifest.json` (machine)
and in the root README (human). The old `_orig/` and `_pre-unify/` snapshots and the `_tools/` graph
mover are gone as well: git history has them (`git log -- workflows/`), and the working set is meant to
be exactly the three graphs that produced the measured rows.
