# -*- coding: utf-8 -*-
"""Page analyser: measures the *structure* of manga pages (panel geometry, gutters, bleeds,
slants, insets, ink balance). Stores numbers only, never the artwork.

Works on CBZ/ZIP archives, folders of images, or single images.
    python -m mangaforge.analyze <path> [<path> ...] --out analysis.jsonl --series NAME
"""
import argparse, io, json, math, os, re, sys, zipfile
import numpy as np, cv2

IMG_RX = re.compile(r"\.(jpe?g|png|webp|bmp)$", re.I)
H = 1000  # working height (pixels) for pages

# ----------------------------------------------------------------- I/O
def iter_images(path):
    """Yield (name, BGR ndarray) from a cbz/zip, a folder (recursive) or an image."""
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in sorted(files):
                p = os.path.join(root, f)
                if IMG_RX.search(f):
                    im = cv2.imread(p, cv2.IMREAD_COLOR)
                    if im is not None: yield p, im
                elif f.lower().endswith((".cbz", ".zip")):
                    yield from iter_images(p)
    elif path.lower().endswith((".cbz", ".zip")):
        with zipfile.ZipFile(path) as z:
            for n in sorted(x for x in z.namelist() if IMG_RX.search(x)):
                buf = np.frombuffer(z.read(n), np.uint8)
                im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                if im is not None: yield f"{path}::{n}", im
    elif IMG_RX.search(path):
        im = cv2.imread(path, cv2.IMREAD_COLOR)
        if im is not None: yield path, im

# ----------------------------------------------------------------- helpers
def _edge_angles(poly):
    """Deviation (deg) of each edge from the nearest axis."""
    out = []
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        a = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
        out.append(min(a % 90, 90 - (a % 90)))
    return out

def _background(gray):
    b = np.concatenate([gray[:6].ravel(), gray[-6:].ravel(), gray[:, :6].ravel(), gray[:, -6:].ravel()])
    return float(np.median(b))

