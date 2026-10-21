"""The capture on fakes (no network, no database, no clock): pages are asked
by key, never by $skip, at the feed's own cap; each page is landed verbatim by
hash; a pass resumes from its last key; a full copy is followed by changes;
a block stops the run; a refusal is never caught; off-peak is held; the
position names the host; the measure counts the held copy."""
import datetime as dt
import hashlib
import json
import os
import urllib.parse

import pytest

import support.fetchgate as fg
from registers.charities import capture as C

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NZ = dt.timezone(dt.timedelta(hours=13))
NIGHT = dt.datetime(2026, 10, 20, 23, 0, tzinfo=NZ)
NOON = NIGHT.replace(hour=12)


class FakeTables:
    def __init__(self):
        self.passes, self.pages, self.aside = [], [], []

    def open_pass(self, s):
        for p in reversed(self.passes):
            if p["entity_set"] == s and p["finished_at"] is None:
                return p
        return None

    def last_done(self, s, mode=None):
        done = [p for p in self.passes if p["entity_set"] == s and p["finished_at"] and (mode is None or p["mode"] == mode)]
        return (None, None) if not done else (done[-1]["finished_at"], done[-1]["started_at"])

    def begin(self, s, mode, since=None):
        p = {"pass_id": len(self.passes) + 1, "entity_set": s, "mode": mode, "since": since, "next_key": None,
             "pages": 0, "stated": None, "rows": 0, "finished_at": None, "started_at": self.now}
        self.passes.append(p)
        return p

    def add_page(self, p, s, url, sha, rows, first_key, last_key, new, stated=None):
        p["pages"] += 1
        p["rows"] += rows
        if stated is not None:
            p["stated"] = stated
        if last_key is not None:
            p["next_key"] = last_key
        self.pages.append({"pass_id": p["pass_id"], "set": s, "url": url, "sha": sha, "rows": rows, "new": new})

    def finish(self, p):
        p["finished_at"] = self.now

    def set_aside(self, pass_id, item, stage, reason):
        self.aside.append((pass_id, item, stage, reason))


class FakeStore:
    def __init__(self):
        self.docs, self.names = {}, []

    def land(self, data, *, name, source, name_kind, content_type):
        sha = hashlib.sha256(data).hexdigest()
        new = sha not in self.docs
        self.docs[sha] = data
        self.names.append(name)
        return type("Ref", (), {"sha256": sha})(), new


class FakeFeed:
    """A feed of keyed rows per set; answers as the OData service does."""

    def __init__(self, sets=None, statuses=None):
        self.sets = sets or {}
        self.statuses = statuses or {}
        self.asked = []

    def __call__(self, url, timeout):
        self.asked.append(url)
        u = urllib.parse.urlsplit(url)
        name = u.path.strip("/")
        for mark, status in self.statuses.items():
            if mark in url:
                return fg.Fetched(url, status, b"", url, fg.looks_challenged(status, b""))
        if name in C.DOCS or u.netloc != C.HOST or name == "$metadata":
            return fg.Fetched(url, 200, b"<doc " + name.encode() + b">", url)
        q = dict(urllib.parse.parse_qsl(u.query))
        key = {n: k for n, k, _ in C.KEYED}.get(name)
        rows = self.sets.get(name, [])
        if key:
            after = None
            since = None
            for cond in q.get("$filter", "").split(" and "):
                if cond.startswith(f"{key} gt "):
                    after = int(cond.split()[-1])
                if cond.startswith("ModifiedOn ge "):
                    since = cond.split("'")[1]
            rows = sorted(rows, key=lambda r: r[key])
            if since:
                rows = [r for r in rows if r.get("ModifiedOn", "") >= since]
            if C.REGISTERED_FILTER in q.get("$filter", ""):
                rows = [r for r in rows if r.get("RegistrationStatus") == "Registered"]
            matching = rows
            if after is not None:
                rows = [r for r in rows if r[key] > after]
            page = rows[:int(q.get("$top", 1000))]
        else:
            matching = page = rows
        d = {"results": page}
        if "$inlinecount" in q:
            d["__count"] = str(len(matching))
        return fg.Fetched(url, 200, json.dumps({"d": d}).encode(), url)


