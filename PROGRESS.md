# Progress log

Newest entry on top. One entry per work session: what was done, decisions + why,
problems found, next step. This file + `PROJECT.md` are the complete restore state —
a new agent session only needs to read both.

---

## 2026-11-04 (19:45) — first video: the MiniMax H3 graph and its sample

### Done
- `workflows/MMH3.json` entered the repo: a **MiniMax H3 FL2V** (first+last-frame-to-video) graph —
  two Qwen-inpaint renders of the house as the first/last frame, the camera glide and the soundscape
  asked in words, its own video+audio VAEs. It is the first output of the video branch (next-steps
  item 6), and it is deliberately **not** part of the measured three: no depth/compare nodes, no
  `_api` copy, no rows in `docs/metrics.md`.
- Its single result, the ComfyUI output `2026-11-04/video_03.mp4` (19:01), is kept byte-exact at
  `docs/gallery/video/video_03.mp4` (1024×576, 24 fps, 5.17 s, 124 frames, H.264 + AAC).
- Provenance recorded where the repo's rules say it must be: a video section in `gallery/MANIFEST.md`
  + an entry in `MANIFEST.json`, a fourth record in `workflows/manifest.json`, and the "three graphs"
  wording in `workflows/README.md` / root README corrected to name the fourth graph.

### Honest holes found while recording it (all written down, not papered over)
- **The prompt and the widget disagree about length.** The prompt aligns the two pictures at 0.00 s
  and 15.08 s of "the target video"; the duration widget says 5 s and the frame-count expression
  made 124 frames → a 5.2 s file. Parameters were recorded from the saved file, per the standing rule.
- **The two input frames had a name collision - now byte-pinned.** The graph loads them by name
  (`qwen21_inpaint_00015/00014.png`) from ComfyUI `input/`, and the ComfyUI outputs of those names
  exist twice by date (02.11 12:2x and 04.11 12:32) with **identical bytes** - reused counters, or a
  fixed-seed style variant reproducing itself. During this session the frames were preserved in the
  repo: `docs/gallery/video/first_frame.jpg` is the byte-identical former gallery row
  `qwen_inpaint/style_charred-plus-timber.jpg` (moved into `video/`), `docs/gallery/video/last_frame.png`
  is the byte-identical 4032x2268 output of `qwen21_inpaint_00014.png`, itself a previously
  uncatalogued shou-sugi-ban-plus-timber style variant (its embedded seed 139346433945169).
- The graph as saved runs seed 4 fixed, 6 steps, cfg 1.0, `res_multistep`; the turbo LoRA is stacked
  but switched off.

### Next step (only if the video branch is to be measured)
- Add the depth/compare nodes to MMH3 like the measured graphs have, save the two frame inputs into
  the repo, and make an `_api` export so the run can be replayed headless.

---

## 2026-11-03 (23:00) — the third method ran; three rows exist; the metric itself is now the problem

### Done
- Ran the instrumented `krea2_edit` graph in the UI (22:49) → its depth pair appeared →
  `collect_metrics.py` now scores **all three methods**. Table is complete for one run each.
- Added the missing half of the measurement chain: `collect_metrics.py` reads
  `docs/metrics/run_*.json` written by `run_workflow.py` (wall time + whole-GPU peak) and puts a
  record in a row **only if that run was going on when the row's files were saved** — the two
  columns `run time (s)` / `peak GPU used` replace the never-populated `graph timer` column, and
  the header says plainly why they are dashes until a headless run exists.
- Generated the conditions block straight into `docs/metrics.md` (shared input photo, fixed seed,
  GPU + the fact that a local chat model occupies the card, and what is **not** controlled) so a
  reader sees the fairness caveats next to the numbers instead of having to open the manifest.
- Wrote `scripts/contact_sheet.py` → `docs/gallery/compare.png`: the source photo and the three
  results at the same tile width, each labelled with the numbers of that same run. The tiles come
  from `measurements.json`, so the picture and the table cannot drift apart.

