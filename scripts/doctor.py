# -*- coding: utf-8 -*-
"""Report (and with --fix, repair) drift between this project's Excelsior files and what this version reads.
Never run as a side effect of a design task.
usage: python3 doctor.py [--fix] [--root DIR]"""
import argparse, glob, json, os, sys
from _common import project_root, frontmatter, state, CONTEXT_VERSION, VERSION, emit

REQUIRED = {"SERIES.md": ["## Premise", "## Readers", "## Canon", "## Cast", "## Format"],
            "STYLE.md": ["## Paper", "## Line", "## Borders and gutters", "## Lettering voices"]}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--fix", action="store_true"); ap.add_argument("--root")
    a = ap.parse_args(argv); root = a.root or project_root(); rep = []
    for name, heads in REQUIRED.items():
        p = os.path.join(root, name); meta, body = frontmatter(p)
        if meta is None:
            rep.append(dict(file=name, status="missing", action="run `init`" if name == "SERIES.md" else "run `document`", auto=False)); continue
        v = str(meta.get("excelsior", "0"))
        if v != str(CONTEXT_VERSION):
            rep.append(dict(file=name, status=f"version {v} → {CONTEXT_VERSION}", action="set frontmatter excelsior: 1", auto=True))
            if a.fix:
                txt = open(p, encoding="utf-8").read()
                if txt.startswith("---") and "excelsior:" in txt.split("\n---", 1)[0]:
                    import re; txt = re.sub(r"excelsior:\s*\S+", f"excelsior: {CONTEXT_VERSION}", txt, count=1)
                elif txt.startswith("---"): txt = txt.replace("---\n", f"---\nexcelsior: {CONTEXT_VERSION}\n", 1)
                else: txt = f"---\nexcelsior: {CONTEXT_VERSION}\n---\n" + txt
                open(p, "w", encoding="utf-8").write(txt)
        missing = [h for h in heads if h not in body]
        if missing: rep.append(dict(file=name, status="missing sections", sections=missing, action="add them by interview, never invent", auto=False))
    cfgp = state(root, "config.json")
    if os.path.exists(cfgp):
        try: json.load(open(cfgp))
        except Exception: rep.append(dict(file=".excelsior/config.json", status="unreadable JSON", action="fix or delete", auto=False))
    for snap in glob.glob(state(root, "critique", "*.json")):
        t = json.load(open(snap)).get("target")
        if t and not os.path.exists(os.path.join(root, t)) and not os.path.exists(t):
            rep.append(dict(file=os.path.relpath(snap, root), status="critique of a target that no longer exists", action="delete snapshot", auto=False))
    emit(dict(excelsior=VERSION, root=root, findings=rep, clean=not rep)); return 0


if __name__ == "__main__":
    sys.exit(main())
