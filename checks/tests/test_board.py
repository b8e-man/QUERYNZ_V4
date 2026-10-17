"""The board runs its checks, alarms on every red and every raised alarm,
leaves its exit red, writes the board and a run record; the heartbeat
alarms when the board is stale; the job files carry the qv4- prefix and a
deadline."""
import datetime as dt
import json
import os
import re

from checks import board

NOW = dt.datetime(2026, 10, 18, 7, 30, tzinfo=dt.timezone(dt.timedelta(hours=13)))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def green(now=None):
    return {"check": "fake-green", "ok": True, "items": [{"name": "a", "ok": True, "detail": "fine"}], "alarms": []}


def red(now=None):
    return {"check": "fake-red", "ok": False, "items": [{"name": "b", "ok": False, "detail": "broken"}],
            "alarms": [("mail", "something arrived")]}


def crashes(now=None):
    raise RuntimeError("boom")


def test_green_board_exits_zero_and_sends_nothing(tmp_path, capsys):
    sent = []
    rc = board.run_board([green], now=NOW, board_path=str(tmp_path / "board.json"),
                         send=lambda t, b, **k: sent.append((t, b)) or True, runs_path=str(tmp_path / "runs.jsonl"))
    assert rc == 0 and sent == []
    b = json.load(open(tmp_path / "board.json"))
    assert b["ok"] and b["ran_at"] == NOW.isoformat(timespec="seconds")
    run = json.loads(open(tmp_path / "runs.jsonl").read().splitlines()[-1])
    assert run["job"] == "qv4-checks-board" and run["ok"] and run["red"] == 0
    assert "GREEN" in capsys.readouterr().out


def test_red_item_and_raised_alarm_each_send_and_the_exit_is_red(tmp_path):
    sent = []
    rc = board.run_board([green, red], now=NOW, board_path=str(tmp_path / "board.json"),
                         send=lambda t, b, **k: sent.append((t, b)) or True, runs_path=str(tmp_path / "runs.jsonl"))
    assert rc == 1
    titles = [t for t, _ in sent]
    assert any("fake-red/b red" in t for t in titles) and any(t.endswith(": mail") for t in titles)
    b = json.load(open(tmp_path / "board.json"))
    assert not b["ok"] and b["alarms_sent"] == 2


def test_a_crashing_check_is_a_red_item_not_a_dead_board(tmp_path):
    sent = []
    rc = board.run_board([crashes, green], now=NOW, board_path=str(tmp_path / "board.json"),
                         send=lambda t, b, **k: sent.append((t, b)) or True, runs_path=str(tmp_path / "runs.jsonl"))
    assert rc == 1 and len(sent) == 1 and "RuntimeError: boom" in sent[0][1]
    b = json.load(open(tmp_path / "board.json"))
    assert [r["check"] for r in b["results"]] == ["test-board", "test-board"] or len(b["results"]) == 2


def test_heartbeat_alarms_when_the_board_is_stale_or_missing(tmp_path):
    sent = []
    send = lambda t, b, **k: sent.append((t, b)) or True  # noqa: E731
    p = str(tmp_path / "board.json")
    assert board.heartbeat(now=NOW, board_path=p, send=send) == 1 and "never run" in sent[-1][0]
    board.run_board([green], now=NOW, board_path=p, send=send, runs_path=str(tmp_path / "runs.jsonl"))
    assert board.heartbeat(now=NOW + dt.timedelta(hours=20), board_path=p, send=send) == 0
    assert board.heartbeat(now=NOW + dt.timedelta(hours=27), board_path=p, send=send) == 1
    assert "stale" in sent[-1][0] and "27 h ago" in sent[-1][1]


def test_job_files_carry_the_prefix_a_deadline_and_a_persistent_timer():
    jobs = os.path.join(REPO, "checks", "jobs")
    names = sorted(os.listdir(jobs))
    assert names == ["qv4-checks-board.service", "qv4-checks-board.timer",
                     "qv4-checks-heartbeat.service", "qv4-checks-heartbeat.timer"]
    for n in names:
        text = open(os.path.join(jobs, n)).read()
        assert n.startswith("qv4-")
        if n.endswith(".service"):
            assert re.search(r"^TimeoutStartSec=\d+$", text, re.M), n
            assert "ExecStart=/home/user/querynzv4/.venv/bin/python -m checks.board" in text
            assert "WorkingDirectory=/home/user/querynzv4" in text
        else:
            assert "Persistent=true" in text and "OnCalendar=" in text and "WantedBy=timers.target" in text
