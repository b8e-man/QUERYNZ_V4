"""The reading's rules on pages shaped like the FMA's (every name invented),
a mutant check of those rules, the capture's politeness on a fake transport,
and the filled sample (real pages, sample.list) against the row contract,
the ledger, withholding and the views. No model is called and nothing is
fetched."""
import datetime as dt
import os
import types

import pytest

from support import db, rowcontract, sample
from registers.fma import capture, check, load, read
from registers.fma import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = "e" * 64
SAMPLE_SCHEMA = "scratch_test_fma"


def _page(title, body, published="25 August 2026", description="The FMA warns about an invented business."):
    return ("<html><head><title>x | Financial Markets Authority</title>"
            f'<meta name="description" content="{description}"></head><body>'
            f'<div class="published"><span class="published__text">{published}</span></div>'
            f'<h1 class="registry-item-page__heading-wrap--title-item">{title}</h1>'
            f'<div class="registry-item-page__body-wrap-main"><p>SHARE THIS</p>{body}</div>'
            "<!--/Elemental Area Main Ends--></body></html>").encode()


def _listing(name, slugs, total=726):
    item = lambda s: ('<li class="search-results-semantic__result-item"><article><header>'
                      f'<h3><a href="{read.PATHS[name]}{s}/" target="_blank">{s.title()}</a></h3></header>'
                      '<footer><span class="search-results-semantic__date"> 1 October 2026 </span></footer></article></li>')
    return (f'<html><div class="results-list__result-count"><span class="results-list__count">{total}</span> results found'
            "</div>" + "".join(item(s) for s in slugs) + "</html>").encode()


TIMELINE = ('<h2>Timeline</h2><h3 class="regular">March 2026</h3><p>The court imposed an invented penalty.</p>'
            '<ul><li><strong>Related media release:</strong> <a href="/x/">x</a></li></ul>'
            "<p><strong>17 June 2026</strong></p><p>The FMA accepted an enforceable undertaking.</p>"
            "<p>Related media release: something</p><hr><h2>Background</h2><p>Older text.</p>")