### Fixed: the two result-matching rules were wrong in a way that mattered
- Matched “nearest in time” picked, for the MOSS graph, `Test_2026-11-03_00012_.png` **2052×576**
  — that is the source+result stitch made by the LCImageStitchMulti node, not the render. So the
  first MOSS row quoted a canvas that was never generated, and the contact sheet showed a
  layout/preview image instead of a house. Measured on this machine: a graph writes its result PNG
  **0–1 s before** the depth map made from it, then a second later the stitches/overlays.
  New rule: keep only candidates with the **aspect ratio of the depth map**, take the last one
  saved at or before it, list everything skipped (`result_candidates` + the note), and allow
  `result_pick` in the manifest to pin a file. MOSS now resolves to `00011` **1024×576** and the
  2052×576 stitch is named as skipped. My earlier `canvas_note` (“MOSS generated 2052×576”) was
  wrong and is corrected — all three methods are actually at ~1024×576, so the cost comparison is
  close to fair after all.
- `verdict()` had no case for “the method did nothing”. Now the local-change claim is judged by
  each run's own floor, measured: the same bad-fraction on the input map against itself = **0.0 at
  0 %, 1.64 % at a 1 % camera nudge, 3.1 % at 2 %, 6.0 % at 4 %**. Below half the 1 % figure the
  verdict says “no measurable depth change”. All three rows land there (0.61 / 0.38 / 0.01 %).

### Numbers of this first complete comparison (one run each, seed 20261103)
| method | canvas | r | edges r | pixels off | flat tiles Δ |
|---|---|---|---|---|---|
| krea2_edit (no control) | 1024×576 | 0.9936 | 0.6553 | 0.61 % | 0 |
| moss_inpaint (color+depth+boxes) | 1024×576 | 0.9947 | 0.6008 | 0.38 % | +2 |
| qwen_inpaint (mask+stitch) | 1049×590 | 0.9993 | 0.9788 | 0.01 % | 0 |

### What the images say that the numbers did not (the human half, now part of the method)
- All three produced a believable different finish of the *same* house: Krea2 → smooth beige
  plaster; Qwen → same, cleanest, facade only; MOSS → yellow brick with wooden frames.
  So the material task succeeded while `bad_frac` stayed ~0 → **the depth metric is blind to a
  colour/texture swap**, which is expected (a flat wall stays flat in depth) and is now written
  into the docs instead of pretending the number covers it.
- **The global r failed to notice that MOSS moved the camera**: its tile shows the house from a
  different, closer angle, yet r = 0.9947. `edges r` (0.60) and the tile columns did notice.
  Conclusion for the README and for the metric: global pearson on normalised depth is a coarse
  “same house, roughly same place” test, not a viewpoint test.

### Problems / next step
1. **A second measure is needed for “the finish actually changed”**: the geometry metric cannot
   see it. Cheapest honest option: an appearance delta inside a stated facade region (colour
   histogram + texture energy against the source, with the region drawn once by hand or reused
   from the MOSS layout boxes) — plus the existing human check via `contact_sheet.py`. Not
   written yet; do not claim “materials measured” until it is.
2. Time/VRAM still empty: run `python scripts/run_workflow.py <id>` with ComfyUI up — the API
   graphs for all three are already in `workflows/_api/`. Also worth re-checking why `LCTimer`
   keeps `lc_runs` empty (the UI run at 22:49 recorded nothing).
3. Multiple seeds per method: one run per method is not a comparison — variance is unknown, and
   Krea2/Qwen/MOSS all need the same *explicit* material instruction (the current prompts differ:
   the MOSS run changed the viewpoint and the window frames, i.e. it solved a different task).
4. Naming fix in the graphs (result SaveImage = graph id) would remove the ⚠ flags entirely.
5. Then: README arc + conclusions; the honest arc is now: “built three controllable pipelines →
   all three keep the house → the metric I wrote cannot see the part that matters (the finish) and
   under-detects a viewpoint change → here is what it does catch and what I would add next”.

---

## 2026-11-03 (late) — measurement scripts fixed, first two rows of the table are real

⚠ The previous work session (03.11, 19:00–22:10) was **never written here** — the state below
was reconstructed from git + files. Written now so a new session does not have to redo it.

