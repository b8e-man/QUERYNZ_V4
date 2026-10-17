"""The reading-limit check: the repository itself is within its limits; a
file one byte over fails; a status file over 3 KB fails; the orientation
file's hard limits must match the master."""
import os
import shutil
import tempfile

from checks import reading_limits as rl

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_repository_is_within_its_limits():
    assert rl.check(REPO) == []


def test_limits_are_read_from_the_index_table():
    lim = rl.limits_from_index(open(os.path.join(REPO, "docs", "PLAN.md"), encoding="utf-8").read())
    assert lim["CLAUDE.md"] == 10_000 and lim["docs/PLAN.md"] == 5_000 and lim["docs/plan/core.md"] == 27_000
    assert lim["docs/plan/limits.md"] == 7_000 and lim["docs/plan/step-1b.md"] == 28_000 and lim["docs/plan/track-h.md"] == 28_000
    assert "docs/plan/design.md" not in lim     # no limit


def toy_repo():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "docs", "plan"))
    os.makedirs(os.path.join(d, "docs", "status"))
    with open(os.path.join(d, "docs", "PLAN.md"), "w") as f:
        f.write("# Plan\n\n| File | Holds | Limit |\n| --- | --- | --- |\n| `CLAUDE.md`, at the top | x | 10 KB |\n"
                "| `docs/plan/core.md` | y | 27 KB |\n| `docs/plan/step-0.md` to `step-7.md`, and `step-1b.md` | z | 28 KB |\n")
    with open(os.path.join(d, "docs", "plan", "limits.md"), "w") as f:
        f.write("## Hard limits\n\n1. one\n")
    with open(os.path.join(d, "CLAUDE.md"), "w") as f:
        f.write("# orient\n\n## Hard limits\n\n1. one\n")
    with open(os.path.join(d, "docs", "status.md"), "w") as f:
        f.write("ok\n")
    return d


def test_one_byte_over_fails_and_the_limit_itself_passes():
    d = toy_repo()
    try:
        p = os.path.join(d, "docs", "plan", "core.md")
        with open(p, "w") as f:
            f.write("x" * 27_000)
        assert rl.check(d) == []
        with open(p, "a") as f:
            f.write("x")
        assert rl.check(d) == ["docs/plan/core.md is 27,001 bytes; its limit is 27,000"]
        s = os.path.join(d, "docs", "status", "sess.md")
        with open(s, "w") as f:
            f.write("y" * 3_001)
        assert any("docs/status/sess.md is 3,001 bytes" in x for x in rl.check(d))
        with open(os.path.join(d, "CLAUDE.md"), "a") as f:
            f.write("2. two\n")
        assert "CLAUDE.md's Hard limits differ from docs/plan/limits.md" in rl.check(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