def rules(mod) -> list:
    broken = []
    L = mod.read_listing(_listing("warnings", ["alpha-limited", "beta-scam"]), "warnings")
    if L["stated"] != 726 or [i["slug"] for i in L["items"]] != ["alpha-limited", "beta-scam"]:
        broken.append("a list's own count and its items are read in order")
    if L["items"] and L["items"][0]["card"] != "1 October 2026|Alpha-Limited":
        broken.append("an item's fingerprint is its date and title as listed")

    w = mod.read_page(_page("Alpha Limited – Suspected scam",
                            "<p>The FMA is concerned that Beta Holdings Ltd (NZBN: 9429000000002) is offering shares, in breach "
                            "of section 22 of the Financial Markets Conduct Act 2013 and the Financial Markets Conduct Act.</p>"
                            "<p><strong>Entity Name:&nbsp;</strong>Alpha Limited; Beta Holdings Ltd<br>"
                            "<strong>Address:&nbsp;</strong>12 Invented Street, Town<br>"
                            "<strong>Website:&nbsp;</strong>alpha.example</p>"), SHA, "warnings", "alpha-limited")
    a, ps = w["action"], w["parties"]
    if not a or a["key"] != "fma/warning/alpha-limited" or a["kind"] != "warning" or a["published_on"] != dt.date(2026, 8, 25):
        broken.append("the key is the slug; the kind and the date published")
    if [(p["name"], p["named_in"], p["split_from"]) for p in ps] != [
            ("Alpha Limited", "field: Entity Name", "semicolon"), ("Beta Holdings Ltd", "field: Entity Name", "semicolon")]:
        broken.append("each value of a party field, split on ';'; the address field never")
    if len(ps) == 2 and (ps[1]["company_number"] != "9429000000002" or ps[0]["company_number"] is not None):
        broken.append("a company number only where printed beside the name")
    if a and (a["acts"] != ["Financial Markets Conduct Act 2013"]
              or a["sections"] != ["section 22 of the Financial Markets Conduct Act 2013"]):
        broken.append("each Act by title once; each section as stated")
    if a and a["summary"] != "The FMA warns about an invented business.":
        broken.append("the FMA's own summary")

    d = mod.read_page(_page("Gamma Traders Limited – Fake offers", "<p>Text.</p>"), SHA, "warnings", "gamma")["parties"]
    e = mod.read_page(_page("Delta Corporation", "<p>WARNING: an offer.</p>"), SHA, "warnings", "delta")["parties"]
    t = mod.read_page(_page("Invented scams target investors", "<p>Text.</p>"), SHA, "warnings", "topic")
    if [(p["name"], p["named_in"]) for p in d] != [("Gamma Traders Limited", "heading, before its dash")]:
        broken.append("no field: the heading before its dash")
    if [(p["name"], p["named_in"]) for p in e] != [("Delta Corporation", "heading")]:
        broken.append("no field, no dash: the heading when it ends in a legal ending")
    if t["parties"] or not t["action"]["names_nobody"]:
        broken.append("a topic alert names nobody")

    c = mod.read_page(_page("Epsilon Limited and Zeta Ltd", TIMELINE), SHA, "enforcement", "epsilon")
    c2 = mod.read_page(_page("Eta Person and Theta Limited", TIMELINE), SHA, "enforcement", "eta")
    if [p["name"] for p in c["parties"]] != ["Epsilon Limited", "Zeta Ltd"] or len(c2["parties"]) != 1:
        broken.append("a case's heading split on ' and ' only between two legal names")
    ca = c["action"]
    if not ca or ca["key"] != "fma/enforcement/epsilon" or ca["outcome"] != "The FMA accepted an enforceable undertaking." \
            or ca["outcome_on"] != dt.date(2026, 6, 17) or ca["outcome_when"] != "17 June 2026":
        broken.append("the outcome is the latest timeline entry, without its 'Related' lines")
    m = mod.read_page(_page("Iota Limited", TIMELINE.replace("<p><strong>17 June 2026</strong></p>",
                                                              "<p><strong>17 June 2025</strong></p>")), SHA, "enforcement", "iota")
    if m["action"]["outcome_when"] != "March 2026" or m["action"]["outcome_on"] is not None:
        broken.append("a month is never made a day")

    h = mod.read_page(_page("Kappa – warning", "<p><strong>Entity Name:</strong> Withheld</p>"), SHA, "warnings", "kappa")
    if not (h["parties"] and h["parties"][0]["withheld"] and h["parties"][0]["name"] is None):
        broken.append("a name the FMA withholds is withheld")
    s = mod.read_page(_page("Invented Person and Lambda Limited", "<p>A court order of name suppression applies.</p>" + TIMELINE),
                      SHA, "enforcement", "invented-person")
    sp = s["parties"]
    if not (len(sp) == 1 and sp[0]["withheld"] and sp[0]["name"] is None):
        broken.append("a stated suppression withholds a party with no organisation word")
    o = mod.read_page(_page("Mu Limited", "<p>Name suppression applies to an employee.</p>"), SHA, "enforcement", "mu")
    if o["parties"][0]["withheld"]:
        broken.append("a stated suppression leaves an organisation named")
    sa = s["action"]
    if not (sa["title"] is None and sa["url"] is None and sa["slug"] is None and sa["summary"] is None
            and sa["outcome"] is None and "invented" not in sa["key"] and all("invented" not in p["key"] for p in sp)):
        broken.append("a suppression withholds the heading, address, slug, summary, outcome and a key made from them")
    again = mod.read_page(_page("Invented Person and Lambda Limited", "<p>Name suppression.</p>"), "d" * 64,
                          "enforcement", "invented-person")
    if again["action"]["key"] != sa["key"]:
        broken.append("the withheld key is the same across re-reads")

    for bad in (b"<html><title>Just a moment...</title></html>", b"<html><title>Page not found</title><h1>Gone</h1></html>"):
        if mod.read_page(bad, SHA, "warnings", "x")["action"] is not None:
            broken.append("a page not of the item's shape is set aside whole")
    try:
        mod.read_listing(b"<html><title>Page not found</title></html>", "warnings")
        broken.append("a page not of the listing's shape is refused")
    except ValueError:
        pass
    return broken


def test_every_rule_holds():
    assert rules(read) == []


