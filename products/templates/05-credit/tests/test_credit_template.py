"""The business credit and monitoring template on fixtures: it loads on the
shape, names only published views with their licences, runs its sections in
a credit analyst's order, and its rules keep the flag contract: every change
between the monthly files is listed, newest first, dated by its file with
the grain stated; a change check never clears while the status and name
changes are unreachable; a recent Gazette insolvency is red, an old one is
not recent; a removal is not insolvency; a namesake's evidence is amber at
most; from a company its people are not followed, so their checks block; a
founding director is not churn; no suppressed name and no address in a
flag; no word of cause or ownership. A mutant check breaks the rules file
on purpose, twelve ways, and requires these properties to catch every break.

Imports nothing of products.report (the one-way test): the shape is reached
through its command line, and the rules file is loaded by path as the shape
loads it, with the name `contract` bound to the shape's contract file
(products/report/contract.py, read by path) before it runs."""
import importlib.util
import inspect
import os
import re
import subprocess
import sys
import tomllib

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ORDER = ["identity", "standing", "changes", "gazette", "people", "people-notices", "not-held"]
COMMON = ("group-standing", "hubs-met", "replaced-return")
#: words that would join two facts as cause or call a holder an owner (the shape's rules 3 and 4 hold the full list on every report)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|behind|owners?|owns|owned|"
                   r"beneficial)\b", re.I)
GAZETTE_CO = {"gazette_liquidations", "gazette_company_notices"}
GAZETTE_PERSON = {"gazette_prohibitions", "gazette_bankruptcies"}
CHANGE_CHECKS = ("monthly_changes", "recent_adverse_change")
PEOPLE_CHECKS = ("people_failed_companies", "other_current_companies", "prohibition", "bankruptcy")
OFFICE_LINE = "12 Smith Street"
HIDDEN = "Secret Person NAME"


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


CONTRACT = by_path("qv4_test_report_contract_credit", os.path.join(REPO, "products", "report", "contract.py"))


def rules_module(source: str = None):
    """As the shape's loader does: `contract` bound, then the file run; a
    mutant's source is run the same way."""
    if source is None:
        return by_path("qv4_test_credit_rules", os.path.join(HERE, "rules.py"), contract=CONTRACT)
    mod = type(sys)("qv4_test_credit_mutant")
    mod.contract = CONTRACT
    exec(compile(source, "rules.py (mutant)", "exec"), mod.__dict__)
    return mod


R = rules_module()


def rule(name, mod=None):
    for r in (mod or R).RULES:
        if r.__name__ == name:
            return r
    raise KeyError(name)


# ── the template ────────────────────────────────────────────────────────────

def test_the_shape_loads_it_by_name_with_every_view_known_and_every_rule():
    out = subprocess.run([sys.executable, "-m", "products.report", "templates"], cwd=REPO, capture_output=True, text=True, timeout=20)
    assert out.returncode == 0, out.stderr
    line = [x for x in out.stdout.splitlines() if x.startswith("credit ")]
    assert line and HERE in line[0], out.stdout
    t = toml()
    assert f"{len(t['reads'])} views, {len(t['sections'])} sections, {len(R.RULES)} rules" in line[0]


def test_it_names_each_view_once_with_its_licence_and_fewer_than_the_shape():
    t = toml()
    views = [r["view"] for r in t["reads"]]
    assert len(views) == len(set(views)) and t["depth"] == 2
    assert all(r.get("licence") and r.get("attribution") and r.get("refresh") for r in t["reads"])
    with open(os.path.join(REPO, "products", "report", "templates", "subject", "template.toml"), "rb") as f:
        shape = {r["view"] for r in tomllib.load(f)["reads"]}
    assert set(views) < shape, "a use-case template names fewer views than the shape's"
    assert {"companies", "directors", "shareholders", "company_addresses"} | GAZETTE_CO | GAZETTE_PERSON <= set(views)
    for money in ("party_return_donors", "disclosures", "candidate_return_donors"):
        assert money not in views, "a credit check reads no political money"


