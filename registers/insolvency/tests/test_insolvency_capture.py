"""The capture, the load and the check against the sample database on a fake API (answers shaped like the definition's
examples, every name and number invented), inside one transaction rolled back at the end: nothing stays in the sample
database and nothing is fetched. The key is a test string; the test asserts it reaches only the header."""
import datetime as dt
import json
import os
import types
import urllib.parse

import pytest

from support import db, fetchgate
from support.docstore import landing
from registers.insolvency import capture, check, load

TODAY = dt.date(2026, 11, 2)
L = "scratch_test_insolvency"
STAGE = "scratch_test_insolvency_stage"
KEY = "test-key-not-a-real-one-0000"

#: (register, estate, adjudicated, detail fields): the register as the fake API holds it
ESTATES = [
    ("Insolvency", 1001, "2026-09-10", {"insolvencyStatus": "Current"}),
    ("Insolvency", 1002, "2026-08-15", {"insolvencyStatus": "Discharged", "dischargeOrCompletionDate": "2020-01-01"}),
    ("Insolvency", 1003, "2026-09-20", {"insolvencyStatus": "Suppressed"}),
    ("Insolvency", 1004, "2026-10-01", {"estateName": None, "organisationName": "Invented Trading Limited",
                                        "nzbn": "9429000000017", "insolvencyStatus": "Current"}),
    ("Insolvency", 1005, "2026-08-20", {"insolvencyStatus": "Discharged", "dischargeOrCompletionDate": "2010-05-05",
                                        "multipleInsolvencies": True}),
    ("DRO", 2001, "2026-10-12", {"insolvencyStatus": "Current"}),
]


def _estate(reg, n, adj, extra):
    e = {"estateNumber": n, "estateName": f"Invented Person {n}", "insolvencyTypeDescription": "Creditor Application",
         "insolvencyStatus": "Current", "adjudicationOrLiquidationDate": adj + "T00:00:00", "multipleInsolvencies": False,
         "addressAtAdjudication": f"{n} Invented Street, Exampletown", "monthOfBirth": 4, "yearOfBirth": 1971,
         "currentAddresses": [{"line": f"{n} Invented Road"}], "courtName": "High Court"}
    e.update(extra)
    return e


class FakeAPI:
    """Routes a gated URL to an answer; counts calls; `removed` names estates on the removals call; `gone` 404s."""

    def __init__(self, removed=(), gone=()):
        self.urls, self.removed, self.gone = [], set(removed), set(gone)

    def __call__(self, url, timeout):
        self.urls.append(url)
        u = urllib.parse.urlparse(url)
        q = dict(urllib.parse.parse_qsl(u.query))
        path = u.path.split("/insolvency-trustee-services/v5", 1)[1]   # the live API answers only under its version
        if path == "/insolvencies/removalorcorrections":
            rows = [{"estateNumber": n, "removedDate": TODAY.isoformat(), "addressAtAdjudication": "9 Invented Way"}
                    for n in sorted(self.removed)] if q["page"] == "1" and q["date-from"] <= TODAY.isoformat() <= q["date-to"] else []
            return 200, json.dumps({"removedOrCorrectedInsolvencies": rows, "totalItems": len(rows)}).encode(), url
        if path == "/insolvencies":
            f, t = dt.date.fromisoformat(q["date-from"]), dt.date.fromisoformat(q["date-to"])
            hits = [_estate(*e) for e in ESTATES if e[0] == q["register"] and f <= dt.date.fromisoformat(e[2]) <= t
                    and e[1] not in self.gone]
            return 200, json.dumps({"searchResults": [{k: v for k, v in h.items() if k != "dischargeOrCompletionDate"}
                                                      for h in hits], "totalItems": len(hits), "page": int(q["page"]),
                                    "pageSize": 100, "totalPages": 1}).encode(), url
        n = int(path.rsplit("/", 1)[1])
        if n in self.gone:
            return 404, b"", url
        e = next(_estate(*x) for x in ESTATES if x[1] == n)
        return 200, json.dumps(e).encode(), url


class Pacer:
    def wait(self, host, floor):
        return 0.0


