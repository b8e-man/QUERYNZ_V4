"""Insurance underwriting on fixtures: it loads on the shape, names only
published views with their licences, runs its sections in the order an
underwriter reads them, and its rules keep the flag contract: a sister
company's failure is dated from its Gazette notice with the person's own
role on that company dated beside it, red only where a confirmed role began
on or before the failure and is still listed, never red through a hub, a
near link or a role that began after; a removal and a receiver's ceasing to
act are not a failure; officer churn does not count a new company's first
board and never clears; the safety record and every register it would read
are blocked, never clear; a check the walk could not have seen is blocked
(from a company its officers are not followed; a short walk; past roles not
held); a suppressed name is never counted; dates side by side, no word of
cause or ownership and no address in a flag. A mutant check breaks the rules
file on purpose, sixteen ways, and requires these properties to catch every
break.

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
ORDER = ["identity", "standing", "solvency", "people", "companies", "people-notices", "beside", "safety"]
COMMON = ("group-standing", "hubs-met", "replaced-return")
VIEWS = {"companies", "directors", "shareholders", "company_addresses", "gazette_liquidations", "gazette_liquidators", "gazette_company_notices",
         "gazette_appointments", "gazette_prohibitions", "gazette_bankruptcies", "societies", "society_officers"}
#: words that would join two facts as cause or call a holder an owner (the shape's rules 3 and 4 hold the full list on every report)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|behind|owners?|owns|owned|"
                   r"beneficial)\b", re.I)
HISTORY_CHECKS = ("sister_company_failure", "register_events", "other_current_companies")
PEOPLE_CHECKS = ("sister_company_failure", "other_current_companies", "prohibition", "bankruptcy", "practitioner_roles")
ALWAYS_BLOCKED = ("safety_record", "regulator_actions", "court_judgments", "tribunals", "change_history", "status_history",
                  "mortgagee_possession", "insolvency_register", "securities_register")


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


CONTRACT = by_path("qv4_test_report_contract_insurance", os.path.join(REPO, "products", "report", "contract.py"))


def rules_module(source: str = None):
    """As the shape's loader does: `contract` bound, then the file run; a
    mutant's source is run the same way."""
    if source is None:
        return by_path("qv4_test_insurance_rules", os.path.join(HERE, "rules.py"), contract=CONTRACT)
    mod = type(sys)("qv4_test_insurance_mutant")
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
    line = [x for x in out.stdout.splitlines() if x.startswith("insurance ")]
    assert line and HERE in line[0], out.stdout
    t = toml()
    assert f"{len(t['reads'])} views, {len(t['sections'])} sections, {len(R.RULES)} rules" in line[0]


def test_it_names_only_the_views_the_brief_names_each_once_with_its_licence():
    t = toml()
    views = [r["view"] for r in t["reads"]]
    assert len(views) == len(set(views)) and set(views) == VIEWS and t["depth"] == 2
    assert all(r.get("licence") and r.get("attribution") and r.get("refresh") for r in t["reads"])
    assert "registered offices only, never a residential address" in [r for r in t["reads"] if r["view"] == "company_addresses"][0]["licence"]
    for unreached in ("company_states", "gazette_possessions"):
        assert unreached not in views, "the catalogue does not know it: carded, named in the flags"
    src = open(os.path.join(HERE, "template.toml"), encoding="utf-8").read()
    assert "the-catalogue-does-not-know-gazette-possessions" in src


