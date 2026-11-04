# Gallery manifest - where each gallery image came from

Every image in `docs/gallery/` was copied out of this machine's ComfyUI output folder
(`J:/AI/ComfyUI-Easy-Install/ComfyUI/output`). Nothing here was re-generated: these are the files real
runs wrote, resized to at most 1600 px wide and saved as JPEG (q92) - which is why their names and sizes
differ from the originals in the table below. The full prompt text of each run is in `prompts.json` here;
the graphs are in `workflows/`; the scored rows named in the last column are the rows of `docs/metrics.md`.
The original PNGs still carry their workflow in the file metadata, so any of them can be dragged back onto
the ComfyUI canvas. `MANIFEST.json` is the machine-readable form of this table.

| gallery file | came from | run at | native size | seed | steps/cfg | what was asked of the model | what this image is |
|---|---|---|---|---|---|---|---|
| `source_DJI_0021.jpg` | `DJI_0021.JPG` | n/a | 1600x900 | - | - | - | the single input of every measured run: aerial photo of the real house (the repo copy is a 2048px, GPS-stripped version) |
| `krea2_edit/pair00004.jpg` | `krea2_edit_00113_.png` | 2026-11-04 00:29 | 1024x576 | 1026441803173828 | 10 / 1.0 | light warm-grey plaster on the main volumes, dark graphite window frames and door, dark standing-seam metal roof | measured row krea2_edit/00004 - the best-scoring run of this method, fixed seed 20261103 |
| `krea2_edit/pair00003.jpg` | `krea2_edit_00112_.png` | 2026-11-04 00:28 | 1024x576 | 20261103 | 10 / 1.0 | the same prompt and the same seed as pair00004 | measured row krea2_edit/00003 - its distance from pair00004 IS the run-to-run floor of this method: same seed, visibly different result |
| `krea2_edit/pair00002.jpg` | `krea2_edit_00111_.png` | 2026-11-04 00:25 | 1024x576 | 20261103 | 10 / 1.0 | the same prompt and seed again | measured row krea2_edit/00002 - the row where the geometry score collapsed (r 0.33): the house was redrawn from another position |
| `krea2_edit/style_three-materials.jpg` | `krea2_edit_00089_.png` | 2026-11-03 00:47 | 1152x648 | 287993650944121 | 10 / 1.0 | a three-material request: pale ash-grey facing brick on designated wall sections, charcoal graphite render on monolithic walls, vertical larch slats on accents | not measured as a row: a different finish request through the same graph, no spatial control at all |
| `krea2_edit/style_model-chooses.jpg` | `krea2_edit_00090_.png` | 2026-11-03 00:49 | 1152x648 | 1078819473404524 | 10 / 1.0 | no finish named in the main prompt ('apply modern facade finishing materials'), only a material list in a second text block | not measured as a row: what the method does when the finish is not stated - it picks one itself |
| `krea2_edit/early_test_other_frame.jpg` | `krea2_edit_00065_.png` | 2026-10-31 23:03 | 1152x648 | 509643149738007 | 10 / 1.0 | warm wooden panels + white plaster + panoramic glass + finished landscaping | 31.10 test on a different frame (DJI_0001): shows the 'the photo turns into a CGI render' failure mode, kept on purpose |
| `moss_inpaint/pair00001.jpg` | `MOSS Box Edit/Test_2026-11-03_00011_.png` | 2026-11-03 22:03 | 1024x576 | - | None / 2.5 | same generic 'apply modern facade finishing materials' + a material list, given as a layout-box prompt; the edit is allowed only inside the box | measured row moss_inpaint/00001 - colour+depth control with layout boxes, run from the UI |
| `moss_inpaint/pair00002.jpg` | `MOSS Box Edit/Test_2026-11-04_00001_.png` | 2026-11-04 00:33 | 1024x576 | - | None / 2.5 | as above | measured row moss_inpaint/00002 - headless replay of the frozen API graph |
| `moss_inpaint/pair00003.jpg` | `MOSS Box Edit/Test_2026-11-04_00003_.png` | 2026-11-04 00:34 | 1024x576 | - | None / 2.5 | as above | measured row moss_inpaint/00003 - second headless replay; note this method is the deterministic one (00001/00005/00009 are byte-identical files) |
| `moss_inpaint/not_a_replay.jpg` | `MOSS Box Edit/Test_2026-11-04_00007_.png` | 2026-11-04 00:35 | 1024x576 | - | None / 2.5 | as above | a file from the same folder that is NOT a replay of the frozen graph: the camera moved. This is the case the geometry metric under-detects (r still 0.99) |
| `moss_inpaint/earlier_graph_version.jpg` | `MOSS Box Edit/Test_2026-11-03_00003_.png` | 2026-11-03 18:51 | 1080x608 | - | None / 2.5 | as above | an 18:51 run of the graph before the instrumentation pass (1080x608): yellow brick with timber frames, kept as an older variant of the same request |
| `qwen_inpaint/pair00001.jpg` | `qwen21_inpaint_00040.png` | 2026-11-03 22:08 | 1049x590 | 20261103 | None / 1.0 | rebuild the surface here as light warm-grey plaster with a dark graphite window frame, keep the exact shape and position of the opening and everything around it | measured row qwen_inpaint/00001 - inpaint inside a mask touched in the UI; everything outside it is stitched back pixel-identical (1049x590 crop) |
| `qwen_inpaint/pair00002.jpg` | `qwen21_inpaint_00041.png` | 2026-11-03 22:09 | 1049x590 | 20261103 | None / 1.0 | the same mask, the same seed | measured row qwen_inpaint/00002 - second run, essentially the same image: this method is reproducible in the region it edits |
| `qwen_inpaint/pair00003.jpg` | `qwen21_inpaint_00045.png` | 2026-11-04 00:38 | 1049x590 | 947104845645106 | None / 1.0 | the same mask region | measured row qwen_inpaint/00003 - produced from the UI, the graph cannot be replayed headless (the touched points live in the browser) |
| `qwen_inpaint/style_slate-larch.jpg` | `qwen21_inpaint_00012.png` | 2026-11-02 12:19 | 4032x2268 | 614694269351546 | None / 1.0 | dark slate stone masonry on the lower volume + dark larch wood siding above, alpine chalet | a style variant of the whole facade, full 4032x2268 output of the graph before instrumentation - not a measured row |
| `qwen_inpaint/style_shou-sugi-ban.jpg` | `qwen21_inpaint_00013.png` | 2026-11-02 12:20 | 4032x2268 | 305226617989783 | None / 1.0 | black charred wood siding (shou sugi ban), minimalistic dark aluminium frames, Nordic aesthetic | style variant, same graph |
| `video/first_frame.jpg` (moved on 04.11 from `qwen_inpaint/style_charred-plus-timber.jpg`) | `qwen21_inpaint_00015.png` | 2026-11-02 12:31 | 4032x2268 (the repo copy is a 1600x900 JPEG) | 551516032584579 | None / 1.0 | charred wood with warm timber accent slats around the entrance and window cutouts | style variant, same graph; since 04.11 this same file is also the **first frame** of `video/video_03.mp4` |
| `qwen_inpaint/style_micro-cement-panels.jpg` | `qwen21_inpaint_00026.png` | 2026-11-02 12:46 | 4032x2268 | 21312943037179 | None / 1.0 | ultra-light grey vertical micro-cement panels front/rear, dark anthracite gable ends, dark metal frames | style variant, same graph |
| `qwen_inpaint/style_offwhite-composite.jpg` | `qwen21_inpaint_00029.png` | 2026-11-02 12:49 | 4032x2268 | 403732651075716 | None / 1.0 | off-white vertical composite panels on the main volume, dark anthracite aluminium slats on the side wing | style variant, same graph |
| `qwen_inpaint/appearance_row_00039.jpg` | `qwen21_inpaint_00039.png` | 2026-11-03 17:50 | 4032x2268 | 191308024412646 | 25 / 1.0 | a long material list: pale ash-grey facing brick with warm beige tones, smooth painted fibre-cement render with charcoal graphite walls, vertical larch slat cladding - all asked as one prompt, and 'keep everything else exactly the same' appended by the graph | the image the appearance-metric row method_qwen_full_00039.json was computed on. It is a full-frame 4032x2268 output of the same graph (this variant does not crop to the mask), which is exactly why it is the only Qwen row metric 2 could score against the source frame. What was masked is recorded NOWHERE: the mask was never written to a file, and the touches still stored in the node are three points named 'car', 'chair', 'table' - they cannot explain an edit that covers the whole facade, so they are most likely leftover demo state from an earlier picture of the same size. Weakest of the four appearance rows; the next-steps list in README.md section 5, item 3 (save the mask) is what would close it. |