### What the 03.11 (19:00–22:10) session did (reconstructed)
- Replaced the A/B/C plan with **three real comparison graphs, all on one input photo**
  (`source/photos/DJI_0021.JPG`, aerial, no GPS): `workflows/krea2_edit.json` (edit only, no
  control signal), `workflows/moss_inpaint.json` (MOSS color+depth control + layout boxes),
  `workflows/qwenImage_inpaint.json` (mask inpaint + stitch back). The A/B/C letters are now a
  writing decision, not a file-structure one (see the `_note` in `workflows/manifest.json`).
- `workflows/manifest.json` became the single source of truth for the scripts (ids, prefixes,
  conditions, seed 20261103 fixed in all three graphs).
- All three graphs were instrumented identically (`workflows/_tools/`): `LCTimer` node, two
  `DepthAnythingV2Preprocessor` + SaveImage nodes (`<prefix>_depth_in/_out`) — originals kept
  in `_orig/`, the pre-unification state in `_pre-unify/`, and the log in `_tools/unify_report.txt`.
- Wrote the measurement toolchain: `scripts/lib.py` (asks a running ComfyUI `/object_info`
  which widgets are real, so a value overridden by a link is not reported as the setting),
  `geometry_score.py` (pearson_r + self-nudged probes + gradient + 8×6 tile grid + flat-tile
  counter), `collect_metrics.py`, `make_index.py`, `trace_size.py`, `photos.py`,
  `import_api_from_history.py` (pulls the API graph of a run out of ComfyUI history instead of
  hand-exporting), `run_workflow.py` (headless run + wall time + peak GPU memory).
- `docs/metrics.md` created with the reading instructions; `workflows/index.md` generated.
- Queued runs in the UI at 22:02–22:09: depth pairs exist for **moss_inpaint and qwen_inpaint**,
  none for **krea2_edit**.

### What this session did
- Ran `collect_metrics.py`: it scored **nothing** although the pairs were on disk. Two real bugs:
  1. `lib.COUNTER_RE` only knew the old `prefix-00001.png` counter form, while this ComfyUI
     (0.43.2) writes `prefix_00001_.png` (trailing underscore). depth_in and depth_out of one
     run got different pair keys → no pair ever formed. Fixed: the regex accepts both forms.
  2. The result image is saved by the graphs under **different prefixes** than the measurement
     nodes: the Qwen graph → `qwen21_inpaint_*`, the MOSS graph → a date prefix inside a
     subfolder (`MOSS Box Edit/Test_2026-11-03_NNNNN_.png`). So the canvas column stayed empty.
     `find_measurement_pairs()` now takes an explicit `result_prefix` (in the manifest, with a
     `result_prefix_note` per graph) and falls back to matching by save time (±30 min) because
     **counters restart per prefix** — such a row is flagged `⚠ result matched by save time`,
     never presented as certain.
- Filled the table (2 of 3 methods scored, first honest numbers):
  - `moss_inpaint` 2052×576: r **0.9947** vs its own 1 % probe 0.9894 → geometry held, but
    **edges r only 0.60** and **+2 flat tiles** — the fine structure (window/roof lines) was
    repainted, some areas became texture blobs. Local change tiny (0.4 % of pixels), so this is
    a warning about the method, not a success.
  - `qwen_inpaint` 1049×590: r **0.9993**, edges **0.9788**, local change 0.01 % — geometry is
    preserved **by construction** (stitch outside the mask), so the interesting question for
    this method is only the quality inside the mask, which these numbers do not measure.
  - Both probes (0.9894 / 0.946) are far above the photo calibration quoted in the header
    (0.81 / 0.56). Not a contradiction: those were **photo** probes, depth maps are smoother.
    The text in `docs/metrics.md`, `collect_metrics.py` and `geometry_score.py` now states the
    two scales separately and quotes the measured depth-map probes, so a reader cannot mix them.
- Corrected `manifest.json → canvas_note` from the real saved canvases: the MOSS graph generated
  **2052×576**, not the 1024×1024 written in its aspect node — an incoming link overrides it.
  Exactly the case the /object_info logic exists for; the note now says so.
- Regenerated `workflows/index.md`, re-ran `collect_metrics.py` (idempotent, table only).

