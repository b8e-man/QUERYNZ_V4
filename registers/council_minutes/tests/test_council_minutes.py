"""The listing reader's rules on pages shaped like InfoCouncil's (every venue
and code invented), a mutant check of the rules, the capture on a fake
transport (politeness, the old estate's documents never fetched, a block
holds one instance and the run goes on, a document asked once), and the
filled sample (real listings, sample.list) against the row contract, the
grid's own counts and the venue rule. No model is called, no PDF is read and
nothing is fetched."""
import datetime as dt
import os
import re
import types

import pytest

from support import db, rowcontract, sample
from registers.council_minutes import capture, check, load, read
from registers.council_minutes import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_SCHEMA = "scratch_test_council_minutes"
BASE = "https://invented.infocouncil.biz"
VENUE = "12 Pretend Street, Nowhere"


def _row(date, body, links, alt=False):
    cells = {"bpsGridAgenda": [], "bpsGridAttachments": [], "bpsGridMinutes": [], "bpsGridMinutesAttachments": []}
    for cell, fname in links:
        cells[cell].append(f'<a title="Doc for x (1.5MB)" class="bpsGridPDFLink" '
                           f'href="RedirectToDoc.aspx?URL=Open/2026/10/{fname}" target="_blank">PDF(1.5MB)</a>')
    tds = "".join(f'<td class="{c}">{"".join(v)}</td>' for c, v in cells.items())
    cls = "bpsGridMenuAltItem" if alt else "bpsGridMenuItem"
    return (f'<tr class="{cls}"><td class="bpsGridDate">{date}<br /><span>9:30 am</span></td>'
            f'<td class="bpsGridCommittee">{body} <br /><span style=\'font-size: 85%;\'>{VENUE}</span></td>{tds}</tr>')


def _page(rows):
    return ('<html><head><link href="App_Themes/Default/BusinessPapers.css?ver=2" rel="stylesheet" /></head><body>'
            '<select name="ddlYear"><option value="2025">2025</option><option selected="selected" value="2026">2026'
            '</option></select><table>' + "".join(rows) + "</table></body></html>").encode()


PAGE = _page([
    _row("21 Oct 2026", "Council", [("bpsGridAgenda", "CO_20261021_AGN_3600_AT.PDF"),
                                    ("bpsGridAgenda", "CO_20261021_AGN_3600_AT_WEB.htm"),
                                    ("bpsGridMinutes", "CO_20261021_MIN_3600.PDF")]),
    _row("21 Oct 2026", "Council Supplementary", [("bpsGridAgenda", "CO_20261021_AGN_3600_SUP.PDF")], alt=True),
    _row("22/10/2026", "Extraordinary Council", [("bpsGridAgenda", "XC-C_20261022_AGN_AT.PDF"),
                                                 ("bpsGridMinutesAttachments", "XC-C_20261022_MAT_3601.PDF")]),
    _row("23 Oct 2026", "Hearings Panel", []),
])


def test_every_rule_holds():
    out = read.read_listing(PAGE, "e" * 64, BASE)
    ms, ds = out["meetings"], out["documents"]
    assert out["year"] == 2026 and len(ms) == 4 == capture.grid_rows(PAGE)
    assert [m["meeting_date"] for m in ms] == [dt.date(2026, 10, 21)] * 2 + [dt.date(2026, 10, 22), dt.date(2026, 10, 23)]
    assert [m["body"] for m in ms] == ["Council", "Council Supplementary", "Extraordinary Council", "Hearings Panel"]
    assert len({m["key"] for m in ms}) == 4 and ms[1]["key"] == "invented.infocouncil.biz/CO_20261021_AGN_3600_SUP"
    assert ms[3]["key"].endswith("/row 4") and ms[3]["documents"] == 0
    assert [(d["kind"], d["format"]) for d in ds[:3]] == [("agenda", "pdf"), ("agenda", "html"), ("minutes", "pdf")]
    assert ds[2]["code"] == "CO" and ds[2]["doc_type"] == "MIN" and ds[2]["size_as_printed"] == "1.5MB"
    assert ds[4]["code"] == "XC-C" and ds[4]["number"] is None and ds[5]["kind"] == "minutes attachments"
    assert all(m["meeting_time"] == "9:30 am" for m in ms)


def test_no_venue_reaches_a_row():
    out = read.read_listing(PAGE, "e" * 64, BASE)
    blob = repr(out)
    assert "Pretend" not in blob and "Nowhere" not in blob


def test_a_page_that_is_not_a_listing_is_refused():
    with pytest.raises(read.NotTheShape):
        read.read_listing(b"<html><body>Server Error in '/' Application.</body></html>", "e" * 64, BASE)


