"""Company monitoring's tests (plan 5.5). The reading and the differences are
tested on invented answers shaped like the interface's (every name and
address invented); the night is run on the filled sample with a fake
transport and an in-memory store, inside a transaction that is rolled back;
the eight real answers are read from the filled sample. Nothing calls the
interface. The slow test compares the real answers with the real lane."""
import datetime as dt
import hashlib
import json
import os

import pytest

from support import db, fetchgate, rowcontract
from registers.companies import check, monitor as M
from registers.companies.load import table
from registers.companies.tests.test_companies_lane import LANE

N1, N2 = "9429046854308", "9429052976568"           # sample companies (sample.list)
SOLE = "9429053867209"


def _stamp(day: str) -> str:
    return f"{day}T00:00:00.000+1200"


def _addr(kind, line="1 Example Street"):
    return {"addressType": kind, "address1": line, "address2": "Exampletown", "address3": None, "address4": None,
            "postCode": "1010", "countryCode": "NZ", "careOf": None, "startDate": _stamp("2020-02-01"),
            "endDate": None, "uniqueIdentifier": f"a-{kind}", "pafId": None}


def _role(first, last, start, end=None, uid=None, rtype="Director"):
    return {"roleType": rtype, "roleStatus": "INACTIVE" if end else "ACTIVE", "startDate": _stamp(start),
            "endDate": _stamp(end) if end else None, "uniqueIdentifier": uid or f"r-{first}",
            "rolePerson": {"firstName": first, "middleNames": None, "lastName": last, "title": None},
            "roleEntity": None, "roleAddress": [_addr("RESIDENTIAL", "9 Private Lane")], "roleAsicAddress": None}


def _answer(nzbn=N1, *, code="LTD", name="Example Limited", status="Registered", roles=(), holdings=(),
            history=(), addresses=None, **kw):
    return {"nzbn": nzbn, "entityName": name, "entityTypeCode": code, "entityTypeDescription": code,
            "entityStatusCode": "50", "entityStatusDescription": status, "registrationDate": _stamp("2018-06-25"),
            "lastUpdatedDate": "2026-10-01T09:00:00.000+1300", "sourceRegister": "COMPANY", "roles": list(roles),
            "addresses": {"addressList": addresses if addresses is not None else
                          [_addr("REGISTERED"), _addr("SERVICE", "5 Service Road")]},
            "emailAddresses": [{"emailAddress": "someone@example.invalid"}], "phoneNumbers": [{"phoneNumber": "0"}],
            "privacySettings": {}, "tradingNames": [],
            "company-details": {"shareholding": {"numberOfShares": 100, "shareAllocation": list(holdings),
                                                 "historicShareholder": list(history)}}, **kw}


def _alloc(shares, *holders):
    return {"allocation": shares, "shareholder": list(holders)}


def _person_holder(full, start="2018-06-25", hist=False, end=None):
    k = "historicIndividualShareholder" if hist else "individualShareholder"
    a = "historicShareholderAddress" if hist else "shareholderAddress"
    h = {"type": "individual", "appointmentDate": _stamp(start), k: {"fullName": full}, a: _addr("HOLDER")}
    if end:
        h["vacationDate"] = _stamp(end)
    return h


def _org_holder(name, nzbn="9429000000017", start="2019-01-01"):
    return {"type": "entity", "appointmentDate": _stamp(start),
            "otherShareholder": {"currentEntityName": name, "nzbn": nzbn}}


def _read(obj, at="2026-10-21T23:30:00+13:00"):
    data = json.dumps(obj).encode()
    sha = hashlib.sha256(data).hexdigest()
    return M.read_answer(data, sha, at), sha


def _monthly(name="Example Limited", status="Registered", directors=(), holdings=(), office=None):
    s = M.State("monthly", "e" * 64, "the monthly file companies-2026-08", name, status)
    for full, start in directors:
        s.directors[(M.person_key(full), start)] = {"name": full, "key": f"d/{full}", "suppressed": False,
                                                     "ended": None}
    for full, shares, org in holdings:
        s.holdings[(M.holder_key(full, org), shares)] = {"name": full, "key": f"s/{full}", "suppressed": False}
    if office:
        s.office = {"key": M.office_key(office), "start": "2015-01-01", "text": ", ".join(x for x in office if x), "held_key": "o/1"}
    s.compares = tuple(c for c, held in (("directors", s.directors), ("holdings", s.holdings), ("office", s.office))
                       if held)
    return s


