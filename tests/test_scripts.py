"""Smoke tests: python3 -m pytest tests  (or python3 tests/test_scripts.py)"""
import json, os, subprocess, sys, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); S = os.path.join(ROOT, "scripts"); EX = os.path.join(ROOT, "examples", "knity")

def run(*a, cwd=EX):
    return subprocess.run([sys.executable, os.path.join(S, a[0]), *a[1:]], capture_output=True, text=True, cwd=cwd)

def test_detect():
    r = run("detect.py", "--json", "CH01_plan_v4.json"); assert r.returncode in (0, 2); d = json.loads(r.stdout); assert "score" in d and d["stats"]

def test_rules():
    assert len(json.loads(run("detect.py", "--rules", "x").stdout)) >= 30

def test_seed():
    d = json.loads(run("concept_seed.py", "--scope", "direction", "--mode", "hook", "--seed", "3").stdout); assert d["assigned_rank"] >= 1 and d["challengers"]

def test_inspire():
    d = json.loads(run("inspire_page.py", "CH01_plan_v4.json", "--page", "9", "--k", "2").stdout); assert d["variants"]

def test_proof():
    out = os.path.join(tempfile.mkdtemp(), "p.html"); assert run("proof.py", "CH01_plan_v4.json", "--out", out, "--pages", "1-3").returncode == 0 and os.path.exists(out)

def test_context():
    assert "DIRECTIVE FORMAT print" in run("context.py").stdout

if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
    shutil.rmtree(os.path.join(EX, ".excelsior"), ignore_errors=True)
