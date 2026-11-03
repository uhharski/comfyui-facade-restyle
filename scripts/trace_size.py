#!/usr/bin/env python3
"""Trace where the generated size actually comes from in a graph.

Widgets that set a width/height are frequently overridden by an incoming link (a resize
node feeding the sampler), so reading the widget values alone can state the wrong canvas.
This walks the link chain backwards from the sampler's image/latent input and prints the
chain, so "identical conditions" in the measurements can be verified rather than assumed.

The graph is read in the UI format (links = [id, from_node, from_slot, to_node, to_slot, type]).

usage: python scripts/trace_size.py workflows/moss_inpaint.json 113 image
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SIZE_HINTS = ("width", "height", "resolution", "megapixel", "max_res", "side")
KIND = {"latent_image": "latent", "image": "image", "pixels": "image"}


def main() -> int:
    path = Path(sys.argv[1])
    start_id, slot = int(sys.argv[2]), sys.argv[3]
    graph = json.loads(path.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    links = {l[0]: l for l in graph.get("links", [])}

    def out_slot_name(node_id: int, link_id: int) -> str:
        for out in nodes[node_id].get("outputs", []):
            if out.get("links") and link_id in out["links"]:
                return out["name"]
        return "?"

    def walk(node_id: int, slot_name: str, depth: int = 0, seen=()):
        node = nodes.get(node_id)
        if node is None or node_id in seen or depth > 12:
            return
        inputs = node.get("inputs", [])
        target = next((i for i in inputs if i["name"] == slot_name), None)
        link = links.get(target["link"]) if target and target.get("link") else None
        wv = node.get("widgets_values")
        interesting = {}
        if isinstance(wv, dict):
            interesting = {k: v for k, v in wv.items()
                           if any(h in k.lower() for h in SIZE_HINTS)}
        elif isinstance(wv, list):
            interesting = {f"widget[{i}]": v for i, v in enumerate(wv)
                           if isinstance(v, (int, float)) and not isinstance(v, bool)}
        title = node.get("title") or ""
        print("  " * depth + f"{node['type']} #{node_id}"
              + (f" “{title}”" if title else "")
              + (f"  {interesting}" if interesting else ""))
        if link:
            walk(link[1], out_slot_name(link[1], link[0]), depth + 1, seen + (node_id,))

    print(f"# {path.name}: where the {KIND.get(slot, slot)} for node {start_id} comes from")
    walk(start_id, slot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
