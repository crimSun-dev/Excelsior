Run systematic **technical** checks on a chapter and generate a scored report. Don't fix issues; document them for other commands to address.

This is a production audit, not an editorial critique. Check what is measurable and verifiable in the plan, the pages and the files.

## Diagnostic Scan

Run `python3 .claude/skills/excelsior/scripts/detect.py --json --stats <plans>` once, render the proof (`proof.py --png`), then check five dimensions. Score each 0–4.

### 1. Readability

**Check for**:
- **Reading order:** tier boundaries that fork the eye; panels whose top edges align across a row so the reader can't tell rows from columns; balloons that read out of order; right-to-left pages with left-to-right cues (or the reverse).
- **Lettering size at reading size:** body lettering at least about 7–8 pt on a printed B6/A5 page; on a phone, balloon text at the platform's display width must stay legible without zoom (webtoon: about 800 px wide, lettering x-height around 14–16 px).
- **Contrast:** lettering on tone or colour readable (dark text on light balloon; tinted balloons keep ≥4.5:1); SFX legible against the art.
- **Load:** detector `letter-*` findings; words per page against the critique's reading-load budget.

**Score 0–4**: 0 = readers lose the order regularly · 1 = frequent ambiguity or illegible text · 2 = workable with rough pages · 3 = good, isolated issues · 4 = never a hesitation.

### 2. Print and file specs

**Check for** (print): trim, bleed (usually 3 mm / 0.125 in) and safe area respected; no balloon or face inside the trim-to-safe band; spreads with nothing vital in the gutter (binding loss); page count matching the signature (multiples of 4/8/16 when the printer requires it); resolution (line art 600–1200 dpi, tone 600 dpi, colour 300–350 dpi); screentone frequency that won't moiré at print size.
**Check for** (webtoon): canvas width (commonly 800 px), slice height limits per platform, file size limits, no vital art across a slice seam, gaps that survive the platform's own margins.

**Score 0–4**: 0 = files would be rejected · 4 = press- and platform-ready.

### 3. Format and direction

**Check for**: the plan's `reading` matches SERIES.md; mirrored references kept their mirrored panel shapes; flipped editions don't mirror text, watches, handedness and asymmetrical costumes or logos without a decision; reveal parity matches the edition's first-page side; the print edition and the scroll edition carry the same beats (`adapt` owns differences).

**Score 0–4**.

### 4. Consistency

**Check for**: STYLE.md drift (paper meanings, border weights, gutter widths, balloon voices, SFX hand); character model and costume continuity between pages; prop continuity (what is in whose hand); naming and spelling against SERIES.md; panel prompts carrying the same style line and character fragments.

**Score 0–4**.

### 5. Staging integrity (CRITICAL)

Run the detector and verify each finding against the proof. Look for repeated shortcuts (the storyboard grid, the face parade, splash inflation), drift from the series' own grammar, and pages interchangeable with an unrelated series. Keep deterministic findings separate from visual judgment; call out false positives.

**Score 0–4**: 0 = systemic · 1 = major repeated failures · 2 = several verified issues · 3 = minor isolated · 4 = coherent and intentional.

## Generate Report

### Audit Health Score

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Readability | ? | |
| 2 | Print and file specs | ? | |
| 3 | Format and direction | ? | |
| 4 | Consistency | ? | |
| 5 | Staging integrity | ? | |
| **Total** | | **??/20** | **[Rating band]** |

Bands: 18–20 Excellent · 14–17 Good · 10–13 Acceptable · 6–9 Poor · 0–5 Critical. Report the detector's own 0–100 score beside it (it normalises penalties per 20 pages).

### Staging Integrity Verdict
**Start here.** Pass/fail: does the chapter express a coherent, series-specific page grammar? Cite verified evidence and detector findings.

### Executive Summary
Score, counts by severity, top 3–5 issues, next steps.

### Detailed Findings by Severity
For each: **[P?] Issue** · Location (page, panel, file) · Dimension · Impact on the reader or the printer · Standard (library rule, platform spec, STYLE.md line) · Recommendation · Suggested command.

### Patterns & Systemic Issues
("Every impact page from 9 to 63 hands its biggest frame to the setup, not the hit: the layout pass ignored beat weight.")

### Positive Findings

## Recommended Actions

1. **[P?] `/excelsior <command>`**: what to fix, with pages.

Only commands that address findings; end with `/excelsior polish`. Then: "You can ask me to run these one at a time, all at once, or in any order. Re-run `/excelsior audit` after fixes to see the score move."

Be thorough but actionable; too many P3s is noise.
