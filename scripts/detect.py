# -*- coding: utf-8 -*-
"""Excelsior detector: deterministic page and chapter checks over a storyboard plan.

Reads a mangaforge plan (pages[].layout + pages[].beats) or a bare beats file (pages[].panels with art notes)
and reports craft, shot-language, lettering, pacing and "AI manga" tells, each tied to the reference library's
numbers (MANGA COMPOSITION STANDARD v2). Geometry rules need a planned layout; story rules run on beats alone.

usage: python3 detect.py [--json] [--stats] [--root DIR] PLAN.json [PLAN2.json ...]
exit: 0 clean · 2 findings · 1 error
"""
import argparse, collections, json, math, os, statistics, sys
from _common import (load_plan, classify_shot, angle_of, words, series_config, project_root, state, emit)

try:
    from mangaforge.layout import load_model, SIZE_WEIGHT
    MODEL = load_model()
except Exception:                                    # detector still runs without the model
    MODEL, SIZE_WEIGHT = None, {"splash": 9, "big": 5, "wide": 3, "med": 1.6, "close": 1.0, "insert": 0.6}

G = (MODEL or {}).get("global", {})
REF = dict(
    ppp_p50=G.get("panels_per_page_q", {}).get("p50", 4), ppp_p90=G.get("panels_per_page_q", {}).get("p90", 6),
    contrast_p25=G.get("size_contrast_q", {}).get("p25", 2.9), contrast_p50=G.get("size_contrast_q", {}).get("p50", 5.1),
    run_p90=(MODEL or {}).get("rhythm", {}).get("longest_same_density_run_q", {}).get("p90", 8),
    splash_rate=G.get("splash_rate", 0.09), slant_rate=G.get("slant_page_rate", 0.23), inset_rate=G.get("inset_page_rate", 0.04),
    shots=dict(MS=.27, WS=.20, MCU=.17, FS=.14, CU=.11, INS=.06, EWS=.03, ECU=.02),
    angles=dict(eye=.56, low=.15, high=.14, dutch=.10, ots=.04),
)

