"""The frozen-product check against a fixture of the live old folder: green
when the release published inside the window and is current, red when it is
stale, flipped elsewhere or the old board did not run; reader mail alarms
once; the listing carries every file's hash and never hashes twice."""
import datetime as dt
import hashlib
import json
import os

import pytest

from checks import frozen_product as fp

NOW = dt.datetime(2026, 10, 18, 7, 30, tzinfo=dt.timezone(dt.timedelta(hours=13)))


def iso(t):
    return t.isoformat(timespec="seconds")


@pytest.fixture
def old(tmp_path):
    """A live old folder with one published version, a fresh old board, one
    reader message and a few staged files."""
    root = tmp_path / "old"
    snap = root / "var" / "pi-snapshot"
    (snap / "v" / "2026-10-18T0616").mkdir(parents=True)
    (snap / "current").symlink_to(snap / "v" / "2026-10-18T0616")
    (snap / "RELEASES.jsonl").write_text(
        json.dumps({"at": "2026-10-17T06:29:17", "action": "flip", "from": "a", "to": "2026-10-17T0616"}) + "\n"
        + json.dumps({"at": "2026-10-17T06:29:17+13:00", "action": "publish", "version": "2026-10-17T0616"}) + "\n"
        + json.dumps({"at": iso(NOW - dt.timedelta(hours=1)), "action": "publish", "version": "2026-10-18T0616"}) + "\n")
    (root / "var" / "audits").mkdir(parents=True)
    (root / "var" / "audits" / "board_state.json").write_text(json.dumps(
        {"ran_at": iso((NOW - dt.timedelta(minutes=40)).astimezone(dt.timezone.utc)), "failed": 2, "checks": 76,
         "red": ["T7.12", "T7.71"]}))
    (root / "data-layer" / "docs" / "ledger").mkdir(parents=True)
    (root / "data-layer" / "docs" / "ledger" / "feedback.json").write_text(json.dumps(
        [{"at": "2026-10-03T22:58:18Z", "kind": "feedback", "message": "12 Example Street, Karori", "page": "#/", "key": "k1"}]))
    st = root / "var" / "staging"
    (st / "ec-donations" / "archive").mkdir(parents=True)
    (st / "ec-donations" / "archive" / "Act-Party-Annual-Return-2021.pdf").write_bytes(b"%PDF-1.4 fake return\n")
    (st / "ec-financials").mkdir()
    (st / "ec-financials" / "ACT-Financial-Statements-2024.pdf").write_bytes(b"%PDF-1.4 fake statements\n")
    return str(root)


def test_green_when_published_inside_the_window_and_current(old, tmp_path):
    r = fp.check(now=NOW, old_live=old, state_dir=str(tmp_path / "state"))
    by = {i["name"]: i for i in r["items"]}
    assert r["ok"], r
    assert by["release"]["ok"] and "2026-10-18T0616" in by["release"]["detail"]
    assert by["old-board"]["ok"] and "2 of 76 red" in by["old-board"]["detail"]
    assert by["listing"]["ok"] and "2 files" in by["listing"]["detail"]


def test_red_when_the_last_green_release_is_older_than_the_window(old, tmp_path):
    later = NOW + dt.timedelta(hours=26)
    r = fp.check(now=later, old_live=old, state_dir=str(tmp_path / "state"))
    by = {i["name"]: i for i in r["items"]}
    assert not r["ok"] and not by["release"]["ok"] and "27 h ago" in by["release"]["detail"]
    assert not by["old-board"]["ok"]


def test_red_when_current_points_at_another_version(old, tmp_path):
    cur = os.path.join(old, "var", "pi-snapshot", "current")
    os.mkdir(os.path.join(old, "var", "pi-snapshot", "v", "2026-10-17T0616"))
    os.remove(cur)
    os.symlink(os.path.join(old, "var", "pi-snapshot", "v", "2026-10-17T0616"), cur)
    r = fp.check(now=NOW, old_live=old, state_dir=str(tmp_path / "state"))
    by = {i["name"]: i for i in r["items"]}
    assert not by["release"]["ok"] and "current points at 2026-10-17T0616" in by["release"]["detail"]