def _kinds(changes):
    return sorted((c[0], c[4], c[5]) for c in changes)


# --- the reading ----------------------------------------------------------------------------------------------

def test_an_answer_reads_roles_holdings_and_the_registered_office_and_keeps_every_other_address_private():
    r, _ = _read(_answer(roles=[_role("Ann", "Able", "2018-06-25"), _role("Ben", "Baker", "2018-06-25", "2026-09-30")],
                         holdings=[_alloc(70, _person_holder("Ann Able")),
                                   _alloc(30, _org_holder("7559576 - Holder Co Limited"))],
                         history=[_person_holder("Ben Baker", hist=True, end="2026-09-30")]))
    assert [(x["full"], x["start"], x["end"]) for x in r.roles] == [("Ann Able", "2018-06-25", None),
                                                                    ("Ben Baker", "2018-06-25", "2026-09-30")]
    names = {x["name"]: x for x in r.holdings}
    assert "Holder Co Limited" in names                                   # the register number is off the name
    assert names["Ben Baker"]["end"] == "2026-09-30" and not names["Ben Baker"]["current"]
    assert [o["line_1"] for o in r.offices] == ["1 Example Street"]       # REGISTERED only
    kinds = sorted(k for _, k, _ in r.private)
    assert kinds == ["holder", "holder", "role", "role", "service"]
    text = json.dumps([r.entity, r.roles, r.holdings, r.offices])
    assert "9 Private Lane" not in text and "5 Service Road" not in text
    assert "example.invalid" not in text and r.set_aside == []


def test_sole_traders_partnerships_and_trusts_are_kinds_of_their_own_and_their_addresses_are_all_private():
    sole, _ = _read(_answer(SOLE, code="Sole_Trader", name=None, addresses=[_addr("OFFICE")]))
    part, _ = _read(_answer(code="Partnership", addresses=[]))
    trust, _ = _read(_answer(code="Trading_Trust", roles=[_role("Cy", "Carter", "2024-09-16", rtype="Trustee")],
                             addresses=[_addr("OFFICE"), _addr("REGISTERED")]))
    assert (sole.entity["kind"], part.entity["kind"], trust.entity["kind"]) == ("sole_trader", "partnership", "trust")
    assert sole.entity["name"] is None                                     # the register withholds it
    assert trust.offices == [] and sole.offices == []
    assert sorted(k for _, k, _ in trust.private) == ["office", "registered", "role"]


def test_a_withheld_name_is_not_read_and_a_role_with_no_name_is_set_aside():
    r, _ = _read(_answer(privacySettings={"namePrivateInformation": True},
                         roles=[{"roleType": "Director", "rolePerson": {}, "roleEntity": None}]))
    assert r.entity["name"] is None and len(r.set_aside) == 1 and r.roles == []


def test_the_day_is_the_interface_s_own_new_zealand_day():
    assert M.day_of("2025-04-01T00:00:00.000+1300") == "2025-04-01"
    assert M.day_of("2018-06-25T23:59:59.000+1200") == "2018-06-25"
    assert M.day_of(None) is None and M.day_of("soon") is None


# --- the differences ------------------------------------------------------------------------------------------

def test_an_ended_role_takes_the_interface_s_end_date_and_a_new_one_its_start():
    before = _monthly(directors=[("Ann Able", "2018-06-25"), ("Ben Baker", "2018-06-25")])
    r, sha = _read(_answer(roles=[_role("Ann", "Able", "2018-06-25"), _role("Ben", "Baker", "2018-06-25", "2026-09-30"),
                                  _role("Cy", "Carter", "2026-10-01")]))
    got = _kinds(M.diff(before, M.state_of_answer(r, sha), r))
    assert got == [("director_appointed", "2026-10-01", "register"), ("director_ended", "2026-09-30", "register")]


def test_a_role_the_answer_does_not_list_is_seen_not_dated():
    before = _monthly(directors=[("Ann Able", "2018-06-25"), ("Dee Doe", "2001-01-01")])
    r, sha = _read(_answer(roles=[_role("Ann", "Able", "2018-06-25")]))
    assert _kinds(M.diff(before, M.state_of_answer(r, sha), r)) == [("director_not_listed", None, "seen")]


