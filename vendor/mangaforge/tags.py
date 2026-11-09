# -*- coding: utf-8 -*-
"""Shot tags for reference pages (lazy: tag a page the first time it's drawn as a reference).

Each tagged page stores, per panel in the template's reading order, the shot size and camera angle:
    shot:  EWS WS FS MS MCU CU ECU INS        angle: eye low worm high bird dutch ots pov
Tags are judged by eye from the reference page, then reused as camera hints in prompts.

    mangaforge tag pending plan.json             list reference pages a plan uses that are still untagged
    mangaforge tag sheet KEY [KEY ...] --out s.jpg   contact sheet with panel numbers in template order (local thumbnails)
    mangaforge tag set KEY "CU/low, MS/eye, WS/high"  store tags for one page
"""
import argparse, json, os
from .inspire import TAGS_PATH, load_tags, key as tkey
from .refpool import load_pool, RTL_SERIES

SHOTS = {"EWS", "WS", "FS", "MS", "MCU", "CU", "ECU", "INS"}
ANGLES = {"eye", "low", "worm", "high", "bird", "dutch", "ots", "pov"}


def parse(spec):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part: out.append(None); continue
        shot, _, angle = part.partition("/")
        shot = shot.strip().upper(); angle = (angle.strip() or "eye").lower()
        if shot not in SHOTS: raise ValueError(f"unknown shot {shot!r} (use {sorted(SHOTS)})")
        if angle not in ANGLES: raise ValueError(f"unknown angle {angle!r} (use {sorted(ANGLES)})")
        out.append(dict(shot=shot, angle=angle))
    return out


def save(tags):
    with open(TAGS_PATH, "w", encoding="utf-8") as f: json.dump(tags, f, indent=0, sort_keys=True)


def set_tags(key, spec, note=""):
    pool = {tkey(t): t for t in load_pool()["templates"]}
    t = pool[key]
    panels = parse(spec) if isinstance(spec, str) else spec
    if len(panels) != t["n"]: raise ValueError(f"{key} has {t['n']} panels, got {len(panels)} tags")
    tags = load_tags(); tags[key] = dict(panels=panels, note=note); save(tags)
    return tags[key]


REF_ROOT = os.environ.get("MANGAFORGE_REF_ROOT", "/home/claude/mds")


def sheet(keys, out, width=420, root=None):
    from PIL import Image, ImageDraw, ImageFont
    pool = {tkey(t): t for t in load_pool()["templates"]}
    tiles = []
    for k in keys:
        t = pool[k]
        th = t["th"] if os.path.isabs(t["th"]) else os.path.join(root or REF_ROOT, t["th"])
        im = Image.open(th).convert("RGB")
        h = int(width * im.height / im.width); im = im.resize((width, h)); d = ImageDraw.Draw(im)
        flip = t["s"] in RTL_SERIES
        # template coords are relative to the live box; recover it roughly from the polygons' extent
        for i, p in enumerate(t["ps"]):
            us = [x for x, _ in p["q"]]; vs = [y for _, y in p["q"]]
            cu = sum(us) / len(us); cv = sum(vs) / len(vs)
            if flip: cu = 1 - cu
            x = (0.06 + 0.88 * cu) * width; y = (0.05 + 0.9 * cv) * h
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(230, 30, 60)); d.text((x - 5, y - 7), str(i + 1), fill="white")
        d.rectangle([0, 0, width, 18], fill=(0, 0, 0)); d.text((4, 3), k[:60], fill="white")
        tiles.append(im)
    cols = 4; rows = (len(tiles) + cols - 1) // cols
    H = max(t.height for t in tiles)
    S = Image.new("RGB", (cols * (width + 8), rows * (H + 8)), "white")
    for i, im in enumerate(tiles): S.paste(im, ((i % cols) * (width + 8), (i // cols) * (H + 8)))
    S.save(out, quality=82)
    return out


def pending(plan_path):
    p = json.load(open(plan_path, encoding="utf-8")); tags = load_tags()
    return [pg["inspired_by"]["key"] for pg in p["pages"] if pg.get("inspired_by") and pg["inspired_by"]["key"] not in tags]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mangaforge tag", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("pending"); a1.add_argument("plan")
    a2 = sub.add_parser("sheet"); a2.add_argument("keys", nargs="+"); a2.add_argument("--out", default="tag_sheet.jpg")
    a2.add_argument("--root", help="folder that holds the analysis thumbs/ (default $MANGAFORGE_REF_ROOT)")
    a3 = sub.add_parser("set"); a3.add_argument("key"); a3.add_argument("tags"); a3.add_argument("--note", default="")
    a4 = sub.add_parser("bulk", help="apply a JSON file {key: 'CU/low, MS/eye', ...}"); a4.add_argument("file")
    a5 = sub.add_parser("exclude", help="drop a reference page from sampling (afterwords, ads, misdetected pages)")
    a5.add_argument("keys", nargs="+"); a5.add_argument("--note", default="not a story page")
    a = ap.parse_args(argv)
    if a.cmd == "pending": print("\n".join(pending(a.plan)))
    elif a.cmd == "sheet": print(sheet(a.keys, a.out, root=a.root))
    elif a.cmd == "set": print(set_tags(a.key, a.tags, a.note))
    elif a.cmd == "exclude":
        tags = load_tags()
        for k in a.keys: tags[k] = dict(exclude=True, note=a.note)
        save(tags); print(len(a.keys), "excluded")
    elif a.cmd == "bulk":
        for k, v in json.load(open(a.file, encoding="utf-8")).items():
            try: set_tags(k, v)
            except Exception as e: print("skip", k, e)
        print(len(load_tags()), "pages tagged")


if __name__ == "__main__":
    main()
