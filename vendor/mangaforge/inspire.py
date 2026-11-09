# -*- coding: utf-8 -*-
"""Reference-inspired layouts.

For each new page, draw a random handful of real reference pages that suit it (same panel count,
similar energy, panel sizes in the right order), adapt each one's actual panel geometry to the
K-nity page (slants, insets and bleeds kept), and return the best few. Every layout records which
reference page inspired it. Only geometry is reused; artwork never leaves the reference library.

    from mangaforge.inspire import inspire
    layouts = inspire(PageSpec(panels=[...], energy=7, beat="impact"), k=3)
"""
import json, math, os, random
from .layout import PageSpec, PanelSpec, TRIM_W, TRIM_H, BLEED, SIZE_WEIGHT, _poly_area, _nearest_gen, score_page, load_model
from .refpool import load_pool, SERIES_NAME, bbox
from .learn import tiers as _tiers

HERE = os.path.dirname(__file__)
TAGS_PATH = os.path.join(HERE, "model", "shot_tags.json")
MARGIN = 0.42
X0, Y0, X1, Y1 = MARGIN, MARGIN * 1.05, TRIM_W - MARGIN, TRIM_H - MARGIN * 1.05
SHOT_WORDS = {"EWS": "extreme wide shot", "WS": "wide shot", "FS": "full-figure shot", "MS": "medium shot",
              "MCU": "medium close-up", "CU": "close-up", "ECU": "extreme close-up", "INS": "insert detail shot"}
ANGLE_WORDS = {"eye": "eye level", "low": "low angle", "worm": "worm's-eye view", "high": "high angle",
               "bird": "bird's-eye view", "dutch": "dutch angle", "ots": "over the shoulder", "pov": "point of view"}


def key(t):
    return f"{t['c']}:{t['p']}"


_TAGS = None


def load_tags():
    global _TAGS
    if _TAGS is None:
        try:
            with open(TAGS_PATH, encoding="utf-8") as f: _TAGS = json.load(f)
        except (OSError, ValueError):
            _TAGS = {}
    return _TAGS


def _rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v)
    i = 0
    while i < len(o):  # average ranks for ties
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
        for k in range(i, j + 1): r[o[k]] = (i + j) / 2
        i = j + 1
    return r


