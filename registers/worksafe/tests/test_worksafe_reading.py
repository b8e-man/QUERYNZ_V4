"""The reading's rules on pages shaped like WorkSafe's (every name invented),
a mutant check of those rules, the capture's politeness on a fake transport,
and the filled sample (real pages, sample.list) against the row contract,
the ledger, withholding and the views. No model is called and nothing is
fetched."""
import datetime as dt
import os
import types

import pytest

from support import db, rowcontract, sample
from registers.worksafe import capture, check, load, read
from registers.worksafe import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = "e" * 64
SAMPLE_SCHEMA = "scratch_test_worksafe"


def _summary(defendant, section="Sections 36(1)(a) and 48(1) of the Health and Safety at Work Act 2015",
             offence="12 March 2023", fine="$60,000", extra=""):
    row = lambda k, v: f'<div class="row">\n<div class="label">{k}:</div>\n<div>{v}</div>\n</div>'
    return ("<html><head><title>x | WorkSafe</title></head><body>"
            f'<h1 class="page-title">{defendant}</h1><section id="main-page-content" class="s-cms-content">'
            '<div class="highlight-block"><h2 class="h3 no-line">Court Summary - at a glance</h2>'
            + row("Date of offence", offence) + row("Plea", "Guilty") + "</div>"
            + row("Defendant name", defendant) + row("Industry", "Construction") + row("Date of offence", offence)
            + row("Facts in brief", "The victim fell at 12 Invented Street, Town.") + row("Offence section", section)
            + row("Date(s) charged ", "2 May 2024") + row("Court", "Auckland - District Court") + row("Plea", "Guilty")
            + row("Final decision date", '<time datetime="2024-12-12">December 12, 2024</time>')
            + row("Decision", "Convicted and fined") + row("Fine imposed", fine)
            + row("Reparation", "Emotional harm – $40,000") + extra
            + '</section><!-- // end main-page-content \\ --></body></html>').encode()


def _undertaking(name, contravention="Being a PCBU, did fail to comply with that duty."):
    return ("<html><head><title>x | WorkSafe</title></head><body>"
            f'<h1 class="page-title">{name}</h1><section id="main-page-content" class="s-cms-content">'
            '<p class="status-tag" data-status-tag="complete">Complete</p>'
            '<p class="publication-info"><time datetime="2026-06-29 09:00:00">29 June 2026</time></p>'
            f'<p class="intro">We have accepted an enforceable undertaking from {name}.</p>'
            "<h2>Incident</h2><p>On 1 May 2023 a worker was hurt at 5 Invented Road.</p>"
            f"<h2>Alleged contravention</h2><p>{contravention}</p>"
            "<h2>Date accepted</h2><p>8 June 2026</p><h2>Further information</h2><p>x</p>"
            '</section><div id="page-utilities"></div></body></html>').encode()


def _listing(name, slugs, total=608):
    art = lambda s: (f'<article itemscope><h1 class="h2" itemprop="name"><a href="{read.PATHS[name]}{s}/" itemprop="url">'
                     f'{s.title()}</a></h1><p class="date-info"><time datetime="2024-12-12">December 12, 2024</time></p>'
                     + ('<p class="status-tag" data-status-tag="complete">Complete</p>' if name == "undertakings" else "")
                     + "</article>")
    return (f'<html><p class="result-summary mt-6">\n Found <strong>{total}</strong> results\n</p>'
            + "".join(art(s) for s in slugs) + "</html>").encode()


def _all_text(action) -> str:
    return " ".join(str(v) for v in action.values() if v is not None)


