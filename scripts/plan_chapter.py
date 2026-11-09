# -*- coding: utf-8 -*-
"""Beats → planned chapter. Every page borrows real reference geometry (mode inspire), or the learned-structure
engine (mode engine), or both compete (mode mix). Writes PLAN.json and PLAN_prompts.md (one image prompt per panel).

Beats format (one JSON): {"title", "style"?, "cast"?, "pages": [{"no", "energy" 0-10, "beat" calm|build|impact|reveal|pause|dread,
  "scene", "paper", "note", "panels": [{"id": "3.2", "size": splash|big|wide|med|close|insert, "shot"?: EWS..INS,
  "angle"?: EYE|LOW|HIGH|DUTCH|..., "art": "...", "lettering": [{"kind": dialogue|caption|sfx, "speaker", "text"}],
  "inset"?, "breakout"?, "borderless"?}]}]}
usage: python3 plan_chapter.py BEATS.json --out CH01_plan.json [--mode inspire|engine|mix] [--seed N] [--rtl]"""
import argparse, json, os, sys
from _common import series_config, project_root
from mangaforge.plan import plan, prompts_md


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("beats"); ap.add_argument("--out", required=True); ap.add_argument("--mode", default="inspire")
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--variants", type=int, default=4); ap.add_argument("--rtl", action="store_true")
    a = ap.parse_args(argv)
    cfg = series_config(project_root(os.path.dirname(os.path.abspath(a.beats))))
    beats = json.load(open(a.beats, encoding="utf-8"))
    p = plan(beats, variants=a.variants, seed=a.seed, reading="rtl" if (a.rtl or cfg["reading"] == "rtl") else "ltr", mode=a.mode)
    # carry explicit shot/angle/borderless fields through to the plan's beats
    json.dump(p, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.splitext(a.out)[0] + "_prompts.md", "w", encoding="utf-8").write(prompts_md(p))
    print(json.dumps(dict(written=a.out, pages=len(p["pages"]), rhythm=p["rhythm"]), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