def _spearman(a, b):
    if len(a) < 2: return 0.0
    ra, rb = _rank(a), _rank(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else 0.0


def prescore(t, spec):
    """How well a reference page's shape suits this page's beats (before adapting)."""
    ws = [p.w() for p in spec.panels]
    ar = [p["a"] for p in t["ps"]]
    fit = _spearman(ws, ar) if max(ws) > min(ws) else 0.0
    s = 2.0 * fit
    # the heaviest beat should land on one of the two biggest panels
    if max(ws) >= 2.4 and len(ws) > 2:
        hv = ws.index(max(ws)); top2 = sorted(range(len(ar)), key=lambda i: -ar[i])[:2]
        s += 0.6 if hv in top2 else -0.8
    # size contrast close to what the beats ask for (area ratio grows faster than the weight ratio)
    if len(ws) > 1:
        want = (max(ws) / min(ws)) ** 1.25; have = max(ar) / max(1e-4, min(ar))
        s -= 0.22 * abs(math.log(have / want))
    s += 1.4 * math.exp(-((t["e"] - spec.energy) / 2.6) ** 2)
    s += 0.5 * t.get("cl", 1.0)
    for p, q in zip(spec.panels, t["ps"]):
        u0, v0, u1, v1 = bbox(q["q"])
        asp = (u1 - u0) * (X1 - X0) / max(1e-3, (v1 - v0) * (Y1 - Y0))   # panel aspect on the K-nity page
        want = {"wide": (1.15, 9), "big": (0.6, 9), "splash": (0.5, 9), "close": (0.42, 2.6), "med": (0.45, 3.2), "insert": (0.4, 3.5)}.get(p.size, (0.4, 9))
        if asp < want[0]: s -= 0.9 * min(2.0, want[0] / max(asp, 0.05) - 1) + 0.3
        elif asp > want[1]: s -= 0.4
        if p.size == "wide": s += 0.35 if u1 - u0 > 0.82 else -0.6
        if p.inset: s += 0.4 if q["i"] else -0.25
        elif q["i"] and p.w() >= 1.3: s -= 0.9          # a real beat would be shrunk into an inset
        if p.size == "splash" and len(spec.panels) > 1 and q["a"] < 0.35: s -= 0.6
    if spec.beat in ("pause", "calm") and t["e"] > 7.5: s -= 0.5
    if spec.beat in ("impact", "reveal") and t["e"] < 3: s -= 0.5
    return s


def adapt(t, spec):
    """Map a template's geometry onto the K-nity page and attach the beats in reading order."""
    gw, gh = X1 - X0, Y1 - Y0
    tags = load_tags().get(key(t), {}).get("panels", [])
    out = []
    # tiers for the tier index used downstream
    cells = [dict(bbox=[*bbox(q["q"])[:2], bbox(q["q"])[2] - bbox(q["q"])[0], bbox(q["q"])[3] - bbox(q["q"])[1]], k=i)
             for i, q in enumerate(t["ps"]) if not q["i"]]
    tier_of = {}
    for ti, tr in enumerate(_tiers(dict(panels=cells))):
        for p in tr["ps"]: tier_of[p["k"]] = ti
    # a bleed on one panel carries to every panel that reaches the same page edge (the detector often flags only one)
    page_bleed = set("".join(q["e"] for q in t["ps"]))
    reach = {"t": lambda b: b[1] < 0.03, "b": lambda b: b[3] > 0.97, "l": lambda b: b[0] < 0.03, "r": lambda b: b[2] > 0.97}
    for z, (p, q) in enumerate(zip(spec.panels, t["ps"])):
        edges = set(q["e"]) | {e for e in page_bleed if not q["i"] and reach[e](bbox(q["q"]))}
        if p.bleed is False: edges = set()
        pts = []
        for u, v in q["q"]:
            if spec.reading == "rtl": u = 1 - u
            x = X0 + min(1, max(0, u)) * gw; y = Y0 + min(1, max(0, v)) * gh
            lft, rgt = ("r", "l") if spec.reading == "rtl" else ("l", "r")
            nob = p.bleed is False
            if (("t" in edges and v < 0.03) or v < -0.02) and not nob: y = -BLEED
            if (("b" in edges and v > 0.97) or v > 1.02) and not nob: y = TRIM_H + BLEED
            if ((lft in edges and u < 0.03) or u < -0.02) and not nob: x = -BLEED
            if ((rgt in edges and u > 0.97) or u > 1.02) and not nob: x = TRIM_W + BLEED
            pts.append((x, y))
        if p.bleed is True and not edges:   # forced bleed: push every edge that sits on the live boundary
            pts = [(-BLEED if x <= X0 + 0.15 else (TRIM_W + BLEED if x >= X1 - 0.15 else x),
                    -BLEED if y <= Y0 + 0.15 else (TRIM_H + BLEED if y >= Y1 - 0.15 else y)) for x, y in pts]
        bl = sorted({"top" if y < 0 else "bottom" for _, y in pts if y < 0 or y > TRIM_H} |
                    {"left" if x < 0 else "right" for x, _ in pts if x < 0 or x > TRIM_W})
        xs = [x for x, _ in pts]; ys = [y for _, y in pts]
        bb = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
        if bb[2] < 0.2 or bb[3] < 0.2: return None           # degenerate after mapping
        if not q["i"] and not (0.2 <= bb[2] / bb[3] <= 5.5): return None   # text columns / hairline strips, not panels
        ratio = bb[2] / bb[3]; gen, gen_ratio = _nearest_gen(ratio)
        opp = {"T": "B", "M": "T", "B": "T"}[p.subject[0]] + {"L": "R", "C": "L", "R": "L"}[p.subject[1]]
        inset = bool(q["i"])
        d = dict(id=p.id, size=p.size, weight=p.w(), poly=[[round(x, 4), round(y, 4)] for x, y in pts],
                 bbox=[round(v, 4) for v in bb], aspect=round(ratio, 4), gen_size=gen, gen_ratio=gen_ratio,
                 area_share=round(_poly_area(pts) / (TRIM_W * TRIM_H), 4), bleed=bl, inset=inset,
                 z=10 + z if inset else z, breakout=p.breakout, subject=p.subject, lettering_zone=opp,
                 tier=tier_of.get(z, max(tier_of.values(), default=0)), slant=q["s"])
        if z < len(tags) and tags[z]: d["ref_shot"] = tags[z]
        out.append(d)
    ref = dict(key=key(t), series=SERIES_NAME.get(t["s"], t["s"]), code=t["s"], chapter=t["c"], page=t["p"] + 1,
               title=t.get("ti", ""), energy=t["e"], structure=t["sig"], tagged=bool(tags))
    return dict(trim=[TRIM_W, TRIM_H], bleed=BLEED, structure=t["sig"], structure_share=0.0, energy=spec.energy, beat=spec.beat,
                gutter_in=None, margin_in=MARGIN, reading=spec.reading, panels=out, inspired_by=ref, source="reference")


def candidates(spec, pool=None, series=None, exclude=()):
    pool = pool or load_pool()
    n = len(spec.panels)
    tags = load_tags()
    if n < 2: return []   # single-panel pages: the detector often merges panels there, so the engine handles splashes
    return [t for t in pool["templates"] if t["n"] == n and t.get("cl", 1) >= 0.5 and t.get("cov", 1) >= 0.9
            and (not series or t["s"] in series) and key(t) not in exclude and not tags.get(key(t), {}).get("exclude")]


def inspire(spec, k=3, handful=24, pool=None, model=None, series=None, exclude=(), temperature=0.9):
    """Return up to k adapted layouts (best first), each with layout['inspired_by'].
    Draws `handful` references at random, weighted by how well they suit the page and balanced across series."""
    pool = pool or load_pool(); model = model or load_model()
    rng = random.Random(spec.seed)
    C = candidates(spec, pool, series, exclude)
    if not C: return []
    share = {}
    for t in C: share[t["s"]] = share.get(t["s"], 0) + 1
    S = len(share)
    scored = [(prescore(t, spec), t) for t in C]
    best = max(s for s, _ in scored)
    # weighted random draw without replacement (Efraimidis-Spirakis keys)
    keyed = []
    for s, t in scored:
        w = math.exp((s - best) / temperature) * (len(C) / (S * share[t["s"]])) ** 0.85
        if w <= 0: continue
        keyed.append((rng.random() ** (1.0 / w), s, t))
    keyed.sort(key=lambda x: -x[0])
    drawn = keyed[:handful]
    res = []
    for _, s, t in drawn:
        L = adapt(t, spec)
        if L is None or min(p["area_share"] for p in L["panels"]) < 0.004: continue   # degenerate after mapping
        sc = score_page(L, model)
        L["inspire_score"] = round(s - 0.35 * len(sc["notes"]), 3)
        res.append((L["inspire_score"], L, sc))
    res.sort(key=lambda x: -x[0])
    # prefer different series among the top picks
    picked, seen = [], set()
    for r in res:
        if r[1]["inspired_by"]["code"] not in seen:
            picked.append(r); seen.add(r[1]["inspired_by"]["code"])
        if len(picked) == k: break
    for r in res:
        if len(picked) == k: break
        if r not in picked: picked.append(r)
    out = []
    for s, L, sc in picked:
        L["score"] = sc; out.append(L)
    return out


def shot_hint(tag):
    """'CU/low' style tag -> words for an image prompt."""
    if not tag: return ""
    shot = SHOT_WORDS.get(tag.get("shot", ""), ""); ang = ANGLE_WORDS.get(tag.get("angle", ""), "")
    return ", ".join(x for x in (shot, ang) if x)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sizes", default="big,med,close,med", help="panel sizes in reading order, e.g. wide,med,med,big")
    ap.add_argument("--energy", type=float, default=5); ap.add_argument("--beat", default="build")
    ap.add_argument("--k", type=int, default=3); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rtl", action="store_true"); ap.add_argument("--svg", help="write the picks side by side to this SVG")
    a = ap.parse_args(argv)
    spec = PageSpec(panels=[PanelSpec(id=str(i + 1), size=s.strip().rstrip("*"), inset=s.strip().endswith("*"))
                            for i, s in enumerate(a.sizes.split(","))], energy=a.energy, beat=a.beat,
                    reading="rtl" if a.rtl else "ltr", seed=a.seed)
    Ls = inspire(spec, k=a.k)
    for L in Ls:
        r = L["inspired_by"]
        print(f"{L['inspire_score']:+.2f}  {r['series']} · {r['chapter']} p{r['page']} · {r['structure']} · notes: {L['score']['notes']}")
    if a.svg and Ls:
        from .layout import svg
        parts = [svg(L, scale=40) for L in Ls]
        w = 7 * 40 + 20
        body = "".join(f'<g transform="translate({i * w},0)">{p[p.index(">") + 1:p.rindex("</svg>")]}</g>' for i, p in enumerate(parts))
        open(a.svg, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * len(parts)}" height="{10 * 40 + 20}">{body}</svg>')
        print("->", a.svg)


if __name__ == "__main__":
    main()
