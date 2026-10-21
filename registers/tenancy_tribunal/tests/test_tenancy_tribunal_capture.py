"""The capture on fakes (no network, no database, no clock): the listing is
asked for no name, address or text; each order is fetched once and landed by
hash; a block stops the run; a refusal is never caught; off-peak is held;
the position on file names the host; the check compares counts."""
import datetime as dt
import gzip
import hashlib
import json
import os
import re

import pytest

import support.fetchgate as fg
from registers.tenancy_tribunal import capture as C
from registers.tenancy_tribunal import check

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(LANE))
NIGHT = dt.datetime(2026, 10, 18, 23, 0, tzinfo=dt.timezone(dt.timedelta(hours=13)))
NOON = NIGHT.replace(hour=12)


def solr_doc(order_ids, published="2023-10-20", mbie=True, app="4608458"):
    orders = [json.dumps({"dateOfIssue": "13/10/2023", "orderId": o, "publishedOrderPdfName": f"{o}-Tribunal_Order.pdf",
                          "applicationId": app}) for o in order_ids]
    return {"id": f"{order_ids[0]}_x", "applicationNumber_s": [app], "publishedDate_dt": f"{published}T23:59:59.999Z",
            "unpublishedDate_s": ["2026-10-20 00:00:00.0"], "decisionDateIndex_l": 20231013,
            "orderDetailJson_s": orders, "tenancyMBIEOrder_txt": ["Yes" if mbie else "No"]}


def listing_bytes(docs, num_found=None, start=0):
    body = json.dumps({"responseHeader": {"status": 0}, "response": {
        "numFound": len(docs) if num_found is None else num_found, "start": start, "docs": docs}}).encode()
    return gzip.compress(body)


class FakeTables:
    def __init__(self):
        self.orders, self.listings, self.aside = {}, [], []

    def create(self):
        pass

    def listed_months(self):
        return {m for m, *_ in self.listings}

    def add_listing(self, month, num_found, rows_read, sha, url):
        self.listings.append((month, num_found, rows_read, sha, url))

    def upsert_orders(self, rows):
        for r in rows:
            self.orders.setdefault(r["order_id"], {**r, "document": None}).update(
                unpublished_date=r["unpublished_date"], listing=r["listing"])

    def pending(self, limit):
        skip = {i for i, s, _ in self.aside if s == "fetch"}
        rows = sorted((r for r in self.orders.values() if r["document"] is None and r["order_id"] not in skip),
                      key=lambda r: (r["unpublished_date"], r["published_date"], r["order_id"]))
        return [(r["order_id"], r["source_url"]) for r in rows[:limit]]

    def captured(self, order_id, sha):
        self.orders[order_id]["document"] = sha

    def set_aside(self, item, stage, reason):
        self.aside.append((item, stage, reason))


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
        self.names.append((name, name_kind, source))
        return Ref(sha), new


class FakeSite:
    """Answers like the Ministry's host: listings by month, PDFs by name."""

    def __init__(self, months, missing=(), blocked_after=None):
        self.months, self.missing, self.blocked_after, self.asked = months, set(missing), blocked_after, []

    def __call__(self, url, timeout=60, **kw):
        self.asked.append(url)
        if self.blocked_after is not None and len(self.asked) > self.blocked_after:
            return fg.Fetched(url, 429, b"", url, fg.looks_challenged(429, b""))
        if url.startswith(C.LISTING):
            q = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
            month = re.search(r"publishedDate_dt%3A%5B(\d{4}-\d{2})", q["q"]).group(1)
            return fg.Fetched(url, 200, listing_bytes(self.months.get(month, [])), url)
        name = url.rsplit("/", 1)[1]
        if name in self.missing:
            return fg.Fetched(url, 404, b"", url)
        return fg.Fetched(url, 200, b"%PDF-1.7 order " + name.encode(), url)


class NoWait:
    def wait(self, host, floor):
        self.last = (host, floor)
        return 0.0


