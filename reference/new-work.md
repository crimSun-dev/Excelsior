# New staging work

Use this flow when staging a new chapter, arc or series, or replacing a series' visual world. SERIES.md owns story truth. STYLE.md owns durable visual decisions. A chapter brief (`.excelsior/briefs/<chapter>.md`) keeps strategy that belongs only to one chapter or scene. Complete [init.md](init.md) first when SERIES.md is missing; a missing STYLE.md does not route back to init.

## 1. Decide what is already true

Read STYLE.md, the script or beats, existing pages, plans, model sheets and storyboards.

- **Redesign:** preserve story, dialogue, canon, cast and explicit house commitments; replace the old staging world rather than polishing it. The old look is evidence of what the series is, not authority over what it becomes.
- **Established world:** inherit it. A missing STYLE.md does not erase a coherent page grammar already present in finished chapters; document that grammar instead of inventing a replacement.
- **Incomplete world:** preserve confirmed devices (paper rules, balloon voices, border language) and recognisable traits, then help the user expand the system for this new chapter.
- **No visual authority:** create a new world with the user.

A scene, page or panel inside an established chapter inherits that chapter. Do not turn a local addition into a new identity exercise.

## 2. Ask what will change the work

Ask one round of two or three related questions through the structured question tool when available. Skip settled facts; a precise request may need only a compact confirmation.

- **Hook:** what must the reader be dying to know at the turn, and what is the one image the chapter is remembered by?
- **Follow:** what is the geography, who moves where, and what is the decisive blow or play?
- **Converse:** whose face carries the scene, what is unsaid, where is the laugh or the sting?
- **Immerse:** what does the place or the memory feel like, and how long should the reader stay in it?

Across modes, ask what success looks like for the reader, what must remain untouched (canon, lines, reveals), and what would make a polished chapter feel wrong. Do not ask for panel counts, gutter widths or canned art-style lanes.

## 3. Choose the right amount of invention

### Extend an existing chapter

Inherit its world and page grammar. Resolve only the new beats, page budget, shot language, lettering and how the addition joins the surrounding pages (density, paper, the turn before and after). Do not run a concept roll or change STYLE.md unless the user approves a durable system change.

### Stage a whole chapter or scene inside an established world

