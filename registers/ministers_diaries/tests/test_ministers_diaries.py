"""registers/ministers_diaries: the reading of the MCP's parliament-diaries
records, on records made in the recorded shape (no database), then on the
filled sample (real documents named by hash in sample.list): every row keeps
the row contract, the release's withholdings are kept and counted, a
location is shown only as a place of business, the provider's text stays
private, and each published row cites its document and the PDF."""
import datetime as dt
import hashlib
import os

import pytest

from support import db, lane, rowcontract, sample
from support import mcpsource as M
from support.mcpsource.tests.fake import made_record
from registers.ministers_diaries import check, read

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(LANE))
PDF = "https://www.beehive.govt.nz/sites/default/files/2025-04/Hon%20Minister%20A%20-%20March%202025.pdf"


def _rec(n, **kw):
    r = made_record("parliament-diaries", n, M.shapes()["parliament-diaries"])
    r.update({"id": str(n), "rowid": n, "minister": "Hon Minister A", "portfolio": "Transport", "date": "2025-03-04",
              "year": "2025", "time": "9:00 AM - 9:30 AM", "meeting": "Meeting with an association",
              "location": "Parliament Buildings", "attendees": "Chief Executive, an association", "source_url": PDF})
    r["capture"] = {"_collected": "2026-10-17T06:35:49Z", "source_url": PDF}
    r.update(kw)
    r["text"] = " | ".join(str(r[f]) for f in ("date", "time", "minister", "portfolio", "meeting", "location", "attendees"))
    return r


def _docs(*recs):
    return {hashlib.sha256(M.record_bytes(r)).hexdigest(): M.record_bytes(r) for r in recs}


def _read(*recs):
    store = _docs(*recs)
    return read.read([(s, i, None) for i, s in enumerate(store)], store.__getitem__,
                     loaded_at="2026-10-27T09:00:00+13:00")


def test_the_lane_folder_has_every_piece():
    assert lane.check_folder(LANE) == []


def test_an_entry_is_read_as_released_and_its_release_counted():
    res = _read(_rec(1), _rec(2, date="2025-03-05"))
    assert res.counts["entries"] == 2 and res.counts["releases"] == 1 and not res.set_aside
    e = res.entries[0]
    assert (e["minister"], e["portfolio"], e["entry_on"], e["time"], e["location"]) == \
        ("Hon Minister A", "Transport", "2025-03-04", "9:00 AM - 9:30 AM", "Parliament Buildings")
    assert e["fields_unread"] == [] and e["withheld"] == [] and "text" not in e
    r = res.releases[0]
    assert (r["entries"], r["minister"], r["ministers_named"], r["pdf_url"], r["upload_folder"], r["month_named"],
            r["entries_month"], r["month"], r["first_on"], r["last_on"]) == \
        (2, "Hon Minister A", 1, PDF, "2025-04", "2025-03", "2025-03", "2025-03", "2025-03-04", "2025-03-05")
    assert r["file_name"] == "Hon Minister A - March 2025.pdf"
    for row in res.entries + res.releases:
        assert rowcontract.validate(row) == [], row["key"]


def test_a_file_name_only_release_gets_no_address_and_a_span_names_no_month():
    res = _read(_rec(1, source_url="Hon Minister B - May 2026.pdf"),
                _rec(2, source_url="26 October 2017 - 31 December 2018.pdf", date="2018-01-02"))
    by = {r["key"]: r for r in res.releases}
    assert by["Hon Minister B - May 2026.pdf"]["pdf_url"] is None
    assert by["Hon Minister B - May 2026.pdf"]["month_named"] == "2026-05"
    span = by["26 October 2017 - 31 December 2018.pdf"]
    assert span["month_named"] is None and span["month"] == "2018-01"       # the entries' one month, not the name's first


def test_the_releases_withholdings_are_kept_as_released_and_counted():
    res = _read(_rec(1, meeting="Withheld under section 9(2)(f)(iv) of the Official Information Act",
                     attendees="Withheld under s.6 (a)", location="Withheld under OIA", time="Withheld under OIA"),
                _rec(2, portfolio="9(2)(f)(iv)"), _rec(3, meeting="Meet: Revenue Private Secretaries"))
    by = {e["key"]: e for e in res.entries}
    assert by["1"]["withheld"] == ["time", "meeting", "location", "attendees"]
    assert by["1"]["meeting"].startswith("Withheld under section 9(2)") and by["1"]["location"] == "Withheld under OIA"
    assert by["2"]["withheld"] == ["portfolio"] and by["3"]["withheld"] == []      # "Private Secretaries" is a role
    assert res.counts["withheld fields"] == 5 and res.releases[0]["withheld_entries"] == 2


