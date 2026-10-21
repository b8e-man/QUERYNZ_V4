"""The reading's rules on pages shaped like the Commission's (every name
invented), a mutant check of those rules, the capture's politeness on a fake
transport, and the filled sample (real pages, sample.list) against the row
contract, the ledger, withholding and the views. No model is called and
nothing is fetched."""
import datetime as dt
import os
import types

import pytest

from support import db, rowcontract, sample
from registers.commerce_commission import capture, check, load, read
from registers.commerce_commission import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = "e" * 64
SAMPLE_SCHEMA = "scratch_test_commerce_commission"


def _entry(parties, act="Fair Trading Act 1986 s 30(1)", number="PRJ0000001", opened="09 June 2026",
           closed="19 October 2026", summary="Investigation into an invented trader.", heading=None):
    rec = lambda k, v: (f'<div class="case-details__record"><div class="case-details__record-title"> {k} </div>'
                        f'<div class="case-details__record-value"> {v} </div></div>')
    return ("<html><head><title>x | Commerce Commission</title></head><body><main>"
            f"<h1>{heading or parties}</h1><div class='content-block__content'><p>{summary}</p></div>"
            '<h2 class="h5">Case Details</h2>\n<div class="case-details">'
            + rec("Parties", parties) + rec("Category", "Consumer") + rec("Sub-category", "")
            + rec("Act/Section/Part", act) + rec("Industry", "Retail") + rec("Status", "Closed")
            + rec("Outcome", "Warning") + rec("Case number", number) + rec("Date opened", opened)
            + rec("Date closed", closed) + rec("Contact person", "Staff Member, staff@example.invalid")
            + "</div>\n<project-block></project-block></main></body></html>").encode()


def _listing(cards, total=1727):
    card = lambda slug, title, status, outcome: (
        '<li><div class="card card--has-link"><div class="card__status card__status--' + status + '">x</div>'
        f'<a class="card__link" href="/case-register/case-register-entries/{slug}/" > {title} </a>'
        '<div class="card__info-detail"><span class="card__info-title">Outcome:</span><span> ' + outcome + '</span></div>'
        '<div class="card__tag"> Consumer </div></div></li>')
    return (f'<html><x-list :total="{total}" :results-count="100"></x-list>'
            + "".join(card(*c) for c in cards) + "</html>").encode()