def test_a_missing_release_log_or_board_is_red(tmp_path):
    r = fp.check(now=NOW, old_live=str(tmp_path / "empty"), state_dir=str(tmp_path / "state"))
    by = {i["name"]: i for i in r["items"]}
    assert not by["release"]["ok"] and not by["old-board"]["ok"] and "listing" not in by


def test_reader_mail_alarms_once_and_never_carries_the_message(old, tmp_path):
    state = str(tmp_path / "state")
    r = fp.check(now=NOW, old_live=old, state_dir=state)
    assert len(r["alarms"]) == 1
    title, body = r["alarms"][0]
    assert "2026-10-03T22:58:18Z" in body and "#/" in body
    assert "Karori" not in body and "Example Street" not in body
    assert r["ok"]   # mail is attention, not a failure of the product
    r2 = fp.check(now=NOW, old_live=old, state_dir=state)
    assert r2["alarms"] == []
    fb = os.path.join(old, "data-layer", "docs", "ledger", "feedback.json")
    rows = json.load(open(fb)) + [{"at": "2026-10-18T01:00:00Z", "page": "#/donor/x", "key": "k2"}]
    json.dump(rows, open(fb, "w"))
    r3 = fp.check(now=NOW, old_live=old, state_dir=state)
    assert len(r3["alarms"]) == 1 and "#/donor/x" in r3["alarms"][0][1]


def test_listing_has_every_file_with_its_hash_and_is_written_once_per_version(old, tmp_path):
    state = str(tmp_path / "state")
    calls = []

    def counting(path):
        calls.append(path)
        return fp.sha256_file(path)

    fp.check(now=NOW, old_live=old, state_dir=state, hasher=counting)
    listing = os.path.join(state, "listings", "2026-10-18T0616.jsonl")
    lines = [json.loads(l) for l in open(listing)]
    assert lines[0]["version"] == "2026-10-18T0616" and lines[0]["files"] == 2
    rows = {r["path"]: r for r in lines[1:]}
    p = "ec-donations/archive/Act-Party-Annual-Return-2021.pdf"
    assert rows[p]["sha256"] == hashlib.sha256(b"%PDF-1.4 fake return\n").hexdigest()
    assert rows[p]["bytes"] == 21 and rows[p]["mtime"]
    assert len(calls) == 2
    # the same version again: nothing re-listed, nothing re-hashed
    r = fp.check(now=NOW, old_live=old, state_dir=state, hasher=counting)
    assert len(calls) == 2 and "already listed" in [i for i in r["items"] if i["name"] == "listing"][0]["detail"]
    # a new version: one new file is hashed, the unchanged ones come from the cache
    snap = os.path.join(old, "var", "pi-snapshot")
    os.mkdir(os.path.join(snap, "v", "2026-10-19T0616"))
    os.remove(os.path.join(snap, "current"))
    os.symlink(os.path.join(snap, "v", "2026-10-19T0616"), os.path.join(snap, "current"))
    with open(os.path.join(snap, "RELEASES.jsonl"), "a") as f:
        f.write(json.dumps({"at": iso(NOW + dt.timedelta(hours=23)), "action": "publish", "version": "2026-10-19T0616"}) + "\n")
    with open(os.path.join(old, "var", "staging", "ec-financials", "new.pdf"), "wb") as f:
        f.write(b"new")
    r = fp.check(now=NOW + dt.timedelta(hours=24), old_live=old, state_dir=state, hasher=counting)
    assert len(calls) == 3
    assert "3 files" in [i for i in r["items"] if i["name"] == "listing"][0]["detail"]


def test_a_naive_time_in_the_release_log_is_read_as_local_time():
    t = fp.parse_when("2026-10-17T23:38:52", NOW.tzinfo)
    assert t.utcoffset() == dt.timedelta(hours=13)
    assert fp.parse_when("2026-10-16T17:58:09+00:00").utcoffset() == dt.timedelta(0)
    assert fp.parse_when("2026-10-16T17:58:09Z").utcoffset() == dt.timedelta(0)