class NoCommit:
    """The capture commits as it goes; here every commit is held in the one transaction the test rolls back."""

    def __init__(self, c):
        self.c = c

    def execute(self, *a, **k):
        return self.c.execute(*a, **k)

    def cursor(self, *a, **k):
        return self.c.cursor(*a, **k)

    def transaction(self):
        return self.c.transaction()

    def commit(self):
        pass


@pytest.fixture
def env(monkeypatch, tmp_path):
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    store = {}
    raw = db.connect(db.OWNER_KEY, "querynz_v4_sample")
    conn = NoCommit(raw)

    def land(body, **kw):
        ref, new = landing.land(body, root=str(tmp_path), **kw)     # the store's own landing, its bytes under tmp_path
        store[ref.sha256] = body
        return ref, new

    monkeypatch.setattr(capture, "land", land)
    monkeypatch.setattr(capture, "SEARCH_FROM", dt.date(2026, 7, 1))
    conn.execute(f"DROP SCHEMA IF EXISTS {L} CASCADE")
    conn.execute(f"DROP SCHEMA IF EXISTS {STAGE} CASCADE")
    conn.execute(f"CREATE SCHEMA {L}")
    try:
        yield types.SimpleNamespace(conn=conn, store=store, raw=raw)
    finally:
        raw.rollback()
        raw.close()


def _gate(api):
    return {"fetch": api, "pacer": Pacer(), "key": KEY}


def _night(env, api):
    return capture.run_night(env.conn, L, anytime=True, today=TODAY, log=lambda *a: None, **_gate(api))


def _load(env):
    counts = load.build(env.conn, STAGE, read_bytes=env.store.__getitem__, today=TODAY, version=1, ledger_schema=L)
    rows = {r[0]: r[1] for r in env.conn.execute(f"SELECT estate_number, kind FROM {STAGE}.estates").fetchall()}
    unanswered = dict(env.conn.execute(f"SELECT estate_number, reason FROM {STAGE}.unanswered").fetchall())
    return counts, rows, unanswered


def _flags(env, schema=STAGE):
    return {r[0]: dict(zip(("suppressed", "past_window", "removal_seen_at", "absent_since", "name"), r[1:])) for r in
            env.conn.execute(f"SELECT estate_number, suppressed, window_unknown OR shown_until < %s, removal_seen_at, "
                             f"absent_since, name FROM {schema}.estates", (TODAY,)).fetchall()}


def test_the_night_the_load_and_the_check(env):
    api = FakeAPI()
    out = _night(env, api)
    assert out["ok"] and out["details"] == 6 and out["stopped"] == "nothing wanted is left"
    assert any("1001 Invented Street" in b.decode() and "1001 Invented Road" in b.decode() and "yearOfBirth" in b.decode()
               for b in env.store.values()), "the answers are landed whole (ruling 142), addresses and birth fields in them"
    counts, rows, unanswered = _load(env)
    assert set(rows) == {1001, 1002, 1003, 1004, 1005, 2001} and rows[1004] == "company" and not unanswered
    f = _flags(env)
    assert f[1002]["past_window"] and not f[1001]["past_window"] and not f[1005]["past_window"]
    assert f[1003]["suppressed"] and f[1003]["name"] == "" and not f[1001]["suppressed"]
    kept = env.conn.execute(f"SELECT key, name FROM {STAGE}_private.suppressed_names").fetchall()
    assert kept == [("insolvency/1003", "Invented Person 1003")], "the suppressed estate's name is kept privately by key"
    assert counts["estates"] == 6 and counts["set_aside"] == 0 and counts["suppressed"] == 1 and counts["past_window"] == 1
    problems = check.reading(env.conn, STAGE, L, TODAY)
    assert problems == ["estates are held and the removals-and-corrections operation has never been asked"]
    assert capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(api))["ok"]
    assert check.reading(env.conn, STAGE, L, TODAY) == []
    assert check.reading(env.conn, STAGE, L, TODAY + dt.timedelta(days=3))[0].startswith("the removals were last asked")
    # every search page is walked once, the latest 60 days again; the API's own count matches what was seen
    assert {r: (said, seen) for r, said, seen in check.against_api(env.conn, L)} == {"Insolvency": (5, 5), "DRO": (1, 1)}
    assert all(KEY not in u for u in api.urls)
    asked = [r[0] for r in env.conn.execute(f"SELECT asked FROM {L}.calls").fetchall()]
    assert asked and all(KEY not in a for a in asked)


