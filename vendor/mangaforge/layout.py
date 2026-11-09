# -*- coding: utf-8 -*-
"""Layout engine: turns a page of story beats into panel geometry, using structures and
statistics learned from the reference library (model.json).

Coordinates are inches on the trimmed page (origin top-left); bleed extends past 0..W and 0..H.
"""
import json, math, os, random
from dataclasses import dataclass, field, asdict

HERE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(HERE, "model", "model.json")

# print geometry (inches)
TRIM_W, TRIM_H, BLEED = 7.0, 10.0, 0.125
SIZE_WEIGHT = {"splash": 8.0, "big": 4.0, "wide": 2.4, "med": 1.6, "close": 1.3, "insert": 0.7}
GEN_SIZES = {(1, 1): "1024x1024", (3, 2): "1536x1024", (2, 3): "1024x1536"}


def load_model(path=None):
    with open(path or MODEL_PATH, encoding="utf-8") as f:
        return json.load(f)


@dataclass
class PanelSpec:
    id: str
    size: str = "med"            # splash | big | wide | med | close | insert
    weight: float = None         # overrides size
    bleed: bool = None           # force / forbid bleed (None = engine decides)
    breakout: str = None         # edge the subject may cross: top|bottom|left|right
    inset: bool = False          # float over the previous panel instead of taking a cell
    subject: str = "MC"          # subject cell TL..BR; lettering goes opposite
    def w(self):
        return self.weight if self.weight else SIZE_WEIGHT.get(self.size, 1.6)


@dataclass
class PageSpec:
    panels: list
    energy: float = 5.0          # 0 calm .. 10 climax
    beat: str = "build"          # calm | build | impact | reveal | pause | dread
    reading: str = "ltr"         # ltr | rtl
    margin: str = "print"        # print (live-area margin) | bleed-heavy
    seed: int = 0


# ----------------------------------------------------------------- geometry helpers
def _isect(h, v):
    """h: y = a + s*(x - cx); v: x = c + t*(y - cy). Returns (x, y)."""
    a, s, cx = h; c, t, cy = v
    # x = c + t*(a + s*(x-cx) - cy)  ->  x(1 - t s) = c + t(a - s cx - cy)
    x = (c + t * (a - s * cx - cy)) / (1 - t * s)
    return (x, a + s * (x - cx))


def _poly_area(p):
    return 0.5 * abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p))))


def _nearest_gen(ratio):
    best = min(GEN_SIZES, key=lambda k: abs(math.log(ratio / (k[0] / k[1]))))
    return GEN_SIZES[best], f"{best[0]}:{best[1]}"


# ----------------------------------------------------------------- structure choice
def candidate_structures(model, n):
    out = [s for s in model["structures"] if s["n"] == n]
    if not out:  # synthesise rows of 1..3
        rows, left = [], n
        while left > 0:
            k = min(3, left) if left != 4 else 2
            rows.append(k); left -= k
        out = [dict(sig="|".join(map(str, rows)), n=n, count=1, share=0.001, tier_h_median=[1 / len(rows)] * len(rows),
                    tier_w=[dict(sorted_median=[1 / k] * k) for k in rows], slant_rate=0.2, slant_deg_median=6.0,
                    bridge_rate=0.5, energy_q=dict(p25=3, p50=5, p75=7))]
    return out