def test_its_sections_run_in_the_credit_analysts_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"], "the first section holds the namesakes and nothing confirmed"
    assert not set(s["identity"]["views"]) & (GAZETTE_CO | GAZETTE_PERSON | {"companies"})
    assert s["standing"]["views"][0] == "companies", "every company reached heads the standing section"
    assert set(s["changes"]["views"]) == {"directors", "shareholders", "company_addresses"} and "roles" in s["changes"]["sources"]
    assert "month, not a day" in s["changes"]["text"] and "monthly-changes" in s["changes"]["text"]
    assert GAZETTE_CO <= set(s["gazette"]["views"]) and "pointing" in s["gazette"]["sources"]
    assert "second" in s["people"]["sources"] and "not a clear" in s["people"]["text"]
    assert set(s["people-notices"]["views"]) == GAZETTE_PERSON and "not a clear" in s["people-notices"]["text"]
    assert "second" not in {x for sec in t["sections"] if sec["name"] != "people" for x in sec.get("sources", [])}
    nh = s["not-held"]
    assert {"securities", "insolvency", "courts"} <= set(nh["not_held"]) and nh["views"] == []
    for named in ("Personal Property Securities Register", "Insolvency Register", "court judgments", "credit-bureau defaults",
                  "before 16 August 2026", "step 5.5"):
        assert named in nh["text"], named
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views
        assert not CAUSE.search(x["text"]) and not CAUSE.search(x["heading"]), x["name"]


def test_the_known_limits_page_and_the_checkpoint_list_exist():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    assert "namesake" in page and "not a clear" in page and "checkpoint" in page.lower() and "month" in page
    lim = toml()["limits"]
    assert any("namesake" in x for x in lim) and any("does not yet follow" in x for x in lim) and any("a month and not a day" in x for x in lim)
    assert any("since" in x for x in lim) and any("pub.company_states" in x for x in lim)
    with open(os.path.join(HERE, "checkpoint.list"), encoding="utf-8") as f:
        keys = [x.strip() for x in f if x.strip() and not x.startswith("#")]
    assert len(keys) == 12 and all(re.match(r"^[a-z_]+:\S+$", k) for k in keys), "twelve register keys, one a line, nothing else"


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "society_officers": "person", "gazette_prohibitions": "person",
        "gazette_bankruptcies": "person", "companies": "organisation", "societies": "organisation", "company_addresses": "place",
        "gazette_company_notices": "organisation", "gazette_liquidations": "organisation", "party_return_donors": "figure"}
JUL, AUG, SEP = "companies-2026-07", "companies-2026-08", "companies-2026-09"
NEAR_PEOPLE = "a connection that passes through more than one person is listed as near, never confirmed (the design's default)"


def it(ref, view, grade="confirmed", title="X", statement=None, dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False,
       kind=None, entity_title=None, flags=None):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": kind or KIND[view], "title": title,
            "statement": statement or f"{title}: a row", "dates": {"undated": dates == "undated", "text": dates},
            "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1, "grade": grade,
            "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": flags or [], "replaced_by": None, "entity_title": entity_title}


def co(n, name, status="Registered", registered="2011-03-03", first=JUL, last=AUG, in_latest=True, **row):
    return it(f"companies:companies/{n}", "companies", title=name, statement=f"{name}: {status} LTD, NZBN {n}",
              dates=f"from {registered}; no end filed", row={"key": f"companies/{n}", "nzbn": str(n), "status": status, "entity_type": "LTD",
                                                            "registered_on": registered, "first_file": first, "last_file": last,
                                                            "in_latest": in_latest, **row})


ACME = co(1, "ACME TRADING LIMITED")
GAMMA = co(3, "GAMMA BUILD LIMITED", status="In Liquidation", registered="2015-05-01")
DELTA = co(4, "DELTA LIMITED", registered="2001-05-01")


def role(company, key, name, first=JUL, last=AUG, in_latest=True, appointed="2012-01-01", view="directors", grade="confirmed", **kw):
    row = {"entity_key": company["ref"].split(":", 1)[1], "role_type": "DIRECTOR", "appointed_on": appointed, "first_file": first,
           "last_file": last, "in_latest": in_latest}
    if view == "shareholders":
        row = {"entity_key": company["ref"].split(":", 1)[1], "shares": kw.pop("shares", 100), "first_file": first, "last_file": last,
               "in_latest": in_latest}
    return it(f"{company['ref']}/{'director' if view == 'directors' else 'shareholder'}/{key}", view, grade=grade, title=name,
              via=company["ref"], entity_title=company["title"], row=row, **kw)


