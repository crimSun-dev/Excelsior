# -*- coding: utf-8 -*-
"""Persist and read critique snapshots (.excelsior/critique/<slug>.json). The snapshot is a backlog for polish.
usage: python3 critique_storage.py slug TARGET
       python3 critique_storage.py save TARGET SNAPSHOT.json     (adds timestamp, keeps previous as history)
       python3 critique_storage.py latest [TARGET]
       python3 critique_storage.py trend TARGET"""
import json, os, sys, time, glob
from _common import project_root, state, slug, emit


def main(argv=None):
    a = argv or sys.argv[1:]
    if not a: print(__doc__); return 1
    root = project_root(); cmd = a[0]
    if cmd == "slug":
        print(slug(a[1])); return 0
    if cmd == "save":
        s = slug(a[1]); snap = json.load(open(a[2], encoding="utf-8"))
        snap.update(target=a[1], slug=s, saved=time.strftime("%Y-%m-%dT%H:%M:%S"))
        p = state(root, "critique", f"{s}.json", make=True)
        hist = []
        if os.path.exists(p):
            old = json.load(open(p, encoding="utf-8")); hist = old.pop("history", []) + [{k: old.get(k) for k in ("saved", "score", "counts")}]
        snap["history"] = hist[-20:]
        json.dump(snap, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(os.path.relpath(p, root)); return 0
    if cmd == "latest":
        if len(a) > 1:
            p = state(root, "critique", f"{slug(a[1])}.json")
            if not os.path.exists(p): print("null"); return 0
        else:
            snaps = sorted(glob.glob(state(root, "critique", "*.json")), key=os.path.getmtime)
            if not snaps: print("null"); return 0
            p = snaps[-1]
        print(open(p, encoding="utf-8").read()); return 0
    if cmd == "trend":
        p = state(root, "critique", f"{slug(a[1])}.json")
        if not os.path.exists(p): print("[]"); return 0
        s = json.load(open(p, encoding="utf-8"))
        emit(s.get("history", []) + [{k: s.get(k) for k in ("saved", "score", "counts")}]); return 0
    print(__doc__); return 1


if __name__ == "__main__":
    sys.exit(main())
