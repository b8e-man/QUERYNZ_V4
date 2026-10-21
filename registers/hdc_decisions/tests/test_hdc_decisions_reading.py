"""The reading's rules on pages shaped like the Commissioner's (every name
invented), a mutant check of those rules (and of the consumer-detail guard,
with a consumer detail planted), the capture's politeness and its hold on a
fake transport, the proposed profiles, and the filled sample (real pages,
sample.list) against the row contract, the ledger, the guard and the views.
No model is called and nothing is fetched."""
import datetime as dt
import json
import os
import types

import pytest

from support import db, profiles, rowcontract, sample
from registers.hdc_decisions import capture, check, load, read
from registers.hdc_decisions import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = "e" * 64
SAMPLE_SCHEMA = "scratch_test_hdc_decisions"


def _page(body, date="12 Oct 2026", meta=(("Group providers", "Rest Home"), ("Rights", "4(1)")), web_id="",
          notice="Names have been removed to protect privacy. Identifying letters are assigned in alphabetical order "
                 "and bear no relationship to the person’s actual name.",
          heading="Invented failings in the care of an older woman with dementia"):
    li = "".join(f'<li><strong>{k} :</strong> <span class="ss360-category-x">{v}</span></li>' for k, v in meta)
    return ("<html><head><title>x</title></head><body><main class=\"l-page\">"
            f'<h1 class="o-layout-header__heading">{heading}</h1>'
            f'<div class="o-layout-header__date">Date:<span></span><span class="ss360-date">{date}</span></div>'
            + (f'<span class="u-hidden">{web_id}</span>' if web_id else "")
            + f'<article><div class="u-hidden"><ul>{li}</ul></div>'
            '<section class="c-rte"><div class="t-link-parent c-rte__body-text">'
            + (f"<p><em>{notice}</em></p>" if notice else "") + body
            + "</div></section></article></main></body></html>").encode()


#: the older drafting: a notice with exceptions, a parties block split at line breaks, 'Opinion: X — finding'
OLD = _page(
    "<h2>Invented Care Homes Limited<br />Rest Home<br />Registered Nurse, RN B<br />General Practitioner, Dr Jane "
    "Inventa</h2><h5>Findings</h5><p>Invented Care Homes Limited (ICH) (company number 1234567) runs the rest home.</p>"
    "<h3>Opinion: Invented Care Homes Limited — breach</h3>"
    "<p>Accordingly, I find that ICH breached Rights 4(1) and 4(2) of the Code.</p>"
    "<p>RN B did not breach Right 6(1) of the Code.</p>"
    "<p>I have considered whether Dr Inventa breached Right 7(1) of the Code.</p>"
    "<h3>Opinion: RN B — adverse comment</h3><h3>Opinion: Dr Inventa — breach</h3>"
    "<h3>Opinion: The rest home — other comment</h3>"
    "<h5>Falls management for Mrs A — breach</h5>"
    "<p>Dr Jane Inventa is named in this report because of public safety concerns.</p>"
    "<h3>Recommendations</h3><p>I recommend that ICH: provide a written apology.</p>"
    "<p>I recommend that Dr Inventa undertake further training.</p><h3>Follow-up actions</h3>"
    "<h3>Recommendations for Mrs A’s family, aged 84</h3>"
    "<h2>Further information about Mrs A, aged 84, in Tauranga</h2>",
    date="25 Sept 2017", meta=(("Group providers", "Rest Home"), ("Occupations", "General Practitioner"), ("Rights", "4(1)")),
    notice="Names have been removed (except Invented Care Homes Limited, Dr Jane Inventa and the expert who advised "
           "on this case) to protect privacy.")

#: the 2026 drafting: no parties block; the provider defined in the first paragraph; 'Decision: X – finding'
NEW = _page(
    "<ol><li><p>HDC received a complaint about the care provided to her mother, Mrs B, by Kōwhai Invented Lodge "
    "(KIL; trading as Kōwhai Lodge) in Gisborne.</p></li></ol><h2>Information gathered</h2>"
    "<h2>Decision: KIL – breach</h2><p>KIL did not provide services with reasonable care and skill, and breached "
    "Right 4(1) of the Code.</p><h2>Recommendations and follow-up actions</h2><p>I recommend that KIL:</p>"
    "<h5><strong>PROVIDER :</strong> Kōwhai Invented Lodge</h5>", web_id="CAS-10000-A1B2C3")


