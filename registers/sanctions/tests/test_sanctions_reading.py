"""The three readings' rules on hand-made documents (every name invented),
a mutant check of those rules, the authorisation of each list (ruling 132),
the capture's politeness (weekly by the record, nothing fetched twice, a block
a failed read of one list), a load into the sample database from hand-made
documents and the check over it, and, marked slow, the real lists as landed,
read from the document store by the hashes sample.list names. No model is
called and nothing is fetched."""
import collections
import datetime as dt
import os
import types

import pytest

from support import db, rowcontract
from registers.sanctions import capture, check, load, read
from registers.sanctions.tests import fixture as F

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_SCHEMA = "scratch_test_sanctions"
A, B, C = "a" * 64, "b" * 64, "c" * 64


def rules(mod) -> list:
    broken = []
    un = mod.read_document("un-sc", F.UN_XML, A, 1)
    by = {r["list_ref"]: r for r in un["rows"]}
    p = by.get("KPi.901")
    if un["items"] != 3 or len(un["rows"]) != 2 or len(un["set_aside"]) != 1:
        broken.append("un: every element a listing or a catch-log line")
    if not p or p["name"] != "INVENTED PERSON" or p["aliases"] != ["Invented Persson"] or p["kind"] != "individual":
        broken.append("un: names as published, aliases once")
    if p and (p["countries"] != ["Exampleland"] or p["birth_countries"] != ["Otherland"]):
        broken.append("un: a country and nothing finer")
    flat = repr(un["rows"])
    if any(s in flat for s in ("Secret Road", "Exampleville", "X1234567", "Birthtown", "Company Lane", "Port Example")):
        broken.append("un: no street, city or document number is read")
    if p and (p["birth_dates"] != ["1960-02-03", "1958-1961"] or p["designated_on"] != dt.date(2016, 3, 2)
              or p["updated_on"] != dt.date(2020, 5, 6) or p["positions"] != ["Minister of Examples"]):
        broken.append("un: birth dates, designation and update as listed")
    if p and (p["key"] != "sanctions/un-sc/KPi.901" or p["list_version"] != "2026-10-20T23:00:05.952Z" or p["regime"] != "DPRK"):
        broken.append("un: keyed by the list's own reference, versioned by dateGenerated")
    if by.get("IRe.901", {}).get("kind") != "entity":
        broken.append("un: entities are entities")
    po = mod.read_document("nz-police-tsa", F.police_xlsx(), B, 1, "2026-10-02", F.PAGE_1373)
    pk = {r["key"].split("nz-police-tsa/")[1]: r for r in po["rows"]}
    if po["items"] != len(po["rows"]) + len(po["set_aside"]) + po["skipped"]:
        broken.append("police: items reconcile")
    i2 = pk.get("individual/2")
    if not i2 or i2["aliases"] != ["Invented EXAMPEL"] or i2["other_ref"] != "TAi.902" or i2["designated_on"] != dt.date(2002, 10, 17):
        broken.append("police: an integer ID is a listing and its decimals its aliases")
    if i2 and (i2["updated_on"] != dt.date(2026, 3, 10) or "1972" not in "".join(i2["birth_dates"]) or i2["regime"].startswith("UN-listed")):
        broken.append("police: dates from serials and text; the regime from the UN prefix")
    if "individual/3" not in pk:
        broken.append("police: an ID written '3. 00' is an ID")
    if "Example Street" in repr(po["rows"]) or "P0000001" in repr(po["rows"]):
        broken.append("police: addresses and passports are not read")
    if not any(a["reason"] == "no name" for a in po["set_aside"]):
        broken.append("police: a row with no name is set aside")
    f = pk.get("1373/1")
    if not f or f["aliases"] != ["Front of Invention", "IF"] or f["renewed_on"] != [dt.date(2013, 2, 11), dt.date(2016, 2, 2)] or f["expires_on"] is None:
        broken.append("police: a 1373 designation with its renewals and expiry")
    t = pk.get("1373/23")
    if not t or t["kind"] != "individual" or t["name"] != "Imaginary Person Name" or t["birth_dates"] != ["27 October 1990"]:
        broken.append("police: 'NAME, DOB day' in a 1373 row is an individual")
    if pk.get("1373/18", {}).get("status") != "expired" or pk.get("individual/123", {}).get("status") != "revoked" \
            or pk.get("entity/1", {}).get("status") != "revoked" or pk.get("entity/1", {}).get("ended_on") is None:
        broken.append("police: expirations and both sections of revocations, with their end dates")
    if po["stated"] != 2:
        broken.append("police: the 1373 page's stated count is read")
    dup = mod.read_document("nz-police-tsa", F.police_xlsx(expired_dup=True), B, 1, "2026-10-02", F.PAGE_1373)
    if not any("listed twice" in a["reason"] for a in dup["set_aside"]):
        broken.append("police: an identifier listed twice is set aside")
    mf = mod.read_document("mfat-russia", F.mfat_xlsx(), C, 1, "2026-09-09")
    mk = {r["list_ref"]: r for r in mf["rows"]}
    if mf["stated"] != 3 or len(mf["rows"]) != 3 or len(mf["set_aside"]) != 1 or mf["skipped"] != 2:
        broken.append("mfat: listings, the Total row's figure, an Asset counted, an unknown Type set aside")
    iv = mk.get("RUS-0001")
    if not iv or iv["name"] != "Ivan Inventovich Examplov" or iv["aliases"] != ["Ivan Examplof", "I. Examplov"]:
        broken.append("mfat: names and aliases as published")
    if iv and (iv["designated_on"] != dt.date(2022, 3, 3) or iv["birth_dates"] != ["1960-03-25"] or iv["regime"] != "Asset Freeze, Travel Ban"):
        broken.append("mfat: dates and sanction types")
    if "Hidden Street" in repr(mf["rows"]) or "000000" in repr([r["aliases"] for r in mf["rows"]]):
        broken.append("mfat: no address or passport")
    if len([r for r in mf["rows"] if r["list_ref"].startswith("RUS-0002")]) != 2 or len({r["key"] for r in mf["rows"]}) != len(mf["rows"]):
        broken.append("mfat: a repeated identifier keeps both listings, keyed apart")
    bad = mod.read_document("mfat-russia", F.xlsx([("x", {1: {1: "nothing"}})]), C, 1)
    if bad["rows"] or len(bad["set_aside"]) != 1:
        broken.append("mfat: a workbook without the profile's header is set aside whole")
    return broken


