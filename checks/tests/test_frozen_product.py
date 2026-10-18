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


def unit(uid, active="active", sub=None, load="loaded", enabled="enabled"):
    sub = sub or ("waiting" if uid.endswith(".timer") else "running")
    return {"Id": uid, "LoadState": load, "ActiveState": active, "SubState": sub, "UnitFileState": enabled}


# every must-run unit running, a timer-driven one-shot between runs, node1's units not here
OK = {u: unit(u) for u in fp.MUST_RUN}
OK["ec-disclosures.service"] = unit("ec-disclosures.service", "inactive", "dead", enabled="static")
OK["offsite-push.timer"] = unit("offsite-push.timer")
OK["querynz-vip.service"] = unit("querynz-vip.service", "inactive", "dead", load="not-found", enabled="")
OK["querynz-deploy-node1.timer"] = unit("querynz-deploy-node1.timer", "inactive", "dead")


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
    r = fp.check(states=OK, live=str(tmp_path), now=NOW, old_live=old, state_dir=str(tmp_path / "state"))
    by = {i["name"]: i for i in r["items"]}
    assert r["ok"], r
    assert by["release"]["ok"] and "2026-10-18T0616" in by["release"]["detail"]
    assert by["old-board"]["ok"] and "2 of 76 red" in by["old-board"]["detail"]
    assert by["listing"]["ok"] and "2 files" in by["listing"]["detail"]


def test_red_when_the_last_green_release_is_older_than_the_window(old, tmp_path):
    later = NOW + dt.timedelta(hours=26)
    r = fp.check(states=OK, live=str(tmp_path), now=later, old_live=old, state_dir=str(tmp_path / "state"))
    by = {i["name"]: i for i in r["items"]}
    assert not r["ok"] and not by["release"]["ok"] and "27 h ago" in by["release"]["detail"]
    assert not by["old-board"]["ok"]


def test_red_when_current_points_at_another_version(old, tmp_path):
    cur = os.path.join(old, "var", "pi-snapshot", "current")
    os.mkdir(os.path.join(old, "var", "pi-snapshot", "v", "2026-10-17T0616"))
    os.remove(cur)
    os.symlink(os.path.join(old, "var", "pi-snapshot", "v", "2026-10-17T0616"), cur)
    r = fp.check(states=OK, live=str(tmp_path), now=NOW, old_live=old, state_dir=str(tmp_path / "state"))
    by = {i["name"]: i for i in r["items"]}
    assert not by["release"]["ok"] and "current points at 2026-10-17T0616" in by["release"]["detail"]


def test_a_missing_release_log_or_board_is_red(tmp_path):
    r = fp.check(states=OK, live=str(tmp_path), now=NOW, old_live=str(tmp_path / "empty"), state_dir=str(tmp_path / "state"))
    by = {i["name"]: i for i in r["items"]}
    assert not by["release"]["ok"] and not by["old-board"]["ok"] and "listing" not in by


def test_reader_mail_alarms_once_and_never_carries_the_message(old, tmp_path):
    state = str(tmp_path / "state")
    r = fp.check(states=OK, live=str(tmp_path), now=NOW, old_live=old, state_dir=state)
    assert len(r["alarms"]) == 1
    title, body = r["alarms"][0]
    assert "2026-10-03T22:58:18Z" in body and "#/" in body
    assert "Karori" not in body and "Example Street" not in body
    assert r["ok"]   # mail is attention, not a failure of the product
    r2 = fp.check(states=OK, live=str(tmp_path), now=NOW, old_live=old, state_dir=state)
    assert r2["alarms"] == []
    fb = os.path.join(old, "data-layer", "docs", "ledger", "feedback.json")
    rows = json.load(open(fb)) + [{"at": "2026-10-18T01:00:00Z", "page": "#/donor/x", "key": "k2"}]
    json.dump(rows, open(fb, "w"))
    r3 = fp.check(states=OK, live=str(tmp_path), now=NOW, old_live=old, state_dir=state)
    assert len(r3["alarms"]) == 1 and "#/donor/x" in r3["alarms"][0][1]


