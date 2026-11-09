# -*- coding: utf-8 -*-
"""Reference-inspired layout variants for one page (the engine behind `layout` and `live`).

Draws a weighted random handful of real reference pages with the same panel count and similar energy, adapts
their panel geometry to your trim (mirroring right-to-left pages), and returns the best k. With --enforce-peak,
only variants whose largest panel holds the page's heaviest beat survive (the fix for craft-peak-not-biggest).

usage: python3 inspire_page.py PLAN.json --page 9 [--k 3] [--enforce-peak] [--seed N] [--series DB,HNK]
       python3 inspire_page.py PLAN.json --page 9 --apply 0 [--out NEW_PLAN.json]   (swap in variant 0)
       python3 inspire_page.py --sizes wide,med,med,big --energy 7 --beat impact      (no plan needed)
"""
import argparse, json, os, shutil, sys
from _common import emit
from mangaforge.layout import load_model, PageSpec, PanelSpec, SIZE_WEIGHT
from mangaforge.inspire import inspire
from mangaforge.plan import page_spec, page_from_layout


def peak_ok(L, beat_panels):
    main = [p for p in beat_panels if not p.get("inset")]
    if len(main) < 2: return True
    ranked = sorted(main, key=lambda p: -SIZE_WEIGHT.get(p.get("size", "med"), 1.6))
    if SIZE_WEIGHT.get(ranked[0].get("size"), 1.6) <= SIZE_WEIGHT.get(ranked[1].get("size"), 1.6): return True
    by = {str(p["id"]): p for p in L["panels"] if not p["inset"]}
    hid = str(ranked[0]["id"])
    return hid in by and by[hid]["area_share"] >= max(p["area_share"] for p in by.values()) - 1e-6


def summary(L):
    return dict(structure=L["structure"], inspired_by=L.get("inspired_by"), score=L.get("score"), inspire_score=L.get("inspire_score"),
                panels=[dict(id=p["id"], size=p["size"], area=round(p["area_share"], 3), aspect=p["aspect"], bleed=p["bleed"], inset=p["inset"])
                        for p in L["panels"]])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", nargs="?"); ap.add_argument("--page", type=int); ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--enforce-peak", action="store_true")
    ap.add_argument("--series", help="limit references to these series codes"); ap.add_argument("--apply", type=int)
    ap.add_argument("--out"); ap.add_argument("--sizes"); ap.add_argument("--energy", type=float, default=5); ap.add_argument("--beat", default="build")
    ap.add_argument("--rtl", action="store_true")
    a = ap.parse_args(argv)
    model = load_model(); series = a.series.split(",") if a.series else None
    if a.sizes:
        spec = PageSpec(panels=[PanelSpec(id=str(i + 1), size=s.strip().rstrip("*"), inset=s.strip().endswith("*")) for i, s in enumerate(a.sizes.split(","))],
                        energy=a.energy, beat=a.beat, reading="rtl" if a.rtl else "ltr", seed=a.seed)
        emit([summary(L) for L in inspire(spec, k=a.k, model=model, series=series)]); return 0
    plan = json.load(open(a.plan, encoding="utf-8"))
    idx = next(i for i, pg in enumerate(plan["pages"]) if pg["page"] == a.page)
    pg = plan["pages"][idx]; beats = pg["beats"]
    spec = page_spec(beats, plan.get("reading", "ltr"), seed=a.seed * 7919 + a.page)
    picks = []
    for attempt in range(6):
        spec.seed += attempt * 101
        for L in inspire(spec, k=max(a.k * 3, 8), handful=48, model=model, series=series):
            if a.enforce_peak and not peak_ok(L, beats["panels"]): continue
            if L.get("inspired_by", {}).get("key") not in {x.get("inspired_by", {}).get("key") for x in picks}: picks.append(L)
        if len(picks) >= a.k: break
    picks = sorted(picks, key=lambda L: -(L.get("inspire_score") or 0))[:a.k]
    if a.apply is None:
        emit(dict(page=a.page, beat=pg["beat"], current=summary(pg["layout"]), variants=[summary(L) for L in picks],
                  next="re-run with --apply <index> to swap a variant into the plan")); return 0
    if not picks: print("no variant satisfied the constraints", file=sys.stderr); return 1
    L = picks[a.apply]
    page_from_layout(plan, pg, L, model)
    out = a.out or a.plan
    if out == a.plan: shutil.copyfile(a.plan, a.plan + ".bak")
    json.dump(plan, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    emit(dict(applied=summary(L), written=out)); return 0


if __name__ == "__main__":
    sys.exit(main())