def rules(mod) -> list:
    broken = []
    L = mod.read_listing(_listing([("alpha-traders-limited", "Alpha Traders Limited", "closed", "Warning"),
                                   ("withheld-3", "Withheld", "open", "")]))
    if L["stated"] != 1727 or [i["slug"] for i in L["items"]] != ["alpha-traders-limited", "withheld-3"]:
        broken.append("the listing's own total and its cards are read in order")
    if L["items"] and L["items"][0]["card"] != "closed|Warning||Consumer":
        broken.append("a card's fingerprint is its status, outcome, date closed and tag")

    a = mod.read_entry(_entry("Alpha Traders Ltd t/a Alpha Toys, Alpha Games; Beta Holdings Limited (NZBN: 9429000000001)",
                              act="Fair Trading Act 1986 s 9; Credit Contracts and Consumer Finance Act 2003 ss 9C, 17"),
                       SHA, "alpha-traders-limited")
    c, ps = a["case"], a["parties"]
    if not c or c["key"] != "commerce_commission/case/alpha-traders-limited" or c["case_number"] != "PRJ0000001":
        broken.append("the key is the entry's slug; the case number as stated")
    if c and (c["acts"] != ["Fair Trading Act 1986", "Credit Contracts and Consumer Finance Act 2003"]
              or c["sections"] != ["s 9", "ss 9C, 17"]):
        broken.append("each Act stated and its sections")
    if c and (c["opened_on"] != dt.date(2026, 6, 9) or c["action_on"] != dt.date(2026, 10, 19)):
        broken.append("the dates as stated; the action's date is the closing date")
    if [(p["name"], p["trading_as"], p["split_from"]) for p in ps] != [
            ("Alpha Traders Ltd", "Alpha Toys, Alpha Games", "semicolon"), ("Beta Holdings Limited", None, "semicolon")]:
        broken.append("parties split on '; ', a trading name kept beside its party")
    if len(ps) == 2 and (ps[1]["company_number"] != "9429000000001" or ps[0]["company_number"] is not None):
        broken.append("a company number only where printed beside the name")

    j = mod.read_entry(_entry("Gamma Limited and Delta Ltd"), SHA, "gamma")["parties"]
    k = mod.read_entry(_entry("Gamma Limited and Invented Person"), SHA, "gamma2")["parties"]
    if [p["name"] for p in j] != ["Gamma Limited", "Delta Ltd"] or [p["name"] for p in k] != ["Gamma Limited and Invented Person"]:
        broken.append("' and ' splits only between two legal names")

    w = mod.read_entry(_entry("Withheld"), SHA, "withheld-3")
    if not (w["case"]["title_withheld"] and w["case"]["title"] is None and w["parties"][0]["withheld"]
            and w["parties"][0]["name"] is None):
        broken.append("'Withheld' is withheld, never a name")

    s = mod.read_entry(_entry("Epsilon Limited; Invented Person; Omicron Limited and Invented Other",
                              summary="Name suppression continues for one party."),
                       SHA, "epsilon-limited-and-invented-person")
    sp = {p["ordinal"]: p for p in s["parties"]}
    if not (sp.get(3) and sp[3]["withheld"] and sp[3]["name"] is None):
        broken.append("a stated suppression withholds a name joined to an organisation's")
    if not (sp.get(2) and sp[2]["withheld"] and sp[2]["name"] is None):
        broken.append("a stated suppression withholds a party with no organisation word")
    if not (sp.get(1) and not sp[1]["withheld"] and sp[1]["name"] == "Epsilon Limited"):
        broken.append("a stated suppression leaves an organisation named")
    sc = s["case"]
    if not (sc and sc["title"] is None and sc["url"] is None and sc["slug"] is None
            and "invented" not in sc["key"] and all("invented" not in p["key"] for p in s["parties"])):
        broken.append("a suppression withholds the heading, the address, the slug and a key made from them")
    again = mod.read_entry(_entry("Epsilon Limited; Invented Person", summary="Name suppression continues."), "d" * 64,
                           "epsilon-limited-and-invented-person")
    if sc and again["case"]["key"] != sc["key"]:
        broken.append("the withheld key is the same across re-reads")

    bad = mod.read_entry(b"<html><title>Just a moment...</title></html>", SHA, "x")
    gone = mod.read_entry(b"<html><title>Page not found</title><h1>Page not found</h1></html>", SHA, "y")
    if bad["case"] is not None or len(bad["set_aside"]) != 1 or gone["case"] is not None:
        broken.append("a page not of the entry's shape is set aside whole")
    try:
        mod.read_listing(b"<html><title>Page not found</title></html>")
        broken.append("a page not of the listing's shape is refused")
    except ValueError:
        pass
    return broken


def test_every_rule_holds():
    assert rules(read) == []


