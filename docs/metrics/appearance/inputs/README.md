# Inputs of the control rows that were not repo files

Each record in `docs/metrics/appearance/` names the two images it measured by absolute path. Most of
those paths are inside this repo or inside this machine's ComfyUI folder, but one control was computed
against a file that was sitting in `C:\Users\vikto\AppData\Local\Temp\` at measurement time. The exact
bytes are kept here so the record can still be re-checked.

| file | record | where it came from |
|---|---|---|
| `other_house.jpg` | `control_other_house.json` (its `result` field) | the same frame as `../../../source/photos/web/DJI_0001.jpg` — another house of the same flight — re-encoded into a Temp working copy at 2048×1152. Not byte-identical to the repo copy (a decoded-pixel difference of up to 16/255, so the re-encode is real), which is why the measured file is stored here instead of pointing at the repo copy. Content correlation with the repo copy at 256×144: 1.000 |

Why this control exists at all: it is the one that **has to fire**. If a different house, framed at the
same place in the same region, did not move the numbers, then the region measures nothing and every other
row in that folder is meaningless. What it actually reported: colour EMD 0.066, detail ratio 0.533, and
layout correlation **−0.108** (see `docs/metrics.md` § 2).
