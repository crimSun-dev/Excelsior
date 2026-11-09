# -*- coding: utf-8 -*-
"""Planner: story beats in, page layouts and per-panel image prompts out.

Input formats
  1. Simple beats JSON:
     {"style": "...", "cast": {"KKIRI": "..."},
      "pages": [{"energy": 7, "beat": "impact",
                 "panels": [{"id": "1", "size": "big", "shot": "what we see", "camera": "low angle, 24mm",
                             "light": "...", "acting": "...", "subject": "BC", "breakout": "top",
                             "lettering": [{"kind": "dialogue", "speaker": "KKIRI", "text": "..."}]}]}]}
  2. K-nity chapter export (CH01_pages.json / CH02_pages.json) — detected automatically.
Output: plan.json (layouts + prompts + lettering) and prompts.md (copy-paste for ChatGPT).
"""
import argparse, json, os, random
from .layout import PageSpec, PanelSpec, make_page, score_page, load_model
from .inspire import inspire, shot_hint

ANGLE = {"EYE": "eye-level shot", "LOW": "low-angle shot", "WORM": "worm's-eye view", "HIGH": "high-angle shot",
         "BIRD": "bird's-eye view straight down", "DUTCH": "dutch-angle (tilted) shot", "OTS": "over-the-shoulder shot",
         "PROF": "profile shot", "BACK": "shot from behind", "ECU": "extreme close-up", "SIL": "silhouette against the light",
         "FIX": "locked-off frontal frame"}
CELLNAME = {"T": "upper", "M": "middle", "B": "lower", "L": "left", "C": "centre", "R": "right"}
DEFAULT_STYLE = ("Japanese manga panel, black-and-white ink with screentone shading, confident brush line weight, "
                 "heavy spot blacks, clean white space, cinematic composition")
NEGATIVE = "No text, no letters, no speech bubbles, no captions, no panel borders, no frame, no watermark, no signature."
TONE_ENERGY = {"P": 8.5, "L": 4.0, "V": 3.0, "N": 5.0}


def cell_words(c):
    return f"{CELLNAME[c[0]]}-{CELLNAME[c[1]]}" if c != "MC" else "centre"


def build_prompt(panel, layout_panel, style, cast):
    shot = panel.get("shot") or panel.get("art") or ""
    for name, desc in (cast or {}).items():
        if name.lower() in shot.lower() and desc not in shot:
            shot += f" ({name}: {desc})"
    cam = panel.get("camera") or ANGLE.get(panel.get("angle", ""), "") or shot_hint(layout_panel.get("ref_shot"))
    if panel.get("lens"): cam = f"{cam}, {panel['lens']}" if cam else panel["lens"]
    parts = [style + ".", shot.rstrip(".") + "."]
    s_ = lambda t: str(t).strip().rstrip(".")
    if cam: parts.append(f"Camera: {s_(cam)}.")
    if panel.get("light"): parts.append(f"Lighting: {s_(panel['light'])}.")
    if panel.get("acting") or panel.get("face"): parts.append(f"Acting: {s_(panel.get('acting') or panel.get('face'))}.")
    lp = layout_panel
    parts.append(f"Composition: this image will be cropped into a {lp['aspect']:.2f}:1 panel; keep the main subject in the "
                 f"{cell_words(lp['subject'])} of the frame and inside the central 80%; leave the {cell_words(lp['lettering_zone'])} "
                 f"area simple (sky, wall, shadow or tone) for lettering.")
    if lp.get("breakout"):
        parts.append(f"The subject reaches toward the {lp['breakout']} edge of the frame (it will break out of the panel border); "
                     f"keep the silhouette clean against a plain background so it can be cut out.")
    parts.append(NEGATIVE)
    return " ".join(parts)


