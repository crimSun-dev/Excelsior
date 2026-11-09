# -*- coding: utf-8 -*-
"""The dice. Keeps every run from converging on the category default.

--scope direction : a new visual world for a series, arc or chapter. You have written seven grounded directions,
                    ordered by resonance; the roll assigns which one gets built and deals 1–3 catalog challengers
                    (layout grammars from the measured reference library, plus a few labelled unmeasured traditions)
                    to fuse and weigh against it.
--scope scene     : a whole scene or sequence inside an established world. You have five to seven structures;
                    the roll assigns one. No challengers.
--scope page      : a single open page. Same as scene, three to five structures.
usage: python3 concept_seed.py --scope direction --mode hook [--count 7] [--seed N] [--schema]
"""
import argparse, json, os, random, secrets, sys, time
from _common import project_root, state, emit

try:
    from mangaforge.layout import load_model
    BY = load_model().get("by_series", {})
except Exception:
    BY = {}


def stats(code):
    s = BY.get(code) or {}
    if not s: return None
    ppp = s.get("panels_per_page", {}); tot = sum(ppp.values()) or 1
    med = sorted((int(k) for k, v in ppp.items() for _ in range(v)))[tot // 2] if ppp else None
    return dict(pages=s.get("pages"), panels_per_page_median=med, size_contrast_median=round(s.get("size_contrast_q", {}).get("p50", 0), 1),
                slant_rate=s.get("slant_page_rate"), frame_break_rate=s.get("bridge_page_rate"), inset_rate=s.get("inset_page_rate"),
                splash_rate=s.get("splash_rate"), dark_page_rate=s.get("dark_page_rate"), black_ink_median=s.get("ink_black_q", {}).get("p50"))


# Grammars, not looks: what a tradition does with the page. Measured entries carry real numbers from the library.
CATALOG = [
 dict(id="calm-grid-diagonal-break", name="Calm grid, diagonal break", source="DB", measured=True, modes=["follow", "converse"],
      grammar="Quiet and talk pages on a strict rectangular grid with margins; arcs open on a wide city or landscape; the fight page throws one huge diagonal panel across the grid.",
      study=["DB ch304 p14 (grid broken by one exploding panel)", "DB ch193 p11 (single diagonal impact, SFX across the page)", "DB ch423 p1 (Capsule Corp wide)"],
      fuse="Lend the series' talk scenes total stillness so the one diagonal per chapter lands like a slammed door."),
 dict(id="zigzag-bands", name="Zig-zag bands", source="DBS", measured=True, modes=["follow"],
      grammar="Fight pages built from horizontal bands with parallel or alternating diagonal cuts; SFX ride the cuts across gutters; density as speed (median 7 panels).",
      study=["DBS ch4 p7 (three bands, eye ricochets)", "DBS ch9 p23 (six fast tilted panels)", "DBS ch4 p12 (black space panel among white)"],
      fuse="Use the band rhythm for chases and rallies; return to rectangles the instant the action stops."),
 dict(id="ornament-and-float", name="Ornament and float", source="HNK", measured=True, modes=["immerse", "converse"],
      grammar="Ornamental caption frames, dense spot blacks, borderless floating panels, faces overlapping the tiers above and below; extreme size contrast (median 8.3×).",
      study=["HNK ch87 p29 (splash, ornamental caption)", "HNK ch92 p27 (borderless hands)", "HNK ch62 p9 (symmetric bird's-eye over two small talk panels)"],
      fuse="Take the frame away only where intimacy or the uncanny peaks; the ornament becomes the series' own motif, never borrowed decoration."),
 dict(id="slant-as-voice", name="Slant as house voice", source="KSB", measured=True, modes=["converse", "hook"],
      grammar="Tier boundaries slant even in dialogue (56% of pages), so slant is tone, not action; comic timing via big reaction faces and straddling shout balloons; chibi punchlines.",
      study=["KSB ch1 p26 (reaction face, slanted tiers, straddling shout)", "KSB ch101 p4 (stacked close-ups of one face)", "KSB ch5 p27 (chibi punchline)"],
      fuse="Only if the series' voice is comic or restless; then the calm page (rare, rectangular) becomes the dramatic tell."),
 dict(id="scroll-clock", name="Scroll as clock", source="LC", measured=True, modes=["immerse", "hook"],
      grammar="Vertical strips: the gap is the clock (0.05× width action, 0.18× normal, 0.4–0.6× held breath); tall cinematic blocks mixed with tiny inserts; colour carries time.",
      study=["Link Click strips: block height median 0.91× width, black gaps only 9% of the time"],
      fuse="For webtoon editions or for print sequences that should read like a held breath: translate gaps into empty tiers and white space."),
 dict(id="dark-slivers", name="Dark page, vertical slivers", source="P3", measured=True, modes=["immerse", "hook"],
      grammar="Dark-dominant pages (51%), scratch-texture energy fields, tall vertical slivers, SFX lettered vertically down the page; white is earned.",
      study=["P3 ch5 p29 (vertical SFX, white sky sliver)", "P3 ch11 p39 (full-page creature with a reaction sliver)"],
      fuse="For dread, night and memory: invert the paper and make white the accent."),
 dict(id="calling-card-angles", name="Calling-card angles", source="P5", measured=True, modes=["hook", "follow"],
      grammar="Black-heavy pages, angular cuts, cut-in reaction slivers; heightened text set as a vertical column beside the splash at the peak only.",
      study=["P5 ch3 p25 (spread, text column)", "P5 ch8 p18 (figure overruns every border)", "P5 ch6 p36 (low-angle breakout, ends on a shocked face)"],
      fuse="Reserve the angular, typographic peak for the one moment per chapter the series earns it."),
 # unmeasured traditions: real grammars, no library numbers; label them so in the hand
 dict(id="nine-grid-clock", name="Nine-panel metronome", source=None, measured=False, modes=["converse", "immerse"],
      grammar="A fixed 3×3 grid held across pages; time is panel count; a merged double cell is an event.",
      study=["(unmeasured: American alternative-comics grid tradition)"], fuse="Hold the grid through an interrogation or a countdown; break it once."),
 dict(id="ligne-claire-strip", name="Clear-line strip", source=None, measured=False, modes=["converse", "follow"],
      grammar="Three or four strict tiers, even lighting, everything legible; continuity and geography over drama.",
      study=["(unmeasured: Franco-Belgian album tradition)"], fuse="For heists, procedures and travel: the reader always knows where everyone is."),
 dict(id="gekiga-weight", name="Gekiga weight", source=None, measured=False, modes=["converse", "immerse"],
      grammar="Grounded anatomy, heavy blacks, long silent sequences, cinematic cutting; few words, slow time.",
      study=["(unmeasured: 1960s–70s Japanese dramatic-pictures tradition)"], fuse="For grief and consequence: let three silent panels do what a monologue would."),
 dict(id="shoujo-flow", name="Flower-flow layout", source=None, measured=False, modes=["converse", "immerse"],
      grammar="Panels dissolve into each other; full-height figures stand outside the panel grid; monologue floats free of balloons; screentone atmosphere carries feeling.",
      study=["(unmeasured: shoujo layout tradition)"], fuse="For inner life: the character stands in front of the page while the scene continues behind."),
 dict(id="yonkoma-beat", name="Four-beat strip", source=None, measured=False, modes=["converse"],
      grammar="Four equal vertical panels: setup, development, turn, punch; the rhythm is the joke.",
      study=["(unmeasured: yonkoma tradition)"], fuse="For comic interludes, omake and chapter-break gags; strict grid, punch in the last cell."),
 dict(id="storyboard-cut", name="Film storyboard cut", source=None, measured=False, modes=["follow", "hook"],
      grammar="Every panel is a shot with a lens and a move; continuity of screen direction (180° rule); match cuts across page turns.",
      study=["(unmeasured: film pre-visualisation practice)"], fuse="For chases and set pieces: keep screen direction and let a match cut ride the page turn."),
 dict(id="emaki-scroll", name="Handscroll continuity", source=None, measured=False, modes=["immerse", "follow"],
      grammar="One continuous space across panels and pages; the gutter is a step in time, not a cut in space.",
      study=["(unmeasured: Japanese handscroll narrative tradition)"], fuse="For a walk through a place: the background runs on behind the borders."),
]
RANK_W = [0.22, 0.20, 0.17, 0.14, 0.11, 0.09, 0.07]


def schema():
    return dict(direction_card=dict(thesis="the one idea this world owns and the category default it refuses",
                                    world="paper, line, tone, borders, gutters, lettering voices — recognisable with all story removed",
                                    first_page="exact composition of the opening page: what is where, at what scale, what the turn reveals",
                                    reader_path="what the reader feels and understands across the chapter",
                                    signature="the one device only this series does",
                                    risk="the honest way it could fail"),
                challenger_case="one line: why this fused challenger beats or loses to the assigned direction on reader identification and story clarity",
                canon_card="the category standard played straight, same anatomy")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", choices=["direction", "scene", "page"], default="direction")
    ap.add_argument("--mode", choices=["hook", "follow", "converse", "immerse"], default="hook")
    ap.add_argument("--count", type=int); ap.add_argument("--seed", type=int); ap.add_argument("--schema", action="store_true")
    ap.add_argument("--exclude", default="", help="comma-separated catalog ids or ranks already shown (re-roll)")
    ap.add_argument("--root")
    a = ap.parse_args(argv)
    if a.schema:
        emit(schema()); return 0
    seed = a.seed if a.seed is not None else secrets.randbits(32)
    rng = random.Random(seed)
    key = f"EXC-{a.scope[0].upper()}{a.mode[0].upper()}-{seed:08x}"
    count = a.count or (7 if a.scope == "direction" else (6 if a.scope == "scene" else 4))
    excl = set(x.strip() for x in a.exclude.split(",") if x.strip())
    ranks = [r for r in range(1, count + 1) if str(r) not in excl]
    w = [RANK_W[min(r - 1, len(RANK_W) - 1)] for r in ranks]
    assigned = rng.choices(ranks, weights=w, k=1)[0]
    out = dict(seed_key=key, scope=a.scope, mode=a.mode, assigned_rank=assigned,
               instruction=f"Build your #{assigned} {'direction' if a.scope == 'direction' else 'structure'} as written. "
                           "Your top-ranked option is what every run would ship; the roll is the point.")
    if a.scope == "direction":
        pool = [c for c in CATALOG if c["id"] not in excl]
        fit = [c for c in pool if a.mode in c["modes"]]; other = [c for c in pool if a.mode not in c["modes"]]
        k = rng.choice([1, 2, 2, 3, 3])
        hand = rng.sample(fit, min(k, len(fit)))
        if len(hand) < k and other: hand += rng.sample(other, min(k - len(hand), len(other)))
        for c in hand:
            c = dict(c); c["numbers"] = stats(c["source"]) if c["source"] else None
            out.setdefault("challengers", []).append(c)
        out["fuse_rule"] = ("Fuse each challenger before judging it: the challenger supplies the page grammar, the series supplies every fact, "
                            "character and canon rule, and clarity wins conflicts. Weigh fused challengers against the assigned direction on "
                            "two axes only: reader identification and story clarity. Losing to strong grounded material is a valid outcome.")
        out["standing_exit"] = "Offer the category standard, played straight, as the last option. Never recommend it."
        out["schema"] = "run with --schema for the card anatomy"
    try:
        root = a.root or project_root()
        p = state(root, "seeds.jsonl", make=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(t=int(time.time()), **{k: out[k] for k in ("seed_key", "scope", "mode", "assigned_rank")},
                                    challengers=[c["id"] for c in out.get("challengers", [])])) + "\n")
    except Exception:
        pass
    emit(out); return 0


if __name__ == "__main__":
    sys.exit(main())
