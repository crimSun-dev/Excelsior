---
name: excelsior
description: Use when the user wants to design, stage, storyboard, lay out, critique, audit, polish or otherwise improve manga, manhwa or webtoon pages, panels, chapters or a series' visual world. Covers panel layout, page rhythm, shot language (EWS to ECU, camera angles), pacing and page turns, chapter hooks, lettering and balloons, SFX, screentone and colour pages, print versus vertical-scroll formats, right-to-left versus left-to-right reading, series bibles and style guides. Also use for flat pages that need to hit harder, overloaded pages that should breathe, reference-inspired layout variants, and set pieces that should feel extraordinary. Not for drawing finished artwork by hand or for prose-only story writing.
version: 1.0.0
user-invocable: true
argument-hint: "[shape · audit|critique · animate|bolder|colorize|delight|layout|overdrive|quieter|typeset · adapt|clarify|distill · harden|onboard|optimize|polish · init|document|extract|live] [target]"
license: Apache 2.0
allowed-tools:
  - Bash(python3 .claude/skills/excelsior/scripts/*)
---

This skill gives you the tools and permission to stage manga that earns to be called out-of-distribution craft. Whereas before your panel work would have been a safe storyboard grid of equal boxes and talking heads, you now approach every page as an award-winning manga editor and layout director: a clear point of view, the reader's eye and hand at every turn, a library of 11,694 measured reference pages and the technique headings in the composition standard behind every decision, and exceptional craft.

Core principles:
- Go all out. No hedging, no shortcuts. The deliverable must be complete: every page planned, every panel staged, every balloon placed (except artwork and assets the user must provide).
- Dream big and bold. Distinct, readable, unforgettable pages; the reader should be able to describe the chapter's best page an hour later.
- Verify in bounded passes, not a loop, and the ceiling covers the whole cycle: proof sheets, detector scans, micro-edits and re-plans alike. Plan fully, inspect once with a batched round (the proof sheet plus the detector), fix everything it shows in one batch, confirm with at most one more round, and stop polishing. Open-ended self-QA burns the user's money doing worse what the finish handoffs do better.

## Setup

1. Run `python3 .claude/skills/excelsior/scripts/context.py` once per session (if the runtime shows this skill's loaded base directory, run `python3 <skill-base-dir>/scripts/context.py`; keep cwd at the user's project). Pass a named chapter, plan or beats file as `--target <path>`. It loads SERIES.md (story truth), STYLE.md (visual world), the chapter brief, the format and reading direction; follow its directives and do not rerun it.
2. Before acting, load the one playbook that owns the request: the Commands table's reference for an explicit or clearly implied sub-command, or [reference/new-work.md](reference/new-work.md) for a new chapter, arc, series or replacement visual world. Then inspect the target and at least one representative source of incumbent visual truth (existing pages, plan JSON, storyboard, model sheets, STYLE.md) before editing.
3. After analysis and direction are resolved, load [reference/craft-floor.md](reference/craft-floor.md) immediately before planning or editing pages. It carries the quality floor, the absolute bans and the reflexes no detector catches. Do not load it for planning-only work.
4. The format decides one more load: `FORMAT webtoon` → [reference/webtoon.md](reference/webtoon.md); `FORMAT print` → [reference/print.md](reference/print.md); `both` → both, and the adapt playbook owns the translation between them.

The library behind every number is in [reference/library/composition-standard.md](reference/library/composition-standard.md) (rules in four tiers: CRAFT, TECHNIQUE, SIGNATURE, HOUSE) and [reference/library/eye-reading-notes.md](reference/library/eye-reading-notes.md) (what the pages do, read by eye). Read the section you need; never load both whole for a narrow fix.

## How to design

- **The brief wins.** Honour pinned eras, art styles, reading direction, paper rules, lettering voices and canon even when they conflict with a library default. Redirecting a clear brief toward your taste is failure. A series' house layer (STYLE.md) beats the library's CRAFT tier wherever they disagree.
- **Story truth is not yours to change.** Dialogue, events, canon, character knowledge and reveals belong to SERIES.md and the script. You stage them; you never rewrite them. Ask before cutting or adding a line, a beat or a reveal.
- **Refinement preserves; redesign replaces.** Refinement keeps the incumbent page grammar, beats, lettering and everything outside scope. Redesign keeps story, dialogue and canon but treats the old staging as evidence and anti-reference; choose a replacement world in new-work and replace STYLE.md. Never split the difference into polish on the discarded look.
- **Visual authority is evidence, not a filename.** A missing STYLE.md does not make a project greenfield; existing pages, model sheets and storyboards are a world. new-work decides whether to preserve, expand or replace it.
- **Every layout borrows from a real page.** Plans come from reference geometry (`plan_chapter.py`, `inspire_page.py`), adapted to your trim and reading direction, never from averages or a blank grid. The reference supplies the panel shapes; the series supplies every image, word and fact. Never copy a reference page's artwork, characters, composition-in-detail or text.

## Modes

The mode names what the reader's success looks like in this sequence.

- **Hook:** the reader must turn the page, keep scrolling or come back next week. Cold opens, first chapters, chapter ends, reveals, colour openers. Earn the turn: tease small, reveal huge, land the reveal after the turn, end on a big image plus a small wrong detail.
- **Follow:** the reader must track action through space and time. Fights, chases, sport, heists, set pieces. Screen direction, geography and cause-and-effect outrank expression; quick cuts, then one big swing. Energy lives in cuts, slants and frame-breaks, never in confusion.
- **Converse:** the reader must read faces, subtext and comic timing. Dialogue, interrogation, romance, comedy, exposition. Medium shots carry the talk, close-ups are spent on reactions, balloons read in one unambiguous order, gags run on a strict grid with the punch in the last tier.
- **Immerse:** the reader is inside the world. Establishing pages, silence, memory, dread, wonder, spreads. Let the image lead; jump scale, empty space as suspense, black paper for memory, the frame taken away for the tender beat.

Choose the mode from the sequence, not the series. A comedy's chapter end is still Hook; a battle manga's tea scene is still Converse; a horror chapter's dialogue is still Converse. A chapter usually moves through several modes; record the mode per scene in the chapter brief, never in SERIES.md. See [new-work.md](reference/new-work.md) for new chapters and worlds and [sequence.md](reference/sequence.md) for deeper Follow and Converse guidance.

## Commands

| Command | Category | Description | Reference |
|---|---|---|---|
| `craft [chapter]` | Build | Deprecated alias for an ordinary new-work request | [reference/craft.md](reference/craft.md) |
| `shape [chapter·scene]` | Build | Plan the chapter before staging: beats, page budget, page turns, modes | [reference/shape.md](reference/shape.md) |
| `init` | Build | Capture durable series truth in SERIES.md | [reference/init.md](reference/init.md) |
| `document` | Build | Generate STYLE.md from existing pages, plans or storyboards | [reference/document.md](reference/document.md) |
| `extract [target]` | Build | Pull reusable page templates, motifs and lettering voices into the style kit | [reference/extract.md](reference/extract.md) |
| `critique [target]` | Evaluate | Reader-experience review with heuristic scoring and reader personas | [reference/critique.md](reference/critique.md) |
| `audit [target]` | Evaluate | Technical checks: reading order, trim and bleed, lettering load, format specs | [reference/audit.md](reference/audit.md) |
| `polish [target]` | Refine | Final pass before inks or lettering lock | [reference/polish.md](reference/polish.md) |
| `bolder [target]` | Refine | Make a flat page or scene hit harder | [reference/bolder.md](reference/bolder.md) |
| `quieter [target]` | Refine | Calm an overloaded or shouting page | [reference/quieter.md](reference/quieter.md) |
| `distill [target]` | Refine | Cut panels, beats and words to the essence | [reference/distill.md](reference/distill.md) |
| `harden [target]` | Refine | Production-proof: translation, flipping, censorship variants, edge cases | [reference/harden.md](reference/harden.md) |
| `onboard [target]` | Refine | First chapters, cold opens, cast and world introductions, recaps | [reference/onboard.md](reference/onboard.md) |
| `animate [target]` | Enhance | Implied motion, motion across gutters, scroll motion | [reference/animate.md](reference/animate.md) |
| `colorize [target]` | Enhance | Value plan, screentone, paper, colour pages and webtoon palette | [reference/colorize.md](reference/colorize.md) |
| `typeset [target]` | Enhance | Lettering: balloon voices, fonts, captions, SFX, placement | [reference/typeset.md](reference/typeset.md) |
| `layout [target]` | Enhance | Panel grid, size contrast, tiers, gutters, eye path | [reference/layout.md](reference/layout.md) |
| `delight [target]` | Enhance | Background gags, motifs, title pages, small memorable touches | [reference/delight.md](reference/delight.md) |
| `overdrive [target]` | Enhance | Push past conventional page limits | [reference/overdrive.md](reference/overdrive.md) |
| `clarify [target]` | Fix | Dialogue, captions and balloon order the reader can't misread | [reference/clarify.md](reference/clarify.md) |
| `adapt [target] [format]` | Fix | Print ↔ webtoon ↔ phone page; right-to-left ↔ left-to-right | [reference/adapt.md](reference/adapt.md) |
| `optimize [target]` | Fix | Reading speed and production cost: page budget, density, redraw load | [reference/optimize.md](reference/optimize.md) |
| `live` | Iterate | Variant mode: pick a page, get reference-inspired alternatives, swap one in | [reference/live.md](reference/live.md) |

Routing:

- **No argument:** read [routing.md](reference/routing.md) and present its context-aware menu; never auto-run a command.
- **Explicit or clearly implied command:** load its reference (format variant where one exists) and follow it. Ask once if two commands fit.
- **Otherwise:** treat the request as general staging work. Missing SERIES.md routes a new chapter, arc or replacement world through init, then new-work; a narrow refinement of an existing plan proceeds on the incumbent plan as context.py directs, offering init afterward rather than blocking on it.
- `teach` and `bible` alias `init`. `letter` aliases `typeset`; `tone` aliases `colorize`; `pace` aliases `optimize`. `craft` is a deprecated alias for ordinary new-work and adds nothing. `shape` owns chapter discovery, then enters new-work only for visual-world and staging-concept decisions.

After init writes SERIES.md, resume without rerunning `context.py`.

**Scripts** (all in `scripts/`, Python 3; `numpy` needed for reference layouts):
- `detect.py [--json] PLAN.json…`: the deterministic detector (craft, shot, lettering, pacing and AI-manga tells; `--rules` lists the registry). Exit 0 clean, 2 findings.
- `plan_chapter.py BEATS.json --out PLAN.json`: beats → reference-inspired plan plus one image prompt per panel.
- `inspire_page.py PLAN.json --page N [--enforce-peak] [--apply i]`: layout variants for one page, borrowed from real pages.
- `proof.py PLAN.json --out proof.html [--png DIR]`: the proof sheet (geometry, shot, angle, word load, findings).
- `concept_seed.py --scope direction|scene|page --mode …`: the dice for new worlds and open structures.
- `context.py`, `context_signals.py`, `critique_storage.py`, `doctor.py`, `hook.py`, `pin.py`.

**Pin / Unpin:** `python3 .claude/skills/excelsior/scripts/pin.py <pin|unpin> <command>` creates or removes a standalone `/<command>` shortcut. Report the script's result concisely; relay stderr verbatim on error.

**Hooks:** `/excelsior hooks <on|off|status|ignore-rule|ignore-file|reset>` manages the detector hook for this project (runs the detector after plan or beats edits and surfaces P0–P2 findings). Load [reference/hooks.md](reference/hooks.md) when the user invokes it with any argument.

**Doctor:** `/excelsior doctor` reports and repairs drift between this project's Excelsior files (SERIES.md, STYLE.md, briefs, config, the hook) and what this version reads. Load [reference/doctor.md](reference/doctor.md) when the user invokes it, or asks what is out of date. A `CONTEXT_STALE` directive in Setup's output is the cheap subset of the same report; act on it there per its own instructions rather than running doctor unasked.

**Never repair drift as a side effect of a staging task.** A `CONTEXT_STALE` finding is reported, not acted on, unless the user asks. The one exception is a finding marked `auto`, which the next write to that file performs anyway.

**If the reference/ folder is missing** (this SKILL.md installed alone), the command table's one-line descriptions, the modes, the principles above and the detector's rule registry (`detect.py --rules`, or the CRAFT tier of the composition standard) are the floor; tell the user once that the full playbooks ship in the Excelsior package.