def run(site, tables=None, store=None, now=NIGHT, **kw):
    tables, store = tables or FakeTables(), store or FakeStore()
    r = C.Run(tables, land_fn=store, opener=site, pacer=NoWait(), clock=lambda: 0.0, now_local=lambda: now,
              log=lambda *_: None, **kw)
    return r, tables, store


# ── the listing asks for nothing personal ────────────────────────────────────

def test_the_listing_asks_only_for_numbers_and_dates():
    url = C.listing_url(dt.date(2024, 2, 1))
    fl = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))["fl"]
    asked = set(fl.replace("%2C", ",").split(","))
    assert asked == set(C.FIELDS)
    for personal in ("casePerOrg", "Name", "tenancyAddress", "tenancySuburb", "tenancyStreet", "tenancyCity",
                     "document_text", "Applicant", "Respondent"):
        assert not any(personal.lower() in f.lower() for f in asked), personal
    assert "jurisdictionCode_s%3ATT" in url
    assert "2024-02-01T00%3A00%3A00Z+TO+2024-03-01T00%3A00%3A00Z%7D" in url     # the month, half-open


def test_no_table_has_a_column_for_a_name_or_an_address():
    sql = open(os.path.join(LANE, "tables.sql"), encoding="utf-8").read()
    cols = re.findall(r"^\s+([a-z_]+)\s+(?:text|date|integer|timestamptz|boolean)", sql, re.M)
    assert cols and not [c for c in cols if re.search(r"name|address|party|tenant|landlord|suburb|street", c)]


def test_an_order_row_carries_the_url_the_search_page_builds():
    mbie = C.order_rows(solr_doc(["111"], mbie=True), "a" * 64)[0]
    assert mbie["source_url"] == C.DOCUMENTS + "PDF/111-Tribunal_Order.pdf"
    plain = C.order_rows(solr_doc(["222"], mbie=False), "a" * 64)[0]
    assert plain["source_url"] == C.DOCUMENTS + "222.pdf"
    assert mbie["published_date"] == dt.date(2023, 10, 20) and mbie["decision_date"] == dt.date(2023, 10, 13)
    assert mbie["unpublished_date"] == dt.date(2026, 10, 20)
    assert len(C.order_rows(solr_doc(["1", "2"]), "a" * 64)) == 2      # one application, two orders


def test_the_window_is_thirty_seven_months_oldest_first():
    w = C.window(dt.date(2026, 10, 18))
    assert len(w) == 37 and w[0] == dt.date(2023, 10, 1) and w[-1] == dt.date(2026, 10, 1)
    again = C.months_to_list(dt.date(2026, 10, 18), set(w))
    assert again == [dt.date(2026, 9, 1), dt.date(2026, 10, 1)]     # the two still filling are listed every night


# ── a run ─────────────────────────────────────────────────────────────────────

def months_with(docs_by_month):
    return {m: docs for m, docs in docs_by_month.items()}


def test_a_run_lists_lands_each_order_once_and_a_second_run_fetches_nothing():
    site = FakeSite(months_with({"2023-10": [solr_doc(["1"]), solr_doc(["2", "3"])], "2026-10": [solr_doc(["9"], "2026-10-02")]}))
    r, t, store = run(site)
    out = r.run(dt.date(2026, 10, 18))
    assert out["landed"] == 4 and out["stopped"] == ""
    assert len(t.listings) == 37 and all(o["document"] for o in t.orders.values())
    assert {n for n, k, s in store.names if k == "url" and s == "tenancy_tribunal" and n.endswith(".pdf")} == \
        {o["source_url"] for o in t.orders.values()}
    pdfs = [u for u in site.asked if u.endswith(".pdf")]
    assert len(pdfs) == 4
    r2, _, _ = run(site, tables=t, store=store)
    out2 = r2.run(dt.date(2026, 10, 18))
    assert out2["landed"] == 0 and len([u for u in site.asked if u.endswith(".pdf")]) == 4    # cached: nothing twice
    assert len(site.asked) - 37 - 4 == 2                                   # only the two filling months again


