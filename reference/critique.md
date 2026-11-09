### Purpose

Resolve one stable target (a page range, a chapter plan, a scene, finished pages), run two independent assessments, synthesise a reader-experience critique, persist a snapshot, and ask the user what to improve next. The chat response is the primary deliverable; the snapshot is an archive and backlog for `polish`.

### Hard Invariants

- Assessment A (editorial review) and Assessment B (detector plus proof-sheet evidence) are both required.
- A and B MUST run as two isolated sub-agents whenever a sub-agent/Task tool is exposed. Running them inline is a degraded run, allowed ONLY when no sub-agent tool exists (or the user declined).
- If you degrade for any reason, the report's first line MUST be a banner: `⚠️ DEGRADED: single-context (<reason>)`. A silent degraded critique is a failed critique.
- Assessment A must finish before detector findings enter the synthesis context. Detector output is deterministic, but it still anchors judgment.
- A skipped detector is a failed critique run unless `detect.py` is missing or crashes after a real attempt, or the target is finished artwork with no plan (then B reads the pages by eye against the craft floor and says so).
- Viewable targets require looking: render the proof sheet (`proof.py --png`) or open the page images. Never critique a chapter from its JSON alone.

### Setup

1. **Resolve the target** to a concrete file: "chapter 2" → `CH02_plan.json` (or the page images folder); "the fight" → the plan plus a page range.
2. **Slug it:** `python3 .claude/skills/excelsior/scripts/critique_storage.py slug "<resolved target>"`. If this fails, skip persistence and trend, but continue the critique.
3. **Read `.excelsior/critique/ignore.md`** if it exists. Drop matching findings silently; it is the only prior-run input critique consumes.
4. **Render the evidence once:** `python3 .claude/skills/excelsior/scripts/proof.py <plan> --out .excelsior/proof/<slug>.html --png .excelsior/proof/<slug>/`. Both assessments read these PNGs.

### Assessment Orchestration

Delegate A and B to separate sub-agents. They must not see each other's output. Do not show findings to the user until synthesis. Each sub-agent receives: the target path, the PNG folder, SERIES.md and STYLE.md paths, the chapter brief path, and this file's path for its own section.

### Assessment A: Editorial Review

Read the script or beats and look at every proof page (or finished page). Think like the series' editor and its most demanding reader.

