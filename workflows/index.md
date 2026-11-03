# Workflow index (generated)

`python scripts/make_index.py` writes this file — do not edit it by hand.
It is the readable printout of what each graph contains right now: models, sizes,
seeds, samplers, and the run times the graph itself recorded.

A value that is overridden by an incoming link is listed under “parameters that do
not come from widgets” — an old number left in a widget of a saved workflow does
not mean the graph uses it. The canvas that was really generated is recorded per
run in `docs/metrics.md`, read from the saved result image.

Common measurement input: `DJI_0021.JPG`; GPU `RTX 5070 12 GB`. the agent backend CAN run a model on this same card, but whether one was resident during a given run is not assumed either way: every run record stores the free VRAM reported by /system_stats immediately before that run, and `run_workflow.py --cold` can clear the card first to make the starting state defined. Measured on 04.11 the five headless runs began with 10980, 4531, 1389, 841 and 165 MiB free — the largest peak (10742 MiB) happened when the card was empty, so an earlier blanket claim that a chat model was sitting on the GPU during these rows is not true of them and was removed.

## `krea2_edit.json`  (id `krea2_edit`)

- method: image-edit conditioning only (no control signal): the photo is the input, the task is stated in words
- control signal: none
- what we expect to see: tends to drift: geometry comes only from the latent + prompt
- measurement outputs: `krea2_edit_depth_in-*.png`, `krea2_edit_depth_out-*.png`, plus the result image itself
- headless replay: possible with `python scripts/run_workflow.py krea2_edit`
- repeating the same graph gives: NOT reproducible with a fixed seed: the same API graph and the same seed 20261103 produced krea2_edit_00111.png and krea2_edit_00114.png, and those two files differ (mean absolute difference 0.0139, 1.5 % of pixels differ by more than 0.1). That difference is this method's noise floor: any claim about changing the material has to be larger than it. Two explanations are possible and not separated here - a seed that a Krea2 Edit conditioning node does not honour the way a KSampler does, or non-deterministic GPU kernels; checking which would need the same graph with a different seed and a fixed algorithm, which is not measured yet

**Models and weights in this graph**

| field | value | where |
|---|---|---|
| text encoder | `QWEN\qwen3vl_4b_fp8_scaled.safetensors` | node 56 `CLIPLoader` |
| vae | `qwen_image_vae.safetensors` | node 57 `VAELoader` |
| lora | `Krea2\krea2_identity_edit_v1_2.safetensors` | node 71 `LoraLoaderModelOnly` |
| diffusion model | `Krea 2\kreavantisMASTERFP8_v10.safetensors` | node 55 `UNETLoader` |
| checkpoint | `depth_anything_v2_vits.pth` | node 90 `DepthAnythingV2Preprocessor` “Depth of SOURCE (krea2_edit)” |
| checkpoint | `depth_anything_v2_vits.pth` | node 91 `DepthAnythingV2Preprocessor` “Depth of RESULT (krea2_edit)” |

**Run settings**

| field | value | where |
|---|---|---|
| width | `1024` | node 82 `EmptySD3LatentImage` |
| height | `1024` | node 82 `EmptySD3LatentImage` |
| seed | `20261103` | node 53 `KSampler` |
| steps | `10` | node 53 `KSampler` |
| cfg | `1` | node 53 `KSampler` |
| sampler | `euler_ancestral` | node 53 `KSampler` |
| scheduler | `normal` | node 53 `KSampler` |
| denoise | `1` | node 53 `KSampler` |
| lora strength | `1` | node 71 `LoraLoaderModelOnly` |
| width | `1024` | node 87 `ImageResizeKJv2` |
| height | `576` | node 87 `ImageResizeKJv2` |
| resample | `nearest-exact` | node 87 `ImageResizeKJv2` |
| keep proportion | `resize` | node 87 `ImageResizeKJv2` |
| width | `1024` | node 86 `ImageResizeKJv2` |
| height | `576` | node 86 `ImageResizeKJv2` |
| resample | `nearest-exact` | node 86 `ImageResizeKJv2` |
| keep proportion | `resize` | node 86 `ImageResizeKJv2` |
| depth resolution | `1024` | node 90 `DepthAnythingV2Preprocessor` “Depth of SOURCE (krea2_edit)” |
| depth resolution | `1024` | node 91 `DepthAnythingV2Preprocessor` “Depth of RESULT (krea2_edit)” |

