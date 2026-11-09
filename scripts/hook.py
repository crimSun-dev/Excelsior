# -*- coding: utf-8 -*-
"""Claude Code PostToolUse hook: after a plan/beats JSON is written or edited, run the detector on it and surface
P0–P2 findings to the agent. Install with `hook.py install` (writes .claude/settings.json), remove with `uninstall`.
Respects .excelsior/config.json {"hook": "on|off", "ignore_rules": [...], "ignore_files": [...]}.
usage: (as hook) reads the tool event JSON on stdin · python3 hook.py install|uninstall|status|ignore-rule RULE|ignore-file NAME|reset"""
import json, os, sys, subprocess
from _common import project_root, state, HERE

CMD = f"python3 {os.path.join(HERE, 'hook.py')}"


def cfg_path(root): return state(root, "config.json", make=True)
def load(root):
    try: return json.load(open(cfg_path(root)))
    except Exception: return {}
def save(root, c): json.dump(c, open(cfg_path(root), "w"), indent=1)


def settings(root):
    p = os.path.join(root, ".claude", "settings.json"); os.makedirs(os.path.dirname(p), exist_ok=True)
    try: s = json.load(open(p))
    except Exception: s = {}
    return p, s


def main(argv=None):
    a = argv if argv is not None else sys.argv[1:]
    root = project_root()
    if a:
        c = load(root); cmd = a[0]
        if cmd == "install":
            p, s = settings(root)
            hooks = s.setdefault("hooks", {}).setdefault("PostToolUse", [])
            if not any(CMD in json.dumps(h) for h in hooks):
                hooks.append({"matcher": "Write|Edit", "hooks": [{"type": "command", "command": CMD}]})
            json.dump(s, open(p, "w"), indent=1); c["hook"] = "on"; save(root, c); print(f"hook on · {p}")
        elif cmd == "uninstall":
            p, s = settings(root)
            s.get("hooks", {})["PostToolUse"] = [h for h in s.get("hooks", {}).get("PostToolUse", []) if CMD not in json.dumps(h)]
            json.dump(s, open(p, "w"), indent=1); c["hook"] = "off"; save(root, c); print("hook off")
        elif cmd == "status": print(json.dumps(dict(hook=c.get("hook", "off"), ignore_rules=c.get("ignore_rules", []), ignore_files=c.get("ignore_files", []))))
        elif cmd in ("ignore-rule", "ignore-file"):
            k = "ignore_rules" if cmd == "ignore-rule" else "ignore_files"; c.setdefault(k, []); c[k] = sorted(set(c[k] + a[1:])); save(root, c); print(f"{k}: {c[k]}")
        elif cmd == "reset": c.pop("ignore_rules", None); c.pop("ignore_files", None); save(root, c); print("ignores cleared")
        else: print(__doc__); return 1
        return 0
    # running as a hook
    try: ev = json.load(sys.stdin)
    except Exception: return 0
    if load(root).get("hook", "on") == "off": return 0
    path = (ev.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(".json") or "/.excelsior/" in path or not os.path.exists(path): return 0
    try:
        d = json.load(open(path, encoding="utf-8")); pg = (d.get("pages") or [None])[0]
        if not isinstance(pg, dict) or not ("layout" in pg or "panels" in pg): return 0
    except Exception: return 0
    r = subprocess.run([sys.executable, os.path.join(HERE, "detect.py"), "--json", path], capture_output=True, text=True)
    try: res = json.loads(r.stdout)
    except Exception: return 0
    hot = [f for f in res["findings"] if f["severity"] in ("P0", "P1", "P2")]
    if not hot: return 0
    msg = f"Excelsior detector on {os.path.basename(path)} (score {res['score']}): " + "; ".join(
        f"{f['severity']} {f['rule']} p{f['page']}: {f['message']} → {f['fix']}" for f in hot[:12])
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
