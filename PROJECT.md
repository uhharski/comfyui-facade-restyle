# A House Without an Interior Design Project: Controlled Generation of Finishes from a Floor Plan

> Working title (rename before publishing on GitHub:
> `house-from-floorplan` / `krea2-architecture-pipeline`)

## 1. Why

Two goals solved by one project:

1. **Personal:** we are building a house. All I have is a floor plan (PDF); there is no
   design project. I want to see the house in different façade/interior finishes, lighting
   and surroundings before spending money on materials.
2. **Career:** a portfolio project for the position *Junior AI Engineer (image and video
   generation)*, Luminary Ventures OÜ / MyArchitectAI
   (hard application deadline 21.11.2026, but I apply early: **target 07–10.11**, done by 05.11).

Their product does exactly this: upload your project → get a photorealistic render that
preserves geometry → swap materials/light → turn images into video. This project is the
live version of the same problem.

## 2. One-sentence idea

A pipeline "floor plan → white-box 3D model → controlled generation of photorealistic
house variants", with an honest comparison of two approaches and measurements.

## 3. Pipeline

```
floor plan (PDF)
  → PNG page of the plan (scale calibrated against a known wall)
  → white-box 3D model: UE5 scene (already built, § 5.1); Sweet Home 3D as fallback
  → screenshots of the white model (façade from 3–4 angles, one view per room)
    — straight from UE5, incl. exact depth/lineart render passes
  → control signals: Depth Anything / lineart / canny (comfyui_controlnet_aux)
  → Krea 2 + Krea2 Control LoRA (ComfyUI, fp8)            ← approach A
  → Krea2 edit / style reference directly on the 2D plan  ← approach B (expected to fail,
     report honestly: perspective and dimensions break down)
  → comparison table + before/after gallery + conclusions
```

Optional extensions:
- façade material variants: plaster / brick / wood; season and time of day;
- video: façade fly-around or day-to-night transition (SVD / Wan / AnimateDiff);
- a LoRA trained by me on one specific material (closes the "your own LoRAs" requirement).

## 4. Job requirements → where they are covered

| Requirement / "nice to have"                          | Where in this project               |
|--------------------------------------------------------|-------------------------------------|
| Public work: code, LoRAs, ComfyUI workflows           | repo with workflow JSON + scripts   |
| Comparisons / benchmarks with conclusions              | approach A vs B table, metrics      |
| Running on modest hardware (quantization, VRAM, speed) | fp8/GGUF, VRAM and runtime measures |
| Two+ solutions to one problem, honest before/after     | A/B plus the negative result of B   |
| Your own LoRA                                          | train a façade-material LoRA (phase 2) |
| Mini-report "built → failed → how I knew it improved"  | the README follows exactly this arc |
| Activity trace over 6+ months                          | commit early and often, before the deadline |

## 5. Stack (already installed)

- ComfyUI: `J:/AI/ComfyUI-Easy-Install/ComfyUI`
- Models: Krea 2 fp8 (`models/diffusion_models/Krea 2/`), Flux-2-klein Q8_0 GGUF
- Nodes: `comfyui-krea2-controlnet` (Control LoRA: depth/canny/lineart/normal),
  `comfyui-krea2edit`, `ComfyUI-Krea2-Ostris-Edit`, `krea2-style-refrence`,
  `krea2-nag`, `ComfyUI-Krea2T-Enhancer`, blueprints "Krea-2 Turbo"
- 3D: **Unreal Engine 5 (existing project, see § 5.1)**, with Sweet Home 3D / Planner5D as a fallback

### 5.2 Target hardware (measured 25.10)

```
GPU : NVIDIA GeForce RTX 5070, 12 GB VRAM (12227 MiB), driver 616.64
CPU : AMD Ryzen 7 5700X 8-core
RAM : 64 GB
```

Consequences for the measurements section (§ 4 "modest hardware"):
- 12 GB VRAM is exactly the "modest hardware" claim we want to demonstrate: fp8 UNet
  (13 GB checkpoints) will not fit fully resident → expect CPU offload and ComfyUI's
  lowvram path; this is worth measuring and reporting honestly, not hiding.
