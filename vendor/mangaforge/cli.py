# -*- coding: utf-8 -*-
"""mangaforge command line.

  mangaforge analyze <cbz|folder ...> --out analysis.jsonl     measure page composition (numbers only)
  mangaforge learn analysis.jsonl --out model.json             build the composition model
  mangaforge refpool analysis.jsonl [...]                      store every usable page as a layout template
  mangaforge plan beats.json --out plan.json                   layouts + per-panel prompts (+ prompts.md)
                                                               (default --mode inspire: each page adapts a real reference page)
  mangaforge inspire --sizes wide,med,close,big --energy 7     try reference-inspired layouts for one page
  mangaforge tag pending|sheet|set|bulk|exclude ...            shot/angle tags for reference pages (lazy)
  mangaforge gen plan.json --out panels                        generate panels with the OpenAI Images API
  mangaforge compose plan.json --panels panels --out pages     compose every page that has images
  mangaforge watch plan.json --panels panels --out pages       re-compose whenever new panel images land
  mangaforge serve [--public-url https://...]                  designer + REST (custom GPT) + MCP (ChatGPT/Claude)
"""
import argparse, json, os, sys, time


def compose_cmd(a, once=True):
    from .compose import compose_page
    from PIL import Image
    p = json.load(open(a.plan, encoding="utf-8")); os.makedirs(a.out, exist_ok=True)
    styles = json.load(open(a.letter_styles, encoding="utf-8")) if a.letter_styles else {}
    done = {}
    while True:
        for pg in p["pages"]:
            files = {x["id"]: os.path.join(a.panels, f"{pg['page']}_{x['id']}.png") for x in pg["panels"]}
            have = {k: v for k, v in files.items() if os.path.exists(v)}
            if not have and not a.proofs: continue
            stamp = tuple(sorted((k, os.path.getmtime(v)) for k, v in have.items()))
            if done.get(pg["page"]) == stamp: continue
            out = os.path.join(a.out, f"page_{pg['page']:03d}")
            compose_page(pg["layout"], {k: Image.open(v) for k, v in have.items()},
                         {x["id"]: x.get("lettering", []) for x in pg["panels"]} if not a.no_letters else {},
                         dpi=a.dpi, tone=a.tone, out_png=out + ".png", out_pdf=out + ".pdf" if a.pdf else None, letter_styles=styles)
            done[pg["page"]] = stamp
            print(f"page {pg['page']}: {len(have)}/{len(files)} panels -> {out}.png")
        if once: return
        time.sleep(2)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"): print(__doc__); return
    cmd, rest = argv[0], argv[1:]
    if cmd == "analyze":
        from .analyze import main as m; return m(rest)
    if cmd == "learn":
        from .learn import main as m; return m(rest)
    if cmd == "refpool":
        from .refpool import main as m; return m(rest)
    if cmd == "inspire":
        from .inspire import main as m; return m(rest)
    if cmd == "tag":
        from .tags import main as m; return m(rest)
    if cmd == "plan":
        from .plan import main as m; return m(rest)
    if cmd == "gen":
        from .imagegen import main as m; return m(rest)
    if cmd == "serve":
        from .server import main as m; return m(rest)
    if cmd in ("compose", "watch"):
        ap = argparse.ArgumentParser(prog=f"mangaforge {cmd}")
        ap.add_argument("plan"); ap.add_argument("--panels", default="panels"); ap.add_argument("--out", default="pages")
        ap.add_argument("--dpi", type=int, default=300); ap.add_argument("--tone", choices=["screen", "bands"])
        ap.add_argument("--pdf", action="store_true"); ap.add_argument("--proofs", action="store_true", help="also render pages with no images yet")
        ap.add_argument("--no-letters", action="store_true"); ap.add_argument("--letter-styles")
        a = ap.parse_args(rest)
        return compose_cmd(a, once=(cmd == "compose"))
    print("unknown command", cmd); print(__doc__)


if __name__ == "__main__":
    main()
