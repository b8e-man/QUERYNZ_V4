"""The orientation file: up to 3 KB of orientation, then the hard limits
whole, copied from docs/plan/limits.md; 10 KB in all. A check fails if the
copy differs (plan: "What to read, and how much")."""
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE = os.path.join(REPO, "CLAUDE.md")
LIMITS = os.path.join(REPO, "docs", "plan", "limits.md")


def test_orientation_carries_the_hard_limits_unchanged_and_fits():
    text = open(CLAUDE, encoding="utf-8").read()
    limits = open(LIMITS, encoding="utf-8").read()
    assert text.endswith(limits), "CLAUDE.md must end with docs/plan/limits.md, byte for byte"
    orientation = text[: -len(limits)]
    assert len(orientation.encode("utf-8")) <= 3000, f"orientation is {len(orientation.encode('utf-8'))} bytes; 3 KB"
    assert len(text.encode("utf-8")) <= 10000
    for must in ("docs/PLAN.md", "docs/plan/map.md", "docs/status.md", "docs/board.md", "bin/ask",
                 "/home/user/Git Repos/QueryNZ_V3", "/home/user/qnz3-ref", "/home/user/querynzv4-work/inbox"):
        assert must in orientation, must