def test_a_holding_that_left_takes_its_vacation_date_and_a_company_holder_matches_without_its_number():
    before = _monthly(holdings=[("Ann Able", 70, False), ("Holder Co Limited", 30, True), ("Ben Baker", 10, False)])
    r, sha = _read(_answer(holdings=[_alloc(70, _person_holder("Ann Able")),
                                     _alloc(30, _org_holder("7559576 - HOLDER CO LIMITED"))],
                           history=[_person_holder("Ben Baker", hist=True, end="2026-09-30")]))
    assert _kinds(M.diff(before, M.state_of_answer(r, sha), r)) == [("holding_ended", "2026-09-30", "register")]


def test_status_name_and_office_changes_and_an_unchanged_answer_has_none():
    office = ("1 Example Street", "Exampletown", None, None, "1010")
    r, sha = _read(_answer())
    assert M.diff(_monthly(office=office), M.state_of_answer(r, sha), r) == []
    r2, sha2 = _read(_answer(name="Renamed Limited", status="Removed",
                             addresses=[{**_addr("REGISTERED", "2 Other Road"), "startDate": _stamp("2026-10-02")}]))
    got = _kinds(M.diff(_monthly(office=office), M.state_of_answer(r2, sha2), r2))
    assert got == [("name", None, "seen"), ("registered_office", "2026-10-02", "register"), ("status", None, "seen")]


def test_a_category_the_monthly_file_lists_nothing_current_for_is_not_compared():
    """The August file holds no current role of a removed company: absence there is not a difference."""
    r, sha = _read(_answer(status="Removed", roles=[_role("Ann", "Able", "2018-06-25")],
                           holdings=[_alloc(1, _person_holder("Ann Able"))]))
    assert _kinds(M.diff(_monthly(status="Removed"), M.state_of_answer(r, sha), r)) == []
    assert M.diff(None, M.state_of_answer(r, sha), r) == []               # a first sight is not a change


# --- the call -------------------------------------------------------------------------------------------------

def test_off_peak_is_before_the_societies_asks_and_never_the_maintenance_window():
    at = lambda d, h, m=0: dt.datetime(2026, 10, d, h, m, tzinfo=M.NZ)   # 21 October 2026 is a Wednesday
    assert M.off_peak(at(20, 23, 30)) and M.off_peak(at(21, 0, 30))
    assert not M.off_peak(at(21, 22, 30))                                  # Wednesday 21:00 to 23:00
    assert M.off_peak(at(21, 23, 30))
    assert not M.off_peak(at(22, 2)) and not M.off_peak(at(22, 12))


def _gate(monkeypatch, tmp_path):
    host = fetchgate.host_of(M.BASE)
    monkeypatch.setitem(fetchgate._ROBOTS, host, fetchgate.Robots(host, "", 404, False, 0.0, "", ""))
    monkeypatch.setattr(fetchgate, "LEDGER_DIR", str(tmp_path / "gate"))
    return {"ledger_dir": str(tmp_path / "gate"), "pacer": fetchgate.Pacer(sleep=lambda s: None)}


def test_a_call_goes_through_the_gate_and_a_block_lands_nothing(monkeypatch, tmp_path):
    g = _gate(monkeypatch, tmp_path)
    got, ref = M.fetch_entity(N1, None, key="SECRETKEY", fetch=lambda u, t: (429, b"", u), **g)
    assert ref is None and got.blocked
    with pytest.raises(fetchgate.Refused):
        M.fetch_entity(N1, None, key="SECRETKEY", fetch=lambda u, t: (200, b"{}", u), positions_dir=str(tmp_path),
                       ledger_dir=g["ledger_dir"], pacer=g["pacer"])
    with pytest.raises(ValueError):
        M.entity_url("9429046854309")                                      # a wrong check digit
    assert "SECRETKEY" not in "".join(p.read_text() for p in (tmp_path / "gate").iterdir())


def test_the_key_is_read_from_the_credential_folder_and_its_absence_names_no_value(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "CRED_DIR", str(tmp_path))
    with pytest.raises(RuntimeError) as e:
        M.api_key()
    assert "nzbn.env" in str(e.value) or "FileNotFoundError" in str(e.value)
    (tmp_path / "nzbn.env").write_text("NZBN_API_KEY='abc'\n")
    assert M.api_key() == "abc"