### Problems found, not yet fixed
- `krea2_edit` still has **no depth pair** → no third row. Its API graph *is* in
  `workflows/_api/krea2_edit.api.json` (imported from history, includes the instrumentation
  nodes), so `python scripts/run_workflow.py krea2_edit` is enough — ComfyUI has to be running.
- **`LCTimer` recorded nothing** in any of the three graphs (`lc_runs` empty), so the
  `graph timer (s)` column is “—” even though runs happened. `run_workflow.py` measures wall
  time + peak GPU memory itself into `docs/metrics/run_*.json`, but **`collect_metrics.py` does
  not read those files yet** — that merge is the missing link for the time/VRAM columns.
- Naming bugs to fix in the graphs (or keep the manifest workarounds): result SaveImage prefix
  should equal the graph id (`qwen21_inpaint` → `qwen_inpaint`, MOSS result nodes → `moss_inpaint`).
- `index.md` still prints “parameter names unavailable” for the MOSS graph's Set/Get/Note nodes:
  those types are not in the cached `.object_info.json`. Harmless for numbers (values are
  positional there), but it should be stated rather than look like a script failure.

### Next step
1. Start ComfyUI, run `python scripts/run_workflow.py krea2_edit` → get the third depth pair and
   the first real wall-time/VRAM record, then `collect_metrics.py`.
2. Teach `collect_metrics.py` to pick up `docs/metrics/run_*.json` (time + peak VRAM per row)
   instead of relying on the empty `LCTimer` history.
3. Decide the canvas question: with 2052×576 vs 1049×590 vs (1024×576) the cost comparison is
   unfair; unify the canvases in the graphs or state cost per megapixel in the table.
4. Only after three rows exist: start writing the README arc and the A/B/C conclusions.
5. Keep the rule: write here before closing a session (this entry is one session late).

---

## 2026-10-25 (evening) — hardware measured, Workflow A unblocked

**Done**
- Recorded hardware (was an open question in PROJECT.md § 8, blocked the quantization/metrics
  plan): **RTX 5070 12 GB VRAM, Ryzen 7 5700X, 64 GB RAM** (via nvidia-smi / wmic) → added as PROJECT.md § 5.2.
  12 GB is the honest "runs on modest hardware" story: the fp8 Krea2 checkpoints are 13 GB,
  so they cannot stay fully resident → ComfyUI CPU offload / lowvram path is the real
  configuration, and we will measure peak VRAM + s/it rather than pretend otherwise.
- Audited the ComfyUI side of the plan and found a **hard blocker for Workflow A (task 3)**:
  the `comfyui-krea2-controlnet` node was installed, but **no Control LoRA weights existed**
  anywhere under `models/loras` (only identity-edit / style LoRAs). Without them the pipeline
  cannot run at all.
- Installed the public depth Control LoRA (`Patil/Krea-2-depth-controlnet`, HF,
  `depth-control-lora.safetensors`, 862 MB, size verified against the HF content-length)
  → `models/loras/Krea2/krea2_depth_control_lora.safetensors`. Documented in PROJECT.md § 5.3
  with the node's recommended depth settings (grayscale / per_image_minmax / invert=false).
- Inventoried what is actually available: Krea2 fp8/INT8 community mixes only
  (darkBeast, krea2SATDirtyrealism, pornmasterKrea2_turbo, muse INT8) — **no official
  Krea-2-Raw**; Qwen VAE present (needed by `Krea2 Control Image Encode`); Gemma text encoder
  present; `comfyui_controlnet_aux` installed; first outputs `krea2_edit_*` / `krea2_candidate_*`
  / `krea2_final_*` exist in `ComfyUI/output` as "before" material.

**Decisions**
- Depth is the primary control signal for approach A (the only public Krea2 Control LoRA);
  canny/lineart weights may not exist publicly → treat lineart from UE5 as a *comparison
  render pass* and via `comfyui_controlnet_aux` for the honest A-vs-B table, not as a control
  LoRA. Don't promise "4 control types" in the README.
- Measure at 1024–1280 px, log VRAM/peak memory and time per iteration into `docs/metrics.md`
  (to be created during tasks 3–5).