Evaluate:
- **Staging specificity:** is the page grammar, shot language and lettering grounded in this series, or could an unrelated series use these pages unchanged? Make this judgment before seeing detector output.
- **Holistic reading:** eye path, hierarchy, pacing, page turns, shot language, acting, lettering, paper and value, consistency with STYLE.md, canon.
- **Reading load:** consult [Reading Load](#reading-load) below; report pages over budget and panels with more than one new fact.
- **Emotional journey:** peak-end rule across the chapter, emotional valleys, where the reader is allowed to breathe, whether the last page hooks.
- **Manga heuristics:** consult the [Heuristics Scoring Guide](#heuristics-scoring-guide) below; score all 10 heuristics 0–4, marking any that cannot apply as `n/a`.

Return: staging-specificity verdict, heuristic scores, reading load, emotional journey, 2–3 strengths, 3–5 priority issues, persona red flags, minor observations, provocative questions.

### Assessment B: Detector + Proof Evidence

```bash
python3 .claude/skills/excelsior/scripts/detect.py --json --stats <plan(s)>
```

Exit 0 = clean; 2 = findings. Read each finding against the proof PNG for its page and mark false positives (a deliberate tease that opens a scene on an insert; a silent impact the note says is deliberate). Report the `stats` block beside the library numbers it carries (panels per page, size contrast, slant rate, shot and angle mix).

Return: counts by severity and rule, verified findings with page and panel, false positives with reasons, the stats comparison.

### Generate Combined Critique Report

Synthesise; do not concatenate. Note where the editor and the detector agree, where the detector caught what the editor missed, and where its findings are false positives. Present the full structured critique in chat.

#### Report header provenance

First line: `Method: dual-agent (A: <agent-id> · B: <agent-id>)`, or the degraded banner.

#### Reading Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Unambiguous reading order | ? | |
| 2 | Clarity of space and action | ? | |
| 3 | Hierarchy and dominance | ? | |
| 4 | Pacing and rhythm | ? | |
| 5 | Page-turn and scroll economy | ? | |
| 6 | Shot language and acting | ? | |
| 7 | Lettering integration | ? | |
| 8 | Consistency with the world | ? | |
| 9 | Economy | ? | |
| 10 | Resonance and memorability | ? | |
| **Total** | | **??/[applicable max]** | **[Rating band]** |

The applicable maximum is 4 × the heuristics actually scored. Be honest: a 4 means genuinely excellent; most real chapters score 20–32 of 40. Bands: 36–40 Exceptional · 28–35 Strong · 20–27 Workable · 12–19 Weak · 0–11 Re-stage.

#### Staging Specificity Verdict

**Start here.** Does the chapter feel staged for this series, or genre-interchangeable? Editor's unanchored assessment first; then the deterministic scan (counts, pages, false positives).

#### Overall Impression
A gut reaction: what works, what doesn't, the single biggest opportunity.

#### What's Working
2–3 specific things, with pages.

#### Priority Issues
The 3–5 most impactful problems, ordered by importance, each:
- **[P?] What** (pages)
- **Why it matters** to the reader
- **Fix** (concrete: "promote 9.3 to the bottom tier at ~40% of the page; step 9.2 down")
- **Suggested command** (from: /excelsior adapt, animate, audit, bolder, clarify, colorize, delight, distill, document, harden, layout, onboard, optimize, overdrive, polish, quieter, shape, typeset)

#### Persona Red Flags
Auto-select 2–3 personas from the [Reader Personas](#reader-personas) below (plus 1–2 from SERIES.md's readers). For each, walk the chapter and list what broke for them, with pages.

#### Minor Observations

#### Questions to Consider
Provocative questions that might unlock a better chapter ("What if the reveal on p17 waited for the turn?" "Does the talk scene need nine pages, or four and a silence?").

Be direct, be specific (page and panel), say why it matters to the reader, give concrete fixes, prioritise ruthlessly, don't soften.

### Persist the Snapshot

Write the report body (through Questions to Consider) plus metadata to a temp JSON: `{"score": n, "max": n, "na": [..], "counts": {"P0": n, "P1": n, "P2": n, "P3": n}, "issues": [{"severity", "pages", "what", "fix", "command"}], "body": "<markdown>"}`, then:

```bash
python3 .claude/skills/excelsior/scripts/critique_storage.py save "<resolved target>" <temp.json>
python3 .claude/skills/excelsior/scripts/critique_storage.py trend "<resolved target>"
```

Delete the temp file. Append one line: **Trend for `<slug>`: 24 → 28 → 32 (out of 40)**, or "First run for this target, no trend yet." Failures here never block the critique.

### Ask the User

After presenting findings, ask 2–4 targeted questions with the structured tool, each referencing specific findings: which category to tackle first (offer the top 2–3), whether a tonal mismatch was intended, how much to take on (top 3 / all / critical only), what is off-limits (published pages, approved spreads). Skip questions when the findings are one or two clear issues.

### Recommended Actions

After the answers, list commands in priority order (`/excelsior <command>`: what to fix, with pages). Only commands that address real findings; respect scope and off-limits; end with `/excelsior polish` if any fixes were recommended. Then: "You can ask me to run these one at a time, all at once, or in any order. Re-run `/excelsior critique` after fixes to see the score move."

---

## Reference Material

### Reading Load

Manga is read at speed; load is the enemy of momentum.

- **Intrinsic load** (the story itself): new characters, new rules, new places. Budget: one new named character per page, one new rule per scene, introduced in a picture before a caption.
- **Extraneous load** (bad staging): ambiguous reading order, balloons that cross the action, unclear screen direction, a wide missing so the reader cannot place anyone, a talk scene with nine faces and no room.
- **Germane load** (earned effort): a visual motif the reader learns (paper means time), a rhyme between chapters. Good load; spend it deliberately.

Checklist: words per page (talk pages ≤ ~120, action pages ≤ ~40); balloons per panel ≤ 3; new facts per panel ≤ 1; any page where the picture alone no longer tells you what happened (the skeleton test: remove all text; does the page still read?).

### Heuristics Scoring Guide

Score each 0–4: 0 broken · 1 major problems · 2 workable with clear issues · 3 good, minor issues · 4 excellent.

1. **Unambiguous reading order.** Panels and balloons read in one order in the series' direction; tier boundaries are clear; Z- or N-path never forks; nothing invites the reader to read a lower panel first. 4 = never a hesitation. 0 = readers must re-read to understand order.
2. **Clarity of space and action.** The reader knows where everyone is and what hit what; screen direction holds; each scene is placed (or deliberately withheld and then paid off). 4 = the fight could be re-blocked from the pages alone.
3. **Hierarchy and dominance.** One panel dominates each page and it is the right one; size contrast near the library's 4–5×; the heaviest beat owns the biggest frame. 0 = equal boxes everywhere or the wrong beat is biggest.
4. **Pacing and rhythm.** Density changes every page or two; silence and talk breathe; open big, close big, a lean middle; the chapter has a tempo. 0 = one density for ten pages.
5. **Page-turn and scroll economy.** Reveals land after a turn (print) or below a long gap (scroll); pages end on a question; the last page hooks. n/a for a single page.
6. **Shot language and acting.** Scale varies with intent; mediums carry talk, close-ups are spent on reactions, wides place and pull back; angles mean power and vulnerability; acting reads in posture, not only faces.
7. **Lettering integration.** Balloons placed in the lettering zones, never over faces or the action's line; voices distinct; load within budget; SFX drawn into the scene; translated or special speech marked per STYLE.md.
8. **Consistency with the world.** Paper, borders, gutters, value plan, lettering voices and character models follow STYLE.md; the series' devices recur where they should. n/a only before STYLE.md exists.
9. **Economy.** Every panel earns its place; no caption restates the picture; no beat is staged twice; no splash is spent on a non-event.
10. **Resonance and memorability.** The peak lands; the reader would describe one page an hour later; the end is felt (peak-end rule).

#### Issue Severity (P0–P3)

- **P0 Blocking:** the reader cannot follow the story (reading order breaks, a reveal is spoiled, canon is violated, a panel is missing). Fix before anything else.
- **P1 Major:** the scene works against its own intent (the hit is the smallest panel, the joke lands before the punch line, a talk scene is unreadable). Fix before inks.
- **P2 Minor:** a weaker version of the right page (flat loud page, cramped wide, long balloon). Fix in the next pass.
- **P3 Polish:** nice to fix (even splits, a slightly late establishing shot).

### Reader Personas

Walk the chapter as each selected reader and name what broke, with pages.

1. **The phone binger, "Mika":** reads at night on a phone, one thumb, fast, often a chapter a minute. Breaks on: tiny balloons, dense talk pages, two-page spreads cut in half, reading order that needs the whole page in view, reveals visible before the swipe.
2. **The first manga reader, "Dan":** new to the form. Breaks on: right-to-left order without cues, panel paths that fork, SFX they can't parse, chibi asides with no set-up, too many named characters too fast.
3. **The series veteran, "Rina":** knows every chapter. Breaks on: canon slips, model drift, a device used out of its meaning (black paper outside memory), a rhyme missed, a reveal staged weaker than its set-up.
4. **The translator-letterer, "Tomas":** has to put this into another language. Breaks on: balloons with no room for 30% text expansion, SFX baked into art with no space for a translation, puns that carry plot, text-heavy small panels.
5. **The skimmer, "Jun":** reads the pictures and glances at words. Breaks on: plot that only exists in captions, acting that only exists in dialogue, pages whose skeleton says nothing.
6. **The returning reader, "Asha":** comes back after a month off. Breaks on: no re-orientation in the first pages, a cold open with no anchor, cast reintroduced only by name.

#### Selecting Personas

| Target | Personas |
|---|---|
| Chapter one, cold open | Dan, Mika, Jun |
| Mid-series chapter | Rina, Asha, Mika |
| Action set piece | Jun, Mika, Dan |
| Talk-heavy chapter | Tomas, Mika, Jun |
| Webtoon episode | Mika, Asha, Jun |
| Localisation pass | Tomas, Dan |

#### Project-Specific Personas

When SERIES.md describes its readers, build 1–2 personas from it in the same shape: **[Role]: "[Name]"**, how and where they read, what they come for, what breaks them.