- Plan: keep control/VAE stages in fp8 or bf16, generate at 1024–1280 px first, record
  peak VRAM + seconds/iteration per approach (A vs B). Record numbers in `docs/metrics.md`.

### 5.3 Krea2 Control LoRA weights (installed 25.10)

The `comfyui-krea2-controlnet` node was installed but its Control LoRA weights were missing
(no depth/canny/lineart files anywhere under `models/loras`) — this was the hard blocker for
Workflow A. Installed the public depth Control LoRA:
- source: `Patil/Krea-2-depth-controlnet` (HF), file `depth-control-lora.safetensors`, 862 MB
- installed as: `models/loras/Krea2/krea2_depth_control_lora.safetensors`
- **License: Krea 2 Community License** (not MIT) — must be stated in the repo before the
  model/outputs are published publicly.
- Node defaults for the depth LoRA (from the node README): `channel_mode=grayscale`,
  `normalize=per_image_minmax`, `invert=false` (invert only if near objects come out dark).
- Only a depth LoRA exists publicly; canny/lineart/normal variants would need the matching
  preprocessor image and may not be available — plan A uses depth as the primary control.

Note: `models/diffusion_models/Krea 2/` contains community fp8/INT8 mixes (no official
Krea-2-Raw). The depth LoRA is trained on Krea-2-Raw, so the first smoke test must verify it
actually patches (the node raises an error if no compatible block weights are found) — try the
turbo/plain fp8 mix first, and treat "LoRA silently does nothing" as a failure mode to report.

### 5.1 Existing UE5 source (my own work)

Location: `C:/Users/vikto/Desktop/Dom/3d/v2.0` — copy versioned in this repo at
`source/3d-datasmith/`

There are **two** exports in that folder: `house.udatasmith` (04.03, older, v1) and
`v2.0/v2_0.udatasmith` (05.03, newer). `v2.0` is the one used and copied into the repo.

Format check (25.10): this is **not a .uproject** but a **Datasmith export from ArchiCAD 29**
(`v2_0.udatasmith` + `v2_0_Assets/` with .udsmesh and .tiff textures, ~41 MB).
Pipeline: ArchiCAD (BIM source of the design and of the PDF floor plan) → Datasmith →
import into UE5 (Datasmith plugin) or view via free Epic Datasmith Converter.
The house model in § 5.1 below therefore comes from this ArchiCAD Datasmith scene.

I have already built a visualization of the house in **Unreal Engine 5** and made a
**virtual-reality** version of it. The interiors are bare walls with no furniture — which
is intentional and actually ideal: bare geometry is the perfect white-model input, and
furnishing is exactly what the generative step adds (prompt-driven, many variants at once;
optionally constrained with furniture blocker boxes in UE5 or inpaint masks).

The UE5 project (source assets, layout, camera set-ups)
is a project asset and a differentiator:

- The white-box geometry already exists: no need to re-trace the floor plan in another
  tool. White-model screenshots (façade + interiors) are rendered directly from UE5 with
  unlit/basic-material view modes, so control signals (depth, lineart) are exact.
- UE5 can output ground-truth depth render targets and clean lineart — better control maps
  than extracting them from photos.
- VR/stereo walkthroughs and turntable sequences from UE5 are ready inputs for image-to-video
  experiments (SVD / Wan / AnimateDiff) and for the HF Space demo.
- The UE5 work itself is publishable evidence (screenshots, short video, short write-up) of
  building real things end-to-end — directly relevant to the job's product domain
  (architectural visualization).

## 6. Work plan

### Reverse schedule (today 25.10 → finished by 05.11 → apply 07–10.11)

| Days        | Milestone                                                          |
|-------------|---------------------------------------------------------------------|
| 25–27.10    | repo created, UE5 project located, white-model view modes set up     |
| 28–30.10    | export renders from UE5 (façade ×3–4, interiors) + depth/lineart    |
| 31.10–01.11 | Workflow A end-to-end: depth → Krea2 Control → material variants     |
| 02–03.11    | Workflow B run and documented as failure; variant C if attempted     |
| 03–04.11    | evaluation sheet, VRAM/time metrics, before/after gallery            |
| 04–05.11    | README (built → broke → measured), repo cleanup                      |
| 06.11       | buffer day                                                         |
| 07–08.11    | **application sent** (CV + links, English)                           |
| 09–21.11    | while waiting: own-LoRA experiment, video/VR clip, HF Space          |