def choose_structure(model, spec, rng):
    n = len([p for p in spec.panels if not p.inset])
    cands = candidate_structures(model, n)
    weights = [p.w() for p in spec.panels if not p.inset]
    scored = []
    for s in cands:
        tiers = [int(x) for x in s["sig"].split("|")]
        e = s["energy_q"]["p50"] if s.get("energy_q") else 5
        aff = max(0.25, math.exp(-((e - spec.energy) / 5.0) ** 2))
        # a heavy panel wants a tier of its own (or few panels in its tier)
        sizes = [p.size for p in spec.panels if not p.inset]
        i = 0; fit = 1.0
        for k in tiers:
            group = weights[i:i + k]; gs = sizes[i:i + k]; i += k
            if max(group) >= 6 and k > 1: fit *= 0.12         # a splash owns its tier
            elif max(group) >= 4 and k > 1: fit *= 0.3        # a big panel wants its own tier
            if "wide" in gs and k > 1: fit *= 0.5              # a wide shot wants the full width
            if k >= 4: fit *= 0.25                             # 4+ across is rare and cramped
            if k == 1 and max(group) < 1.4: fit *= 0.8
        # calm pages like more tiers; climaxes like fewer
        scored.append((s["share"] ** 0.6 * aff * fit, s))
    scored.sort(key=lambda t: -t[0])
    top = [(w ** 3, st) for w, st in scored[:4]]   # sharpen: variety without picking poor fits
    tot = sum(w for w, _ in top)
    r = rng.random() * tot
    for w, s in top:
        r -= w
        if r <= 0: return s
    return top[0][1]