# --- what is published ----------------------------------------------------------------------------------------

def _publish_sql():
    """publish.sql without its comments."""
    with open(os.path.join(LANE, "publish.sql"), encoding="utf-8") as f:
        return "\n".join(line.split("--")[0] for line in f)


def test_the_hand_off_takes_the_asker_from_the_login_and_is_granted_to_the_product_reader_only():
    sql = _publish_sql()
    for fn in ("request_company_check", "watch_company", "unwatch_company"):
        assert f"REVOKE ALL ON FUNCTION pub.{fn}(" in sql and f"ON FUNCTION pub.{fn}(" in sql
    assert sql.count("SECURITY DEFINER") == 3 and sql.count("session_user") == 2
    assert "p_asked_by" not in sql and "asked_by text" not in sql.split("FUNCTION pub.request_company_check")[1][:120]


def test_no_published_monitor_view_names_an_address_column_other_than_the_registered_office():
    sql = _publish_sql().split("CREATE OR REPLACE VIEW pub.company_changes")[1]
    for col in rowcontract.FORBIDDEN_COLUMNS + ("line_1", "postcode", "lookup_addresses", "companies_private"):
        assert col not in sql, col


# --- the night, on the filled sample ---------------------------------------------------------------------------

class _NoCommit:
    """The sample connection with commit turned off, so a test's night is rolled back whole."""

    def __init__(self, conn):
        self._c = conn

    def commit(self):
        pass

    def __getattr__(self, name):
        return getattr(self._c, name)


@pytest.fixture
def night(filled, monkeypatch, tmp_path):
    g = _gate(monkeypatch, tmp_path)
    store = {}

    class Ref:
        def __init__(self, sha):
            self.sha256 = sha

    def fake_land(data, **kw):
        sha = hashlib.sha256(data).hexdigest()
        store[sha] = data
        return Ref(sha), True
    monkeypatch.setattr(M, "land", fake_land)
    monkeypatch.setattr(M, "read_bytes", lambda sha: store[sha])
    monkeypatch.setattr(check, "in_store", lambda sha: sha in store)
    monkeypatch.setattr("support.jobrun.RUNS", str(tmp_path / "runs.jsonl"))
    conn = filled["conn"]
    conn.rollback()
    T = M.Tables(filled["schema"], shared=True)
    for t in M.KEPT + M.REBUILT + M.PRIVATE_REBUILT:
        conn.execute(f"DELETE FROM {getattr(T, t)}")
    clock = {"now": dt.datetime(2026, 10, 22, 23, 30, tzinfo=M.NZ)}
    answers = {}

    def fetch(url, timeout):
        n = url.rsplit("/", 1)[1]
        clock["now"] += dt.timedelta(seconds=5)
        if n not in answers:
            return 404, b"", url
        a = answers[n]
        if isinstance(a, BaseException):
            raise a
        return (a, b"", url) if isinstance(a, int) else (200, json.dumps(a).encode(), url)

    def go(**kw):
        return M.run(_NoCommit(conn), filled["schema"], True, key="SECRETKEY", fetch=fetch, now=lambda: clock["now"],
                     log=lambda *a: None, **g, **kw)

    def ask(nzbn=None, name=None):
        # stamped from the fixture's clock: the column's DEFAULT now() is the real clock, and a threshold
        # measured against the fixture's clock then passes or fails by the day the suite runs
        return conn.execute(f"INSERT INTO {T.requests} (nzbn, name, product, asked_by, asked_at) VALUES (%s, %s, "
                            f"'test', session_user, %s) RETURNING id", (nzbn, name, clock["now"])).fetchone()[0]

    yield {"conn": conn, "T": T, "go": go, "ask": ask, "answers": answers, "clock": clock, "store": store,
           "fetch": fetch, "gate": g,
           "t": lambda n: table(filled["schema"], n, True)}
    conn.rollback()


def _held_directors(conn, T, nzbn):
    return conn.execute(f"SELECT full_name, appointed_on FROM {T.directors} WHERE nzbn = %s AND in_latest",
                        (nzbn,)).fetchall()