def run(tables, feed, store, now=NIGHT, **kw):
    tables.now = now
    r = C.Run(tables, land_fn=store.land, opener=feed, clock=lambda: 0.0, sleep=lambda s: None,
              now_local=lambda: now, log=lambda *a: None, **kw)
    return r, r.run()


def orgs(n, registered_every=2):
    return [{"OrganisationId": i, "RegistrationStatus": "Registered" if i % registered_every == 0 else "Deregistered",
             "ModifiedOn": "2026-01-01T00:00:00"} for i in range(1, n + 1)]


def test_a_page_is_asked_by_key_at_the_feeds_cap_never_by_skip():
    u = C.page_url("Officers", "OfficerId", after=1234)
    q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(u).query))
    assert q["$orderby"] == "OfficerId" and q["$top"] == "1000" and q["$filter"] == "OfficerId gt 1234"
    assert "$skip" not in q and "$returnall" not in u
    assert C.PAGE <= 1000


def test_the_first_page_asks_the_feeds_own_count_and_a_changes_page_its_date():
    since = dt.datetime(2026, 10, 19, 23, 0, tzinfo=NZ)
    q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(C.page_url("AnnualReturn", "AnnualReturnId", None, since, True)).query))
    assert q["$inlinecount"] == "allpages"
    assert q["$filter"] == "ModifiedOn ge datetime'2026-10-19T10:00:00'"        # the feed's clock is UTC


def test_a_full_copy_lands_every_page_verbatim_and_reconciles_to_the_stated_count():
    feed, store, t = FakeFeed({"Organisations": orgs(2500)}), FakeStore(), FakeTables()
    _, out = run(t, feed, store, sets=["Organisations"])
    p = [p for p in t.passes if p["entity_set"] == "Organisations"][0]
    assert p["finished_at"] and p["mode"] == "full"
    assert p["stated"] == 2500 == p["rows"]
    assert [pg["rows"] for pg in t.pages if pg["set"] == "Organisations"] == [1000, 1000, 500]
    for pg in t.pages:
        assert store.docs[pg["sha"]] == feed(pg["url"], 0).body      # the bytes as served, unchanged
    assert out["stopped"] == "" and not t.aside


def test_a_full_pass_of_organisations_lands_the_register_s_count_of_registered_charities():
    feed, store, t = FakeFeed({"Organisations": orgs(2500)}), FakeStore(), FakeTables()
    run(t, feed, store, sets=["Organisations"])
    reg = [p for p in t.passes if p["entity_set"] == C.REGISTERED]
    assert len(reg) == 1 and reg[0]["stated"] == 1250 and reg[0]["finished_at"] and reg[0]["mode"] == "whole"
    page = [pg for pg in t.pages if pg["set"] == C.REGISTERED][0]
    assert "RegistrationStatus eq 'Registered'" in urllib.parse.unquote(page["url"]) and page["sha"] in store.docs
    run(t, feed, store, now=NIGHT + dt.timedelta(days=1), sets=["Organisations"])     # a changes pass asks nothing more
    assert len([p for p in t.passes if p["entity_set"] == C.REGISTERED]) == 1


def test_a_page_ending_exactly_on_the_cap_asks_once_more_and_finishes_on_the_empty_page():
    feed, store, t = FakeFeed({"Groups": [{"GroupId": i} for i in range(1, 1001)]}), FakeStore(), FakeTables()
    run(t, feed, store, sets=["Groups"])
    assert [pg["rows"] for pg in t.pages] == [1000, 0]
    assert t.passes[0]["finished_at"]


def test_a_pass_cut_short_resumes_from_its_last_key():
    feed, store, t = FakeFeed({"Officers": [{"OfficerId": i} for i in range(1, 3001)]}), FakeStore(), FakeTables()
    _, out = run(t, feed, store, sets=["Officers"], max_pages=2)
    assert out["stopped"] == "page cap reached" and t.passes[0]["finished_at"] is None
    assert t.passes[0]["next_key"] == 2000
    run(t, feed, store, sets=["Officers"])
    assert len(t.passes) == 1 and t.passes[0]["finished_at"] and t.passes[0]["rows"] == 3000
    assert "OfficerId gt 2000" in urllib.parse.unquote(feed.asked[2])


