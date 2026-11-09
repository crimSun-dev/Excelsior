# -*- coding: utf-8 -*-
"""Learn a composition model from analysis.jsonl (output of mangaforge.analyze).

The model holds statistics and layout structures only (numbers, no artwork):
  - page-level distributions (panels per page, size contrast, gutters, slants, frame-break rate, ink balance)
  - tier structures ("1|2|1" = one panel, then two, then one) with learned tier heights and widths
  - chapter rhythm (how panel density changes page to page, where splash pages fall)
  - vertical-scroll pacing (block heights and gap lengths) for webtoon mode
    python -m mangaforge.learn analysis.jsonl --out mangaforge/model/model.json
"""
import argparse, collections, json, math
import numpy as np


def _q(v, ps=(10, 25, 50, 75, 90)):
    v = [x for x in v if x is not None]
    if not v: return None
    return {f"p{p}": round(float(np.percentile(v, p)), 4) for p in ps}


def clean(p):
    return p["nv"] == 4 and p["solidity"] > 0.95


def true_slant(p):
    return clean(p) and 2.5 < p["slant"] < 30


def tiers(r):
    ps = sorted(r["panels"], key=lambda p: p["bbox"][1] + p["bbox"][3] / 2)
    T = []
    for p in ps:
        y0, y1 = p["bbox"][1], p["bbox"][1] + p["bbox"][3]
        for t in T:
            ov = min(y1, t["y1"]) - max(y0, t["y0"])
            if ov > 0.5 * min(y1 - y0, t["y1"] - t["y0"]):
                t["ps"].append(p); t["y0"] = min(t["y0"], y0); t["y1"] = max(t["y1"], y1); break
        else:
            T.append(dict(y0=y0, y1=y1, ps=[p]))
    T.sort(key=lambda t: t["y0"])
    for t in T: t["ps"].sort(key=lambda p: p["bbox"][0])
    return T


def dyn_score(r):
    ar = [p["area"] for p in r["panels"]] or [1]
    contrast = math.log(max(ar) / min(ar)) if len(ar) > 1 else 0
    ts = sum(1 for p in r["panels"] if true_slant(p))
    return 0.9 * contrast + 0.7 * min(ts, 4) + 0.35 * min(r["breaks"], 6) + 0.8 * (r["insets"] > 0) + \
        0.6 * min(r["n"], 7) / 7 + 2.4 * r["ink"]["black"]


def usable(r):
    if r.get("strip") or r.get("error") or r.get("spread"): return False
    if not (1 <= r["n"] <= 9) or r["coverage"] < 0.6: return False
    # credit / promo pages are colour on otherwise monochrome series
    if r["ink"]["sat"] > 0.12 and r.get("colour_series") is not True: return False
    return True


