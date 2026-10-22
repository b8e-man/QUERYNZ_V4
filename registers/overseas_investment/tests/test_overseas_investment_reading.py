"""The reading's rules on pages shaped like the office's (every name and
place invented), a mutant check of those rules, the capture's politeness on a
fake transport, and the filled sample (real pages, sample.list) against the
row contract, the ledger, withholding and the views. No model is called and
nothing is fetched."""
import datetime as dt
import os
import re
import types

import pytest

from support import db, rowcontract, sample
from registers.overseas_investment import capture, check, load, read
from registers.overseas_investment import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = "e" * 64
SAMPLE_SCHEMA = "scratch_test_overseas_investment"


def _summary(rows, applicant="Alpha Holdings Limited", cases=("202600001",), kind="Decision", date="2026-08-20"):
    meta = ('<dl  class="content__wider-col node__meta-grid mb-12">'
            f'<dt class="field__label">Applicant</dt><dd> {applicant} </dd>'
            '<dt class="field__label">Case number(s)</dt><dd>'
            + "".join(f'<div class="clearfix">{c}</div>' for c in cases) + "</dd>"
            f'<dt class="field__label">Decision date</dt><dd><time datetime="{date}T12:00:00Z">x</time></dd>'
            f'<dt class="field__label">Type</dt><dd>{kind}</dd></dl>')
    table = "".join(f"<tr><th>{h}</th><td>{v}</td></tr>" for h, v in rows)
    return ('<html><head><title>x | Toitū Te Whenua</title></head><body><main>'
            '<div class="node node--type-oi-info-release node--view-mode-full">' + meta
            + '<div class="content__wider-col"><div class="prose w-100"><div class="table-responsive"><table class="table">'
            + f"<tbody>{table}</tbody></table></div></div></div></div></main></body></html>").encode()


def _listing(rows, page=0, last=1):
    row = lambda slug, case, who, when: (
        '<tr class="published-1"><td headers="x" class="views-field views-field-field-oi-case-number">'
        f'<a href="/our-work/overseas-investment-regulation/decisions/2026-08/{slug}" hreflang="en">{case}</a> </td>'
        f'<td headers="x" class="views-field views-field-field-oi-applicant">{who} </td>'
        f'<td headers="x" class="views-field views-field-field-decision-date"><time datetime="{when}T12:00:00Z">x</time></td></tr>')
    pager = (f'<a href="?field_decision_date_value=2026&amp;page={page}" title="Current page" aria-current="page">x</a>'
             + (f'<a href="?field_decision_date_value=2026&amp;page={last}" title="Go to last page">Last</a>' if page < last else ""))
    return ('<html><div class="block-views-block:oi-investment-releases-block-3"><table><thead><tr>'
            '<th class="views-field views-field-field-oi-case-number">Case number</th></tr></thead><tbody>'
            + "".join(row(*r) for r in rows) + f"</tbody></table>{pager}</div></html>").encode()


BASIC = [("Decision", "<strong>Consent granted</strong><br>Section 12(1)(a) Overseas Investment Act 2005"),
         ("Decision maker", "Toitū Te Whenua Land Information New Zealand"),
         ("Decision date", "20 August 2026"),
         ("Pathway", "Sensitive land - Primary consent"),
         ("Investment", "Acquisition of approximately 4.5 hectares of land located at 29 Invented Road, Inventa, "
                        "Invented Island 1971, Auckland; and 1,200 square metres at Lot 2 DP 123456, Inventa."),
         ("Consideration", "$8,400,000"),
         ("Applicant", "<strong>Alpha Holdings Limited as sole trustee of the Alpha Trust (company number 1234567)"
                       "</strong><br>British Virgin Islands 100%"),
         ("Vendors", "<strong>Invented Person and Other Person as trustees of the Beta Family Trust</strong><br>"
                     "New Zealand 100%"),
         ("Background", "<p>The Applicant is buying the Land.</p><p>Consent was granted as the national interest "
                        "test was met.</p>"),
         ("More information", "Agent Person<br>c/- Invented Law<br>15 Invented Street West, Auckland 1010")]


