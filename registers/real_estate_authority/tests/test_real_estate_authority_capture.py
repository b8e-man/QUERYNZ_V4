"""The capture on fakes (no network, no database, no clock). The fake pages
copy the database's own markup (read 18 October 2026) with invented
placeholders for every name: a listing gives its count, its pages and ten
cases; an abstract links its PDFs. Each page and PDF is fetched once and
landed by hash; a block stops the run; a refusal is never caught; off-peak
is held; the position on file names the host; the check compares counts."""
import datetime as dt
import hashlib
import json
import os
import re
import urllib.parse

import pytest

import support.fetchgate as fg
from registers.real_estate_authority import capture as C
from registers.real_estate_authority import check

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(LANE))
NIGHT = dt.datetime(2026, 10, 18, 23, 0, tzinfo=dt.timezone(dt.timedelta(hours=13)))
TODAY = dt.date(2026, 10, 18)


def listing_page(year, page, cases, per=10):
    pages = max(1, -(-len(cases) // per))
    rows = cases[(page - 1) * per: page * per]
    blocks = "".join(
        '<div class="element ElementHTMLContent" id="e314"><div class="container dn-results">'
        '<div class="pure-g" style="margin-bottom: 0px"><div class="pure-u-md-1-3">\n\t\t\t\t<h4>'
        f'{when}</h4></div><div class="pure-u-md-2-3"><h3><A HREF="abstract.aspx?case={c}" '
        f'title="Complaints Assessment Committee Hearing Details" onClick="SdisplayX(\'abstract.aspx?case={c}\',\'\'); '
        f'return false;" target="_blank">Agent A</a></h3><p><strong>Unsatisfactory Conduct</strong> '
        f'<em>Other / Sales (Residential)</em> <A class="dnhide" HREF="abstract.aspx?case={c}" '
        'title="Complaints Assessment Committee Hearing Details">more</a></p></div></div></div></div>'
        for c, when in rows)
    return (f'<html><body><div id="e313"> Search Results ({len(cases)}) &nbsp;for "{year}" Page {page} of {pages}'
            f'</div>{blocks}</body></html>').encode()


def abstract_page(c, pdfs):
    links = "".join(f'<tr><td>Determination</td><td><a href="/reaa/pdfs/{p}">download</a></td></tr>' for p in pdfs)
    return (f'<html><h1 class="page-header">Decision</h1><h4 >DECISION</h4><p>No further action</p>'
            f'<h4 >COMPLAINT HISTORY</h4><table>{links}</table></html>').encode()


class FakeSite:
    def __init__(self, years, pdfs=None, missing=(), blocked_after=None):
        self.years, self.pdfs, self.missing, self.blocked_after, self.asked = years, pdfs or {}, set(missing), blocked_after, []

    def __call__(self, url, timeout=60, **kw):
        self.asked.append(url)
        if self.blocked_after is not None and len(self.asked) > self.blocked_after:
            body = b"<html><title>Just a moment...</title>cf-chl</html>"
            return fg.Fetched(url, 200, body, url, fg.looks_challenged(200, body))
        if url.startswith(C.LISTING):
            q = dict(urllib.parse.parse_qsl(url.split("?", 1)[1]))
            return fg.Fetched(url, 200, listing_page(int(q["qd1"]), int(q.get("pagesel", 1)),
                                                     self.years.get(int(q["qd1"]), [])), url)
        if "abstract.aspx" in url:
            c = int(url.rsplit("=", 1)[1])
            return fg.Fetched(url, 200, abstract_page(c, self.pdfs.get(c, [f"C{c}_Determination.pdf"])), url)
        name = url.rsplit("/", 1)[1]
        if name in self.missing:
            return fg.Fetched(url, 404, b"", url)
        return fg.Fetched(url, 200, b"%PDF-1.4 " + name.encode(), url)


class FakeTables:
    def __init__(self):
        self.cases, self.docs, self.listings, self.asides = {}, {}, [], []

    def create(self):
        pass

    def listed_years(self):
        return {l[0] for l in self.listings}

    def add_listing(self, year, page, num_found, pages, sha, url):
        self.listings.append((year, page, num_found, pages, sha, url))

    def upsert_cases(self, year, rows, sha):
        for c, when, body in rows:
            self.cases.setdefault(c, {"year": year, "when": when, "body": body, "abstract": None, "captured": False})

    def pending(self, limit):
        skip = {i for i, s, _ in self.asides if s == "abstract"}
        rows = sorted((c for c, r in self.cases.items() if not r["captured"] and str(c) not in skip),
                      key=lambda c: (self.cases[c]["body"] != C.AT_RISK_BODY, self.cases[c]["when"] or dt.date.max, c))
        return rows[:limit]

    def held_urls(self, case_id):
        return {u for (c, u) in self.docs if c == case_id}

    def add_document(self, case_id, url, number, sha):
        self.docs[(case_id, url)] = (number, sha)

    def captured(self, case_id, sha):
        self.cases[case_id].update(abstract=sha, captured=True)

    def set_aside(self, item, stage, reason):
        self.asides.append((str(item), stage, reason))


class Ref:
    def __init__(self, sha):
        self.sha256 = sha


class FakeStore:
    def __init__(self):
        self.held, self.names = {}, []

    def __call__(self, data, *, name, source, name_kind, content_type):
        sha = hashlib.sha256(data).hexdigest()
        new = sha not in self.held
        self.held[sha] = data
        self.names.append((name, name_kind, source, content_type))
        return Ref(sha), new


class NoWait:
    def wait(self, host, floor):
        self.last = (host, floor)
        return 0.0


def run(site, tables=None, store=None, now=NIGHT, **kw):
    tables, store = tables or FakeTables(), store or FakeStore()
    r = C.Run(tables, land_fn=store, opener=site, pacer=NoWait(), clock=lambda: 0.0, now_local=lambda: now,
              log=lambda *_: None, **kw)
    return r, tables, store


def cases(start, n, when="01 Sep 2015"):
    return [(start + i, when) for i in range(n)]


# ── the pages ─────────────────────────────────────────────────────────────────

def test_a_listing_page_gives_its_count_its_pages_and_its_cases():
    n, pages, rows = C.parse_listing(listing_page(2015, 1, cases(2000, 23)))
    assert (n, pages, len(rows)) == (23, 3, 10)
    assert rows[0] == (2000, dt.date(2015, 9, 1), "Complaints Assessment Committee Hearing")
    with pytest.raises(ValueError):
        C.parse_listing(b"<html>the front page</html>")


def test_the_listing_url_pages_the_way_the_form_does():
    q = dict(urllib.parse.parse_qsl(C.listing_url(2015, 3).split("?", 1)[1]))
    assert q == {"qd3": "during", "qd1": "2015", "Go": "Submit Search", "opgsize": "10", "Cpgs": "0", "Cpge": "9",
                 "pagesel": "3"}
    assert "pagesel" not in C.listing_url(2015, 1)


def test_an_abstract_gives_its_pdfs_and_their_complaint_numbers():
    links = C.pdf_links(abstract_page(63529, ["C62477_Determination.pdf", "C62477_Penalty.pdf"]))
    assert links == [f"https://{C.HOST}/reaa/pdfs/C62477_Determination.pdf", f"https://{C.HOST}/reaa/pdfs/C62477_Penalty.pdf"]
    assert C.complaint_number(links[0]) == "C62477"


def test_no_table_has_a_column_for_a_name_or_an_address():
    sql = open(os.path.join(LANE, "tables.sql"), encoding="utf-8").read()
    cols = re.findall(r"^\s+([a-z_]+)\s+(?:text|date|integer|timestamptz|boolean)", sql, re.M)
    assert cols and not [c for c in cols if re.search(r"name|address|licensee|agent|complainant|vendor|buyer", c)]


def test_years_from_2010_oldest_first_and_the_two_still_filling_every_night():
    assert C.years_to_list(TODAY, set())[0] == 2010 and C.years_to_list(TODAY, set())[-1] == 2026
    assert C.years_to_list(TODAY, set(range(2010, 2027))) == [2025, 2026]


# ── a run ─────────────────────────────────────────────────────────────────────

def test_a_run_lists_every_page_lands_each_case_once_and_a_second_run_fetches_nothing_new():
    site = FakeSite({2015: cases(2000, 12), 2026: cases(9000, 2, "01 Sep 2026")})
    r, t, store = run(site)
    out = r.run(TODAY)
    assert out["stopped"] == "" and out["cases"] == 14 and out["landed"] == 14
    assert all(c["captured"] and c["abstract"] for c in t.cases.values())
    assert len([u for u in site.asked if u.startswith(C.LISTING)]) == 17 + 1      # 2015 has two pages
    assert f"https://{C.HOST}/reaa/pdfs/C2000_Determination.pdf" in {n for n, *_ in store.names}
    assert {s for _, k, s, _ in store.names} == {"real_estate_authority"} and {k for _, k, _, _ in store.names} == {"url"}
    asked = len(site.asked)
    r2, _, _ = run(site, tables=t, store=store)
    out2 = r2.run(TODAY)
    assert out2["cases"] == 0 and len(site.asked) - asked == 2           # only the two filling years' first pages


def test_the_committee_s_oldest_is_fetched_first():
    site = FakeSite({2023: cases(100, 1, "01 Nov 2023"), 2026: cases(9000, 1, "01 Sep 2026")})
    r, t, _ = run(site, max_items=1)
    r.run(TODAY)
    assert t.cases[100]["captured"] and not t.cases[9000]["captured"]
    t.cases[50] = {"year": 2012, "when": dt.date(2012, 3, 1), "body": "Real Estate Agents Disciplinary Tribunal Hearing",
                   "abstract": None, "captured": False}
    assert t.pending(5) == [9000, 50]          # the Tribunal's, which stay, after every Committee decision


def test_a_missing_pdf_is_set_aside_and_the_case_still_held():
    site = FakeSite({2015: cases(2000, 1)}, missing={"C2000_Determination.pdf"})
    r, t, _ = run(site)
    r.run(TODAY)
    assert t.cases[2000]["captured"] and any(s == "pdf" and why == "HTTP 404" for _, s, why in t.asides)


def test_a_challenge_stops_the_run_and_nothing_more_is_asked():
    site = FakeSite({2015: cases(2000, 5)}, blocked_after=20)
    r, t, _ = run(site)
    out = r.run(TODAY)
    assert out["stopped"].startswith("stopped: a challenge page") and len(site.asked) == 21
    assert any("hard limit 6" in why for _, _, why in t.asides)


def test_a_gate_refusal_is_never_caught():
    def refuse(url, timeout=60, **kw):
        raise fg.Refused("no position")
    r, _, _ = run(refuse)
    with pytest.raises(fg.Refused):
        r.run(TODAY)


def test_nothing_is_asked_outside_off_peak_unless_on_purpose():
    site = FakeSite({2015: cases(2000, 1)})
    r, _, _ = run(site, now=NIGHT.replace(hour=14))
    assert r.run(TODAY)["stopped"] == "off-peak is over" and site.asked == []
    r2, _, _ = run(site, now=NIGHT.replace(hour=14), anytime=True)
    assert r2.run(TODAY)["cases"] == 1


def test_the_lane_paces_at_its_floor():
    p = NoWait()
    r = C.Run(FakeTables(), land_fn=FakeStore(), opener=FakeSite({}), pacer=p, clock=lambda: 0.0,
              now_local=lambda: NIGHT, log=lambda *_: None)
    r.run(TODAY, list_only=True)
    assert p.last == (C.HOST, C.FLOOR_S) and C.FLOOR_S >= 5.0


# ── the gate lets the lane through, and only under its position ─────────────

def test_the_position_on_file_names_the_host_and_the_gate_lets_the_lane_through(tmp_path, monkeypatch):
    positions = os.path.join(REPO, "docs", "legal", "positions")
    assert fg.position_for(C.HOST, positions) == "real-estate-authority-decisions"
    text = open(os.path.join(positions, "real-estate-authority-decisions.md"), encoding="utf-8").read()
    for q in ("Is the page open?", "Is storing it lawful copying?", "What terms did we accept?",
              "What does privacy law", "Crawl delay", "Floor we use"):
        assert q in text
    monkeypatch.setitem(fg._ROBOTS, C.HOST, fg.Robots(C.HOST, "User-agent: *\nDisallow: /\n", 200, False, 0.0,
                                                      "2026-10-18T22:00:00+13:00", ""))
    f = fg.open_url(C.listing_url(2015), fetch=lambda u, t: (200, listing_page(2015, 1, []), u),
                    pacer=fg.Pacer(now=lambda: 0.0, sleep=lambda s: None), positions_dir=positions,
                    ledger_dir=str(tmp_path))
    assert f.status == 200 and not f.blocked                     # robots says Disallow; ruling 10: not a permission
    rows = [json.loads(l) for l in open(next(tmp_path.iterdir()), encoding="utf-8")]
    assert rows[-1]["allowed"] and rows[-1]["position"] == "real-estate-authority-decisions"


# ── the check ─────────────────────────────────────────────────────────────────

def test_the_check_names_short_years_and_withdrawn_ones():
    out = check.compare({2015: 292, 2023: 84, 2026: 40}, {2015: 292, 2023: 80, 2026: 41})
    assert [r["year"] for r in out["equal"]] == [2015]
    assert [r["year"] for r in out["short"]] == [2023]
    assert [r["year"] for r in out["withdrawn"]] == [2026]