def test_every_rule_holds():
    assert rules(read) == []


MUTANTS = {
    "un: city read with the country": ('countries=once(a.findtext("COUNTRY") for a in e.findall(f"{tag}_ADDRESS"))',
                                       'countries=once((a.findtext("CITY") or "") + " " + (a.findtext("COUNTRY") or "") for a in e.findall(f"{tag}_ADDRESS"))'),
    "un: no reference kept": ('            if not ref:\n                out["set_aside"].append(aside("un-sc", sha, place, "key", "no REFERENCE_NUMBER"))\n                continue\n',
                              '            ref = ref or "none"\n'),
    "un: aliases not deduplicated": ('row["aliases"] = [a for a in once(row["aliases"]) if a != name]',
                                     'row["aliases"] = [text(a) for a in row["aliases"] if text(a)]'),
    "police: aliases as listings": ("return base, int(((d - base) * 100).quantize(Decimal(1)))", "return s, 0"),
    "police: the ID with a space dropped": ('s = re.sub(r"\\s+", "", str(v or ""))', 's = str(v or "").strip()'),
    "police: the address read": ("nationalities=once(c.get(k) for k in (27, 28, 29))", "nationalities=once(c.get(k) for k in (27, 28, 29, 44))"),
    "police: 1373 individual missed": ('m = re.match(r"^(?P<name>.+?),\\s*DOB\\s+(?P<dob>.+)$", nm)', "m = None"),
    "police: revocations as current": ('add(listing("nz-police-tsa", f"{kind}/{base}", kind, "revoked"',
                                       'add(listing("nz-police-tsa", f"{kind}/{base}", kind, "designated"'),
    "police: twice listed kept": ('        if row["key"] in seen:\n', '        if False:\n'),
    "mfat: the Total row as a listing": ('MFAT_COUNTED = ("asset", "total")', 'MFAT_COUNTED = ("asset",)'),
    "mfat: unknown types read as entities": ("kind = MFAT_KINDS.get(typ)", 'kind = MFAT_KINDS.get(typ, "entity")'),
    "mfat: a repeated identifier overwritten": ('ref = uid if seen[uid] == 1 else', 'ref = uid if True else'),
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
    try:
        broken = rules(_mutant(*MUTANTS[name]))
    except (KeyError, TypeError, AttributeError, ValueError):
        broken = ["crashed"]
    assert broken, f"the mutant '{name}' passes every rule"


# ── the hold ──────────────────────────────────────────────────────────────────

class FakeTables:
    def __init__(self, last=None, held=None, versions=()):
        self.landed_rows, self.asides = [], []
        self.last, self._held, self._versions = last, held or {}, set(versions)

    def landed(self, *a):
        self.landed_rows.append(a)

    def set_aside(self, *a):
        self.asides.append(a)

    def last_asked(self, list_id):
        return self.last

    def held(self, list_id):
        return self._held

    def versions(self, list_id, role="list"):
        return self._versions


NOW = dt.datetime(2026, 11, 2, 23, 0, tzinfo=capture.NZ)


def _ok(body):
    return types.SimpleNamespace(status=200, body=body, final_url="", blocked="")


def _run(t, opener, lists, **kw):
    return capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="d" * 64), True), lists=lists,
                       opener=opener, authorised=lambda l: "2026-11-02 ruling 132", anytime=True,
                       sleep=lambda s: None, now=lambda: NOW, log=lambda m: None, **kw).run()