def _published(env):
    load.publish(env.conn, STAGE, log=lambda *a: None, schema=L, views=False)
    return {r[0] for r in env.conn.execute(f"SELECT estate_number FROM {L}.estates").fetchall()}


def test_a_removal_is_flagged_at_once_kept_and_asked_again(env):
    """Ruling 142: the removals flag an estate, its row and its answers kept (before 4 November 2026 the row was deleted
    and the answers withdrawn)."""
    _night(env, FakeAPI())
    _load(env)
    assert 1001 in _published(env)
    api = FakeAPI(removed={1001}, gone={1001})
    out = capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(api))
    assert out["ok"] and out["named"] == 1 and out["flagged"] == 1 and out["asked_again"] == 1 and out["corrected"] == 0
    assert _flags(env, L)[1001]["removal_seen_at"] is not None, "the row stays, flagged"
    shas = [r[0] for r in env.conn.execute(f"SELECT document FROM {L}.calls WHERE estate = 1001 AND why = 'detail' "
                                           f"AND document IS NOT NULL").fetchall()]
    w = landing.documents_of(shas, env.raw)
    assert w and not any(d["withdrawn"] for d in w.values()), "the removed estate's answers are not withdrawn"
    assert any(u.endswith("/insolvencies/1001") for u in api.urls)
    _, rows, unanswered = _load(env)
    f = _flags(env)[1001]
    assert 1001 in rows and 1001 not in unanswered and f["removal_seen_at"] and f["absent_since"]
    assert check.reading(env.conn, STAGE, L, TODAY) == []


def test_a_correction_comes_back_and_stands(env):
    _night(env, FakeAPI())
    _load(env)
    _published(env)
    out = capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(FakeAPI(removed={1001})))
    assert out["corrected"] == 1
    _, rows, _ = _load(env)
    assert 1001 in rows


def test_a_removal_of_an_estate_never_held_is_not_asked_again(env):
    """The first run's list reaches back to the API's start; asking every estate on it again at 5 s a call ran the job
    past its deadline (2 November 2026, 1,511 named). One we never held has nothing to correct."""
    _night(env, FakeAPI())
    api = FakeAPI(removed={1001, 987654})
    out = capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(api))
    assert out["ok"] and out["named"] == 2 and out["asked_again"] == 1
    assert any(u.endswith("/insolvencies/1001") for u in api.urls)
    assert not any(u.endswith("/insolvencies/987654") for u in api.urls)


def test_a_removals_re_ask_does_not_make_an_estate_held_the_next_day(env):
    """3 November 2026: the old rule counted any earlier detail call as holding, and the removals' own re-asks are detail
    calls, so the next day every estate the first run had asked was asked again."""
    _night(env, FakeAPI())
    call = env.conn.execute(f"INSERT INTO {L}.calls (at, day, why, asked, estate, status) VALUES "
                            f"(now() - interval '1 day', %s, 'detail', '/insolvencies/987654', 987654, 404) RETURNING id",
                            (TODAY,)).fetchone()[0]
    env.conn.execute(f"INSERT INTO {L}.removals (estate, removed_on, call, seen_at) VALUES "
                     f"(987654, %s, %s, now() - interval '2 days')", (TODAY, call))
    api = FakeAPI(removed={987654})
    capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(api))
    assert not any(u.endswith("/insolvencies/987654") for u in api.urls)


def test_the_removal_mutant_is_caught(env, monkeypatch):
    """apply_removal made a no-op: the row is not flagged after its removal, and the check goes red."""
    _night(env, FakeAPI())
    _load(env)
    _published(env)
    monkeypatch.setattr(capture, "apply_removal", lambda *a, **k: 0)
    capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(FakeAPI(removed={1001}, gone={1001})))
    assert 1001 in {r[0] for r in env.conn.execute(f"SELECT estate_number FROM {L}.estates").fetchall()}
    assert any("the removals named with no answer since, not flagged" in p for p in check.reading(env.conn, L, L, TODAY))


def test_a_removal_between_build_and_publish_is_flagged_at_publish(env):
    _night(env, FakeAPI())
    _load(env)
    capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(FakeAPI(removed={1001}, gone={1001})))
    assert 1001 in _published(env)              # staged before the removal; kept, and flagged at publish
    assert _flags(env, L)[1001]["removal_seen_at"] is not None
    assert env.conn.execute(f"SELECT count(*) FROM {L}_private.suppressed_names").fetchone()[0] == 1