def _listing(slugs, year=2017, page=1, of=5):
    tiles = "".join(f'<li class="o-grid__item"><a class="o-tile o-tile--column t-border-hover" '
                    f'href="/decisions/search-decisions/{year}/{s}/"><div class="o-tile__body">'
                    f'<h3 class="o-tile__heading">Invented care of a man aged 80</h3><p class="o-tile__text">'
                    f"\n 0{i + 1} Nov {year}\n</p></div></a></li>" for i, s in enumerate(slugs))
    pag = (f'<div class="c-pagination"><span class="c-pagination__status">\nPage {page} of {of}\t</span></div>'
           if of else "")
    return (f'<html><main>{pag}<div class="c-listing-pods"><ul>{tiles}</ul></div>{pag}</main></html>').encode()


def _all_text(out) -> str:
    return json.dumps(out, default=str, ensure_ascii=False)


def rules(mod) -> list:
    broken = []
    L = mod.read_listing(_listing(["15hdc00001", "16hdc00002"], page=2))
    if L["stated"] != 5 or L["page"] != 2 or [i["slug"] for i in L["items"]] != ["15hdc00001", "16hdc00002"]:
        broken.append("the listing's own pages stated and its tiles in order")
    if L["items"] and ("aged" in L["items"][0]["card"] or L["items"][0]["listed_on"] != dt.date(2017, 11, 1)):
        broken.append("a tile's fingerprint is its date and a hash of its heading, never the heading")

    o = mod.read_page(OLD, SHA, "15hdc00001")
    d, ps = o["decision"], {p["name"]: p for p in o["providers"]}
    text = _all_text({k: v for k, v in o.items() if k != "set_aside"})
    if not d or d["key"] != "hdc_decisions/decision/15hdc00001" or d["case_number"] != "15HDC00001":
        broken.append("the key is the address's slug; the file number from it")
    if d and d["decided_on"] != dt.date(2017, 9, 25):
        broken.append("the page's date as stated ('Sept')")
    if list(ps) != ["Invented Care Homes Limited"]:
        broken.append("one provider row per organisation named; none for a generic kind or an individual")
    p = ps.get("Invented Care Homes Limited") or {}
    if p.get("abbreviation") != "ICH" or p.get("company_number") != "1234567":
        broken.append("a provider's abbreviation from its definition; a company number only where printed beside it")
    if p.get("rights_breached") != ["4(1)", "4(2)"] or p.get("findings") != ["breach"] or not p.get("recommended"):
        broken.append("a provider's rights breached, its finding and its recommendation")
    if d and d["rights_breached"] != ["4(1)", "4(2)"]:
        broken.append("a negated breach or a question is not a breach")
    if d and "Registered Nurse — adverse comment" not in d["findings"]:
        broken.append("an individual's finding is kept under their role")
    if d and "an unnamed rest home — other comment" not in d["findings"]:
        broken.append("a provider the Commissioner does not name is 'an unnamed <kind>'")
    if d and (d["named_roles"] != ["General Practitioner"] or d["naming_grounds"] != ["public safety concerns"]):
        broken.append("a named practitioner is a role, with the naming policy's ground the page states")
    if "Inventa" in text or "Jane" in text:
        broken.append("a named practitioner's name is never kept")
    if "RN B" in text or "Mrs A" in text or "Dr C" in text:
        broken.append("a letter label is never kept")
    if "dementia" in text or "older woman" in text or "Further information" in text:
        broken.append("the heading and the body's own headings are never kept")
    if d and (d["recommendation_headings"] != ["Recommendations", "Follow-up actions"]
              or not any(s["stage"] == "guard" and s["reason"].startswith("recommendation_heading") for s in o["set_aside"])):
        broken.append("a recommendation heading carrying a consumer detail is refused and logged")
    if any("84" in s["reason"] or "Mrs" in s["reason"] for s in o["set_aside"]):
        broken.append("the catch log names the field, never the value")
    if d and d["recommended_to"] != ["Invented Care Homes Limited", "General Practitioner"]:
        broken.append("recommendations' addressees: a named provider, a role")
    if d and d["kind"] != "breach":
        broken.append("the kind is the gravest finding stated")

    n = mod.read_page(NEW, SHA, "cas-10000-a1b2c3")
    nd, np_ = n["decision"], n["providers"]
    if not (nd and nd["web_id"] == "CAS-10000-A1B2C3" and nd["case_number"] is None):
        broken.append("the 2026 layout: the site's id; no file number where none is stated")
    if [x["name"] for x in np_] != ["Kōwhai Invented Lodge"] or np_[0]["abbreviation"] != "KIL" \
            or np_[0]["also_called"] != ["Kōwhai Lodge"] or np_[0]["findings"] != ["breach"]:
        broken.append("the 2026 layout: the provider from its definition, its finding through its abbreviation")
    if np_ and np_[0]["rights_breached"] != ["4(1)"]:
        broken.append("a breach statement after 'did not provide' is still a breach")
    if "Gisborne" in _all_text(nd) or "mother" in _all_text(nd):
        broken.append("no place or relation beyond the provider")

    cs = mod.read_page(_page("<p>This case concerns Invented Health Trust (IHT). IHT breached Right 4(1) of the "
                             "Code (22HDC00499).</p>", meta=(), notice=""), SHA, "delay-in-diagnosis-of-cancer",
                       kind="case study")
    c = cs["decision"]
    if not (c and c["kind"] == "case study" and c["url"] is None and c["slug"] is None and "cancer" not in c["key"]
            and cs["private"] and cs["private"][0]["slug"] == "delay-in-diagnosis-of-cancer"):
        broken.append("a case study's address (its summary) is private; its key is its slug's hash")
    if c and (c["case_number"] != "22HDC00499" or [x["name"] for x in cs["providers"]] != ["Invented Health Trust"]):
        broken.append("a case study's stated file number, and the provider its breach statement names")

    bad = mod.read_page(b"<html><title>Just a moment...</title></html>", SHA, "x")
    gone = mod.read_page(b"<html><main><h1>Page not found</h1></main></html>", SHA, "y")
    news = mod.read_page(b'<html><main><span class="ss360-date">12 Oct 2026</span><div class="c-news">x</div></main></html>',
                         SHA, "z")
    if bad["decision"] is not None or len(bad["set_aside"]) != 1 or gone["decision"] is not None or news["decision"]:
        broken.append("a page not of the decision's shape is set aside whole")
    try:
        mod.read_listing(b"<html><title>Page not found</title></html>")
        broken.append("a page not of the listing's shape is refused")
    except ValueError:
        pass

    for planted in ("Mrs B", "aged 84", "an 84-year-old man", "her daughter", "dementia", "Tauranga", "the consumer"):
        if not mod.consumer_detail(f"Recommendations about {planted}"):
            broken.append(f"the guard refuses a planted consumer detail ({planted!r})")
    for fine in ("Recommendations", "Follow-up actions", "General Practitioner", "public safety concerns"):
        if mod.consumer_detail(fine):
            broken.append(f"the guard passes a plain value ({fine!r})")
    if mod.consumer_detail("Waikato District Health Board", "name") or not mod.consumer_detail("Mrs B’s rest home", "name"):
        broken.append("a provider's name may carry a place, never a letter label")
    return broken