# ---------------------------------------------------------------- rule registry
RULES = {
 # craft (mechanics the reference library agrees on)
 "craft-equal-boxes":     ("craft", "P2", "Panels are near-equal in size ({v}× biggest/smallest; library median {ref}×).", "Let one panel dominate: about 4–5× the smallest. Give the size to the beat with the most weight."),
 "craft-even-split":      ("craft", "P3", "Two panels share a row at a {v} split.", "Split about 60/40; the wider side goes to the heavier beat."),
 "craft-peak-not-biggest":("craft", "P1", "The heaviest beat ({v}) is not the largest panel on an {beat} page.", "Promote the peak panel to the biggest frame; step the setup panels down ('quick cuts, then one big swing')."),
 "craft-end-light":       ("craft", "P2", "The page ends on an {beat} but the bottom tier is not the tallest.", "End heavy: give the last tier the most height so the turn lands on the biggest image."),
 "craft-overcrowded":     ("craft", "P1", "{v} panels on one page (library p90 is {ref}).", "Split the page or merge beats; 7+ only for rapid exchanges."),
 "craft-density-plateau": ("craft", "P2", "{v} pages in a row at the same panel density (library p90 run is {ref}).", "Change density every page or two: open one page up, tighten the next."),
 "craft-flat-loud":       ("craft", "P2", "Loud page (energy {v}) with no slant, bleed or frame-break.", "Add one: slant a tier boundary 5–9°, bleed the heavy panel, or let the subject cross a border."),
 "craft-gutter-order":    ("craft", "P3", "Gutters between tiers are not wider than gutters within a row.", "Widen tier gutters to ~1.45× the in-row gutter so rows read as rows."),
 "craft-middle-splash":   ("pacing", "P3", "{v} single-panel pages in the middle of the chapter.", "Open big, close big: keep the middle lean with one or two big moments."),
 "craft-weak-ending":     ("pacing", "P1", "The chapter's last page does not hook ({v}).", "End on a big image plus a small wrong detail, or a reveal that lands on the final page."),
 "craft-reveal-parity":   ("pacing", "P2", "Reveal on page {v} lands where the reader can already see it (print: reveals belong on {ref} pages, after a turn).", "Move the reveal by one page, or end the previous page on the tease so the turn does the work."),
 "craft-inset-overuse":   ("craft", "P3", "Insets on {v} of pages (library {ref}).", "Insets land because they are rare; keep them as seasoning."),
 "craft-borderless-overuse": ("craft", "P3", "{v} borderless beats in scene {scene}.", "Take the frame away once per scene, for the most tender or charged beat."),
 "craft-slant-calm":      ("craft", "P3", "Slanted cuts on a {beat} page.", "Keep calm and talk pages rectangular so the slant still means speed (unless slant is the series signature)."),
 # shot language
 "shot-no-establish":     ("shot", "P2", "Scene {scene} opens without a wide or full shot (first panels: {v}).", "Place the reader: open on WS/EWS/FS, or deliberately tease small and pay the wide off within the page."),
 "shot-talking-heads":    ("shot", "P2", "{v} dialogue panels in a row framed CU/MCU/ECU.", "Break the run with a medium two-shot or a wide that shows where they stand."),
 "shot-monotone-page":    ("shot", "P3", "Every panel on the page is {v}.", "Mix scales on the page; the jump in scale carries feeling without a word."),
 "shot-insert-run":       ("shot", "P3", "{v} inserts in a row.", "Inserts are for props; return to a person between them."),
 "shot-wide-cramped":     ("shot", "P2", "{v} shot squeezed into {ref} of the page.", "Big panels get the wide shots; give this one room or tighten the framing."),
 "shot-dutch-calm":       ("shot", "P3", "Dutch angle on a calm page (energy {v}).", "Save the tilt for loud pages; use low/high angles for power and vulnerability."),
 "shot-no-pullback":      ("shot", "P3", "Only {v} of pages end on a wide or full shot (library ~43%).", "Step the camera back on the last panel more often as the page turns."),
 # lettering
 "letter-balloon-long":   ("lettering", "P2", "Balloon of {v} words (limit {ref}).", "Split it across two balloons or two panels; cut to the line that carries the beat."),
 "letter-panel-dense":    ("lettering", "P2", "{v} words in one panel (limit {ref}).", "Move lines to an adjacent panel or a narrow talk tier."),
 "letter-balloon-count":  ("lettering", "P3", "{v} balloons in one panel (limit {ref}).", "Fewer, better-placed balloons; reading order gets ambiguous past three."),
 "letter-small-panel":    ("lettering", "P2", "{v} words in a panel that is {ref} of the page.", "Small panels hold a word or a reaction; give the dialogue a bigger frame."),
 "letter-caption-stack":  ("lettering", "P3", "{v} captions stacked in one panel.", "Spread narration across the beat or let one picture carry it."),
 "letter-impact-silent":  ("lettering", "P3", "Impact page with no sound effect.", "Letter the hit; SFX is part of the picture (or make the silence deliberate and say so in the note)."),
 # AI-manga tells (chapter-level)
 "slop-equal-grid":       ("slop", "P1", "{v} of multi-panel pages are near-equal grids.", "The storyboard-grid tell. Re-plan with reference-inspired layouts (inspire.py) so pages borrow real geometry."),
 "slop-face-parade":      ("slop", "P1", "{v} of character panels are close-ups (library ~30%).", "Build pages on medium shots; spend close-ups on reactions."),
 "slop-eye-level":        ("slop", "P2", "{v} of panels at eye level (library ~56%).", "Use low and high angles for power and vulnerability."),
 "slop-dutch-spam":       ("slop", "P2", "{v} of panels are dutch (library ~10%).", "A tilt everywhere is a tilt nowhere."),
 "slop-splash-inflation": ("slop", "P2", "{v} of pages are single-panel (library {ref}).", "Splashes are spent, not sprinkled; fold weaker ones into multi-panel pages."),
 "slop-speedlines":       ("slop", "P3", "Speed lines named in {v} of panels.", "Motion comes from staging and cuts first; keep speed lines for the swing."),
 "slop-centered":         ("slop", "P3", "{v} of panels put the subject dead centre.", "Place subjects on thirds and leave the opposite cell for lettering."),
}
SEV_W = {"P0": 25, "P1": 8, "P2": 3, "P3": 1}


