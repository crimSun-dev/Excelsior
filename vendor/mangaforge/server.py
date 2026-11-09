# -*- coding: utf-8 -*-
"""mangaforge server: REST API (for ChatGPT custom-GPT Actions) + MCP endpoint (for ChatGPT
developer-mode connectors, Claude, and other MCP clients) + the Manga Designer web UI.

    python -m mangaforge.server --port 8765 --workdir ./mf_work [--public-url https://<your-tunnel>]

Endpoints
  GET  /                     Manga Designer (web UI)
  GET  /model.json           the learned composition model
  POST /api/plan             beats -> layouts + panel prompts (returns plan_id)
  POST /api/compose          plan_id + page + images (openaiFileIdRefs | urls | base64) -> finished page
  POST /api/generate         plan_id + page -> generates missing panels with the OpenAI API, then composes
  GET  /files/...            composed pages and plans
  GET  /openapi.json         schema to paste into a custom GPT's Actions
  /mcp                       MCP (streamable HTTP)
"""
import argparse, base64, contextlib, io, json, os, re, time, urllib.request, uuid

from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse, HTMLResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from PIL import Image

from .layout import load_model
from .plan import plan as make_plan, knity_to_beats, prompts_md
from .compose import compose_page

HERE = os.path.dirname(__file__)
WORK = os.environ.get("MANGAFORGE_WORKDIR", os.path.abspath("mf_work"))
PUBLIC = os.environ.get("MANGAFORGE_PUBLIC_URL", "http://localhost:8765")
MODEL = load_model()


def _wd(*p):
    path = os.path.join(WORK, *p); os.makedirs(os.path.dirname(path), exist_ok=True); return path


def _save_plan(p):
    pid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    json.dump(p, open(_wd("plans", pid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(_wd("plans", pid + "_prompts.md"), "w", encoding="utf-8").write(prompts_md(p))
    return pid


def _load_plan(pid):
    if not re.fullmatch(r"[\w-]+", pid or ""): raise ValueError("bad plan_id")
    return json.load(open(_wd("plans", pid + ".json"), encoding="utf-8"))


def _fetch_image(ref):
    """ref: {'download_link'|'url'|'b64'|'path'}"""
    if isinstance(ref, str): ref = {"url": ref}
    if ref.get("b64"): return Image.open(io.BytesIO(base64.b64decode(ref["b64"])))
    url = ref.get("download_link") or ref.get("url")
    if url:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "mangaforge"}), timeout=60) as r:
            return Image.open(io.BytesIO(r.read()))
    if ref.get("path"): return Image.open(ref["path"])
    raise ValueError("image reference needs download_link, url, b64 or path")


def _page(p, page):
    for pg in p["pages"]:
        if str(pg["page"]) == str(page): return pg
    raise ValueError(f"page {page} not in plan")


def do_plan(body):
    if "pages" not in body and "panels" in body:  # single page shortcut
        body = dict(pages=[dict(no=1, energy=body.get("energy", 5), beat=body.get("beat", "build"), panels=body["panels"])],
                    style=body.get("style"), cast=body.get("cast"))
    if body.get("pages") and "template" in body["pages"][0]: body = knity_to_beats(body)
    p = make_plan(body, style=body.get("style"), cast=body.get("cast"), variants=int(body.get("variants", 4)),
                  seed=int(body.get("seed", 0)), reading=body.get("reading", "ltr"), model=MODEL, mode=body.get("mode", "inspire"))
    pid = _save_plan(p)
    return dict(plan_id=pid, prompts_url=f"{PUBLIC}/files/plans/{pid}_prompts.md", rhythm=p["rhythm"],
                pages=[dict(page=pg["page"], structure=pg["layout"]["structure"], energy=pg["energy"], beat=pg["beat"],
                            score_notes=pg["score"]["notes"], inspired_by=pg.get("inspired_by"),
                            panels=[dict(panel_id=x["id"], image_size=x["size"], crop_aspect=x["aspect"], prompt=x["prompt"]) for x in pg["panels"]])
                       for pg in p["pages"]])