def knity_to_beats(ch):
    """Convert a K-nity chapter export into the simple beats format."""
    pages = []
    for pg in ch["pages"]:
        tones = [p.get("tone", "N") for p in pg["panels"]]
        es = [TONE_ENERGY.get(t, 5) for t in tones]
        energy = round(sum(es) / len(es) + 0.6 * (max(es) - sum(es) / len(es)), 2)
        sizes = [p["size"] for p in pg["panels"]]
        if pg["template"] == "V1": beat = "pause"
        elif "splash" in sizes: beat = "reveal"
        elif tones[-1] == "P": beat = "impact"
        elif all(t in ("L", "V") for t in tones): beat = "calm"
        else: beat = "build"
        panels = []
        for p in pg["panels"]:
            let = []
            for b in p.get("lettering", []):
                kind = {"dialogue": "dialogue", "thought_caption": "caption", "caption": "caption", "device_text": "caption"}[b["kind"]]
                let.append(dict(kind=kind, speaker=b.get("speaker"), text=b["text"]))
            for sfx in p.get("sfx", []):
                t = sfx.split("(")[0].strip().rstrip(".")
                if t and len(t.split()) <= 3 and len(t) <= 22: let.append(dict(kind="sfx", text=t))
            panels.append(dict(id=p["id"], size=p["size"], art=p["art"], angle=p["angle"], lens=p.get("lens"), light=p.get("light"),
                               face=p.get("face"), subject=p.get("subject_cell", "MC"), lettering=let,
                               inset=(p["size"] == "insert" and pg["template"] in ("SI", "SI2")),
                               breakout="top" if p["angle"] in ("WORM", "LOW") and p["size"] in ("big", "splash") else None))
        pages.append(dict(no=pg["no"], energy=energy, beat=beat, paper=pg.get("paper", "white"), panels=panels,
                          note=pg.get("note", ""), scene=pg.get("scene"), clock=pg.get("clock")))
    return dict(title=ch.get("title"), pages=pages)


def page_spec(pg, reading="ltr", seed=0):
    specs = [PanelSpec(id=str(p["id"]), size=p.get("size", "med"), bleed=p.get("bleed"), breakout=p.get("breakout"),
                       inset=bool(p.get("inset")), subject=p.get("subject", "MC")) for p in pg["panels"]]
    return PageSpec(panels=specs, energy=pg.get("energy", 5), beat=pg.get("beat", "build"), reading=reading, seed=seed)


def page_from_layout(plan_obj, pg_out, L, model=None):
    """Swap a planned page's layout (e.g. for another reference) and rebuild its prompts."""
    model = model or load_model()
    beats = pg_out["beats"]; by_id = {p["id"]: p for p in L["panels"]}
    pg_out["layout"] = L; pg_out["score"] = score_page(L, model); pg_out["inspired_by"] = L.get("inspired_by")
    pg_out["panels"] = [dict(id=str(p["id"]), prompt=build_prompt(p, by_id[str(p["id"])], plan_obj["style"], plan_obj.get("cast")),
                             size=by_id[str(p["id"])]["gen_size"], aspect=by_id[str(p["id"])]["aspect"],
                             subject=by_id[str(p["id"])]["subject"], lettering_zone=by_id[str(p["id"])]["lettering_zone"],
                             breakout=by_id[str(p["id"])].get("breakout"), ref_shot=by_id[str(p["id"])].get("ref_shot"),
                             lettering=p.get("lettering", [])) for p in beats["panels"]]
    return pg_out


