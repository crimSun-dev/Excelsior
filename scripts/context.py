# -*- coding: utf-8 -*-
"""Load the project's Excelsior context once per session and print directives.

Reads SERIES.md (story truth: premise, audience, canon, cast, format), STYLE.md (visual world: line, tone,
paper, borders, lettering voices) and the chapter brief for --target, then prints them with directives:
  NO_SERIES_MD      no series bible yet: route new work through `init`
  NO_STYLE_MD       no recorded visual world: `document` it from existing pages, or new-work records it at finish
  CONTEXT_STALE     a file was written by an older Excelsior: report it, do not repair it unasked
  FORMAT <print|webtoon|both> READING <ltr|rtl>   load reference/print.md or reference/webtoon.md
usage: python3 context.py [--target CHAPTER_OR_PLAN] [--root DIR]
"""
import argparse, glob, os, sys
from _common import project_root, frontmatter, series_config, state, CONTEXT_VERSION, VERSION


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target"); ap.add_argument("--root")
    a = ap.parse_args(argv)
    root = a.root or project_root()
    out, directives = [], []
    print(f"# Excelsior {VERSION} context · project root: {root}")
    for name, flag in (("SERIES.md", "NO_SERIES_MD"), ("STYLE.md", "NO_STYLE_MD")):
        p = os.path.join(root, name)
        meta, body = frontmatter(p)
        if meta is None:
            directives.append(flag); continue
        v = str(meta.get("excelsior", "0"))
        if v != str(CONTEXT_VERSION):
            directives.append(f"CONTEXT_STALE {name} (written for excelsior:{v}, this version reads {CONTEXT_VERSION})")
        out.append(f"\n## {name}\n" + body.strip())
    cfg = series_config(root)
    directives.append(f"FORMAT {cfg['format']} READING {cfg['reading']} TURN_REVEALS {cfg['turn_reveals']} LANGUAGE {cfg['language']}")
    if a.target:
        key = os.path.splitext(os.path.basename(a.target))[0].split("_plan")[0]
        cands = glob.glob(state(root, "briefs", f"{key}*.md"))
        if cands:
            out.append(f"\n## Chapter brief ({os.path.basename(cands[0])})\n" + open(cands[0], encoding="utf-8").read().strip())
        else:
            directives.append(f"NO_BRIEF {key} (shape writes one; not required for refinement)")
    snaps = sorted(glob.glob(state(root, "critique", "*.json")), key=os.path.getmtime)
    if snaps:
        directives.append(f"LATEST_CRITIQUE {os.path.relpath(snaps[-1], root)}")
    print("\n".join("DIRECTIVE " + d for d in directives))
    print("\n".join(out))
    if "NO_SERIES_MD" in directives:
        print("\nNext: new chapters or a new visual world go through `init` first; a narrow fix to an existing plan may proceed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
