# Init flow

`init` captures durable series truth in SERIES.md. It does not invent a visual world and does not write STYLE.md; [new-work.md](new-work.md) creates or expands one, and [document.md](document.md) records an incumbent one.

## Step 1: Load current state

Use the SERIES.md path resolved by context.py. Update it instead of creating a competing authority. In a shared universe with several series, confirm shared versus series-specific scope before writing.

- **No SERIES.md:** explore, interview, and write it.
- **SERIES.md exists:** ask what story knowledge is stale or missing; do not reopen confirmed canon without a reason.
- **Only STYLE.md exists:** leave it untouched and create SERIES.md.
- **Reboot or remaster request:** preserve confirmed canon unless the user changes it. Visual replacement happens later in new-work, not here.

Never silently overwrite an existing file or offer STYLE.md during init. If another request invoked init, finish SERIES.md and resume it.

## Step 2: Explore the project

Before asking, read enough to avoid making the user repeat known facts: scripts, beat sheets, prose drafts, production bibles, storyboards, character sheets, previous chapters, plans and any decision manifests. Note names, spellings, honorifics, languages on the page, recurring devices, the reading direction and the publication format.

Treat project evidence as a hypothesis, not user approval. Note visual maturity without documenting, extending or replacing the world.

Form a format hypothesis: `print` (tankōbon or magazine pages), `webtoon` (vertical scroll), or `both` (one story published in both, which makes `adapt` a standing job). Form a reading hypothesis: `ltr` or `rtl`.

## Step 3: Interview for story truth

Use the structured question tool when available; otherwise ask and wait. Keep rounds to at most three focused questions and require one real answer or approval round before writing a new SERIES.md. Confirm inferences.

Start with the unknowns that most change future staging decisions:

1. Who reads this, where and how (age band, platform, reading speed, familiarity with manga grammar), and what do they come back for?
2. What is the series' premise and its meaningfully different mechanism, the thing no neighbouring series does?
3. What canon, cast rules, language rules, reveal schedule and production constraints must every chapter preserve?

Confirm format and reading direction separately. Add a round only for a material gap: a canon rule that changes staging (who may appear with whom before a reveal), a language rule that changes lettering (translated speech in a marked style, a pronoun-free character), a content rating, the team's capacity (pages per week, colour or not). Record undecided facts instead of inventing them.

Do not ask for an art style, panel grammar, tone palette, fonts or reference series during init. If the user volunteers a binding visual constraint, record it under House Commitments without expanding it.

### What belongs here

- premise, mechanism, readers, genre promise, tone, the series' question;
- canon, cast and relationships, reveal schedule, what each character knows when;
- language and naming rules, rating, format, reading direction, trim, team capacity;
- confirmed house commitments (devices the user has already fixed).

### What does not belong here

- panel grammars, paper rules, line, tone, lettering design, page concepts (those go to STYLE.md);
- scene modes, chapter beats, the turn plan (chapter briefs);
- invented lore, invented backstory, invented reception or sales claims;
- a requirement to decide every optional field.

## Step 4: Write SERIES.md

Write only confirmed facts and explicitly marked open decisions. Omit irrelevant sections rather than filling them with generic prose.

```markdown
---
excelsior: 1
format: print            # print | webtoon | both
reading: ltr             # ltr | rtl
turn_reveals: even       # print only: page parity the reader sees right after a turn
trim: 7x10               # inches, or 800px for webtoon width
language: en
max_words_balloon: 25
max_words_panel: 40
---
# Series

## Premise
## Mechanism
## Readers
## Genre Promise and Tone
## Canon
## Cast
## Reveal Schedule
## Language and Naming
## Format
## Production Capacity
## House Commitments
## Open Decisions
```

The frontmatter keys are read by the detector and the planner; keep them accurate. New files go at the project root.

### Completion gate

Before loading new-work or resuming shape, verify that SERIES.md exists at the resolved path and contains the confirmed record. If it is absent, init is incomplete. Do not substitute interview notes for the file.

## Step 5: Configure the hook when useful

If the project keeps plan or beats JSON, offer `/excelsior hooks on` once (see [hooks.md](hooks.md)); never install it unasked.

## Step 6: Wrap up or resume

Summarise captured and deliberately undecided facts. Do not offer STYLE.md merely because it is missing.

Recommend the next action from the actual project state:

- Script but no staging: `/excelsior shape <chapter>`.
- Finished pages without STYLE.md: `/excelsior document`.
- Existing plans needing work: name the most relevant scoped command (`critique`, `layout`, `bolder`).

If init was invoked by another request, resume without rerunning context.py.
