#!/usr/bin/env python3
"""
add_instrumentation.py — add the SAME measurement tail to every workflow in this folder.

Why a script and not hand edits: three workflows come from three different custom-node
packs (comfyui-krea2edit + KJNodes, ComfyUI_LC123/LC_MaskMaker, ausboss-nodes). Only
pack-agnostic nodes can be identical across all of them, and the insertion has to be
mechanical so it is the same shape in every graph.

What gets added to each graph (5 nodes + 1 timer, identical everywhere):

  source-of-truth image ──┐
                          ├─ DepthAnythingV2Preprocessor (depth of the real photo)  ─ SaveImage <prefix>_depth_in
  generated image ────────┤
                          └─ DepthAnythingV2Preprocessor (depth of the result)     ─ SaveImage <prefix>_depth_out
                             both depth maps ────────────────────────────────────── LCBatchImageComparer (A/B)
                             (no sockets) ───────────────────────────────────────── LCTimer (on-canvas timing)

The two depth maps of the SAME run are the geometry-preservation check: visually in the
comparer, numerically in the external scoring script (the two saved PNGs are its input).
No installed node pack provides SSIM/PSNR/LPIPS/depth-correlation, so numbers are computed
outside the graph; inside the graph we only put things that are identical for every approach.

Nothing in the existing graph is rewired and no sampler/size/seed setting is changed:
the new nodes are extra consumers of signals that already exist.

Originals are kept in workflows/_orig/<name>.json.orig.

Usage:  python _tools/add_instrumentation.py [--check]
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # workflows/

DEPTH_CKPT = "depth_anything_v2_vits.pth"              # smallest Depth-Anything-V2: cheap
DEPTH_RESOLUTION = 1024                                # keep windows/roof edges resolvable
COMPARER = "LCBatchImageComparer"                      # from ComfyUI_LC123_nodes, pack-agnostic here
TIMER = "LCTimer"                                      # browser-side, no sockets, never executes

TARGETS = {
    "krea2_edit.json": {
        "prefix": "krea2_edit",
        "src": (87, "IMAGE", "source image (resized base)"),
        "out": (54, "IMAGE", "VAEDecode - generated"),
    },
    "moss_inpaint.json": {
        "prefix": "moss_inpaint",
        "src": (30, "image", "AspectRatioSimplifier - corrected source photo"),
        "out": (98, "IMAGE", "Get_Layout image - generated"),
    },
    "qwenImage_inpaint.json": {
        "prefix": "qwen_inpaint",
        "src": (2, "image", "Crop+Rotate+Pad - source photo"),
        "out": (29, "your picture, changed", "subgraph output - stitched result"),
    },
}


def out_slot(node, name):
    for i, o in enumerate(node.get("outputs", [])):
        if o.get("name") == name:
            return i
    raise KeyError(f"node {node['id']} ({node['type']}) has no output {name!r}")


def make_node(node_id, ntype, title, pos, size, inputs, widgets, outputs):
    return {
        "id": node_id,
        "type": ntype,
        "title": title,
        "pos": [int(pos[0]), int(pos[1])],
        "size": [int(size[0]), int(size[1])],
        "flags": {"collapsed": False},
        "order": 900 + node_id,          # recomputed by the frontend on load
        "mode": 0,
        "minsize": {"contentHeight": 120, "width": size[0]},
        "inputs": inputs,
        "outputs": outputs,
        "properties": {"Node name for S&R": ntype},
        "widgets_values": widgets,
    }


def process(path, check_only=False):
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = TARGETS[path.name]
    nodes = {n["id"]: n for n in data["nodes"]}

    already = [n["id"] for n in data["nodes"]
               if n.get("title", "").startswith(("Depth of SOURCE (" + cfg["prefix"],
                                                 "Geometry A/B: depth IN vs OUT (" + cfg["prefix"]))]
    if already:
        raise SystemExit(f"{path.name}: already instrumented (nodes {already}); "
                         f"restore _orig/{path.name}.orig first or edit the prefix")

    src_id, src_name, _ = cfg["src"]
    out_id, out_name, _ = cfg["out"]
    src_slot = out_slot(nodes[src_id], src_name)
    out_slot_idx = out_slot(nodes[out_id], out_name)

    base_x, base_y = nodes[out_id]["pos"]
    start = (base_x, base_y + 640)

    next_node = max(nodes)
    next_link = max([l[0] for l in data["links"]] + [0]) + 1
    added, new_links = [], []

    def link(src, sslot, dst, dslot, ltype):
        nonlocal next_link
        next_link += 1
        new_links.append([next_link, src, sslot, dst, dslot, ltype])
        outs = nodes[src]["outputs"][sslot].setdefault("links", None)
        if outs is None:
            nodes[src]["outputs"][sslot]["links"] = outs = []
        outs.append(next_link)
        if dst in nodes:                       # existing node: attach on its input
            nodes[dst]["inputs"][dslot]["link"] = next_link
        return next_link

    def consume(node, name, ltype):
        for i, inp in enumerate(node.get("inputs", [])):
            if inp.get("name") == name:
                return i
        node.setdefault("inputs", []).append({"name": name, "type": ltype, "link": None})
        return len(node["inputs"]) - 1

    def new_id():
        nonlocal next_node
        next_node += 1
        return next_node

    depth_in_id, depth_out_id, save_in_id, save_out_id = new_id(), new_id(), new_id(), new_id()
    comparer_id, timer_id = new_id(), new_id()
    depth_inputs = lambda: [{"name": "image", "type": "IMAGE", "link": None}]

    # 1/2 depth of the real photo and depth of the result — same node type, same settings
    for nid, title, sid, slot, prefix in (
        (depth_in_id, f"Depth of SOURCE ({cfg['prefix']})", src_id, src_slot, "_depth_in"),
        (depth_out_id, f"Depth of RESULT ({cfg['prefix']})", out_id, out_slot_idx, "_depth_out"),
    ):
        n = make_node(nid, "DepthAnythingV2Preprocessor", title,
                      (start[0], start[1] + (0 if nid == depth_in_id else 320)), (320, 130),
                      depth_inputs(), [DEPTH_CKPT, DEPTH_RESOLUTION],
                      [{"name": "IMAGE", "type": "IMAGE", "links": []}])
        data["nodes"].append(n); nodes[nid] = n
        link(sid, slot, nid, 0, "IMAGE")
        added.append((nid, "DepthAnythingV2Preprocessor", title))

    # 3/4 save both depth maps -> input of the external scoring script (identical for all runs)
    for nid, title, src, prefix in (
        (save_in_id, f"Save depth IN ({cfg['prefix']})", depth_in_id, cfg["prefix"] + "_depth_in"),
        (save_out_id, f"Save depth OUT ({cfg['prefix']})", depth_out_id, cfg["prefix"] + "_depth_out"),
    ):
        n = make_node(nid, "SaveImage", title, (start[0] + 420, start[1] + (0 if nid == save_in_id else 320)),
                      (320, 300),
                      [{"name": "images", "type": "IMAGE", "link": None},
                       {"name": "filename_prefix", "type": "STRING", "widget": {"name": "filename_prefix"}, "link": None}],
                      [prefix], [])
        data["nodes"].append(n); nodes[nid] = n
        link(src, 0, nid, 0, "IMAGE")
        added.append((nid, "SaveImage", title))

    # 5 the one comparator for every workflow: input-depth vs output-depth
    n = make_node(comparer_id, COMPARER, f"Geometry A/B: depth IN vs OUT ({cfg['prefix']})",
                  (start[0] + 800, start[1]), (720, 560),
                  [{"name": "image_a", "type": "IMAGE", "link": None},
                   {"name": "image_b", "type": "IMAGE", "link": None}],
                  [], [])
    data["nodes"].append(n); nodes[comparer_id] = n
    link(depth_in_id, 0, comparer_id, 0, "IMAGE")
    link(depth_out_id, 0, comparer_id, 1, "IMAGE")
    added.append((comparer_id, COMPARER, "geometry comparator"))

    # 6 on-canvas stopwatch (no sockets; keeps its history inside the workflow file)
    n = make_node(timer_id, TIMER, f"Run timer ({cfg['prefix']})", (start[0], start[1] - 120), (260, 90),
                  [], [], [])
    data["nodes"].append(n); nodes[timer_id] = n
    added.append((timer_id, TIMER, "run timer"))

    data["links"].extend(new_links)
    data["last_node_id"] = max(data["last_node_id"], next_node)
    data["last_link_id"] = max(data.get("last_link_id") or 0, next_link)

    if check_only:
        return added, new_links
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return added, new_links


def main():
    check = "--check" in sys.argv
    for name, cfg in TARGETS.items():
        p = HERE / name
        backup = HERE / "_orig" / (p.name + ".orig")
        if not backup.exists():
            shutil.copy2(p, backup)
        added, links = process(p, check)
        print(f"== {name}: +{len(added)} nodes, +{len(links)} links (prefix '{cfg['prefix']}')")
        for nid, ntype, title in added:
            print(f"   [{nid:>3}] {ntype:<28} {title}")


if __name__ == "__main__":
    main()
