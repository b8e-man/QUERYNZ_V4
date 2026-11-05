"""The files under `live` that belong to one box carry its name (5 November 2026, node1's return):
with `live` shared over NFS, two boxes must never read or write each other's watchdog state or night mark."""
import json
import os

from support.scheduler import cards, watchdog


def test_watchdog_files_carry_the_box():
    box = os.uname().nodename
    assert watchdog.STATE.endswith(f"radiance-watchdog-state-{box}.json")
    assert watchdog.LOG.endswith(f"radiance-watchdog-{box}.jsonl")


def test_the_night_mark_carries_the_box():
    # read in a fresh process: conftest has moved this process's NIGHT_MARK into the test's folder
    import subprocess, sys
    out = subprocess.run([sys.executable, "-c", "from support.scheduler import cards; print(cards.NIGHT_MARK)"],
                         capture_output=True, text=True, check=True).stdout.strip()
    assert os.path.basename(out) == f"night-window-{os.uname().nodename}.json"


def test_a_mark_under_the_old_name_is_recovered_only_on_node2(tmp_path, monkeypatch):
    before, own = tmp_path / "night-window.json", tmp_path / "night-window-node2.json"
    before.write_text(json.dumps({"unit": "qv4-radiance", "worker": "node2", "since": "x"}))
    monkeypatch.setattr(cards, "NIGHT_MARK", str(own))
    monkeypatch.setattr(cards, "NIGHT_MARK_BEFORE", str(before))
    logs = []
    m = cards.Manager(window=None, log=logs.append, reservations=[])
    for name, moved in (("node1", False), ("node2", True)):
        monkeypatch.setattr(os, "uname", lambda n=name: os.uname_result(("Linux", n, "", "", "")))
        class W: box = name; alarm = staticmethod(lambda *a: None)
        m.night_recover(W())
        assert own.exists() is moved and before.exists() is not moved
