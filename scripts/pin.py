# -*- coding: utf-8 -*-
"""Create or remove a standalone /<command> shortcut skill that routes to `excelsior <command>`.
usage: python3 pin.py pin|unpin COMMAND [--dir .claude/skills]"""
import os, sys, shutil

COMMANDS = {"shape", "init", "document", "extract", "critique", "audit", "polish", "bolder", "quieter", "distill", "harden", "onboard",
            "animate", "colorize", "typeset", "layout", "delight", "overdrive", "clarify", "adapt", "optimize", "live"}


def main(argv=None):
    a = argv or sys.argv[1:]
    if len(a) < 2 or a[0] not in ("pin", "unpin") or a[1] not in COMMANDS:
        print(__doc__ + "\ncommands: " + ", ".join(sorted(COMMANDS)), file=sys.stderr); return 1
    base = a[a.index("--dir") + 1] if "--dir" in a else os.path.join(".claude", "skills")
    d = os.path.join(base, f"excelsior-{a[1]}")
    if a[0] == "unpin":
        if os.path.isdir(d): shutil.rmtree(d); print(f"unpinned /{a[1]}")
        else: print(f"/{a[1]} was not pinned")
        return 0
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "SKILL.md"), "w").write(f"""---
name: excelsior-{a[1]}
description: Shortcut for `excelsior {a[1]}` on a manga chapter, page or plan. Use when the user types /{a[1]} in a manga project.
user-invocable: true
argument-hint: "[target]"
---
Load the `excelsior` skill and run its `{a[1]}` command with the user's arguments, exactly as if they had typed `/excelsior {a[1]} <args>`.
""")
    print(f"pinned /{a[1]} → {d}"); return 0


if __name__ == "__main__":
    sys.exit(main())
