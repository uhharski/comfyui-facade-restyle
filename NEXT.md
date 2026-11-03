# Next tasks (open when the session ends — resume from here)

Status at writing time: `docs/metrics.md` has 9 scored rows (3 methods × 3 depth pairs), every row
flagged where the evidence is weak; every cost number is tied to a run record and states how that
tie was made. Nothing here is a bug list — these are decisions and the work that depends on them.

Restore state of the project itself: read `PROJECT.md` and the newest entry of `PROGRESS.md`
first (`PROGRESS.md` is the user's file — do not edit it unless asked).

---

## A. Do first — the metric's blind spot (needs no GPU, no ComfyUI: pure CPU on files that exist)

The geometry score measures one thing: whether the structure of the scene survived. It is
**blind to the material swap**, because the depth map of a flat wall does not change when its
finish changes. Today the only appearance number in the project is a global RGB difference
(Krea2 0.124 / MOSS 0.125 / Qwen 0.054 mean abs. difference), which includes sky, grass and the
neighbouring houses — so it cannot go into the table.

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
     recomputed per row so the numbers stay readable.
2. **One facade region for all three methods** — decided by the user, two options:
   - *hand-drawn polygon saved as a mask PNG* (recommended; the region is then a project input
     like any other, and its provenance is stated). The photo area to avoid: sky, lawn,
     neighbouring houses, road.
   - *reuse the layout boxes already inside the MOSS graph* — no work needed, but they are
     rectangles and will include sky and neighbours, and that has to be written in the row's
     limitations.
   Until this exists, the appearance column stays out of the table, and no text may claim that
   materials were measured.
3. Optional, kills two problems at once: **export the Qwen mask to a file** (`MaskByTouch` offers
   saving its picks). That removes the `headless: blocked` entry in `workflows/manifest.json`
   (the graph currently fails headless with "the picks were made on another picture") *and* gives
   a declared region for that method.

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
- optional one-line change, user's call, still not done: set the MOSS graph's
  `AspectRatioSimplifier` custom height to 576 so all three generate at the same canvas. Left
  alone, `conditions.canvas_note` states the difference instead — that is acceptable, it is not
  silent either way.

## C. Last — the portfolio text (README, gallery captions, the closing comparison)

Not before A and B: half of the sentences would be about numbers that do not exist yet. What the
project can already claim honestly today, and what must wait for A/B, is listed in the newest
`PROGRESS.md` entry §5 — in particular: no "materials measured" claim until
`scripts/appearance_score.py` exists.

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
