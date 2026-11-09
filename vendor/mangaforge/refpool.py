# -*- coding: utf-8 -*-
"""Reference pool: every usable analysed page stored as a reusable layout template.

A template is geometry only: the page's panel shapes (normalised to its live area), which ones
bleed, which float as insets, slant angles, and the page's energy. No artwork is stored.

    python -m mangaforge.refpool analysis.jsonl [more.jsonl ...] --out mangaforge/model/refpool.json.gz
"""
import argparse, bisect, collections, gzip, json, math, os
import numpy as np
from .learn import usable, dyn_score, true_slant, tiers

HERE = os.path.dirname(__file__)
POOL_PATH = os.path.join(HERE, "model", "refpool.json.gz")
# Japanese sources read right-to-left; their templates are mirrored for left-to-right books
RTL_SERIES = {"DB", "DBS", "HNK", "KSB", "P3", "P5"}
SERIES_NAME = {"DB": "Dragon Ball (colour)", "DBS": "Dragon Ball Super", "HNK": "Jibaku Shounen Hanako-kun",
               "KSB": "KonoSuba", "LC": "Link Click", "P3": "Persona 3", "P5": "Persona 5"}


# ----------------------------------------------------------------- convex polygon helpers
def area(p):
    return 0.5 * abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p))))


def ccw(p):
    s = sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))
    return p if s < 0 else p[::-1]


def clip(subject, clipper):
    """Sutherland-Hodgman: intersection of a polygon with a convex polygon."""
    def inside(pt, a, b):
        return (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0]) >= 0
    def cross(p1, p2, a, b):
        dc = (a[0] - b[0], a[1] - b[1]); dp = (p1[0] - p2[0], p1[1] - p2[1])
        n1 = a[0] * b[1] - a[1] * b[0]; n2 = p1[0] * p2[1] - p1[1] * p2[0]
        d = dc[0] * dp[1] - dc[1] * dp[0]
        if abs(d) < 1e-12: return p2
        return ((n1 * dp[0] - n2 * dc[0]) / d, (n1 * dp[1] - n2 * dc[1]) / d)
    out = list(subject); cl = clipper
    # orientation: make clipper counter-clockwise in y-down coords (inside test sign)
    if sum(cl[i][0] * cl[i - 1][1] - cl[i - 1][0] * cl[i][1] for i in range(len(cl))) > 0: cl = cl[::-1]
    for i in range(len(cl)):
        a, b = cl[i - 1], cl[i]
        inp = out; out = []
        if not inp: break
        s = inp[-1]
        for e in inp:
            if inside(e, a, b):
                if not inside(s, a, b): out.append(cross(s, e, a, b))
                out.append(e)
            elif inside(s, a, b): out.append(cross(s, e, a, b))
            s = e
    return out


def overlap(p, q):
    c = clip(p, q)
    return area(c) if len(c) >= 3 else 0.0


def bbox(p):
    xs = [x for x, _ in p]; ys = [y for _, y in p]
    return min(xs), min(ys), max(xs), max(ys)


def xy_order(items):
    """Reading order (left-to-right) by recursive XY cuts: rows top to bottom, then columns left to right,
    then rows again inside each column. Boxes are shrunk a little so slanted gutters still cut cleanly.
    items: (key, x, y, w, h)."""
    def shrink(it):
        k, x, y, w, h = it
        return (k, x + 0.12 * w, y + 0.12 * h, x + 0.88 * w, y + 0.88 * h)
    def groups(bs, lo, hi):
        bs = sorted(bs, key=lambda b: b[lo]); out = [[bs[0]]]; edge = bs[0][hi]
        for b in bs[1:]:
            if b[lo] >= edge: out.append([b])
            else: out[-1].append(b)
            edge = max(edge, b[hi])
        return out
    def rec(bs):
        if len(bs) <= 1: return [b[0] for b in bs]
        rows = groups(bs, 2, 4)
        if len(rows) > 1: return [k for r in rows for k in rec(r)]
        cols = groups(bs, 1, 3)
        if len(cols) > 1: return [k for c in cols for k in rec(c)]
        return [b[0] for b in sorted(bs, key=lambda b: (b[2] + b[4], b[1] + b[3]))]
    return rec([shrink(i) for i in items])


