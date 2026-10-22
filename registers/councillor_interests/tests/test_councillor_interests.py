"""The register reader's rules on a page shaped like Invercargill's (every
name, company, address and number invented), a mutant check of the withheld
rules, the capture on a fake transport (a council whose terms bar automated
access is never asked, a block holds the whole site, a document is asked
once, a page not due still yields its documents), the filled sample (real
pages, sample.list) against the row contract, DIA's 78 councils and the
withheld rules, and the position against what it captures. No
model is called, no PDF is read and nothing is fetched."""
import datetime as dt
import hashlib
import os
import re
import types

import pytest

from support import db, rowcontract, sample
from registers.councillor_interests import capture, check, load, read
from registers.councillor_interests import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_SCHEMA = "scratch_test_councillor_interests"
SECRETS = ("14 Pretend Street", "Nowhere Road", "hemi@invented.example", "021 555 0199", "Aroha Madeup",
           "Spouse Employer Ltd", "Lot 9 Imaginary Block", "Imaginary Valley")


def _member(role_name, rows):
    trs = "".join(f'<tr><td><p><strong>{i}.</strong></p></td><td><p><strong>{label}</strong></p>'
                  + "".join(f"<p>{e}</p>" for e in entries) + "</td></tr>" for i, (label, entries) in enumerate(rows, 1))
    return f'<table><tr><td colspan="2"><p><strong>{role_name}</strong></p></td></tr>{trs}</table>'


PAGE = ("<html><body><h1>Register of member’s pecuniary interests</h1>" + _member("Mayor Tama Invented", [
    ("Company Directorships and controlling interests (section 54E(1)(a)", ["Invented Holdings Limited"]),
    ("Employment (section 54E(1)(c)", ["Nil"]),
    ("Interest in real property (section 54E(1)(g)", ["Lot 9 Imaginary Block, 14 Pretend Street, Nowhere", "Family home (jointly owned), Imaginary Valley"]),
    ("Spouse or partner interests", ["Aroha Madeup – Spouse Employer Ltd"]),
]) + _member("Cr Mere Madeup", [
    ("Beneficial interest in a Trust (section 54E(1)(d)", ["Madeup Family Trust"]),
    ("Other interests", ["Contact: hemi@invented.example or 021 555 0199", "Rotary Club of Nowhere"]),
    ("Location of real property held by a Trust", ["12 Nowhere Road"]),
]) + "</body></html>").encode()


def test_every_rule_holds():
    assert read.recognise(PAGE) == "register"
    out = read.read_register(PAGE, "e" * 64, "https://www.invented.govt.nz/register")
    assert [(m["role"], m["member"]) for m in out["members"]] == [("Mayor", "Tama Invented"), ("Cr", "Mere Madeup")]
    cats = [(r["member"], r["category"], r["clause"], r["entries"]) for r in out["rows"]]
    assert cats == [("Tama Invented", "Company Directorships and controlling interests", "a", ["Invented Holdings Limited"]),
                    ("Tama Invented", "Employment", "c", []),
                    ("Mere Madeup", "Beneficial interest in a Trust", "d", ["Madeup Family Trust"]),
                    ("Mere Madeup", "Other interests", None, ["Rotary Club of Nowhere"])]
    assert sum(out["withheld"].values()) == 4


def test_nothing_withheld_reaches_a_row():
    out = read.read_register(PAGE, "e" * 64, "https://www.invented.govt.nz/register")
    blob = repr(out["rows"]) + repr(out["members"])
    assert not [s for s in SECRETS if s in blob]
    assert all(not re.search(r"\d", k[0]) for k in out["withheld"])          # headings only, never a value


def test_a_landing_page_is_a_page_and_its_register_links_are_found():
    landing = (b'<a href="/files/register-of-pecuniary-interests-2026.pdf">Register</a>'
               b'<a href="https://other.example.nz/pecuniary.pdf">elsewhere</a><a href="mailto:x@y.nz">pecuniary</a>'
               b'<a href="/council/members">Elected members\' interests register</a><a href="/news">News</a>')
    assert read.recognise(landing) == "page"
    got = capture.register_links(landing, "https://www.invented.govt.nz/council/", "www.invented.govt.nz")
    assert got == [("https://www.invented.govt.nz/files/register-of-pecuniary-interests-2026.pdf", "document"),
                   ("https://www.invented.govt.nz/council/members", "page")]