**Inputs and output prefixes**

| field | value | where |
|---|---|---|
| input image | `DJI_0021.JPG` | node 72 `LoadImage` |
| input image | `DJI_0021.JPG` | node 89 `LoadImage` |
| output prefix | `krea2_edit` | node 29 `SaveImage` |
| output prefix | `krea2_edit_depth_in` | node 92 `SaveImage` “Save depth IN (krea2_edit)” |
| output prefix | `krea2_edit_depth_out` | node 93 `SaveImage` “Save depth OUT (krea2_edit)” |

**Parameters that do not come from widgets**

- node 79 `Krea2EditModelPatch`: comes from links, the value shown above is the stale widget value: model, source_latent, source_latent_b
- node 82 `EmptySD3LatentImage`: comes from links, the value shown above is the stale widget value: height, width
- node 53 `KSampler`: comes from links, the value shown above is the stale widget value: latent_image, model, negative, positive
- node 85 `Krea2EditGroundedEncode`: comes from links, the value shown above is the stale widget value: clip, input image, image_b
- node 71 `LoraLoaderModelOnly`: comes from links, the value shown above is the stale widget value: model
- node 87 `ImageResizeKJv2`: comes from links, the value shown above is the stale widget value: input image
- node 29 `SaveImage`: comes from links, the value shown above is the stale widget value: images
- node 84 `Krea2EditGroundedEncode`: comes from links, the value shown above is the stale widget value: clip, input image, image_b
- node 86 `ImageResizeKJv2`: comes from links, the value shown above is the stale widget value: input image
- node 90 `DepthAnythingV2Preprocessor` “Depth of SOURCE (krea2_edit)”: comes from links, the value shown above is the stale widget value: input image
- node 91 `DepthAnythingV2Preprocessor` “Depth of RESULT (krea2_edit)”: comes from links, the value shown above is the stale widget value: input image
- node 92 `SaveImage` “Save depth IN (krea2_edit)”: comes from links, the value shown above is the stale widget value: images
- node 93 `SaveImage` “Save depth OUT (krea2_edit)”: comes from links, the value shown above is the stale widget value: images

_(node 95 `LCTimer` has recorded no run yet — the times appear in the graph after the first run in the UI)_

**Verdict / status**

_(заполняется после прогона / to fill after the run)_
---

## `moss_inpaint.json`  (id `moss_inpaint`)

- method: color+depth control (MOSS) + layout boxes
- control signal: depth (Depth Anything V2) + colour reference + bounding boxes
- what we expect to see: expected to hold geometry: depth is an explicit control signal
- measurement outputs: `moss_inpaint_depth_in-*.png`, `moss_inpaint_depth_out-*.png`, plus the result image itself
- headless replay: possible with `python scripts/run_workflow.py moss_inpaint`
- repeating the same graph gives: reproducible while the graph is frozen: two headless replays of workflows/_api/moss_inpaint.api.json wrote bit-identical results (MOSS Box Edit/Test_2026-11-04_00001_.png == Test_2026-11-04_00005_.png). This says nothing about pressing Run in the UI: the LCSeed node in that graph generates a fresh seed for every queued run unless it is switched to a fixed mode, which is why the nine UI runs on 03.11/04.11 differ

**Models and weights in this graph**

| field | value | where |
|---|---|---|
| model_file | `moss_image_sft_bf16.safetensors` | node 23 `LCOptimizer` |
| text_encoder | `qwen3.5_9b_int8_convrot.safetensors` | node 23 `LCOptimizer` |
| vae | `flux2-vae_small.safetensors` | node 23 `LCOptimizer` |
| control_file | `MOSS\moss-color-depth-control.safetensors` | node 115 `LCMOSSControl` |
| checkpoint | `depth_anything_v2_vits.pth` | node 122 `DepthAnythingV2Preprocessor` “Depth of SOURCE (moss_inpaint)” |
| checkpoint | `depth_anything_v2_vits.pth` | node 123 `DepthAnythingV2Preprocessor` “Depth of RESULT (moss_inpaint)” |

**Run settings**