## Video (kept at native size - nothing here was re-encoded or resized)

| gallery file | came from | run at | what this video is |
|---|---|---|---|
| `video/video_03.mp4` | `2026-11-04/video_03.mp4` (`VideoMakerV2`, save prefix `%date%/video`) | 2026-11-04 19:01 | the first video in this repo: made by [`../../workflows/MMH3.json`](../../workflows/MMH3.json), a **MiniMax H3 FL2V** (frame-to-video) graph - the first and last frames of the shot are given as images, the camera move and the soundscape are asked in words. Not a measured row: that graph has no depth/compare nodes, and the video branch is only the next-steps item 6 in the root README, just started. |
| `video/first_frame.jpg` | the gallery row `qwen_inpaint/style_charred-plus-timber.jpg` (`qwen21_inpaint_00015.png`), byte-identical, moved into `video/` on 04.11 | 2026-11-02 12:31 | the **first frame** the video was generated between (LoadImage `qwen21_inpaint_00015.png`) |
| `video/last_frame.png` | `qwen21_inpaint_00014.png`, byte-identical, 4032x2268 at native size | 2026-11-02 12:23 (file date, see the name-collision note below) | the **last frame** of the shot (LoadImage `qwen21_inpaint_00014.png`); its own embedded metadata says seed 139346433945169, euler/simple, cfg 1.0, prompt = black shou-sugi-ban charred siding + warm timber accents (the request between the 00013 and 00015 gallery rows, never catalogued) |