def test_the_soonest_to_leave_is_fetched_first():
    old = solr_doc(["old"], "2023-10-20")
    new = solr_doc(["new"], "2026-10-02")
    new["unpublishedDate_s"] = ["2029-10-02 00:00:00.0"]
    site = FakeSite({"2023-10": [old], "2026-10": [new]})
    r, t, _ = run(site, max_items=1)
    r.run(dt.date(2026, 10, 18))
    assert t.orders["old"]["document"] and t.orders["new"]["document"] is None


def test_a_missing_order_is_set_aside_and_not_asked_again():
    site = FakeSite({"2023-10": [solr_doc(["1"]), solr_doc(["2"])]}, missing={"1-Tribunal_Order.pdf"})
    r, t, _ = run(site)
    out = r.run(dt.date(2026, 10, 18))
    assert out["landed"] == 1 and ("1", "fetch", "HTTP 404") in t.aside
    r2, _, _ = run(site, tables=t)
    r2.run(dt.date(2026, 10, 18))
    assert len([u for u in site.asked if u.endswith("1-Tribunal_Order.pdf")]) == 1


def test_a_block_stops_the_run_and_nothing_more_is_asked():
    site = FakeSite({"2023-10": [solr_doc([str(i)]) for i in range(10)]}, blocked_after=40)
    r, t, _ = run(site)
    out = r.run(dt.date(2026, 10, 18))
    assert out["stopped"].startswith("stopped: HTTP 429") and len(site.asked) == 41
    assert any(s == "fetch" and "hard limit 6" in why for _, s, why in t.aside)


def test_three_transport_failures_in_a_row_stop_the_run():
    calls = []

    def dead(url, timeout=60, **kw):
        calls.append(url)
        raise ConnectionResetError(104, "Connection reset by peer")
    r, t, _ = run(dead)
    out = r.run(dt.date(2026, 10, 18))
    assert len(calls) == 3 and "3 transport failures" in out["stopped"]


def test_a_gate_refusal_is_never_caught():
    def refuse(url, timeout=60, **kw):
        raise fg.Refused("no position")
    r, _, _ = run(refuse)
    with pytest.raises(fg.Refused):
        r.run(dt.date(2026, 10, 18))


def test_nothing_is_asked_outside_off_peak_unless_on_purpose():
    site = FakeSite({"2023-10": [solr_doc(["1"])]})
    r, _, _ = run(site, now=NOON)
    out = r.run(dt.date(2026, 10, 18))
    assert site.asked == [] and out["stopped"] == "off-peak is over"
    r2, _, _ = run(site, now=NOON, anytime=True)
    assert r2.run(dt.date(2026, 10, 18))["landed"] == 1


def test_the_budget_ends_the_run():
    site = FakeSite({"2023-10": [solr_doc([str(i)]) for i in range(5)]})
    ticks = iter(range(0, 10 ** 6, 100))
    r = C.Run(FakeTables(), land_fn=FakeStore(), opener=site, pacer=NoWait(), clock=lambda: next(ticks),
              now_local=lambda: NIGHT, budget_s=1000, log=lambda *_: None)
    out = r.run(dt.date(2026, 10, 18))
    assert out["stopped"] == "budget spent" and out["landed"] < 5


def test_the_lane_paces_at_its_floor():
    p = NoWait()
    r = C.Run(FakeTables(), land_fn=FakeStore(), opener=FakeSite({}), pacer=p, clock=lambda: 0.0,
              now_local=lambda: NIGHT, log=lambda *_: None)
    r.run(dt.date(2026, 10, 18), list_only=True)
    assert p.last == (C.HOST, C.FLOOR_S) and C.FLOOR_S >= 5.0