def do_compose(body):
    p = _load_plan(body["plan_id"]); pg = _page(p, body["page"])
    ids = [x["id"] for x in pg["panels"]]
    imgs = {}
    refs = body.get("openaiFileIdRefs") or []
    for i, ref in enumerate(refs):  # match by panel id in the file name, else by order
        name = (ref.get("name") or "") if isinstance(ref, dict) else ""
        m = re.search(r"(?:^|[_\-\s])p?(\w+)\.(?:png|jpe?g|webp)$", name)
        pid = m.group(1) if m and m.group(1) in ids else (ids[i] if i < len(ids) else None)
        if pid: imgs[pid] = _fetch_image(ref)
    for it in body.get("images", []):
        imgs[str(it["panel_id"])] = _fetch_image(it)
    folder = body.get("panels_dir") or os.path.join(WORK, "panels")
    for pid in ids:  # manual mode: files dropped into the panels folder as <page>_<panel>.png
        f = os.path.join(folder, f"{pg['page']}_{pid}.png")
        if pid not in imgs and os.path.exists(f): imgs[pid] = Image.open(f)
    lettering = {x["id"]: x.get("lettering", []) for x in pg["panels"]} if body.get("letter", True) else {}
    stem = f"{body['plan_id']}_p{pg['page']}"
    png, pdf = _wd("pages", stem + ".png"), _wd("pages", stem + ".pdf")
    compose_page(pg["layout"], imgs, lettering, dpi=int(body.get("dpi", 200)), tone=body.get("tone"), out_png=png, out_pdf=pdf,
                 letter_styles=body.get("letter_styles") or {})
    missing = [i for i in ids if i not in imgs]
    return dict(page_url=f"{PUBLIC}/files/pages/{stem}.png", pdf_url=f"{PUBLIC}/files/pages/{stem}.pdf", missing_panels=missing,
                openaiFileResponse=[f"{PUBLIC}/files/pages/{stem}.pdf"])


def do_generate(body):
    from .imagegen import generate
    p = _load_plan(body["plan_id"]); pg = _page(p, body["page"])
    folder = os.path.join(WORK, "panels"); os.makedirs(folder, exist_ok=True)
    made = []
    for x in pg["panels"]:
        f = os.path.join(folder, f"{pg['page']}_{x['id']}.png")
        if not os.path.exists(f):
            generate(x["prompt"], x["size"], body.get("quality", "medium"), body.get("refs"), f); made.append(x["id"])
    res = do_compose(dict(plan_id=body["plan_id"], page=pg["page"], tone=body.get("tone")))
    res["generated"] = made
    return res


def do_inspire(body):
    """Alternative reference-inspired layouts for one page (of a plan, or from sizes)."""
    from .inspire import inspire
    from .plan import page_spec
    from .layout import svg
    if body.get("plan_id"):
        p = _load_plan(body["plan_id"]); pg = _page(p, body["page"])
        spec = page_spec(pg["beats"], p.get("reading", "ltr"), seed=int(body.get("seed", 1)))
        excl = {pg["inspired_by"]["key"]} if pg.get("inspired_by") else set()
    else:
        sizes = body.get("sizes") or [x.get("size", "med") for x in body.get("panels", [])]
        spec = page_spec(dict(panels=[dict(id=str(i + 1), size=s.rstrip("*"), inset=s.endswith("*")) for i, s in enumerate(sizes)],
                              energy=body.get("energy", 5), beat=body.get("beat", "build")), body.get("reading", "ltr"), int(body.get("seed", 1)))
        excl = set()
    out = []
    for L in inspire(spec, k=int(body.get("k", 3)), model=MODEL, exclude=excl):
        r = L["inspired_by"]; stem = f"insp_{r['key'].replace(':', '_')}_{spec.seed}"
        open(_wd("pages", stem + ".svg"), "w").write(svg(L, scale=40))
        out.append(dict(ref_key=r["key"], inspired_by=f"{r['series']} · {r['chapter']} · page {r['page']}", structure=r["structure"],
                        notes=L["score"]["notes"], size_contrast=L["score"]["size_contrast"],
                        wireframe_url=f"{PUBLIC}/files/pages/{stem}.svg",
                        panels=[dict(panel_id=x["id"], crop_aspect=x["aspect"], ref_shot=x.get("ref_shot")) for x in L["panels"]]))
    return dict(options=out)