def test_a_failed_read_stops_and_the_key_goes_in_the_header_only(env, monkeypatch):
    sent = []

    def go(url, timeout, headers, max_bytes):
        sent.append((url, dict(headers)))
        return 429, b"", url, {}

    monkeypatch.setattr(fetchgate, "_go", go)
    out = capture.run_night(env.conn, L, anytime=True, today=TODAY, log=lambda *a: None, pacer=Pacer(), key=KEY,
                            sleep=lambda s: None)
    assert not out["ok"] and out["calls"] == 1 and "429" in out["stopped"]
    url, headers = sent[0]
    assert headers[capture.KEY_HEADER] == KEY and KEY not in url and "subscription-key" not in url
    row = env.conn.execute(f"SELECT asked, status, document FROM {L}.calls").fetchone()
    assert KEY not in row[0] and row[1] == 429 and row[2] is None


def test_a_200_that_is_not_an_answer_is_a_failed_read(env):
    out = capture.run_night(env.conn, L, anytime=True, today=TODAY, log=lambda *a: None, pacer=Pacer(), key=KEY,
                            fetch=lambda url, t: (200, b'{"statusCode": 200, "note": "not an answer"}', url))
    assert not out["ok"] and "none of the three answers" in out["stopped"]


def test_off_peak_and_the_lookup_limit(env):
    nz = capture.NZ
    assert capture.off_peak(dt.datetime(2026, 11, 2, 21, 30, tzinfo=nz))          # a Monday
    assert not capture.off_peak(dt.datetime(2026, 11, 4, 21, 30, tzinfo=nz))      # a Wednesday
    assert not capture.off_peak(dt.datetime(2026, 11, 2, 22, 0, tzinfo=nz))
    out = capture.run_night(env.conn, L, today=TODAY, now=lambda: dt.datetime(2026, 11, 2, 12, 0, tzinfo=nz),
                            log=lambda *a: None, **_gate(FakeAPI()))
    assert out["calls"] == 0 and out["stopped"] == "off-peak ended"
    with pytest.raises(ValueError):
        capture.lookup(env.conn, list(range(11)), L, **_gate(FakeAPI()))


def test_the_suppression_mutants_are_caught_by_the_check(env, monkeypatch):
    """A suppressed estate whose names stay in its row, or whose flag is lost, is red."""
    from registers.insolvency import read
    _night(env, FakeAPI())
    capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(FakeAPI()))
    _load(env)
    assert check.reading(env.conn, STAGE, L, TODAY) == []
    monkeypatch.setattr(read, "private_names", lambda row: None)
    _load(env)
    assert any("with a name in the row" in p for p in check.reading(env.conn, STAGE, L, TODAY))
    monkeypatch.setattr(read, "suppressed", lambda e: False)
    _load(env)
    assert any("suppression flag is not the register's words" in p for p in check.reading(env.conn, STAGE, L, TODAY))


def _identifiers(env):
    return {(e, f): v for e, f, v in env.conn.execute(f"SELECT estate, field, value FROM {L}_private.identifiers").fetchall()}


def test_the_identifying_fields_are_kept_privately_and_flagged_by_a_removal(env):
    """3 November 2026 (Arthur: gather the identifying information too): the addresses and the month and year of birth
    are in the private ledger, never in a staged or published column; a removal flags them (ruling 142; it cleared
    them before 4 November 2026)."""
    _night(env, FakeAPI())
    ids = _identifiers(env)
    assert ids[(1001, "addressAtAdjudication")] == "1001 Invented Street, Exampletown"
    assert ids[(1001, "monthOfBirth")] == "4" and ids[(1001, "yearOfBirth")] == "1971"
    assert "1001 Invented Road" in ids[(1001, "currentAddresses")]
    _load(env)
    _published(env)
    api = FakeAPI(removed={1001}, gone={1001})
    assert capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(api))["ok"]
    left = _identifiers(env)
    assert left[(1001, "monthOfBirth")] == "4" and any(e == 1002 for e, _ in left), "kept through the removal"
    flagged = {f for f, r in env.conn.execute(f"SELECT field, removed_at FROM {L}_private.identifiers WHERE estate = 1001")
               .fetchall() if r is not None}
    assert flagged >= {"monthOfBirth", "addressAtAdjudication"}
    assert not any(e == 9 or "Invented Way" in v for (e, _), v in left.items()), "a removals page gives no identifiers"
    _load(env)
    assert check.reading(env.conn, STAGE, L, TODAY) == []
    env.conn.execute(f"UPDATE {L}_private.identifiers SET removed_at = NULL WHERE estate = 1001")
    assert any("hold identifying fields from before, not flagged" in p for p in check.reading(env.conn, STAGE, L, TODAY))