def test_listing_has_every_file_with_its_hash_and_is_written_once_per_version(old, tmp_path):
    state = str(tmp_path / "state")
    calls = []

    def counting(path):
        calls.append(path)
        return fp.sha256_file(path)

    fp.check(states=OK, live=str(tmp_path), now=NOW, old_live=old, state_dir=state, hasher=counting)
    listing = os.path.join(state, "listings", "2026-10-18T0616.jsonl")
    lines = [json.loads(l) for l in open(listing)]
    assert lines[0]["version"] == "2026-10-18T0616" and lines[0]["files"] == 2
    rows = {r["path"]: r for r in lines[1:]}
    p = "ec-donations/archive/Act-Party-Annual-Return-2021.pdf"
    assert rows[p]["sha256"] == hashlib.sha256(b"%PDF-1.4 fake return\n").hexdigest()
    assert rows[p]["bytes"] == 21 and rows[p]["mtime"]
    assert len(calls) == 2
    # the same version again: nothing re-listed, nothing re-hashed
    r = fp.check(states=OK, live=str(tmp_path), now=NOW, old_live=old, state_dir=state, hasher=counting)
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
    r = fp.check(states=OK, live=str(tmp_path), now=NOW + dt.timedelta(hours=24), old_live=old, state_dir=state, hasher=counting)
    assert len(calls) == 3
    assert "3 files" in [i for i in r["items"] if i["name"] == "listing"][0]["detail"]


def test_a_naive_time_in_the_release_log_is_read_as_local_time():
    t = fp.parse_when("2026-10-17T23:38:52", NOW.tzinfo)
    assert t.utcoffset() == dt.timedelta(hours=13)
    assert fp.parse_when("2026-10-16T17:58:09+00:00").utcoffset() == dt.timedelta(0)
    assert fp.parse_when("2026-10-16T17:58:09Z").utcoffset() == dt.timedelta(0)


def test_the_carve_out_list_is_the_safety_hook_s():
    import importlib.util
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    spec = importlib.util.spec_from_file_location("fence", os.path.join(here, ".claude", "hooks", "fence.py"))
    fence = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fence)
    assert set(fp.CARVE_OUT) == set(fence.CARVE_OUT)
    assert all(u.startswith(fence.CARVE_OUT_PREFIXES) for u in fp.SYSTEM_UNITS)
    assert fp.MUST_RUN <= {f"{n}{s}" for n in fp.CARVE_OUT for s in (".service", ".timer")} | set(fp.SYSTEM_UNITS)


def test_the_carve_out_is_green_with_every_must_run_unit_up_and_node1_s_only_reported(old, tmp_path):
    r = fp.check(states=OK, live=str(tmp_path), now=NOW, old_live=old, state_dir=str(tmp_path / "state"))
    item = [i for i in r["items"] if i["name"] == "carve-out"][0]
    assert item["ok"], item
    assert f"{len(fp.MUST_RUN)} of {len(fp.MUST_RUN)} must-run" in item["detail"]
    assert "never seen running here" in item["detail"] and "querynz-deploy-node1.timer" in item["detail"]
    assert "not installed here: querynz-vip" in item["detail"] and "querynz-vip.timer" not in item["detail"]
    assert "ec-disclosures.service" not in item["detail"]   # a one-shot between runs of its timer


def test_the_carve_out_is_red_when_a_unit_the_release_needs_is_down(old, tmp_path):
    states = dict(OK)
    states["querynz-pi-web.service"] = unit("querynz-pi-web.service", "inactive", "dead", enabled="disabled")
    r = fp.check(states=states, live=str(tmp_path), now=NOW, old_live=old, state_dir=str(tmp_path / "state"))
    item = [i for i in r["items"] if i["name"] == "carve-out"][0]
    assert not r["ok"] and not item["ok"]
    assert "the release needs: querynz-pi-web.service inactive/dead" in item["detail"]
    states["querynz-vision-ocr.service"] = unit("querynz-vision-ocr.service", load="not-found", active="inactive", sub="dead")
    r = fp.check(states=states, live=str(tmp_path), now=NOW, old_live=old, state_dir=str(tmp_path / "state"))
    item = [i for i in r["items"] if i["name"] == "carve-out"][0]
    assert "querynz-vision-ocr.service is not installed here" in item["detail"]