# ----------------------------------------------------------------- template extraction
def _shape(pn, W, H):
    """Panel polygon in page fractions. Clean quads keep their (possibly slanted) shape;
    messy hulls (balloons straddling the border) fall back to the bounding box."""
    if pn["nv"] == 4 and pn["solidity"] > 0.95:
        poly = [tuple(v) for v in pn["poly"]]
    else:
        x, y, w, h = pn["bbox"]; poly = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    return poly


def template(r, energy):
    W, H = r["w"], r["h"]
    raw = []
    for pn in r["panels"]:
        if pn["area"] < 0.01: continue   # balloons / caption boxes the detector caught as panels
        poly = _shape(pn, W, H)
        raw.append(dict(poly=poly, area=area([(x * W, y * H) for x, y in poly]) / (W * H), bleed=pn["bleed"],
                        slant=pn["slant"] if true_slant(pn) else 0.0, src=pn))
    if not raw: return None
    # insets: a small panel sitting inside a bigger one
    for a in raw:
        a["inset"] = False
        ax0, ay0, ax1, ay1 = bbox(a["poly"])
        for b in raw:
            if b is a or b["area"] < a["area"] * 2.2: continue
            bx0, by0, bx1, by1 = bbox(b["poly"])
            iw = max(0, min(ax1, bx1) - max(ax0, bx0)); ih = max(0, min(ay1, by1) - max(ay0, by0))
            if iw * ih > 0.8 * (ax1 - ax0) * (ay1 - ay0): a["inset"] = True; break
    cells = [a for a in raw if not a["inset"]]
    # reject pages whose cells overlap (detector merged/split something)
    for i, a in enumerate(cells):
        for b in cells[i + 1:]:
            ov = overlap([(x * W, y * H) for x, y in a["poly"]], [(x * W, y * H) for x, y in b["poly"]]) / (W * H)
            if ov > 0.02 * min(a["area"], b["area"]) + 1e-6: return None
    # live box from the panels that do not bleed on that side
    def side(vals, flags, fallback):
        v = [x for x, f in zip(vals, flags) if not f]
        return v if v else [fallback]
    x0 = min(side([bbox(a["poly"])[0] for a in cells], [a["bleed"]["left"] for a in cells], r["margin"]))
    x1 = max(side([bbox(a["poly"])[2] for a in cells], [a["bleed"]["right"] for a in cells], 1 - r["margin"]))
    y0 = min(side([bbox(a["poly"])[1] for a in cells], [a["bleed"]["top"] for a in cells], r["margin"] * W / H))
    y1 = max(side([bbox(a["poly"])[3] for a in cells], [a["bleed"]["bottom"] for a in cells], 1 - r["margin"] * W / H))
    if x1 - x0 < 0.5 or y1 - y0 < 0.5: return None
    gw, gh = x1 - x0, y1 - y0
    flip = r["series"] in RTL_SERIES
    ps = []
    for a in raw:
        pts = []
        for x, y in a["poly"]:
            u = (x - x0) / gw; v = (y - y0) / gh
            if flip: u = 1 - u          # store every template as left-to-right
            pts.append([round(u, 4), round(v, 4)])
        b = a["bleed"]
        edges = "".join(k for k, f in (("t", b["top"]), ("b", b["bottom"]),
                                         ("l", b["right"] if flip else b["left"]), ("r", b["left"] if flip else b["right"])) if f)
        ps.append(dict(q=pts, a=round(a["area"], 4), i=int(a["inset"]), e=edges, s=round(a["slant"], 1)))
    # reading order (left-to-right after mirroring): tiers top to bottom, panels left to right; insets after their host
    fake = dict(panels=[dict(bbox=[min(x for x, _ in p["q"]), min(y for _, y in p["q"]),
                                   max(x for x, _ in p["q"]) - min(x for x, _ in p["q"]),
                                   max(y for _, y in p["q"]) - min(y for _, y in p["q"])], k=k)
                        for k, p in enumerate(ps) if not p["i"]])
    order = xy_order([(p["k"], *p["bbox"]) for p in fake["panels"]])
    for k, p in enumerate(ps):
        if p["i"]:  # after the cell whose box contains its centre
            cx = sum(x for x, _ in p["q"]) / len(p["q"]); cy = sum(y for _, y in p["q"]) / len(p["q"])
            host = next((h for h in order if not ps[h]["i"] and bbox(ps[h]["q"])[0] <= cx <= bbox(ps[h]["q"])[2]
                         and bbox(ps[h]["q"])[1] <= cy <= bbox(ps[h]["q"])[3]), order[-1] if order else None)
            order.insert(order.index(host) + 1 if host in order else len(order), k)
    ps = [ps[k] for k in order]
    for p in ps:   # every panel must sit inside the live box (bleeds aside) and have real size
        u0, v0, u1, v1 = bbox(p["q"])
        if u1 - u0 < 0.08 or v1 - v0 < 0.06: return None
        if (u0 < -0.025 and "l" not in p["e"]) or (u1 > 1.025 and "r" not in p["e"]) or \
           (v0 < -0.025 and "t" not in p["e"]) or (v1 > 1.025 and "b" not in p["e"]): return None
    sig = "|".join(str(len(t["ps"])) for t in tiers(fake))
    # share of panel area whose outline was measured cleanly (messy hulls may be merged panels)
    tot = sum(a["area"] for a in raw) or 1
    clean_share = sum(a["area"] for a in raw if a["src"]["nv"] <= 6 and a["src"]["solidity"] > 0.93) / tot
    # how much of the live box the cells tile (holes = panels the detector missed)
    from PIL import Image, ImageDraw
    m = Image.new("L", (100, 140), 0); dr = ImageDraw.Draw(m)
    for p in ps: dr.polygon([(x * 100, y * 140) for x, y in p["q"]], fill=255)
    cov = float((np.asarray(m) > 0).mean())
    return dict(s=r["series"], c=r["chapter"], p=r["page"], n=len(ps), sig=sig, e=energy, d=round(r["dyn"], 3),
                bk=r["breaks"], ink=round(r["ink"]["black"], 3), dark=int(bool(r.get("dark"))), cl=round(clean_share, 2), cov=round(cov, 3), ps=ps,
                th=_rel(r.get("thumb") or r.get("f") or ""), ti=(r.get("title") or "")[:80])


