"""The scheduler's board check reads the hourly report and says what is red."""
import datetime as dt
import json

from checks import scheduler as sc

NOW = dt.datetime(2026, 10, 18, 21, 30, tzinfo=dt.timezone(dt.timedelta(hours=13)))


def record(**over):
    written = NOW - dt.timedelta(minutes=30)
    rec = {
        "written": written.astimezone(dt.timezone.utc).isoformat(timespec="seconds"),
        "queue": {"done": 38, "leased": 1},
        "workers": [{"name": "node2", "box": "node2", "state": "running",
                     "last_seen": (written - dt.timedelta(seconds=20)).isoformat(sep=" ")}],
        "cards": [{"box": "node2", "card": 0, "reserved": True, "profile": None, "holder": None},
                  {"box": "node2", "card": 1, "reserved": False, "profile": "text-reader", "holder": "qv4-reread"}],
        "runs": [{"job": "qv4-checks-board", "outcome": "ok", "finished_at": written.isoformat(sep=" ")}],
    }
    rec.update(over)
    return rec


def write(tmp_path, rec):
    p = tmp_path / "scheduler.json"
    p.write_text(json.dumps(rec, default=str))
    return str(p)


def items(result):
    return {i["name"]: i for i in result["items"]}


def test_a_fresh_report_with_a_live_worker_and_a_clean_reserved_card_is_green(tmp_path):
    r = sc.check(now=NOW, path=write(tmp_path, record()))
    assert r["ok"], r
    assert items(r)["report"]["detail"].startswith("written 0.5 h ago; queue: done 38, leased 1")
    assert items(r)["workers"]["detail"] == "running: node2"


def test_no_report_is_red(tmp_path):
    r = sc.check(now=NOW, path=str(tmp_path / "missing.json"))
    assert not r["ok"] and r["items"][0]["name"] == "report"


def test_a_stale_report_is_red(tmp_path):
    old = (NOW - dt.timedelta(hours=5)).astimezone(dt.timezone.utc).isoformat(timespec="seconds")
    r = sc.check(now=NOW, path=write(tmp_path, record(written=old)))
    assert not items(r)["report"]["ok"] and "5 h ago" in items(r)["report"]["detail"]


def test_a_worker_silent_at_the_report_is_red_and_a_stopped_one_is_not_counted(tmp_path):
    written = NOW - dt.timedelta(minutes=30)
    workers = [{"name": "node2", "state": "running", "last_seen": (written - dt.timedelta(minutes=40)).isoformat(sep=" ")},
               {"name": "node2-b", "state": "stopped", "last_seen": (written - dt.timedelta(hours=9)).isoformat(sep=" ")}]
    r = sc.check(now=NOW, path=write(tmp_path, record(workers=workers)))
    assert not items(r)["workers"]["ok"]
    assert "node2" in items(r)["workers"]["detail"] and "node2-b" not in items(r)["workers"]["detail"]


def test_no_running_worker_is_red(tmp_path):
    r = sc.check(now=NOW, path=write(tmp_path, record(workers=[])))
    assert not items(r)["workers"]["ok"]


def test_a_reserved_card_holding_a_profile_is_red(tmp_path):
    cards = [{"box": "node2", "card": 0, "reserved": True, "profile": "embedding", "holder": None}]
    r = sc.check(now=NOW, path=write(tmp_path, record(cards=cards)))
    assert not items(r)["reserved"]["ok"] and "node2 card 0" in items(r)["reserved"]["detail"]


def test_a_failed_run_inside_the_window_is_red_and_an_old_one_is_not(tmp_path):
    recent = (NOW - dt.timedelta(hours=2)).isoformat(sep=" ")
    old = (NOW - dt.timedelta(hours=40)).isoformat(sep=" ")
    r = sc.check(now=NOW, path=write(tmp_path, record(runs=[{"job": "qv4-reread", "outcome": "failed", "finished_at": old}])))
    assert items(r)["runs"]["ok"]
    r = sc.check(now=NOW, path=write(tmp_path, record(runs=[{"job": "qv4-reread", "outcome": "failed", "finished_at": recent}])))
    assert not items(r)["runs"]["ok"] and "qv4-reread (failed)" in items(r)["runs"]["detail"]


def test_the_live_record_shape_is_read(tmp_path):
    """The shape support/scheduler/queue.py: status writes, with the fields the check uses."""
    rec = record()
    rec["recent"] = []
    rec["swaps"] = []
    r = sc.check(now=NOW, path=write(tmp_path, rec))
    assert {i["name"] for i in r["items"]} == {"report", "workers", "reserved", "runs"}