def rules(mod) -> list:
    broken = []
    L = mod.read_listing(_listing("undertakings", ["alpha-limited", "beta-ltd"], total=62), "undertakings")
    if L["stated"] != 62 or [i["slug"] for i in L["items"]] != ["alpha-limited", "beta-ltd"]:
        broken.append("a list's own count and its items are read in order")
    if L["items"] and L["items"][0]["card"] != "2024-12-12|Alpha-Limited|Complete":
        broken.append("an item's fingerprint is its date, title and status as listed")

    p = mod.read_page(_summary("Alpha Limited and Beta Ltd",
                               section="AL – Sections 36(1)(a) Health and Safety at Work Act 2015 (HSWA)<br />"
                                       "BL – Sections 43(2)(b) HSWA",
                               offence="Between 14 October 2022 and 6 May 2023",
                               fine="Starting point of $450,000. Final fine $30,000, split 55% and 45%"),
                      SHA, "prosecutions", "alpha-limited-and-beta-ltd")
    a, ps = p["action"], p["parties"]
    if not a or a["key"] != "worksafe/prosecution/alpha-limited-and-beta-ltd" or a["kind"] != "prosecution":
        broken.append("the key is the slug; the kind")
    if [(x["name"], x["split_from"]) for x in ps] != [("Alpha Limited", "and between two legal names"),
                                                       ("Beta Ltd", "and between two legal names")]:
        broken.append("joint defendants split on ' and ' between two legal names")
    if a and a["section_charged"] != ("AL – Sections 36(1)(a) Health and Safety at Work Act 2015 (HSWA); "
                                      "BL – Sections 43(2)(b) HSWA"):
        broken.append("the section charged as stated, a line per defendant")
    if a and a["acts"] != ["Health and Safety at Work Act 2015"]:
        broken.append("each Act the section names by title")
    if a and (a["offence_on"] is not None or a["offence_when"] != "Between 14 October 2022 and 6 May 2023"):
        broken.append("a range of offence dates is kept as stated and never made a day")
    if a and (a["decided_on"] != dt.date(2024, 12, 12) or a["charged_on"] != dt.date(2024, 5, 2)
              or a["action_on"] != dt.date(2024, 12, 12)):
        broken.append("the decision's date from its datetime; the date charged")
    if a and a["fine_amount"] is not None:
        broken.append("a fine stated with several figures has no single figure")
    if a and "Invented Street" in _all_text(a):
        broken.append("the facts in brief are never read")

    one = mod.read_page(_summary("Gamma Limited"), SHA, "prosecutions", "gamma")["action"]
    if one["fine_amount"] != 60000.0 or one["offence_on"] != dt.date(2023, 3, 12):
        broken.append("one stated figure is the fine; one stated day is the offence's day")
    hs = mod.read_page(_summary("Delta Limited", section="Sections 36(1)(a), 48(1) and 48(2)(c) of HSWA"), SHA,
                       "prosecutions", "delta")["action"]
    if hs["acts"] != ["HSWA"]:
        broken.append("an Act named only by its abbreviation is kept as stated")
    j = mod.read_page(_summary("Epsilon Limited and Invented Person"), SHA, "prosecutions", "eps")["parties"]
    if [x["name"] for x in j] != ["Epsilon Limited and Invented Person"]:
        broken.append("' and ' splits only between two legal names")

    c = mod.read_page(_summary("2021-B"), SHA, "prosecutions", "2021-b")
    if not (c["parties"][0]["withheld"] and c["parties"][0]["name"] is None and c["action"]["title"] is None
            and c["action"]["url"] is None and "2021-b" not in c["action"]["key"]):
        broken.append("a code in place of a name is withheld, with the heading, address and slug")
    n = mod.read_page(_summary("Name suppressed"), SHA, "prosecutions", "name-suppressed-2")
    if not (n["parties"][0]["withheld"] and n["parties"][0]["name"] is None):
        broken.append("a name WorkSafe writes suppressed is withheld")
    s = mod.read_page(_summary("Invented Person", extra='<div class="row"><div class="label">Note:</div>'
                                                        "<div>Name suppression was granted.</div></div>"),
                      SHA, "prosecutions", "invented-person")
    if not (s["parties"][0]["withheld"] and s["action"]["title"] is None and "invented" not in s["action"]["key"]):
        broken.append("a stated suppression withholds a party who is not one organisation alone")
    k = mod.read_page(_summary("Kappa Limited and Invented Other", extra='<div class="row"><div class="label">Note:</div>'
                                                                        "<div>Name suppression applies.</div></div>"),
                      SHA, "prosecutions", "kappa")
    if not k["parties"][0]["withheld"]:
        broken.append("a stated suppression withholds a name joined to an organisation's")
    o = mod.read_page(_summary("Omega Limited", extra='<div class="row"><div class="label">Note:</div>'
                                                      "<div>Name suppression for the victim.</div></div>"),
                      SHA, "prosecutions", "omega")
    if o["parties"][0]["withheld"]:
        broken.append("a stated suppression leaves one organisation alone named")

    u = mod.read_page(_undertaking("Zeta Limited", "In breach of sections 36(1)(a) and 48(1) of the Health and Safety "
                                                   "at Work Act 2015."), SHA, "undertakings", "zeta-limited")
    ua = u["action"]
    if not ua or ua["key"] != "worksafe/undertaking/zeta-limited" or ua["status"] != "Complete" \
            or ua["published_on"] != dt.date(2026, 6, 29) or ua["accepted_on"] != dt.date(2026, 6, 8) \
            or ua["action_on"] != dt.date(2026, 6, 8):
        broken.append("an undertaking's status, date published and date accepted")
    if ua and (ua["sections"] != ["sections 36(1)(a) and 48(1) of the Health and Safety at Work Act 2015"]
               or ua["acts"] != ["Health and Safety at Work Act 2015"]):
        broken.append("the sections and Act an alleged contravention states")
    if [(x["name"], x["named_in"]) for x in u["parties"]] != [("Zeta Limited", "heading")]:
        broken.append("an undertaking's duty holder from its heading")
    if ua and "Invented Road" in _all_text(ua):
        broken.append("the incident is never read")

    if mod.read_page(_undertaking("Eta Limited"), SHA, "prosecutions", "eta")["action"] is not None:
        broken.append("a page not of the court summary's shape is set aside whole")
    if mod.read_page(b"<html><title>Just a moment...</title></html>", SHA, "undertakings", "x")["action"] is not None:
        broken.append("a block page is set aside whole")
    try:
        mod.read_listing(b"<html><title>Page not found</title></html>", "prosecutions")
        broken.append("a page not of the listing's shape is refused")
    except ValueError:
        pass
    return broken