def do_relayout(body):
    """Use a specific reference page (ref_key from inspire) for one planned page; rebuilds that page's prompts."""
    from .inspire import adapt
    from .refpool import load_pool
    from .plan import page_spec, page_from_layout
    p = _load_plan(body["plan_id"]); pg = _page(p, body["page"])
    t = next(t for t in load_pool()["templates"] if f"{t['c']}:{t['p']}" == body["ref_key"])
    spec = page_spec(pg["beats"], p.get("reading", "ltr"))
    if t["n"] != len(spec.panels): raise ValueError("that reference has a different panel count")
    L = adapt(t, spec)
    if L is None: raise ValueError("that reference does not map cleanly onto this page")
    page_from_layout(p, pg, L, MODEL)
    with open(_wd("plans", body["plan_id"] + ".json"), "w", encoding="utf-8") as f: json.dump(p, f, ensure_ascii=False, indent=1)
    open(_wd("plans", body["plan_id"] + "_prompts.md"), "w", encoding="utf-8").write(prompts_md(p))
    return dict(page=pg["page"], inspired_by=pg["inspired_by"], score_notes=pg["score"]["notes"],
                panels=[dict(panel_id=x["id"], image_size=x["size"], crop_aspect=x["aspect"], prompt=x["prompt"]) for x in pg["panels"]])


# ----------------------------------------------------------------- HTTP layer
async def api(request):
    try:
        body = await request.json()
        fn = {"plan": do_plan, "compose": do_compose, "generate": do_generate, "inspire": do_inspire,
              "relayout": do_relayout}[request.path_params["op"]]
        return JSONResponse(fn(body))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def files(request):
    rel = request.path_params["path"]
    full = os.path.abspath(os.path.join(WORK, rel))
    if not full.startswith(os.path.abspath(WORK)) or not os.path.exists(full): return Response(status_code=404)
    return FileResponse(full, headers={"Content-Disposition": f'inline; filename="{os.path.basename(full)}"'})


async def index(request):
    return HTMLResponse(open(os.path.join(HERE, "designer", "index.html"), encoding="utf-8").read())


async def model_json(request):
    return JSONResponse(MODEL)


