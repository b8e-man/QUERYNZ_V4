"""The reading's rules on answers shaped like the interface's (every name
invented), a mutant check of those rules, the capture's politeness on a
fake transport, and the filled sample (real answers, sample.list) against
the row contract, the ledger, the address rule and the views. No model is
called and nothing is fetched."""
import datetime as dt
import json
import os
import types

import pytest

from support import db, rowcontract, sample
from registers.limited_partnerships import capture, check, load, read
from registers.limited_partnerships import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = "c" * 64
DAY = dt.date(2026, 10, 21)
SAMPLE_SCHEMA = "scratch_test_limited_partnerships"


def _addr(kind, end=None, start="2020-01-01T00:00:00.000+1300", line="1 Invented Street"):
    return {"uniqueIdentifier": None, "startDate": start, "endDate": end, "careOf": None, "address1": line,
            "address2": "Exampletown", "address3": None, "address4": None, "postCode": "9999", "countryCode": "NZ",
            "addressType": kind, "pafId": None}


def _role(kind="Partner", status="Active", person=None, body=None, uid="r1", addrs=("POSTAL",)):
    return {"roleType": kind, "roleStatus": status, "startDate": None, "endDate": None, "uniqueIdentifier": uid,
            "rolePerson": person, "roleEntity": body, "roleAddress": [_addr(a) for a in addrs]}


def _answer(code="Y", roles=None, withheld=False, **kw):
    j = {"nzbn": "9429000000017", "entityName": "Invented Fund LP", "entityTypeCode": code,
         "entityTypeDescription": "Limited Partnership (NZ)", "entityStatusCode": "50",
         "entityStatusDescription": "Registered", "registrationDate": "2019-05-02T00:00:00.000+1200",
         "sourceRegisterUniqueIdentifier": "2000001",
         "addresses": {"addressList": [_addr("REGISTERED", start="2021-01-02T00:00:00.000+1300", line="2 New Road"),
                                       _addr("REGISTERED", start="2022-03-01T00:00:00.000+1300",
                                             end="2023-01-01T00:00:00.000+1300", line="9 Ended Road"),
                                       _addr("POSTAL")]},
         "privacySettings": {"namePrivateInformation": True if withheld else None, "partnersPrivateInformation": None},
         "non-company-details": {"countryOfOrigin": "NZ"},
         "roles": roles if roles is not None else [
             _role(body={"entityName": "Invented GP Limited", "nzbn": "9429000000024"}, uid="g1"),
             _role(person={"firstName": "Ana", "middleNames": None, "lastName": "Example"}, status="Inactive", uid="g2"),
             _role(kind="Person Authorised For Service", body={"entityName": "Agent Ltd", "nzbn": None}, uid="a1")]}
    j.update(kw)
    return json.dumps(j).encode()


def _read(body, mod=read):
    return mod.read_answer(body, SHA, DAY, 1)


# ── the rules, as assertions a mutant must break ──────────────────────────────

def rules(mod) -> list:
    """Every rule of the reading, on invented answers; the names of those that do not hold."""
    broken = []
    out = _read(_answer(), mod)
    p = out["partnership"]
    if not (p and p["registered_office"] and p["registered_office"].startswith("2 New Road") and p["office_since"] == dt.date(2021, 1, 2)):
        broken.append("the current registered office, not an ended one")
    if [g["kind"] for g in out["partners"]] != ["body", "person"] or out["other_roles"] != 1 or out["roles"] != 3:
        broken.append("only Partner roles are general partners; the others are counted")
    if [g["current"] for g in out["partners"]] != [True, False]:
        broken.append("Active is current, Inactive is past")
    if any(g["started_on"] or g["ended_on"] or g["dates_stated"] for g in out["partners"]):
        broken.append("no date is made up where the answer states none")
    if not out["addresses"] or any(k in g for g in out["partners"] for k in ("address", "addresses")):
        broken.append("a partner's addresses go to the private twin only")
    if p and any("address" in k and k != "registered_office" for k in p):
        broken.append("the partnership row carries no address but the registered office")
    w = _read(_answer(withheld=True), mod)["partnership"]
    if not (w and w["name"] is None and w["name_withheld"]):
        broken.append("a name the register withholds is not read")
    sup = _read(_answer(privacySettings={"partnersPrivateInformation": True}), mod)["partners"]
    if not sup or not all(g["suppressed"] for g in sup):
        broken.append("partners the register withholds are suppressed")
    two = _read(_answer(roles=[_role(body={"entityName": "First GP Ltd", "nzbn": None}, uid="same"),
                               _role(body={"entityName": "Second GP Ltd", "nzbn": None}, uid="same")]), mod)
    if len({g["key"] for g in two["partners"]}) != 2:
        broken.append("two partners under one identifier are two rows")
    rep = _read(_answer(roles=[_role(body={"entityName": "First GP Ltd", "nzbn": None}, uid="same")] * 2), mod)
    if len(rep["partners"]) != 1 or len(rep["set_aside"]) != 1:
        broken.append("the same partner twice is set aside once")
    noname = _read(_answer(roles=[_role(person={"firstName": None, "lastName": None})]), mod)
    if noname["partners"] or len(noname["set_aside"]) != 1:
        broken.append("a partner with no name is set aside")
    company = _read(_answer(code="LTD"), mod)
    if company["partnership"] is not None or len(company["set_aside"]) != 1:
        broken.append("an answer that is not a limited partnership is set aside whole")
    if _read(_answer(), mod)["partners"][0]["key"] != out["partners"][0]["key"]:
        broken.append("keys are stable across reads")
    return broken