def test_every_rule_holds():
    assert rules(read) == []


MUTANTS = {
    "the last figure taken as the fine": ('"fine_amount": one_figure(fine)',
                                          '"fine_amount": float(re.sub(r"[^\\d.]", "", _MONEY.findall(fine)[-1])) '
                                          'if fine and _MONEY.findall(fine) else None'),
    "a code read as a name": ('else "WorkSafe publishes a code in place of the name" if CODE.match(name)',
                              'else "x" if False'),
    "a stated suppression ignored": ('else "the page states a suppression" if states_suppression', 'else None if True'),
    "a suppression withholds companies too": ("states_suppression and not (org and not _AND.search(name))",
                                              "states_suppression"),
    "a joined name kept on a suppression": ("states_suppression and not (org and not _AND.search(name))",
                                            "states_suppression and not org"),
    "' and ' split everywhere": ("if len(bits) == 2 and all(LEGAL_ENDING.search(b) for b in bits):", "if len(bits) == 2:"),
    "the facts in brief read": ('section = lines(f.get("offence section", "")) or None',
                                'section = lines(f.get("offence section", "") + f.get("facts in brief", "")) or None'),
    "a range made a day": ('"offence_on": date_of(_ONE_DATE.match(offence_when).group(1)) if offence_when and _ONE_DATE.match(offence_when) else None',
                           '"offence_on": date_of(re.findall(r"\\d{1,2} [A-Z][a-z]+ \\d{4}", offence_when)[0]) if offence_when else None'),
    "the abbreviation not kept": ("    if not out:\n        for m in ABBREVIATIONS", "    if False:\n        for m in ABBREVIATIONS"),
    "the address kept on a withheld name": ('"url": None if suppressed else', '"url": None if False else'),
    "any page read as a court summary": ('if name == "prosecutions" and not glance:', "if False:"),
    "a field's lines run together": ('s = re.sub(r"<br\\s*/?>|</p>|</li>", "\\n", s or "", flags=re.I)', 's = s or ""'),
    "the action dated by its publication": ('action["action_on"] = action["decided_on"] or action["accepted_on"] or action["published_on"]',
                                            'action["action_on"] = action["published_on"] or action["decided_on"]'),
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


def _run(answers, now=dt.datetime(2026, 10, 22, 23, 0, tzinfo=capture.NZ), elsewhere=False):
    t, clock, asked = FakeTables(), [0.0], []
    pages = {"prosecutions": _listing("prosecutions", ["a", "b"], total=2),
             "undertakings": _listing("undertakings", ["c"], total=1)}

    def opener(url, timeout):
        asked.append(url)
        clock[0] += 0.1
        a = answers.pop(0) if answers else 200
        if isinstance(a, Exception):
            raise a
        name = next((n for n, p in read.PATHS.items() if url.endswith(p)), None)
        body = pages[name] if name else (_summary("Invented Limited") if "/prosecutions/" in url
                                         else _undertaking("Invented Limited"))
        final = "https://elsewhere.example/x" if elsewhere and not name else url
        return types.SimpleNamespace(url=url, status=a, body=body if a == 200 else b"<html>error</html>",
                                     final_url=final, blocked="HTTP 403: a block" if a in (403, 429) else "")

    run = capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="a" * 64), True), opener=opener,
                      clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                      now=lambda: now, docs={})
    return run.run(), t, asked, clock


