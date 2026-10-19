"""The windowed lanes on the checks board (track E, merge request windowed-1).
Each lane's own outside check (`python -m registers.<lane>.check`) compares
the source's own counts, as last listed, with what is held; it exits 0 when
nothing is short, 1 when a month or year is short, and prints the summary.
Imports run one way (checks import support only), so the lane checks run as
commands and the board reads their exit code and last lines. Stdlib only."""
import os
import subprocess
import sys

LANES = ("tenancy_tribunal", "real_estate_authority")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT_S = 120


def run_lane(lane: str) -> tuple[int, str]:
    """(exit code, output) of the lane's check, run with this interpreter."""
    try:
        p = subprocess.run([sys.executable, "-m", f"registers.{lane}.check"], cwd=REPO,
                           capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return 3, f"no answer in {TIMEOUT_S} s"
    return p.returncode, (p.stdout + p.stderr).strip()


def check(run=run_lane, lanes=LANES) -> dict:
    items = []
    for lane in lanes:
        rc, out = run(lane)
        lines = [l for l in out.splitlines() if l.strip()]
        if rc == 0:
            detail = "; ".join(lines[:3]) or "nothing short"
            items.append({"name": lane, "ok": True, "detail": detail})
        elif rc == 1:
            short = [l.strip() for l in lines if l.strip().startswith("short")]
            items.append({"name": lane, "ok": False, "detail": "short: " + ("; ".join(short[:5]) or "; ".join(lines[-3:]))})
        else:
            items.append({"name": lane, "ok": False, "detail": f"the check failed (exit {rc}): {'; '.join(lines[-2:]) or 'no output'}"})
    return {"check": "windowed", "ok": all(i["ok"] for i in items), "alarms": [], "items": items}
