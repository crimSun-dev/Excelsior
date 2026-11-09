# -*- coding: utf-8 -*-
"""OpenAI image generation adapter (no SDK needed). Reads OPENAI_API_KEY from the environment.

Model is configurable (MANGAFORGE_IMAGE_MODEL, default gpt-image-1). Check OpenAI's docs for the
current model names and sizes; this adapter only uses the documented generations/edits endpoints.
    python -m mangaforge.imagegen plan.json --out panels --pages 17-20 [--refs cast/kkiri.png ...]
"""
import argparse, base64, json, os, sys, time, urllib.request, uuid, mimetypes

API = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("MANGAFORGE_IMAGE_MODEL", "gpt-image-1")


def _post_json(url, payload, key):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r: return json.load(r)


def _post_multipart(url, fields, files, key):
    bnd = uuid.uuid4().hex; body = b""
    for k, v in fields.items():
        body += f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, path in files:
        mt = mimetypes.guess_type(path)[0] or "image/png"
        body += f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{os.path.basename(path)}\"\r\nContent-Type: {mt}\r\n\r\n".encode()
        body += open(path, "rb").read() + b"\r\n"
    body += f"--{bnd}--\r\n".encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={bnd}"})
    with urllib.request.urlopen(req, timeout=300) as r: return json.load(r)


def generate(prompt, size="1024x1024", quality="medium", refs=None, out_path=None, key=None, model=None):
    key = key or os.environ.get("OPENAI_API_KEY")
    if not key: raise RuntimeError("Set OPENAI_API_KEY (or use manual mode: generate in ChatGPT and drop files into the panels folder)")
    model = model or MODEL
    if refs:  # character consistency: pass model sheets as reference images to the edits endpoint
        res = _post_multipart(f"{API}/images/edits", dict(model=model, prompt=prompt, size=size, quality=quality),
                              [("image[]", r) for r in refs], key)
    else:
        res = _post_json(f"{API}/images/generations", dict(model=model, prompt=prompt, size=size, quality=quality, n=1), key)
    b64 = res["data"][0].get("b64_json")
    if not b64 and res["data"][0].get("url"):
        with urllib.request.urlopen(res["data"][0]["url"]) as r: data = r.read()
    else: data = base64.b64decode(b64)
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        open(out_path, "wb").write(data)
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("plan"); ap.add_argument("--out", default="panels"); ap.add_argument("--pages")
    ap.add_argument("--quality", default="medium"); ap.add_argument("--refs", nargs="*")
    ap.add_argument("--budget", type=int, default=40, help="max images this run")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    p = json.load(open(a.plan, encoding="utf-8")); n = 0
    lo, hi = (int(x) for x in a.pages.split("-")) if a.pages else (-10**9, 10**9)
    log = open(os.path.join(a.out, "generations.jsonl") if os.path.isdir(a.out) else "generations.jsonl", "a")
    for pg in p["pages"]:
        if not lo <= pg["page"] <= hi: continue
        for x in pg["panels"]:
            path = os.path.join(a.out, f"{pg['page']}_{x['id']}.png")
            if os.path.exists(path): continue  # cache: never pay twice
            if n >= a.budget: print("budget reached"); return
            print("gen", path, x["size"]); n += 1
            if a.dry_run: continue
            generate(x["prompt"], x["size"], a.quality, a.refs, path)
            log.write(json.dumps(dict(t=time.time(), file=path, model=MODEL, size=x["size"], prompt=x["prompt"])) + "\n"); log.flush()


if __name__ == "__main__":
    main()