def test_after_a_full_copy_the_next_run_asks_only_for_changes_since_a_day_before_it_began():
    feed, store, t = FakeFeed({"Organisations": orgs(10)}), FakeStore(), FakeTables()
    run(t, feed, store, sets=["Organisations"])
    run(t, feed, store, now=NIGHT + dt.timedelta(days=1), sets=["Organisations"])
    assert [p["mode"] for p in t.passes if p["entity_set"] == "Organisations"] == ["full", "changes"]
    assert t.passes[2]["since"] == NIGHT - dt.timedelta(days=1)
    assert "ModifiedOn ge datetime'2026-10-19T10:00:00'" in urllib.parse.unquote(feed.asked[-1])


def test_the_same_bytes_again_are_already_held_not_a_new_document():
    feed, store, t = FakeFeed({"Organisations": orgs(10)}), FakeStore(), FakeTables()
    run(t, feed, store, sets=["Organisations"])
    _, out = run(t, feed, store, now=NIGHT + dt.timedelta(days=C.FULL_EVERY_DAYS), sets=["Organisations"])
    assert out["new"] == 0 and out["already_held"] == 2         # the page, and the register's count with it


def test_a_full_copy_is_run_again_after_its_period_so_a_withheld_row_is_seen_gone():
    assert C.plan_pass(NIGHT, NIGHT, False, NIGHT + dt.timedelta(days=C.FULL_EVERY_DAYS))[0] == "full"
    assert C.plan_pass(NIGHT, NIGHT, False, NIGHT + dt.timedelta(days=1))[0] == "changes"
    assert C.plan_pass(None, None, False, NIGHT)[0] == "full"
    assert C.plan_pass(NIGHT, NIGHT, True, NIGHT)[0] == "resume"


def test_keys_that_do_not_rise_are_not_trusted_and_stop_the_run():
    with pytest.raises(ValueError):
        C.page_keys([{"K": 3}, {"K": 3}], "K")
    with pytest.raises(ValueError):
        C.page_keys([{"K": 5}], "K", after=5)
    assert C.page_keys([{"K": 6}, {"K": 9}], "K", after=5) == [6, 9]


def test_a_block_stops_the_run_with_a_catch_log_line_and_nothing_more_is_asked():
    feed = FakeFeed({"Officers": [{"OfficerId": i} for i in range(1, 3001)]}, statuses={"OfficerId%20gt%201000": 500})
    store, t = FakeStore(), FakeTables()
    _, out = run(t, feed, store, sets=["Officers", "AnnualReturn"])
    assert out["stopped"].startswith("stopped:") and "hard limit 6" in out["stopped"]
    assert len(t.aside) == 1 and t.aside[0][2] == "fetch"
    assert not any("AnnualReturn" in u for u in feed.asked)
    assert t.passes[0]["finished_at"] is None and t.passes[0]["next_key"] == 1000


def test_a_gate_refusal_is_never_caught():
    def refuse(url, timeout):
        raise fg.Refused("no position")
    t = FakeTables()
    t.now = NIGHT
    with pytest.raises(fg.Refused):
        C.Run(t, land_fn=FakeStore().land, opener=refuse, clock=lambda: 0.0, sleep=lambda s: None,
              now_local=lambda: NIGHT, log=lambda *a: None, sets=["Groups"]).run()


def test_three_transport_failures_in_a_row_stop_the_run():
    calls = []

    def flaky(url, timeout):
        calls.append(url)
        raise OSError("reset")
    t = FakeTables()
    _, out = run(t, flaky, FakeStore(), sets=list(C.WHOLE))
    assert len(calls) == 3 and "transport failures" in out["stopped"]


def test_nothing_is_asked_outside_off_peak_unless_on_purpose():
    feed = FakeFeed({"Groups": [{"GroupId": 1}]})
    _, out = run(FakeTables(), feed, FakeStore(), now=NOON)
    assert feed.asked == [] and out["stopped"] == "off-peak is over"
    feed2 = FakeFeed({"Groups": [{"GroupId": 1}]})
    run(FakeTables(), feed2, FakeStore(), now=NOON, anytime=True, sets=["Groups"])
    assert len(feed2.asked) == 1


