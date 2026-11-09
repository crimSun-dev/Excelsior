# -*- coding: utf-8 -*-
"""Proof sheet: every planned page drawn as geometry with shot, angle and lettering load per panel, the beat,
the paper, the reference that inspired it and the detector's findings beside it. This is the evidence a critique
or a reviewer looks at (no artwork needed). Optional PNGs per page for agents that read images.

usage: python3 proof.py PLAN.json --out proof.html [--pages 1-12] [--png DIR]"""
import argparse, html, json, os, sys
from _common import load_plan, classify_shot, angle_of, words, series_config, project_root
import detect

E = html.escape
PAPER = {"black": ("#111", "#eee"), "amber": ("#f2c56b", "#2a1d05"), "white": ("#fbfbf8", "#15161c")}


def page_svg(pg, findings, w=280):
    L = pg["layout"]; W, H = L["trim"]; s = w / W; b = (L.get("bleed") or 0.125) * s
    bg, ink = PAPER.get(pg["paper"], PAPER["white"])
    out = [f'<svg viewBox="{-b:.1f} {-b:.1f} {W*s+2*b:.1f} {H*s+2*b:.1f}" width="{W*s+2*b:.0f}" height="{H*s+2*b:.0f}" xmlns="http://www.w3.org/2000/svg">',
           f'<rect x="{-b:.1f}" y="{-b:.1f}" width="{W*s+2*b:.1f}" height="{H*s+2*b:.1f}" fill="{bg}" opacity=".55"/>',
           f'<rect width="{W*s:.1f}" height="{H*s:.1f}" fill="{bg}" stroke="#999" stroke-dasharray="2 2"/>']
    bad = {str(f["panel"]) for f in findings if f.get("panel")}
    by = {str(p["id"]): p for p in pg["panels"]}
    for g in sorted(L["panels"], key=lambda g: g.get("z", 0)):
        pts = " ".join(f"{x*s:.1f},{y*s:.1f}" for x, y in g["poly"])
        p = by.get(str(g["id"]), {})
        dash = ' stroke-dasharray="4 3"' if p.get("borderless") else ""
        stroke = "#d33" if str(g["id"]) in bad else ink
        fill = "rgba(255,255,255,.9)" if g["inset"] else "none"
        out.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{2.2 if str(g["id"]) in bad else 1.4}"{dash}/>')
        cx = sum(x for x, _ in g["poly"]) / len(g["poly"]) * s; cy = sum(y for _, y in g["poly"]) / len(g["poly"]) * s
        wd = sum(words(b.get("text")) for b in p.get("lettering", []) if b.get("kind") != "sfx")
        lab = f'{g["id"]} · {classify_shot(p) if p else "?"}' + (f' · {angle_of(p)}' if p and angle_of(p) != "eye" else "")
        out.append(f'<text x="{cx:.0f}" y="{cy:.0f}" font-size="11" text-anchor="middle" fill="{stroke}" font-family="system-ui">{E(lab)}</text>')
        if wd: out.append(f'<text x="{cx:.0f}" y="{cy+13:.0f}" font-size="9.5" text-anchor="middle" fill="{stroke}" opacity=".75" font-family="system-ui">{wd} words</text>')
    out.append("</svg>")
    return "".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument("plan"); ap.add_argument("--out", required=True)
    ap.add_argument("--pages"); ap.add_argument("--png")
    a = ap.parse_args(argv)
    raw, pages = load_plan(a.plan)
    if not pages or not pages[0]["layout"]:
        print("proof needs a planned layout (run plan_chapter.py first)", file=sys.stderr); return 1
    cfg = series_config(project_root(os.path.dirname(os.path.abspath(a.plan))))
    F, S = detect.check(a.plan, cfg)
    sel = None
    if a.pages:
        lo, _, hi = a.pages.partition("-"); sel = range(int(lo), int(hi or lo) + 1)
    cards = []
    for pg in pages:
        if sel and pg["no"] not in sel: continue
        fs = [f for f in F if f["page"] == pg["no"]]
        ref = pg.get("inspired_by") or {}
        refs = f'{ref.get("series", "")} {ref.get("chapter", "")} p{ref.get("page", "")}' if ref else "engine"
        cards.append(f'<figure id="p{pg["no"]}"><figcaption><b>p{pg["no"]}</b> · {E(pg["beat"])} · energy {pg["energy"]} · {E(pg["paper"])} paper'
                     f'<br><small>layout from {E(refs)}</small></figcaption>{page_svg(pg, fs)}'
                     + "".join(f'<p class="f {f["severity"]}"><b>{f["severity"]}</b> {E(f["rule"])}: {E(f["message"])}</p>' for f in fs) + "</figure>")
    chap = [f for f in F if not f["page"]]
    doc = f"""<title>{E(raw.get('title') or 'Proof')} · proof</title><style>
:root{{--bg:#f6f5f1;--fg:#16171c;--mut:#666;--bad:#c22}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#121316;--fg:#e9e8e3;--mut:#9a9a9a;--bad:#ff6b6b;color-scheme:dark}}}}
:root[data-theme=dark]{{--bg:#121316;--fg:#e9e8e3;--mut:#9a9a9a;--bad:#ff6b6b;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui;padding-block:24px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:22px}} figure{{margin:0;min-width:0;padding:6px}} figcaption{{margin-bottom:6px}}
small,.f{{color:var(--mut)}} .f{{margin:4px 0;font-size:12.5px}} .P1,.P0{{color:var(--bad)}} svg{{max-width:100%;height:auto}}</style>
<h1>{E(raw.get('title') or os.path.basename(a.plan))}: proof</h1>
<p>{len(pages)} pages · red outlines mark panels with findings · dashed = borderless.</p>
<ul>{''.join(f'<li><b>{f["severity"]}</b> {E(f["rule"])}: {E(f["message"])}</li>' for f in chap)}</ul>
<main>{''.join(cards)}</main>"""
    open(a.out, "w", encoding="utf-8").write(doc)
    print(a.out)
    if a.png:
        os.makedirs(a.png, exist_ok=True)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                b = pw.chromium.launch(); pgw = b.new_page(viewport=dict(width=1400, height=900), device_scale_factor=1)
                pgw.set_content(doc, wait_until="domcontentloaded")
                for el in pgw.query_selector_all("figure"):
                    el.screenshot(path=os.path.join(a.png, el.get_attribute("id") + ".png"))
                b.close()
            print(f"pngs → {a.png}")
        except Exception as e:
            print(f"png export skipped: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