@pytest.mark.parametrize("location,shown,why", [
    ("Parliament Buildings", "Parliament Buildings", None),
    ("Auckland", "Auckland", None),
    ("Ambassador's Residence, Wellington", None, read.HELD_HOME),
    ("At home", None, read.HELD_HOME),
    ("12 Example Street, Suburb, Town", None, read.HELD_STREET),
    ("Example Council, 12 Example Street, Town", "Example Council, 12 Example Street, Town", None),
    ("Level 3, 99 The Terrace, Wellington", "Level 3, 99 The Terrace, Wellington", None),
    ("Withheld in accordance with s9(2)(a)", "Withheld in accordance with s9(2)(a)", None),
    ("", None, None),
])
def test_a_location_is_shown_only_as_a_place_of_business(location, shown, why):
    assert read.place_of_business(location) == (shown, why)


def test_a_held_location_and_a_masked_address_go_to_the_private_table_only():
    res = _read(_rec(1, location="12 Example Street, Suburb"),
                _rec(2, attendees="A Person, 12 Example Road, Town; Chief Executive"))
    by = {e["key"]: e for e in res.entries}
    assert by["1"]["location"] is None and by["1"]["location_held"] == read.HELD_STREET
    assert by["2"]["attendees"] == f"A Person, {read.MASK}, Town; Chief Executive" and by["2"]["addresses_masked"] == 1
    priv = {p[0]: p for p in res.private}
    assert priv["1"][1] == "12 Example Street, Suburb" and priv["2"][3].startswith("A Person, 12 Example Road")
    assert all(p[4] for p in res.private)                                   # the provider's text, private only
    assert res.releases[0]["locations_held"] == 1


def test_the_version_the_pull_saw_last_is_read_never_the_highest_seq():
    old = _rec(4)
    new = {**old, "text": old["text"] + " "}                                # the provider re-read the text in place
    store = _docs(old, new)
    s_old, s_new = list(store)
    res = read.read([(s_old, 9, "4"), (s_new, 4, "4")], store.__getitem__)
    assert res.entries[0]["document"] == s_new and res.entries[0]["versions"] == 2 and res.entries[0]["seq"] == 4
    back = read.read([(s_old, 9, "4"), (s_new, 4, "4"), (s_old, 9, "4")], store.__getitem__)
    assert back.entries[0]["document"] == s_old
    assert res.counts["entries"] + res.counts["older versions"] + res.counts["set aside"] == res.counts["documents"]


def test_a_record_with_no_release_is_set_aside_and_an_unknown_field_listed():
    res = _read(_rec(1), _rec(2, source_url=""), _rec(3, sentiment="warm"))
    assert [w for _, _, w in res.set_aside] == ["no source_url: no release to place it in"]
    assert {e["key"]: e["fields_unread"] for e in res.entries}["3"] == ["sentiment"]


def test_the_published_views_never_carry_the_text_the_private_table_or_an_address_column():
    sql = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read().lower()
    views = sql.split("create or replace view")[1:]
    assert len(views) == 2
    for v in views:
        assert "_private" not in v and " text," not in v and "e.text" not in v
        assert "citation_url" in v and "document" in v and "file_name" in v
        for col in rowcontract.FORBIDDEN_COLUMNS:
            assert f" {col}," not in v and f".{col}," not in v


# ── the outside check ────────────────────────────────────────────────────────

def _held(**kw):
    h = {"cursor": 1000, "arrivals": 1000, "documents": 1100, "caught": 0, "entries": 1000, "releases": 10,
         "older versions": 100, "files set aside": 0, "set aside": 0, "fields unread": 0, "words": 50000,
         "release entries": 1000, "releases miscounted": 0, "entries with no release": 0,
         "releases naming more than one minister": 0}
    h.update(kw)
    return h


def test_the_check_is_green_when_the_counts_agree_and_names_each_failure():
    o = {"records": 1000, "n_docs": 1000, "corpus_words": 50100}
    assert check.judge(_held(), o) == []
    assert any(f.startswith("taken") for f in check.judge(_held(cursor=900, arrivals=900), o))
    assert any(f.startswith("read") for f in check.judge(_held(entries=990), o))
    assert any("words" in f for f in check.judge(_held(words=40000), o))
    assert check.judge(_held(**{"release entries": 999}), o) == \
        ["releases: the releases count 999 entries, the entries are 1000"]
    assert check.judge(_held(**{"releases miscounted": 2}), o) == ["releases: 2 releases miscounted"]
    assert check.judge(_held(**{"releases naming more than one minister": 1}), o) == \
        ["releases: 1 releases naming more than one minister"]
    assert check.judge(_held(caught=1, arrivals=999), o) == ["clean: 1 caught"]


