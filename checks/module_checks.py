"""The lanes' and the products' own checks on the board (plan 4.5, second
tranche; the way windowed.py does it for track E's two lanes).

Every `registers/<lane>/check.py` with a `main`, and the two products that
have one (`products/board`, `products/published_site`), is run as a
command with a timeout, the way the module itself documents:

    python -m registers.<lane>.check
    python -m products.board check
    python -m products.published_site check

Imports run one way (checks import support only), so the board reads each
check's exit code and last lines and never imports a lane. Exit 0 is
green with the first lines as detail; 1 is red with the lines that name
what is short or differs; anything else (a crash, a timeout) is red and
says so. The two windowed lanes already sit on the board through
windowed.py and are left out here. Stdlib only.
Tests: checks/tests/test_module_checks.py."""
from __future__ import annotations

import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "module-checks"
#: on the board already, through windowed.py
ELSEWHERE = {"tenancy_tribunal", "real_estate_authority"}
PRODUCTS = {"board": ["python", "-m", "products.board", "check"],
            "published_site": ["python", "-m", "products.published_site", "check"]}
#: measured on node2, 20 October 2026: every check answered in under two
#: seconds (the slowest, gazette and the board, in 1.0 s); the allowance is
#: a hundredfold, and a check past it is red and says so, never skipped
DEFAULT_TIMEOUT_S = 120
TIMEOUTS_S: dict = {}
_MAIN = re.compile(r"^def main\(", re.M)


def discover(repo: str = None) -> dict:
    """{name: command} for every lane check with a main, and the products."""
    repo = repo or REPO
    out = {}
    lanes = os.path.join(repo, "registers")
    try:
        names = sorted(os.listdir(lanes))
    except OSError:
        names = []
    for lane in names:
        if lane in ELSEWHERE or lane.startswith(("_", ".")):
            continue
        path = os.path.join(lanes, lane, "check.py")
        try:
            with open(path, encoding="utf-8") as f:
                src = f.read()
        except OSError:
            continue
        if _MAIN.search(src):
            out[lane] = ["python", "-m", f"registers.{lane}.check"]
    for prod, cmd in PRODUCTS.items():
        if os.path.exists(os.path.join(repo, "products", prod, "check.py")):
            out[prod] = list(cmd)
    return out


def run_one(name: str, cmd: list, timeout_s: int = None, repo: str = None) -> tuple:
    """(exit code, output) of one check, run with this interpreter."""
    timeout_s = timeout_s or TIMEOUTS_S.get(name, DEFAULT_TIMEOUT_S)
    argv = [sys.executable] + cmd[1:] if cmd and cmd[0] == "python" else cmd
    try:
        p = subprocess.run(argv, cwd=repo or REPO, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return 3, f"no answer in {timeout_s} s"
    except OSError as exc:
        return 4, f"could not run: {exc}"
    return p.returncode, (p.stdout + p.stderr).strip()


def item(name: str, rc: int, out: str) -> dict:
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    if rc == 0:
        return {"name": name, "ok": True, "detail": "; ".join(lines[:2])[:300] or "green, no output"}
    if rc == 1:
        telling = [l for l in lines if re.search(r"\b(short|differ|red|fail|missing|not held|unequal|mismatch)", l, re.I)]
        return {"name": name, "ok": False, "detail": ("; ".join(telling[:4]) or "; ".join(lines[-3:]) or "red, no output")[:400]}
    return {"name": name, "ok": False, "detail": f"the check did not run (exit {rc}): {'; '.join(lines[-2:]) or 'no output'}"[:400]}


def check(run=run_one, commands: dict = None, *, now=None) -> dict:
    items = []
    for name, cmd in (commands or discover()).items():
        rc, out = run(name, cmd)
        items.append(item(name, rc, out))
    return {"check": NAME, "ok": all(i["ok"] for i in items), "alarms": [], "items": items}


def main(argv=None) -> int:
    """Run them all and print the items, timing each (for setting TIMEOUTS_S)."""
    import time
    red = 0
    for name, cmd in discover().items():
        t = time.time()
        rc, out = run_one(name, cmd)
        i = item(name, rc, out)
        red += not i["ok"]
        print(f"{'ok ' if i['ok'] else 'RED'}  {name:<18} {time.time() - t:6.1f} s  {i['detail']}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
