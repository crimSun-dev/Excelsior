Layout turns story priority into reading order, dominance, rhythm and breath. Diagnose the structural problem before moving panels.

---

## Reader mode

- **Hook + Immerse:** composition may be asymmetric, borderless or intentionally disruptive when the beat earns it; the reveal owns the page.
- **Follow:** geometry carries speed and direction: slants that zig-zag, slivers, quick cuts then one big swing; the eye path must still never fork.
- **Converse:** predictable structure is an affordance: rectangular tiers, medium shots, a talk tier with room for balloons; comedy on a strict grid with the punch in the last tier.

Preserve the established world. A layout command changes structure inside it; identity replacement belongs to [new-work.md](new-work.md).

## Two isolated assessments

When a sub-agent tool is available, run these independently; otherwise run them yourself in this order.

1. **Layout assessment** on the proof PNGs (or finished pages), answering every question with evidence:
   - **Reading order:** squint at the page. With detail blurred, can you identify the dominant panel, the entry and the exit, in order? Does any tier boundary fork the eye?
   - **Dominance:** is there one dominant panel, and is it the beat that matters most?
   - **Rhythm:** tight and generous tiers in a deliberate cadence, or one tier height repeated? Splits 60/40 or 50/50?
   - **Structure:** does the page's topology match the beat (stacked bands for a push-in, full-height slivers for a standoff, a grid for comedy)?
   - **Density:** panels per page against the mode and the neighbouring pages.
   - **Shots in frames:** wides in big frames, inserts small, close-ups where reactions are.
   - **Extremes:** the talkiest page, the busiest fight page, the quietest page; what breaks?
2. **Mechanical scan:** `python3 .claude/skills/excelsior/scripts/detect.py --json <plan>` and keep the craft and shot families. Keep this out of the first assessment, then synthesise. A clean scan cannot prove rhythm.

## Set the spatial thesis

Before editing, name for each target page: the eye path, the dominant beat, what groups and what separates, the density relative to the neighbours, the one technique the page uses (by its library name).

## Apply

- **Borrow real geometry.** `python3 .claude/skills/excelsior/scripts/inspire_page.py PLAN --page N --k 3 [--enforce-peak] [--series DB,HNK]` returns three reference-inspired variants (panel shapes only, adapted and mirrored for your reading direction). Choose by the thesis, not the score; `--apply i` swaps it in and rebuilds the panel prompts.
- **Dominance:** biggest about 4–5× the smallest; the heaviest beat owns it.
- **Tiers:** squeeze the middle tier into a breath strip; end heavy on hook and impact pages; tier gutters wider than row gutters.
- **Density:** change every page or two; no plateau longer than about five pages.
- **Techniques:** jump scale; push in band by band; slivers as pan or trap; insets as seasoning (rare); the frame taken away once per scene; repeat, then break.
- **Shots:** restage shot sizes and angles in the beats where the new geometry changes what a frame can hold (a panel that grew can take the wide; a panel that shrank becomes the insert).

## Verify

One proof render and one detector run; compare before and after for the target pages (size contrast, findings cleared). Read the pages in order once at reading size. Two rounds is the ceiling.

## Live-mode parameters

When called from `live`, the variant knobs are: `--k`, `--seed`, `--series`, `--enforce-peak`, and the beat's own `energy`, `beat` and panel sizes.
