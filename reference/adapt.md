Adapt translates a chapter between formats and reading directions without losing its beats: print page ↔ vertical scroll ↔ phone-sized page; right-to-left ↔ left-to-right.

## Print → webtoon (scroll)

- Every page becomes a sequence of blocks; panels re-stack top to bottom in reading order. Wide panels stay wide; tall slivers become tall blocks; side-by-side pairs either stack or become one wide block.
- **The gap is the clock:** about 0.05× width for action, 0.18× normal, 0.4–0.6× a held breath (Link Click strip medians). A page turn becomes the longest gap; a reveal sits below it.
- Re-letter for the width: balloons can't straddle tiers that no longer touch; move them into the block they belong to.
- Spreads become a tall block or a slow pan; nothing vital where the platform slices.
- `mangaforge.layout.make_scroll` (via `plan_chapter.py` with a webtoon SERIES.md) builds a first scroll pass; then stage it by hand.

## Webtoon → print

- Group blocks into pages by beat; a long gap is a candidate page turn. Rebuild dominance (scroll often has no size contrast; print needs it). Run `inspire_page.py` per page.
- Consolidate tall establishing blocks into the top tier of a page or a splash.

## Phone-sized page

Fewer panels per page (2–3), bigger lettering, no fine detail carrying plot, reveals one swipe away.

## Right-to-left ↔ left-to-right

- Mirror panel geometry (the planner mirrors references automatically); re-check every tier's read order.
- Do not mirror what must not mirror (text, clocks, handedness, logos, asymmetrical costumes): mark those panels for redraw (see [harden.md](harden.md)).
- Re-check turn parity: which page the reader sees after a turn depends on which side page one sits.

## Verify

Detector on the new plan; proof read in the new format at its real size; a beat-by-beat checklist showing nothing was dropped.