**Found problems**
- The depth LoRA is trained on Krea-2-Raw, but the local UNets are derived fp8/INT8 mixes.
  The node raises an error when no compatible block weights load, so the first smoke test is
  a real test — "LoRA accepted the mix but does nothing visually" is a failure mode to report,
  not to hide. Try turbo/plain fp8 first.
- **License:** the Control LoRA is under the *Krea 2 Community License*, not MIT. Must be
  declared in the repo before publishing weights/outputs publicly.
- The 3D source folder holds two Datasmith exports (`house.udatasmith`, 04.03 = older v1, and
  `v2.0/v2_0.udatasmith`, 05.03 = newer). Confirmed v2.0 is the intended one; noted in
  PROJECT.md § 5.1 so a future session does not pick the older file by accident.

**Next step (25–27.10 milestone, in order)**
1. Unattended smoke test of Workflow A: one existing white-ish image → Depth Anything preproc →
   `Krea2 Control Image Encode` → depth LoRA → sampler. Purpose: prove the LoRA patches the
   fp8 mix and get a VRAM/time baseline *before* any UE5 export work. Doable via ComfyUI API
   (headless) instead of the web UI.
2. If it patches: open the Datasmith scene in UE5 (or the free Datasmith Converter), check
   import scale/normals, set up unlit + PostProcess volume depth/lineart views → first façade
   render + its exact depth pass (task 1–2).
3. If it does not patch: try Krea-2-Raw/GGUF route and record the failure in the README arc.

---

## 2026-10-25 (later) — 3D source located

- Path provided by me and inspected: `C:/Users/vikto/Desktop/Dom/3d/v2.0` — it is a
  **Datasmith export from ArchiCAD 29** (`v2_0.udatasmith`, 184 static meshes, .tiff
  textures, ~41 MB), not a .uproject. Corrected PROJECT.md § 5.1/§ 7/§ 8.
- Implication: ArchiCAD is the BIM source; the PDF floor plan is very likely vector.
  Next time open it in UE5 (Datasmith plugin) or the free Datasmith Converter and check
  import quality (norms, materials, scale).

---

## 2026-10-25 — Project kickoff

**Done**
- Chose target: Junior AI Engineer (image/video generation), Luminary Ventures OÜ /
  MyArchitectAI. Hard deadline 21.11.2026 → **self-set target: apply 07–10.11, finish by 05.11**.
- Read and translated the job ad; extracted its actual criteria into PROJECT.md § 4.
- Idea fixed: personal house build (no design project, only a PDF floor plan) doubles as
  the portfolio project — "floor plan → white model → controlled generation of finishes".
- Inventoried local setup: ComfyUI at `J:/AI/ComfyUI-Easy-Install/ComfyUI`, Krea 2 fp8
  weights, Krea2 control/edit/style-ref/NAG/enhancer nodes, first `krea2_edit_*` experiments exist.
- Discovered the existing **UE5 house visualization incl. a VR version** (bare interiors,
  no furniture — kept as-is on purpose, it is the ideal white-model input).
- Wrote PROJECT.md (plan, A/B/C approaches, reverse schedule); created this PROGRESS.md.

**Decisions**
- Pipeline uses the existing UE5 scene instead of rebuilding in Sweet Home 3D
  (exact depth/lineart render passes, VR clips for later video experiments).
- Three branches for the comparison story: A = depth-control via Krea2 Control LoRA;
  B = direct edit on 2D plan (expected failure, report honestly);
  C = furniture blockers + masks for real-size furniture (optional).
- Project docs in English (job working language).

**Found problems / open questions**
- UE5 project path not recorded yet; publication rights (asset licenses / NDA) unknown.
- PDF: vector or scan — decides tracing route (not that critical anymore, UE5 scene exists).
- GPU/VRAM specs not written down yet (needed for the quantization/metrics section).

**Next step (25–27.10 milestone)**
1. Record the UE5 project location; set up white-model view modes (unlit / lineart / depth).
2. `git init` in this folder, first commit.
3. Export first renders (façade ×1 to start) and run the first Krea2 Control test.