def test_ministers_are_named_against_members_by_title_words_only():
    keys = {"bishop chris", "collins judith", "clark david", "peters winston"}
    assert check.bare("Rt Hon Winston Peters") == "Winston Peters"
    assert check.bare("Hon Judith Collins KC") == "Judith Collins"
    assert check.bare("Hon Dr David Clark") == "David Clark"
    got = check.ministers_against_members(["Hon Chris Bishop", "Hon Judith Collins KC", "Hon Dr David Clark",
                                           "Rt Hon Winston Peters", "Hon Christopher Bishop", "No Minister"], keys)
    assert got == {"ministers named": 6, "found in pub.members": 4, "not found": 2}     # no nickname, no guess


# ── the filled sample ────────────────────────────────────────────────────────

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_ministers_diaries"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    from registers.ministers_diaries import load as L, sample as S
    schema = _schema()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}_private")
        S.fill(conn, schema, items)
        conn.commit()

        def q(sql):
            cur = conn.execute(sql)
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.pub_"))
        conn.commit()
        t = f"{schema}.ministers_diaries"
        yield {"items": items, "entries": q(f"SELECT * FROM {t}_entries"), "releases": q(f"SELECT * FROM {t}_releases"),
               "files": q(f"SELECT * FROM {t}_files"), "set_aside": q(f"SELECT * FROM {t}_set_aside"),
               "private": q(f"SELECT * FROM {schema}_private.ministers_diaries_entries"),
               "pub_entries": q(f"SELECT * FROM {schema}.pub_minister_diary_entries"),
               "pub_releases": q(f"SELECT * FROM {schema}.pub_minister_diary_releases")}


def test_every_sample_document_is_read_and_every_row_keeps_the_contract(filled):
    assert len(filled["files"]) == len(filled["items"]) and not filled["set_aside"]
    assert sorted(f["status"] for f in filled["files"]).count("older version") == 1
    today = dt.date.today()
    for t in ("entries", "releases"):
        for r in filled[t]:
            row = {**r, "loaded_at": r["loaded_at"].isoformat()}
            assert rowcontract.validate(row, today) == [], (t, r["key"])
    assert all(not e["fields_unread"] for e in filled["entries"])


def test_the_sample_holds_its_hard_cases(filled):
    es, rs = filled["entries"], filled["releases"]
    assert any("meeting" in e["withheld"] for e in es) and any("time" in e["withheld"] for e in es)
    held = {e["location_held"] for e in es}
    assert {read.HELD_HOME, read.HELD_STREET} <= held
    assert any(e["addresses_masked"] for e in es) and any(e["attendees"] is None for e in es)
    assert any(read.STREET.search(e["location"] or "") for e in es)          # a business address, shown
    assert any(e["entry_on"] < dt.date(2019, 1, 1) for e in es) and any(e["entry_on"].year == 2026 for e in es)
    assert any(r["pdf_url"] is None for r in rs) and any(r["pdf_url"] for r in rs)
    assert any(e["minister"] == "No Minister" for e in es)
    assert any(e["versions"] == 2 for e in es)


def test_what_is_held_back_is_in_the_private_table_and_never_published(filled):
    priv = {p["key"]: p for p in filled["private"]}
    assert set(priv) == {e["key"] for e in filled["entries"]} and all(p["text"] for p in priv.values())
    for e in filled["pub_entries"]:
        if e["location_held"]:
            assert e["location"] is None and priv[e["key"]]["location"]
            if e["location_held"] == read.HELD_HOME:
                assert read.HOME.search(priv[e["key"]]["location"])
            else:
                assert read.STREET.search(priv[e["key"]]["location"])
        assert not read.HOME.search(e["location"] or "")
        for f in ("meeting", "attendees"):
            v = e[f] or ""
            assert not read.STREET.search(v.replace(read.MASK, "")), (e["key"], f)
            if e["addresses_masked"] and read.MASK in v:
                assert priv[e["key"]][f] and read.STREET.search(priv[e["key"]][f])
        assert not {"text", "address"} & set(e)


def test_every_published_row_cites_its_document_and_the_pdf(filled):
    assert len(filled["pub_entries"]) == len(filled["entries"])
    assert len(filled["pub_releases"]) == len(filled["releases"])
    for name in ("pub_entries", "pub_releases"):
        for r in filled[name]:
            assert len(r["document"]) == 64 and r["file_name"], (name, r["key"])
            assert r["citation_url"] is None or r["citation_url"].startswith(read.PDF_HOST), (name, r["key"])
    by = {r["key"]: r for r in filled["releases"]}
    n = {}
    for e in filled["entries"]:
        n[e["release"]] = n.get(e["release"], 0) + 1
    assert all(by[k]["entries"] == v for k, v in n.items()) and set(n) == set(by)