def test_the_identifying_fields_are_only_in_the_private_schema(env):
    """4 November 2026: the identifiers table sat in the lane's own schema, which the session login reads; it belongs in
    `<lane>_private`, and the check is red on a copy left in the lane's schema or on a login that can see the private one."""
    _night(env, FakeAPI())
    assert env.conn.execute(f"SELECT to_regclass('{L}.identifiers') IS NULL").fetchone()[0]
    assert env.conn.execute(f"SELECT count(*) FROM {L}_private.identifiers").fetchone()[0] > 0
    _load(env)
    assert not any("private" in p or "can see" in p for p in check.reading(env.conn, STAGE, L, TODAY))
    env.conn.execute(f"CREATE TABLE {L}.identifiers (estate bigint)")
    assert any("outside the private schema" in p for p in check.reading(env.conn, STAGE, L, TODAY))
    env.conn.execute(f"DROP TABLE {L}.identifiers")
    env.conn.execute(f"GRANT USAGE ON SCHEMA {L}_private TO qv4_read")
    assert any("qv4_read can see" in p for p in check.reading(env.conn, STAGE, L, TODAY))



def test_a_search_answer_after_a_removal_is_an_answer_since(env, monkeypatch):
    """3 November 2026: 982 estates the first removals run named came back in the night's search walk before any detail
    was asked; the load read the search answer as the latest, the check counted details only, and the load went red."""
    env.conn.execute(capture.ledger_sql(L))
    cid = env.conn.execute(f"INSERT INTO {L}.calls (at, day, why, asked, status) VALUES (now() - interval '2 days', "
                           f"current_date - 2, 'removals', 'x', 200) RETURNING id").fetchone()[0]
    env.conn.execute(f"INSERT INTO {L}.removals (estate, removed_on, call, seen_at) VALUES (1001, 'x', %s, "
                     f"now() - interval '2 days')", (cid,))
    monkeypatch.setattr(capture, "details_wanted", lambda *a, **k: [])
    _night(env, FakeAPI())
    _, rows, _ = _load(env)
    assert 1001 in rows, "the load reads the later search answer"
    assert not any("the removals named with no answer since" in p for p in check.reading(env.conn, STAGE, L, TODAY))


# --- 5 November 2026: the removals job re-asked every naming of the last days, and one lost answer failed the run ---

def _removals(env, api, today=TODAY, **kw):
    return capture.run_removals(env.conn, L, today=today, log=lambda *a: None, **kw, **_gate(api))


def _detail_asks(api, n):
    return sum(1 for u in api.urls if u.endswith(f"/insolvencies/{n}"))


class Lost:
    """The fake API, but the detail calls for `estates` get no answer at all (an exception, as a name lookup or an SSL
    EOF gives)."""

    def __init__(self, api, estates, exc=None):
        self.api, self.estates, self.exc = api, set(estates), exc
        self.urls = api.urls

    def __call__(self, url, timeout):
        if any(url.endswith(f"/insolvencies/{n}") for n in self.estates):
            self.api.urls.append(url)
            raise self.exc or OSError("[Errno -5] No address associated with hostname")
        return self.api(url, timeout)