# ----------------------------------------------------------------- main generator
def make_page(spec: PageSpec, model=None):
    model = model or load_model()
    rng = random.Random(spec.seed)
    g = model["global"]
    s = choose_structure(model, spec, rng)
    tiers = [int(x) for x in s["sig"].split("|")]
    cells = [p for p in spec.panels if not p.inset]
    insets = [p for p in spec.panels if p.inset]
    E = max(0.0, min(10.0, spec.energy))

    # ---- live area
    margin = 0.0 if spec.margin == "bleed-heavy" else 0.42   # ~0.055-0.06 of width, as learned from print-format pages
    X0, Y0, X1, Y1 = margin, margin * 1.05, TRIM_W - margin, TRIM_H - margin * 1.05
    gut_frac = (g["gutter_q"] or {}).get("p50", 0.0117)
    gutter = gut_frac * TRIM_W * (1.6 if spec.beat in ("pause", "calm") else (0.85 if E >= 7 else 1.0))
    gutter = max(0.07, gutter)
    # Japanese convention: the gaps between tiers are wider than the gaps between panels in a tier
    hgut, vgut = gutter * 1.45, gutter * 0.75

    # ---- tier heights: learned shape, bent toward the heavy panels
    base = list(s["tier_h_median"])
    i = 0; tw = []
    for k in tiers:
        tw.append(max(p.w() for p in cells[i:i + k]) ** 0.55); i += k
    h = [b * w for b, w in zip(base, tw)]
    # finish on the biggest beat when the page ends on a hook/impact
    if spec.beat in ("impact", "reveal") and len(h) > 1:
        h[-1] *= 1.12
    tot = sum(h); h = [x / tot for x in h]
    h = [max(0.12, x) for x in h]; tot = sum(h); h = [x / tot for x in h]

    # ---- slants: probability and angle scale with energy (learned rate ~0.2 overall, ~0.5 on action pages)
    slant_p = min(0.9, 0.03 + 0.06 * E) if spec.beat not in ("calm", "pause") else 0.04
    deg_q = g["slant_deg_q"] or dict(p25=4.5, p50=6.6, p75=9.9, p90=14.4)
    def angle():
        lo, hi = (deg_q["p25"], deg_q["p50"]) if E < 5 else ((deg_q["p50"], deg_q["p90"]) if E < 8 else (deg_q["p75"], deg_q["p90"] + 4))
        return rng.uniform(lo, hi)
    zig = rng.choice([-1, 1])

    # horizontal boundaries: y = a + s*(x - cx)
    cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
    usable_h = (Y1 - Y0) - hgut * (len(tiers) - 1)
    bounds = []
    acc = Y0
    for ti in range(len(tiers) - 1):
        acc += h[ti] * usable_h
        sl = 0.0
        if rng.random() < slant_p:
            sl = math.tan(math.radians(angle())) * zig; zig *= -1
            # keep the cut from eating more than 35% of the neighbouring tiers
            lim = 0.35 * min(h[ti], h[ti + 1]) * usable_h / ((X1 - X0) / 2)
            sl = max(-lim, min(lim, sl))
        bounds.append((acc + hgut / 2, sl))
        acc += hgut
    # keep every tier at least 60% of its nominal thickness at both page edges
    for _ in range(12):
        ok = True
        tl = [(Y0, 0.0)] + [(y + hgut / 2, sl) for (y, sl) in bounds]
        bl = [(y - hgut / 2, sl) for (y, sl) in bounds] + [(Y1, 0.0)]
        for ti in range(len(tiers)):
            nom = bl[ti][0] - tl[ti][0]
            for x in (X0, X1):
                th = (bl[ti][0] + bl[ti][1] * (x - cx)) - (tl[ti][0] + tl[ti][1] * (x - cx))
                if th < 0.6 * nom:
                    ok = False
                    if ti > 0: bounds[ti - 1] = (bounds[ti - 1][0], bounds[ti - 1][1] * 0.6)
                    if ti < len(bounds): bounds[ti] = (bounds[ti][0], bounds[ti][1] * 0.6)
        if ok: break
    top_lines = [(Y0, 0.0, cx)] + [(y + hgut / 2, sl, cx) for (y, sl) in bounds]
    bot_lines = [(y - hgut / 2, sl, cx) for (y, sl) in bounds] + [(Y1, 0.0, cx)]

    panels = []
    idx = 0
    for ti, k in enumerate(tiers):
        grp = cells[idx:idx + k]; idx += k
        learned = s["tier_w"][ti]["sorted_median"] if ti < len(s["tier_w"]) else [1 / k] * k
        ws = [p.w() for p in grp]
        # blend story weights with the learned unequal split (60/40 is the norm, not 50/50)
        order = sorted(range(k), key=lambda j: -ws[j])
        lw = [0] * k
        for rank, j in enumerate(order): lw[j] = learned[rank] if rank < len(learned) else 1 / k
        wts = [0.5 * (w / sum(ws)) + 0.5 * l for w, l in zip(ws, lw)]
        tw_ = sum(wts); wts = [x / tw_ for x in wts]
        usable_w = (X1 - X0) - vgut * (k - 1)
        xs = [X0]
        for j in range(k - 1): xs.append(xs[-1] + wts[j] * usable_w + vgut)
        vlines = []
        for j in range(1, k):
            t = 0.0
            if rng.random() < slant_p * 0.8:
                t = math.tan(math.radians(angle())) * rng.choice([-1, 1])
                th = (bot_lines[ti][0] - top_lines[ti][0])
                lim = 0.22 * min(wts[j - 1], wts[j]) * usable_w / max(0.5, th / 2)
                t = max(-lim, min(lim, t))
            xb = xs[j] - vgut / 2
            vlines.append((xb, t))
        tcy = (top_lines[ti][0] + bot_lines[ti][0]) / 2
        lefts = [(X0, 0.0, tcy)] + [(x + vgut / 2, t, tcy) for (x, t) in vlines]
        rights = [(x - vgut / 2, t, tcy) for (x, t) in vlines] + [(X1, 0.0, tcy)]
        order_lr = range(k) if spec.reading == "ltr" else reversed(range(k))
        for col, p in zip(order_lr, grp):
            T, B, L, R = top_lines[ti], bot_lines[ti], lefts[col], rights[col]
            poly = [_isect(T, L), _isect(T, R), _isect(B, R), _isect(B, L)]
            panels.append(dict(spec=p, poly=poly, tier=ti, col=col, edges=dict(top=ti == 0, bottom=ti == len(tiers) - 1, left=col == 0, right=col == k - 1)))

    # ---- bleed: the heaviest panel on loud pages, or forced
    heavy = max(panels, key=lambda q: q["spec"].w())
    for q in panels:
        want = q["spec"].bleed if q["spec"].bleed is not None else (q is heavy and E >= 6.5 and q["spec"].w() >= 2.4)
        q["bleed"] = []
        if want:
            poly = q["poly"]
            for edge, flag in q["edges"].items():
                if not flag: continue
                q["bleed"].append(edge)
                if edge == "top": poly = [(x, -BLEED if y <= Y0 + 1e-6 else y) for x, y in poly]
                if edge == "bottom": poly = [(x, TRIM_H + BLEED if y >= Y1 - 1e-6 else y) for x, y in poly]
                if edge == "left": poly = [(-BLEED if x <= X0 + 1e-6 else x, y) for x, y in poly]
                if edge == "right": poly = [(TRIM_W + BLEED if x >= X1 - 1e-6 else x, y) for x, y in poly]
            q["poly"] = poly

    # ---- insets float over the previous cell's far corner
    for p in insets:
        host = panels[-1] if panels else None
        if not host: continue
        xs_ = [x for x, _ in host["poly"]]; ys_ = [y for _, y in host["poly"]]
        bw, bh = (max(xs_) - min(xs_)) * 0.36, (max(ys_) - min(ys_)) * 0.34
        x1 = min(max(xs_), TRIM_W - 0.3) - 0.18; y1 = min(max(ys_), TRIM_H - 0.3) - 0.18
        poly = [(x1 - bw, y1 - bh), (x1, y1 - bh), (x1, y1), (x1 - bw, y1)]
        panels.append(dict(spec=p, poly=poly, tier=host["tier"], col=host["col"], edges={}, bleed=[], inset=True))

    # ---- finish: ids, z, ratios, lettering zone
    out = []
    for z, q in enumerate(panels):
        xs_ = [x for x, _ in q["poly"]]; ys_ = [y for _, y in q["poly"]]
        bb = [min(xs_), min(ys_), max(xs_) - min(xs_), max(ys_) - min(ys_)]
        ratio = bb[2] / bb[3]
        gen, gen_ratio = _nearest_gen(ratio)
        p = q["spec"]
        opp = {"T": "B", "M": "T", "B": "T"}[p.subject[0]] + {"L": "R", "C": "L", "R": "L"}[p.subject[1]]
        out.append(dict(id=p.id, size=p.size, weight=p.w(), poly=[[round(x, 4), round(y, 4)] for x, y in q["poly"]],
                        bbox=[round(v, 4) for v in bb], aspect=round(ratio, 4), gen_size=gen, gen_ratio=gen_ratio,
                        area_share=round(_poly_area(q["poly"]) / (TRIM_W * TRIM_H), 4), bleed=q.get("bleed", []),
                        inset=bool(q.get("inset")), z=10 + z if q.get("inset") else z, breakout=p.breakout,
                        subject=p.subject, lettering_zone=opp, tier=q["tier"]))
    return dict(trim=[TRIM_W, TRIM_H], bleed=BLEED, structure=s["sig"], structure_share=s["share"], energy=E, beat=spec.beat,
                gutter_in=dict(between_tiers=round(hgut, 4), within_tier=round(vgut, 4)), margin_in=margin, reading=spec.reading, panels=out)