The file is the byte-exact ComfyUI output: 1024x576, 24 fps, 5.17 s, 124 frames, H.264 video + AAC
stereo audio (the graph loads a separate audio VAE, so the video comes with sound). As saved, the graph
ran seed 4 (fixed), 6 steps, cfg 1.0, `res_multistep`/`simple`; the duration widget says 5 s and a frame-
count expression rounds it to 124 frames - while the prompt text itself aligns the two reference pictures
at 0.00 s and 15.08 s of "the target video", so the prompt was written for a longer shot than what was
generated. This is a case of the repo's standing rule: the recorded parameters are from the saved file,
not from the widgets.

The two frames the video is built between now sit next to it, byte-pinned: `first_frame.jpg` is the
byte-identical gallery image of `qwen21_inpaint_00015.png` (the row `style_charred-plus-timber.jpg`
above - on 04.11 the file was moved out of `qwen_inpaint/` into `video/`, and the graph's `LoadImage`
name refers to the copy in ComfyUI's `input/`), and `last_frame.png` is the byte-identical full-size
output `qwen21_inpaint_00014.png`, a shou-sugi-ban-plus-timber style variant whose prompt text sits
between the 00013 and 00015 rows and was never catalogued before.

One honest wrinkle stays on the record: the ComfyUI folder holds **two** files named
`qwen21_inpaint_00014.png` / `_00015.png` by date - 02.11 12:2x and 04.11 12:32 - and the two bytes of
a pair are **identical**, so either the fixed-seed style variant reproduced itself exactly on 04.11, or
the same file was re-saved under a reused counter number. Either way the bytes that went into the video
are now preserved in this folder, which is what provenance needs.

What was asked of the model (the prompt in the graph, abbreviated): a fixed-lens, hyper-stable photoreal
"drone shot" glide from left to right along the western facade, starting exactly at the framing of
Picture 1 and ending exactly at that of Picture 2, rigid walls / straight lines / no warping or morphing
throughout, plus a soft drone-propeller ambience and a minimal cinematic soundtrack (low cello, piano).

## Depth pairs (PNG at native size - these two images are what the geometry metric compared)

| gallery file | came from |
|---|---|
| `depth/krea2_pair00004_depth_in.png` | `krea2_edit_depth_in_00004_.png` |
| `depth/krea2_pair00004_depth_out.png` | `krea2_edit_depth_out_00004_.png` |
| `depth/moss_pair00003_depth_in.png` | `moss_inpaint_depth_in_00003_.png` |
| `depth/moss_pair00003_depth_out.png` | `moss_inpaint_depth_out_00003_.png` |
| `depth/qwen_pair00003_depth_in.png` | `qwen_inpaint_depth_in_00003_.png` |
| `depth/qwen_pair00003_depth_out.png` | `qwen_inpaint_depth_out_00003_.png` |

Not in the gallery on purpose: the 2052x576 files in `MOSS Box Edit/` are the node's own
source+result side-by-side stitches, not canvases that were generated. The 4032x2268 Qwen
outputs are reduced to 1600 px here, so their exact bytes exist only in the ComfyUI folder.

## Which gallery image each appearance row was measured on

The rows of `docs/metrics/appearance/` are numbers about specific files. Those files are here:

| appearance record | the file it measured | gallery copy |
|---|---|---|
| `method_krea2_00111.json` | `krea2_edit_00111_.png` | `krea2_edit/pair00002.jpg` |
| `method_moss_replay_00005.json` | `MOSS Box Edit/Test_2026-11-04_00005_.png` | `moss_inpaint/pair00002.jpg` (00001/00005/00009 are byte-identical files, so the gallery copy is that same image) |
| `method_moss_not_a_replay_00007.json` | `MOSS Box Edit/Test_2026-11-04_00007_.png` | `moss_inpaint/not_a_replay.jpg` |
| `method_qwen_full_00039.json` | `qwen21_inpaint_00039.png` | `qwen_inpaint/appearance_row_00039.jpg` |

One control input is not in this folder, because it was never a ComfyUI output: the 'other house'
control was measured against a file that lived in `AppData/Local/Temp` - its exact bytes are
preserved in `docs/metrics/appearance/inputs/`.
