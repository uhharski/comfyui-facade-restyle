# Next tasks (open when the session ends — resume from here)

Status at writing time: `docs/metrics.md` has 9 scored rows (3 methods × 3 depth pairs), every row
flagged where the evidence is weak; every cost number is tied to a run record and states how that
tie was made. Nothing here is a bug list — these are decisions and the work that depends on them.

Restore state of the project itself: read `PROJECT.md` and `PROGRESS.md` first (`PROGRESS.md` is
the user's file — do not edit it unless asked). Note that its newest entry (2026-11-03 23:00)
does **not** cover the 04.11 work — the headless runs, the run records, the pairing fixes and the
determinism findings are recorded in the git log (`984c607`, `0a16c51`), in
`docs/metrics/run_*.json` and in `workflows/manifest.json` under `replay`.

---

## A. Do first — the metric's blind spot (needs no GPU, no ComfyUI: pure CPU on files that exist)

The geometry score measures one thing: whether the structure of the scene survived. It is
**blind to the material swap**, because the depth map of a flat wall does not change when its
finish changes. Today the only appearance numbers that exist were computed in a chat session and
are **not in the repo** (Krea2 0.124 / MOSS 0.125 / Qwen 0.054 mean absolute difference over the
whole image, sky, lawn and neighbours included) — so they cannot be quoted in the table or in any
text. Only one related number is recorded: the Krea2 repeat-run difference 0.0139, in
`workflows/manifest.json` (`replay.determinism`) and `workflows/index.md`.

1. **`scripts/appearance_score.py`** — measures the thing the task is actually about, inside a
   declared region:
   - distance between colour histograms inside the region (Hue/Sat + value, Earth Mover distance),
     i.e. "the finish changed";
   - texture energy there (local gradient/variance statistics), i.e. "the facade kept its detail"
     — this is what catches a smeared-paint result that global r still calls perfect;
   - the number is only ever reported against this method's **own noise floor**: the same
     measurement between two runs with the *same* prompt and seed. For Krea2 that floor is already
     known (mean abs. diff 0.0139 between two runs of the same graph and same seed). The output
     sentence is "the change is K times the noise floor", never "there is a change".
   - Same discipline as `geometry_score.py`: one formula for all three methods, computed after
     generation, with the scale probe (identical = 1.00, 1 % nudge = 0.81, 4 % nudge = 0.56)
     recomputed per row so the numbers stay readable. The photo-scale calibration is reproducible
     with the same code — re-run while writing this file on `source/photos/web/DJI_0021.jpg`
     (2048x1152), which gives exactly the numbers the docs quote:
     ```
     import sys, tempfile, pathlib; sys.path.insert(0, "scripts")
     import geometry_score as g, numpy as np; from PIL import Image
     p = "source/photos/web/DJI_0021.jpg"; a = np.asarray(Image.open(p).convert("RGB"))
     tmp = pathlib.Path(tempfile.mkdtemp())
     for pct in (1, 2, 4):
         off = int(round(a.shape[1] * pct / 100))
         q = tmp / f"nudge{pct}.png"; Image.fromarray(np.roll(a, off, axis=1)).save(q)
         s = g.score(pathlib.Path(p), q)
         print(pct, s["pearson_r"], s["bad_frac_gt_0.15"])   # 1% 0.8093 0.1521
     print(g.score(pathlib.Path(p), pathlib.Path(p))["pearson_r"])   # identical 1.0
     ```
     So the photo-scale floor of "something changed" is 0.1521 at a 1 % nudge — that is the scale
     `appearance_score.py` works on, since it compares photos, not depth maps. The depth-map floors
     (1.6 % / 3.1 % / 6.0 %) stay computed per row inside `geometry_score.py`; the two scales must
     never be read against each other.
2. **One facade region for all three methods** — decided by the user, two options:
   - *hand-drawn polygon saved as a mask PNG* (recommended; the region is then a project input
     like any other, and its provenance is stated). The photo area to avoid: sky, lawn,
     neighbouring houses, road.
   - *reuse the layout boxes already inside the MOSS graph* — no work needed, but they are
     rectangles and will include sky and neighbours, and that has to be written in the row's
     limitations.
   Until this exists, the appearance column stays out of the table, and no text may claim that
   materials were measured.
3. Optional, kills two problems at once: **make the Qwen mask an artifact of the repo**. Verified
   in the node code (`ausboss-nodes/nodes/node_mask_by_touch.py`): the node does return a real
   `MASK` output (`RETURN_TYPES = ("MASK", "IMAGE", "STRING")`), and what it writes by itself goes
   to ComfyUI's temp folder only as a picture for its own face ("the mask is returned either
   way") — there is no "save mask" button. What does **not** survive saving the graph is the
   picked points: they live in the browser's node state, so the headless replay fails with
   "the picks were made on another picture". The concrete fix is therefore: add a SaveImage of the
   node's `mask` output to the UI graph, run it once in the UI, and build the headless graph on a
   mask loader instead of the touch node. That removes the `headless: blocked` entry in
   `workflows/manifest.json` *and* gives a declared region — although it is the region of the
   touched part, not of the whole facade, so A.2 is still needed for a region shared by all three
   methods.

## B. Then — make the cost columns a comparison instead of a set of facts (needs ComfyUI running)

The existing rows are not comparable: they started from different states (10980 / 4531 / 1389 /
841 / 165 MiB free), one is cold (61.5 s) and one warm (4.2 s), and one "86.8 s" record was a run
that failed in 2.37 s while the rest of the time was queue waiting. To turn this into a ranking:

- start ComfyUI (the scripts never start it) — `python scripts/run_workflow.py <id> --cold`, so
  each run begins from a defined state (the script asks the server to unload models first);
- **3 seeds per method** with the *same* stated material prompt, nothing else using the card;
  Krea2's seed does not pin the output, so its variance is part of the result, not an error;
- the Qwen rows can only be produced from the UI (or after A.3), which is itself a finding: two
  of three methods can be replayed by a script, one cannot;
- about the canvas, now checked in the node code rather than guessed: MOSS is **already** at
  1024x576, the same as Krea2, so the only real difference left is the Qwen graph's 1049x590 crop
  chosen around the touched mask — and no size widget controls that. Why the MOSS widgets say
  1024x1024 while the render is 1024x576: with `resolution_source` Off ("from the image/mask") and
  an image linked into `AspectRatioSimplifier`, the node takes the **image's** aspect ratio and
  scales it so the longer side is `max_resolution` (1024); `custom_width`/`custom_height` are then
  ignored (`ComfyUI_LC123_nodes/aspect_ratio.py`, tooltip at the `resolution_source` widget and the
  `if has_source and not resolution_source:` branch in `run()`). So setting the size deliberately
  means turning `resolution_source` on first — not editing `custom_height`, which is what an earlier
  note here claimed. Left as it is, the sizes still match; only the intent is implicit, and
  `conditions.canvas_note` states the real sizes per row.

## C. Last — the portfolio text (README, gallery captions, the closing comparison)

Not before A and B: half of the sentences would be about numbers that do not exist yet. The
constraint from the last `PROGRESS.md` entry (`Problems / next step` section, 2026-11-03 23:00)
stands: no "materials measured" claim until `scripts/appearance_score.py` exists — that entry is
also where the idea of the appearance delta inside a stated facade region first appears.

## Commands that reproduce the current state

```
python scripts/import_api_from_history.py   # API graphs from what really ran (needs server)
python scripts/run_workflow.py krea2_edit --cold   # one measured headless run + record
python scripts/collect_metrics.py --pairs 3 # rewrites docs/metrics.md, writes measurements.json
python scripts/make_index.py                # rewrites workflows/index.md
python scripts/contact_sheet.py             # gallery PNGs
```

`workflows/_api/*.api.json` are generated — change the UI-format JSON above them, then re-import;
never hand-edit them.

## Checked against the code while writing this (so it is not remembered wrong)

- `AspectRatioSimplifier` with `resolution_source` Off and a linked image ignores
  `custom_width/custom_height` and fits the image's own aspect to `max_resolution` — that is why
  the MOSS render is 1024x576 although its widgets say 1024x1024 (`aspect_ratio.py`).
- `MaskByTouch` returns a real `MASK` output; there is no "save mask" control, and its own picture
  files go to the temp folder ("the mask is returned either way"). The unpreserved part is the
  picked points, which are browser state.
- The photo-scale calibration in `docs/metrics.md` and in `geometry_score.py`'s docstring
  reproduces from `geometry_score.score` + `np.roll` (numbers above).
- `PROGRESS.md` has no numbered sections — the reference to "§5" that appeared in an earlier chat
  meant the `Problems / next step` part of its newest entry.
- The global appearance differences quoted in chat (0.124 / 0.125 / 0.054) are not stored
  anywhere in the repo; only the Krea2 repeat-run figure 0.0139 is.

