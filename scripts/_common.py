# -*- coding: utf-8 -*-
"""Shared helpers for Excelsior scripts: paths, project files, plan loading, shot classification."""
import json, os, re, sys, glob, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
VENDOR = os.path.join(SKILL_DIR, "vendor")
if VENDOR not in sys.path:
    sys.path.insert(0, VENDOR)

VERSION = "1.0.0"
CONTEXT_VERSION = 1            # SERIES.md / STYLE.md frontmatter `excelsior:` value this version reads
STATE_DIR = ".excelsior"


def project_root(start=None):
    """Walk up from cwd to the first folder holding SERIES.md, STYLE.md or .excelsior; else cwd."""
    d = os.path.abspath(start or os.getcwd())
    while True:
        if any(os.path.exists(os.path.join(d, n)) for n in ("SERIES.md", "STYLE.md", STATE_DIR)):
            return d
        up = os.path.dirname(d)
        if up == d:
            return os.path.abspath(start or os.getcwd())
        d = up


def state(root, *parts, make=False):
    p = os.path.join(root, STATE_DIR, *parts)
    if make:
        os.makedirs(p if not os.path.splitext(p)[1] else os.path.dirname(p), exist_ok=True)
    return p


def frontmatter(path):
    """Tiny YAML-ish frontmatter reader (key: value, lists as [a, b])."""
    if not os.path.exists(path):
        return None, ""
    txt = open(path, encoding="utf-8").read()
    meta = {}
    if txt.startswith("---"):
        end = txt.find("\n---", 3)
        if end > 0:
            for line in txt[3:end].strip().splitlines():
                if ":" in line and not line.startswith(" "):
                    k, v = line.split(":", 1); v = v.strip().strip('"').strip("'")
                    if v.startswith("[") and v.endswith("]"):
                        v = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
                    meta[k.strip()] = v
            txt = txt[end + 4:]
    return meta, txt


def series_config(root):
    meta, _ = frontmatter(os.path.join(root, "SERIES.md"))
    meta = meta or {}
    smeta, _ = frontmatter(os.path.join(root, "STYLE.md"))
    smeta = smeta or {}
    cfg = dict(format="print", reading="ltr", turn_reveals="even", trim="7x10", language="en",
               max_words_balloon=25, max_words_panel=40, max_balloons_panel=3, borderless_per_scene=1,
               signature_slant=False)
    for src in (meta, smeta):
        for k, v in src.items():
            if k in cfg:
                if isinstance(cfg[k], bool): v = str(v).lower() in ("1", "true", "yes", "on")
                elif isinstance(cfg[k], int):
                    try: v = int(v)
                    except ValueError: continue
                cfg[k] = v
    return cfg


def load_plan(path):
    """Accept a mangaforge plan (pages[].layout + pages[].beats) or a beats file (pages[].panels with art).
    Returns a list of normalised pages: dict(no, energy, beat, scene, paper, note, layout|None, panels=[...])."""
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for i, pg in enumerate(d.get("pages", [])):
        if "layout" in pg:
            b = pg.get("beats") or {}
            geo = {str(p["id"]): p for p in pg["layout"]["panels"]}
            panels = []
            for p in (b.get("panels") or pg.get("panels") or []):
                q = dict(p); q["geo"] = geo.get(str(p["id"]))
                panels.append(q)
            out.append(dict(no=pg.get("page", i + 1), energy=pg.get("energy", b.get("energy", 5)), beat=pg.get("beat", b.get("beat", "build")),
                            scene=b.get("scene"), paper=b.get("paper", "white"), note=pg.get("note", ""), layout=pg["layout"],
                            inspired_by=pg.get("inspired_by"), absurdity=pg.get("absurdity", b.get("absurdity", [])), panels=panels))
        else:
            out.append(dict(no=pg.get("no", i + 1), energy=pg.get("energy", 5), beat=pg.get("beat", "build"), scene=pg.get("scene"),
                            paper=pg.get("paper", "white"), note=pg.get("note", ""), layout=None, inspired_by=None,
                            absurdity=pg.get("absurdity", []),
                            panels=[dict(p, geo=None) for p in pg.get("panels", [])]))
    return d, out


