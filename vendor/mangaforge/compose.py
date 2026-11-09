# -*- coding: utf-8 -*-
"""Compositor: places generated images into a layout's panels and letters the page.

Handles non-rectangular panels, bleeds, insets (z-order), frame-breaks (a cut-out layer drawn
above the border), balloons with tails aimed at the subject, captions, SFX that straddle borders,
and an optional manga ink/screentone pass. Output: PNG and/or PDF at print resolution.
"""
import math, os, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops

HERE = os.path.dirname(__file__)
FONT_DIALOGUE = os.path.join(HERE, "fonts", "ComicNeue-Bold.ttf")
FONT_SFX = os.path.join(HERE, "fonts", "Bangers-Regular.ttf")

CELL = {"T": 0.22, "M": 0.5, "B": 0.78, "L": 0.22, "C": 0.5, "R": 0.78}


def _font(path, px):
    try: return ImageFont.truetype(path, px)
    except Exception: return ImageFont.load_default()


def _load(img):
    if img is None: return None
    if isinstance(img, Image.Image): return img
    return Image.open(img)


# ----------------------------------------------------------------- ink / tone pass
def manga_tone(im, levels=4, screen=True, lpi_px=9, contrast=1.25):
    """Greyscale with hard tone bands; the mid bands become halftone dots (screentone)."""
    g = ImageOps.autocontrast(im.convert("L"), cutoff=1)
    g = g.point(lambda v: max(0, min(255, int((v - 128) * contrast + 128))))
    if not screen:
        return g.point(lambda v: int(round(v / 255 * (levels - 1)) * 255 / (levels - 1))).convert("RGB")
    w, h = g.size
    out = Image.new("L", (w, h), 255)
    src = g.load(); dst = out.load()
    step = lpi_px
    d = ImageDraw.Draw(out)
    for y in range(0, h, step):
        for x in range(0, w, step):
            v = src[min(w - 1, x + step // 2), min(h - 1, y + step // 2)]
            if v < 45:  # spot black
                d.rectangle([x, y, x + step, y + step], fill=0)
            elif v < 215:  # screentone dot, area ~ darkness
                r = (1 - v / 255) * step * 0.62
                cx, cy = x + step / 2, y + step / 2
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
    # keep line art crisp on top: edges from the source
    edges = g.filter(ImageFilter.FIND_EDGES).point(lambda v: 0 if v > 60 else 255)
    out = ImageChops.multiply(out, edges)
    return out.convert("RGB")


# ----------------------------------------------------------------- lettering
def _wrap(text, font, max_w, draw):
    words = text.split(); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def draw_balloon(draw, text, anchor, target, px_per_in, kind="dialogue", max_w_in=1.55, font_px=None, style=None):
    """anchor = balloon centre (px); target = point the tail aims at (px). Returns balloon bbox."""
    style = style or {}
    font_px = font_px or int(0.118 * px_per_in)
    font = _font(FONT_DIALOGUE, font_px)
    txt = text.upper() if kind != "caption" else text
    lines = _wrap(txt, font, max_w_in * px_per_in * 0.78, draw)
    lh = int(font_px * 1.12)
    tw = max(draw.textlength(l, font=font) for l in lines); th = lh * len(lines)
    cx, cy = anchor
    lw = max(3, int(0.012 * px_per_in))
    if kind == "caption":
        pad = 0.07 * px_per_in
        box = [cx - tw / 2 - pad, cy - th / 2 - pad, cx + tw / 2 + pad, cy + th / 2 + pad]
        draw.rectangle(box, fill=style.get("fill", "white"), outline="black", width=lw)
    else:
        rx, ry = tw / 2 / 0.78 + 0.05 * px_per_in, th / 2 / 0.74 + 0.05 * px_per_in
        if kind == "mask":  # K-nity: Ken's mask balloon is a perfect circle
            rx = ry = max(rx, ry)
        box = [cx - rx, cy - ry, cx + rx, cy + ry]
        # tail first so the ellipse covers its root
        if target and kind in ("dialogue", "mask", "shout"):
            ang = math.atan2(target[1] - cy, target[0] - cx)
            bx, by = cx + math.cos(ang) * rx * 0.8, cy + math.sin(ang) * ry * 0.8
            dist = math.hypot(target[0] - bx, target[1] - by)
            L = min(dist * 0.55, 0.42 * px_per_in)
            tip = (bx + math.cos(ang) * L, by + math.sin(ang) * L)
            perp = ang + math.pi / 2; wid = 0.07 * px_per_in
            base1 = (bx + math.cos(perp) * wid, by + math.sin(perp) * wid)
            base2 = (bx - math.cos(perp) * wid, by - math.sin(perp) * wid)
            draw.polygon([base1, tip, base2], fill="white", outline="black", width=lw)
        if kind == "thought":
            draw.ellipse(box, fill="white", outline="black", width=lw)
            for k, sc in enumerate((0.16, 0.1)):
                ox = cx + (target[0] - cx) * (0.55 + 0.2 * k) if target else cx + rx
                oy = cy + (target[1] - cy) * (0.55 + 0.2 * k) if target else cy + ry
                r = sc * px_per_in * 0.5
                draw.ellipse([ox - r, oy - r, ox + r, oy + r], fill="white", outline="black", width=lw)
        else:
            draw.ellipse(box, fill="white", outline="black", width=lw)
            if style.get("hairline"):  # K-nity: Kkiri's cyan-magenta hairline
                draw.ellipse([box[0] + lw * 2, box[1] + lw * 2, box[2] - lw * 2, box[3] - lw * 2], outline=style["hairline"], width=max(1, lw // 2))
    y = cy - th / 2
    for l in lines:
        w = draw.textlength(l, font=font)
        draw.text((cx - w / 2, y), l, font=font, fill="black"); y += lh
    return box


def draw_sfx(canvas, text, center, px_per_in, size_in=0.9, angle=-9, fill="white", stroke="black"):
    font = _font(FONT_SFX, int(size_in * px_per_in))
    tmp = Image.new("RGBA", (int(len(text) * size_in * px_per_in * 0.75 + px_per_in), int(size_in * px_per_in * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    sw = max(4, int(size_in * px_per_in * 0.07))
    d.text((px_per_in * 0.3, px_per_in * 0.15), text, font=font, fill=fill, stroke_width=sw, stroke_fill=stroke)
    tmp = tmp.rotate(angle, expand=True, resample=Image.BICUBIC)
    bb = tmp.getbbox()
    if bb: tmp = tmp.crop(bb)
    canvas.alpha_composite(tmp, (int(center[0] - tmp.width / 2), int(center[1] - tmp.height / 2)))


# ----------------------------------------------------------------- page
def compose_page(layout, images, lettering=None, breakouts=None, dpi=300, tone=None, border_in=0.016,
                 paper="white", out_png=None, out_pdf=None, letter_styles=None):
    """images: {panel_id: path|PIL}; lettering: {panel_id: [{kind, text, speaker?}]}
    breakouts: {panel_id: path|PIL RGBA cut-out of the subject, same framing as the panel image}
    tone: None | 'screen' | 'bands'  (manga ink pass on every panel image)"""
    lettering = lettering or {}; breakouts = breakouts or {}; letter_styles = letter_styles or {}
    W, H, b = layout["trim"][0], layout["trim"][1], layout["bleed"]
    ppi = dpi
    cw, ch = int(round((W + 2 * b) * ppi)), int(round((H + 2 * b) * ppi))
    canvas = Image.new("RGBA", (cw, ch), paper)
    P = lambda x, y: ((x + b) * ppi, (y + b) * ppi)
    lw = max(2, int(border_in * ppi))
    panels = sorted(layout["panels"], key=lambda p: p["z"])
    placed = {}

    def draw_panel(p):
        poly = [P(x, y) for x, y in p["poly"]]
        xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
        bx0, by0, bx1, by1 = int(min(xs)), int(min(ys)), int(math.ceil(max(xs))), int(math.ceil(max(ys)))
        bw, bh = max(1, bx1 - bx0), max(1, by1 - by0)
        src = _load(images.get(p["id"]))
        if src is None:  # empty panel: light grey with an X so it is obvious in proofs
            src = Image.new("RGB", (bw, bh), (235, 236, 240))
            dd = ImageDraw.Draw(src); dd.line([(0, 0), (bw, bh)], fill=(200, 200, 205), width=3); dd.line([(0, bh), (bw, 0)], fill=(200, 200, 205), width=3)
        src = src.convert("RGB")
        if tone: src = manga_tone(src, screen=(tone == "screen"), lpi_px=max(6, int(ppi / 34)))
        # cover-fit, keeping the subject cell where the layout expects it
        sc = max(bw / src.width, bh / src.height)
        rs = src.resize((max(1, int(src.width * sc + 0.5)), max(1, int(src.height * sc + 0.5))), Image.LANCZOS)
        fx, fy = CELL[p["subject"][1]], CELL[p["subject"][0]]
        ox = int(min(0, max(bw - rs.width, bw * fx - rs.width * fx)))
        oy = int(min(0, max(bh - rs.height, bh * fy - rs.height * fy)))
        tile = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); tile.paste(rs, (ox, oy))
        mask = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(mask).polygon([(x - bx0, y - by0) for x, y in poly], fill=255)
        if p.get("inset"):  # white halo so an inset reads as laid on top
            halo = Image.new("L", (cw, ch), 0)
            ImageDraw.Draw(halo).polygon(poly, fill=255)
            halo = halo.filter(ImageFilter.MaxFilter(int(lw * 3) | 1))
            canvas.paste(Image.new("RGBA", (cw, ch), "white"), (0, 0), halo)
        canvas.paste(tile, (bx0, by0), mask)
        # border: skip edges that run along the bleed
        d = ImageDraw.Draw(canvas)
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = p["poly"][i], p["poly"][(i + 1) % len(poly)]
            on_bleed = (abs(x1 - x2) < 1e-3 and (x1 < 0 or x1 > W)) or (abs(y1 - y2) < 1e-3 and (y1 < 0 or y1 > H))
            if not on_bleed:
                d.line([poly[i], poly[(i + 1) % len(poly)]], fill="black", width=lw)
        placed[p["id"]] = dict(poly=poly, box=(bx0, by0, bw, bh), off=(ox, oy), size=rs.size, scale=sc)

    for p in panels:
        if not p.get("inset"): draw_panel(p)
    # frame-breaks: cut-out layer above every border (insets are laid over them afterwards)
    for p in panels:
        cut = _load(breakouts.get(p["id"]))
        if cut is None or p["id"] not in placed: continue
        cut = cut.convert("RGBA"); info = placed[p["id"]]
        if tone:
            rgb = manga_tone(cut.convert("RGB"), screen=(tone == "screen"), lpi_px=max(6, int(ppi / 34))).convert("RGBA")
            rgb.putalpha(cut.getchannel("A")); cut = rgb
        cut = cut.resize(info["size"], Image.LANCZOS)
        bx0, by0, bw, bh = info["box"]
        # allow the cut-out to spill past one edge by up to 14% of the panel
        edge = p.get("breakout") or "top"
        allow = Image.new("L", cut.size, 0); ad = ImageDraw.Draw(allow)
        ox, oy = info["off"]
        rect = [-ox, -oy, -ox + bw, -oy + bh]
        if edge == "top": rect[1] -= 0.14 * bh
        if edge == "bottom": rect[3] += 0.14 * bh
        if edge == "left": rect[0] -= 0.14 * bw
        if edge == "right": rect[2] += 0.14 * bw
        ad.rectangle(rect, fill=255)
        a = ImageChops.multiply(cut.getchannel("A"), allow); cut.putalpha(a)
        outline = a.filter(ImageFilter.MaxFilter(int(lw * 2) | 1))
        ring = Image.new("RGBA", cut.size, "black"); ring.putalpha(ImageChops.subtract(outline, a))
        canvas.alpha_composite(ring, (bx0 + ox, by0 + oy)); canvas.alpha_composite(cut, (bx0 + ox, by0 + oy))
    for p in panels:
        if p.get("inset"): draw_panel(p)
    # lettering
    d = ImageDraw.Draw(canvas)
    for p in panels:
        items = lettering.get(p["id"]) or []
        if not items: continue
        bx0, by0, bw, bh = placed[p["id"]]["box"]
        z = p.get("lettering_zone", "TL")
        zx = {"L": 0.27, "C": 0.5, "R": 0.73}[z[1]]; zy = {"T": 0.2, "M": 0.5, "B": 0.78}[z[0]]
        tx, ty = bx0 + bw * CELL[p["subject"][1]], by0 + bh * CELL[p["subject"][0]] - 0.1 * bh
        y = by0 + bh * zy
        for k, it in enumerate(items):
            kind = it.get("kind", "dialogue")
            if kind == "sfx":
                fit = (bw * 0.8) / ppi / max(1, len(it["text"])) / 0.55        # Bangers glyphs ~0.55 em wide
                size = min(it.get("size_in", 0.85), max(0.28, fit), bh / ppi * 0.4)
                draw_sfx(canvas, it["text"], (bx0 + bw * it.get("x", 0.6), by0 + bh * it.get("y", 0.55)), ppi, size_in=size, angle=it.get("angle", -9))
                continue
            x = bx0 + bw * (zx + (0.08 if k % 2 else 0) * (1 if zx < 0.5 else -1))
            st = letter_styles.get(it.get("speaker"), {})
            box = draw_balloon(d, it["text"], (x, y), (tx, ty), ppi, kind=st.get("kind", kind), style=st,
                               max_w_in=min(1.7, max(0.95, bw / ppi * 0.5)))
            y = box[3] + 0.12 * ppi if zy < 0.6 else box[1] - 0.12 * ppi - (box[3] - box[1])
    img = canvas.convert("RGB")
    if out_png: img.save(out_png, dpi=(dpi, dpi))
    if out_pdf: img.save(out_pdf, "PDF", resolution=dpi)
    return img


def compose_scroll(scroll_layout, images, lettering=None, bg="white", gap_colour=None, out_png=None):
    W, H = scroll_layout["width"], scroll_layout["height"]
    canvas = Image.new("RGBA", (W, H), bg); d = ImageDraw.Draw(canvas)
    for p in scroll_layout["panels"]:
        x, y, w, h = p["box"]
        src = _load(images.get(p["id"])) or Image.new("RGB", (w, h), (230, 230, 235))
        src = ImageOps.fit(src.convert("RGB"), (w, h), Image.LANCZOS)
        canvas.paste(src, (x, y))
        if w < W: d.rectangle([x, y, x + w, y + h], outline="black", width=3)
        for it in (lettering or {}).get(p["id"], []):
            draw_balloon(d, it["text"], (x + w * 0.3, y + h * 0.18), (x + w * 0.5, y + h * 0.5), 300, kind=it.get("kind", "dialogue"), max_w_in=1.4, font_px=int(W * 0.035))
    img = canvas.convert("RGB")
    if out_png: img.save(out_png)
    return img