MUTANTS = {
    "'Withheld' kept as a name": ('withheld_by = ("the Commission withholds the name" if WITHHELD.match(name)',
                                  'withheld_by = ("the Commission withholds the name" if False'),
    "a stated suppression ignored": ('else "the page states a suppression" if states_suppression', 'else None if True'),
    "a suppression withholds companies too": ("states_suppression and not (org and not _AND.search(name))",
                                              "states_suppression"),
    "a joined name kept on a suppression": ("states_suppression and not (org and not _AND.search(name))",
                                            "states_suppression and not org"),
    "' and ' split everywhere": ("if len(bits) == 2 and all(LEGAL_ENDING.search(b) for b in bits)", "if len(bits) == 2"),
    "'; ' not split": ('parts = [p.strip() for p in field.split(";") if p.strip()]', "parts = [field]"),
    "the heading kept on a suppression": ("title_withheld = bool(WITHHELD.match(title)) or suppressed",
                                          "title_withheld = bool(WITHHELD.match(title))"),
    "the address kept on a suppression": ('"url": None if suppressed else', '"url": None if False else'),
    "the key from the slug on a suppression": ('if suppressed else f"{KEY_PREFIX}/{slug}"', 'if False else f"{KEY_PREFIX}/{slug}"'),
    "Acts not split": ("end = found[i + 1].start() if i + 1 < len(found) else len(text)", "end = len(text)"),
    "the action dated by its opening": ('"action_on": closed or opened', '"action_on": opened'),
    "any page read as an entry": ("    if not _DETAILS.search(t):\n", "    if False:\n"),
    "the trading name left in the name": ('name, trading = (_TA.split(name, maxsplit=1) + [""])[:2]', 'trading = ""'),
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
        self.p, self.listed, self.items, self.asides, self.docs, self.finished = None, [], {}, [], [], False

    def open_pass(self, name):
        return None if self.finished else self.p

    def last_finished(self, name):
        return None

    def begin(self, name):
        self.p = {"pass_id": 1, "list": name, "stated": None, "next_page": 1, "pages": 0, "items": 0}
        return self.p

    def add_page(self, p, n, url, sha, items, stated):
        self.listed += [(i["slug"], i["url"], i["card"]) for i in items]
        p.update(next_page=n + 1, pages=p["pages"] + 1, items=len(self.listed), stated=p["stated"] or stated)

    def finish(self, p):
        self.finished = True

    def pending(self, name, limit):
        return [r for r in self.listed if self.items.get(r[0]) != r[2]][:limit]

    def add_item(self, name, slug, url, card, sha):
        self.items[slug] = card

    def docs_due(self, days):
        return False

    def add_doc(self, *a):
        self.docs.append(a)

    def set_aside(self, pass_id, item, stage, reason):
        self.asides.append((stage, reason))


def _run(answers, cards):
    t, clock, asked = FakeTables(), [0.0], []
    listing = _listing([(s, s, "closed", "Warning") for s in cards], total=len(cards))

    def opener(url, timeout):
        asked.append(url)
        clock[0] += 0.1
        a = answers.pop(0) if answers else 200
        if isinstance(a, Exception):
            raise a
        body = listing if "page=" in url else (b"<html><title>Just a moment...</title></html>" if a == "shape"
                                               else _entry("Invented Limited"))
        st = 200 if a == "shape" else a
        return types.SimpleNamespace(url=url, status=st, body=body if st == 200 else b"<html>error</html>",
                                     final_url=url, blocked="HTTP 403: a block" if st in (403, 429) else "")

    run = capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="a" * 64), True), opener=opener,
                      clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                      now=lambda: dt.datetime(2026, 10, 22, 23, 0, tzinfo=capture.NZ), docs={})
    return run, run.run(), t, asked, clock


def test_a_block_stops_the_run():
    run, out, t, asked, clock = _run([200, 200, 403], ["a", "b", "c", "d"])
    assert out["stopped"].startswith("stopped:") and len(asked) == 3 and t.items == {"a": "closed|Warning||Consumer"}
    assert clock[0] >= 2 * capture.FLOOR_S and capture.outcome(out)[0]      # a polite stop after landing is green


def test_a_server_error_and_a_timeout_are_failed_reads_and_the_run_goes_on():
    run, out, t, asked, clock = _run([200, 500, TimeoutError("slow"), 200, 200], ["a", "b", "c", "d"])
    assert not out["stopped"] and set(t.items) == {"c", "d"}
    assert [s for s, _ in t.asides] == ["fetch", "fetch"] and clock[0] >= capture.REST_S


def test_three_failed_reads_in_a_row_stop_the_run():
    run, out, t, asked, clock = _run([200, 502, 503, ConnectionResetError("reset")], ["a", "b", "c", "d"])
    assert out["stopped"].startswith("stopped:") and "3 failed reads" in out["stopped"] and not t.items


def test_a_page_not_of_the_entry_shape_is_not_landed():
    run, out, t, asked, clock = _run([200, "shape", 200], ["a", "b"])
    assert set(t.items) == {"b"} and t.asides[0][0] == "item"


