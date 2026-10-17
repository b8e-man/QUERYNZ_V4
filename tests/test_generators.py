"""The three generators read one small file per card, lesson and question and
write the one file nobody edits. Each refuses a record it cannot read, and
the committed records all generate cleanly (so a malformed card never
reaches main)."""
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(REPO, "bin")


def run(tool, repo):
    return subprocess.run([sys.executable, os.path.join(BIN, tool), "--repo", repo], capture_output=True, text=True)


@pytest.fixture
def toy(tmp_path):
    for d in ("cards", "lessons", "docs/decisions/queue"):
        (tmp_path / d).mkdir(parents=True)
    return str(tmp_path)


def test_board_sorts_cards_into_board_and_parking(toy):
    cards = {
        "fence-live-on-save": "# The fence went live on save\nkind: blocker\nstate: closed\nsession: founding-1\nopened: 2026-10-18\nclosed: 2026-10-18\n\nFixed.\n",
        "donor-page-cut": "# Donor list cut at 1,500\nkind: finding\nstate: open\nuse-case: 1\nsession: ftm-compare\nopened: 2026-10-20\n\nSeen.\n",
        "gate-slow": "# The gate is slow\nkind: blocker\nstate: open\nsession: founding-2\nopened: 2026-10-19\n\nHm.\n",
        "pane-colours": "# Colour the panes\nkind: idea\nstate: open\nsession: board-1\nopened: 2026-10-21\n\nLater.\n",
        "accepted-one": "# Not held: votes\nkind: finding\nstate: accepted\nuse-case: 1\nsession: x\nopened: 2026-10-20\nclosed: 2026-10-22\n\nOn the limits page.\n",
    }
    for n, t in cards.items():
        open(os.path.join(toy, "cards", n + ".md"), "w").write(t)
    p = run("board", toy)
    assert p.returncode == 0, p.stderr
    board = open(os.path.join(toy, "docs", "board.md")).read()
    park = open(os.path.join(toy, "docs", "parking.md")).read()
    assert "## Blockers open: 1" in board and "gate-slow" in board and "fence-live-on-save" not in board.split("## Off the board")[0]
    assert "## Findings open: 1" in board and "donor-page-cut" in board
    assert "Closed 1 · accepted onto a known-limits page 1 · dropped 0" in board
    assert "pane-colours" in park and "pane-colours" not in board
    assert run("board", toy).stdout.strip() == "board: unchanged"
    open(os.path.join(toy, "cards", "bad.md"), "w").write("# Bad\nkind: wish\nstate: open\nsession: x\nopened: 2026-10-18\n")
    p = run("board", toy)
    assert p.returncode == 1 and "kind must be" in p.stderr
    open(os.path.join(toy, "cards", "bad.md"), "w").write("# Bad\nkind: finding\nstate: closed\nsession: x\nopened: 2026-10-18\n")
    p = run("board", toy)
    assert p.returncode == 1 and "closed:" in p.stderr


def test_lessons_index_is_one_line_per_rule(toy):
    open(os.path.join(toy, "lessons", "a-hook-is-live.md"), "w").write(
        "A hook is live the moment its file is saved.\narea: fences\npaid-for-by: 2026-10-18\n\nWhy.\n")
    open(os.path.join(toy, "lessons", "b.md"), "w").write("Second rule here.\narea: gate, tests\n\nWhy.\n")
    p = run("lessons-index", toy)
    assert p.returncode == 0, p.stderr
    idx = open(os.path.join(toy, "lessons", "INDEX.md")).read()
    assert "- A hook is live the moment its file is saved. — `a-hook-is-live.md` (fences)" in idx
    assert "- Second rule here. — `b.md` (gate, tests)" in idx
    assert idx.count("\n- ") == 2
    open(os.path.join(toy, "lessons", "c.md"), "w").write("# A heading is not a rule\narea: x\n\nWhy.\n")
    p = run("lessons-index", toy)
    assert p.returncode == 1 and "first line must be the rule" in p.stderr
    os.remove(os.path.join(toy, "lessons", "c.md"))
    open(os.path.join(toy, "lessons", "d.md"), "w").write("No area line.\n\nWhy.\n")
    assert run("lessons-index", toy).returncode == 1


def test_decisions_queue_separates_no_default(toy):
    q = os.path.join(toy, "docs", "decisions", "queue")
    open(os.path.join(q, "switch.md"), "w").write(
        "# When the rebuilt site replaces the frozen one\ndefault: none\nblocks: step 4.8\nrecommendation: after seven clean days\nraised: 2026-10-18 by founding-1\n")
    open(os.path.join(q, "card-free.md"), "w").write(
        "# Whether one card is kept free\ndefault: no card is kept empty\nblocks: nothing\nrecommendation: the default\nraised: 2026-10-18 by founding-1\n\nMore.\n")
    p = run("decisions", toy)
    assert p.returncode == 0, p.stderr
    out = open(os.path.join(toy, "docs", "decisions", "queue.md")).read()
    assert "## No default: 1" in out and "## With a default: 1" in out
    assert "[When the rebuilt site replaces the frozen one](queue/switch.md) | none | step 4.8" in out
    open(os.path.join(q, "bad.md"), "w").write("# No fields\n\nbody\n")
    p = run("decisions", toy)
    assert p.returncode == 1 and "missing" in p.stderr


def test_the_committed_records_generate_cleanly():
    """Run against the repository itself: every card, lesson and question in
    git must be readable, and the generated files must be current."""
    for tool, out in (("board", "docs/board.md"), ("lessons-index", "lessons/INDEX.md"), ("decisions", "docs/decisions/queue.md")):
        before = open(os.path.join(REPO, out)).read() if os.path.exists(os.path.join(REPO, out)) else None
        p = run(tool, REPO)
        assert p.returncode == 0, p.stderr
        after = open(os.path.join(REPO, out)).read()
        assert before == after, f"{out} was stale: run bin/{tool} and commit it"