def test_a_request_is_answered_by_one_call_and_its_differences_are_dated_changes(night):
    conn, T = night["conn"], night["T"]
    held = _held_directors(conn, T, N1)
    assert held, "the sample holds the company's directors"
    (full, start), rest = held[0], held[1:]
    first, *more = full.split()
    roles = [_role(first, " ".join(more), start.isoformat(), "2026-10-15")]
    roles += [_role(f.split()[0], " ".join(f.split()[1:]), s.isoformat(), uid=f"r{i}") for i, (f, s) in enumerate(rest)]
    night["answers"][N1] = _answer(N1, roles=roles, addresses=[])
    rid = night["ask"](N1)
    out = night["go"]()
    assert out["ok"] and out["calls"] == 1 and out["answered"] == 1
    state, call = conn.execute(f"SELECT state, call_id FROM {T.requests} WHERE id = %s", (rid,)).fetchone()
    assert state == "answered" and call
    ch = conn.execute(f"SELECT kind, effective_on, date_basis, held_key FROM {T.changes} WHERE nzbn = %s", (N1,)).fetchall()
    assert ("director_ended", dt.date(2026, 10, 15), "register") in [c[:3] for c in ch]
    assert all(c[3] for c in ch if c[0] == "director_ended")             # it names the monthly row it ends
    end = conn.execute(f"SELECT ended_on FROM {T.lookup_roles} WHERE nzbn = %s AND held_key IS NOT NULL AND "
                       f"ended_on IS NOT NULL", (N1,)).fetchall()
    assert end == [(dt.date(2026, 10, 15),)]


def test_nothing_is_fetched_twice_in_a_day_and_bad_requests_are_set_aside_with_their_reason(night):
    conn, T = night["conn"], night["T"]
    night["answers"][N1] = _answer(N1, addresses=[])
    a, b = night["ask"](N1), night["ask"](N1)
    bad, gone = night["ask"]("1234"), night["ask"]("9429000000017")
    by_name = night["ask"](name="no such entity, invented")
    out = night["go"]()
    assert out["calls"] == 2 and out["from_today"] == 1                    # N1 once, the 404 once
    rows = dict(conn.execute(f"SELECT id, state || ': ' || coalesce(reason, '') FROM {T.requests}").fetchall())
    assert rows[a].startswith("answered") and "day's answer" in rows[b]
    assert rows[bad].startswith("set_aside: not an NZBN") and "404" in rows[gone]
    assert rows[by_name].startswith("set_aside: no entity held under that exact name")
    assert check.monitor_failed(conn, night["t"], now=night["clock"]["now"]) == []


def test_a_name_request_resolves_to_the_one_entity_held_under_it(night):
    conn, T = night["conn"], night["T"]
    name = conn.execute(f"SELECT name FROM {T.entities} WHERE nzbn = %s", (N2,)).fetchone()[0]
    night["answers"][N2] = _answer(N2, name=name, addresses=[])
    rid = night["ask"](name=name.lower())
    night["go"]()
    assert conn.execute(f"SELECT state, resolved_nzbn FROM {T.requests} WHERE id = %s", (rid,)).fetchone() == \
        ("answered", N2)


def test_a_block_stops_the_night_and_leaves_the_request_waiting(night):
    conn, T = night["conn"], night["T"]
    night["answers"][N1] = 429
    night["answers"][N2] = _answer(N2, addresses=[])
    r1, r2 = night["ask"](N1), night["ask"](N2)
    out = night["go"]()
    assert not out["ok"] and out["calls"] == 1 and "failed read" in out["stopped"]
    st = dict(conn.execute(f"SELECT id, state FROM {T.requests}").fetchall())
    assert st == {r1: "waiting", r2: "waiting"}
    night["clock"]["now"] += dt.timedelta(days=3)
    assert any("request(s) neither answered" in w
               for w in check.monitor_failed(conn, night["t"], now=night["clock"]["now"]))


def test_the_day_s_limit_stops_the_calls_and_the_check_counts_them(night, monkeypatch):
    conn, T = night["conn"], night["T"]
    for n in (N1, N2):
        night["answers"][n] = _answer(n, addresses=[])
        night["ask"](n)
    out = night["go"](daily_limit=1)
    assert out["calls"] == 1 and "limit" in out["stopped"]
    monkeypatch.setattr(M, "DAILY_LIMIT", 0)
    assert any("over the day's limit" in w for w in check.monitor_failed(conn, night["t"], now=night["clock"]["now"]))


