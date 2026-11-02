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
                    for n in sorted(self.removed)] if q["page"] == "1" and q["date-to"] == TODAY.isoformat() else []
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
    withheld = dict(env.conn.execute(f"SELECT estate_number, reason FROM {STAGE}.withheld").fetchall())
    return counts, rows, withheld


def test_the_night_the_load_and_the_check(env):
    api = FakeAPI()
    out = _night(env, api)
    assert out["ok"] and out["details"] == 6 and out["stopped"] == "nothing wanted is left"
    assert all("Invented Street" not in b.decode() and "Invented Road" not in b.decode() and "Birth" not in b.decode()
               for b in env.store.values()), "an address or a birth field was landed"
    counts, rows, withheld = _load(env)
    assert set(rows) == {1001, 1004, 1005, 2001} and rows[1004] == "company"
    assert withheld[1002].startswith("past its window") and withheld[1003].startswith("suppressed")
    assert counts["estates"] == 6 and counts["set_aside"] == 0
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


def test_a_removal_is_out_at_once_its_answers_withdrawn_and_asked_again(env):
    _night(env, FakeAPI())
    _load(env)
    assert 1001 in _published(env)
    api = FakeAPI(removed={1001}, gone={1001})
    out = capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(api))
    assert out["ok"] and out["named"] == 1 and out["taken_out"] == 1 and out["asked_again"] == 1 and out["corrected"] == 0
    assert 1001 not in {r[0] for r in env.conn.execute(f"SELECT estate_number FROM {L}.estates").fetchall()}
    shas = [r[0] for r in env.conn.execute(f"SELECT document FROM {L}.calls WHERE estate = 1001 AND why = 'detail'").fetchall()]
    w = landing.documents_of(shas, env.raw)
    assert w and all(d["withdrawn"] and "removal or correction" in d["withdrawn"] for d in w.values()), \
        "the removed estate's answers are withdrawn, never deleted"
    assert any(u.endswith("/insolvencies/1001") for u in api.urls)
    _, rows, withheld = _load(env)
    assert 1001 not in rows and withheld[1001] == "absent from the register when last asked"
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


def test_the_removal_mutant_is_caught(env, monkeypatch):
    """apply_removal made a no-op: the row stays after its removal, and the check goes red."""
    _night(env, FakeAPI())
    _load(env)
    _published(env)
    monkeypatch.setattr(capture, "apply_removal", lambda *a, **k: 0)
    capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(FakeAPI(removed={1001}, gone={1001})))
    assert 1001 in {r[0] for r in env.conn.execute(f"SELECT estate_number FROM {L}.estates").fetchall()}
    assert any("the removals named" in p for p in check.reading(env.conn, L, L, TODAY))


def test_a_removal_between_build_and_publish_is_not_published(env):
    _night(env, FakeAPI())
    _load(env)
    capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(FakeAPI(removed={1001}, gone={1001})))
    assert 1001 not in _published(env)          # staged before the removal; taken out again at publish


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


def test_the_window_and_suppression_mutants_are_caught_by_the_check(env, monkeypatch):
    """The load's withholding made a no-op: the suppressed estate and the one past its window are staged, and the check
    goes red on them."""
    from registers.insolvency import read
    _night(env, FakeAPI())
    capture.run_removals(env.conn, L, today=TODAY, log=lambda *a: None, **_gate(FakeAPI()))
    monkeypatch.setattr(read, "why_withheld", lambda *a, **k: None)
    _, rows, _ = _load(env)
    assert {1002, 1003} <= set(rows)
    assert any("suppressed, annulled or past their window" in p for p in check.reading(env.conn, STAGE, L, TODAY))