def test_its_sections_run_in_the_underwriters_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"] and "companies" not in s["identity"]["views"], \
        "an entity is filed in the first section naming its view: a confirmed company never lands with the namesakes"
    assert s["standing"]["views"] == ["company_addresses"]
    assert set(s["solvency"]["views"]) == {"gazette_liquidations", "gazette_company_notices"} and "pointing" in s["solvency"]["sources"]
    assert "pointing" not in {x for sec in t["sections"] if sec["name"] != "solvency" for x in sec.get("sources", [])}
    assert s["people"]["views"] == ["directors", "shareholders"] and "roles" in s["people"]["sources"]
    assert s["companies"]["views"] == ["companies"]
    assert set(s["people-notices"]["views"]) == {"gazette_prohibitions", "gazette_bankruptcies"}
    assert "second" in s["beside"]["sources"] and "second" not in {x for sec in t["sections"] if sec["name"] != "beside" for x in sec.get("sources", [])}
    assert s["safety"]["views"] == [] and {"courts", "insolvency", "securities", "fsp"} <= set(s["safety"]["not_held"])
    for named in ("WorkSafe", "enforceable undertakings", "Commerce Commission", "Financial Markets Authority", "court judgments",
                  "Employment Relations Authority", "Disputes Tribunal", "Fire and Emergency", "16 August 2026"):
        assert named in s["safety"]["text"], named
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views
        assert not CAUSE.search(x["text"]) and not CAUSE.search(x["heading"]), x["name"]


def test_the_known_limits_page_and_the_checkpoint_list_exist():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    for want in ("namesake", "not a clear", "checkpoint", "WorkSafe", "never clear", "sister"):
        assert want in page, want
    lim = toml()["limits"]
    assert any("safety record is not held" in x for x in lim) and any("does not yet follow" in x for x in lim)
    with open(os.path.join(HERE, "checkpoint.list"), encoding="utf-8") as f:
        keys = [x.strip() for x in f if x.strip() and not x.startswith("#")]
    assert len(keys) == 12 and len(set(keys)) == 12 and all(re.match(r"^[a-z_]+:\S+$", k) for k in keys), "twelve register keys, one a line"


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "society_officers": "person", "gazette_prohibitions": "person",
        "gazette_bankruptcies": "person", "gazette_liquidators": "person", "companies": "organisation", "societies": "organisation",
        "company_addresses": "place", "gazette_company_notices": "organisation", "gazette_liquidations": "organisation"}
THROUGH = "a connection that passes through more than one person is listed as near, never confirmed (the design's default)"


def it(ref, view, grade="confirmed", title="X", statement=None, dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False,
       kind=None, entity_title=None, flags=(), rule_=None):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": kind or KIND[view], "title": title,
            "statement": statement or f"{title}: a row", "dates": {"undated": dates == "undated", "text": dates},
            "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1, "grade": grade,
            "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": list(flags), "replaced_by": None, "entity_title": entity_title,
            "rule": rule_}


def company(n, title, status, registered, **kw):
    return it(f"companies:companies/{n}", "companies", title=title, statement=f"{title}: {status} LTD, NZBN {n}",
              dates=f"from {registered}; no end filed (in the latest file)",
              row={"key": f"companies/{n}", "nzbn": str(n), "status": status, "entity_type": "LTD", "registered_on": registered, "in_latest": True}, **kw)


def director(n, letter, title, appointed, company_title, via=None, in_latest=True, grade="confirmed", reason=None):
    return it(f"companies:companies/{n}/director/{letter}", "directors", grade=grade, title=title,
              statement=f"{title}: DIRECTOR of {company_title}", dates=f"from {appointed}; no end filed (in the latest file)", via=via,
              row={"entity_key": f"companies/{n}", "role_type": "DIRECTOR", "appointed_on": appointed, "in_latest": in_latest}, reason=reason)


FAILED = company(1, "ACME FREIGHT LIMITED", "In Liquidation", "2011-03-03")
NEWCO = company(2, "KEA LOGISTICS LIMITED", "Registered", "2020-09-01")
GAMMA = company(3, "GAMMA STORAGE LIMITED", "In Receivership", "2015-05-01")
OLDCO = company(4, "DELTA LIMITED", "Registered", "2001-05-01")
LIQ = it("gazette:gazette/2020-al1/company/1", "gazette_liquidations", title="ACME FREIGHT LIMITED", dates="appointed 13 July 2020",
         row={"register_key": "companies/1", "appointed_on": "2020-07-13", "published_on": "2020-07-15", "appointed_by": "court"}, via=FAILED["ref"])
