Live is variant mode: pick a page, get reference-inspired alternatives, compare them side by side, swap one in. It is fast iteration inside an established chapter, not a new world.

## First-time setup

- Live needs a planned chapter (`*_plan.json`) and numpy for the reference pool.
- The Manga Designer (`vendor/mangaforge/designer/index.html`, also publishable as an artifact) is the visual surface: it shows a page, its reference-inspired variants and the proof geometry.
- Optional server: `python3 -m mangaforge.server` (from `vendor/`, needs fastapi and uvicorn) exposes `/api/inspire` and `/api/relayout` and MCP tools `inspire_layouts` and `use_reference_layout` for harnesses that drive the designer live.

## The loop

1. The user names a page (or picks one in the designer) and an action: `layout` (new geometry), `bolder`, `quieter`, `peak` (enforce the heaviest beat as the biggest panel).
2. Run `python3 .claude/skills/excelsior/scripts/inspire_page.py PLAN --page N --k 3 [--enforce-peak] [--seed S] [--series …]`.
3. Render the variants beside the current page (`proof.py` on a temp plan per variant, or the designer) and say in one line what each does differently (which reference page inspired it, its dominance, its tiers).
4. The user picks; `--apply i` swaps it in (a `.bak` is kept). Re-run the detector on that page only.
5. Re-roll with a new `--seed` on request; after two re-rolls with no pick, ask what quality is missing.

## Rules

- Variants change geometry only; beats, lines and canon stay.
- Every variant names the real page that inspired it; reference artwork is never copied, only panel shapes.
- Never apply without the user's pick in an attended session.