def rules(mod) -> list:
    broken = []
    L = mod.read_listing(_listing([("202600002", "202600002", "Alpha Holdings Limited", "2026-08-20"),
                                   ("202600003-202600004", "202600003", "Gamma Limited", "2026-08-19"),
                                   ("202600003-202600004", "202600004", "Gamma Limited", "2026-08-19")]))
    if L["last_page"] != 1 or [(i["slug"], i["case_number"]) for i in L["items"]] != [
            ("202600002", "202600002"), ("202600003-202600004", "202600003"), ("202600003-202600004", "202600004")]:
        broken.append("the listing's rows, once per case number, and the pager's last page")
    if L["items"] and L["items"][0]["card"] != "202600002|Alpha Holdings Limited|2026-08-20":
        broken.append("a row's fingerprint is its case number, applicant and date")
    if mod.read_listing(_listing([("202600002", "202600002", "A Limited", "2026-08-20")], page=3, last=3))["last_page"] != 3:
        broken.append("on the last page the pager's last page is the current one")

    a = mod.read_summary(_summary(BASIC), SHA, "202600001")
    d, ps = a["decision"], a["parties"]
    if not d or d["key"] != "overseas_investment/decision/202600001" or d["case_numbers"] != ["202600001"]:
        broken.append("the key is the page's slug; the case numbers as stated")
    if d and (d["outcome"] != "Consent granted" or d["granted"] is not True
              or d["section"] != "Section 12(1)(a) Overseas Investment Act 2005"):
        broken.append("the outcome and its section as stated")
    if d and (d["decided_on"] != dt.date(2026, 8, 20) or d["pathway"] != "Sensitive land - Primary consent"):
        broken.append("the decision date and the pathway as stated")
    if d and ("29 Invented" in d["investment"] or "DP 123456" in d["investment"] or d["addresses_withheld"] != 2
              or "Inventa" not in d["investment"]):
        broken.append("a street address and a legal description are withheld, the locality kept")
    if d and (d["area_ha"] != [4.5, 0.12] or d["areas_stated"][0] != "approximately 4.5 hectares"):
        broken.append("areas as stated and in hectares")
    if not a["private"] or "29 Invented Road" not in a["private"][0]["investment_stated"]:
        broken.append("the statement as published is held private")
    if d and (d["consideration_nzd"] != 8400000 or d["consideration_withheld"]):
        broken.append("one dollar figure is the consideration")
    if d and d["rationale"] != ["Consent was granted as the national interest test was met."]:
        broken.append("the rationale is the sentence naming a test, as stated")
    if [(p["role"], p["role_stated"]) for p in ps] != [("applicant", "Applicant"), ("vendor", "Vendors")]:
        broken.append("one party per bold name, by role")
    if len(ps) == 2 and (ps[0]["company_number"] != "1234567" or "company number" in (ps[0]["name"] or "")
                         or ps[0]["trust"] != "Alpha Trust" or ps[1]["company_number"] is not None):
        broken.append("a company number only where printed beside the name; the trust named")
    if len(ps) == 2 and (ps[0]["origins"] != ["British Virgin Islands"] or ps[0]["shares"] != [100.0]):
        broken.append("ownership origin and share as stated")
    if any("Agent" in str(v) or "15 Invented Street" in str(v) for v in list(d.values()) + [p for p in ps]):
        broken.append("More information is never read")

    w = mod.read_summary(_summary([
        ("Decision", "<strong>Consent declined</strong><br>Section 12(a) Overseas Investment Act 2005"),
        ("Investment", "Withheld under s9(2)(b)(ii) of the Official Information Act"),
        ("Consideration", "$1,000,000 (deposit); balance withheld under s9(2)(b)(ii) of the Official Information Act"),
        ("Applicant", "<p>Withheld under s9(2)(a) of the Official Information Act</p><p>Invented Holder, Australia (100%)</p>"),
        ("Vendor", "<strong>Delta Limited</strong><br>New Zealand 100%")],
        applicant="Withheld under s9(2)(a) of the Official Information Act"), SHA, "202600009")
    wp = w["parties"]
    if not (wp and wp[0]["withheld"] and wp[0]["name"] is None and wp[0]["origins"] is None):
        broken.append("a withheld name is withheld, with its ownership origins")
    if not (len(wp) == 2 and not wp[1]["withheld"] and wp[1]["name"] == "Delta Limited"):
        broken.append("a withholding binds only the name withheld")
    if w["decision"] and (w["decision"]["applicant_listed"] is not None or w["decision"]["granted"] is not False
                          or not w["decision"]["consideration_withheld"] or w["decision"]["consideration_nzd"] is not None):
        broken.append("the listed applicant is withheld too; declined; the figure withheld")

    v = mod.read_summary(_summary(BASIC[:6] + [
        ("Vendor", "<strong>Epsilon Limited</strong> (in receivership)<br>United States Public (93.1%)<br>"
                   "<strong>Zeta LLC</strong><br>Various overseas persons (100%)"),
        ("Background", "x")]), SHA, "202600010")["parties"]
    if [(p["name"], p["status"], p["shares"]) for p in v if p["role"] == "vendor"] != [
            ("Epsilon Limited", "(in receivership)", [93.1]), ("Zeta LLC", None, [100.0])]:
        broken.append("ownership lines under a name are that party's; a status beside the name")
    sh = mod.read_summary(_summary(BASIC[:6] + [
        ("Vendor", "<strong>Eta Limited</strong><strong>Theta Limited</strong><p>New Zealand (100%)</p>")]),
        SHA, "202600011")["parties"]
    if [(p["shares"], p["ownership_scope"]) for p in sh] != [([100.0], "every party named in the cell")] * 2:
        broken.append("lines only under the last of several names are shared")

    n = mod.read_summary(_summary([
        ("Notification", "Section 23A Overseas Investment Act 2005<br> Schedule 4(2) – standing consent"),
        ("Notification number", "6 (of 10)"), ("Date", "22&nbsp;November 2022"),
        ("Investment", "Acquisition of approximately 3.2 ha of Land at 94 Invented Road, Inventa (the Land)."),
        ("Lease amount", "$132,000 per annum"),
        ("Consent holder", "<strong>Iota Limited</strong><br> Malaysia (80%)<br> Singapore (20%)")],
        kind="Notification", cases=("202200072/6",), date="2022-11-21"), SHA, "2022000726")
    nd = n["decision"]
    if not nd or nd["outcome"] is not None or not nd["section"].startswith("Section 23A") or nd["granted"] is not None:
        broken.append("a notification whose cell begins with its section has no outcome")
    if nd and (nd["decided_on"] != dt.date(2022, 11, 22) or nd["notification_number"] != "6 (of 10)"):
        broken.append("'Date' is the decision date; the notification number as stated")
    if nd and (nd["consideration_heading"] != "Lease amount" or nd["consideration_nzd"] is not None):
        broken.append("a lease amount is never read as a price")
    if nd and (nd["area_ha"] != [3.2] or "94 Invented" in nd["investment"]):
        broken.append("'ha' is hectares; the address withheld")
    if [p["role"] for p in n["parties"]] != ["applicant"]:
        broken.append("a consent holder is the applicant")

    if mod.withhold_addresses("approximately 5 hectares at RD 5 Inventa") != ("approximately 5 hectares at RD 5 Inventa", 0):
        broken.append("a rural delivery number is not a street address")
    other = mod.read_summary(_summary(BASIC).replace(b"node--type-oi-info-release", b"node--type-page"), SHA, "z")
    if other["decision"] is not None:
        broken.append("a page that is not an overseas investment release is not a summary")
    bad = mod.read_summary(b"<html><title>Just a moment...</title></html>", SHA, "x")
    gone = mod.read_summary(b"<html><title>Page not found</title><main>Page not found</main></html>", SHA, "y")
    if bad["decision"] is not None or len(bad["set_aside"]) != 1 or gone["decision"] is not None:
        broken.append("a page not of the summary's shape is set aside whole")
    try:
        mod.read_listing(b"<html><title>Page not found</title></html>")
        broken.append("a page not of the listing's shape is refused")
    except ValueError:
        pass
    return broken