def test_every_rule_holds():
    assert rules(read) == []


MUTANTS = {
    "the guard passes everything": ('    if not m:\n        return ""\n    s = m.group(0)', '    if True:\n        return ""\n    s = ""'),
    "the guard misses ages": ('GUARD_STRICT = re.compile("|".join((_LABEL, _AGE, _KIN,',
                              'GUARD_STRICT = re.compile("|".join((_LABEL, _KIN,'),
    "the guard misses conditions": ('_PERSON_WORDS, _CONDITION, _PLACE)), re.I)', '_PERSON_WORDS, _PLACE)), re.I)'),
    "the guard misses places": ('_PERSON_WORDS, _CONDITION, _PLACE)), re.I)', '_PERSON_WORDS, _CONDITION)), re.I)'),
    "names kept for a named practitioner": ('        named_roles.append(role or "a practitioner")', '        named_roles.append(person)'),
    "the guard not applied to headings": ('        why = consumer_detail(bare, field)', '        why = ""'),
    "the catch log spells the value": ('f"{field}: {why}; the value is not kept"', 'f"{field}: {why}; {value}"'),
    "an individual's label kept": ('        return x or "an issue heading"', '        return x or who'),
    "a generic kind made a row": ('        if not r["named"]:\n            continue', '        if False:\n            continue'),
    "negations read as breaches": ('        if _NEGATED.search(clause) or _QUESTION.search(clause):\n            continue',
                                   '        if False:\n            continue'),
    "parties not split at line breaks": ('        for line in lines:\n            if "," in line:',
                                         '        for line in [text]:\n            if "," in line:'),
    "a case study's address published": ('        "providers_named": 0, "url": address if opaque else None,',
                                         '        "providers_named": 0, "url": address,'),
    "every heading a recommendation heading": ('if k == "h" and _REC_HEADING.match(h)', 'if k == "h"'),
    "the number read anywhere": ('m = _NUMBER_BESIDE.match(text[at.end(): at.end() + 80])',
                                 'm = _NUMBER_BESIDE.search(text)'),
    "any page read as a decision": ('    if not _BODY.search(t):\n        return "no body', '    if False:\n        return "no body'),
    "the 'Sept' date unread": ('.replace("Sept ", "Sep ")', '.replace("Sept ", "Sept ")'),
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
    except (KeyError, TypeError, AttributeError, ValueError, IndexError, NameError):
        broken = ["crashed"]
    assert broken, f"the mutant '{name}' passes every rule"


# ── the profiles ─────────────────────────────────────────────────────────────

def test_the_proposed_profiles_are_whole_and_new():
    rows = [json.loads(l) for l in open(os.path.join(LANE, "profile-proposed.jsonl"), encoding="utf-8") if l.strip()]
    assert {r["slug"] for r in rows} == {read.LISTING_PROFILE, read.DECISION_PROFILE, read.CASE_STUDIES_PROFILE,
                                         read.CASE_STUDY_PROFILE}
    held = profiles.current()
    for r in rows:
        assert profiles.valid_slug(r["slug"]) and r["kind"] == profiles.KIND and r["version"] == read.PROFILE_VERSION
        assert all(k in r for k in profiles.FIELDS) and r["by"] and r["at"]
        assert r["slug"] not in held or int(held[r["slug"]]["version"]) < r["version"]
        assert "Mrs" not in json.dumps(r) and "aged" not in json.dumps(r)


# ── the capture's politeness and its hold, on a fake transport ─────────────────

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


def _run(answers, slugs):
    t, clock, asked = FakeTables(), [0.0], []
    listing = _listing(slugs, of=1)

    def opener(url, timeout):
        asked.append(url)
        clock[0] += 0.1
        a = answers.pop(0) if answers else 200
        if isinstance(a, Exception):
            raise a
        body = (listing if "filter-year" in url else b"<html><title>Just a moment...</title></html>" if a == "challenge"
                else b"<html><main>not found</main></html>" if a == "shape" else NEW)
        st = 200 if a in ("challenge", "shape") else a
        return types.SimpleNamespace(url=url, status=st, body=body if st == 200 else b"<html>error</html>",
                                     final_url=url, blocked="")

    run = capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="a" * 64), True), opener=opener,
                      clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                      now=lambda: dt.datetime(2026, 10, 22, 23, 0, tzinfo=capture.NZ), docs={},
                      lists=[capture.year_list(2017)])
    return run, run.run(), t, asked, clock