def plan(beats, style=None, cast=None, variants=4, seed=0, reading="ltr", model=None, mode="inspire"):
    """mode: 'inspire' = adapt real reference pages (engine for splashes or when nothing fits),
    'engine' = learned-structure generator only, 'mix' = both compete on the same score."""
    model = model or load_model()
    used, recent = set(), []
    style = style or beats.get("style") or DEFAULT_STYLE
    cast = cast or beats.get("cast") or {}
    out_pages = []
    prev_sig = None
    for pi, pg in enumerate(beats["pages"]):
        specs = [PanelSpec(id=str(p["id"]), size=p.get("size", "med"), bleed=p.get("bleed"), breakout=p.get("breakout"),
                           inset=bool(p.get("inset")), subject=p.get("subject", "MC")) for p in pg["panels"]]
        best = None
        sp0 = PageSpec(panels=specs, energy=pg.get("energy", 5), beat=pg.get("beat", "build"), reading=reading,
                       seed=seed * 1000 + pi * 17)
        cands = []
        if mode in ("inspire", "mix"):
            for L in inspire(sp0, k=variants, model=model, exclude=used):
                cands.append((L, L["score"], 0.8 + 0.1 * L["inspire_score"]))
        if mode in ("engine", "mix") or not cands:
            for v in range(variants):
                sp = PageSpec(panels=specs, energy=sp0.energy, beat=sp0.beat, reading=reading, seed=sp0.seed + v)
                L = make_page(sp, model); L["source"] = "engine"
                cands.append((L, score_page(L, model), 0.1 * L["structure_share"] * 10))
        for L, sc, bonus in cands:
            q = -len(sc["notes"]) + (0.6 if L["structure"] != prev_sig else 0) + 0.15 * min(sc["size_contrast"], 9) / 9 + bonus
            code = (L.get("inspired_by") or {}).get("code")
            if code and code in recent: q -= 0.35        # spread the references across series
            if best is None or q > best[0]: best = (q, L, sc)
        _, L, sc = best; prev_sig = L["structure"]
        if L.get("inspired_by"):
            used.add(L["inspired_by"]["key"]); recent = (recent + [L["inspired_by"]["code"]])[-2:]
        by_id = {p["id"]: p for p in L["panels"]}
        panels = []
        for p in pg["panels"]:
            lp = by_id[str(p["id"])]
            panels.append(dict(id=str(p["id"]), prompt=build_prompt(p, lp, style, cast), size=lp["gen_size"], aspect=lp["aspect"],
                               subject=lp["subject"], lettering_zone=lp["lettering_zone"], breakout=lp.get("breakout"),
                               ref_shot=lp.get("ref_shot"), lettering=p.get("lettering", [])))
        out_pages.append(dict(page=pg.get("no", pi + 1), energy=L["energy"], beat=L["beat"], layout=L, score=sc, panels=panels,
                              note=pg.get("note", ""), inspired_by=L.get("inspired_by"), beats=pg))
    # chapter-level rhythm check against the corpus
    ns = [len(p["layout"]["panels"]) for p in out_pages]
    rq = model["rhythm"]["longest_same_density_run_q"]
    cls = ["L" if n <= 2 else ("M" if n <= 5 else "H") for n in ns]
    run = best_run = 1
    for a, b in zip(cls, cls[1:]):
        run = run + 1 if a == b else 1; best_run = max(best_run, run)
    gq = model["global"]["panels_per_page_q"]
    notes = []
    if ns and sorted(ns)[len(ns) // 2] < gq["p50"]:
        notes.append(f"median {sorted(ns)[len(ns)//2]} panels/page vs reference median {gq['p50']:.0f}: consider splitting some beats")
    if best_run > rq["p90"]:
        notes.append(f"{best_run} pages in a row with the same panel density (reference p90 = {rq['p90']:.0f}): vary the rhythm")
    return dict(title=beats.get("title"), style=style, cast=cast, reading=reading, pages=out_pages, rhythm=dict(panels_per_page=ns, longest_same_density_run=best_run, notes=notes))


def prompts_md(p):
    L = [f"# {p.get('title') or 'Manga plan'} · panel prompts", "",
         "Generate each image at the listed size, then save it as `<page>_<panel>.png` (e.g. `12_3.png`) in your panels folder.", ""]
    for pg in p["pages"]:
        L.append(f"## Page {pg['page']} · {pg['beat']} · energy {pg['energy']} · structure {pg['layout']['structure']}")
        r = pg.get("inspired_by")
        if r: L.append(f"_Layout inspired by {r['series']}, {r['chapter']}, page {r['page']} (panel shapes only)._")
        for x in pg["panels"]:
            L.append(f"**{pg['page']}_{x['id']}** · {x['size']} · crop {x['aspect']:.2f}:1")
            L.append(f"```\n{x['prompt']}\n```")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("beats"); ap.add_argument("--out", default="plan.json"); ap.add_argument("--style")
    ap.add_argument("--pages", help="range like 17-24"); ap.add_argument("--variants", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--rtl", action="store_true")
    ap.add_argument("--mode", choices=["inspire", "engine", "mix"], default="inspire",
                    help="inspire: adapt real reference pages (default); engine: learned generator; mix: both compete")
    a = ap.parse_args(argv)
    src = json.load(open(a.beats, encoding="utf-8"))
    beats = knity_to_beats(src) if "chapter" in src and "pages" in src and "template" in src["pages"][0] else src
    if a.pages:
        lo, hi = [int(x) for x in a.pages.split("-")]
        beats["pages"] = [p for i, p in enumerate(beats["pages"]) if lo <= p.get("no", i + 1) <= hi]
    p = plan(beats, style=a.style, variants=a.variants, seed=a.seed, reading="rtl" if a.rtl else "ltr", mode=a.mode)
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    md = os.path.splitext(a.out)[0] + "_prompts.md"
    open(md, "w", encoding="utf-8").write(prompts_md(p))
    print(f"planned {len(p['pages'])} pages -> {a.out}, {md}")
    for n in p["rhythm"]["notes"]: print("note:", n)


if __name__ == "__main__":
    main()