def test_every_rule_holds():
    assert rules(read) == []


def test_the_withholding_of_addresses_keeps_business_words():
    keep = ["acquiring 100% of the shares in Invented Limited", "the consideration exceeds $100 million",
            "approximately 295 hectares of land adjacent to the airport", "up to 15 developments in Auckland",
            "RD 5 Inventa", "the second of 27 transactions", "an interest in 38% of the shares in Kappa Limited"]
    for k in keep:
        assert read.withhold_addresses(k) == (k, 0), k
    for a in ["at 14 Invented Creek, Inventa", "at 131-139 Invented Road, and 2 and 4 Other Street, Inventa",
              "at 20, 26B, 28A and 28B Invented Street, Inventa", "at 57, 59 and 61 Invented Avenue.",
              "being Lot 1 DP 12345 and Section 3 Block IV Inventa Survey District"]:
        out, n = read.withhold_addresses(a)
        assert n >= 1 and not any(ch.isdigit() for ch in out.replace("IV", "")), (a, out)


MUTANTS = {
    "a withheld name kept": ('        withheld = bool(WITHHELD.search(name))\n', '        withheld = False\n'),
    "origins kept under a withheld name": ('"origins": None if withheld else origins', '"origins": origins'),
    "the listed applicant kept on a withholding": ('if listed_applicant and (applicants_withheld or',
                                                   'if listed_applicant and False and (applicants_withheld or'),
    "street addresses kept": ("    out = STREET.sub(street, out)\n", ""),
    "legal descriptions kept": ("    out = LEGAL.sub(legal, text)\n", "    out = text\n"),
    "rural delivery read as a street": ("(?<!RD )", ""),
    "ownership lines shared everywhere": ('shared = len(parties) > 1 and parties[-1]["lines"] and not any(p["lines"] for p in parties[:-1])',
                                          'shared = len(parties) > 1'),
    "ownership lines never shared": ("    if shared:\n        for p in parties[:-1]:", "    if False:\n        for p in parties[:-1]:"),
    "a lease amount read as a price": ("    if cons_head and not PRICE_HEADINGS.match(cons_head):\n        nzd = None\n", ""),
    "a withheld figure read": ("    if withheld or len(found) != 1", "    if len(found) != 1"),
    "the section read as the outcome": ("    if lines and _SECTION_FIRST.match(lines[0][0]):", "    if False:"),
    "'Date' not read": ('or date_of(by.get("date", ""))', ""),
    "the company number left in the name": ('            name = clean(name[:number.start()] + name[number.end():])\n', '            pass\n'),
    "any page read as a summary": ('    if "node--type-oi-info-release" not in t:\n', '    if False:\n'),
    "a consent holder not a party": (r'("applicant", re.compile(r"^(?:applicants?|consent holders?)\b", re.I))',
                                     r'("applicant", re.compile(r"^(?:applicants?)\b", re.I))'),
    "the pager's last page from the current page only": ("return {\"page\": page, \"last_page\": max([page] + pages)",
                                                         "return {\"page\": page, \"last_page\": page"),
    "square metres read as hectares": ("else n / 10000", "else n"),
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
    except (KeyError, TypeError, AttributeError, ValueError, IndexError):
        broken = ["crashed"]
    assert broken, f"the mutant '{name}' passes every rule"


# ── the capture's politeness, on a fake transport ─────────────────────────────

class FakeTables:
    def __init__(self):
        self.p, self.listed, self.items, self.asides, self.finished = None, [], {}, [], False

    def open_pass(self, name):
        return None if self.finished else self.p

    def last_finished(self, name):
        return None

    def begin(self, name):
        self.p = {"pass_id": 1, "list": name, "stated_pages": None, "stated": None, "next_page": 0, "pages": 0, "items": 0}
        return self.p

    def add_page(self, p, n, url, sha, items, stated_pages, stated):
        self.listed += [(i["slug"], i["url"], i["card"]) for i in items]
        p.update(next_page=n + 1, pages=p["pages"] + 1, items=len(self.listed), stated_pages=stated_pages,
                 stated=stated if stated is not None else p["stated"])

    def finish(self, p):
        self.finished = True

    def pending(self, limit, names=None):
        return [r for r in self.listed if self.items.get(r[0]) != r[2]][:limit]

    def add_item(self, slug, url, card, sha):
        self.items[slug] = card

    def docs_due(self, days):
        return False

    def set_aside(self, pass_id, item, stage, reason):
        self.asides.append((stage, reason))


def _run(answers, slugs):
    t, clock, asked = FakeTables(), [0.0], []
    listing = _listing([(s, s, "Invented Limited", "2026-08-20") for s in slugs], page=0, last=0)

    def opener(url, timeout):
        asked.append(url)
        clock[0] += 0.1
        a = answers.pop(0) if answers else 200
        if isinstance(a, Exception):
            raise a
        body = listing if "page=" in url else (b"<html><title>Just a moment...</title></html>" if a == "shape"
                                               else _summary(BASIC))
        st = 200 if a == "shape" else a
        return types.SimpleNamespace(url=url, status=st, body=body if st == 200 else b"<html>error</html>",
                                     final_url=url, blocked="HTTP 403: a block" if st in (403, 429) else "")

    run = capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="a" * 64), True), opener=opener,
                      clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                      now=lambda: dt.datetime(2026, 10, 22, 23, 0, tzinfo=capture.NZ), docs={},
                      lists=[capture.List(2026)])
    return run, run.run(), t, asked, clock