def test_the_kind_comes_from_the_listed_name():
    assert [load.kind_of(b) for b in ("Council Supplementary", "Extraordinary Council", "Council Workshop",
                                      "Hearings Panel", "Finance Committee")] == \
        ["supplementary", "extraordinary", "workshop", "hearing", "meeting"]


MUTANTS = {
    "the venue read with the body": ("body_name", lambda cell: read.text(cell)),
    "a day-first date dropped": ("_DMY", re.compile(r"^$never")),
    "a hyphened code missed": ("_FILE", re.compile(r"^([A-Za-z0-9]+)_(\d{8})_([A-Za-z]+)(?:_(\d+))?([A-Za-z0-9_]*)\.(htm|pdf)$", re.I)),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_is_caught(name, monkeypatch):
    attr, value = MUTANTS[name]
    monkeypatch.setattr(read, attr, value)
    with pytest.raises((AssertionError, TypeError)):
        test_every_rule_holds()
        test_no_venue_reaches_a_row()


# ── the capture on a fake transport ───────────────────────────────────────────

class FakeTables:
    def __init__(self):
        self.listings, self.docs, self.held, self.aside = [], {}, {}, []

    def held_hosts(self):
        return dict(self.held)

    def hold(self, host, why):
        self.held[host] = why

    def last_listing(self, host):
        got = [a for h, a in ((x[0], x[1]) for x in self.listings) if h == host]
        return max(got) if got else None

    def listing(self, host, url, status, sha, rows, why):
        if sha:
            self.listings.append((host, dt.datetime.now(dt.timezone.utc), sha))

    def held_listings(self):
        return [(h, s) for h, _, s in sorted(self.listings, key=lambda x: x[1], reverse=True)]

    def known(self):
        return set(self.docs)

    def document(self, url, host, file, state, sha, listed_in, why=None, asked=True):
        self.docs[url] = (state, sha, asked)

    def set_aside(self, item, stage, reason):
        self.aside.append((item, stage, reason))


def _fetched(url, status=200, body=b"", blocked=""):
    return types.SimpleNamespace(url=url, status=status, body=body, final_url=url, blocked=blocked, location="")


def _run(tables, answers, store, *, hour=23, old=None, instances=None):
    asked = []

    def opener(url, timeout):
        asked.append(url)
        return answers(url)

    def land_fn(data, *, name, content_type):
        import hashlib
        sha = hashlib.sha256(data).hexdigest()
        new = sha not in store
        store[sha] = data
        return types.SimpleNamespace(sha256=sha), new

    clock = [0.0]
    r = capture.Run(tables, land_fn=land_fn, old=old or {}, read_fn=read.recognise, opener=opener,
                    clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                    now=lambda: dt.datetime(2026, 10, 22, hour, 30, tzinfo=capture.NZ),
                    instances=instances or {BASE: "Invented District Council", "https://other.infocouncil.biz": "Other"})
    return r, asked, clock


def _with_store(monkeypatch, store):
    import support.docstore.landing as L
    monkeypatch.setattr(L, "read_bytes", lambda sha, root=None: store[sha])


def test_the_capture_lands_each_minutes_pdf_once_and_never_the_old_estate_s(monkeypatch):
    store, t = {}, FakeTables()
    _with_store(monkeypatch, store)
    other = PAGE.replace(b"CO_20261021", b"OT_20261021").replace(b"XC-C_", b"OX-C_")
    answers = lambda u: _fetched(u, body=(other if "other." in u else PAGE) if u.endswith("/") else b"%PDF-1.4 " + u.encode())
    old = {capture.old_key("https://other.infocouncil.biz/RedirectToDoc.aspx?URL=Open/2026/10/OT_20261021_MIN_3600.PDF"): "a" * 64}
    r, asked, clock = _run(t, answers, store, old=old)
    out = r.run()
    assert out["listings"] == 2 and out["landed"] == 1 and out["old_estate"] == 1
    assert not any("OT_20261021_MIN" in u for u in asked)
    assert t.docs[next(u for u in t.docs if "OT_20261021_MIN" in u)] == ("held by the old estate", "a" * 64, False)
    assert len(asked) == 3 and clock[0] >= capture.FLOOR_S          # paced per host: the second ask of one host waited
    r2, asked2, _ = _run(t, answers, store, old=old)
    assert r2.run()["requests"] == 0 and asked2 == []          # listings under a week old; every minutes PDF met


def test_a_block_holds_that_instance_and_the_run_goes_on(monkeypatch):
    store, t = {}, FakeTables()
    _with_store(monkeypatch, store)

    def answers(u):
        if u.startswith(BASE):
            return _fetched(u, 403, b"", "HTTP 403: a block or a challenge; a challenged read is a failed read (hard limit 6)")
        return _fetched(u, body=PAGE.replace(b"CO_", b"OT_")) if u.endswith("/") else _fetched(u, body=b"%PDF-1.4 x")
    r, asked, _ = _run(t, answers, store)
    out = r.run()
    assert "invented.infocouncil.biz" in t.held and out["listings"] == 1 and out["landed"] == 1
    r2, asked2, _ = _run(t, answers, store)
    r2.run()
    assert not any(u.startswith(BASE) for u in asked2)          # a challenged read is not retried


def test_a_listing_that_moved_holds_the_instance_and_a_non_pdf_is_set_aside(monkeypatch):
    store, t = {}, FakeTables()
    _with_store(monkeypatch, store)

    def answers(u):
        if u.startswith(BASE):
            return _fetched(u, 404)
        return _fetched(u, body=PAGE) if u.endswith("/") else _fetched(u, body=b"<html>not here</html>")
    out = _run(t, answers, store)[0].run()
    assert t.held["invented.infocouncil.biz"].startswith("the listing: HTTP 404")
    assert out["set_aside"] == 1 and out["landed"] == 0


def test_no_request_outside_off_peak(monkeypatch):
    store, t = {}, FakeTables()
    _with_store(monkeypatch, store)
    r, asked, _ = _run(t, lambda u: _fetched(u, body=PAGE), store, hour=14)
    assert r.run()["requests"] == 0 and asked == [] and r.stopped == "off-peak is over"


# ── the filled sample: real listings ──────────────────────────────────────────

def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def _rows(conn, q):
    cur = conn.execute(q)
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@pytest.fixture(scope="module")
def filled():
    _db_or_skip()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        S.fill(conn, SAMPLE_SCHEMA, items)
        conn.execute(load.sql("publish.sql", SAMPLE_SCHEMA).replace("pub.", f"{SAMPLE_SCHEMA}.v_"))
        conn.commit()
        T = lambda t: load.table(SAMPLE_SCHEMA, t)
        yield {"conn": conn, "items": items, **{t: _rows(conn, f"SELECT * FROM {T(t)}") for t in load.TABLES},
               "listings": S.listings_of(items, conn)}


def test_every_listing_is_read_and_its_rows_equal_its_grid(filled):
    assert len(filled["read_listings"]) == len(filled["listings"]) == 5 and not filled["read_set_aside"]
    assert all(l["state"] == "read" and l["meetings"] == l["grid_rows"] > 0 for l in filled["read_listings"])
    assert sum(l["meetings"] for l in filled["read_listings"]) == len(filled["meetings"])


def test_every_row_meets_the_row_contract(filled):
    for r in filled["meetings"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


def test_the_hard_cases_read_as_the_council_lists_them(filled):
    by_host = {}
    for m in filled["meetings"]:
        by_host.setdefault(m["host"], []).append(m)
    assert all(m["meeting_date"] for m in by_host["infocouncil.dunedin.govt.nz"])          # 22/10/2026 dates
    assert any("-" in (m["code"] or "") for m in by_host["palmerstonnorth.infocouncil.biz"])   # JSC-C
    assert all(m["code"] for m in by_host["horowhenua.infocouncil.biz"])                    # no number in the name
    assert any(m["kind"] == "supplementary" for m in by_host["carterton.infocouncil.biz"])
    assert {m["minutes_held"] for m in filled["meetings"]} <= {"not yet captured", "no minutes listed", "html only"}


def test_no_venue_on_a_real_page_reaches_a_row(filled):
    from support.docstore.landing import read_bytes
    venues = set()
    for _, sha, _ in filled["listings"]:
        page = read_bytes(sha).decode("utf-8", "replace")
        for cell in re.findall(r'<td class="bpsGridCommittee">(.*?)</td>', page, re.S):
            parts = re.split(r"<br\s*/?>", cell, maxsplit=1, flags=re.I)
            if len(parts) == 2 and read.text(parts[1]):
                venues.add(read.text(parts[1]))
    assert len(venues) > 10
    bodies = {m["body"] for m in filled["meetings"]}
    assert not [v for v in venues if any(v in b for b in bodies)]


def test_the_reading_is_clean_and_goes_red_when_broken(filled):
    conn = filled["conn"]
    assert check.reading(conn, SAMPLE_SCHEMA) == []
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    try:
        conn.execute(f"DELETE FROM {T('meetings')} WHERE key = (SELECT min(key) FROM {T('meetings')})")
        conn.execute(f"UPDATE {T('meetings')} SET body = '14 Invented Street' WHERE key = (SELECT max(key) FROM {T('meetings')})")
        problems = check.reading(conn, SAMPLE_SCHEMA)
    finally:
        conn.rollback()
    assert any("grid" in p for p in problems) and any("street address" in p for p in problems)
