> **Additional context needed**: the quality bar and what is locked (pencils, inks, lettering, published).

Polish is refinement, never concealed re-staging. Preserve the incumbent page grammar, beats, lines and everything outside scope. If the staging itself is wrong, say so and recommend `layout`, `bolder` or a redesign instead of smuggling in a replacement.

A detector result is defect evidence, not proof of quality. Look at the proof pages and read them as a reader would.

## 1. Establish the system

Read STYLE.md, the chapter brief and neighbouring chapters. If no STYLE.md exists, use the series' coherent conventions from finished pages.

Classify each drift before fixing it:

- **missing rule:** the series needs a recorded convention (how it letters whispers);
- **one-off staging:** an existing kit template or device should replace it;
- **conceptual mismatch:** the scene's mode or rhythm differs from comparable scenes;
- **local defect:** the page is simply unfinished or inconsistent.

Fix the cause at the narrowest correct level. Ask when a binding house rule cannot be inferred.

## 2. Gather the evidence

Render the proof (`proof.py --png`) and read every page in order, at reading size (phone width for webtoon). Determine what is locked, the time available, and known deliberately-unfinished pages.

If a prior critique exists, use it as one input:

```bash
python3 .claude/skills/excelsior/scripts/critique_storage.py latest "<resolved target>"
```

Incorporate relevant P0/P1 issues and name the snapshot read. Perform an independent pass either way.

## 3. Triage

Fix in this order:

1. reading-order breaks, spoiled reveals, canon slips, missing beats or lines;
2. wrong dominance on impact and reveal pages, turns that land on the wrong page, a weak last page;
3. rhythm and shot-language drift (plateaus, talking-head runs, cramped wides, unplaced scenes);
4. lettering placement and load, balloon voices, SFX integration;
5. even splits, gutter consistency, prompt hygiene.

Do not perfect one page while leaving the rest below the same bar.

## 4. Polish the whole chapter

### Flow and hierarchy
- Every page's eye path enters top-outside and exits at the turn corner; nothing pulls the eye backwards.
- The dominant panel is the right one; promote with `inspire_page.py PLAN --page N --enforce-peak --apply i`.

### Layout and rhythm
- Splits 60/40; middle tiers squeezed; tier gutters wider than row gutters; density changes every page or two.

### Shots and acting
- Scenes placed; talking-head runs broken by a two-shot; wides in big frames; the last panel of a page pulls back more often than not.

### Lettering
- Balloons in the lettering zones, tails to mouths, no balloon over a face or the action line; voices per STYLE.md; SFX drawn into the scene.

### Paper, value, continuity
- Paper meanings consistent; value balance per page deliberate; props and costumes continuous across cuts; panel prompts share the style line.

## 5. Verify and finish

Re-run the detector and the proof once. Two rounds is the ceiling. Report what changed (pages), what is left open and why, and the detector score before and after.
