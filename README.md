# Excelsior

A manga, manhwa and webtoon staging skill: the panel-and-page edition of Impeccable. Where Impeccable designs frontend interfaces, Excelsior stages chapters: panel layout, page rhythm, shot language, page turns, lettering, paper and value, print and scroll formats. It mirrors Impeccable's architecture one-to-one (a router SKILL.md, reader modes, a commands table, one playbook per command, a craft floor, a concept roll, dual-agent critique, a deterministic detector, a hook, a doctor), with every rule grounded in a measured reference library of 11,694 manga pages and 15 techniques read by eye.

## Install

Copy this folder to `.claude/skills/excelsior/` in a project (or your user skills folder). Python 3 with `numpy` is required for reference-inspired layouts; `playwright` is optional (proof PNGs); `fastapi` and `uvicorn` are optional (live server).

## Project files

| File | Owns |
|---|---|
| `SERIES.md` | Story truth: premise, readers, canon, cast, language rules, format, reading direction (written by `init`) |
| `STYLE.md` | Visual world: paper, line, tone, borders, page grammar, shot language, lettering voices (written by `document` or at the end of new work) |
| `.excelsior/briefs/<chapter>.md` | One chapter's strategy: mode per scene, page budget, turns, direction contract (written by `shape` / new work) |
| `<chapter>_plan.json` | The staged chapter: per page beat, energy, layout borrowed from a real page, per panel shot, angle, prompt, lettering |
| `.excelsior/critique/`, `seeds.jsonl`, `config.json` | Snapshots, concept rolls, hook settings |

## Commands

`/excelsior` with no argument shows a context-aware menu. Build: `shape`, `init`, `document`, `extract`. Evaluate: `critique`, `audit`. Refine: `polish`, `bolder`, `quieter`, `distill`, `harden`, `onboard`. Enhance: `animate`, `colorize`, `typeset`, `layout`, `delight`, `overdrive`. Fix: `clarify`, `adapt`, `optimize`. Iterate: `live`. Plus `hooks`, `doctor`, and `pin` for standalone shortcuts.

## Modes

Hook (turn the page) · Follow (track the action) · Converse (read the faces) · Immerse (be inside the world). Chosen per scene, not per series.

## Scripts

`scripts/detect.py` (34 rules in five families: craft, shot, lettering, pacing, AI-manga tells), `plan_chapter.py`, `inspire_page.py`, `proof.py`, `concept_seed.py`, `context.py`, `context_signals.py`, `critique_storage.py`, `doctor.py`, `hook.py`, `pin.py`. The layout engine and reference pool are vendored from mangaforge 0.2 (`vendor/mangaforge`): panel geometry only, never artwork.

## Example

`examples/knity/` holds the K-nity Volume 1 Chapter 1 and 2 plans with starter SERIES.md and STYLE.md. `CH01_plan_v4.json` is the Chapter 1 plan after `inspire_page.py --enforce-peak` re-laid the six impact pages where the hit was not the biggest panel (detector 69 → 86).

## Credits

Architecture, command set and playbook structure adapted from Impeccable 4.0.4 (Apache License 2.0). Manga rules and data from the mangaforge reference library (CrimSun Studio). See NOTICE.