RECEIVER = it("gazette:gazette/2023-ar1/company/1", "gazette_company_notices", title="GAMMA STORAGE LIMITED · receivership",
              dates="appointed 23 July 2023", via=GAMMA["ref"],
              row={"kind": "receivership", "action": "appointment", "event_basis": "appointment", "register_key": "companies/3", "event_on": "2023-07-23"})
REMOVAL = it("gazette:gazette/2020-ds1/company/9", "gazette_company_notices", title="DELTA LIMITED · removal", via=OLDCO["ref"],
             dates="objections by 17 August 2020; published 20 July 2020",
             row={"kind": "removal", "action": "intention to remove", "event_basis": "objections by", "register_key": "companies/4",
                  "event_on": "2020-08-17", "published_on": "2020-07-20"})
CEASED = it("gazette:gazette/2020-ar9/company/1", "gazette_company_notices", title="DELTA LIMITED · receivership", via=OLDCO["ref"],
            dates="ceased to act 14 July 2020", row={"kind": "receivership", "action": "ceased to act", "event_basis": "ceased to act",
                                                     "register_key": "companies/4", "event_on": "2020-07-14", "published_on": "2020-07-16"})
#: a winding-up application on ACME a year before the person joined its board: an application is not the failure's date
APPLICATION = it("gazette:gazette/2010-aw1/company/1", "gazette_company_notices", title="ACME FREIGHT LIMITED · winding-up application",
                 dates="to be heard 2 March 2010; published 1 February 2010", via=FAILED["ref"],
                 row={"kind": "winding-up application", "action": "application", "event_basis": "hearing", "register_key": "companies/1",
                      "event_on": "2010-03-02", "published_on": "2010-02-01"})
#: the person: a director of ACME from 2011, so on its board on the day its liquidator was appointed (13 July 2020)
PERSON = director(1, "a", "Jane Mary DOE", "2011-03-03", "ACME FREIGHT LIMITED")
ON_NEWCO = director(2, "a", "Jane Mary DOE", "2020-09-01", "KEA LOGISTICS LIMITED")
ON_OLDCO = director(4, "a", "Jane Mary DOE", "2001-05-01", "DELTA LIMITED")
#: the same person appointed to ACME only after its liquidator was
LATE = director(1, "a", "Jane Mary DOE", "2021-01-10", "ACME FREIGHT LIMITED")
PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", title="Jane Mary Doe · prohibition",
            dates="from 22 September 2022; to 22 September 2027", row={"ends_on": "2027-09-22"})
BANKRUPT = it("gazette:gazette/2019-ba1/person/1", "gazette_bankruptcies", title="DOE · Jane Mary", dates="adjudicated 2 May 2019",
              row={"kind": "adjudication", "event_on": "2019-05-02"})
CO_A = it("companies:companies/1/director/z", "directors", grade="near", title="John SMITH", via=FAILED["ref"], entity_title="ACME FREIGHT LIMITED",
          reason=THROUGH, row={"entity_key": "companies/1", "in_latest": True})
PRO_HUB = {"ref": PERSON["ref"], "title": "Jane Mary DOE", "kind": "professional-director", "text": "a professional director: 80 directorships",
           "evidence": {"directorships": 80}}
#: from the going company: its first board (at registration) and two directors appointed this year
FIRST = director(2, "f", "Ann FIRST", "2020-09-01", "KEA LOGISTICS LIMITED", via=NEWCO["ref"])
NEW1 = director(2, "n", "Bob NEW", "2026-03-02", "KEA LOGISTICS LIMITED", via=NEWCO["ref"])
NEW2 = director(2, "m", "Cat NEWER", "2026-06-15", "KEA LOGISTICS LIMITED", via=NEWCO["ref"])
GONE = director(2, "g", "Dan GONE", "2020-09-01", "KEA LOGISTICS LIMITED", via=NEWCO["ref"], in_latest=False)
OWN_LIQ = dict(LIQ, ref="gazette:gazette/2026-al5/company/2", title="KEA LOGISTICS LIMITED", via=NEWCO["ref"], dates={"undated": False,
               "text": "appointed 1 August 2026"},
               row=dict(LIQ["row"], register_key="companies/2", appointed_on="2026-08-01"))