@pytest.mark.parametrize("answer", [403, 429, 500, 503, "challenge"])
def test_a_block_a_limit_a_server_error_or_a_challenge_stops_the_run(answer):
    run, out, t, asked, clock = _run([200, 200, answer], ["15hdc00001", "15hdc00002", "15hdc00003", "15hdc00004"])
    assert out["stopped"].startswith("stopped:") and len(asked) == 3 and list(t.items) == ["15hdc00001"]
    assert clock[0] >= 2 * capture.FLOOR_S and capture.outcome(out)[0]      # a polite stop after landing is green


def test_a_timeout_is_a_failed_read_and_three_stop_the_run():
    run, out, t, asked, clock = _run([200, TimeoutError("slow"), 200], ["15hdc00001", "15hdc00002", "15hdc00003"])
    assert not out["stopped"] and set(t.items) == {"15hdc00002", "15hdc00003"}
    run, out, t, asked, clock = _run([200, TimeoutError(), ConnectionResetError(), TimeoutError()],
                                     ["15hdc00001", "15hdc00002", "15hdc00003", "15hdc00004"])
    assert "3 failed reads" in out["stopped"] and not t.items


def test_a_page_not_of_the_decision_shape_is_not_landed():
    run, out, t, asked, clock = _run([200, "shape", 200], ["15hdc00001", "15hdc00002"])
    assert set(t.items) == {"15hdc00002"} and t.asides[0][0] == "item"