| field | value | where |
|---|---|---|
| steps | `25` | node 26 `LCSamplerConfigureSimple` |
| detailer steps | `25` | node 26 `LCSamplerConfigureSimple` |
| denoise | `1` | node 26 `LCSamplerConfigureSimple` |
| cfg | `2.5` | node 26 `LCSamplerConfigureSimple` |
| sampler | `er_sde` | node 26 `LCSamplerConfigureSimple` |
| scheduler | `simple` | node 26 `LCSamplerConfigureSimple` |
| base seed | `20261103` | node 28 `LCSeed` |
| max_resolution | `1024` | node 30 `AspectRatioSimplifier` |
| size source | `False` | node 30 `AspectRatioSimplifier` |
| aspect preset | `custom` | node 30 `AspectRatioSimplifier` |
| custom width | `1024` | node 30 `AspectRatioSimplifier` |
| custom height | `1024` | node 30 `AspectRatioSimplifier` |
| swap dimensions | `Off` | node 30 `AspectRatioSimplifier` |
| resample | `lanczos` | node 30 `AspectRatioSimplifier` |
| proportion | `crop` | node 30 `AspectRatioSimplifier` |
| crop position | `center` | node 30 `AspectRatioSimplifier` |
| sigma shift | `4` | node 63 `ModelSamplingAuraFlow` |
| width | `0` | node 86 `LCMOSSLayoutPrompt` |
| height | `0` | node 86 `LCMOSSLayoutPrompt` |
| width | `1024` | node 105 `LCBoundingBoxes` |
| height | `1024` | node 105 `LCBoundingBoxes` |
| seed | `7584161123816341` | node 113 `LCMOSSBoxEdit` |
| steps | `25` | node 113 `LCMOSSBoxEdit` |
| cfg | `2.5` | node 113 `LCMOSSBoxEdit` |
| sampler | `er_sde` | node 113 `LCMOSSBoxEdit` |
| scheduler | `simple` | node 113 `LCMOSSBoxEdit` |
| mask grow | `16` | node 113 `LCMOSSBoxEdit` |
| mask feather | `64` | node 113 `LCMOSSBoxEdit` |
| keep | `0` | node 113 `LCMOSSBoxEdit` |
| depth resolution | `518` | node 114 `LCDepthAnythingV2` |
| strength | `1` | node 115 `LCMOSSControl` |
| value | `True` | node 120 `PrimitiveBoolean` “Use 🥅 Controlnet” |
| depth resolution | `1024` | node 122 `DepthAnythingV2Preprocessor` “Depth of SOURCE (moss_inpaint)” |
| depth resolution | `1024` | node 123 `DepthAnythingV2Preprocessor` “Depth of RESULT (moss_inpaint)” |

**Inputs and output prefixes**

| field | value | where |
|---|---|---|
| input image | `DJI_0021.JPG` | node 29 `LoadImage` |
| output prefix | `ComfyUI` | node 77 `SaveImage` |
| output prefix | `ComfyUI` | node 112 `SaveImage` |
| output prefix | `moss_inpaint_depth_in` | node 124 `SaveImage` “Save depth IN (moss_inpaint)” |
| output prefix | `moss_inpaint_depth_out` | node 125 `SaveImage` “Save depth OUT (moss_inpaint)” |

**Parameters that do not come from widgets**

- node 25 `SetNode` “Set_Pipe”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 30 `AspectRatioSimplifier`: comes from links, the value shown above is the stale widget value: input image
- node 31 `SetNode` “Set_Org Pic”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 33 `LCImageLabel`: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 63 `ModelSamplingAuraFlow`: comes from links, the value shown above is the stale widget value: model
- node 77 `SaveImage`: comes from links, the value shown above is the stale widget value: output prefix, images
- node 79 `GetNode` “Get_Pipe”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 86 `LCMOSSLayoutPrompt`: comes from links, the value shown above is the stale widget value: elements, prompt
- node 87 `LCShowText`: comes from links, the value shown above is the stale widget value: text
- node 92 `SetNode` “Set_Layout image”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 97 `LCNote` “MOSS Box Edit 🖌️”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 98 `GetNode` “Get_Layout image”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 99 `GetNode` “Get_Org Pic”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 102 `LCNotify`: comes from links, the value shown above is the stale widget value: any
- node 104 `LCNote` “BBOX Notes:”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 105 `LCBoundingBoxes`: comes from links, the value shown above is the stale widget value: input image
- node 107 `LCDynamicOverlay`: comes from links, the value shown above is the stale widget value: image_a, image_b
- node 109 `SetNode` “Set_BBOX Image”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 110 `LCImageStitchMulti`: comes from links, the value shown above is the stale widget value: image_01, image_02
- node 111 `GetNode` “Get_BBOX Image”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 112 `SaveImage`: comes from links, the value shown above is the stale widget value: output prefix, images
- node 113 `LCMOSSBoxEdit`: comes from links, the value shown above is the stale widget value: cfg, clip, elements, input image, model, negative, prompt, sampler, scheduler, seed, steps, vae
- node 114 `LCDepthAnythingV2`: comes from links, the value shown above is the stale widget value: input image
- node 115 `LCMOSSControl`: comes from links, the value shown above is the stale widget value: depth_map, model, vae
- node 119 `LC Bypasser`: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 121 `LCNote` “Base Prompt 📝”: parameter names unavailable (ComfyUI not reachable, no .object_info.json cache) — values are positional
- node 122 `DepthAnythingV2Preprocessor` “Depth of SOURCE (moss_inpaint)”: comes from links, the value shown above is the stale widget value: input image
- node 123 `DepthAnythingV2Preprocessor` “Depth of RESULT (moss_inpaint)”: comes from links, the value shown above is the stale widget value: input image
- node 124 `SaveImage` “Save depth IN (moss_inpaint)”: comes from links, the value shown above is the stale widget value: images
- node 125 `SaveImage` “Save depth OUT (moss_inpaint)”: comes from links, the value shown above is the stale widget value: images

