# -*- coding: utf-8 -*-
"""Signals for the no-argument menu: what exists, what was last critiqued, what changed.
usage: python3 context_signals.py [--root DIR]   (prints JSON)"""
import argparse, glob, json, os, subprocess, sys, time
from _common import project_root, series_config, state, emit


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--root"); a = ap.parse_args(argv)
    root = a.root or project_root()
    plans = [p for p in glob.glob(os.path.join(root, "**", "*.json"), recursive=True)
             if "/.excelsior/" not in p and "/vendor/" not in p and "node_modules" not in p][:400]
    def kind(p):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception: return None
        pg = (d.get("pages") or [None])[0] if isinstance(d, dict) else None
        if not isinstance(pg, dict): return None
        return "plan" if "layout" in pg else ("beats" if "panels" in pg else None)
    found = {"plan": [], "beats": []}
    for p in plans:
        k = kind(p)
        if k: found[k].append(os.path.relpath(p, root))
    snaps = sorted(glob.glob(state(root, "critique", "*.json")), key=os.path.getmtime)
    latest = None
    if snaps:
        s = json.load(open(snaps[-1], encoding="utf-8"))
        latest = dict(path=os.path.relpath(snaps[-1], root), target=s.get("target"), score=s.get("score"),
                      p0=s.get("counts", {}).get("P0", 0), p1=s.get("counts", {}).get("P1", 0),
                      age_hours=round((time.time() - os.path.getmtime(snaps[-1])) / 3600, 1))
    changed = []
    try:
        r = subprocess.run(["git", "-C", root, "status", "--porcelain"], capture_output=True, text=True, timeout=5)
        changed = [l[3:] for l in r.stdout.splitlines() if l[3:].endswith((".json", ".md"))]
    except Exception:
        pass
    cfg = series_config(root)
    emit(dict(setup=dict(hasSeries=os.path.exists(os.path.join(root, "SERIES.md")), hasStyle=os.path.exists(os.path.join(root, "STYLE.md")),
                         format=cfg["format"], reading=cfg["reading"], hasPlans=bool(found["plan"]), hasBeats=bool(found["beats"])),
              plans=found["plan"][:20], beats=found["beats"][:20], critique=dict(latest=latest),
              briefs=[os.path.basename(b) for b in glob.glob(state(root, "briefs", "*.md"))],
              git=dict(changedFiles=changed[:30]), scan=dict(targets=found["plan"][:10])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