def test_the_lane_rests_its_floor_after_each_answer():
    t, slept, now = FakeTables(), [], [0.0]
    t.now = NIGHT

    def opener(url, timeout):
        now[0] += 2.0                       # each answer takes two seconds
        return FakeFeed({"Officers": [{"OfficerId": i} for i in range(1, 2501)]})(url, timeout)

    def sleep(s):
        slept.append(s)
        now[0] += s
    C.Run(t, land_fn=FakeStore().land, opener=opener, clock=lambda: now[0], sleep=sleep, now_local=lambda: NIGHT,
          log=lambda *a: None, sets=["Officers"]).run()
    assert slept == [C.FLOOR_S, C.FLOOR_S]
    assert C.FLOOR_S >= 5.0


def test_a_redirect_to_another_host_stops_the_run_and_lands_nothing():
    # the gate returns a redirect off the host unfetched: the 3xx and its Location, final_url the URL asked
    def away(url, timeout):
        return fg.Fetched(url, 302, b"", url, "", "https://elsewhere.example/x")
    store, t = FakeStore(), FakeTables()
    _, out = run(t, away, store, sets=["Groups"])
    assert "redirected to elsewhere.example" in out["stopped"] and not store.docs
    assert [a[3] for a in t.aside] == ["redirected to elsewhere.example: not landed, and the run stops"]


def test_the_code_lists_and_documents_are_asked_weekly_and_a_full_list_is_not_trusted():
    feed, store, t = FakeFeed({"MainSector": [{"Id": 1}], "Sectors": [{"SectorId": 1}]}), FakeStore(), FakeTables()
    run(t, feed, store, sets=["MainSector", "Sectors", "$metadata"])
    run(t, feed, store, now=NIGHT + dt.timedelta(days=1), sets=["MainSector", "Sectors", "$metadata"])
    assert len(feed.asked) == 3                       # a set with no ModifiedOn is not asked again within the week
    run(t, feed, store, now=NIGHT + dt.timedelta(days=C.WHOLE_EVERY_DAYS), sets=["Sectors"])
    assert len(feed.asked) == 4 and t.passes[-1]["mode"] == "full"
    big = FakeFeed({"MainSector": [{"Id": i} for i in range(1000)]})
    t2 = FakeTables()
    run(t2, big, FakeStore(), sets=["MainSector"])
    assert t2.aside and "cap" in t2.aside[0][3]


def test_every_set_named_in_the_feed_that_holds_rows_is_walked():
    names = {n for n, _, _ in C.KEYED} | set(C.WHOLE)
    for must in ("Organisations", "Officers", "AnnualReturn", "Groups"):
        assert must in names


def test_the_position_names_the_host_and_the_gate_lets_the_lane_through(tmp_path):
    host = fg.host_of(C.BASE)
    assert fg.position_for(host, C.POSITIONS) == "charities-register"
    assert fg.position_for("www.charities.govt.nz", C.POSITIONS) == "charities-register"
    d = fg.decide(C.page_url("Officers", "OfficerId"), None, fg.position_for(host, C.POSITIONS))
    assert d.allowed


def test_the_measure_counts_the_held_copy_against_the_registers_count():
    feed, store, t = FakeFeed({"Organisations": orgs(2500)}), FakeStore(), FakeTables()
    run(t, feed, store, sets=["Organisations"])
    held = [store.docs[pg["sha"]] for pg in t.pages if pg["set"] == "Organisations"]
    rows = sum(C.count_registered(b)[0] for b in held)
    reg = sum(C.count_registered(b)[1] for b in held)
    assert rows == 2500 and reg == 1250


def test_nothing_the_capture_prints_is_a_row():
    src = open(os.path.join(LANE, "capture.py"), encoding="utf-8").read()
    for line in src.splitlines():
        if "print(" in line or "self.log(" in line:
            assert "rows[" not in line and "FullName" not in line and "Address" not in line