def test_a_held_list_asks_nothing_and_an_authorised_one_is_fetched():
    asked = []

    def opener(url, timeout):
        asked.append(url)
        return types.SimpleNamespace(status=200, body=F.UN_XML, final_url=url, blocked="")

    land = lambda d, **k: (types.SimpleNamespace(sha256="d" * 64), True)
    t = FakeTables()
    out = capture.Run(t, land_fn=land, opener=opener, authorised=lambda l: None, anytime=True).run()
    assert asked == [] and out["held"] == 3 and t.landed_rows == []
    t = FakeTables()
    out = capture.Run(t, land_fn=land, lists=("un-sc",), opener=opener, authorised=lambda l: "2026-11-01 ruling",
                      anytime=True, sleep=lambda s: None).run()
    assert asked[-1] == capture.UN_XML and t.landed_rows[-1][4] == "2026-10-20T23:00:05.952Z"


def test_the_real_position_authorises_all_three_by_ruling_132():
    import support.fetchgate as fg
    assert os.path.exists(os.path.join(fg.POSITIONS_DIR, "sanctions-lists.md"))
    for l in capture.LISTS:
        got = capture.authorisation(l, fg.POSITIONS_DIR)
        assert got and "ruling 132" in got, l
    assert capture.authorisation("un-sc", os.path.join(LANE, "no-such-folder")) is None


def test_a_block_on_one_list_is_a_failed_read_and_the_next_list_is_asked():
    asked = []

    def opener(url, timeout):
        asked.append(url)
        if "mfat.govt.nz" in url:
            return types.SimpleNamespace(status=403, body=b"Incapsula incident", final_url=url, blocked="challenge: incapsula")
        return _ok(F.UN_XML)

    t = FakeTables()
    out = _run(t, opener, ("mfat-russia", "un-sc"))
    # MFAT: its first request is walled; nothing more is asked of it; the UN is asked and landed
    assert [u for u in asked if "mfat" in u] == [capture.DOCS["mfat-russia"]["terms-of-use"]]
    assert asked[-1] == capture.UN_XML and t.landed_rows[-1][0] == "un-sc"
    assert out["failed"] == {"mfat-russia": "challenge: incapsula"} and out["stopped"].startswith("stopped:")
    assert any(a[0] == "mfat-russia" and a[2] == "fetch" for a in t.asides)


def test_a_wall_page_in_place_of_the_workbook_is_a_failed_read():
    def opener(url, timeout):
        return _ok(b"<html>please wait</html>" if url == capture.MFAT_FILE else b"<p>Updated 9 September 2026</p>")

    t = FakeTables(held={"terms-of-use": {capture.DOCS["mfat-russia"]["terms-of-use"]: None},
                         "copyright": {capture.DOCS["mfat-russia"]["copyright"]: None}})
    out = _run(t, opener, ("mfat-russia",))
    assert "mfat-russia" in out["failed"] and not any(r[1] == "list" for r in t.landed_rows)