def _rel(path):
    """Thumbnail path relative to the analysis root (thumbs/... or pages/...), so the pool travels between machines."""
    for k in ("/thumbs/", "/pages/"):
        if k in path: return k.strip("/") + "/" + path.split(k, 1)[1]
    return path


def build(rows):
    sat = collections.defaultdict(list)
    for r in rows:
        if not r.get("strip") and not r.get("error"): sat[r["series"]].append(r["ink"]["sat"])
    colour = {s for s, v in sat.items() if np.median(v) > 0.12}
    for r in rows:
        if r.get("series") in colour: r["colour_series"] = True
    # the first sample and the full ingest overlap on some chapters: keep one copy per (series, chapter no., page)
    seen, uniq = set(), []
    for r in sorted(rows, key=lambda r: 0 if r.get("thumb") else 1):
        k = (r["series"], r["chapter"].split("_")[1], r["page"])
        if k in seen: continue
        seen.add(k); uniq.append(r)
    rows = uniq
    # bonus / extra / omake chapters are not story pages (seen by eye: bookstore comics, covers, café books)
    import re as _re
    bonus = _re.compile(r"bonus|extras?\b|omake|afterword|picture book|cafe book|comic tribute|special thanks", _re.I)
    rows = [r for r in rows if not bonus.search(r.get("title") or "")]
    pages = [r for r in rows if usable(r)]
    for r in pages: r["dyn"] = dyn_score(r)
    ds = sorted(r["dyn"] for r in pages)
    out, rej = [], 0
    for r in pages:
        e = round(10 * bisect.bisect_left(ds, r["dyn"]) / max(1, len(ds)), 2)
        t = template(r, e)
        if t: out.append(t)
        else: rej += 1
    return dict(version=1, count=len(out), rejected=rej, series=dict(collections.Counter(t["s"] for t in out)),
                by_n=dict(sorted(collections.Counter(t["n"] for t in out).items())), templates=out)


_POOL = None


def load_pool(path=None):
    global _POOL
    if _POOL is None or path:
        p = path or POOL_PATH
        op = gzip.open if p.endswith(".gz") else open
        with op(p, "rt", encoding="utf-8") as f: _POOL = json.load(f)
    return _POOL


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("analysis", nargs="+"); ap.add_argument("--out", default=POOL_PATH)
    a = ap.parse_args(argv)
    rows = [json.loads(l) for f in a.analysis for l in open(f, encoding="utf-8") if l.strip()]
    pool = build(rows)
    with gzip.open(a.out, "wt", encoding="utf-8") as f: json.dump(pool, f, separators=(",", ":"))
    print(f"pool: {pool['count']} templates ({pool['rejected']} rejected) {pool['series']} by n {pool['by_n']} -> {a.out}")


if __name__ == "__main__":
    main()
