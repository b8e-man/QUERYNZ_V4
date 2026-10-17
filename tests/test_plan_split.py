"""The split is proven (plan step 1.1): every line of the original lands in
exactly one piece, joining the pieces in the recorded order gives the
original back, every heading is in headings.md, and every file is within
the limit the index sets. The original is read from git at the commit the
manifest names, so the proof reruns the split as a pure function and does
not depend on the live pieces, which rulings edit later."""
import importlib.util
import json
import os
import subprocess
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN_DIR = os.path.join(REPO, "docs", "plan")
MANIFEST = os.path.join(PLAN_DIR, "manifest.json")
LIMITS = {"PLAN.md": 5000, "core.md": 27000, "limits.md": 7000, "step-": 28000, "track": 28000}
pytestmark = pytest.mark.skipif(not os.path.exists(MANIFEST), reason="the plan is not split yet")


def _tool():
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader("split_plan", os.path.join(REPO, "bin", "split-plan"))
    spec = importlib.util.spec_from_loader("split_plan", loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def original():
    m = json.load(open(MANIFEST))
    p = subprocess.run(["git", "show", f"{m['source_commit']}:{m['source_path']}"], cwd=REPO, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return m, p.stdout


def test_every_line_lands_once_and_the_pieces_rejoin(original):
    m, text = original
    tool = _tool()
    pieces = tool.split(text)
    assert sum(len(b) for _, _, b in pieces) == len(text.splitlines(keepends=True))
    assert [p["lines"] for p in m["pieces"]] == [len(b) for _, _, b in pieces]
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "PLAN.md")
        open(src, "w", encoding="utf-8").write(text)
        out = os.path.join(d, "plan")
        p = subprocess.run(["python3", os.path.join(REPO, "bin", "split-plan"), "--source", src, "--out", out, "--commit", "x"],
                           capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        fresh = json.load(open(os.path.join(out, "manifest.json")))

        def read(f):
            return open(os.path.join(d, f) if f == "PLAN.md" else os.path.join(out, f), encoding="utf-8").read()
        assert tool.rejoin(fresh, read) == text
        # a file is made of pieces that need not sit together in the document
        assert len({i for i, p in enumerate(fresh["pieces"]) if p["file"] == "core.md"}) > 1
        for f, limit in LIMITS.items():
            for name in os.listdir(out if f != "PLAN.md" else d):
                if name.startswith(f) and name.endswith(".md"):
                    size = os.path.getsize(os.path.join(out if f != "PLAN.md" else d, name))
                    assert size <= limit, f"{name} is {size} bytes; its limit is {limit}"


def test_the_live_pieces_exist_and_headings_md_names_every_heading(original):
    m, text = original
    for p in m["pieces"]:
        path = os.path.join(REPO, "docs", "PLAN.md") if p["file"] == "PLAN.md" else os.path.join(PLAN_DIR, p["file"])
        assert os.path.isfile(path), p["file"]
    headings = open(os.path.join(PLAN_DIR, "headings.md"), encoding="utf-8").read()
    for ln in text.splitlines():
        if ln.startswith("## ") or ln.startswith("### "):
            assert f"- {ln.strip()} →" in headings, ln
    for step in ("1.1", "1.11", "1b.9", "2.15", "4.9", "7.7", "H.5", "D.2"):
        assert f"- {step} →" in headings, step


def test_an_unknown_or_misordered_heading_is_refused(original):
    tool = _tool()
    _, text = original
    with pytest.raises(SystemExit):
        tool.split(text.replace("### Who Arthur is", "### Who Arthur was", 1))
    with pytest.raises(SystemExit):
        tool.split(text + "\n## A new section\n")
