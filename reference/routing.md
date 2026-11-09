# No-argument routing: the context-aware menu

Read this when the user invokes `/excelsior` with no argument. They are asking "what should I do next with my manga?" Make the menu context-aware instead of static.

Setup has already run `context.py`. If that reported `NO_SERIES_MD`, the project has no captured story truth: lead the menu with `/excelsior init` as the top recommendation (one line on why: every other command stages against the series bible) and still show the rest below; don't silently jump into init. Otherwise run `python3 .claude/skills/excelsior/scripts/context_signals.py` once and read its JSON, then lead with the **2–3 highest-value next commands**, each with a one-line reason pulled from the signals, followed by the full menu (the Commands table in SKILL.md, grouped by category). **Never auto-run a command; the recommendation is a suggestion the user confirms.**

Reason over the signals; there is no score to obey:

- `setup.hasStyle` false while `setup.hasPlans` true, or pages exist on disk → `document` (capture the visual world before it drifts).
- `setup.hasBeats` true and `setup.hasPlans` false → the chapter is written but not staged: `shape` if there is no brief for it, otherwise plan it (new-work, which runs `plan_chapter.py`).
- `critique.latest` is `null` and a plan exists → the project has never been critiqued; `/excelsior critique <plan>` is a strong default.
- `critique.latest` with a low `score` or non-zero `p0` / `p1` → `polish` (it reads that snapshot as its backlog), or re-run `critique` if `age_hours` is large and the plan changed since.
- `git.changedFiles` pointing at one chapter → scope `audit` or `polish` to that plan, naming it.
- `setup.format` is `both` and only one format exists on disk → `adapt`.
- Otherwise group by intent (stage something new / improve what's there / iterate visually), tailored to the current chapter and format.

**If `scan.targets` is non-empty, run `python3 .claude/skills/excelsior/scripts/detect.py --json <scan.targets joined by spaces>` once.** Fold the hits into your picks: many `craft-equal-boxes` or `slop-equal-grid` hits → `layout`; `craft-peak-not-biggest` or `craft-flat-loud` → `bolder`; `letter-*` families → `typeset` or `clarify`; `shot-talking-heads` or `slop-face-parade` → `layout` with a shot-language focus; `craft-weak-ending` or `craft-reveal-parity` → `shape` the page turns or `onboard` for a first chapter; `slop-splash-inflation` or `craft-middle-splash` → `distill`. It's a real, current signal that beats guessing. If the detector errors, skip it and recommend `audit`; never block the suggestion on it.

Keep it to 2–3 pointed picks with the exact command to type. The menu stays the fallback; the recommendation is the lede.