def learn(rows, colour_series=(), cap=700):
    # a series counts as colour when most of its pages are saturated (then colour pages are not credits)
    sat = collections.defaultdict(list)
    for r in rows:
        if not r.get("strip") and not r.get("error"): sat[r["series"]].append(r["ink"]["sat"])
    auto = {s for s, v in sat.items() if np.median(v) > 0.12}
    for r in rows:
        if r.get("series") in colour_series or r.get("series") in auto: r["colour_series"] = True
    pages = [r for r in rows if usable(r)]
    strips = [r for r in rows if r.get("strip")]
    for r in pages: r["dyn"] = dyn_score(r)
    dyn_sorted = sorted(r["dyn"] for r in pages)

    def energy(d):  # percentile mapped to 0..10
        import bisect
        return round(10 * bisect.bisect_left(dyn_sorted, d) / max(1, len(dyn_sorted)), 2)
    for r in pages: r["energy"] = energy(r["dyn"])

    def page_stats(P):
        n = [r["n"] for r in P]
        ar = [p["area"] for r in P for p in r["panels"]]
        con = [max(p["area"] for p in r["panels"]) / min(p["area"] for p in r["panels"]) for r in P if r["n"] > 1]
        deg = [p["slant"] for r in P for p in r["panels"] if true_slant(p)]
        return dict(pages=len(P),
                    panels_per_page=dict(collections.Counter(n)), panels_per_page_q=_q(n),
                    panel_area_q=_q(ar), size_contrast_q=_q(con),
                    slant_page_rate=round(float(np.mean([any(true_slant(p) for p in r["panels"]) for r in P])), 3),
                    slant_deg_q=_q(deg),
                    bridge_page_rate=round(float(np.mean([r["breaks"] > 0 for r in P])), 3),
                    bridges_per_page_q=_q([r["breaks"] for r in P]),
                    bleed_page_rate=round(float(np.mean([r["bleeds"] > 0 for r in P])), 3),
                    inset_page_rate=round(float(np.mean([r["insets"] > 0 for r in P])), 3),
                    splash_rate=round(float(np.mean([r["n"] == 1 for r in P])), 3),
                    gutter_q=_q([r["gutter"] for r in P if r["gutter"] > 0]),
                    margin_q=_q([r["margin"] for r in P]),
                    ink_black_q=_q([r["ink"]["black"] for r in P]), ink_white_q=_q([r["ink"]["white"] for r in P]),
                    dark_page_rate=round(float(np.mean([r["dark"] for r in P])), 3))

    by = collections.defaultdict(list)
    for r in pages: by[r["series"]].append(r)
    # series-balanced view: no single series (e.g. a 500-chapter run) dominates the house numbers
    import random as _r
    rng = _r.Random(0); bal = []
    for s_, v in sorted(by.items()):
        bal += v if len(v) <= cap else rng.sample(v, cap)
    model = dict(version=2, pages=len(pages), balanced_pages=len(bal), balance_cap=cap, strips=len(strips), series=sorted(by),
                 global_=page_stats(bal), global_pooled=page_stats(pages),
                 by_series={s: page_stats(v) for s, v in by.items()})
    pages_all, pages = pages, bal

    # ---- structures
    S = collections.defaultdict(list)
    for r in pages:
        T = tiers(r)
        if len(T) > 5: continue
        sig = "|".join(str(len(t["ps"])) for t in T)
        H = sum(t["y1"] - t["y0"] for t in T)
        S[sig].append(dict(h=[(t["y1"] - t["y0"]) / H for t in T],
                           w=[[p["bbox"][2] / sum(q["bbox"][2] for q in t["ps"]) for p in t["ps"]] for t in T],
                           big=[max(range(len(t["ps"])), key=lambda i: t["ps"][i]["area"]) for t in T],
                           slant=any(true_slant(p) for p in r["panels"]),
                           deg=[p["slant"] for p in r["panels"] if true_slant(p)],
                           bridge=r["breaks"] > 0, energy=r["energy"], series=r["series"]))
    structures = []
    tot = sum(len(v) for v in S.values())
    for sig, ex in sorted(S.items(), key=lambda kv: -len(kv[1])):
        if len(ex) < 6: continue
        k = len(ex[0]["h"])
        hs = np.array([e["h"] for e in ex])
        widths = []
        for ti in range(k):
            m = len(ex[0]["w"][ti])
            W = np.array([e["w"][ti] for e in ex if len(e["w"][ti]) == m])
            # order-free: sort widths descending to learn the split, remember where the widest sits
            Ws = -np.sort(-W, axis=1)
            pos = collections.Counter(e["big"][ti] for e in ex)
            widths.append(dict(sorted_median=[round(float(x), 3) for x in np.median(Ws, axis=0)],
                               widest_pos=[round(pos[i] / len(ex), 3) for i in range(m)]))
        structures.append(dict(sig=sig, n=sum(int(x) for x in sig.split("|")), count=len(ex), share=round(len(ex) / tot, 4),
                               tier_h_median=[round(float(x), 3) for x in np.median(hs, axis=0)],
                               tier_h_iqr=[[round(float(a), 3), round(float(b), 3)] for a, b in zip(np.percentile(hs, 25, axis=0), np.percentile(hs, 75, axis=0))],
                               tier_w=widths,
                               slant_rate=round(float(np.mean([e["slant"] for e in ex])), 3),
                               slant_deg_median=round(float(np.median([d for e in ex for d in e["deg"]])), 2) if any(e["deg"] for e in ex) else None,
                               bridge_rate=round(float(np.mean([e["bridge"] for e in ex])), 3),
                               energy_q=_q([e["energy"] for e in ex], (25, 50, 75)),
                               series=dict(collections.Counter(e["series"] for e in ex).most_common())))
    model["structures"] = structures

    # ---- chapter rhythm
    ch = collections.defaultdict(list)
    for r in rows:
        if r.get("strip") or r.get("error"): continue
        ch[r["chapter"]].append(r)
    deltas, runs, pos = [], [], [0] * 10
    for c, v in ch.items():
        v.sort(key=lambda r: r["page"])
        n = [1 if r.get("spread") else r["n"] for r in v if r["n"] > 0 or r.get("spread")]
        if len(n) < 6: continue
        deltas += list(np.abs(np.diff(n)))
        cls = ["L" if x <= 2 else ("M" if x <= 5 else "H") for x in n]
        best = cur = 1
        for a, b in zip(cls, cls[1:]):
            cur = cur + 1 if a == b else 1; best = max(best, cur)
        runs.append(best)
        for i, x in enumerate(n):
            if x == 1: pos[min(9, int(10 * i / len(n)))] += 1
    model["rhythm"] = dict(chapters=len(runs), page_delta_q=_q(deltas), longest_same_density_run_q=_q(runs),
                           splash_by_decile=pos)
    # ---- scroll pacing (webtoon strips)
    if strips:
        model["scroll"] = dict(strips=len(strips),
                               block_h_over_w_q=_q([b for r in strips for b in r["blocks"]]),
                               gap_over_w_q=_q([g for r in strips for g in r["gaps"]]),
                               dark_gap_rate=round(float(np.mean([d for r in strips for d in r["gap_dark"]] or [0])), 3))
    model["energy_calibration"] = _q(dyn_sorted, (10, 25, 50, 75, 90))
    return model


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("analysis"); ap.add_argument("--out", default="model.json")
    ap.add_argument("--colour-series", nargs="*", default=[], help="force these series to count as colour (auto-detected otherwise)")
    a = ap.parse_args(argv)
    rows = [json.loads(l) for l in open(a.analysis, encoding="utf-8") if l.strip()]
    m = learn(rows, tuple(a.colour_series))
    m["global"] = m.pop("global_")
    json.dump(m, open(a.out, "w", encoding="utf-8"), indent=1)
    print(f"model: {m['pages']} pages, {len(m['structures'])} structures -> {a.out}")


if __name__ == "__main__":
    main()