def test_a_watch_falls_due_by_its_interval_and_off_peak_holds_the_night(night):
    conn, T = night["conn"], night["T"]
    night["answers"][N1] = _answer(N1, addresses=[])
    conn.execute(f"INSERT INTO {T.watch} (nzbn, product, asked_by, asked_at, every_days) VALUES (%s, 'test', "
                 f"session_user, %s, 7)", (N1, night["clock"]["now"]))
    assert night["go"]()["watches"] == 1
    night["clock"]["now"] += dt.timedelta(days=1)
    assert night["go"]()["watches"] == 0                                   # not due for a week
    night["clock"]["now"] += dt.timedelta(days=7)
    assert night["go"]()["watches"] == 1
    night["clock"]["now"] = night["clock"]["now"].replace(hour=12)
    night["ask"](N2)
    assert night["go"]()["stopped"] == "off-peak ended"


def test_a_change_that_cites_no_landed_answer_fails_the_check(night):
    conn, T = night["conn"], night["T"]
    night["answers"][N1] = _answer(N1, status="Removed", addresses=[])
    night["ask"](N1)
    night["go"]()
    assert conn.execute(f"SELECT count(*) FROM {T.changes}").fetchone()[0] >= 1
    conn.execute(f"UPDATE {T.calls} SET status = 500")
    assert any("cite no answer" in w for w in check.monitor_failed(conn, night["t"], now=night["clock"]["now"]))


def test_the_hand_off_writes_one_queue_row_with_the_login_as_the_asker(filled):
    from registers.companies import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.rollback()
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.companies_pub_"))
    rid = conn.execute(f"SELECT {schema}.companies_pub_request_company_check(%s, %s, 'board')", (N1, None)).fetchone()[0]
    who, me = conn.execute(f"SELECT asked_by, session_user FROM {schema}.companies_requests WHERE id = %s",
                           (rid,)).fetchone()
    conn.execute(f"SELECT {schema}.companies_pub_watch_company(%s, 'board', 3)", (N1,))
    conn.execute(f"SELECT {schema}.companies_pub_watch_company(%s, 'board', 5)", (N1,))
    watch = conn.execute(f"SELECT every_days, active FROM {schema}.companies_watch WHERE nzbn = %s", (N1,)).fetchall()
    conn.rollback()
    assert who == me and watch == [(5, True)]


# --- the real answers, from the filled sample --------------------------------------------------------------------

def _q(conn, sql):
    cur = conn.execute(sql)
    return [dict(zip([d[0] for d in cur.description], r)) for r in cur]


def test_the_proved_answers_are_read_as_their_sample_comments_say(filled):
    conn, s = filled["conn"], filled["schema"]
    conn.rollback()
    look = {r["nzbn"]: r for r in _q(conn, f"SELECT * FROM {s}.companies_lookups WHERE latest")}
    assert len(look) == len(M.PROOF)
    assert (look[SOLE]["kind"], look[SOLE]["name"]) == ("sole_trader", None)
    assert look["9429053867230"]["kind"] == "partnership" and look["9429053867223"]["kind"] == "trust"
    assert not look["9429053867223"]["in_monthly"] and look[N1]["in_monthly"]
    offices = {r["nzbn"] for r in _q(conn, f"SELECT nzbn FROM {s}.companies_lookup_offices")}
    assert "9429053867223" not in offices and N1 in offices
    changes = _q(conn, f"SELECT * FROM {s}.companies_changes")
    assert [(c["nzbn"], c["kind"], c["before"], c["after"]) for c in changes] == \
        [("9429041764886", "status", "In Liquidation", "Removed")]
    ends = _q(conn, f"SELECT ended_on FROM {s}.companies_lookup_roles WHERE ended_on IS NOT NULL")
    assert len(ends) >= 5                                                   # real end dates the file never had
    priv = _q(conn, f"SELECT kind, count(*) AS n FROM {s}_private.companies_lookup_addresses GROUP BY 1")
    assert {p["kind"] for p in priv} >= {"role", "holder", "office"}
    assert check.monitor_failed(conn, lambda n: table(s, n, True)) == []


