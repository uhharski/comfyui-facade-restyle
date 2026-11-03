#!/usr/bin/env python3
"""Import the API-format graph of runs that already happened, straight from ComfyUI.

    python scripts/import_api_from_history.py            # newest matching run per graph
    python scripts/import_api_from_history.py --list     # describe what is in the history

Why this exists: any graph that has been queued in the UI already exists on the server in API
format, because ComfyUI stores the executed prompt in its history. Pulling it from there is
better than exporting by hand from the menu — it is the graph that REALLY ran (a manual export
writes what is on screen, which is not always the same), and it needs no browser work at all.

A history entry is matched to a graph in `workflows/manifest.json` by node ids: the frontend
keeps the ids of the UI graph when it converts it to API format, so the id set of the graph in
this repo has to be a subset of the id set of the run. That test is specific here — the three
graphs differ in ids, and the measurement nodes added to each of them are unique.

Writes `workflows/_api/<name>.api.json` (the same format the UI's "Export (API)" downloads),
ready for `scripts/run_workflow.py <id>`, and appends the prompt id it came from to
`workflows/_api/import_log.txt`. The history lives in the server's memory: after a ComfyUI
restart it is empty, and only runs that already happened can be imported.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

API_DIR = lib.WORKFLOWS / "_api"


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def history_entries(url: str, limit: int = 100) -> list[dict]:
    """The server's history, oldest first. An entry's `prompt` field is [id, graph, extra]:
    the graph is exactly the API-format dict that was executed."""
    h = get_json(f"{url}/history?max_items={limit}")
    out = []
    for pid, e in h.items():
        pr = e.get("prompt") or []
        graph = pr[1] if len(pr) > 1 else {}
        extra = pr[2] if len(pr) > 2 else {}
        out.append({"pid": pid, "graph": graph, "extra": extra,
                    "status": (e.get("status") or {}).get("status_str"),
                    "at": extra.get("updated_at") or extra.get("created_at") or 0})
    out.sort(key=lambda e: e["at"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="only describe the history")
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    man = lib.load_manifest()
    url = man["comfyui"]["url"].rstrip("/")
    try:
        entries = history_entries(url, args.limit)
    except Exception as exc:                                     # noqa: BLE001
        print(f"cannot reach ComfyUI at {url}: {exc}", file=sys.stderr)
        return 2
    print(f"history at {url}: {len(entries)} entries")
    if args.list:
        for e in entries:
            kinds = sorted({n.get("class_type") for n in e["graph"].values()})
            print(f"  {e['pid'][:14]}  nodes {len(e['graph']):>3}  status {e['status']}  "
                  f"at {datetime.fromtimestamp(e['at'] / 1000):%Y-%m-%d %H:%M}")
            print(f"      classes: {', '.join(kinds[:14])}{' ...' if len(kinds) > 14 else ''}")
        return 0

    API_DIR.mkdir(parents=True, exist_ok=True)
    log, found = API_DIR / "import_log.txt", 0
    for entry in man["workflows"]:
        graph = lib.load_workflow(entry)
        ids = {str(n["id"]) for n in graph.get("nodes", [])}
        matches = [e for e in entries if ids <= set(e["graph"])]
        if not matches:
            print(f"  {entry['id']}: nothing in the history contains this graph "
                  f"({len(ids)} node ids) — queue it in the UI first")
            continue
        e = matches[-1]                       # the newest run of this graph
        dst = API_DIR / (Path(entry["file"]).stem + ".api.json")
        dst.write_text(json.dumps(e["graph"], indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        with log.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {entry['id']} <- prompt {e['pid']} "
                    f"({len(e['graph'])} nodes, status {e['status']})\n")
        print(f"  {entry['id']}: wrote {dst.relative_to(lib.ROOT)} from prompt {e['pid']} "
              f"({len(e['graph'])} nodes, status {e['status']})")
        found += 1
    print(f"\n{found}/{len(man['workflows'])} imported. Replay headlessly with: "
          f"python scripts/run_workflow.py <id>")
    if not found:
        print("Nothing to import: the history only knows about runs that already happened. "
              "--list shows what is in there.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
