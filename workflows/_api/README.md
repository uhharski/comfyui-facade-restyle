# `workflows/_api/` — graphs in API format (generated, do not hand-edit)

The files here are **not** the working copies of the graphs. The working copies are the
UI-format JSONs one level up (`krea2_edit.json`, `moss_inpaint.json`, `qwenImage_inpaint.json`):
they contain positions, groups, colors and subgraph definitions, and they are what you open in
ComfyUI. A file in this folder is the same graph reduced to what the server executes — node ids
mapped to `class_type`, `inputs`, `widgets_values` — which is what `POST /prompt` expects and
what `scripts/run_workflow.py` replays headlessly.

Naming rule: `<stem-of-the-ui-file>.api.json`, i.e. `krea2_edit.api.json`,
`moss_inpaint.api.json`, `qwenImage_inpaint.api.json`. That is the only name the scripts look
for (it comes from the `file` field of `workflows/manifest.json`).

## How a file gets here

1. **Recommended — from the server history**, after you have queued that graph in the UI once:

   ```
   python scripts/import_api_from_history.py            # or --list to inspect the history
   ```

   ComfyUI keeps the executed prompt for every run, so this writes the graph that **really**
   ran. Runs are matched to graphs by node ids (the ids survive the UI→API conversion), and the
   prompt id each file came from is appended to `import_log.txt`.

2. **By hand** — in ComfyUI: workflow menu → **File → Export (API)** (or the command palette:
   “Export Workflow (API Format)”; the legacy “Save (API Format)” button in the Save dropdown
   only appears after Settings → “Enable dev mode options (API save, etc.)”). A JSON downloads —
   its name is not predictable, so save it over the right name in this folder.

Prefer (1). A manual export writes what is currently on screen, which may include edits you
have not run; the history contains the graph that actually produced the images being measured.
For the Qwen graph, which contains a subgraph, the history has a second advantage: it records
how that subgraph reached the server (the frontend may expand it before queueing), which a hand
export does not necessarily reproduce.

If the history is empty (a ComfyUI restart clears it), just queue the graph once — the import
only needs one successful run, and the run itself is not wasted: its outputs are the first
measurement.