def test_off_peak_only_unless_asked():
    t = FakeTables()
    run = capture.Run(t, land_fn=None, opener=lambda u, s: pytest.fail("asked during the day"), docs={},
                      now=lambda: dt.datetime(2026, 10, 22, 14, 0, tzinfo=capture.NZ), lists=[capture.year_list(2017)])
    assert run.run()["stopped"] == "off-peak is over"


def test_the_hold():
    assert capture.held_for("querynz_v4", 10, 10, authorised="") .startswith("held:")
    assert capture.held_for("querynz_v4_sample", 41, 5, authorised="").startswith("held:")
    assert capture.held_for("querynz_v4_sample", 40, 40, authorised="") == ""
    assert capture.held_for("querynz_v4", 10 ** 5, 10 ** 3, authorised="2026-11-01, the Commissioner's letter") == ""
    assert capture.authorisation(os.path.join(LANE, "position")) is None       # held as built


def test_the_lists_open_in_2017():
    names = [x.name for x in capture.all_lists(dt.date(2026, 10, 21))]
    assert names[0] == "decisions-2026" and names[-2] == "decisions-2017" and names[-1] == "case-studies" and len(names) == 11
    assert capture.year_list(2019).page_url(1).endswith("?filter-year=2019")
    assert capture.year_list(2019).page_url(3).endswith("?filter-year=2019&page=3")


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
               "decisions_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_hdc_decisions"),
               "providers_view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_hdc_decision_providers")}


def test_every_listed_page_is_a_row(filled):
    assert len(filled["decisions"]) == 12
    assert {r["state"] for r in filled["read_items"]} == {"read"}
    assert all(s["stage"] == "guard" for s in filled["read_set_aside"])


