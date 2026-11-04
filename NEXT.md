# Next — what is genuinely open

State at 04.11: three graphs, one measured run each, two metrics documented, gallery with provenance,
README written. The project is presentable as it stands. Everything below is either **evidence that would
turn three anecdotes into a comparison**, or a **publishing decision** — there is no blocked work.

Application target stays 07–10.11 (deadline 21.11). `PROJECT.md` is the original brief and stays as
written; `PROGRESS.md` is the user's file.

## A. Evidence (each item is independent; do them in this order)

1. **A façade region that is not a demo box.** Today the appearance metric measures the MOSS graph's
   leftover layout rectangle: 59.3% of the frame, sky/lawn/road included (`workflows/manifest.json →
   conditions.appearance_region`). Draw the façade once, store it as a mask next to the source photo,
   declare its provenance, re-run the appearance rows. *This is the item that makes metric 2 a
   certificate instead of a comparison.*
2. **3 seeds per method, one stated finish, card from a defined state.** Same prompt text for A/B/C
   (the current three prompts are not the same request — flagged in README § 2), `--cold` before each
   run, and a variance column instead of one row. This also fixes the "the two metrics were computed on
   sibling files" problem (docs/metrics.md § 4.4).
3. **Make C replayable headless.** Wire a `SaveImage` on `MaskByTouch`'s `MASK` output once in the UI,
   then replace the touch nodes with `LoadImage`+`LoadMask` in `_api/qwenImage_inpaint.api.json`. Removes
   the only un-measurable cost row, gives the crop the position record it lacks (see 4), and records *what*
   was masked — the measured Qwen appearance row currently cannot say (the touches stored in that graph are
   named car/chair/table while its prompt talks about the façade; docs/metrics.md § 2).
4. **Declare or remove the Qwen crop.** The current graph saves a 1049×590 crop and nothing stores where
   it came from, so those rows cannot be compared to the source frame. Either save the stitched full
   frame, or write the crop offsets next to the file.
5. **The fourth graph that never ran:** `krea2_depth_control_lora.safetensors` is installed (since 25.10)
   and unused — graph A here went through the identity-edit LoRA with no control signal. A depth-Control
   variant is the cleanest test of "hold geometry with a control signal instead of with prompt words". A
   negative result is still a result; this is the highest-value new graph.
6. Optional, only if time is left: image-to-video on the best still, and a small demo page.

## B. Publishing (needs decisions, not engineering)

7. **Rename the folder and make it the repo.** Nothing in the repo depends on the directory name —
   close this session first (Windows locks the cwd), then
   `mv "J:/Projects/AI/Test" "J:/Projects/AI/e2e-ai"`, `git init -b main` on a fresh clone or push as is.
8. **Decide what stays out of the public repo** before pushing: full-resolution photos are already
   gitignored (`source/photos/*.JPG`); check the Datasmith anonymisation note in
   `source/3d-datasmith/README.md` once more, and the Krea 2 Community License line in README § 8.
9. **A one-page version** of the README for the application itself (the question, compare.jpg, the
   metric-blindness finding, the two tables). The long README is the review artifact.
10. `PROGRESS.md` has no entry for the 04.11 sessions (headless runs, run records, determinism
    findings, the cleanup and the README). The git log covers it, but the file says it is the restore
    state — an entry should be written by whoever owns the file.

## C. Known weak points, stated so nobody is surprised

- The Krea2 pair 00002 row (r 0.3326) mixes a 4032×2268 and a 1820×1024 depth map (a cached source map
  was reused). It is both a measurement artifact and a real failure; the row is flagged.
- One run per method: no variance, three different prompts, canvases differ. All in docs/metrics.md § 4.
- Nothing in this repo starts ComfyUI any more: the measurement scripts were removed on purpose
  (04.11 cleanup), so the numbers live in `docs/metrics/*.json` and their definitions in
  `docs/metrics.md` § 1–2. Re-running anything means running the graphs by hand and, if new rows are
  wanted, writing the measurement code again.
