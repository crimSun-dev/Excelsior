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

def test_census_rules():
    """New rules fire only on an explicit mark. K-nity plans do not gain them."""
    plan = {
        "pages": [
            {"no": 1, "beat": "talk", "panels": [{"id": "1.1", "shot": "CU", "gaze": "at-reader", "art": "a face"}]},
            {"no": 2, "beat": "gag", "panels": [{"id": "2.1", "shot": "CU", "to_reader": True, "art": "a face"}]},
            {"no": 3, "beat": "talk", "panels": [{"id": "3.1", "shot": "CU", "gaze": "forward", "art": "a face"}]},
            {"no": 4, "beat": "talk", "panels": [{"id": "4.1", "shot": "CU", "to_reader": True, "listener": True, "art": "a face"}]},
            {"no": 5, "beat": "impact", "panels": [{"id": "5.1", "border_break": True, "art": "a fist"}]},
            {"no": 6, "beat": "impact", "panels": [{"id": "6.1", "border_break": True, "overrun_w": 0.04, "overrun_h": 0.1, "art": "a fist"}]},
            {"no": 7, "beat": "talk", "absurdity": [{"expectation": "the room stays calm", "setup": [], "break": [{"page": 7, "panel": 0}]}],
             "panels": [{"id": "7.1", "art": "the gag"}]},
            {"no": 8, "beat": "talk", "absurdity": [{"expectation": "the room stays calm", "setup": [{"page": 7, "panel": 0}], "break": [{"page": 8, "panel": 0}]}],
             "panels": [{"id": "8.1", "art": "the gag"}]},
        ]
    }
    path = os.path.join(tempfile.mkdtemp(), "census.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f)
    d = json.loads(run("detect.py", "--json", path, cwd=os.path.dirname(path)).stdout)
    rules = {(f["rule"], f["page"]) for f in d["findings"]}
    assert ("expr-reader-address", 1) in rules
    assert ("expr-reader-address", 2) not in rules
    assert ("expr-reader-address", 3) not in rules
    assert ("expr-reader-address", 4) not in rules
    assert ("wall-overrun-unmarked", 5) in rules
    assert ("wall-overrun-unmarked", 6) not in rules
    assert ("absurd-break-without-setup", 7) in rules
    assert ("absurd-break-without-setup", 8) not in rules
    for name in ("CH01_plan_v4.json", "CH02_plan_v3.json"):
        kn = json.loads(run("detect.py", "--json", name).stdout)
        assert not any(f["rule"] in ("expr-reader-address", "wall-overrun-unmarked", "absurd-break-without-setup") for f in kn["findings"])

if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
    shutil.rmtree(os.path.join(EX, ".excelsior"), ignore_errors=True)