def test_a_pass_ends_on_the_pagers_last_page_with_the_offices_count():
    run, out, t, asked, clock = _run([], ["a", "b", "c"])
    assert t.finished and t.p["stated"] == 3 and t.p["stated_pages"] == 1 and set(t.items) == {"a", "b", "c"}
    assert "field_decision_date_value=2026&page=0" in asked[0] and clock[0] >= 3 * capture.FLOOR_S


def test_a_block_stops_the_run():
    run, out, t, asked, clock = _run([200, 200, 403], ["a", "b", "c", "d"])
    assert out["stopped"].startswith("stopped:") and len(asked) == 3 and set(t.items) == {"a"}
    assert clock[0] >= 2 * capture.FLOOR_S and capture.outcome(out)[0]      # a polite stop after landing is green


def test_a_server_error_and_a_timeout_are_failed_reads_and_the_run_goes_on():
    run, out, t, asked, clock = _run([200, 500, TimeoutError("slow"), 200, 200], ["a", "b", "c", "d"])
    assert not out["stopped"] and set(t.items) == {"c", "d"}
    assert [s for s, _ in t.asides] == ["fetch", "fetch"] and clock[0] >= capture.REST_S


def test_three_failed_reads_in_a_row_stop_the_run():
    run, out, t, asked, clock = _run([200, 502, 503, ConnectionResetError("reset")], ["a", "b", "c", "d"])
    assert out["stopped"].startswith("stopped:") and "3 failed reads" in out["stopped"] and not t.items