_(node 127 `LCTimer` has recorded no run yet — the times appear in the graph after the first run in the UI)_

**Verdict / status**

_(заполняется после прогона / to fill after the run)_
---

## `qwenImage_inpaint.json`  (id `qwen_inpaint`)

- method: local inpaint by touched mask, result stitched back into the original pixels
- control signal: manual mask
- what we expect to see: geometry is preserved by construction outside the mask; only the masked region changes
- measurement outputs: `qwen_inpaint_depth_in-*.png`, `qwen_inpaint_depth_out-*.png`, plus the result image itself
- headless replay: **blocked** — the MaskByTouch node stores its touched points as UI state, not in the exported graph, so a headless replay of its API graph fails with 'RuntimeError: Mask by Touch: the picks were made on another picture' (measured 04.11 00:39, prompt 590dee99; the run reported status error, executed in 2.37 s and wrote no file). Its rows are produced by UI runs only. To make it measurable like the others: save the mask as a file (the node offers that) and replace the touch node with a mask loader

**Models and weights in this graph**

| field | value | where |
|---|---|---|
| text encoder | `QWEN\qwen3vl_8b_fp8_scaled.safetensors` | node 8 `CLIPLoader` “Text encoder” |
| vae | `qwen_image_2.1_vae_bf16.safetensors` | node 9 `VAELoader` “VAE” |
| diffusion model | `QWEN\qwenImage21_bf16.safetensors` | node 10 `UNETLoader` “Diffusion model” |
| checkpoint | `sam3.1_multiplex_fp16.safetensors` | node 11 `CheckpointLoaderSimple` “SAM 3 model” |
| checkpoint | `depth_anything_v2_vits.pth` | node 41 `DepthAnythingV2Preprocessor` “Depth of SOURCE (qwen_inpaint)” |
| checkpoint | `depth_anything_v2_vits.pth` | node 42 `DepthAnythingV2Preprocessor` “Depth of RESULT (qwen_inpaint)” |

**Run settings**

| field | value | where |
|---|---|---|
| mask feather | `24` | node 2 `AUSBOSS_NODES_ImageCropRotatePad` “Image Crop + Rotate + Pad - Your picture” |
| resize to megapixels | `True` | node 2 `AUSBOSS_NODES_ImageCropRotatePad` “Image Crop + Rotate + Pad - Your picture” |
| megapixels | `0.59` | node 2 `AUSBOSS_NODES_ImageCropRotatePad` “Image Crop + Rotate + Pad - Your picture” |
| mask grow | `16` | node 3 `AUSBOSS_NODES_MaskByTouch` “Mask by Touch - Click what to change” |
| seed | `20261103` | node 5 `AUSBOSS_NODES_Seed` “Seed” |
| value | `25` | node 6 `AUSBOSS_NODES_Integer` “Integer - Steps” |
| depth resolution | `1024` | node 41 `DepthAnythingV2Preprocessor` “Depth of SOURCE (qwen_inpaint)” |
| depth resolution | `1024` | node 42 `DepthAnythingV2Preprocessor` “Depth of RESULT (qwen_inpaint)” |
| depth resolution | `0` | node 20 `TextEncodeQwenImage21` “Text Encode Qwen Image 2.1 - The crop and your request” (subgraph: Paint it with Qwen) |
| seed | `0` | node 26 `KSampler` “Sampler - CFG 1, euler” (subgraph: Paint it with Qwen) |
| steps | `25` | node 26 `KSampler` “Sampler - CFG 1, euler” (subgraph: Paint it with Qwen) |
| cfg | `1` | node 26 `KSampler` “Sampler - CFG 1, euler” (subgraph: Paint it with Qwen) |
| sampler | `euler` | node 26 `KSampler` “Sampler - CFG 1, euler” (subgraph: Paint it with Qwen) |
| scheduler | `simple` | node 26 `KSampler` “Sampler - CFG 1, euler” (subgraph: Paint it with Qwen) |
| denoise | `1` | node 26 `KSampler` “Sampler - CFG 1, euler” (subgraph: Paint it with Qwen) |

