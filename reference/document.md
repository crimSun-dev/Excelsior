# Document

Generate STYLE.md: the series' visual world as it actually exists in finished pages, plans and storyboards, so every later command stages inside it. Ground truth over intention: record what the pages do, not what the team hoped they would do.

## 1. Gather the evidence

- Finished pages (images or PDFs): read a representative spread by eye, at least one page per scene type (talk, action, silence, chapter end), not just the best ones.
- Plans: run `python3 .claude/skills/excelsior/scripts/detect.py --json --stats <plans>` and keep the `stats` block: panels per page, size contrast, slant rate, shot and angle mix. These are the series' own numbers, set beside the library's.
- Production bibles, character sheets, lettering specs, prior style notes.

## 2. Extract

For each section below, record the rule and one page that proves it ("p23: the mask balloon is a perfect circle with a straight tail"). Where pages disagree, record the majority and list the exceptions as open questions; do not pick a winner silently.

## 3. Confirm the language

Auto-extracted facts are numbers; the atmosphere needs words. Ask the user once (structured tool, two or three questions) to confirm or correct the descriptive language: what the paper means, what each balloon voice sounds like, what the series' signature device is. Do not invent adjectives they have not approved.

## 4. Write STYLE.md

```markdown
---
excelsior: 1
signature_slant: false        # true only if slanted tiers are house style, not an action cue
borderless_per_scene: 1
---
# Style

## World in one paragraph
## Paper                 (what each paper value or colour means; when it changes)
## Line                  (weights, brush vs pen, what thickens for weight)
## Tone and value        (value strategy, screentone families, black balance target)
## Borders and gutters   (border weights, gutter widths, when the frame is taken away)
## Page grammar          (density by mode, dominance, slant rules, bleed rules, the series' own numbers vs the library)
## Shot language         (default shots by mode, angle rules, establishing habits)
## Lettering voices      (balloon shape, border, tail, face per voice; caption styles; SFX hand; translated-speech marking)
## Motifs and devices    (recurring images, rhymes between chapters, the signature device)
## Colour pages          (if any)
## Format rules          (print trim/bleed/safe, webtoon width/gaps; reading direction)
## Exceptions and open questions
```

Keep it a description, not a wish list. Commands read it as law: a rule written here overrides the library's CRAFT tier.

## 5. Hand off

Tell the user what was recorded, which exceptions remain open, and the one command that would most improve consistency (usually `extract` for repeated devices, or `audit` for drift).
