# Census sample schema

Two append-only jsonl families, joined by identity. A code pass never writes to a geometry file.
No page image, traced face, redrawn body, or dialogue transcript is stored anywhere in `corpus/`.

`tools/validate_codes.py` enforces this file. A code file that fails it does not count as read.

## Join key

`series` + `cbz` + `page` + `panel`

- `series`: `DB`, `DBS`, `HNK`, `KSB`, `LC`, `P3`, `P5`.
- `cbz`: path relative to the library root, as written in `COVERAGE.md`.
- `page`: the analyzer's page index within that cbz.
- `panel`: index in the frozen `panels` array. On a strip page, index in the frozen `blocks` array.

## Geometry row: `geometry/<series>.jsonl`

One row per page. Frozen. The analyzer object is stored as returned. These keys are added once and not edited:

| Key | Meaning |
|---|---|
| `cbz` | Pointer to the chapter file. |
| `status` | `measured`, `excluded`, or `unreadable`. |
| `reason` | Required when `excluded` or `unreadable`. |
| `tier_sig` | `learn.tiers()` as `"1\|2\|1"`. Print pages only. Never on a strip, never on Link Click. |
| `reading_order` | Permutation of `panels` indexes: tiers top to bottom; right to left within a tier; an inset follows the smallest panel containing its centre. Polygons are not mirrored. |

Print pages carry the analyzer's `panels[].poly`, `bbox`, `slant`, `bleed`, and page `gutter`, `insets`, `breaks`. Strip pages carry `strip: true`, `blocks`, `gaps`, `gap_dark`. Link Click slices under the analyzer's 2.2x height rule also carry `forced_strip: true`.

Everything an eye reading learns about a page lives on the code row. A code row never changes a geometry row.

## Code row: `codes/<series>.jsonl`

One row per page read by eye. The row's existence means "read".

```json
{
  "series": "HNK", "cbz": "...", "page": 12,
  "read": true,
  "page_kind": "story",
  "sfx_lettering": "none",
  "panels": [
    {"panel": 0,
     "kind": "frame",
     "shape": "rectangle",
     "expression": {"scale": "MCU", "angle": "eye", "gaze": "left", "mouth": "open", "brow": "knit",
                    "marks": [], "deformed": false, "note": ""},
     "faces": 1,
     "technique": [],
     "scene_job": null,
     "merged_frames": 1,
     "poly_fit": "ok"}
  ],
  "absurdity": [],
  "creativity": [],
  "fourth_wall": [],
  "reader_address": [],
  "eye_overrun": [],
  "note": ""
}
```

### Page fields

- `read_token`: the code printed above the art on the rendered page. Required on every row. See "Read receipts".
- `page_kind`: `story`, `credits`, `bonus`, `volume-extra`, or `third-party`.
  - A story page codes every frozen panel index and has no `reason`.
  - A non-story page is `read: true`, requires `reason`, and leaves the rate denominator. Its `panels` may be empty.
  - `third-party` is material by someone other than the series' creators inside the file. `reason` names the kind, such as scanlation fan art or a magazine advert. Its `panels` are always empty, so another artist's drawing never enters this series' samples.
- `order_note`: present only when the page is read in a different order than the frozen `reading_order`. Codes keep using the analyzer panel indexes.
- `note`: one original sentence on what the device does for pacing or the joke.
- A correction is a new row with `"supersedes": true` for the same page. Earlier rows are not edited.

### Panel fields

- `kind`: `frame`, `title-art`, or `non-frame`. Every frozen index is coded. `title-art` and `non-frame` panels have a null `expression` and stay out of expression rates and motif counts.
- `shape`: `rectangle`, `slant`, `sliver`, `borderless`, `inset`, or `bleed`.
- `expression`: one tuple for the dominant face, or `null` when there is no face. `scale` and `angle` use the names in `tags.py`. A feature outside these sets stays in `note` until three sightings.
- `faces`: `0` when `expression` is null, otherwise the number of faces in the panel. Expression rates are dominant-face rates.
- `technique[]`: a `[TECHNIQUE]` heading printed in `composition-standard.md`, copied exactly.
- `scene_job`: KonoSuba only, one of `setup`, `dialogue`, `reaction`, `escalation`, `climax`, `aftermath`. Otherwise `null`.
- `merged_frames`: count of drawn frames inside the one analyzer polygon, at least 1.
- `poly_fit`: `ok` or `cropped`. Neither `merged_frames` nor `poly_fit` adds a box. A code row never holds a box or polygon of its own.

### Devices