def test_a_page_not_of_the_summary_shape_is_not_landed():
    run, out, t, asked, clock = _run([200, "shape", 200], ["a", "b"])
    assert set(t.items) == {"b"} and t.asides[0][0] == "item"


def test_off_peak_only_unless_asked():
    t = FakeTables()
    run = capture.Run(t, land_fn=None, opener=lambda u, s: pytest.fail("asked during the day"), docs={},
                      lists=[capture.List(2026)], now=lambda: dt.datetime(2026, 10, 22, 14, 0, tzinfo=capture.NZ))
    assert run.run()["stopped"] == "off-peak is over"


def test_the_window_is_2017_on():
    assert [x.year for x in capture.lists(dt.date(2026, 10, 21))] == list(range(2017, 2027))


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
        yield {"conn": conn, "items": items, **{t: _rows(conn, f"SELECT * FROM {T(t)}") for t in load.TABLES},
               "decisions_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_overseas_investment_decisions"),
               "parties_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_overseas_investment_parties")}


#: the sample's hard cases by their documents (sample.list numbers them; no name in git)
D = {"trustees": "4710b38ce4d6911d5b6115a219120305c0ced9cdae4ae8f6d045155eb226ba19",
     "five addresses": "84573cef2a2348306d89762b5b9617d64ce7b3e3f4a7e27eb32a829aaf5664c5",
     "declined": "cd4b667106dd833993c0b75a8b1edf1310dfe5249e2dd93cbf8a2af3475f5fe0",
     "no street word": "7d8c52619f563259ad40ece319183f1e57e0652df2d1d3f1f25f29d241822aba",
     "asset value": "19b40c7fa55cd1b2627212a5cab9447ecd31bbec06b41909340e53793837aa03",
     "two cases": "1cc1be1e4ddd719d204d927858fef3c0f9c091f1e770be2b46d866ba5d90ea84",
     "old notification": "2ba28c76522b136f3a37fbced2476c384807cc8eadf7141139b57d18267b29f2",
     "all withheld": "ee73ef7cd86fdfc1a555c52880e765d0e6370774eff8f44abf702ad358023cdc",
     "both withheld": "1d6e1d9f72e1d76dc88ec5da9f6dd8d9d6998e1758003cafa207ad3d8b84c165",
     "seven cases": "e1add9fd7700d9f3f56137bf9bcbe44722b8c47411c223cd1b8f216ac46b896e",
     "two vendors' lines": "1f491138ec4ccc95883a08b6b6c26f0709c2a06cb9e5c7012ad1f3a0ad564769",
     "lease": "2643faf28f446a0978a312b2a8bdcde824b07de38050cec04fe63e90a94d3c30"}