### Tasks

- [ ] 0. Export plan pages from the PDF, calibrate the scale
- [ ] 1. Locate/organize the UE5 project; set up white-model view modes (unlit, lineart, depth)
- [ ] 2. Render passes from UE5: façade ×3–4, one interior per room + depth/lineart passes;
      export a VR/turntable clip for later video experiments
- [ ] 3. Workflow A: white model → depth → Krea2 Control → material variants
      (prerequisite done 25.10: depth Control LoRA weights installed, § 5.3)
- [ ] 4. Workflow B (for comparison): 2D plan straight into edit/style-ref — record the failure
- [ ] 5. Evaluation sheet: geometry intact? materials recognizable? artifacts? VRAM/time
      (optional variant C: UE5 furniture blockers + inpaint masks → furniture at real
      dimensions; second solution to "generator invents wrong-sized furniture")
- [ ] 6. README in the "what I built → what broke → how I measured fixes" format
- [ ] 7. Public GitHub repo + (optional) Hugging Face Space with a Gradio demo
- [ ] 8. (optional) my own LoRA on a façade material; video fly-around of the house
      (UE5 turntable / VR capture as the base clip)
- [ ] 8b. (optional) publish the UE5 visualization as a separate portfolio item
      (screenshots + short video + 3–5-sentence write-up, incl. the VR part)
- [ ] 9. Application: genia@myarchitectai.com — portfolio links + short CV (in English),
      **target 07–08.11.2026** (hard deadline 21.11), including two sentences on "what I
      built last and what went wrong"

## 7. What already exists / has been tried

- Local Krea 2 weights (fp8), control/edit nodes — ready
- First experiments `krea2_edit_*` / `krea2_candidate_*` in ComfyUI — exist, usable
  as "before" material
- Floor plan — PDF, not yet lifted into 3D
- **House model exists as a Datasmith export from ArchiCAD 29** (`C:/Users/vikto/Desktop/Dom/3d/v2.0`,
  184 static meshes, ~41 MB) — imports into UE5; VR visualization was based on it

## 8. Open questions

- Is the PDF vector or a scan? — likely vector (exported from ArchiCAD 29, see § 5.1);
  verify by trying to select text/lines in it. (Less critical now: Datasmith scene exists.)
- ~~Hardware (VRAM)~~ — resolved: RTX 5070 12 GB, Ryzen 7 5700X, 64 GB RAM, see § 5.2
- Repository name and GitHub/HF account
- Where the UE5 project lives and whether it can be published — resolved in part: the repo
  copy of the Datasmith export is anonymized (address/names/paths removed, see
  `source/3d-datasmith/README.md`); still verify the house design itself is OK to publish.
- Real floor heights and roof type details for the white model

## 9. How to restore project state (close pi and come back later)

Three layers, in order of importance:

1. **These files** (`PROJECT.md` + `PROGRESS.md`) are the long-term memory. To resume in a
   brand-new session, first message: "read PROJECT.md and PROGRESS.md, continue from step N of
   the work plan". Enough for any model to pick up the work.
   If `NEXT.md` exists in this folder, read it too: it is the open task list as it stood when the
   last session ended (what to do first, which decisions are still the user's, and the commands
   that reproduce the current tables).
2. **Git history** in this folder — versions, diffs, and the "activity trace" the job
   requirements ask for. Commit after every meaningful step (see § 6 schedule).
3. **The pi session itself** — saved automatically per folder:
   - `pi --continue` — reopen the latest session in this folder;
   - `pi --resume` or `/resume` — pick among past sessions (name this one first with `/name house-ai-project`);
   - `/compact` when context grows; `/export` for an archive.

Rule of thumb: never trust chat memory — write decisions and progress into `PROGRESS.md`
before ending a work session.
