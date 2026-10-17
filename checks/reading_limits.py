"""The reading-limit check (plan 1b.8; index: "A check holds the limits").

Each plan file against its limit in the index table of `docs/PLAN.md`
(the "File | Holds | Limit" table; `None` means no limit; a row naming
`step-0.md` to `step-7.md` or `track-a.md` to `track-h.md` binds each of
them), every status file against 3 KB, and the orientation file's
"Hard limits" against `docs/plan/limits.md` word for word. A kilobyte is
1,000 bytes. Runs in the fast tier (tests/test_reading_limits.py) and as
`python -m checks.reading_limits`.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_LIMIT = 3_000
KB = 1_000


def limits_from_index(index_text: str) -> dict:
    """file (relative to the repository) → bytes, from the index table."""
    out = {}
    for line in index_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].startswith("---") or cells[0] == "File":
            continue
        m = re.search(r"(\d+)\s*KB", cells[-1])
        if not m:
            continue
        limit = int(m.group(1)) * KB
        names = re.findall(r"`([^`]+)`", cells[0])
        for n in names:
            n = n.strip()
            if n == "CLAUDE.md":
                out["CLAUDE.md"] = limit
            elif n.endswith(".md") and "/" in n:
                out[n] = limit
            elif re.fullmatch(r"step-\d+[a-z]?\.md", n):
                out[f"docs/plan/{n}"] = limit
            elif re.fullmatch(r"track-[a-h]\.md", n):
                out[f"docs/plan/{n}"] = limit
        if re.search(r"step-0\.md` to `step-7\.md`", cells[0]):
            for i in range(8):
                out[f"docs/plan/step-{i}.md"] = limit
            out["docs/plan/step-1b.md"] = limit
        if re.search(r"track-a\.md` to `track-h\.md`", cells[0]):
            for c in "abcdefgh":
                out[f"docs/plan/track-{c}.md"] = limit
            out["docs/plan/tracks.md"] = limit
    return out


def hard_limits_section(text: str) -> str:
    m = re.search(r"^## Hard limits\s*$(.*)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def check(repo: str = None) -> list:
    repo = repo or REPO
    problems = []
    try:
        index = open(os.path.join(repo, "docs", "PLAN.md"), encoding="utf-8").read()
    except OSError:
        return ["docs/PLAN.md is missing"]
    for rel, limit in sorted(limits_from_index(index).items()):
        p = os.path.join(repo, rel)
        if not os.path.isfile(p):
            continue
        size = os.path.getsize(p)
        if size > limit:
            problems.append(f"{rel} is {size:,} bytes; its limit is {limit:,}")
    for folder in ("docs", os.path.join("docs", "status")):
        d = os.path.join(repo, folder)
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            if (folder == "docs" and n == "status.md") or (folder != "docs" and n.endswith(".md")):
                size = os.path.getsize(os.path.join(d, n))
                if size > STATUS_LIMIT:
                    problems.append(f"{folder}/{n} is {size:,} bytes; a status file stays under {STATUS_LIMIT:,}")
    try:
        orient = hard_limits_section(open(os.path.join(repo, "CLAUDE.md"), encoding="utf-8").read())
        master = hard_limits_section(open(os.path.join(repo, "docs", "plan", "limits.md"), encoding="utf-8").read())
        if orient != master:
            problems.append("CLAUDE.md's Hard limits differ from docs/plan/limits.md")
    except OSError as exc:
        problems.append(f"cannot compare the hard limits: {exc}")
    return problems


def main() -> int:
    problems = check()
    for p in problems:
        print("OVER " + p)
    print("reading limits: " + ("within limits" if not problems else f"{len(problems)} over"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