- `absurdity[]`: `{"expectation": "...", "setup": [{"page": 2, "panel": 4}], "break": [{"page": 3, "panel": 1}]}`. Each pair addresses the same chapter file. The box is the frozen polygon at that address.
- `creativity[]`: `{"code": "proposed-code", "panels": [...], "note": "...", "origin": "artist"}`. Promoted only under the rule in "Promotion". A `localizer` or `scanlator` origin is not creativity.
- `fourth_wall[]`: `{"class": "...", "panel": 0, "edge": "right", "overrun_w": 0.04, "overrun_h": 0.1, "to_reader": false, "origin": "artist"}`. Classes: `address-reader`, `figure-leaves-grid`, `aside`, `sfx-in-gutter`, `caption-in-gutter`, `prop-enters`, `border-overrun`.
- `reader_address[]`: `{"panel": 0, "aim": "face|balloon|figure"}`, one entry for each panel with a `to_reader: true` device.
- `eye_overrun[]`: eye-labeled crossings on colour pages, same shape as `fourth_wall[]`. This field never feeds `bridge_page_rate`.

### Rules for `fourth_wall` and `eye_overrun`

- `panel: null` is only for a page-level device such as a margin caption. Then `edge`, `overrun_w`, and `overrun_h` are null together.
- A crossing names a real panel index, an `edge` of `top`, `bottom`, `left`, or `right`, and both fractions. `border-overrun` always crosses.
- Overrun is how far the object extends past that edge, as a fraction of page width and of page height. Both numbers are positive when an edge is set, and they are eye estimates.
  - Left or right edge: `overrun_w` is the protrusion and `overrun_h` is the height of the part that has crossed.
  - Top or bottom edge: `overrun_h` is the protrusion and `overrun_w` is the width of the part that has crossed.
- `to_reader: true` means a character, their face, or their balloon is aimed at the reader. A margin teaser or "continued" caption stays `caption-in-gutter` with `to_reader: false`, and it does not enter `reader_address`.
- A face aimed out of the page with an in-scene listener at the camera position is `to_reader: false`. `gaze: forward` only records which way the face points and does not by itself create a `reader_address` entry.

### Lettering origin

`origin` is `artist`, `localizer`, or `scanlator` on a lettering device, and is required on `sfx-in-gutter` and `caption-in-gutter`. It may be `null` on a device that is drawn art. `localizer` is lettering redrawn by an official English edition.

Translator notes stay out of the gutter classes. A crossing can remain with a `localizer` or `scanlator` origin, but it does not count toward technique rates, motif promotion, or creativity, and no technique tag rests on it alone.

`sfx_lettering` is required on every story page: `original` when the original sound-effect lettering is visible on the page, `localizer` or `scanlator` when only replaced lettering is visible, `none` when the page has no sound effects. It is `null` on a non-story page.

## Read receipts

A page counts as read only when its row quotes the code printed above the art by `tools/render_pages.py`. Only a hash of the code is saved, in `codes/_receipts/<series>.json`, so the code exists in plain form only on the image. An image that was removed or never arrived yields no code, and the validator rejects the row. Rendering a page again issues a new code and voids the old one.

No file is exempt.

## Empty versus unread

| State | Representation |
|---|---|
| Not yet read | No code row for that join key. |
| Read, nothing there | A code row with `"read": true` and `"absurdity": []`, `"reader_address": []`. |
| Read, not a story page | A code row with `page_kind` other than `story`, a `reason`, and a valid `read_token`. |
| Not codable | Geometry `status` is `excluded` or `unreadable`. |

Empty is an array that exists on a row that exists. A missing or `null` value for `absurdity`, `reader_address`, `creativity`, or `fourth_wall` makes the row invalid, so a coded empty page cannot be read as unread.

## Rates on the sheets

Rates print as `count / story pages read`. Non-story pages leave the denominator. Each sheet still prints its excluded and unreadable counts beside that rate.

Sound-effect rates print as `count / story pages with sfx_lettering: original`, so a file with replaced lettering does not read artificially low.

Dragon Ball's 527 `unreadable` pages are blank paper, about 99% white. They stay `unreadable`, and their geometry rows stay as they are.

## Promotion

A motif or creativity code promotes at three distinct chapters in one series, matched by volume and chapter identity (the `duplicate` key in `COVERAGE.md`). The same device in both copies of one chapter is one citation. Both files stay in the ledger.

Rates still print as `count / story pages read`, with the distinct-chapter count beside them.

## Other files

- `COVERAGE.md`: resume ledger.
- `samples.jsonl`: one row per device instance, `{"id", join key, "kind", "code"}`.
- `sheets/<series>.md`: rollups.
- `DIFF_AGAINST_EXCELSIOR.md`: written before any Excelsior edit.