def test_a_naming_repeated_by_the_next_days_span_is_not_asked_again(env):
    """The span starts on the cursor's day, so yesterday's naming is on today's page again; 4 and 5 November recorded
    it again under a new time and asked every one again (76 of the 78 items on 5 November were byte for byte 4
    November's)."""
    _night(env, FakeAPI())
    api = FakeAPI(removed={1001})
    assert _removals(env, api)["asked_again"] == 1
    out = _removals(env, api, today=TODAY + dt.timedelta(days=1))
    assert out["ok"] and out["named"] == 1 and out["repeated"] == 1 and out["asked_again"] == 0 and out["flagged"] == 0
    assert _detail_asks(api, 1001) == 1, "the same item, named again, is the same removal: asked once"
    assert env.conn.execute(f"SELECT count(*) FROM {L}.removals WHERE estate = 1001").fetchone()[0] == 1
    assert env.conn.execute(f"SELECT value FROM {L}.cursor WHERE what = 'removals'").fetchone()[0] == \
        (TODAY + dt.timedelta(days=1)).isoformat()


def test_a_changed_item_is_a_new_correction_and_asked_again(env):
    _night(env, FakeAPI())
    api = FakeAPI(removed={1001})
    _removals(env, api)
    env.conn.execute(f"UPDATE {L}.removals SET item_sha = 'an earlier item' WHERE estate = 1001")
    out = _removals(env, api, today=TODAY + dt.timedelta(days=1))
    assert out["repeated"] == 0 and out["asked_again"] == 1 and _detail_asks(api, 1001) == 2


def test_a_lone_transport_failure_is_a_line_and_waits_for_the_next_run(env):
    """4 November 21:07 (a name lookup) and 5 November 05:54 (an SSL EOF): one lost answer after 72 and 330 good ones
    failed the whole run. Now it is a line; that estate is asked next run, and a call with no answer is not an answer."""
    _night(env, FakeAPI())
    api = FakeAPI(removed={1001, 1002, 1004})
    out = _removals(env, Lost(api, {1002}))
    assert out["ok"] and out["asked_again"] == 2 and out["no_answer"] == 1 and "no answer" in out["stopped"]
    assert env.conn.execute(f"SELECT value FROM {L}.cursor WHERE what = 'removals'").fetchone()[0] == TODAY.isoformat()
    again = _removals(env, api, today=TODAY + dt.timedelta(days=1))
    assert again["ok"] and again["asked_again"] == 1 and _detail_asks(api, 1002) == 2 and _detail_asks(api, 1001) == 1


def test_an_incomplete_read_is_a_transport_failure_too(env):
    import http.client
    _night(env, FakeAPI())
    api = FakeAPI(removed={1001, 1002})
    out = _removals(env, Lost(api, {1001}, http.client.IncompleteRead(b"")))
    assert out["ok"] and out["no_answer"] == 1 and out["asked_again"] == 1


def test_three_transport_failures_in_a_row_stop_the_run(env):
    _night(env, FakeAPI())
    api = FakeAPI(removed={1001, 1002, 1004, 1005})
    out = _removals(env, Lost(api, {1001, 1002, 1004}))
    assert not out["ok"] and "3 transport failures in a row" in out["stopped"] and _detail_asks(api, 1005) == 0


def test_a_lost_removals_page_keeps_the_cursor(env):
    _night(env, FakeAPI())
    api = FakeAPI(removed={1001})

    def lost_page(url, timeout):
        if "removalorcorrections" in url:
            raise OSError("[SSL: UNEXPECTED_EOF_WHILE_READING]")
        return api(url, timeout)
    out = _removals(env, lost_page)
    assert out["ok"] and out["no_answer"] == 1 and "asked again next run" in out["stopped"]
    assert env.conn.execute(f"SELECT value FROM {L}.cursor WHERE what = 'removals'").fetchone() is None


def test_the_re_asks_keep_to_the_run_s_budget_and_the_rest_wait(env):
    """5 November 05:54: 330 re-asks at 5 s took 1,782 s of the job's 1,800 s deadline, and 596 more were waiting."""
    _night(env, FakeAPI())
    api = FakeAPI(removed={1001, 1002, 1004})
    ticks = iter(range(0, 10_000, 10))
    out = _removals(env, api, clock=lambda: next(ticks), budget_s=25)
    assert out["ok"] and out["asked_again"] == 2 and "1 re-asks wait for the next run" in out["stopped"]
    assert env.conn.execute(f"SELECT value FROM {L}.cursor WHERE what = 'removals'").fetchone()[0] == TODAY.isoformat()
    again = _removals(env, api)
    assert again["asked_again"] == 1 and again["repeated"] == 3