def test_a_listing_longer_than_one_page_is_paged():
    docs = [solr_doc([str(i)]) for i in range(5)]
    pages = []

    def site(url, timeout=60, **kw):
        q = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
        if url.startswith(C.LISTING):
            start = int(q["start"])
            pages.append(start)
            m = "2023-10" in q["q"]
            chunk = docs[start:start + 2] if m else []
            return fg.Fetched(url, 200, listing_bytes(chunk, 5 if m else 0, start), url)
        return fg.Fetched(url, 200, b"%PDF x" + url.encode(), url)
    r, t, _ = run(site)
    r.run(dt.date(2026, 10, 18), list_only=True)
    assert len(t.orders) == 5 and [l for l in t.listings if l[0] == dt.date(2023, 10, 1)][0][1:3] == (5, 5)


# ── the gate itself lets the lane through, and only under its position ──────

def test_the_position_on_file_names_the_host_and_the_gate_lets_the_lane_through(tmp_path, monkeypatch):
    positions = os.path.join(REPO, "docs", "legal", "positions")
    assert fg.position_for(C.HOST, positions) == "tenancy-tribunal-decisions"
    text = open(os.path.join(positions, "tenancy-tribunal-decisions.md"), encoding="utf-8").read()
    for q in ("Is the page open?", "Is storing it lawful copying?", "What terms did we accept?",
              "What does privacy law", "Crawl delay", "Floor we use"):
        assert q in text
    monkeypatch.setitem(fg._ROBOTS, C.HOST, fg.Robots(C.HOST, "", 0, True, 0.0, "2026-10-18T22:00:00+13:00", ""))
    slept = []
    f = fg.open_url(C.listing_url(dt.date(2024, 1, 1)), fetch=lambda u, t: (200, listing_bytes([]), u),
                    pacer=fg.Pacer(now=lambda: 0.0, sleep=slept.append), positions_dir=positions,
                    ledger_dir=str(tmp_path))
    assert f.status == 200 and not f.blocked
    rows = [json.loads(l) for l in open(next(tmp_path.iterdir()), encoding="utf-8")]
    assert rows[-1]["allowed"] and rows[-1]["position"] == "tenancy-tribunal-decisions" and rows[-1]["floor"] >= 5.0


# ── the check ─────────────────────────────────────────────────────────────────

def test_the_check_names_short_months_and_does_not_fault_the_window():
    a, b, c = dt.date(2023, 10, 1), dt.date(2024, 1, 1), dt.date(2026, 9, 1)
    out = check.compare({a: 10, b: 900, c: 850}, {a: 600, b: 900, c: 849})
    assert [r["month"] for r in out["equal"]] == [b]
    assert [r["month"] for r in out["short"]] == [c]
    assert [r["month"] for r in out["past_window"]] == [a]


def test_a_redirect_to_another_host_stops_the_run_and_lands_nothing():
    site = FakeSite({"2023-10": [solr_doc(["1"])]})

    def moved(url, timeout=60, **kw):
        f = site(url, timeout)
        # the gate returns a redirect off the host unfetched: the 3xx and its Location, final_url the URL asked
        return fg.Fetched(url, 302, b"", url, "", "https://elsewhere.example/x") if url.endswith(".pdf") else f
    r, t, store = run(moved)
    out = r.run(dt.date(2026, 10, 18))
    assert out["stopped"] == "stopped: redirected to elsewhere.example: not landed, and the run stops"
    assert not any(n.endswith(".pdf") for n, *_ in store.names) and t.orders["1"]["document"] is None


class FakeConn:
    def __init__(self, held):
        self.held, self.sql = held, []

    def execute(self, sql, params=()):
        self.sql.append((sql, params))
        return self

    def fetchone(self):
        return (not self.held,)


def test_one_run_of_the_lane_at_a_time():
    for held in (False, True):
        conn = FakeConn(held)
        assert C.Tables(conn).try_lock() is (not held)
        assert conn.sql == [("SELECT pg_try_advisory_lock(hashtext(%s))", (C.JOB,))]
