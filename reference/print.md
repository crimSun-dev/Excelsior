# Print format

- **Trim and bleed:** the plan's trim is in inches (default 7×10 in planning units; tankōbon B6 is about 5×7 in, magazine B5 about 7.2×10.1 in). Bleed 3 mm / 0.125 in beyond trim; safe area about 5 mm inside trim. Balloons and faces stay inside safe.
- **Spreads:** keep faces, balloons and the action line out of the binding gutter (about 10 mm either side); design the spread's read order as one page.
- **Page turns:** in a left-to-right book page 1 is usually a right-hand page, so turning reveals an even (left) page; in a right-to-left book page 1 is a left-hand page, and the even page again comes first after a turn. Set `turn_reveals` in SERIES.md to the parity of the page the reader sees first after a turn; the detector checks reveals against it.
- **Signatures:** printers often need page counts in multiples of 4, 8 or 16; plan chapter lengths or fillers (title page, omake) accordingly.
- **Resolution:** line art 600–1200 dpi bitmap, greyscale tone 600 dpi, colour 300–350 dpi at final size.
- **Screentone:** choose frequencies that survive the print size (fine tones moiré when reduced); keep tone layers separate for edition changes.
- **Margins vs bleed:** a margin on calm pages is what makes the loud page's bleed mean volume (print Dragon Ball bleeds about 38% of pages).