def test_the_cadence_is_weekly_by_the_record():
    asked = []
    opener = lambda url, timeout: asked.append(url) or _ok(F.UN_XML)
    out = _run(FakeTables(last=NOW - dt.timedelta(days=3)), opener, ("un-sc",))
    assert asked == [] and out["not_due"] == 1
    out = _run(FakeTables(last=NOW - dt.timedelta(days=3)), opener, ("un-sc",), due_now=True)
    assert asked and out["not_due"] == 0
    asked.clear()
    out = _run(FakeTables(last=NOW - dt.timedelta(days=7)), opener, ("un-sc",))
    assert asked[-1] == capture.UN_XML and out["landed"] >= 1


def test_nothing_is_fetched_twice():
    asked = []
    wb = "https://www.police.govt.nz/sites/default/files/publications/designated-entities-2-october-2026.xlsx"
    page = b'<a href="/sites/default/files/publications/designated-entities-2-october-2026.xlsx">x</a>'
    opener = lambda url, timeout: asked.append(url) or _ok(page if "1267" in url else b"<p>Updated 9 September 2026</p>")
    copyright_url = capture.DOCS["nz-police-tsa"]["copyright"]
    out = _run(FakeTables(held={"list": {wb: "2026-10-02"}, "copyright": {copyright_url: None}}), opener,
               ("nz-police-tsa",))
    assert wb not in asked and copyright_url not in asked and out["unchanged"] == 1
    asked.clear()
    mfat_terms = {r: {u: None} for r, u in capture.DOCS["mfat-russia"].items()}
    out = _run(FakeTables(held=mfat_terms, versions={"2026-09-09"}), opener, ("mfat-russia",))
    assert asked == [capture.MFAT_PAGE] and out["unchanged"] == 1


def test_the_un_xml_is_asked_with_one_redirect_hop_and_nothing_else_is(monkeypatch):
    seen = []
    import support.fetchgate as fg
    monkeypatch.setattr(fg, "open_url", lambda url, **k: seen.append((url, k.get("follow"))) or _ok(F.UN_XML))
    r = capture.Run(FakeTables(), land_fn=lambda d, **k: (types.SimpleNamespace(sha256="d" * 64), True))
    r.opener(capture.UN_XML, 10)
    r.opener(capture.POLICE_UN_PAGE, 10)
    assert seen == [(capture.UN_XML, 1), (capture.POLICE_UN_PAGE, 0)]


def test_the_mfat_page_names_its_day():
    assert capture.mfat_day(b"<h2>Russia Sanctions Register</h2><p>Last updated: <b>9 September 2026</b></p>") == "2026-09-09"
    assert capture.mfat_day(b"<p>No date here 2026</p>") is None


def test_only_mfat_comes_by_hand_and_only_as_a_workbook(tmp_path):
    p = tmp_path / "x.xlsx"
    p.write_bytes(F.mfat_xlsx())
    t, land = FakeTables(), (lambda d, **k: (types.SimpleNamespace(sha256="e" * 64), True))
    with pytest.raises(capture.Held):
        capture.by_hand(t, land, "un-sc", str(p), "2026-10-20", "arthur")
    with pytest.raises(ValueError):
        capture.by_hand(t, land, "mfat-russia", str(p), "9 September", "arthur")
    capture.by_hand(t, land, "mfat-russia", str(p), "2026-09-09", "arthur")
    assert t.landed_rows[-1][0] == "mfat-russia" and "by hand" in t.landed_rows[-1][6]


def test_the_police_workbook_link_and_its_day():
    page = b'<a href="/sites/default/files/publications/designated-entities-2-october-2026.xlsx">x</a>'
    assert capture.police_workbook(page) == (
        "https://www.police.govt.nz/sites/default/files/publications/designated-entities-2-october-2026.xlsx", "2026-10-02")


# ── a load from hand-made documents, the views and the check ──────────────────

def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