def openapi():
    ref = {"type": "object", "properties": {"name": {"type": "string"}, "id": {"type": "string"}, "mime_type": {"type": "string"}, "download_link": {"type": "string"}}}
    return {
        "openapi": "3.1.0",
        "info": {"title": "mangaforge", "version": "0.1.0", "description": "Plan manga pages from story beats and compose generated panel images into finished pages."},
        "servers": [{"url": PUBLIC}],
        "paths": {
            "/api/plan": {"post": {"operationId": "planPages", "summary": "Plan page layouts and per-panel image prompts from story beats",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {
                    "pages": {"type": "array", "items": {"type": "object", "properties": {
                        "energy": {"type": "number", "description": "0 calm .. 10 climax"},
                        "beat": {"type": "string", "enum": ["calm", "build", "impact", "reveal", "pause", "dread"]},
                        "panels": {"type": "array", "items": {"type": "object", "properties": {
                            "id": {"type": "string"}, "size": {"type": "string", "enum": ["splash", "big", "wide", "med", "close", "insert"]},
                            "shot": {"type": "string"}, "camera": {"type": "string"}, "light": {"type": "string"}, "acting": {"type": "string"},
                            "subject": {"type": "string", "description": "subject cell TL TC TR ML MC MR BL BC BR"},
                            "breakout": {"type": "string", "enum": ["top", "bottom", "left", "right"]}, "inset": {"type": "boolean"},
                            "lettering": {"type": "array", "items": {"type": "object", "properties": {"kind": {"type": "string", "enum": ["dialogue", "thought", "caption", "shout", "sfx"]}, "speaker": {"type": "string"}, "text": {"type": "string"}}}}}}}}}},
                    "style": {"type": "string"}, "cast": {"type": "object", "additionalProperties": {"type": "string"}},
                    "mode": {"type": "string", "enum": ["inspire", "engine", "mix"], "description": "inspire (default): adapt real reference pages; engine: learned generator"}}}}}},
                "responses": {"200": {"description": "plan", "content": {"application/json": {"schema": {"type": "object"}}}}}}},
            "/api/compose": {"post": {"operationId": "composePage", "summary": "Compose one planned page from panel images generated in this chat",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["plan_id", "page"], "properties": {
                    "plan_id": {"type": "string"}, "page": {"type": "integer"},
                    "openaiFileIdRefs": {"type": "array", "items": {"type": "string"}, "description": "The generated panel images for this page, in panel order (max 10)."},
                    "tone": {"type": "string", "enum": ["screen", "bands"], "description": "optional manga ink/screentone pass"}}}}}},
                "responses": {"200": {"description": "page", "content": {"application/json": {"schema": {"type": "object"}}}}}}},
            "/api/inspire": {"post": {"operationId": "inspireLayouts", "summary": "Alternative layouts for one page, each adapted from a real reference manga page (panel shapes only)",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {
                    "plan_id": {"type": "string"}, "page": {"type": "integer"},
                    "sizes": {"type": "array", "items": {"type": "string"}, "description": "instead of a plan page: panel sizes in reading order, e.g. [\"wide\",\"med\",\"close\",\"big\"]; append * for an inset"},
                    "energy": {"type": "number"}, "beat": {"type": "string"}, "k": {"type": "integer"}, "seed": {"type": "integer"}}}}}},
                "responses": {"200": {"description": "options", "content": {"application/json": {"schema": {"type": "object"}}}}}}},
            "/api/relayout": {"post": {"operationId": "useReferenceLayout", "summary": "Switch a planned page to a chosen reference layout (ref_key from inspireLayouts) and rebuild its prompts",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["plan_id", "page", "ref_key"], "properties": {
                    "plan_id": {"type": "string"}, "page": {"type": "integer"}, "ref_key": {"type": "string"}}}}}},
                "responses": {"200": {"description": "page", "content": {"application/json": {"schema": {"type": "object"}}}}}}},
            "/api/generate": {"post": {"operationId": "generateAndCompose", "summary": "Generate any missing panels with the OpenAI Images API on the server, then compose the page",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["plan_id", "page"], "properties": {"plan_id": {"type": "string"}, "page": {"type": "integer"}, "tone": {"type": "string"}}}}}},
                "responses": {"200": {"description": "page", "content": {"application/json": {"schema": {"type": "object"}}}}}}},
        }}


async def openapi_json(request):
    return JSONResponse(openapi())


