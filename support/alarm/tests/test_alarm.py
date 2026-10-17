"""The alarm reads the channel at send time, never leaks it, and records
every alarm whether or not it went."""
import json
import os

import support.alarm as alarm


def fake_channel(tmp_path, url="https://ntfy.example/secret-topic-xyz"):
    p = tmp_path / "alert-channel.env"
    p.write_text(f"# the channel\nALERT_NTFY_URL={url}\n")
    return str(p)


def test_sends_through_the_channel_and_records_it(tmp_path):
    calls = []
    ledger = str(tmp_path / "alarms.jsonl")

    def post(url, title, body, priority):
        calls.append((url, title, body, priority))
        return True

    ok = alarm.send("qv4 node2: test", "body text", channel_file=fake_channel(tmp_path), post=post, ledger=ledger)
    assert ok and calls == [("https://ntfy.example/secret-topic-xyz", "qv4 node2: test", "body text", "high")]
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["sent"] is True and rec["title"] == "qv4 node2: test" and rec["why"] == ""
    assert "secret-topic" not in open(ledger).read()   # the address never reaches the ledger


def test_no_channel_file_is_recorded_not_raised(tmp_path):
    ledger = str(tmp_path / "alarms.jsonl")
    ok = alarm.send("t", "b", channel_file=str(tmp_path / "missing.env"), post=lambda *a: True, ledger=ledger)
    assert ok is False
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["sent"] is False and "no alarm channel" in rec["why"]


def test_a_failing_send_never_crashes_the_caller(tmp_path):
    ledger = str(tmp_path / "alarms.jsonl")

    def post(*a):
        raise ConnectionError("down")

    assert alarm.send("t", "b", channel_file=fake_channel(tmp_path), post=post, ledger=ledger) is False
    rec = json.loads(open(ledger).read().splitlines()[-1])
    assert rec["why"] == "send failed: ConnectionError"


def test_title_is_ascii_for_the_header(tmp_path):
    seen = {}
    alarm.send("qv4 — red ✓", "b", channel_file=fake_channel(tmp_path),
               post=lambda u, t, b, p: seen.setdefault("t", t) or True, ledger=str(tmp_path / "l.jsonl"))
    assert seen["t"].isascii()


def test_channel_url_reads_only_the_key(tmp_path):
    assert alarm.channel_url(fake_channel(tmp_path)) == "https://ntfy.example/secret-topic-xyz"
    p = tmp_path / "other.env"
    p.write_text("OTHER=1\n")
    assert alarm.channel_url(str(p)) is None
    assert alarm.channel_url(str(tmp_path / "nope")) is None
    assert os.path.basename(alarm.CHANNEL_FILE) == "alert-channel.env"
