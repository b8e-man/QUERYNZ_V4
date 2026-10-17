"""The timer writes one line per prompt and per stop, with the session's
name and weight and never the prompt; the board item pairs them, reports
typical and worst per weight, and trims the file to 30 days."""
import datetime as dt
import json
import os
import subprocess
import sys

from checks import session_times as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, ".claude", "hooks", "timer.py")


def run_hook(event, repo, times):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": repo, "QV4_TIMES": times}
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(event), capture_output=True, text=True, timeout=10, env=env)
    return p.returncode


def test_the_hook_writes_the_event_and_never_the_prompt(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".scope").write_text(f"name: ask-1\nweight: question\nscratch: {tmp_path}/s\nfolders:\n")
    times = str(tmp_path / "times" / "session-times.jsonl")
    assert run_hook({"hook_event_name": "UserPromptSubmit", "session_id": "abc", "prompt": "the secret question"}, str(repo), times) == 0
    assert run_hook({"hook_event_name": "Stop", "session_id": "abc"}, str(repo), times) == 0
    assert run_hook({"hook_event_name": "PreToolUse", "session_id": "abc"}, str(repo), times) == 0
    rows = [json.loads(l) for l in open(times)]
    assert [r["event"] for r in rows] == ["prompt", "stop"]
    assert rows[0]["session"] == "ask-1" and rows[0]["weight"] == "question" and rows[0]["id"] == "abc"
    assert "secret" not in open(times).read()


def test_the_board_item_pairs_prompts_with_stops_and_trims(tmp_path):
    times = str(tmp_path / "session-times.jsonl")
    now = dt.datetime(2026, 10, 18, 12, 0, tzinfo=dt.timezone(dt.timedelta(hours=13)))

    def row(event, mins_ago, session="ask-1", weight="question", sid="a"):
        return json.dumps({"at": (now - dt.timedelta(minutes=mins_ago)).isoformat(timespec="seconds"), "event": event,
                           "session": session, "weight": weight, "id": sid})
    with open(times, "w") as f:
        f.write("\n".join([row("prompt", 60), row("stop", 59), row("prompt", 30), row("stop", 25),
                           row("prompt", 10, "fix-keys-1", "fix", "b"), row("stop", 9, "fix-keys-1", "fix", "b"),
                           row("prompt", 60 * 24 * 40, "old", "fix", "c"), row("stop", 60 * 24 * 40 - 1, "old", "fix", "c")]) + "\n")
    r = st.check(now=now, path=times)
    by = {i["name"]: i["detail"] for i in r["items"]}
    assert r["ok"] and "2 turn(s): typical 180 s, worst 300 s; target 120 s MISSED" in by["question"]
    assert by["fix"].startswith("1 turn(s): typical 60 s, worst 60 s; target 1200 s")
    assert by["trim"] == "2 line(s) older than 30 days removed"
    assert len(open(times).read().splitlines()) == 6


def test_no_turns_is_fine(tmp_path):
    r = st.check(now=dt.datetime.now().astimezone(), path=str(tmp_path / "none.jsonl"))
    assert r["ok"] and r["items"][0]["detail"].startswith("no timed turns")