def test_a_unit_once_seen_running_is_red_until_it_runs_again(old, tmp_path):
    state = str(tmp_path / "state")
    states = dict(OK)
    states["querynz-deploy-node1.timer"] = unit("querynz-deploy-node1.timer")
    r = fp.check(states=states, live=str(tmp_path), now=NOW, old_live=old, state_dir=state)
    assert r["ok"]
    states["querynz-deploy-node1.timer"] = unit("querynz-deploy-node1.timer", "inactive", "dead")
    r = fp.check(states=states, live=str(tmp_path), now=NOW, old_live=old, state_dir=state)
    item = [i for i in r["items"] if i["name"] == "carve-out"][0]
    assert not item["ok"] and "stopped since last seen running: querynz-deploy-node1.timer inactive/dead" in item["detail"]
    r = fp.check(states=states, live=str(tmp_path), now=NOW, old_live=old, state_dir=state)   # still red next run
    assert not [i for i in r["items"] if i["name"] == "carve-out"][0]["ok"]
    states["querynz-deploy-node1.timer"] = unit("querynz-deploy-node1.timer")
    r = fp.check(states=states, live=str(tmp_path), now=NOW, old_live=old, state_dir=state)
    assert [i for i in r["items"] if i["name"] == "carve-out"][0]["ok"]


def test_systemctl_that_cannot_be_asked_is_red(old, tmp_path):
    states = dict(OK)
    states["?--user"] = {"Id": "?--user", "LoadState": "error", "ActiveState": "FileNotFoundError"}
    r = fp.check(states=states, live=str(tmp_path), now=NOW, old_live=old, state_dir=str(tmp_path / "state"))
    item = [i for i in r["items"] if i["name"] == "carve-out"][0]
    assert not item["ok"] and "could not be asked" in item["detail"]


def test_the_old_board_s_silence_is_not_red_once_v3_audit_is_on_the_stop_list(old, tmp_path):
    (tmp_path / "stop-list.md").write_text("# batch 3\nv3-audit\n")
    later = NOW + dt.timedelta(hours=26)
    r = fp.check(states=OK, live=str(tmp_path), now=later, old_live=old, state_dir=str(tmp_path / "state"))
    by = {i["name"]: i for i in r["items"]}
    assert by["old-board"]["ok"] and "on the 1.4 stop list" in by["old-board"]["detail"]
    assert "2 of 76 red" in by["old-board"]["detail"]
    assert not by["release"]["ok"]   # the release's own window still counts
    assert fp.stop_list(str(tmp_path)) == {"v3-audit"}
    (tmp_path / "stop-list.md").write_text("v3-audit.timer\n# x\n\nquerynz-api.service\n")
    assert fp.stop_list(str(tmp_path)) == {"v3-audit", "querynz-api"}


def test_parse_show_reads_systemctl_s_blocks():
    text = ("Id=a.timer\nLoadState=loaded\nActiveState=active\nSubState=waiting\nUnitFileState=enabled\n"
            "NextElapseUSecRealtime=Mon 2026-10-19 06:16:03 NZDT\n\n"
            "Id=b.service\nLoadState=not-found\nActiveState=inactive\nSubState=dead\nUnitFileState=\n")
    u = fp.parse_show(text)
    assert u["a.timer"]["NextElapseUSecRealtime"].endswith("NZDT") and fp.is_running(u["a.timer"])
    assert u["b.service"]["LoadState"] == "not-found" and not fp.is_running(u["b.service"])
    user, system = fp.carve_out_names()
    assert "querynz-pi-web.service" in user and "ftm-release.timer" in user and system == ["postgresql.service"]