def test_every_listed_row_is_read(filled):
    assert len(filled["decisions"]) == 16 and not filled["read_set_aside"]
    assert {r["state"] for r in filled["read_items"]} == {"read"} and len(filled["read_items"]) == 16 + 1 + 6


def test_every_row_meets_the_row_contract(filled):
    for r in filled["decisions"] + filled["parties"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


def test_the_hard_cases_read_as_the_office_states_them(filled):
    by = {r["document"]: r for r in filled["decisions"]}
    parties = {}
    for p in filled["parties"]:
        parties.setdefault(p["document"], []).append(p)
    assert by[D["five addresses"]]["addresses_withheld"] == 5 and by[D["five addresses"]]["consideration_withheld"]
    assert by[D["no street word"]]["addresses_withheld"] == 1
    assert by[D["declined"]]["granted"] is False and by[D["declined"]]["attachments"] == 2
    assert by[D["asset value"]]["consideration_heading"] == "Asset Value" and by[D["asset value"]]["consideration_nzd"] is None
    assert len(by[D["two cases"]]["case_numbers"]) == 2 and len(by[D["seven cases"]]["case_numbers"]) == 7
    assert [p["status"] is not None for p in parties[D["two cases"]] if p["role"] == "vendor"] == [True, True, False]
    assert by[D["old notification"]]["outcome"] is None and by[D["old notification"]]["kind"] == "Notification"
    assert all(p["withheld"] and p["name"] is None for p in parties[D["both withheld"]])
    assert by[D["both withheld"]]["applicant_listed"] is None
    assert [p["role"] for p in parties[D["all withheld"]]] == ["applicant", "issuer"]
    vend = [p for p in parties[D["two vendors' lines"]] if p["role"] == "vendor"]
    assert [len(p["shares"]) for p in vend] == [2, 2] and all(p["ownership_scope"] == "this party" for p in vend)
    assert by[D["lease"]]["consideration_heading"] == "Lease amount" and by[D["lease"]]["consideration_nzd"] is None
    assert by[D["trustees"]]["consideration_nzd"] == 8400000


def test_the_private_statement_keeps_what_the_view_withholds(filled):
    priv = {r["key"]: r["investment_stated"] for r in filled["investments"]}
    for d in filled["decisions_view"]:
        if d["addresses_withheld"]:
            assert "[street address withheld]" in d["investment"] and priv[d["key"]] != d["investment"]


def test_the_views_withhold_and_the_check_is_clean(filled):
    held = [r for r in filled["parties_view"] if r["withheld"]]
    assert held and all(r["name"] == "name withheld" and r["origins"] is None for r in held)
    assert check.views(filled["conn"], f"{SAMPLE_SCHEMA}.v_") == []
    assert check.reading(filled["conn"], SAMPLE_SCHEMA) == []


def test_the_check_goes_red_on_a_name_shown_an_address_or_a_broken_ledger(filled):
    conn = filled["conn"]
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    conn.execute(f"UPDATE {T('read_items')} SET parties = parties + 1 WHERE document = %s", (D["declined"],))
    try:
        assert check.reading(conn, SAMPLE_SCHEMA) != []
    finally:
        conn.rollback()
    v = load.sql("publish.sql", SAMPLE_SCHEMA).replace("pub.", f"{SAMPLE_SCHEMA}.v_")
    conn.execute(v.replace("CASE WHEN p.withheld THEN 'name withheld' ELSE p.name END", "coalesce(p.name, 'x')"))
    try:
        assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") != []
    finally:
        conn.rollback()
    conn.execute(f"UPDATE {T('decisions')} d SET investment = i.investment_stated FROM {T('investments')} i "
                 "WHERE i.key = d.key AND d.document = %s", (D["no street word"],))
    conn.execute(v)
    try:
        assert any("street address" in p for p in check.views(conn, f"{SAMPLE_SCHEMA}.v_"))
    finally:
        conn.rollback()
    assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") == []


PRIVATE = re.compile(r"\b\w+_private\.")                     # a table in a private schema


class _Recording:
    """A connection that keeps every statement it is given."""

    def __init__(self, conn):
        self.conn, self.sql = conn, []

    def execute(self, q, *a, **kw):
        self.sql.append(str(q))
        return self.conn.execute(q, *a, **kw)


def test_the_reader_s_run_names_no_private_schema(filled):
    """The board runs the check bare, under the session reader, which has no grant on a _private schema."""
    rec = _Recording(filled["conn"])
    assert check.reading(rec, SAMPLE_SCHEMA, private=False) == []
    assert rec.sql and not any(PRIVATE.search(q) for q in rec.sql)
    rec = _Recording(filled["conn"])
    assert check.reading(rec, SAMPLE_SCHEMA) == []
    assert any(PRIVATE.search(q) for q in rec.sql)              # the owner's run still reads the twin itself
    rec = _Recording(filled["conn"])
    check.views(rec, f"{SAMPLE_SCHEMA}.v_")
    assert not any(PRIVATE.search(q) for q in rec.sql)


def test_the_private_count_matches_the_twin_and_goes_red(filled):
    conn = filled["conn"]
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    assert filled["read_statements"] == [{"statements": len(filled["investments"]), "stray": 0}]
    conn.execute(f"INSERT INTO {T('investments')} VALUES ('overseas_investment/decision/none', 'x', %s)", (SHA,))
    try:
        assert check.reading(conn, SAMPLE_SCHEMA, private=False) == []       # the count stands until the next load
        assert any("private table holds" in p for p in check.reading(conn, SAMPLE_SCHEMA))
        load.count_private(conn, SAMPLE_SCHEMA)
        assert "1 private statements with no decision" in check.reading(conn, SAMPLE_SCHEMA, private=False)
    finally:
        conn.rollback()
    for mutate in (f"DELETE FROM {T('read_statements')}", f"INSERT INTO {T('read_statements')} VALUES (0, 0)",
                   f"UPDATE {T('read_statements')} SET statements = 10000", f"DROP TABLE {T('read_statements')}"):
        conn.execute(mutate)
        try:
            assert check.reading(conn, SAMPLE_SCHEMA, private=False) != [], mutate
        finally:
            conn.rollback()
    assert check.reading(conn, SAMPLE_SCHEMA, private=False) == []


def test_the_listing_pages_read_their_pager(filled):
    from support.docstore.landing import read_bytes
    sha = next(i.split()[3] for i in filled["items"] if i.startswith("key: listing "))
    out = read.read_listing(read_bytes(sha))
    assert out["page"] == 0 and out["last_page"] == 1 and len(out["items"]) == 60