# ----------------------------------------------------------------- scoring against the corpus
def score_page(layout, model=None):
    """How the page sits against the reference distributions. Returns metrics and notes."""
    model = model or load_model(); g = model["global"]
    ps = [p for p in layout["panels"] if not p["inset"]]
    areas = [p["area_share"] for p in ps]
    contrast = max(areas) / min(areas) if len(areas) > 1 else 1
    slanted = 0
    for p in layout["panels"]:
        poly = p["poly"]
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
            a = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 90
            if min(a, 90 - a) > 2.5: slanted += 1; break
    notes = []
    sc = g["size_contrast_q"]
    if len(ps) > 1 and contrast < sc["p25"]: notes.append(f"size contrast {contrast:.1f}x is below the reference p25 ({sc['p25']:.1f}x): make one panel dominate")
    if layout["energy"] >= 7 and not slanted and not any(p["bleed"] for p in layout["panels"]):
        notes.append("loud page with no slant and no bleed: references use at least one on 80%+ of action pages")
    return dict(panels=len(ps), size_contrast=round(contrast, 2), slanted_panels=slanted,
                bleeds=sum(1 for p in layout["panels"] if p["bleed"]), insets=sum(1 for p in layout["panels"] if p["inset"]),
                structure=layout["structure"], structure_share=layout["structure_share"], notes=notes)