def office(company, key, started, last=AUG, in_latest=True, hub=0):
    flags = [{"kind": "busy-address", "text": f"a busy address: {hub} companies", "evidence": {"companies": hub}}] if hub else []
    return it(f"{company['ref']}/registered-office/{started}/{key}", "company_addresses", title=f"{OFFICE_LINE} · Epsom · Auckland",
              statement=f"{company['title']}: registered office at {OFFICE_LINE} · Epsom · Auckland", via=company["ref"],
              row={"entity_key": company["ref"].split(":", 1)[1], "kind": "registered office", "line_1": OFFICE_LINE, "postcode": "1051",
                   "started_on": started, "last_file": last, "in_latest": in_latest}, flags=flags)


STAY = role(ACME, "s", "Jane Mary DOE")
GONE = role(ACME, "g", "John SMITH", last=JUL, in_latest=False)
CAME = role(ACME, "c", "Ann LEE", first=AUG, appointed="2026-07-10")
LATER = role(ACME, "l", "Bob KING", first=SEP, last=SEP, appointed="2026-08-20")
HOLD_JUL = role(ACME, "h1", "Dean WILSON", last=JUL, in_latest=False, view="shareholders", shares=100)
HOLD_AUG = role(ACME, "h2", "Dean  WILSON", first=AUG, view="shareholders", shares=80)
SECRET_GONE = dict(role(ACME, "x", "name suppressed", last=JUL, in_latest=False, suppressed=True), statement=f"{HIDDEN}: DIRECTOR")
OLD_OFFICE = office(ACME, "o1", "2019-01-01", last=JUL, in_latest=False)
NEW_OFFICE = office(ACME, "o2", "2026-07-31", hub=67)
LIQ = it("gazette:gazette/2026-al1/company/1", "gazette_liquidations", title="ACME TRADING LIMITED", dates="appointed 23 July 2026; published 27 July 2026",
         row={"register_key": "companies/1", "appointed_on": "2026-07-23", "published_on": "2026-07-27"}, via=ACME["ref"])
OLD_LIQ = it("gazette:gazette/2019-al1/company/1", "gazette_liquidations", title="ACME TRADING LIMITED", dates="appointed 3 March 2019",
             row={"register_key": "companies/1", "appointed_on": "2019-03-03", "published_on": "2019-03-05"}, via=ACME["ref"])
WINDUP = it("gazette:gazette/2026-ad1/company/1", "gazette_company_notices", title="ACME TRADING LIMITED · winding-up application",
            dates="to be heard 2 November 2026; filed 15 September 2026; published 16 October 2026",
            row={"kind": "winding-up application", "action": "application", "register_key": "companies/1", "event_on": "2026-11-02",
                 "filed_on": "2026-09-15", "published_on": "2026-10-16"}, via=ACME["ref"])
REMOVAL = it("gazette:gazette/2026-ds1/company/9", "gazette_company_notices", title="ACME TRADING LIMITED · removal",
             dates="objections by 17 October 2026; published 19 September 2026",
             row={"kind": "removal", "action": "intention to remove", "register_key": "companies/1", "event_on": "2026-10-17",
                  "published_on": "2026-09-19"}, via=ACME["ref"])
RESTORED = it("gazette:gazette/2026-ds2/company/9", "gazette_company_notices", title="ACME TRADING LIMITED · removal", dates="published 1 October 2026",
              row={"kind": "removal", "action": "restoration", "register_key": "companies/1", "published_on": "2026-10-01"}, via=ACME["ref"])
GAMMA_LIQ = it("gazette:gazette/2025-al2/company/1", "gazette_liquidations", title="GAMMA BUILD LIMITED", dates="appointed 1 May 2025",
               row={"register_key": "companies/3", "appointed_on": "2025-05-01", "published_on": "2025-05-03"}, via=GAMMA["ref"])