OWN_REMOVAL = dict(REMOVAL, ref="gazette:gazette/2026-ds5/company/2", via=NEWCO["ref"], row=dict(REMOVAL["row"], register_key="companies/2"))
OWN_CEASED = dict(CEASED, ref="gazette:gazette/2026-ar5/company/2", via=NEWCO["ref"], row=dict(CEASED["row"], register_key="companies/2"))


def report(subject=PERSON, hubs=(), **sections):
    out = {"found": True, "as_of": "2026-10-21", "subject": subject, "members": [], "flags": [], "hubs": list(hubs),
           "group": {"built": True, "size": 1, "contested": False, "omitted": 0},
           "walk": {"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0}, "sections": []}
    for name in ORDER:
        items = sections.get(name.replace("-", "_"), [])
        out["sections"].append({"name": name, "heading": name, "items": items, "omitted": 0, "omitted_views": [],
                                "blank": None if items else "none found"})
    return out


def person(**kw):
    """A director of a company liquidated on 13 July 2020 (from 2011), of a going company registered in 2020, and of an old company
    with a removal notice; a fourth company, in receivership, is reached with no role of the person's on it."""
    parts = dict(people=[ON_NEWCO, ON_OLDCO], companies=[FAILED, NEWCO, GAMMA, OLDCO], beside=[CO_A], solvency=[LIQ, RECEIVER, REMOVAL])
    parts.update(kw)
    return report(**parts)


def from_company(subject=NEWCO, **kw):
    """Started from the going company: its first board and nothing in the Gazette."""
    parts = dict(people=[FIRST])
    parts.update(kw)
    return report(subject=dict(subject, via=None), **parts)


def short(r):
    r["walk"]["entities_not_expanded"] = 3
    return r


def nearly(*xs):
    return [dict(x, grade="near", reason="reached through a near link: the two rows share a first and last name") for x in xs]


def flags_of(mod, r):
    return [fn(r) for fn in mod.RULES]


# ── the properties, each a list of what broke (empty when they hold) ────────

def properties(mod) -> list:
    """What an underwriter relies on, checked on fixtures; the mutant check
    runs it on each broken copy of the rules and needs it to say something.
    First with the past roles not held (as published today), then held."""
    bad = []
    rl = lambda n: rule(n, mod)   # noqa: E731
    mod.HISTORY = False
    for name in HISTORY_CHECKS:
        for r in (report(companies=[OLDCO], people=[ON_OLDCO]), report()):
            if rl(name)(r)["status"] == "clear":
                bad.append(f"past roles not held: {name} cleared a person whose past companies it cannot see")
    for r in (from_company(), from_company(people=[])):
        if rl("officer_churn")(r)["status"] == "clear":
            bad.append("past roles not held: officer-churn cleared a board whose departures it cannot see")
    mod.HISTORY = True
    starts = {"person": person(), "company": from_company(people=[FIRST, NEW1, NEW2, GONE], solvency=[OWN_LIQ, OWN_REMOVAL]),
              "other": report(subject=it("societies:societies/9", "societies", title="A CLUB")), "empty": report()}
    for start, r in starts.items():
        for f in flags_of(mod, r):
            if CAUSE.search(f["text"]):
                bad.append(f"{start}: {f['rule']} says a word of cause or ownership: {f['text'][:120]}")
            if CONTRACT.address_shaped(f["text"]):
                bad.append(f"{start}: {f['rule']} prints an address: {f['text'][:120]}")
    for name in PEOPLE_CHECKS:
        for r in (from_company(), starts["other"]):
            if rl(name)(r)["status"] == "clear":
                bad.append(f"{r['subject']['view']} start: {name} cleared the people it never followed")
    for name in ALWAYS_BLOCKED:
        for r in (person(), from_company(), report()):
            if rl(name)(r)["status"] != "blocked":
                bad.append(f"{name} is not blocked: the register it reads is not held")
    # the sister company: a confirmed role from before the failure, red; after it, a hub, a near link: never red
    f = rl("sister_company_failure")(person())
    if not (f["status"] == "fired" and f["severity"] == "red" and LIQ["ref"] in f["citations"] and PERSON["ref"] in f["citations"]):
        bad.append(f"a director of a company on the day its liquidator was appointed did not raise sister-company-failure red: {f['status']} "
                   f"{f['severity']}")
    late = rl("sister_company_failure")(person(subject=LATE, companies=[FAILED, NEWCO], solvency=[LIQ]))
    if late["severity"] == "red":
        bad.append("a role that began after the failure date raised sister-company-failure red")
    hub = person()
    hub["hubs"] = [PRO_HUB]
    if rl("sister_company_failure")(hub)["severity"] == "red":
        bad.append("sister-company-failure was red through a professional director: a hub sits on many companies")
    if rl("sister_company_failure")(person(companies=nearly(FAILED), solvency=nearly(LIQ), subject=ON_OLDCO))["severity"] == "red":
        bad.append("sister-company-failure was red on a namesake's company")
    undated = rl("sister_company_failure")(person(companies=[FAILED, NEWCO], solvency=[]))
    if undated["severity"] == "red":
        bad.append("an undated failure (status only) raised sister-company-failure red: no date to set the role beside")
    removal_only = rl("sister_company_failure")(report(subject=ON_OLDCO, companies=[OLDCO], solvency=[REMOVAL]))
    if removal_only["status"] == "fired":
        bad.append("a removal from the register was read as a sister company's failure")
    if rl("sister_company_failure")(person(solvency=[APPLICATION, LIQ, RECEIVER]))["severity"] != "red":
        bad.append("a winding-up application dated the failure before the liquidator's appointment did")
    if rl("sister_company_failure")(person(companies=nearly(FAILED) + [NEWCO], solvency=nearly(LIQ)))["severity"] != "red":
        bad.append("the start row's own company, filed near in a contested group, was read as a namesake's")
    if rl("sister_company_failure")(short(report(subject=ON_OLDCO, companies=[OLDCO])))["status"] == "clear":
        bad.append("short walk: sister-company-failure cleared companies it never read")
    # the entity's own record
    own = rl("insolvency_event")(from_company(solvency=[OWN_LIQ]))
    if not (own["status"] == "fired" and own["severity"] == "red"):
        bad.append("a liquidation on the entity did not raise insolvency-event red")
    for what, notice in (("a removal", OWN_REMOVAL), ("a receiver ceasing to act", OWN_CEASED)):
        if rl("insolvency_event")(from_company(solvency=[notice]))["status"] == "fired":
            bad.append(f"{what} on the entity raised insolvency-event")
    if rl("register_events")(from_company(solvency=[OWN_REMOVAL]))["status"] != "fired":
        bad.append("a removal notice on the entity did not raise register-events")
    young = dict(NEWCO, row=dict(NEWCO["row"], registered_on="2025-06-01"))
    if rl("young_entity")(from_company(subject=young))["status"] != "fired":
        bad.append("an entity registered 16 months ago did not raise young-entity")
    if rl("young_entity")(from_company())["status"] == "fired":
        bad.append("an entity registered six years ago raised young-entity")
    churn = rl("officer_churn")(from_company(people=[FIRST, NEW1, NEW2]))
    if churn["status"] != "fired":
        bad.append("two directors appointed this year did not raise officer-churn")
    first_board = dict(NEWCO, row=dict(NEWCO["row"], registered_on="2026-03-01"))
    if rl("officer_churn")(from_company(subject=first_board, people=[NEW1]))["status"] == "fired" or \
            rl("officer_churn")(from_company(subject=first_board, people=[dict(NEW1, ref="x:1"), dict(NEW2, row=dict(NEW2["row"],
                                                                                                      appointed_on="2026-03-01"))]))["status"] == "fired":
        bad.append("a new company's first board was counted as officer churn")
    # the people's notices
    for name, row in (("prohibition", PROHIB), ("bankruptcy", BANKRUPT)):
        if rl(name)(report(people_notices=[dict(row, suppressed=True)]))["status"] == "fired":
            bad.append(f"a revoked or withheld {name} was counted")
        if rl(name)(report(people_notices=nearly(row)))["severity"] == "red":
            bad.append(f"a namesake's {name} was red")
        if rl(name)(report(people_notices=[row]))["status"] != "fired":
            bad.append(f"a confirmed {name} did not fire")
    return bad


def test_the_properties_hold_on_the_rules_as_written(held):
    assert properties(R) == []


#: (what the mutant breaks, the text replaced, its replacement): each must be unique in rules.py and caught by properties()
MUTANTS = (
    ("the role's date is never set beside the failure", 'if f["date"] and start and start <= f["date"] and _current(r):', "if True:"),
    ("a hub raises the flag red", "red = bool(on) and not hub", "red = bool(on)"),
    ("an undated failure is red", "red = bool(on) and not hub", "red = not hub"),
    ("a removal is a failure", "if c not in by_ref or not _insolvency(n):", "if c not in by_ref:"),
    ("a receiver ceasing dates a failure", ' and "ceas" not in (r.get("action") or "").lower()', ""),
    ("a namesake's failure is red", 'return flag("sister-company-failure", V, "fired", "amber",\n                    f"{len(nearby)}',
     'return flag("sister-company-failure", V, "fired", "red",\n                    f"{len(nearby)}'),
    ("a short walk is never short", 'return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))', "return False"),
    ("a person's notice clears from a company", '    if _company_start(report):\n        return flag(rule, V, "blocked", severity',
     '    if False:\n        return flag(rule, V, "blocked", severity'),
    ("a clear is given though past roles are not held", "    if HISTORY:\n        return flag(rule, V, \"clear\", severity, text, **kw)",
     "    if True:\n        return flag(rule, V, \"clear\", severity, text, **kw)"),
    ("a revoked prohibition is counted", "live = [it for it in items(report, (view,)) if not it.get(\"suppressed\")]", "live = list(items(report, (view,)))"),
    ("a new company's first board is churn", " and not (reg and (start - reg).days <= AT_START_DAYS)", ""),
    ("the safety record clears", 'return flag("safety-record", V, "blocked", "red",\n',
     'return flag("safety-record", V, "clear", "red", sources_held=("pub.companies",), text=\n'),
    ("the entity is never young", "(as_of - reg).days < YOUNG_DAYS]", "(as_of - reg).days < 0]"),
    ("an application dates the failure", "rank = (0 if _appointment(n) else 1, d) if d else None", "rank = (0, d) if d else None"),
    ("the start row's own company can be near", '("confirmed" if it["ref"] == own else it["grade"]) in grades]', 'it["grade"] in grades]'),
    ("a flag joins two facts", 'mine += ", on or before the failure date and still listed"',
     'mine += ", on or before the failure date and still listed, because of the person"'),
)


@pytest.mark.parametrize("what,old,new", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_a_mutant_of_the_rules_is_caught(what, old, new):
    with open(os.path.join(HERE, "rules.py"), encoding="utf-8") as f:
        src = f.read()
    assert src.count(old) == 1, f"the mutant's target is not unique in rules.py: {old!r}"
    caught = properties(rules_module(src.replace(old, new)))
    assert caught, f"the mutant '{what}' passed every property: a check that cannot fail"


# ── each rule, on fixtures ──────────────────────────────────────────────────

@pytest.fixture
def held():
    """The setting a lane publishing past roles would allow: HISTORY on."""
    R.HISTORY = True
    yield
    R.HISTORY = False


def test_while_past_roles_are_not_held_the_history_checks_fire_or_block_and_never_clear():
    R.HISTORY = False
    assert "HISTORY = False" in open(os.path.join(HERE, "rules.py"), encoding="utf-8").read()
    for name in HISTORY_CHECKS:
        f = rule(name)(report())
        assert f["status"] == "blocked" and "current roles only" in f["text"], (name, f)
    c = rule("officer_churn")(from_company())
    assert c["status"] == "blocked" and "a director who left the board before July 2026 is not seen" in c["text"]
    assert rule("sister_company_failure")(person())["status"] == "fired", "what is seen still fires"
    p = rule("past_roles")(report(subject=dict(PERSON, row=dict(PERSON["row"], in_latest=False))))
    assert p["status"] == "blocked" and "1 of the rows listed left the file" in p["text"]


def test_every_rule_runs_from_each_start_once_and_carries_no_common_rules_name():
    society = it("societies:societies/9", "societies", title="A CLUB INCORPORATED")
    for r in (report(), person(), from_company(), from_company(people=[], solvency=[]), report(subject=society)):
        flags = flags_of(R, r)
        assert len({f["rule"] for f in flags}) == len(flags) == len(R.RULES)
        assert not {f["rule"] for f in flags} & set(COMMON), "the builder runs the common rules; no copy here"
    assert R.flag is CONTRACT.flag and R.items is CONTRACT.items and R.section is CONTRACT.section and R.all_items is CONTRACT.all_items
    assert "common_rules" not in toml(), "the template keeps the builder's common rules"


def test_a_sister_companys_failure_is_dated_from_its_notice_with_the_persons_role_beside_it(held):
    f = rule("sister_company_failure")(person())
    assert f["status"] == "fired" and f["severity"] == "red" and f["scope"] == "officer-group"
    assert "ACME FREIGHT LIMITED: liquidation (liquidator appointed by the court), appointed 13 July 2020" in f["text"]
    assert "the person's row: DIRECTOR, from 2011-03-03, on or before the failure date and still listed" in f["text"]
    assert "GAMMA STORAGE LIMITED: receivership, appointed 23 July 2023 | no role or holding of the person's on it" in f["text"]
    assert "2 company(ies) the person has a confirmed row on are in an insolvency, 1 with the person's role" in f["text"]
    assert {FAILED["ref"], LIQ["ref"], PERSON["ref"]} <= set(f["citations"]) and NEWCO["ref"] not in f["citations"]
    late = rule("sister_company_failure")(person(subject=LATE, companies=[FAILED, NEWCO], solvency=[LIQ]))
    assert late["status"] == "fired" and late["severity"] == "amber" and "from 2021-01-10, after the failure date" in late["text"]
    hub = person()
    hub["hubs"] = [PRO_HUB]
    h = rule("sister_company_failure")(hub)
    assert h["severity"] == "amber" and "the person is a hub (professional-director)" in h["text"]
    blocked = rule("sister_company_failure")(from_company())
    assert blocked["status"] == "blocked" and "start a report from each person listed" in blocked["text"]


def test_the_entitys_own_solvency_record_is_dated_from_each_notice():
    f = rule("insolvency_event")(from_company(solvency=[OWN_REMOVAL, OWN_LIQ]))
    assert f["status"] == "fired" and f["severity"] == "red" and f["scope"] == "entity"
    assert f["citations"] == (OWN_LIQ["ref"],) and "1 liquidation" in f["text"] and "appointed 1 August 2026" in f["text"]
    assert rule("insolvency_event")(from_company())["status"] == "clear"
    status_only = rule("insolvency_event")(from_company(subject=FAILED))
    assert status_only["status"] == "fired" and "undated here" in status_only["text"]
    e = rule("register_events")(from_company(solvency=[OWN_REMOVAL]))
    assert e["status"] == "fired" and e["severity"] == "amber" and "none is an insolvency" in e["text"]
    s = rule("entity_status")(from_company(subject=FAILED))
    assert s["status"] == "fired" and s["severity"] == "red" and "'In Liquidation'" in s["text"]
    assert rule("entity_status")(from_company())["status"] == "clear"


def test_officer_churn_counts_this_years_appointments_and_the_rows_that_left_never_the_first_board(held):
    f = rule("officer_churn")(from_company(people=[FIRST, NEW1, NEW2, GONE]))
    assert f["status"] == "fired" and f["severity"] == "amber"
    assert "2 of 3 current director(s) appointed in the 365 days" in f["text"] and "1 director row(s) left the companies file" in f["text"]
    assert f["text"].index("Bob NEW") < f["text"].index("Cat NEWER") and "Ann FIRST" not in f["text"]
    assert rule("officer_churn")(from_company())["status"] == "clear", "with past roles held, one director since registration clears"
    none = rule("officer_churn")(from_company(people=[]))
    assert none["status"] == "fired" and "no current director" in none["text"]
    assert rule("officer_churn")(person())["status"] == "blocked"
    suppressed = rule("officer_churn")(from_company(people=[dict(NEW1, suppressed=True), NEW2]))
    assert "Bob NEW" not in suppressed["text"] and "name suppressed" in suppressed["text"]


def test_young_entity_is_amber_on_the_entity_and_info_on_the_persons_companies(held):
    young = dict(NEWCO, row=dict(NEWCO["row"], registered_on="2025-06-01"))
    f = rule("young_entity")(from_company(subject=young))
    assert f["status"] == "fired" and f["severity"] == "amber" and "2025-06-01" in f["text"]
    g = rule("young_entity")(person(companies=[FAILED, young]))
    assert g["status"] == "fired" and g["severity"] == "info"


def test_the_safety_record_and_every_register_not_held_block_and_never_clear():
    for name in ALWAYS_BLOCKED:
        for r in (person(), from_company(), report()):
            assert rule(name)(r)["status"] == "blocked", name
    s = rule("safety_record")(from_company())
    assert s["severity"] == "red" and "WorkSafe" in s["text"] and "finding of none" in s["text"]
    assert any("enforceable undertakings" in x for x in s["sources_not_held"]) and any("Fire and Emergency" in x for x in s["sources_not_held"])
    assert "Commerce Commission" in rule("regulator_actions")(person())["text"]
    assert "Disputes Tribunal" in rule("tribunals")(person())["text"]
    assert "16 August 2026" in rule("change_history")(person())["text"] and "industry classification" in rule("change_history")(person())["text"]
    assert "pub.company_states" in rule("status_history")(person())["text"]
    assert "pub.gazette_possessions" in rule("mortgagee_possession")(person())["text"]


def test_a_register_name_with_a_word_of_cause_is_not_quoted_in_a_flag(held):
    behind = dict(FAILED, title="BEHIND THE SCENES LIMITED")
    f = rule("sister_company_failure")(person(companies=[behind, NEWCO]))
    assert f["status"] == "fired" and "BEHIND" not in f["text"] and FAILED["ref"] in f["text"]


def test_namesake_exposure_declares_the_report_partial_past_fifty():
    namesake = it("companies:companies/77/director/q", "directors", grade="near", title="Jane DOE")
    r = report(identity=[dict(namesake, ref=f"companies:companies/{i}/director/q") for i in range(55)])
    f = rule("namesake_exposure")(r)
    assert f["status"] == "fired" and f["severity"] == "amber" and "partial" in f["text"]
    assert rule("namesake_exposure")(report())["status"] == "clear"


def test_the_presentation_rules_hold_on_every_flag_from_every_start(held):
    """The shape's own check (rule 9 and rule 3 on fired flags), run on the
    flags each start produces, as the builder runs it on a finished report."""
    for r in (person(), from_company(people=[FIRST, NEW1, NEW2, GONE], solvency=[OWN_LIQ]), report(),
              report(subject=it("societies:societies/9", "societies", title="A CLUB"))):
        r["flags"] = flags_of(R, r)
        problems = [p for p in CONTRACT.presentation_problems(r) if p.startswith("flag ")]
        assert problems == [], problems


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