def _f(rule, page=None, panel=None, file=None, **kw):
    fam, sev, msg, fix = RULES[rule]
    kw.setdefault("v", ""); kw.setdefault("ref", ""); kw.setdefault("beat", ""); kw.setdefault("scene", "")
    return dict(rule=rule, family=fam, severity=kw.pop("severity", sev), page=page, panel=panel, file=file,
                message=msg.format(**kw), fix=fix)


def _slanted(poly):
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        a = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 90
        if min(a, 90 - a) > 2.5:
            return True
    return False


def _density(n):
    return "L" if n <= 2 else ("M" if n <= 5 else "H")


def check(path, cfg):
    raw, pages = load_plan(path)
    F = []; fname = os.path.basename(path)
    stats = collections.Counter(); shots = collections.Counter(); angles = collections.Counter()
    contrasts, ppp = [], []
    prev_scene = None; th_run = 0; ins_run = 0
    borderless = collections.Counter(); ends_wide = 0; centred = 0; npanels = 0; speed = 0
    n = len(pages)
    for idx, pg in enumerate(pages):
        no, beat, energy = pg["no"], pg["beat"], float(pg["energy"] or 5)
        P = pg["panels"]; npanels += len(P)
        L = pg["layout"]
        main = [p for p in P if not (p.get("geo") or {}).get("inset") and not p.get("inset")]
        ppp.append(len(main))
        cls = [classify_shot(p) for p in P]
        for p, c in zip(P, cls):
            shots[c] += 1; angles[angle_of(p)] += 1
            if "speed line" in (p.get("art") or "").lower(): speed += 1
            if p.get("borderless"): borderless[pg["scene"] or "?"] += 1
        # ---- geometry
        if L:
            geo = [p["geo"] for p in main if p.get("geo")]
            if len(geo) > 1:
                areas = [g["area_share"] for g in geo]
                c = max(areas) / max(min(areas), 1e-6); contrasts.append(c)
                if c < 1.5: F.append(_f("craft-equal-boxes", no, file=fname, v=f"{c:.1f}", ref=f"{REF['contrast_p50']:.1f}", severity="P1"))
                elif c < 2.0: F.append(_f("craft-equal-boxes", no, file=fname, v=f"{c:.1f}", ref=f"{REF['contrast_p50']:.1f}"))
                # even split inside a tier
                tiers = collections.defaultdict(list)
                for g in geo: tiers[g.get("tier", 0)].append(g)
                for t, row in tiers.items():
                    if len(row) == 2:
                        w = [r["bbox"][2] for r in row]; s = w[0] / (w[0] + w[1])
                        if 0.46 <= s <= 0.54 and abs(row[0]["bbox"][3] - row[1]["bbox"][3]) < 0.3:
                            F.append(_f("craft-even-split", no, file=fname, v=f"{round(s*100)}/{round((1-s)*100)}"))
                # peak beat gets the biggest frame
                if beat in ("impact", "reveal"):
                    ranked = sorted(main, key=lambda p: -SIZE_WEIGHT.get(p.get("size", "med"), 1.6))
                    heavy = ranked[0]
                    if SIZE_WEIGHT.get(heavy.get("size"), 1.6) > SIZE_WEIGHT.get(ranked[1].get("size"), 1.6) and heavy.get("geo"):
                        if heavy["geo"]["area_share"] + 1e-6 < max(areas):
                            F.append(_f("craft-peak-not-biggest", no, heavy["id"], fname, v=heavy["id"], beat=beat))
                    hs = collections.defaultdict(float)
                    for g in geo: hs[g.get("tier", 0)] = max(hs[g.get("tier", 0)], g["bbox"][3])
                    if len(hs) >= 2 and hs[max(hs)] + 0.05 < max(hs.values()) and idx == n - 1:
                        F.append(_f("craft-end-light", no, file=fname, beat=beat))
            if len(main) > 8 or (len(main) >= 7 and beat not in ("build", "rapid", "talk", "comedy")):
                F.append(_f("craft-overcrowded", no, file=fname, v=len(main), ref=int(REF["ppp_p90"]), severity="P1" if len(main) > 8 else "P3"))
            slant = any(_slanted(g["poly"]) for g in (x["geo"] for x in P if x.get("geo")))
            bleed = any(g.get("bleed") for g in (x["geo"] for x in P if x.get("geo")))
            brk = any((x.get("geo") or {}).get("breakout") or x.get("breakout") for x in P)
            stats["slant"] += slant; stats["bleed"] += bleed; stats["inset"] += any((x.get("geo") or {}).get("inset") for x in P)
            if energy >= 7 and not (slant or bleed or brk):
                F.append(_f("craft-flat-loud", no, file=fname, v=energy))
            if slant and beat in ("calm", "pause") and not cfg["signature_slant"]:
                F.append(_f("craft-slant-calm", no, file=fname, beat=beat))
            gi = L.get("gutter_in") or {}
            if len(set(g.get("tier", 0) for g in geo)) > 1 and gi and gi.get("between_tiers", 1) <= gi.get("within_tier", 0):
                F.append(_f("craft-gutter-order", no, file=fname))
            for p, c in zip(P, cls):
                g = p.get("geo")
                if g and c in ("WS", "EWS") and g["area_share"] < 0.10:
                    F.append(_f("shot-wide-cramped", no, p["id"], fname, v=c, ref=f"{g['area_share']:.0%}"))
                if g and p.get("lettering"):
                    wd = sum(words(b.get("text")) for b in p["lettering"] if b.get("kind") != "sfx")
                    if g["area_share"] < 0.06 and wd > 12:
                        F.append(_f("letter-small-panel", no, p["id"], fname, v=wd, ref=f"{g['area_share']:.0%}"))
                if g and g.get("subject") == "MC": centred += 1
        # ---- story / shot
        if pg["scene"] and pg["scene"] != prev_scene:
            first = cls[:2]
            if not any(c in ("EWS", "WS", "FS") for c in first) and not any(c in ("EWS", "WS", "FS") for c in cls):
                F.append(_f("shot-no-establish", no, file=fname, scene=pg["scene"], v="/".join(first),
                            severity="P3" if beat in ("dread", "pause") or idx == 0 else "P2"))
        prev_scene = pg["scene"] or prev_scene
        if len(cls) >= 3 and len(set(cls)) == 1:
            F.append(_f("shot-monotone-page", no, file=fname, v=cls[0]))
        for p, c in zip(P, cls):
            talk = any(b.get("kind") == "dialogue" for b in p.get("lettering", []))
            if talk and c in ("CU", "MCU", "ECU"):
                th_run += 1
                if th_run == 5: F.append(_f("shot-talking-heads", no, p["id"], fname, v="5+"))
            elif talk or c in ("MS", "WS", "FS", "EWS"):
                th_run = 0
            ins_run = ins_run + 1 if c == "INS" else 0
            if ins_run == 3: F.append(_f("shot-insert-run", no, p["id"], fname, v=3))
            if angle_of(p) == "dutch" and energy < 5:
                F.append(_f("shot-dutch-calm", no, p["id"], fname, v=energy))
            # lettering
            lets = [b for b in p.get("lettering", []) if b.get("kind") != "sfx"]
            for b in lets:
                w = words(b.get("text"))
                if w > cfg["max_words_balloon"]:
                    F.append(_f("letter-balloon-long", no, p["id"], fname, v=w, ref=cfg["max_words_balloon"]))
            tw = sum(words(b.get("text")) for b in lets)
            if tw > cfg["max_words_panel"]: F.append(_f("letter-panel-dense", no, p["id"], fname, v=tw, ref=cfg["max_words_panel"]))
            if len(lets) > cfg["max_balloons_panel"]: F.append(_f("letter-balloon-count", no, p["id"], fname, v=len(lets), ref=cfg["max_balloons_panel"]))
            caps = sum(1 for b in lets if b.get("kind") == "caption")
            if caps >= 3: F.append(_f("letter-caption-stack", no, p["id"], fname, v=caps))
        if beat == "impact" and not any(b.get("kind") == "sfx" for p in P for b in p.get("lettering", [])):
            F.append(_f("letter-impact-silent", no, file=fname))
        if cls and cls[-1] in ("WS", "EWS", "FS"): ends_wide += 1
        if cfg["format"] == "print" and beat == "reveal" and len(main) <= 2:
            want = 0 if cfg["turn_reveals"] == "even" else 1
            if no % 2 != want and idx > 0:
                F.append(_f("craft-reveal-parity", no, file=fname, v=no, ref=cfg["turn_reveals"]))
    # ---- chapter level
    cl = [_density(x) for x in ppp]; run = best = 1
    for a, b in zip(cl, cl[1:]):
        run = run + 1 if a == b else 1; best = max(best, run)
    if best > REF["run_p90"]: F.append(_f("craft-density-plateau", file=fname, v=best, ref=int(REF["run_p90"])))
    elif best > 5: F.append(_f("craft-density-plateau", file=fname, v=best, ref=int(REF["run_p90"]), severity="P3"))
    if n >= 10:
        mid = ppp[int(n * .2): int(n * .8)]
        sp = sum(1 for x in mid if x == 1)
        if sp > max(2, round(len(mid) * .12)): F.append(_f("craft-middle-splash", file=fname, v=sp))
        last = pages[-1]
        big = max(((p.get("geo") or {}).get("area_share", 0) for p in last["panels"]), default=0)
        if last["beat"] not in ("reveal", "impact", "dread", "hook") and big < 0.35:
            F.append(_f("craft-weak-ending", last["no"], file=fname, v=f"{last['beat']}, biggest panel {big:.0%}"))
        if pages[0]["layout"]:
            ir = stats["inset"] / n
            if ir > max(0.10, REF["inset_rate"] * 2.5): F.append(_f("craft-inset-overuse", file=fname, v=f"{ir:.0%}", ref=f"{REF['inset_rate']:.0%}"))
            multi = [c for c in contrasts]
            eq = sum(1 for c in multi if c < 1.6) / max(len(multi), 1)
            if eq >= 0.4: F.append(_f("slop-equal-grid", file=fname, v=f"{eq:.0%}"))
            if centred / max(npanels, 1) > 0.8: F.append(_f("slop-centered", file=fname, v=f"{centred/npanels:.0%}"))
        if ends_wide / n < 0.10: F.append(_f("shot-no-pullback", file=fname, v=f"{ends_wide/n:.0%}"))
        sr = sum(1 for x in ppp if x == 1) / n
        if sr > max(0.22, REF["splash_rate"] * 2.5): F.append(_f("slop-splash-inflation", file=fname, v=f"{sr:.0%}", ref=f"{REF['splash_rate']:.0%}"))
    for sc, k in borderless.items():
        if k > cfg["borderless_per_scene"]: F.append(_f("craft-borderless-overuse", file=fname, v=k, scene=sc))
    chars = sum(v for k, v in shots.items() if k != "INS")
    if chars >= 20:
        cu = (shots["CU"] + shots["MCU"] + shots["ECU"]) / chars
        if cu > 0.55: F.append(_f("slop-face-parade", file=fname, v=f"{cu:.0%}"))
    tot = sum(angles.values())
    if tot >= 20:
        if angles["eye"] / tot > 0.85: F.append(_f("slop-eye-level", file=fname, v=f"{angles['eye']/tot:.0%}"))
        if angles["dutch"] / tot > 0.20: F.append(_f("slop-dutch-spam", file=fname, v=f"{angles['dutch']/tot:.0%}"))
    if npanels >= 20 and speed / npanels > 0.3: F.append(_f("slop-speedlines", file=fname, v=f"{speed/npanels:.0%}"))
    st = dict(file=fname, pages=n, panels=npanels, panels_per_page_median=statistics.median(ppp) if ppp else 0,
              ref_panels_per_page=REF["ppp_p50"],
              size_contrast_median=round(statistics.median(contrasts), 2) if contrasts else None, ref_size_contrast=round(REF["contrast_p50"], 2),
              slant_page_rate=round(stats["slant"] / n, 2) if n and pages[0]["layout"] else None, ref_slant_rate=round(REF["slant_rate"], 2),
              longest_same_density_run=best, shots={k: round(shots[k] / max(sum(shots.values()), 1), 3) for k in shots},
              ref_shots=REF["shots"], angles={k: round(v / max(tot, 1), 3) for k, v in angles.items()}, ref_angles=REF["angles"])
    return F, st


