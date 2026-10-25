# Progress log

Newest entry on top. One entry per work session: what was done, decisions + why,
problems found, next step. This file + `PROJECT.md` are the complete restore state —
a new agent session only needs to read both.

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