def test_every_rule_holds():
    assert rules(read) == []


MUTANTS = {
    "an ended registered office": ('if a.get("addressType") == "REGISTERED" and not a.get("endDate")',
                                   'if a.get("addressType") == "REGISTERED"'),
    "every role a partner": ('if (r or {}).get("roleType") != PARTNER_ROLE:', 'if False:'),
    "Inactive read as current": ('"current": r.get("roleStatus") == "Active"', '"current": True'),
    "the ask day as a start date": ('started, ended = day(r.get("startDate")), day(r.get("endDate"))',
                                    'started, ended = day(r.get("startDate")) or asked_on, day(r.get("endDate"))'),
    "the withheld name read": ('"name": None if withheld else', '"name":'),
    "partner suppression dropped": ('or partners_private)', 'or False)'),
    "keyed by the identifier alone": ("key = f\"{pkey}/partner/{rid or '-'}/{short(kind + '|' + full.lower() + '|' + (body_nzbn or ''))}\"",
                                      "key = f\"{pkey}/partner/{rid or short(full)}\""),
    "no-name partners kept": ('if not full:', 'if False:'),
    "any entity type read": ('if j.get("entityTypeCode") not in KINDS:', 'if j.get("entityTypeCode") is None:'),
}


def _mutant(old, new):
    src = open(read.__file__, encoding="utf-8").read()
    assert src.count(old) == 1, f"the mutant's anchor is not in read.py once: {old}"
    mod = types.ModuleType("read_mutant")
    mod.__file__ = read.__file__
    exec(compile(src.replace(old, new), read.__file__, "exec"), mod.__dict__)
    return mod


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_is_caught(name):
    old, new = MUTANTS[name]
    try:
        broken = rules(_mutant(old, new))
    except (KeyError, TypeError, AttributeError):
        broken = ["crashed"]
    assert broken, f"the mutant '{name}' passes every rule: a rule is missing"


# ── the capture's politeness, on a fake transport ─────────────────────────────

class FakeTables:
    def __init__(self):
        self.asks, self.asides, self.finished = [], [], None

    def last_asked(self):
        return {}

    def begin(self, n, note):
        return 1

    def ask(self, *a):
        self.asks.append(a)

    def set_aside(self, pid, item, stage, why):
        self.asides.append((item, stage, why))

    def finish(self, pid, counts, stopped):
        self.finished = (counts, stopped)


def _fetched(status, body=b"{}", blocked=""):
    return types.SimpleNamespace(status=status, body=body, final_url="", blocked=blocked)


def _run(answers, n=5):
    t, clock, slept = FakeTables(), [0.0], []
    it = iter(answers)

    def opener(url, timeout):
        clock[0] += 0.2
        a = next(it)
        if isinstance(a, Exception):
            raise a
        return a

    def land(data, **kw):
        return types.SimpleNamespace(sha256="d" * 64), True

    run = capture.Run(t, [f"94290000000{i:02d}" for i in range(n)], land_fn=land, opener=opener,
                      clock=lambda: clock[0], sleep=lambda s: (slept.append(s), clock.__setitem__(0, clock[0] + s)),
                      now=lambda: dt.datetime(2026, 10, 22, 21, 10, tzinfo=capture.NZ), max_asks=n)
    return run.run(), t, slept


def test_a_block_stops_the_night_and_a_404_does_not():
    out, t, slept = _run([_fetched(200), _fetched(404), _fetched(429, blocked="HTTP 429"), _fetched(200), _fetched(200)])
    assert out["asked"] == 3 and out["answered"] == 1 and out["not_found"] == 1
    assert out["stopped"].startswith("stopped:") and t.asides[-1][2] == "HTTP 429"


def test_three_transport_failures_stop_the_night_and_calls_are_five_seconds_apart():
    out, t, slept = _run([OSError("x"), OSError("x"), OSError("x"), _fetched(200)])
    assert out["asked"] == 3 and out["stopped"].startswith("stopped:")
    assert slept and all(abs(s - 5.0) < 1e-6 for s in slept)


