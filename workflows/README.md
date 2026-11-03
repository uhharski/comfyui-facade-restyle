# Workflows (ComfyUI) — the reproducible part of the project

This folder holds the **workflow definitions** that produced every generated image in this
repo. A generated PNG without its workflow is not evidence; with the workflow + model list +
metrics it is reproducible, which is exactly what the job requirements ask for
("public work: ComfyUI workflows", "comparisons with conclusions" — see root `PROJECT.md` § 4).

## Layout

```
workflows/
  README.md          this file
  <id>_<short-name>.json     the workflow as used (see "Naming" below)
  _api/                    API-format exports, used for headless / scripted runs
  index.md                 table: id → what it does, which checkpoints/LoRAs, result, notes
```

Put the `.json` files straight in this folder (flat list is fine at this project's scale);
`_api/` is created when we first run something headless.

## Naming

`<approach><number>_<what>_<variant>.json`

```
A01_depth_lora_smoketest.json          approach A = depth control (Krea2 Control LoRA)
A02_depth_plaster_variant.json
B01_plan_direct_edit.json              approach B = 2D plan straight into edit
C01_furniture_mask_inpaint.json        approach C = furniture blockers + masks
```

Approach letters match `PROJECT.md` § 3. The number is a real experiment index, not a
vague "final_final" — every run that we quote in the comparison table must be traceable
to one file here.

## Two formats, why both

| Format                | How to get it in ComfyUI                        | Use                                            |
|-----------------------|-------------------------------------------------|------------------------------------------------|
| UI format (default `Save`) | menu → *Save (export)*                      | the human-editable graph, for the README/review |
| API format                | menu → *Save (API format)* → `_api/…json`  | headless run via `POST /prompt`, no web UI      |

The UI-format JSON embeds node sizes/links and is what a reviewer opens in ComfyUI.
The API-format one is what my scripts re-run to re-measure VRAM and time, so the numbers
in `docs/metrics.md` are not a one-off screenshot.

Also useful: ComfyUI PNG output keeps the workflow inside the PNG metadata, so a gallery
image can be dragged back onto the canvas to recover its graph. Still commit the JSON —
metadata disappears on resizing/re-encoding.

## Per-workflow metadata to record

For every workflow, add a short block at the top of `index.md` (or a `<id>.md` if it grows):

```
id:        A01
goal:      prove the depth Control LoRA actually patches a fp8 mix
checkpoint: models/diffusion_models/Krea 2/pornmasterKrea2_turboV1FP8.safetensors
control lora: models/loras/Krea2/krea2_depth_control_lora.safetensors
text enc:  Gemma (…)
VAE:       Qwen (…)
control:   Depth Anything preprocessor (grayscale / per_image_minmax / invert=false)
size:      1024x…   steps: …   cfg/sigma: …   seed: …
result:    works / patches but weak / fails (error text)
peak VRAM: … MiB   time: … s/it, total … s
verdict:   used / abandoned because …
```

The `verdict` line matters most for the README arc ("what I built → what broke → how I
measured the fix"): a workflow that was abandoned is worth as much as one that worked.

## Missing pieces to write down on purpose

- **Machine-readable model provenance**: checkpoints are community fp8/INT8 mixes; note the
  exact filename, not "Krea 2 fp8".
- **Licenses**: the depth Control LoRA is under the **Krea 2 Community License** (not MIT) —
  declared before publishing outputs.
- **Seeds**: fixed seeds for anything shown in the before/after gallery, so a reviewer can
  reproduce it.