# ---------------------------------------------------------------- shot language
SHOTS = ["EWS", "WS", "FS", "MS", "MCU", "CU", "ECU", "INS"]
ANGLE_CODES = {"EYE": "eye", "LOW": "low", "WORM": "worm", "HIGH": "high", "BIRD": "bird", "DUTCH": "dutch", "OTS": "ots",
               "POV": "pov", "PROF": "eye", "BACK": "eye", "SIL": "eye", "FIX": "eye", "ECU": "eye"}
ENV = r"city|skyline|stadium|avenue|harbou?r|street|tower|rooftop|aerial|from above|pull back|layers|horizon|sky\b|corridor|hallway|campus|courtyard|station|road|traffic|building|whole room|the room|classroom|stairwell|forest|field|village|crowd|landscape"
OBJ = r"\bhand\b|hands|finger|fingers|phone|screen|card|cup|pen|paper|note|keyboard|key\b|wire|cable|plug|switch|watch|clock|badge|mask\b|bag|coin|door handle|foot\b|feet|shoe|sword|blade|gun|letter"
FACE = r"\beyes?\b|pupil|iris|lashes"
HEAD = r"\bface\b|head|expression|cheek|jaw|brow|eyebrow|forehead|smile|grin|mouth|lips|looks|stares|glances|tears?"
CHEST = r"shoulders?|chest|torso|collar"
BODY_FULL = r"full figure|full-figure|stands|standing|walks|walking|runs|running|steps|sprint|leaps|jumps|falls|kneels|crouch|whole body|head to toe"
PERSON = r"\bhe\b|\bshe\b|\bhis\b|\bher\b|\bthey\b|figure|someone|boy|girl|teacher|woman|\bman\b|silhouette|people|kid|child|player|students?"


def classify_shot(p):
    """Explicit `shot` wins; else read the panel's size, camera code and art note."""
    if p.get("shot") in SHOTS:
        return p["shot"]
    art = (p.get("art") or "").lower()
    size, ang = p.get("size", "med"), (p.get("angle") or "EYE").upper()
    has_person = bool(re.search(PERSON, art)) or bool(p.get("cast"))
    action = re.search(r"strikes?|drives|swings?|slams?|lunges?|punch|kicks?|throws?|catches|grabs", art)
    if ang == "ECU":
        if action and size in ("wide", "big", "splash"): return "MS"
        if re.search(FACE, art) and not re.search(r"\bface\b|head|grin|smile", art): return "ECU"
        if re.search(HEAD, art): return "CU" if size == "close" else "MCU"
        return "INS" if re.search(OBJ, art) or not has_person else "ECU"
    if size == "insert" or (size == "close" and re.search(OBJ, art) and not re.search(FACE + "|" + HEAD, art)):
        return "INS"
    if size == "close":
        if re.search(FACE, art) and not re.search(HEAD + "|" + CHEST, art): return "ECU"
        if re.search(CHEST, art): return "MCU"
        return "CU" if (has_person or re.search(HEAD, art)) else "INS"
    if size in ("splash", "big", "wide"):
        if re.search(ENV, art) and (not has_person or re.search(r"tiny|small|far|distant|pull back|from above|aerial|layers", art)):
            return "EWS" if size in ("splash", "big") or re.search(r"tiny|aerial|from above|skyline|city", art) else "WS"
        if re.search(BODY_FULL, art): return "FS"
        if re.search(HEAD, art) and size == "wide": return "MCU"
        return "WS" if size == "wide" or not has_person else "FS"
    if re.search(BODY_FULL, art): return "FS"
    if re.search(HEAD, art): return "MCU"
    return "MS"


def angle_of(p):
    a = p.get("shot_angle") or ANGLE_CODES.get((p.get("angle") or "EYE").upper(), "eye")
    return a


def words(t):
    return len(re.findall(r"[\w'’-]+", t or ""))


def slug(s):
    base = re.sub(r"[^a-zA-Z0-9]+", "-", os.path.splitext(os.path.basename(s))[0]).strip("-").lower() or "target"
    return f"{base}-{hashlib.sha1(os.path.abspath(s).encode()).hexdigest()[:6]}" if os.path.exists(s) else base


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=1))