def test_the_window_and_the_slice():
    assert capture.in_window(dt.datetime(2026, 10, 22, 21, 30, tzinfo=capture.NZ))         # a Thursday
    assert not capture.in_window(dt.datetime(2026, 10, 21, 21, 30, tzinfo=capture.NZ))     # a Wednesday
    assert not capture.in_window(dt.datetime(2026, 10, 22, 22, 0, tzinfo=capture.NZ))
    t0 = dt.datetime(2026, 10, 1, 21, 0, tzinfo=capture.NZ)
    last = {"b": t0 + dt.timedelta(days=2), "a": t0, "d": dt.datetime(2026, 10, 22, 21, 0, tzinfo=capture.NZ)}
    assert capture.slice_for(["a", "b", "c", "d"], last, dt.date(2026, 10, 22)) == ["c", "a", "b"]
    assert capture.slice_for(["a", "b", "c", "d"], last, dt.date(2026, 10, 22), 2) == ["c", "a"]


# ── the filled sample: real answers ───────────────────────────────────────────

def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def _rows(conn, q, *a):
    cur = conn.execute(q, a)
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@pytest.fixture(scope="module")
def filled():
    _db_or_skip()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SAMPLE_SCHEMA}")
        S.fill(conn, SAMPLE_SCHEMA, items)
        views = load.sql("publish.sql", SAMPLE_SCHEMA, True).replace("pub.", f"{SAMPLE_SCHEMA}.v_")
        conn.execute(views)
        conn.commit()
        T = lambda t: load.table(SAMPLE_SCHEMA, t, True)
        yield {"conn": conn, "items": items, **{t: _rows(conn, f"SELECT * FROM {T(t)}") for t in load.TABLES + load.PRIVATE_TABLES},
               "v_partners": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_limited_partnership_partners"),
               "v_partnerships": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_limited_partnerships")}


def test_every_listed_answer_is_a_partnership(filled):
    shas = {i for i in filled["items"] if not i.startswith("key:")}
    assert {p["document"] for p in filled["partnerships"]} == shas
    assert all(not a["superseded"] and a["recognised"] for a in filled["read_answers"])


def test_every_row_meets_the_row_contract(filled):
    for t in ("partnerships", "partners"):
        for r in filled[t]:
            assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], (t, r["key"])


def test_the_ledger_reconciles_and_the_hard_cases_read_as_their_comments_say(filled):
    assert all(a["roles"] == a["partners"] + a["other_roles"] + a["set_aside"] for a in filled["read_answers"])
    by = {p["nzbn"]: p for p in filled["partnerships"]}
    assert by["9429043245406"]["kind"] == "overseas" and by["9429053854551"]["kind"] == "nz"
    gp = [g for g in filled["partners"] if g["nzbn"] == "9429043245406"]
    assert sorted((g["kind"], g["current"]) for g in gp) == [("person", False), ("person", True)]
    two = [g for g in filled["partners"] if g["nzbn"] == "9429043218851"]
    assert len(two) == 2 and len({g["role_id"] for g in two}) == 1 and len({g["key"] for g in two}) == 2
    assert all(p["registered_office"] for p in filled["partnerships"])
    assert not any(g["dates_stated"] for g in filled["partners"])          # the interface states none: none made up
    assert len(filled["partners"]) == 18 and len(filled["partnerships"]) == 15


def test_no_view_carries_a_partner_address_or_a_withheld_name(filled):
    assert filled["addresses"], "the partners' addresses are held privately"
    for v in ("v_partners", "v_partnerships"):
        cols = set(filled[v][0])
        assert not {c for c in cols if any(w in c for w in check.ADDRESSISH)} - {"registered_office"}
    private = {a["address"] for a in filled["addresses"]}
    for g in filled["v_partners"]:
        assert not any(str(v) in private for v in g.values() if v)
    assert all(g["full_name"] == "name withheld by the register" for g in filled["v_partners"] if g["suppressed"])


def test_the_reading_check_is_green_and_goes_red_on_a_broken_ledger(filled):
    conn = filled["conn"]
    T = load.table(SAMPLE_SCHEMA, "read_answers", True)
    one = f"(SELECT min(document) FROM {T})"
    assert check.reading(conn, SAMPLE_SCHEMA, shared=True) == []
    conn.execute(f"UPDATE {T} SET partners = partners + 1 WHERE document = {one}")
    try:
        assert check.reading(conn, SAMPLE_SCHEMA, shared=True) != []
    finally:
        conn.execute(f"UPDATE {T} SET partners = partners - 1 WHERE document = {one}")
        conn.commit()
    assert check.reading(conn, SAMPLE_SCHEMA, shared=True) == []
