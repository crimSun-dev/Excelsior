# Extract

Pull what the series repeats into a reusable kit, so chapters stop re-inventing it and drifting. The kit lives in `.excelsior/kit/` and is referenced from STYLE.md.

## Find the repeats

- **Page templates:** layouts the series reuses (the talk page, the chapter-end page, the flashback page). Pull their geometry from the plans (`pages[].layout`) into `kit/templates.json` with a name, the beat they serve and the page they came from.
- **Motifs:** recurring images, framings and rhymes (a hairline across black paper that opens and closes the book; the same doorway shot at every return). Record each with its meaning and every page it appears on.
- **Lettering voices:** balloon and caption styles per speaker or device. Record shape, border, tail, face, size and an example line.
- **Shot habits:** how this series establishes, how it frames its lead in talk, how it frames the antagonist's entrance.
- **Prompt fragments:** the style line and per-character prompt fragments the panel prompts reuse, so generated reference art stays on-model.

## Consolidate

Where the same device appears in slightly different forms, propose one canonical version and list the variants it replaces; ask before merging variants the user may have meant. Never extract from one occurrence: a pattern needs at least three.

## Wire it in

Add a "Kit" section to STYLE.md naming each entry and its file. Plans can reuse a template by name in the beats (`"template": "talk-page"`); `inspire_page.py` remains the source for pages that should not repeat.

## Before you finish

- Every kit entry cites the pages it came from.
- Nothing in the kit contradicts STYLE.md; where it does, STYLE.md is updated with the user's approval or the entry is dropped.
- No story content (lines, events) went into the kit.