PERSON = role(DELTA, "p", "Jane Mary DOE", appointed="2001-05-01")
ON_GAMMA = role(GAMMA, "p", "Jane Mary DOE", appointed="2015-05-01")
PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", title="Jane Mary Doe · prohibition",
            dates="from 22 September 2022; to 22 September 2027", row={"ends_on": "2027-09-22"})
OLD_PROHIB = dict(PROHIB, ref="gazette:gazette/2003-ot1/prohibition/1", dates={"undated": False, "text": "from 7 October 2003; to 7 October 2006"},
                  row={"ends_on": "2006-10-07"})
BANKRUPT = it("gazette:gazette/2024-ba1/person/1", "gazette_bankruptcies", title="Doe · Jane Mary", dates="9 May 2024",
              row={"event_on": "2024-05-09", "published_on": "2024-05-10"})
NAMESAKE = it("companies:companies/77/director/q", "directors", grade="near", title="Jane DOE")


def report(subject=None, **sections):
    out = {"found": True, "as_of": "2026-10-21", "subject": subject or dict(ACME, via=None), "members": [], "flags": [], "hubs": [],
           "group": {"built": True, "size": 1, "contested": False, "omitted": 0},
           "walk": {"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0}, "sections": []}
    for name in ORDER:
        items = sections.get(name.replace("-", "_"), [])
        out["sections"].append({"name": name, "heading": name, "items": items, "omitted": 0, "blank": None if items else "none found"})
    return out


def busy():
    """A company with every kind of change: a director stays, one leaves, one arrives, one arrives in a later file, a holding changes,
    a suppressed director leaves, the office moves to a busy address; a recent liquidation, an old one, a winding-up application, a
    removal and a restoration."""
    return report(changes=[STAY, GONE, CAME, LATER, HOLD_JUL, HOLD_AUG, SECRET_GONE, OLD_OFFICE, NEW_OFFICE],
                  gazette=[LIQ, OLD_LIQ, WINDUP, REMOVAL, RESTORED])


def quiet():
    return report(changes=[STAY, office(ACME, "o", "2019-01-01")])


def person(**kw):
    return report(subject=PERSON, **{"standing": [DELTA, GAMMA], "changes": [ON_GAMMA], "gazette": [GAMMA_LIQ], **kw})


def other():
    return report(subject=it("party_returns:x/A/1", "party_return_donors", title="ACME TRADING LTD · $5,000"))


def short(r):
    r["walk"]["entities_not_expanded"] = 3
    return r


def nearly(*xs):
    return [dict(x, grade="near", reason="reached through a near link: the two rows share a first and last name") for x in xs]


def flags_of(mod, r):
    return [fn(r) for fn in mod.RULES]


# ── the properties, each a list of what broke (empty when they hold) ────────

def properties(mod) -> list:
    """What a credit analyst relies on, checked on fixtures; the mutant check
    runs it on each broken copy of the rules and needs it to say something."""
    bad = []
    rl = lambda n: rule(n, mod)   # noqa: E731
    for name in CHANGE_CHECKS:
        for r in (quiet(), person(), report()):
            if rl(name)(r)["status"] == "clear":
                bad.append(f"status changes unreachable: {name} cleared")
    m = rl("monthly_changes")(busy())
    text = m["text"]
    if m["status"] != "fired":
        bad.append("monthly-changes did not fire on a company with changes")
    for want in ("John SMITH left", "Ann LEE arrived", "Bob KING arrived", "holding of record changed", "registered office of ACME TRADING LIMITED moved",
                 "a month and not a day", "the August 2026 file", "the September 2026 file"):
        if want not in text:
            bad.append(f"monthly-changes lacks {want!r}")
    if "Bob KING" in text and "John SMITH" in text and text.index("Bob KING") > text.index("John SMITH"):
        bad.append("monthly-changes is not newest first: a September change after an August one")
    young = report(subject=co(9, "NEW CO LIMITED", registered="2026-07-02", first=AUG), changes=[role(co(9, "NEW CO LIMITED", first=AUG), "f", "Ann LEE",
                                                                                                      first=AUG, appointed="2026-07-02")])
    if rl("monthly_changes")(young)["status"] != "fired" or "first shown in the August 2026 file" not in rl("monthly_changes")(young)["text"]:
        bad.append("a company first shown in the later file is not a change: the files held were read from its rows alone")
    for start, r in (("company", busy()), ("person", person(people_notices=[PROHIB, BANKRUPT])), ("other", other())):
        for f in flags_of(mod, r):
            if CAUSE.search(f["text"]):
                bad.append(f"{start}: {f['rule']} says a word of cause or ownership: {f['text'][:120]}")
            if HIDDEN in f["text"] or "name suppressed" in f["text"]:
                bad.append(f"{start}: {f['rule']} quotes a suppressed row's name")
            if OFFICE_LINE in f["text"] or CONTRACT.address_shaped(f["text"]):
                bad.append(f"{start}: {f['rule']} prints an address")
    history = mod.HISTORY
    for held in (False, True):   # with past roles held too, the setting under which every other clear is possible
        mod.HISTORY = held
        for name in PEOPLE_CHECKS:
            if rl(name)(busy())["status"] == "clear":
                bad.append(f"company start: {name} cleared the people it never followed")
            if rl(name)(other())["status"] == "clear":
                bad.append(f"filed-row start: {name} cleared what it never walked")
    mod.HISTORY = history
    rec = rl("recent_adverse_change")(busy())
    if rec["status"] != "fired" or rec["severity"] != "red":
        bad.append("a liquidation published 86 days before the report is not a red recent change")
    if OLD_LIQ["ref"] in rec["citations"]:
        bad.append("a liquidation from 2019 counted as recent")
    dep = rl("recent_adverse_change")(report(changes=[STAY, GONE]))
    if dep["status"] != "fired" or GONE["ref"] not in dep["citations"]:
        bad.append("a director leaving in the latest file is not an adverse change")
    if rl("recent_adverse_change")(report(gazette=[OLD_LIQ]))["status"] == "fired":
        bad.append("an old liquidation alone fired the recent change")
    if rl("insolvency_notices")(report(gazette=[REMOVAL, RESTORED]))["status"] == "fired":
        bad.append("a removal notice fired insolvency-notices: a removal is not insolvency")
    near_only = report(subject=PERSON, standing=nearly(GAMMA), gazette=nearly(GAMMA_LIQ))
    for name in ("insolvency_notices", "people_failed_companies"):
        f = rl(name)(near_only)
        if f["status"] == "fired" and f["severity"] == "red":
            bad.append(f"near only: {name} is red on a namesake's companies")
        if f["status"] == "clear":
            bad.append(f"near only: {name} cleared what a namesake's companies show")
    new = co(9, "NEW CO LIMITED", registered="2026-07-02", first=AUG)
    founder = role(new, "f", "Ann LEE", first=AUG, appointed="2026-07-02")
    if rl("officer_churn")(report(subject=new, changes=[founder]))["status"] == "fired":
        bad.append("a founding director counted as churn")
    jan = co(8, "JANUARY CO LIMITED", registered="2026-01-10")
    if rl("officer_churn")(report(subject=jan, changes=[role(jan, "f", "Ann LEE", appointed="2026-01-10")]))["status"] == "fired":
        bad.append("a founding director in both files counted as a recent appointment")
    if rl("officer_churn")(report(changes=[STAY, GONE, CAME, role(ACME, "n", "Kim NG", appointed="2026-03-01")]))["severity"] != "amber":
        bad.append("three arrivals and departures with a departure are not amber churn")
    if rl("young_entity")(report(subject=new))["status"] != "fired":
        bad.append("a company registered three months ago is not young")
    if rl("prohibition")(person(people_notices=[OLD_PROHIB]))["severity"] == "red":
        bad.append("a prohibition that ended in 2006 is red")
    if rl("prohibition")(person(people_notices=[PROHIB]))["severity"] != "red":
        bad.append("a prohibition in force is not red")
    if rl("insolvency_notices")(short(person(gazette=[])))["status"] == "clear":
        bad.append("short walk: insolvency-notices cleared companies it never read")
    return bad


def test_the_properties_hold_on_the_rules_as_written():
    assert properties(R) == []


#: (what the mutant breaks, the text replaced, its replacement): each must be unique in rules.py and caught by properties()
MUTANTS = (
    ("status changes are taken as reachable", "STATES = False\n", "STATES = True\n"),
    ("the change list is oldest first", 'out.sort(key=lambda x: (x[0] or "", -x[1]), reverse=True)', 'out.sort(key=lambda x: (x[0] or "", -x[1]))'),
    ("a suppressed name is quoted", '    if it.get("suppressed"):\n        return f"a row whose name is suppressed', '    if False:\n        return f"a row whose name is suppressed'),
    ("the files held are read from the rows alone", "    out = set(FILES_MEASURED)", "    out = set()"),
    ("an office move prints the address", "    f\"{_month(nxt)}\" + (f\" filed as from", "    f\"{_month(nxt)} at {new[0]['title'] if new else ''}\" + (f\" filed as from"),
    ("a namesake's notices are red", 'return flag("insolvency-notices", V, "fired", "amber",', 'return flag("insolvency-notices", V, "fired", "red",'),
    ("a removal counts as insolvency", '"deed of company arrangement")\n', '"deed of company arrangement", "removal")\n'),
    ("a people check clears from a company", '    if _company_start(report):\n        return flag("people-failed-companies"',
     '    if False:\n        return flag("people-failed-companies"'),
    ("every notice is recent", "    recent = [it for it in notes if (_published(it) or dt.date.min) >= since]", "    recent = notes"),
    ("a founding director is churn", " and not founding(it)\n", "\n"),
    ("an ended prohibition is red", "PROHIBITION_RED_ENDED = False", "PROHIBITION_RED_ENDED = True"),
    ("a director leaving is not adverse", '(c[1] == 1 and views.get(c[3][0]) == "directors")', "(False)"),
)


@pytest.mark.parametrize("what,old,new", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_a_mutant_of_the_rules_is_caught(what, old, new):
    with open(os.path.join(HERE, "rules.py"), encoding="utf-8") as f:
        src = f.read()
    assert src.count(old) == 1, f"the mutant's target is not unique in rules.py: {old!r}"
    caught = properties(rules_module(src.replace(old, new)))
    assert caught, f"the mutant '{what}' passed every property: a check that cannot fail"


# ── each rule, on fixtures ──────────────────────────────────────────────────

def test_every_rule_runs_from_each_start_once_and_carries_no_common_rules_name():
    society = it("societies:societies/9", "societies", title="A CLUB INCORPORATED")
    for r in (report(), busy(), quiet(), person(), other(), report(subject=society)):
        flags = flags_of(R, r)
        assert len({f["rule"] for f in flags}) == len(flags) == len(R.RULES)
        assert not {f["rule"] for f in flags} & set(COMMON), "the builder runs the common rules; no copy here"
    assert R.flag is CONTRACT.flag and R.items is CONTRACT.items and R.section is CONTRACT.section and R.all_items is CONTRACT.all_items
    assert "common_rules" not in toml(), "the template keeps the builder's common rules"


def test_the_flag_contract_is_the_shapes():
    with pytest.raises(ValueError, match="cite"):
        R.flag("r", "0.1", "fired", "red", "x")
    with pytest.raises(ValueError, match="sources"):
        R.flag("r", "0.1", "clear", "red", "x")


def test_monthly_changes_lists_each_change_by_its_file_newest_first_and_never_clears():
    f = rule("monthly_changes")(busy())
    assert f["status"] == "fired" and f["severity"] == "info"
    t = f["text"]
    assert t.index("the September 2026 file: Bob KING arrived") < t.index("the August 2026 file")
    assert "Ann LEE arrived as director: first shown in the August 2026 file (appointed 2026-07-10, as the register files it)" in t
    assert "John SMITH left as director: last shown in the July 2026 file, not in the August 2026 file; the file states no end" in t
    assert "Dean WILSON's holding of record changed: 100 shares in the July 2026 file, 80 in the August 2026 file" in t
    assert "an office 67 companies share" in t and OFFICE_LINE not in t
    assert "a row whose name is suppressed" in t and HIDDEN not in t
    assert "the files held: companies-2026-07, companies-2026-08, companies-2026-09" in t and "not reachable" in t
    assert {GONE["ref"], CAME["ref"], LATER["ref"], HOLD_JUL["ref"], HOLD_AUG["ref"], OLD_OFFICE["ref"], NEW_OFFICE["ref"]} <= set(f["citations"])
    assert STAY["ref"] not in f["citations"], "a director in both files is no change"
    q = rule("monthly_changes")(quiet())
    assert q["status"] == "blocked" and "no clear is given" in q["text"] and "pub.company_states" in q["text"]


def test_monthly_changes_from_a_person_reads_the_persons_companies():
    f = rule("monthly_changes")(person(changes=[ON_GAMMA, role(GAMMA, "q", "Tom NEW", first=AUG)]))
    assert f["status"] == "fired" and "Tom NEW arrived" in f["text"] and "2 company(ies) the person has a confirmed row on" in f["text"]
    assert rule("monthly_changes")(short(person()))["status"] == "blocked"


def test_a_company_gone_from_the_latest_file_is_red_unless_removed_before():
    gone = co(5, "GONE LIMITED", status="Removed", registered="2020-01-01", last=JUL, in_latest=False)
    f = rule("recent_adverse_change")(report(subject=dict(gone, via=None)))
    assert f["status"] == "fired" and f["severity"] == "red" and "is not in the August 2026 file" in f["text"]
    earlier = dict(gone, row=dict(gone["row"], removed_on="2026-05-20"))
    assert rule("recent_adverse_change")(report(subject=dict(earlier, via=None)))["status"] == "blocked", "the file catching up is not news"
    assert "is not in the August 2026 file" in rule("monthly_changes")(report(subject=dict(earlier, via=None)))["text"]
    s = rule("entity_status")(report(subject=dict(earlier, via=None)))
    assert s["status"] == "fired" and s["severity"] == "red" and "removed 2026-05-20" in s["text"]


def test_recent_adverse_change_dates_each_fact_and_names_its_window():
    f = rule("recent_adverse_change")(busy())
    assert f["status"] == "fired" and f["severity"] == "red"
    assert set(f["citations"]) == {LIQ["ref"], WINDUP["ref"], REMOVAL["ref"]}, "the latest file is September: August's changes are not its"
    assert OLD_LIQ["ref"] not in f["citations"] and RESTORED["ref"] not in f["citations"]
    aug = rule("recent_adverse_change")(report(changes=[STAY, GONE, CAME, OLD_OFFICE, NEW_OFFICE]))
    assert aug["status"] == "fired" and aug["severity"] == "amber" and set(aug["citations"]) == {GONE["ref"], OLD_OFFICE["ref"], NEW_OFFICE["ref"]}
    assert "an office 67 companies share" in aug["text"] and CAME["ref"] not in aug["citations"], "an arrival is not adverse"
    assert "on or after 2026-07-23 (90 days before 2026-10-21)" in f["text"] and "side by side" in f["text"]
    amber = rule("recent_adverse_change")(report(gazette=[REMOVAL]))
    assert amber["status"] == "fired" and amber["severity"] == "amber"
    assert rule("recent_adverse_change")(quiet())["status"] == "blocked"


def test_officer_churn_counts_arrivals_departures_and_recent_appointments():
    f = rule("officer_churn")(busy())
    assert f["status"] == "fired" and f["severity"] == "amber"
    assert "2 director(s) left and 2 arrived between the files" in f["text"] and "1 change(s) among the holders of record" in f["text"]
    one = rule("officer_churn")(report(changes=[STAY, CAME]))
    assert one["status"] == "fired" and one["severity"] == "info"
    assert rule("officer_churn")(quiet())["status"] == "blocked"
    assert rule("officer_churn")(person())["status"] == "blocked" and "start a report from each company" in rule("officer_churn")(person())["text"]


def test_entity_status_states_status_type_age_and_the_latest_file():
    f = rule("entity_status")(quiet())
    assert f["status"] == "clear" and "15 year(s)" in f["text"] and "last shown in the August 2026 file" in f["text"]
    assert "the latest file held is the August 2026 file" in f["text"]
    g = rule("entity_status")(report(subject=dict(GAMMA, via=None)))
    assert g["status"] == "fired" and g["severity"] == "red" and "In Liquidation" in g["text"]
    off = dict(ACME, row=dict(ACME["row"], in_latest=False, last_file=JUL))
    assert rule("entity_status")(report(subject=off))["severity"] == "amber"
    assert rule("entity_status")(person())["status"] == "blocked"


def test_insolvency_and_register_events_on_the_entity():
    f = rule("insolvency_notices")(busy())
    assert f["status"] == "fired" and f["severity"] == "red" and set(f["citations"]) == {LIQ["ref"], OLD_LIQ["ref"], WINDUP["ref"]}
    assert f["text"].index("winding-up application") < f["text"].index("appointed 3 March 2019"), "newest first"
    e = rule("register_events")(busy())
    assert e["status"] == "fired" and "1 removal" in e["text"] and "1 restoration" in e["text"] and "none is an insolvency" in e["text"]
    assert rule("insolvency_notices")(quiet())["status"] == "clear"
    p = rule("insolvency_notices")(person())
    assert p["status"] == "fired" and p["citations"] == (GAMMA_LIQ["ref"],)


def test_people_failed_companies_from_a_person_and_blocked_from_a_company():
    f = rule("people_failed_companies")(person())
    assert f["status"] == "fired" and f["severity"] == "red" and "1 of the 2 company(ies)" in f["text"] and "1 are going" in f["text"]
    assert "GAMMA BUILD LIMITED (liquidation, appointed 1 May 2025)" in f["text"]
    c = rule("people_failed_companies")(busy())
    assert c["status"] == "blocked" and "start a report from each person" in c["text"]
    o = rule("other_current_companies")(person())
    assert o["status"] == "fired" and "DELTA LIMITED" in o["text"]


def test_prohibitions_and_bankruptcies_by_age_and_grade():
    p = rule("prohibition")(person(people_notices=[PROHIB]))
    assert p["status"] == "fired" and p["severity"] == "red" and "in force on 2026-10-21" in p["text"]
    old = rule("prohibition")(person(people_notices=[OLD_PROHIB]))
    assert old["status"] == "fired" and old["severity"] == "amber" and "ended before" in old["text"]
    assert rule("prohibition")(person(people_notices=nearly(PROHIB)))["severity"] == "amber"
    assert rule("prohibition")(person(people_notices=[dict(PROHIB, suppressed=True)]))["status"] == "clear"
    b = rule("bankruptcy")(person(people_notices=[BANKRUPT]))
    assert b["status"] == "fired" and b["severity"] == "red"
    stale = dict(BANKRUPT, row={"event_on": "2005-02-11"})
    s = rule("bankruptcy")(person(people_notices=[stale]))
    assert s["severity"] == "amber" and "Insolvency Register" in s["text"]
    r = person()
    r["walk"]["links_omitted"] = 4
    assert rule("bankruptcy")(r)["status"] == "blocked"


def test_young_entity_and_officers_of_record():
    new = co(9, "NEW CO LIMITED", registered="2026-07-02", first=AUG)
    f = rule("young_entity")(report(subject=new))
    assert f["status"] == "fired" and f["severity"] == "amber" and "3 month(s)" in f["text"]
    assert rule("young_entity")(quiet())["status"] == "clear"
    none_now = report(changes=[GONE])
    assert rule("officers_of_record")(none_now)["status"] == "fired"
    assert rule("officers_of_record")(quiet())["status"] == "clear"


def test_namesake_exposure_declares_the_report_partial_past_fifty():
    r = report(identity=[dict(NAMESAKE, ref=f"companies:companies/{i}/director/q") for i in range(55)])
    f = rule("namesake_exposure")(r)
    assert f["status"] == "fired" and f["severity"] == "amber" and "partial" in f["text"]
    assert rule("namesake_exposure")(report())["status"] == "clear"


def test_the_registers_not_held_block_and_never_clear():
    for name in ("status_name_changes", "since_date", "interface_freshness", "past_roles", "change_history", "securities_register",
                 "insolvency_register", "court_judgments", "credit_bureau", "mortgagee_possession"):
        for r in (busy(), person(), other()):
            assert rule(name)(r)["status"] == "blocked", name
    assert "Personal Property Securities Register" in rule("securities_register")(busy())["text"]
    assert "pub.company_states" in rule("status_name_changes")(busy())["text"]
    assert "since" in rule("since_date")(busy())["text"]


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