def build_mcp():
    try:
        from mcp.server.mcpserver import MCPServer as _S       # mcp >= 2
    except ImportError:
        from mcp.server.fastmcp import FastMCP as _S            # mcp 1.x
    m = _S("mangaforge")

    @m.tool()
    def plan_pages(pages: list, style: str = "", cast: dict = None, seed: int = 0, mode: str = "inspire") -> dict:
        """Plan manga pages. pages = [{energy 0-10, beat calm|build|impact|reveal|pause|dread, panels:[{id, size splash|big|wide|med|close|insert, shot, camera, light, acting, subject cell, breakout edge, inset, lettering:[{kind, speaker, text}]}]}]. mode: inspire (default; each page adapts a real reference page's panel shapes) | engine | mix. Returns plan_id, per-panel image prompts, the exact image size to generate, and which reference inspired each page."""
        return do_plan(dict(pages=pages, style=style or None, cast=cast or {}, seed=seed, mode=mode))

    @m.tool()
    def compose_page_images(plan_id: str, page: int, image_urls: list = None, tone: str = "") -> dict:
        """Compose a planned page. image_urls: one URL per panel in panel order (or omit if images were saved to the server's panels folder as <page>_<panel>.png). Returns a link to the finished page."""
        ids = [x["id"] for x in _page(_load_plan(plan_id), page)["panels"]]
        imgs = [dict(panel_id=i, url=u) for i, u in zip(ids, image_urls or []) if u]
        return do_compose(dict(plan_id=plan_id, page=page, images=imgs, tone=tone or None))

    @m.tool()
    def generate_and_compose(plan_id: str, page: int, tone: str = "") -> dict:
        """Generate the page's panels with the OpenAI Images API (server needs OPENAI_API_KEY) and compose them."""
        return do_generate(dict(plan_id=plan_id, page=page, tone=tone or None))

    @m.tool()
    def inspire_layouts(plan_id: str = "", page: int = 0, sizes: list = None, energy: float = 5, beat: str = "build", k: int = 3, seed: int = 1) -> dict:
        """Draw alternative layouts for a page from real reference manga pages (panel shapes only). Either pass plan_id+page, or sizes like ["wide","med","close","big"] (append * for an inset). Each option has a ref_key, the reference it came from, and a wireframe link."""
        return do_inspire(dict(plan_id=plan_id or None, page=page, sizes=sizes, energy=energy, beat=beat, k=k, seed=seed))

    @m.tool()
    def use_reference_layout(plan_id: str, page: int, ref_key: str) -> dict:
        """Switch a planned page to the layout of a given reference (ref_key from inspire_layouts). Returns the page's new panel prompts and image sizes."""
        return do_relayout(dict(plan_id=plan_id, page=page, ref_key=ref_key))

    @m.tool()
    def reference_standards() -> dict:
        """Key numbers learned from the reference manga library (panels per page, size contrast, slant angles, gutters, rhythm)."""
        g = MODEL["global"]
        return dict(pages=MODEL["pages"], panels_per_page=g["panels_per_page_q"], size_contrast=g["size_contrast_q"],
                    slant_page_rate=g["slant_page_rate"], slant_degrees=g["slant_deg_q"], frame_break_page_rate=g["bridge_page_rate"],
                    gutter_fraction_of_width=g["gutter_q"], rhythm=MODEL["rhythm"],
                    top_structures=[dict(sig=s["sig"], share=s["share"], tier_heights=s["tier_h_median"]) for s in MODEL["structures"][:15]])
    return m


def create_app():
    routes = [Route("/", index), Route("/model.json", model_json), Route("/openapi.json", openapi_json),
              Route("/api/{op}", api, methods=["POST"]), Route("/files/{path:path}", files)]
    mcp = None
    try:
        mcp = build_mcp()
        try:   # mcp >= 2
            sub = mcp.streamable_http_app(streamable_http_path="/", stateless_http=True, host=os.environ.get("MANGAFORGE_MCP_HOST", "0.0.0.0"))
        except TypeError:   # mcp 1.x
            mcp.settings.streamable_http_path = "/"; mcp.settings.stateless_http = True
            sub = mcp.streamable_http_app()
        routes.append(Mount("/mcp", app=sub))
    except Exception as e:  # MCP is optional
        print("MCP disabled:", e)

    @contextlib.asynccontextmanager
    async def lifespan(app):
        if mcp is not None and hasattr(mcp, "session_manager"):
            async with mcp.session_manager.run():
                yield
        else:
            yield
    return Starlette(routes=routes, lifespan=lifespan)


def main(argv=None):
    global WORK, PUBLIC
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--workdir", default=WORK); ap.add_argument("--public-url", default=None)
    a = ap.parse_args(argv)
    WORK = os.path.abspath(a.workdir); os.makedirs(WORK, exist_ok=True)
    PUBLIC = a.public_url or f"http://{a.host}:{a.port}"
    import uvicorn
    print(f"mangaforge on {PUBLIC}  ·  designer: {PUBLIC}/  ·  MCP: {PUBLIC}/mcp  ·  actions schema: {PUBLIC}/openapi.json")
    uvicorn.run(create_app(), host=a.host, port=a.port)


if __name__ == "__main__":
    main()