MUTANTS = {
    "the address field read as a party": ("if clean(label).lower() not in PARTY_FIELDS:", "if False:"),
    "a field's ';' not split": ('values = [v.strip() for v in clean(value).split(";") if v.strip()]',
                                "values = [clean(value)]"),
    "the heading's dash ignored": ("if len(parts) == 2 and parts[0].strip():", "if False:"),
    "every heading a party": ('    if LEGAL_ENDING.search(title):\n        return [(n, "heading", how)',
                              '    if True:\n        return [(n, "heading", how)'),
    "' and ' split everywhere": ("if len(bits) == 2 and all(LEGAL_ENDING.search(b) for b in bits):", "if len(bits) == 2:"),
    "a stated suppression ignored": ('else "the page states a suppression" if states_suppression', 'else None if True'),
    "a suppression withholds companies too": ("states_suppression and not (org and not _AND.search(name))",
                                              "states_suppression"),
    "a joined name kept on a suppression": ("states_suppression and not (org and not _AND.search(name))",
                                            "states_suppression and not org"),
    "the summary kept on a suppression": ('"summary": None if suppressed or not desc else', '"summary": None if not desc else'),
    "the outcome kept on a suppression": ('"outcome": None if suppressed else outcome', '"outcome": outcome'),
    "a month made a day": ('    for fmt in ("%d %B %Y", "%d %b %Y"):', '    for fmt in ("%d %B %Y", "%d %b %Y", "%B %Y"):'),
    "the earliest entry taken": ("if best is None or order > best[0]:", "if best is None or order < best[0]:"),
    "'Related' lines kept": ('if x and not x.lower().startswith("related")', "if x"),
    "a yearless Act title kept beside its dated one": (
        'return [a for a in out if re.search(r"\\d{4}$", a) or not any(b.startswith(a + " ") for b in out)]', "return out"),
    "any page read as an item": ("    if not _H1.search(t) or _BODY_START not in t or _BODY_END not in t:\n", "    if False:\n"),
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
        self.p, self.listed, self.items, self.asides, self.finished = {}, {}, {}, [], set()

    def open_pass(self, name):
        return None if name in self.finished else self.p.get(name)

    def last_finished(self, name):
        return None

    def begin(self, name):
        self.p[name] = {"pass_id": len(self.p) + 1, "list": name, "stated": None, "next_page": 1, "pages": 0, "items": 0}
        return self.p[name]

    def add_page(self, p, n, url, sha, items, stated):
        self.listed.setdefault(p["list"], []).extend((i["slug"], i["url"], i["card"]) for i in items)
        p.update(next_page=n + 1, pages=p["pages"] + 1, items=len(self.listed[p["list"]]), stated=p["stated"] or stated)

    def finish(self, p):
        self.finished.add(p["list"])

    def pending(self, name, limit):
        return [r for r in self.listed.get(name, []) if self.items.get((name, r[0])) != r[2]][:limit]

    def add_item(self, name, slug, url, card, sha):
        self.items[(name, slug)] = card

    def docs_due(self, days):
        return False

    def add_doc(self, *a):
        pass

    def set_aside(self, pass_id, item, stage, reason):
        self.asides.append((stage, reason))


def _run(answers):
    t, clock, asked = FakeTables(), [0.0], []
    pages = {"warnings": _listing("warnings", ["a", "b"], total=2), "enforcement": _listing("enforcement", ["c"], total=1)}

    def opener(url, timeout):
        asked.append(url)
        clock[0] += 0.1
        a = answers.pop(0) if answers else 200
        if isinstance(a, Exception):
            raise a
        name = next((n for n, p in read.PATHS.items() if url.endswith(p) or "?start=" in url and p in url), None)
        body = pages[name] if name else _page("Invented Limited", "<p>x</p>")
        return types.SimpleNamespace(url=url, status=a, body=body if a == 200 else b"<html>error</html>",
                                     final_url=url, blocked="HTTP 429: a block" if a in (403, 429) else "")

    run = capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="a" * 64), True), opener=opener,
                      clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                      now=lambda: dt.datetime(2026, 10, 22, 23, 0, tzinfo=capture.NZ), docs={})
    return run.run(), t, asked, clock


def test_both_lists_are_walked_and_every_item_fetched_once():
    out, t, asked, clock = _run([])
    assert not out["stopped"] and set(t.items) == {("warnings", "a"), ("warnings", "b"), ("enforcement", "c")}
    assert len(asked) == len(set(asked)) == 5 and clock[0] >= 4 * capture.FLOOR_S


def test_a_block_stops_the_run():
    out, t, asked, clock = _run([200, 200, 429])
    assert out["stopped"].startswith("stopped:") and len(asked) == 3 and len(t.items) == 0


def test_a_server_error_and_a_reset_are_failed_reads_and_the_run_goes_on():
    out, t, asked, clock = _run([200, 200, 503, ConnectionResetError("reset"), 200])
    assert not out["stopped"] and set(t.items) == {("enforcement", "c")} and len(t.asides) == 2
    assert clock[0] >= capture.REST_S


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
               "actions_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_fma_actions"),
               "parties_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_fma_parties")}