# ----------------------------------------------------------------- page analysis
def analyse_page(img):
    h0, w0 = img.shape[:2]
    sc = H / h0
    img = cv2.resize(img, (max(1, round(w0 * sc)), H), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    bg = _background(gray)
    dark_page = bg < 90
    g = 255 - gray if dark_page else gray
    # ink balance (on the un-inverted page)
    black = float((gray < 50).mean()); white = float((gray > 215).mean()); mid = 1 - black - white
    sat = float(cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[..., 1].mean() / 255)

    # gutter = near-white pixels connected to the page border
    thr = 225 if not dark_page else 200
    whiteish = (g >= thr).astype(np.uint8)
    whiteish = cv2.morphologyEx(whiteish, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    ff = whiteish.copy(); mask = np.zeros((h + 2, w + 2), np.uint8)
    seeds = [(x, 0) for x in range(0, w, 7)] + [(x, h - 1) for x in range(0, w, 7)] + \
            [(0, y) for y in range(0, h, 7)] + [(w - 1, y) for y in range(0, h, 7)]
    for (x, y) in seeds:
        if ff[y, x] == 1: cv2.floodFill(ff, mask, (x, y), 2)
    gutter = (ff == 2).astype(np.uint8)
    content = (1 - gutter).astype(np.uint8)
    # cut thin bridges (small frame-breaks, balloon tails) so panels separate
    content_o = cv2.morphologyEx(content, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(content_o, 8)
    panels = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 0.012 * h * w: continue
        comp = (lab == i).astype(np.uint8)
        cs, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = max(cs, key=cv2.contourArea)
        hull = cv2.convexHull(c)
        solidity = float(cv2.contourArea(c) / max(1, cv2.contourArea(hull)))
        eps = 0.012 * cv2.arcLength(hull, True)
        ap = cv2.approxPolyDP(hull, eps, True).reshape(-1, 2)
        poly = [(float(px / w), float(py / h)) for px, py in ap]
        devs = _edge_angles([(px, py) for px, py in ap])
        # drop very short edges from the slant measure
        lens = [math.dist(ap[k], ap[(k + 1) % len(ap)]) for k in range(len(ap))]
        sig = [d for d, L in zip(devs, lens) if L > 0.08 * min(h, w)]
        slant = max(sig) if sig else 0.0
        bleed = dict(top=bool(y <= 0.012 * h), bottom=bool(y + bh >= 0.988 * h), left=bool(x <= 0.012 * w), right=bool(x + bw >= 0.988 * w))
        # fraction of the component that the opening removed back near borders = break-outs/bridges
        panels.append(dict(bbox=[float(x / w), float(y / h), float(bw / w), float(bh / h)], area=float(area / (h * w)), poly=poly, nv=len(ap),
                           slant=round(slant, 2), solidity=round(solidity, 3), bleed=bleed))
    # bridges: content pixels removed by the opening that touch two or more panels => frame-break / straddle
    bridge = ((content == 1) & (content_o == 0)).astype(np.uint8)
    nb, blab, bst, _ = cv2.connectedComponentsWithStats(bridge, 8)
    breaks = 0
    if panels:
        dil = cv2.dilate(lab.astype(np.uint16).astype(np.float32), np.ones((5, 5), np.uint8)).astype(np.int32)
        for j in range(1, nb):
            if bst[j][4] < 60: continue
            ids = set(np.unique(dil[blab == j])) - {0}
            if len(ids) >= 2: breaks += 1
    # insets: rectangular contours fully inside a panel occupying 4-35% of it
    insets = 0
    edges = cv2.Canny(gray, 60, 160)
    cs, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for c in cs:
        a = cv2.contourArea(c)
        if a < 0.01 * h * w: continue
        ap = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(ap) != 4 or not cv2.isContourConvex(ap): continue
        bx, by, bw, bh = cv2.boundingRect(ap)
        for p in panels:
            px, py, pw, ph = p["bbox"]
            if bx / w > px + 0.02 and by / h > py + 0.02 and (bx + bw) / w < px + pw - 0.02 and (by + bh) / h < py + ph - 0.02:
                if 0.04 < (bw * bh) / (pw * ph * w * h) < 0.35: insets += 1; break
    # gutter width: thickness of gutter strips between panels (exclude outer margin)
    inner = np.zeros_like(gutter)
    if panels:
        xs = [p["bbox"][0] for p in panels]; ys = [p["bbox"][1] for p in panels]
        xe = [p["bbox"][0] + p["bbox"][2] for p in panels]; ye = [p["bbox"][1] + p["bbox"][3] for p in panels]
        X0, Y0, X1, Y1 = int(min(xs) * w), int(min(ys) * h), int(max(xe) * w), int(max(ye) * h)
        inner[Y0:Y1, X0:X1] = gutter[Y0:Y1, X0:X1]
    gw = 0.0
    if inner.sum() > 50:
        dt = cv2.distanceTransform(inner, cv2.DIST_L2, 3)
        sk = dt[(dt > 0) & (dt >= cv2.dilate(dt, np.ones((3, 3))) - 1e-3)]
        if len(sk): gw = float(np.median(sk) * 2 / w)
    margin = 0.0
    if panels:
        margin = float(min(min(p["bbox"][0] for p in panels), min(1 - p["bbox"][0] - p["bbox"][2] for p in panels)))
    areas = sorted([p["area"] for p in panels], reverse=True)
    cov = float(sum(areas))
    return dict(w=int(w0), h=int(h0), spread=bool(w0 > 1.05 * h0), dark=bool(dark_page), bg=round(bg), ink=dict(black=round(black, 3), mid=round(mid, 3), white=round(white, 3), sat=round(sat, 3)),
                n=len(panels), panels=panels, breaks=breaks, insets=insets, gutter=round(gw, 4), margin=round(margin, 4),
                coverage=round(cov, 3), top_share=round(areas[0] / cov, 3) if areas else 0,
                area_cv=round(float(np.std(areas) / np.mean(areas)), 3) if len(areas) > 1 else 0,
                slanted=sum(1 for p in panels if p["slant"] > 3), max_slant=max([p["slant"] for p in panels], default=0),
                bleeds=sum(1 for p in panels if any(p["bleed"].values())))

# ----------------------------------------------------------------- vertical-scroll strip analysis
def analyse_strip(img):
    """For long webtoon strips: split into blocks of art separated by background gaps."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    rowstd = gray.std(axis=1); rowmean = gray.mean(axis=1)
    bgrow = rowstd < 6
    blocks, gaps = [], []
    y = 0
    while y < h:
        s = y; flag = bgrow[y]
        while y < h and bgrow[y] == flag: y += 1
        (gaps if flag else blocks).append((s / w, (y - s) / w, float(rowmean[s:y].mean())))
    blocks = [b for b in blocks if b[1] > 0.05]
    return dict(strip=True, w=int(w), h=int(h), blocks=[round(b[1], 3) for b in blocks], gaps=[round(g[1], 3) for g in gaps if g[1] > 0.02],
                gap_dark=[bool(g[2] < 80) for g in gaps if g[1] > 0.02])

def analyse_image(img):
    h, w = img.shape[:2]
    if h > 2.2 * w: return analyse_strip(img)
    return analyse_page(img)

# ----------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+"); ap.add_argument("--out", default="analysis.jsonl")
    ap.add_argument("--series", default=None, help="label; default = parent folder name")
    ap.add_argument("--chapter", default=None)
    a = ap.parse_args(argv)
    with open(a.out, "a", encoding="utf-8") as fo:
        for p in a.paths:
            ser = a.series or os.path.basename(os.path.dirname(os.path.abspath(p)))
            ch = a.chapter or os.path.splitext(os.path.basename(p))[0]
            for k, (name, im) in enumerate(iter_images(p)):
                try: r = analyse_image(im)
                except Exception as e: r = dict(error=str(e))
                r.update(series=ser, chapter=ch, page=k, src=os.path.basename(name))
                fo.write(json.dumps(r) + "\n")
            print("analysed", ch, file=sys.stderr)

if __name__ == "__main__":
    main()