def test_both_lists_are_walked_and_every_item_fetched_once():
    out, t, asked, clock = _run([])
    assert not out["stopped"] and set(t.items) == {("prosecutions", "a"), ("prosecutions", "b"), ("undertakings", "c")}
    assert len(asked) == len(set(asked)) == 5 and clock[0] >= 4 * capture.FLOOR_S


def test_a_block_stops_the_run():
    out, t, asked, clock = _run([200, 403])
    assert out["stopped"].startswith("stopped:") and len(asked) == 2 and not t.items
    assert not capture.outcome(out)[0] or out["pages"]                # green only when something landed


def test_a_redirect_to_another_host_stops_the_run_and_lands_nothing():
    out, t, asked, clock = _run([], elsewhere=True)
    assert out["stopped"].startswith("stopped:") and not t.items


def test_a_timeout_is_a_failed_read_and_the_run_goes_on():
    out, t, asked, clock = _run([200, 200, TimeoutError("slow"), 200])
    assert not out["stopped"] and len(t.items) == 2 and t.asides[0][0] == "fetch"


def test_off_peak_only_unless_asked():
    out, t, asked, clock = _run([], now=dt.datetime(2026, 10, 22, 12, 0, tzinfo=capture.NZ))
    assert out["stopped"] == "off-peak is over" and not asked


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
               "actions_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_worksafe_actions"),
               "parties_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_worksafe_parties")}


def test_every_listed_item_is_an_action(filled):
    assert len(filled["actions"]) == 10 and not filled["read_set_aside"]
    assert {r["state"] for r in filled["read_items"]} == {"read"}


def test_every_row_meets_the_row_contract(filled):
    for r in filled["actions"] + filled["parties"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


def test_the_hard_cases_read_as_worksafe_publishes_them(filled):
    by = {r["slug"]: r for r in filled["actions"] if r["slug"]}
    parties = {}
    for p in filled["parties"]:
        parties.setdefault(p["action_key"], []).append(p)
    assert by["tracks-concrete-2002-limited"]["acts"] == ["Health and Safety in Employment Act 1992"]
    assert by["tracks-concrete-2002-limited"]["fine_amount"] == 60000
    jc = by["joan-carpenters-limited-and-church-bay-services-limited"]
    assert jc["fine_amount"] is None and jc["acts"] == ["Health and Safety at Work Act 2015"]
    assert len(parties[jc["key"]]) == 2 and jc["offence_on"] is None
    assert by["all-smart-kitchens-and-granite-works-limited"]["fine_amount"] is None          # instalments
    assert by["turley-farms-limited"]["acts"] == ["HSWA"]
    code = [r for r in filled["actions"] if r["slug"] is None]
    assert len(code) == 1 and code[0]["title"] is None and code[0]["url"] is None
    assert all(p["withheld"] and p["name"] is None for p in parties[code[0]["key"]])
    assert by["citywide-electrical-limited"]["sections"] and by["pact-steel-limited"]["status"] == "In progress"


def test_the_views_withhold_and_the_check_is_clean(filled):
    held = [r for r in filled["parties_view"] if r["withheld"]]
    assert held and all(r["name"] == "name withheld" for r in held)
    assert check.views(filled["conn"], f"{SAMPLE_SCHEMA}.v_") == []
    assert check.reading(filled["conn"], SAMPLE_SCHEMA) == []


def test_the_check_goes_red_on_a_name_shown_or_a_broken_ledger(filled):
    conn = filled["conn"]
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    conn.execute(f"UPDATE {T('read_items')} SET parties = parties + 1 WHERE slug = 'turley-farms-limited'")
    try:
        assert check.reading(conn, SAMPLE_SCHEMA) != []
    finally:
        conn.rollback()
    v = load.sql("publish.sql", SAMPLE_SCHEMA).replace("pub.", f"{SAMPLE_SCHEMA}.v_")
    conn.execute(v.replace("CASE WHEN a.title_withheld THEN 'name withheld by WorkSafe' ELSE a.title END",
                           "coalesce(a.title, a.court)"))
    try:
        assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") != []
    finally:
        conn.rollback()
    conn.execute(f"UPDATE {T('actions')} SET reparation_text = 'paid at 12 Invented Street, Town' "
                 "WHERE slug = 'turley-farms-limited'")
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
    assert got == {"prosecutions": {(608, 20)}, "undertakings": {(62, 20)}}