# ----------------------------------------------------------------- vertical scroll (webtoon) mode
def make_scroll(panels, energy=5.0, width_px=800, seed=0, model=None):
    """Stack panels into a vertical strip. Gap length is pacing: short in action, long for pauses."""
    model = model or load_model(); rng = random.Random(seed)
    sc = model.get("scroll", {})
    gq = sc.get("gap_over_w_q", dict(p25=0.06, p50=0.2, p75=0.41, p90=0.63))
    y = 0.0; out = []
    for p in panels:
        w = p.w()
        hw = {"splash": 1.6, "big": 1.25, "wide": 0.62, "med": 0.85, "close": 0.75, "insert": 0.5}.get(p.size, 0.85)
        full = p.size in ("splash", "big", "wide") or rng.random() < 0.6
        pw = 1.0 if full else rng.uniform(0.62, 0.8)
        x = 0.0 if full else (rng.choice([0.04, 1 - pw - 0.04]))
        hgt = hw * (1.0 if full else 0.9)
        out.append(dict(id=p.id, size=p.size, box=[round(x * width_px), round(y * width_px), round(pw * width_px), round(hgt * width_px)],
                        aspect=round(pw / hgt, 3), gen_size=_nearest_gen(pw / hgt)[0]))
        gap = gq["p50"] if energy < 4 else (gq["p25"] if energy < 7 else gq["p10"] if "p10" in gq else 0.03)
        if p.size in ("splash",) or getattr(p, "pause", False): gap = gq["p75"]
        y += hgt + gap
    return dict(mode="scroll", width=width_px, height=round(y * width_px), panels=out)


def svg(layout, scale=60, paper="#FBFBF8", ink="#15161C", label=True):
    """Wireframe preview of a page layout."""
    W, H, b = layout["trim"][0], layout["trim"][1], layout["bleed"]
    vw, vh = (W + 2 * b) * scale, (H + 2 * b) * scale
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.0f} {vh:.0f}" width="{vw:.0f}" height="{vh:.0f}">',
         f'<rect width="{vw:.0f}" height="{vh:.0f}" fill="{paper}"/>',
         f'<rect x="{b*scale:.1f}" y="{b*scale:.1f}" width="{W*scale:.1f}" height="{H*scale:.1f}" fill="none" stroke="#c33" stroke-dasharray="6 5" stroke-width="1"/>']
    for p in sorted(layout["panels"], key=lambda q: q["z"]):
        pts = " ".join(f"{(x + b) * scale:.1f},{(y + b) * scale:.1f}" for x, y in p["poly"])
        fill = "#cfd3dc" if not p["inset"] else "#e8eaf0"
        s.append(f'<polygon points="{pts}" fill="{fill}" stroke="{ink}" stroke-width="{2 if not p["inset"] else 3}" stroke-linejoin="miter"/>')
        if label:
            x, y = (p["bbox"][0] + b + 0.12) * scale, (p["bbox"][1] + b + 0.35) * scale
            s.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="monospace" font-size="{0.22*scale:.0f}" fill="{ink}">{p["id"]} · {p["size"]} · {p["gen_ratio"]}</text>')
    s.append("</svg>")
    return "".join(s)
