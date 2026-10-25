# Progress log

Newest entry on top. One entry per work session: what was done, decisions + why,
problems found, next step. This file + `PROJECT.md` are the complete restore state —
a new agent session only needs to read both.

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