def test_every_monitor_row_keeps_the_row_contract(filled):
    conn, s = filled["conn"], filled["schema"]
    conn.rollback()
    today = dt.date.today()
    for t in ("lookups", "lookup_roles", "lookup_holdings", "lookup_offices", "changes"):
        for r in _q(conn, f"SELECT * FROM {s}.companies_{t}"):
            row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version",
                                     "read_from")}
            row["loaded_at"] = r["loaded_at"].isoformat()
            row["filed"] = {k: (v.isoformat() if v else None) for k, v in r.items() if k.endswith("_on")}
            row["filed"]["ended_on_stated"] = True                          # the interface states every end
            assert rowcontract.validate(row, today) == [], (t, r["key"])


# --- slow: the real answers against the real lane -------------------------------------------------------------------

@pytest.mark.slow
def test_the_real_answers_against_the_real_lane_give_the_sample_s_one_change():
    """The five proved company answers compared with the lane's real tables
    (querynz_v4): no difference made by the monthly file's shape, and the
    sample's one change (9429041764886, In Liquidation to Removed) found
    against the August 2026 file, the latest file when the answers were
    proved. The October 2026 file (loaded 2 November 2026) shows that
    company Removed, as the answer of 21 October does, so the latest rows
    agree with every answer; a company's status in the August file is its
    earliest state in pub.company_states from that file on, else its
    current one. The real ledger holds no proved answer, so an empty
    temporary one stands in for it."""
    from dataclasses import replace
    from support.docstore.landing import read_bytes
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4-read.env")):
        pytest.skip("no real database here")
    out, earlier = [], []
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '60s'")
        conn.execute("CREATE TEMP TABLE calls (id bigint, nzbn text, at timestamptz, status int, document text)")
        T = M.Tables("companies", override={"calls": "pg_temp.calls"})
        for n, sha, at in M.PROOF[:5]:
            r = M.read_answer(read_bytes(sha), sha, at)
            held = M.held_state(conn, n, T)
            assert held is not None and held.source == "monthly", n
            out += [(n, c[0]) for c in M.diff(held, M.state_of_answer(r, sha), r)]
            was = conn.execute("SELECT file, status FROM pub.company_states WHERE entity_key = %s AND file >= 'companies-2026-08' "
                               "ORDER BY file LIMIT 1", ("companies/" + n,)).fetchone()
            if was:
                before = replace(held, status=was[1], label=f"the monthly file {was[0]}")
                earlier += [(n, c[0], c[2], c[3]) for c in M.diff(before, M.state_of_answer(r, sha), r)]
    assert out == []
    assert earlier == [("9429041764886", "status", "In Liquidation", "Removed")]


# ── the history backfill (Arthur, 1 November 2026) ──────────────────────────────────────────────────────────────

def _want(night, *nzbns):
    conn, T = night["conn"], night["T"]
    conn.execute(M._history_ddl(T))
    conn.execute(f"DELETE FROM {T.history_wanted}")
    for i, n in enumerate(nzbns, start=1):
        conn.execute(f"INSERT INTO {T.history_wanted} (nzbn, rank, reason) VALUES (%s, %s, 'test')", (n, i))


def _history(night, **kw):
    return M.run_history(_NoCommit(night["conn"]), night["T"].schema, True, key="SECRETKEY", fetch=night["fetch"],
                         now=lambda: night["clock"]["now"], log=lambda *a: None, **night["gate"], **kw)


def test_the_backfill_asks_in_rank_order_once_each_and_reads_ended_roles_with_the_register_s_dates(night):
    conn, T = night["conn"], night["T"]
    night["answers"][N1] = _answer(N1, addresses=[], roles=[_role("Ann", "Old", "2007-04-24", "2018-07-06", uid="r-old"),
                                                         _role("Bea", "Now", "2018-07-06", uid="r-now")])
    _want(night, N2, N1)                                   # N2 is absent from the register (404)
    out = _history(night)
    assert out["ok"] and (out["calls"], out["answered"], out["absent"]) == (2, 1, 1)
    assert out["stopped"] == "nothing wanted is left"
    asked = [r[0] for r in conn.execute(f"SELECT nzbn FROM {T.calls} WHERE why = 'history' ORDER BY id").fetchall()]
    assert asked == [N2, N1]
    roles = dict(conn.execute(f"SELECT last_name, ended_on FROM {T.lookup_roles} WHERE nzbn = %s", (N1,)).fetchall())
    assert str(roles["Old"]) == "2018-07-06" and roles["Now"] is None
    assert _history(night)["calls"] == 0, "an entity answered or found absent is never asked again"