@pytest.fixture(scope="module")
def built():
    _db_or_skip()
    docs = {A: F.UN_XML, B: F.police_xlsx(), C: F.mfat_xlsx(), "9" * 64: F.PAGE_1373}
    listed = {"un-sc": {"list": (A, "2026-10-20")}, "nz-police-tsa": {"list": (B, "2026-10-02"), "page-1373": "9" * 64},
              "mfat-russia": {"list": (C, "2026-09-09")}}
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SAMPLE_SCHEMA}")
        counts = load.build(conn, SAMPLE_SCHEMA, listed, read_bytes=docs.__getitem__, shared=True,
                            versions={l: 1 for l in capture.LISTS})
        conn.execute(load.sql("publish.sql", SAMPLE_SCHEMA, True).replace("pub.", f"{SAMPLE_SCHEMA}.v_"))
        conn.commit()
        yield conn, counts


def test_the_load_reconciles_and_every_row_meets_the_contract(built):
    conn, counts = built
    assert counts["lists"] == 3 and counts["listings"] > 0
    cur = conn.execute(f"SELECT * FROM {load.table(SAMPLE_SCHEMA, 'listings', True)}")
    cols = [d.name for d in cur.description]
    for r in cur.fetchall():
        row = dict(zip(cols, r))
        assert rowcontract.validate({**row, "loaded_at": row["loaded_at"].isoformat()}) == [], row["key"]
    assert check.reading(conn, SAMPLE_SCHEMA, shared=True) == []
    assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") == []


def test_the_check_reads_each_list_against_its_own_figure(built):
    conn, _ = built
    out = check.outside(conn, SAMPLE_SCHEMA, today=dt.date(2026, 10, 22), shared=True)
    assert out["lists"]["mfat-russia"]["ok"] and out["lists"]["un-sc"]["ok"]
    # the hand-made 1373 sheet holds 2 current designations and its page says 2; one more on the page is red
    assert out["lists"]["nz-police-tsa"]["ok"] and out["lists"]["nz-police-tsa"]["current_1373"] == 2
    t = load.table(SAMPLE_SCHEMA, "lists", True)
    conn.execute(f"UPDATE {t} SET stated = stated + 1 WHERE list_id = 'nz-police-tsa'")
    try:
        assert not check.outside(conn, SAMPLE_SCHEMA, today=dt.date(2026, 10, 22), shared=True)["lists"]["nz-police-tsa"]["ok"]
    finally:
        conn.rollback()
    assert not check.outside(conn, SAMPLE_SCHEMA, today=dt.date(2026, 12, 1), shared=True)["lists"]["un-sc"]["ok"]


# ── the real lists, as landed (ruling 132): the documents sample.list names, from the store (slow) ─────────

def _real():
    from registers.sanctions import sample
    from support.docstore.landing import read_bytes
    with open(os.path.join(LANE, "sample.list"), encoding="utf-8") as f:
        items = [l.strip() for l in f if l.startswith("key: ")]
    try:
        docs = sample.docs_of(items)
    except LookupError as exc:
        pytest.skip(str(exc))
    return docs, read_bytes


@pytest.mark.slow
@pytest.mark.parametrize("list_id", capture.LISTS)
def test_the_real_list_as_landed_reconciles(list_id):
    docs, read_bytes = _real()
    if list_id not in docs:
        pytest.skip(f"{list_id}: no document landed (sample.list names none: a failed read)")
    sha, version = docs[list_id]["list"]
    extra = read_bytes(docs[list_id]["page-1373"]) if docs[list_id].get("page-1373") else None
    out = read.read_document(list_id, read_bytes(sha), sha, read.profile_version(list_id), version, extra)
    items_aside = [a for a in out["set_aside"] if a["place"] != "document"]
    assert out["items"] == len(out["rows"]) + len(items_aside) + out["skipped"]
    assert len({r["key"] for r in out["rows"]}) == len(out["rows"])
    floor = {"un-sc": 900, "nz-police-tsa": 400, "mfat-russia": 500}[list_id]
    assert collections.Counter(r["status"] for r in out["rows"])["designated"] > floor
    flat = repr(out["rows"]).lower()
    assert "passport" not in flat
    if list_id == "nz-police-tsa":
        cur = sum(1 for r in out["rows"] if r["key"].startswith("sanctions/nz-police-tsa/1373/") and r["status"] == "designated")
        assert out["stated"] is not None and cur > 0