def test_every_listed_item_is_an_action(filled):
    assert len(filled["actions"]) == 12 and not filled["read_set_aside"]
    assert {r["state"] for r in filled["read_items"]} == {"read"}


def test_every_row_meets_the_row_contract(filled):
    for r in filled["actions"] + filled["parties"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


#: the sample's hard cases by their documents (sample.list says what each is; no slug, which can carry a name, in git)
D = {"entity field, NZBN": "dfa61d31de562e1825176adb33bbf5a6b83ecacfafb9b2637ac7dde49df51da0",
     "topic alert": "0d9c42eb78c088e3656e451730a5bbb2836c0b6bea4788700474a7f3ad685e70",
     "2010 heading alone": "97560f91579ae03f48670a36f255b8adf0ca53fecc8683d3274d32e174b1856a",
     "2010 Securities Act": "f8cb3ac212eb160b626d111089a5fb3c19fa27a86df40fe2354dea3e1bcd272c",
     "dated by day": "2c9d83104cb417a1071fcf647756f5cc4ba5a57be613b2aa164dac9f0a808a3a",
     "dated by month, a person": "ef4b793f7f5bdd7e312be4cf6ea1e46e5ba05a990c1871586144c3791572c623",
     "yearless and dated Act": "752a118c00b492c5f22facba41eee1b2abc1c39f4c77832684d3e5f2e85c198d"}


def test_the_hard_cases_read_as_the_fma_publishes_them(filled):
    by = {r["document"]: r for r in filled["actions"]}
    parties = {}
    for p in filled["parties"]:
        parties.setdefault(p["document"], []).append(p)
    bal = parties[D["entity field, NZBN"]]
    assert [(p["named_in"], p["company_number"] is not None) for p in bal] == [("field: Entity Name", True)]
    assert by[D["topic alert"]]["names_nobody"] and D["topic alert"] not in parties
    assert [p["named_in"] for p in parties[D["2010 heading alone"]]] == ["heading"]
    assert by[D["2010 Securities Act"]]["acts"] == ["Securities Act 1978"]
    assert by[D["dated by day"]]["outcome_on"] == dt.date(2026, 6, 17)
    mc = by[D["dated by month, a person"]]
    assert mc["outcome_when"] == "March 2026" and mc["outcome_on"] is None and mc["outcome"]
    assert [p["organisation"] for p in parties[D["dated by month, a person"]]] == [False]
    assert by[D["yearless and dated Act"]]["acts"] == ["Financial Markets Conduct Act 2013"]


def test_the_views_withhold_and_the_check_is_clean(filled):
    assert all(r["name"] != "name withheld" for r in filled["parties_view"] if not r["withheld"])
    assert check.views(filled["conn"], f"{SAMPLE_SCHEMA}.v_") == []
    assert check.reading(filled["conn"], SAMPLE_SCHEMA) == []


def test_the_check_goes_red_on_a_name_shown_or_a_broken_ledger(filled):
    conn = filled["conn"]
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    conn.execute(f"UPDATE {T('read_items')} SET parties = parties + 1 WHERE document = %s", (D["dated by day"],))
    try:
        assert check.reading(conn, SAMPLE_SCHEMA) != []
    finally:
        conn.rollback()
    conn.execute(f"UPDATE {T('parties')} SET withheld = true, withheld_by = 'the page states a suppression' "
                 "WHERE document = %s", (D["dated by month, a person"],))
    try:
        assert check.reading(conn, SAMPLE_SCHEMA) != []          # the name is still in the table
        assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") != []    # and the heading, address and outcome on the view
    finally:
        conn.rollback()
    conn.execute(f"UPDATE {T('actions')} SET summary = 'Office at 12 Invented Street, Town' WHERE document = %s",
                 (D["dated by day"],))
    try:
        assert any("street address" in p for p in check.views(conn, f"{SAMPLE_SCHEMA}.v_"))
    finally:
        conn.rollback()
    assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") == []


def test_the_listing_pages_read_their_own_counts(filled):
    from support.docstore.landing import read_bytes
    got = {}
    for i in filled["items"]:
        if i.startswith("key: listing "):
            _, _, name, sha = i.split()
            out = read.read_listing(read_bytes(sha), name)
            got.setdefault(name, set()).add((out["stated"], len(out["items"])))
    assert got == {"warnings": {(726, 15), (726, 6)}, "enforcement": {(99, 15)}}
