# Doctor

Report, and on request repair, drift between this project's Excelsior files and what this version reads.

Run `python3 .claude/skills/excelsior/scripts/doctor.py` and present its findings as a short table: file, status, action, whether it is `auto`.

- **auto** findings (a version stamp) are safe mechanical repairs: apply them with `doctor.py --fix` only when the user asks, or let the next write to that file perform them.
- **missing** files route to their command (`init` for SERIES.md, `document` for STYLE.md); never create them inside doctor.
- **missing sections** are filled by interview, never invented.
- **stale snapshots** (critiques of plans that no longer exist) are deleted only with the user's yes.

Doctor never runs as a side effect of a staging task.
