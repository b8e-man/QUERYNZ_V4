"""The lessons search returns at most eight rules, one line each with the
file to open, reads the new lessons' first lines and the old index, never
prints a section, and its recall on the eight measured pairs is recorded
here: 3 of 8 at eight, 4 of 8 at twenty on 18 October 2026 (the old tool:
5 of 8 at twenty)."""
import importlib.machinery
import importlib.util
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "bin", "lessons")
_loader = importlib.machinery.SourceFileLoader("lessons_tool", TOOL)
L = importlib.util.module_from_spec(importlib.util.spec_from_loader("lessons_tool", _loader))
_loader.exec_module(L)


def test_at_most_eight_rules_one_line_each_with_the_file():
    p = subprocess.run([sys.executable, TOOL, "watcher", "alarm", "release", "heartbeat"], capture_output=True, text=True)
    lines = [l for l in p.stdout.splitlines() if l.startswith("- ")]
    assert 1 <= len(lines) <= 8
    assert any("watcher is proven by stopping" in l for l in lines)
    wheres = [l.strip() for l in p.stdout.splitlines() if l.startswith("    ")]
    assert all(w.startswith(("lessons/", "reference/lessons-old/")) for w in wheres)
    assert len(p.stdout) < 4000       # a handful of lines, never a section


def test_new_lessons_and_the_old_index_are_both_read():
    corpus = L.rules()
    assert any(w.startswith("lessons/") for _, w in corpus) and any(w.startswith("reference/lessons-old/") for _, w in corpus)
    assert len(corpus) > 500
    got = L.rank(L.words("a heredoc failure does not stop the chain commit"), corpus)
    assert any("heredoc" in r for _, r, _ in got)


def test_recall_on_the_eight_pairs_is_recorded():
    hits, text = L.selftest()
    assert hits >= 3, text          # the floor measured on 18 October 2026; raise it when the search improves
    assert "recall@8" in text and "recall@20" in text


def test_a_thin_result_says_to_search_again():
    p = subprocess.run([sys.executable, TOOL, "zqxv", "qwpl"], capture_output=True, text=True)
    assert "search again" in p.stdout