Keep the visual system fixed. Derive five to seven materially different stagings from the beats, the mode and the reader (where the turns fall, which beat owns the splash, how the camera travels, what the scene's one device is), ordered by resonance. For a genuinely open chapter or scene, run:

`python3 .claude/skills/excelsior/scripts/concept_seed.py --scope scene --mode <mode>`

The script assigns which staging gets built; your top-ranked staging is what every run would ship, so the dice come from outside. Never run it for a local fix or a precisely specified page; stage those directly.

### Create or replace the visual world

1. Name the series' unique mechanism in one sentence (what this story does that no neighbouring series does), the reader's real scene (where and how they read: a phone on a train at night, a tankōbon on a bedroom floor), its cultural home, and what this first chapter must prove. Note the page this genre always ships (the shōnen fight grid, the romance flower-flow, the isekai status window, the webtoon close-up cascade) and its predictable opposite; name both as the rut and keep them out of the seven-candidate list. A brief that paints its own picture (a title, a governing metaphor, a named device) adds its literal reading to the rut: spend at most one candidate on it and derive the rest from elsewhere in the reader's world.
2. From that world, list seven concrete visual systems, artifacts, places or rituals the reader knows by heart, each with one line on why it resonates and can carry the mechanism, ordered by resonance. The reader's world includes its graphic and screen traditions, not only its objects: broadcast graphics, match programmes, school notebooks, transit signage, game HUDs, film grammar, devotional prints, the reading traditions of manga itself. What would this story look like as a physical object; what did its world look like before comics? Near-duplicates count once. When more than three of the seven share one family, the derivation stopped at the most obvious artifact; dig until the list spans at least three families.
3. Turn that material into complete directions: each joins a reusable visual world (paper, line, tone, borders, gutters, lettering voices, the series' signature device) to a concrete first-chapter experience (the opening page, the first turn, the last page).
4. Run `python3 .claude/skills/excelsior/scripts/concept_seed.py --scope direction --mode <mode>` and follow what it prints. This step has no substitute and no skip condition: on a new or replacement world, planning pages before this script has run and its assignment is acknowledged is a contract violation, because the roll is the mechanism that keeps every run from converging on the genre default. The script assigns which direction gets built and deals catalog challengers: page grammars from the measured reference library (with real numbers) and a few labelled unmeasured traditions. Fuse each challenger before judging it: the challenger supplies the page grammar, the series supplies every fact, character and canon rule, and clarity wins conflicts. Weigh fused challengers against the assigned direction on exactly two axes, reader identification and story clarity; losing to strong grounded material is a valid outcome.
5. Present one direction, fully committed: its world, first page, reader path, signature device, how it reaches across the series, and the honest risk. Alongside it, offer the hand's challengers as named alternates, each with its one-line case (an honest "fuses poorly because X" included); the weighing informs the user's choice, it never pre-empts it. Add re-roll with an optional one-line steer. Never present a ranked menu of your own grounded candidates; a lineup invites the safest card. Use the structured question tool: assigned direction first, challengers next, re-roll, and the standing exit last. Run with `--schema` for the card anatomy.

The standing exit: every direction round offers one quiet, permanent alternative, the genre standard played straight. It is the user's door, never yours: never recommend it, never weigh it against the roll, never let it soften the dealt directions. When the user takes it, convention becomes the commitment: ask once for two or three series this should sit beside, make their craft level the bar, and execute the standard at full fidelity, without irony or smuggled quirk. A standing preference is recorded as a house commitment in SERIES.md. Re-roll (`--exclude` the shown ranks and challenger ids) eliminates every direction already shown; after two consecutive re-rolls, ask what quality is missing. You may re-roll on your own only on named factual grounds, when the assigned direction cannot carry the story's truth; taste is never grounds. A user- or brief-pinned direction beats the roll, always.

Every direction the roll can land on must already be viable: true to canon, a real page grammar and lettering system, a distinctive chapter-one experience, drawable by the team in the available time. A candidate that fails on truth is replaced before the roll, never rescued by it.

For **Hook**, the opening must make the premise intelligible and desirable within three pages, and the first turn must pay. For **Follow**, expression may never obscure who is where and what hit what. For **Converse**, the faces and the reading order stay legible. For **Immerse**, the image leads from the first page.

## 4. Commit the world

Pick a value strategy before picking tones: **Paper-light** (white pages, black spotted for weight; the default for Converse-heavy series), **Spot-black** (heavy blacks carry 20–30% of the page and define silhouettes), **Tone-led** (screentone fields carry mood and time), or **Paper-is-story** (the paper itself changes colour or value to mean time, memory or place, and the reader learns the code). Colour pages and webtoons pick the colour equivalent: Restrained, Committed (one hue carries 30–60%), Full palette (3–4 named roles), Drenched. Commit at page scale: fields that own whole pages, not accents sprinkled over grey.

Lettering is cast like a character: choose balloon shapes, borders, tails and faces from the series' world, per voice. A typed comic font on every balloon and SFX means you stopped looking.

Calibration: AI-planned manga clusters around a few looks regardless of story: the equal-box storyboard grid with a close-up in every box; the "cinematic" webtoon cascade of full-width faces separated by identical gaps; the everything-bleeds, everything-tilts action page. All are legitimate when the brief calls for them. Where the brief leaves staging free, landing in one means the self-check failed: if someone could guess your page from the genre alone, rework until they can't.

## 5. Record the decision

Before planning pages, state the chosen direction as a contract at the top of the chapter brief, five short blocks, 150 words at most. THESIS: the one idea this chapter's staging owns and the genre-default arrangement it refuses. OWN-WORLD: paper, line, tone, borders, gutters and lettering voices, specific enough to recognise with every word and face removed. STORY: what the reader understands, feels and wants by the last page. FIRST PAGE: the exact composition, what is where and at what scale, and what the first turn reveals. FORM: the chosen form, its position on your ordered list, and the seed key the script printed. Close with one more line, FINISH: "unreviewed and undocumented is unfinished; this chapter ends with the finish review, the verdict, and STYLE.md". A plan that looks complete with the FINISH line undischarged is not done.

On a new or replacement world, STYLE.md is written at finish, from the planned chapter, by the documenter pass (section 7); a rulebook written before staging gets defended against reality instead of describing it. An ordinary extension does not rewrite STYLE.md.

Write or update the chapter brief at `.excelsior/briefs/<chapter>.md`: scope and the mode per scene; reader, job, the turn and the hook; chosen direction and the memorable page; unresolved decisions. Do not copy SERIES.md or STYLE.md into it.

Whenever image generation is available, the locked direction is visualised before it is planned at full length: load [visualize.md](visualize.md) and follow it, three thumbnail options for the first spread rendered and put before the user.

For `shape`, return the selected direction to [shape.md](shape.md) and stop before persistence or planning.

## 6. Stage with full commitment

1. **Beats.** Turn the script into beats JSON (format in `scripts/plan_chapter.py --help`): one entry per page with energy (0–10), beat (calm, build, impact, reveal, pause, dread), scene, paper, and per panel a size, shot (EWS WS FS MS MCU CU ECU INS), angle, art note, subject placement and lettering. The page budget comes from shape; the turns come from the brief.
2. **Plan.** `python3 .claude/skills/excelsior/scripts/plan_chapter.py BEATS.json --out <CH>_plan.json` borrows real reference geometry for every multi-panel page and writes one image prompt per panel.
3. **Commit every atom.** Every page owns a decision: its dominant panel, its density relative to its neighbours, its camera path, where the eye enters and exits, what crosses a border. Use the library's techniques by name where they fit (tease small/reveal huge; push in band by band; quick cuts then one big swing; jump scale; empty space as suspense; take the frame away; repeat then break; slivers as a pan or a trap; things cross borders; comedy on a strict grid; black paper for memory; chapter-end hook = big image plus small wrong detail).

- **The first page is a thesis, not a title card.** Demonstrate the series' mechanism on page one at the scale the story needs; do not trap it behind a recap or a logo page. The memory test: if a reader stopped after one page, what would they describe an hour later?
- **Prove the opening spread before staging past it.** Plan pages 1–4, render the proof, and check them against the contract before the rest; every later page inherits their shortfall.
- **Prove, don't tell.** Show the character doing the thing; captions that restate the picture add words, not story.
- **Author the reference material.** Thumbnails, model-sheet notes, background references and panel prompts are design material; author them at production fidelity and label anything synthetic.
- **Pace the chapter like an editor.** Vary density, scale, paper and silence inside one grammar; a dense page earns a quiet one; the chapter ends on a real hook.
- **Author motion as staging.** The scene's motion lives in cuts, slants, frame-breaks and the camera's path, once, orchestrated, not speed lines on every panel.

Preserve canon, dialogue, reading direction, format specs and the team's production constraints.

## 7. Inspect and finish

Inspect in one batched round: `python3 .claude/skills/excelsior/scripts/proof.py <plan> --out proof.html --png .excelsior/proof/` plus `detect.py --json <plan>`. Critique the proof against the request and the direction contract, fix material gaps in one batch (re-plan pages with `inspire_page.py --enforce-peak --apply`, re-stage shots, re-letter), and confirm with one final round; two rounds is the ceiling.

Then spawn a fresh finish reviewer (a subagent with no forked history) with: the original request, confirmed answers, the plan path, the proof PNG paths, the direction contract, the detector findings, the craft-floor path and [degraded/finish-reviewer.md](degraded/finish-reviewer.md) as its instructions. It has no conversation context; everything it needs travels in that packet. Without a subagent tool, run that file's pass in-thread after stepping fully out of the staging context, and disclose the substitution in one line. Apply its material fixes in one batch, re-proof, and send the result back for a verdict scoring every material fix resolved, partial or unresolved. Two rounds is the budget an unattended run ends at; an attended session's ceiling belongs to the user. Report the final verdict table as it stands, open items included, under the reviewer's own disposition word.

Then run the documenter pass ([degraded/documenter.md](degraded/documenter.md), as a subagent when available) with the project root, the plan, the direction contract and SERIES.md; it writes STYLE.md from the planned chapter, ground truth over intention. A clean detector pass is not finished; finished is the contract kept, the review closed and the world recorded.