def test_off_peak_only_unless_asked():
    t = FakeTables()
    run = capture.Run(t, land_fn=None, opener=lambda u, s: pytest.fail("asked during the day"), docs={},
                      now=lambda: dt.datetime(2026, 10, 22, 14, 0, tzinfo=capture.NZ))
    assert run.run()["stopped"] == "off-peak is over"


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
               "cases_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_commerce_commission_cases"),
               "parties_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_commerce_commission_parties")}


def test_every_listed_entry_is_a_case(filled):
    assert len(filled["cases"]) == 7 and not filled["read_set_aside"]
    assert {r["state"] for r in filled["read_items"]} == {"read"}


def test_every_row_meets_the_row_contract(filled):
    for r in filled["cases"] + filled["parties"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


#: the sample's hard cases by their documents (sample.list says what each is; no slug, which can carry a name, in git)
D = {"t/a": "7a856cab217f4c5ac0223742008e78a3754e972888f68669d51503541681c52b",
     "withheld": "bd51025bf38c7148cbf0d053c8b652548fe92dd4b1122caaf50d508c83147124",
     "open, a company and a person": "c666357eaec909a784eb61ef33e3d25ec98a7a7c63fd1b1b3752483189bc6ee6",
     "three parties unseparated": "502f2439f2b2b8cc54c2f20772eb677b0c119596313419eaef15ba7c952224c0",
     "a judgment": "f220adec16b8f0d398fa67d9dd2ee749635663dc8e346142f1ad10f0cbebe31c",
     "1991": "3ef10244f033fb40c1ab3286728ab6daa661559c98f36a86e13436826a9e4708",
     "plain": "7563dcb6d8ba06f36ede4df96bf500ac4ede3a87c53e1ec2d0ff09156e0a287e"}


def test_the_hard_cases_read_as_the_register_says(filled):
    by = {r["document"]: r for r in filled["cases"]}
    parties = {}
    for p in filled["parties"]:
        parties.setdefault(p["document"], []).append(p)
    assert by[D["withheld"]]["title"] is None and all(p["withheld"] and p["name"] is None for p in parties[D["withheld"]])
    sky = by[D["open, a company and a person"]]
    assert sky["acts"] == ["Credit Contracts and Consumer Finance Act 2003"] and sky["status"] == "Open"
    assert [p["split_from"] for p in parties[D["open, a company and a person"]]] == ["semicolon", "semicolon"]
    assert [p["organisation"] for p in parties[D["open, a company and a person"]]] == [True, False]
    assert by[D["t/a"]]["sections"] == ["s 30(1)"]
    assert [p["trading_as"] is not None for p in parties[D["t/a"]]] == [True]
    assert by[D["1991"]]["case_number"] is None
    assert by[D["a judgment"]]["case_number"] == "[2021] NZHC 2279"
    moh = parties[D["three parties unseparated"]]
    assert len(moh) == 2 and moh[1]["split_from"] == "and between two legal names"


def test_the_views_withhold_and_the_check_is_clean(filled):
    held = [r for r in filled["parties_view"] if r["withheld"]]
    assert held and all(r["name"] == "name withheld" for r in held)
    assert check.views(filled["conn"], f"{SAMPLE_SCHEMA}.v_") == []
    assert check.reading(filled["conn"], SAMPLE_SCHEMA) == []


def test_the_check_goes_red_on_a_name_shown_or_a_broken_ledger(filled):
    conn = filled["conn"]
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    conn.execute(f"UPDATE {T('read_items')} SET parties = parties + 1 WHERE document = %s", (D["t/a"],))
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
    conn.execute(f"UPDATE {T('cases')} SET outcome = '12 Invented Street, Town' WHERE document = %s", (D["plain"],))
    conn.execute(v)
    try:
        assert any("street address" in p for p in check.views(conn, f"{SAMPLE_SCHEMA}.v_"))
    finally:
        conn.rollback()
    assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") == []


def test_the_listing_page_reads_its_own_total(filled):
    from support.docstore.landing import read_bytes
    sha = next(i.split()[3] for i in filled["items"] if i.startswith("key: listing "))
    out = read.read_listing(read_bytes(sha))
    assert out["stated"] == 1727 and len(out["items"]) == 100 and len({i["slug"] for i in out["items"]}) == 100
