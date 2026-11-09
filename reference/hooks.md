# Hooks

The detector hook runs `detect.py` after any Write or Edit of a plan or beats JSON in this project and surfaces P0–P2 findings to the agent as context, so staging mistakes are caught as they are made.

Commands (map `/excelsior hooks <arg>` to `python3 .claude/skills/excelsior/scripts/hook.py <arg>`):

- `on` → `hook.py install` (adds a PostToolUse hook to `.claude/settings.json`; tell the user it was added and where)
- `off` → `hook.py uninstall`
- `status` → `hook.py status`
- `ignore-rule <rule>` → silence one rule for this project (e.g. `craft-even-split` for a series that splits evenly on purpose); record why in STYLE.md
- `ignore-file <name>` → skip a file (an archived chapter)
- `reset` → clear ignores

Never install the hook unasked. When the hook reports findings during a build, act on them in the same batch instead of re-running the detector by hand.