**Inputs and output prefixes**

| field | value | where |
|---|---|---|
| input image | `DJI_0021.JPG` | node 2 `AUSBOSS_NODES_ImageCropRotatePad` “Image Crop + Rotate + Pad - Your picture” |
| output prefix | `qwen21_inpaint` | node 15 `AUSBOSS_NODES_SaveImage` “Save Image” |
| output prefix | `qwen_inpaint_depth_in` | node 43 `SaveImage` “Save depth IN (qwen_inpaint)” |
| output prefix | `qwen_inpaint_depth_out` | node 44 `SaveImage` “Save depth OUT (qwen_inpaint)” |

**Parameters that do not come from widgets**

- node 3 `AUSBOSS_NODES_MaskByTouch` “Mask by Touch - Click what to change”: comes from links, the value shown above is the stale widget value: clip, input image, model
- node 12 `AUSBOSS_NODES_LoraLoader` “LoRA Loader - Speed LoRA”: comes from links, the value shown above is the stale widget value: model
- node 15 `AUSBOSS_NODES_SaveImage` “Save Image”: fed by links (the value stored in the widget of this node is inert): images
- node 41 `DepthAnythingV2Preprocessor` “Depth of SOURCE (qwen_inpaint)”: comes from links, the value shown above is the stale widget value: input image
- node 42 `DepthAnythingV2Preprocessor` “Depth of RESULT (qwen_inpaint)”: comes from links, the value shown above is the stale widget value: input image
- node 43 `SaveImage` “Save depth IN (qwen_inpaint)”: comes from links, the value shown above is the stale widget value: images
- node 44 `SaveImage` “Save depth OUT (qwen_inpaint)”: comes from links, the value shown above is the stale widget value: images
- node 19 `StringFormat` “Format Text - Your request, and keep the rest” (subgraph: Paint it with Qwen): inputs with no value in this file (they arrive from links): values.a
- node 20 `TextEncodeQwenImage21` “Text Encode Qwen Image 2.1 - The crop and your request” (subgraph: Paint it with Qwen): comes from links, the value shown above is the stale widget value: clip, prompt, vae
- node 20 `TextEncodeQwenImage21` “Text Encode Qwen Image 2.1 - The crop and your request” (subgraph: Paint it with Qwen): inputs with no value in this file (they arrive from links): images.image_1
- node 23 `QwenImage21Cache` “Reference cache” (subgraph: Paint it with Qwen): comes from links, the value shown above is the stale widget value: model
- node 26 `KSampler` “Sampler - CFG 1, euler” (subgraph: Paint it with Qwen): comes from links, the value shown above is the stale widget value: latent_image, model, negative, positive, seed, steps
- node 28 `AUSBOSS_NODES_StitchInpaint` “Stitch Inpaint - Put the new part back” (subgraph: Paint it with Qwen): comes from links, the value shown above is the stale widget value: inpainted, stitcher
- node 17 `AUSBOSS_NODES_CropForInpaint` “Crop For Inpaint - Crop around the picked part” (subgraph: Cut out the picked part): comes from links, the value shown above is the stale widget value: input image, mask
- node 18 `GrowMask` “Grow Mask - A little past the picked part” (subgraph: Cut out the picked part): comes from links, the value shown above is the stale widget value: mask

_(node 46 `LCTimer` has recorded no run yet — the times appear in the graph after the first run in the UI)_

**Verdict / status**

_(заполняется после прогона / to fill after the run)_
---