def test_the_backfill_keeps_its_own_day_s_limit_and_the_monitor_s_limit_and_check_count_the_monitor_s_calls_only(night):
    conn, T = night["conn"], night["T"]
    for n in (N1, N2):
        night["answers"][n] = _answer(n, addresses=[])
    _want(night, N1, N2)
    out = _history(night, daily_limit=1)
    assert out["calls"] == 1 and "backfill's day's limit" in out["stopped"]
    night["ask"](N2)
    assert night["go"](daily_limit=1)["calls"] == 1, "the history call does not spend the monitor's day"
    assert not any("over the day's limit" in w for w in check.monitor_failed(conn, night["t"], now=night["clock"]["now"]))


def test_the_backfill_stops_at_a_failed_read_and_off_peak(night):
    night["answers"][N1] = 429
    night["answers"][N2] = _answer(N2, addresses=[])
    _want(night, N1, N2)
    out = _history(night)
    assert not out["ok"] and out["calls"] == 1 and "failed read" in out["stopped"]
    night["clock"]["now"] = night["clock"]["now"].replace(hour=12)
    assert _history(night)["stopped"] == "off-peak ended"


def test_a_call_that_gets_no_answer_is_recorded_skipped_and_asked_another_night(night):
    """1 November 2026 22:32 a timeout stopped the night after 1,018 calls; accelerated (2 November) one with no answer is
    recorded with status 0, skipped, and asked again on a later run; the run goes on."""
    night["answers"][N1] = TimeoutError("timed out")
    night["answers"][N2] = _answer(N2, addresses=[])
    _want(night, N1, N2)
    out = _history(night)
    assert out["ok"] and out["calls"] == 2 and out["no answer"] == 1 and out["answered"] == 1
    T = night["T"]
    assert night["conn"].execute(f"SELECT status FROM {T.calls} WHERE nzbn = %s", (N1,)).fetchone()[0] == 0
    night["answers"][N1] = _answer(N1, addresses=[])
    again = _history(night)
    assert again["calls"] == 1 and again["answered"] == 1, "the skipped one is asked on the next run"


def test_three_calls_in_a_row_with_no_answer_stop_the_backfill(night, monkeypatch):
    monkeypatch.setattr(M, "HISTORY_NO_ANSWER_RUN", 2)
    night["answers"][N1] = TimeoutError("timed out")
    night["answers"][N2] = TimeoutError("timed out")
    _want(night, N1, N2)
    out = _history(night)
    assert not out["ok"] and out["calls"] == 2 and "2 calls in a row got no answer" in out["stopped"]


def test_the_backfill_s_hours_add_six_to_seven_after_the_societies_asks_and_its_floor_is_a_second():
    at = lambda d, h, m=0: M.dt.datetime(2026, 10, d, h, m, tzinfo=M.NZ)
    assert M.history_off_peak(at(20, 23)) and M.history_off_peak(at(21, 0, 30)) and M.history_off_peak(at(21, 6, 30))
    assert not M.history_off_peak(at(21, 3)) and not M.history_off_peak(at(21, 7)) and not M.history_off_peak(at(21, 12))
    assert not M.history_off_peak(at(21, 22, 30)), "never the Wednesday maintenance window"
    assert M.HISTORY_FLOOR_S >= 1.0, "the approval's ceiling: one request a second at most"
    assert M.FLOOR_S == 5.0, "the monitor keeps its own floor"


def test_a_withheld_name_and_the_contact_lists_are_kept_for_the_private_twin():
    """Ruling 142: the name the register withholds and the e-mail and phone lists were left unread; now each is a
    private line, and the entity row still carries no name."""
    r, _ = _read(_answer(privacySettings={"namePrivateInformation": True}, websites=[{"url": "https://x.invalid"}]))
    assert r.entity["name"] is None
    assert sorted(k for _p, k, _v in r.withheld) == ["emailAddresses", "name withheld", "phoneNumbers", "websites"]
    assert ("entityName", "name withheld", "Example Limited") in r.withheld