def test_every_row_meets_the_row_contract(filled):
    for r in filled["decisions"] + filled["providers"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


#: the sample's hard cases by their documents (sample.list says what each is; no slug, which can carry a summary, in git)
D = {"2017 unnamed DHB": "4b90211d73068b63f9adaf4e4dacec13d5524a5fe48c8cb83e43fc1d19c0769f",
     "three DHBs": "f73a9f6934382a0e95151f57f9913f3043ed372778ebc841079ebfc39912ea6c",
     "company and ACC": "4f774af8f2b239ba7de7076e1b2de49cc0ee4ee0f42e0230607efc09a999276b",
     "joint file numbers": "1d1faa1e2797b24b34b536eaef1352256271876ebb7ef4bc1e55bcf69cf816e0",
     "pharmacy": "d929aeace65b6dbbc6f1611471160bd022176c9dc4a6ece27d99c53fa2093ca5",
     "southern": "8956ff7b03367469e23489e944c759ef9d0f40974a4032d3dcc6ed9d25572bd4",
     "surgeon": "e103e7568734bd091738905c338c7a8fe88431c353c02fd5aeee2a4a2f1290f1",
     "2026": "1f788b1734f4c6534c36d7df4639c557a6cf35bbc520155ee5c02ba559331f09",
     "case study, file number": "5f739104e0b758cc1c97ac2570559daca696c061b1f22fdde8bc281163f029bc"}


def test_the_hard_cases_read_as_the_pages_say(filled):
    by = {r["document"]: r for r in filled["decisions"]}
    prov = {}
    for p in filled["providers"]:
        prov.setdefault(p["document"], []).append(p)
    names = lambda k: [p["name"] for p in prov.get(D[k], [])]
    assert by[D["2017 unnamed DHB"]]["case_number"] == "15HDC01415" and not prov.get(D["2017 unnamed DHB"])
    assert "an unnamed district health board — adverse comment" in by[D["2017 unnamed DHB"]]["findings"]
    assert names("three DHBs") == ["Waikato District Health Board", "Auckland District Health Board",
                                   "Bay of Plenty District Health Board"]
    assert {f for f in by[D["three DHBs"]]["findings"]} >= {"Waikato District Health Board — adverse comment",
                                                            "Bay of Plenty District Health Board — no breach"}
    assert names("company and ACC") == ["ACC", "Geneva Healthcare Limited"]
    assert by[D["joint file numbers"]]["case_numbers"] == ["16HDC01786", "18HDC01259"]
    assert not prov.get(D["pharmacy"]) and by[D["pharmacy"]]["recommended_to"] == ["an unnamed pharmacy"]
    assert names("southern") == ["Southern District Health Board"] and by[D["southern"]]["decided_on"] == dt.date(2024, 2, 22)
    assert by[D["surgeon"]]["rights_tagged"] == ["4(1)", "7(1)", "6(1)(g)"] and "7(1)" in by[D["surgeon"]]["rights_breached"]
    new = prov[D["2026"]][0]
    assert (new["name"], new["abbreviation"], new["findings"], new["rights_breached"]) == \
        ("Ultimate Care Oakland", "UCO", ["breach"], ["4(2)"])
    assert by[D["2026"]]["web_id"] == "CAS-13928-S0F4B9" and by[D["2026"]]["case_number"] == "22HDC00991"
    cs = by[D["case study, file number"]]
    assert cs["kind"] == "case study" and cs["case_number"] == "22HDC00499" and cs["url"] is None


def test_the_views_carry_no_consumer_and_the_check_is_clean(filled):
    assert check.views(filled["conn"], f"{SAMPLE_SCHEMA}.v_") == []
    assert check.reading(filled["conn"], SAMPLE_SCHEMA) == []
    for r in filled["decisions_view"] + filled["providers_view"]:
        assert "title" not in r and "heading" not in r


def test_the_check_refuses_a_planted_consumer_detail(filled):
    conn = filled["conn"]
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    v = load.sql("publish.sql", SAMPLE_SCHEMA).replace("pub.", f"{SAMPLE_SCHEMA}.v_")
    for col, planted in (("recommendation_headings", "ARRAY['Recommendations for Mrs B, aged 84']"),
                         ("named_roles", "ARRAY['Dr Jane Inventa']"), ("findings", "ARRAY['Mrs B — breach']")):
        conn.execute(f"UPDATE {T('decisions')} SET {col} = {planted} WHERE document = %s", (D["pharmacy"],))
        conn.execute(v)
        try:
            assert any(col in p for p in check.views(conn, f"{SAMPLE_SCHEMA}.v_")), col
        finally:
            conn.rollback()
    conn.execute(f"UPDATE {T('read_items')} SET providers = providers + 1 WHERE document = %s", (D["2026"],))
    try:
        assert check.reading(conn, SAMPLE_SCHEMA) != []
    finally:
        conn.rollback()
    conn.execute(f"UPDATE {T('decisions')} SET url = 'https://www.hdc.org.nz/x/' WHERE kind_of_page = 'case study'")
    conn.execute(v)
    try:
        assert any("case studies" in p for p in check.views(conn, f"{SAMPLE_SCHEMA}.v_"))
    finally:
        conn.rollback()
    assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") == []


def test_the_listing_pages_read_their_own_count(filled):
    from support.docstore.landing import read_bytes
    pages = [i.split() for i in filled["items"] if i.startswith("key: listing ")]
    got = {(p[2], read.read_listing(read_bytes(p[3]))["page"]): read.read_listing(read_bytes(p[3])) for p in pages}
    assert got[("decisions-2017", 1)]["stated"] == 5 and len(got[("decisions-2017", 1)]["items"]) == 12
    assert got[("decisions-2017", 5)]["stated"] == 5 and len(got[("decisions-2017", 5)]["items"]) == 1   # 4 × 12 + 1 = 49
    assert got[("all", 168)]["stated"] == 168 and len(got[("all", 168)]["items"]) == 6
    assert got[("case-studies", 1)]["stated"] == 1 and len(got[("case-studies", 1)]["items"]) == 20