MUTANTS = {
    "real property read": ("WITHHELD", re.compile(r"^$never")),
    "a spouse's interests read": ("PRIVATE_PERSON", re.compile(r"^$never")),
    "an address-shaped entry kept": ("withheld_entry", lambda s: False),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_is_caught(name, monkeypatch):
    attr, value = MUTANTS[name]
    monkeypatch.setattr(read, attr, value)
    with pytest.raises(AssertionError):
        test_nothing_withheld_reaches_a_row()


# ── the capture on a fake transport ───────────────────────────────────────────

class FakeTables:
    def __init__(self):
        self.items, self.held = [], {}

    def held_hosts(self):
        return dict(self.held)

    def hold(self, host, why):
        self.held[host] = why

    def last_asked(self, url):
        got = [i for i in self.items if i["url"] == url]
        if not got:
            return None, None
        return max(i["at"] for i in got), any(i["kind"] == "document" for i in got)

    def newest_sha(self, url):
        got = [i for i in self.items if i["url"] == url and i["sha"]]
        return got[-1]["sha"] if got else None

    def item(self, council, url, kind, found_on, status, sha, why):
        self.items.append({"url": url, "kind": kind, "sha": sha, "why": why, "at": dt.datetime.now(dt.timezone.utc)})


def _fetched(url, status=200, body=b"", blocked=""):
    return types.SimpleNamespace(url=url, status=status, body=body, final_url=url, blocked=blocked, location="")


LANDING = b'<a href="/files/register-of-pecuniary-interests-2026.pdf">Register of pecuniary interests</a>'


def _run(t, answers, store, regs, hour=23):
    asked = []

    def opener(url, timeout):
        asked.append(url)
        return answers(url)

    def land_fn(data, *, name, content_type):
        sha = hashlib.sha256(data).hexdigest()
        new = sha not in store
        store[sha] = data
        return types.SimpleNamespace(sha256=sha), new

    clock = [0.0]
    r = capture.Run(t, land_fn=land_fn, opener=opener, registers=regs, clock=lambda: clock[0],
                    sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                    now=lambda: dt.datetime(2026, 10, 22, hour, 30, tzinfo=capture.NZ))
    return r, asked


REGS = {"Invented District Council": ("www.invented.govt.nz", "https://www.invented.govt.nz/council/", None),
        "Auckland Council": ("www.aucklandcouncil.govt.nz", "https://www.aucklandcouncil.govt.nz/x", None),
        "Blocked District Council": ("www.blocked.govt.nz", "https://www.blocked.govt.nz/a", "https://blocked.govt.nz/r.pdf")}


def _answers(u):
    if "blocked" in u:
        return _fetched(u, 403, b"", "HTTP 403: a block or a challenge; a challenged read is a failed read (hard limit 6)")
    return _fetched(u, body=b"%PDF-1.4 x" if u.endswith(".pdf") else LANDING)


def test_terms_bar_blocks_and_documents_once(monkeypatch):
    import support.docstore.landing as L
    store, t = {}, FakeTables()
    monkeypatch.setattr(L, "read_bytes", lambda sha, root=None: store[sha])
    r, asked = _run(t, _answers, store, REGS)
    out = r.run()
    assert not any("aucklandcouncil" in u for u in asked)                     # its terms bar automated access
    assert asked.count("https://www.blocked.govt.nz/a") == 1 and "https://blocked.govt.nz/r.pdf" not in asked
    assert out["documents"] == 1 and out["pages"] == 1 and "www.blocked.govt.nz" in t.held
    r2, asked2 = _run(t, _answers, store, REGS)
    out2 = r2.run()
    assert asked2 == [] and out2["requests"] == 0                             # page not due; document met; site held


def test_a_page_not_due_still_yields_a_new_document(monkeypatch):
    import support.docstore.landing as L
    store, t = {}, FakeTables()
    monkeypatch.setattr(L, "read_bytes", lambda sha, root=None: store[sha])
    regs = {"Invented District Council": REGS["Invented District Council"]}
    _run(t, _answers, store, regs)[0].run()
    t.items = [i for i in t.items if i["kind"] != "document"]                 # as if the document had failed to land
    r2, asked2 = _run(t, _answers, store, regs)
    r2.run()
    assert asked2 == ["https://www.invented.govt.nz/files/register-of-pecuniary-interests-2026.pdf"]


def test_no_request_outside_off_peak():
    r, asked = _run(FakeTables(), _answers, {}, REGS, hour=14)
    assert r.run()["requests"] == 0 and asked == [] and r.stopped == "off-peak is over"


# ── the positions against what the lanes ask ──────────────────────────────────

def _hosts(path):
    return {h.strip() for h in re.search(r"^hosts: (.*)$", open(path, encoding="utf-8").read(), re.M).group(1).split(",")}


def _covered(host, hosts):
    parts = host.split(".")
    return any(".".join(parts[i:]) in hosts for i in range(len(parts) - 1))


def test_the_position_names_every_host_the_lane_asks():
    mine = _hosts(os.path.join(LANE, "position", "councillors-registers-of-interests.md"))
    asked = {capture.REGISTERS[c][0] for c in capture.REGISTERS}
    asked |= {re.sub(r"^https?://([^/]+).*$", r"\1", u) for v in capture.REGISTERS.values() for u in v[1:] if u}
    assert not [h for h in asked if not _covered(h, mine)]


# ── the filled sample: real pages ─────────────────────────────────────────────

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
        yield {"conn": conn, **{t: _rows(conn, f"SELECT * FROM {T(t)}") for t in load.TABLES}}


def test_the_registers_hold_dia_s_78_councils(filled):
    from support.docstore.landing import read_bytes
    import csv
    import io
    data = read_bytes(capture.COUNCIL_LIST_SHA).decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    dia = [r["Council"].strip() for r in csv.DictReader(io.StringIO(data))]
    assert len(dia) == len(filled["registers"]) == len(capture.REGISTERS) == 78


def test_invercargill_reads_and_the_landing_pages_do_not(filled):
    by = {r["council"]: r for r in filled["registers"]}
    assert by["Invercargill City Council"]["form"] == "html register" and by["Invercargill City Council"]["members_read"] == 15
    assert {by[c]["form"] for c in ("Kapiti Coast District Council", "Tauranga City Council", "Hastings District Council")} \
        == {"linked, not found"}
    assert {r["council"] for r in filled["interests"]} == {"Invercargill City Council"} and len(filled["interests"]) > 40
    assert by["Auckland Council"]["form"] == "held: its terms bar automated access"


def test_every_row_meets_the_row_contract(filled):
    for r in filled["interests"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


def test_real_property_and_spouses_are_withheld_on_the_real_page(filled):
    whys = {w["why"].split(":")[0] for w in filled["read_withheld"]}
    assert "real property, a home, an address or a contact" in whys and "a spouse's or partner's interests" in whys
    assert not [r for r in filled["interests"] if read.WITHHELD.search(r["category"]) or read.PRIVATE_PERSON.search(r["category"])]
    assert not [e for r in filled["interests"] for e in r["entries"] if read.withheld_entry(e)]


def test_the_reading_is_clean_and_goes_red_when_broken(filled):
    conn = filled["conn"]
    assert check.reading(conn, SAMPLE_SCHEMA) == []
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    try:
        conn.execute(f"UPDATE {T('interests')} SET category = 'Interest in real property' WHERE key = (SELECT min(key) FROM {T('interests')})")
        conn.execute(f"UPDATE {T('interests')} SET entries = ARRAY['14 Invented Street'] WHERE key = (SELECT max(key) FROM {T('interests')})")
        conn.execute(f"DELETE FROM {T('registers')} WHERE council = 'Gore District Council'")
        problems = check.reading(conn, SAMPLE_SCHEMA)
    finally:
        conn.rollback()
    assert len(problems) == 3, problems


def test_links_resolve_against_the_page_s_base_and_are_cleaned():
    page = (b'<base href="https://www.invented.govt.nz/" /><a href="assets/Register-of-Interests/Cr Invented\n 2026.pdf">'
            b'Register of interests</a><a href="assets/M\xc4\x81ori-pecuniary.pdf">x</a>')
    got = capture.register_links(page, "https://www.invented.govt.nz/our-council/register/", "www.invented.govt.nz")
    assert got == [("https://www.invented.govt.nz/assets/Register-of-Interests/Cr%20Invented%202026.pdf", "document"),
                   ("https://www.invented.govt.nz/assets/M%C4%81ori-pecuniary.pdf", "document")]


def test_a_malformed_address_holds_nothing_and_a_same_site_redirect_is_followed_once(monkeypatch):
    import http.client
    import support.docstore.landing as L
    store, t = {}, FakeTables()
    monkeypatch.setattr(L, "read_bytes", lambda sha, root=None: store[sha])
    land = b'<a href="/r1.pdf">pecuniary</a><a href="/r2.pdf">pecuniary</a>'

    def answers(u):
        if u.endswith("r1.pdf"):
            raise http.client.InvalidURL("URL can't contain control characters")
        if u.endswith("r2.pdf"):
            r = _fetched(u, 301)
            r.location = "https://invented.govt.nz/r2-moved.pdf"
            return r
        return _fetched(u, body=b"%PDF-1.4 y" if u.endswith(".pdf") else land)
    regs = {"Invented District Council": REGS["Invented District Council"]}
    r, asked = _run(t, answers, store, regs)
    out = r.run()
    assert t.held == {} and out["documents"] == 1 and asked[-1] == "https://invented.govt.nz/r2-moved.pdf"
    assert t.last_asked("https://www.invented.govt.nz/r1.pdf")[0] is not None   # FakeTables keeps every row