def test_no_re_asks_in_the_wednesday_maintenance(env):
    """4 November (a Wednesday) 21:07: the re-asks ran into the interface's 21:00 to 23:00 maintenance; three lost
    answers in a row there would have the gate hold the host until a person clears it."""
    _night(env, FakeAPI())
    api = FakeAPI(removed={1001})
    wed = dt.datetime(2026, 11, 4, 21, 0, tzinfo=capture.NZ)
    out = _removals(env, api, now=lambda: wed)
    assert out["ok"] and out["named"] == 1 and out["asked_again"] == 0 and "maintenance" in out["stopped"]
    assert _detail_asks(api, 1001) == 0


def test_the_ledger_ddl_runs_once_and_then_waits_on_no_reader(env, monkeypatch):
    """7 November 2026: the night's capture ran the ledger's DDL first, its ALTER ... ADD COLUMN IF NOT EXISTS waited
    on the table's exclusive lock behind a reader, and the run was cancelled at its 300 s limit before its first call.
    Once applied, only the catalogue is read (no lock on a table); a changed DDL is applied again."""
    sent = []

    class Seen:
        def execute(self, sql, params=None):
            sent.append(sql)
            return env.conn.execute(sql, params)
    assert capture.ensure_ledger(Seen(), L) is True
    sent.clear()
    assert capture.ensure_ledger(Seen(), L) is False
    assert sent and all(q.lstrip().startswith("SELECT obj_description") for q in sent), sent
    ddl = capture.ledger_sql
    monkeypatch.setattr(capture, "ledger_sql", lambda schema=capture.SCHEMA: ddl(schema) + "\n-- changed")
    assert capture.ensure_ledger(Seen(), L) is True


def test_an_estate_with_no_status_is_not_red_for_its_suppression_flag(env):
    """8 November 2026: 315 DRO estates known from the search answer alone carry no insolvencyStatus; the check's test was
    NULL, NULL is distinct from false, and the load was red on rows nothing suppressed."""
    _night(env, FakeAPI())
    capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(FakeAPI()))
    _load(env)
    env.conn.execute(f"UPDATE {STAGE}.estates SET status = NULL WHERE NOT suppressed")
    assert not any("suppression flag" in p for p in check.reading(env.conn, STAGE, L, TODAY))
    env.conn.execute(f"UPDATE {STAGE}.estates SET suppressed = true WHERE status IS NULL")
    assert any("suppression flag" in p for p in check.reading(env.conn, STAGE, L, TODAY))


def test_the_api_count_takes_one_night_per_month_never_every_window_asked(env):
    """9 November 2026: the capture splits a month where the recent window starts, and the split moves nightly; summing
    every window ever asked read 14,089 said for 13,495 seen on a walk that was whole. One night's windows in a month
    are summed, and the month takes its largest night; a real shortfall still shows."""
    capture.ensure_ledger(env.conn, L)

    def asked(day, f, t, total, register="Insolvency"):
        env.conn.execute(f"INSERT INTO {L}.calls (at, day, why, asked, status, total_items) VALUES (%s, %s, 'search', %s, 200, %s)",
                         (f"{day}T21:00:00+13:00", day, f"/insolvencies?date-from={f}&date-to={t}&register={register}&page=1&page-size=100", total))

    asked("2026-11-07", "2026-09-01", "2026-09-07", 30)    # night 1: September split at the 8th
    asked("2026-11-07", "2026-09-08", "2026-09-30", 132)
    asked("2026-11-08", "2026-09-01", "2026-09-08", 46)    # night 2: split at the 9th, one estate more since
    asked("2026-11-08", "2026-09-09", "2026-09-30", 117)
    asked("2026-11-08", "2026-08-01", "2026-08-31", 10)
    call = env.conn.execute(f"SELECT max(id) FROM {L}.calls").fetchone()[0]
    for n in range(173):
        env.conn.execute(f"INSERT INTO {L}.search_seen (estate, register, call) VALUES (%s, 'Insolvency', %s)", (900000 + n, call))
    assert check.against_api(env.conn, L) == [("Insolvency", 173, 173)], "every window summed would say 335"
    env.conn.execute(f"DELETE FROM {L}.search_seen WHERE estate >= 900150")
    assert check.against_api(env.conn, L) == [("Insolvency", 173, 150)]