def ignored(root):
    p = state(root, "config.json")
    try: c = json.load(open(p))
    except Exception: return set(), set()
    return set(c.get("ignore_rules", [])), set(c.get("ignore_files", []))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plans", nargs="+"); ap.add_argument("--json", action="store_true"); ap.add_argument("--stats", action="store_true")
    ap.add_argument("--root"); ap.add_argument("--rules", action="store_true", help="list the rule registry and exit")
    a = ap.parse_args(argv)
    if a.rules:
        emit({k: dict(family=v[0], severity=v[1], message=v[2], fix=v[3]) for k, v in RULES.items()}); return 0
    root = a.root or project_root(os.path.dirname(os.path.abspath(a.plans[0])))
    cfg = series_config(root); ig_rules, ig_files = ignored(root)
    allF, allS = [], []
    for p in a.plans:
        if os.path.basename(p) in ig_files: continue
        try:
            F, S = check(p, cfg)
        except Exception as e:
            print(f"detect: cannot read {p}: {e}", file=sys.stderr); return 1
        allF += [f for f in F if f["rule"] not in ig_rules]; allS.append(S)
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    allF.sort(key=lambda f: (order[f["severity"]], f["file"] or "", f["page"] or 0))
    sev = collections.Counter(f["severity"] for f in allF)
    # penalty per 20 pages, so a 60-page chapter is not punished three times for its length; P0 always caps at 40
    npages = max(sum(x["pages"] for x in allS), 1)
    score = max(0, round(100 - sum(SEV_W[k] * v for k, v in sev.items()) * 20 / max(npages, 20)))
    if sev["P0"]: score = min(score, 40)
    res = dict(tool="excelsior-detect", config=cfg, score=score, counts=dict(sev), by_rule=dict(collections.Counter(f["rule"] for f in allF)),
               findings=allF, stats=allS)
    if a.json:
        emit(res)
    else:
        print(f"Excelsior detector · score {score}/100 · " + ", ".join(f"{k}:{sev[k]}" for k in ("P0", "P1", "P2", "P3") if sev[k]))
        for f in allF:
            loc = f"{f['file']}" + (f" p{f['page']}" if f['page'] else "") + (f".{f['panel']}" if f['panel'] and '.' not in str(f['panel']) else (f" [{f['panel']}]" if f['panel'] else ""))
            print(f"  {f['severity']} {f['rule']:<24} {loc:<28} {f['message']}\n       → {f['fix']}")
        if a.stats:
            for s in allS: print(json.dumps(s, ensure_ascii=False))
    return 2 if allF else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
