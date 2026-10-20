"""The legal counterparty and conflict check on fixtures: it loads on the
shape, names only published views with their licences, runs its sections in
the order a conflicts clerk reads them, and its rules keep the flag contract:
no flag ever clears a conflict (the firm's client list is not an input); the
party's own notices are red, a namesake's amber at most; a check the walk
could not have seen is blocked (from a company its officers are not followed;
a short walk; past roles not held); a removal or an amalgamation is not an
insolvency, and a deed of company arrangement is one; a suppressed name is
never counted; dates side by side and no word of cause or of ownership. A
mutant check breaks the rules file on purpose, eleven ways, and requires
these properties to catch every break.

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
ORDER = ["identity", "officers", "web", "gazette", "money", "not-held"]
COMMON = ("group-standing", "hubs-met", "replaced-return")
#: words that would join two facts as cause or call a holder an owner (the shape's rules 3 and 4 hold the full list on every report)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|behind|owners?|owns|owned|"
                   r"beneficial)\b", re.I)
#: words that would say there is no conflict: absence is not a finding
NO_CONFLICT = re.compile(r"\b(no conflict|conflict[- ]free|not conflicted|cleared to act|safe to act)\b", re.I)
GAZETTE = {"gazette_liquidations", "gazette_company_notices", "gazette_liquidators", "gazette_prohibitions", "gazette_bankruptcies"}
HISTORY_CHECKS = ("company_status", "insolvency_notices", "repeat_insolvency", "amalgamation", "register_events")
PEOPLE_CHECKS = ("conflict_web", "shared_boards", "repeat_insolvency", "prohibition", "practitioner_roles", "charity_officer_roles", "bankruptcy")
ALWAYS_BLOCKED = ("client_overlap", "mortgagee_possession", "bankruptcy", "court_judgments", "disciplinary_findings", "comcom_coverage",
                  "securities_register", "charity_integrity_marks")


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


CONTRACT = by_path("qv4_test_report_contract_legal", os.path.join(REPO, "products", "report", "contract.py"))


def rules_module(source: str = None):
    """As the shape's loader does: `contract` bound, then the file run; a
    mutant's source is run the same way."""
    if source is None:
        return by_path("qv4_test_legal_rules", os.path.join(HERE, "rules.py"), contract=CONTRACT)
    mod = type(sys)("qv4_test_legal_mutant")
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
    line = [x for x in out.stdout.splitlines() if x.startswith("legal ")]
    assert line and HERE in line[0], out.stdout
    t = toml()
    assert f"{len(t['reads'])} views, {len(t['sections'])} sections, {len(R.RULES)} rules" in line[0]


def test_it_names_each_view_once_with_its_licence_and_fewer_than_the_shape():
    t = toml()
    views = [r["view"] for r in t["reads"]]
    assert len(views) == len(set(views)) and t["depth"] == 2, "depth 2: the people on the person's companies are the conflict web"
    assert all(r.get("licence") and r.get("attribution") and r.get("refresh") for r in t["reads"])
    with open(os.path.join(REPO, "products", "report", "templates", "subject", "template.toml"), "rb") as f:
        shape = {r["view"] for r in tomllib.load(f)["reads"]}
    assert set(views) < shape, "a use-case template names fewer views than the shape's"
    for unreached in ("gazette_appointments", "gazette_practitioners"):
        assert unreached not in views, "no link reaches it: reading it would print a blank that is not a clear"
    assert "gazette_liquidators" in views, "a liquidator's row is joined to a director's by the link rules: a practitioner's own appointments"


def test_its_sections_run_in_the_conflicts_clerks_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"], "the first section holds the namesakes and nothing confirmed"
    assert not set(s["identity"]["views"]) & GAZETTE, "a near Gazette notice stays in its own section"
    assert "roles" in s["officers"]["sources"] and "companies" not in s["officers"]["views"], "the officers of record, then the companies"
    assert s["web"]["views"][0] == "companies" and "second" in s["web"]["sources"], "each company of the web heads the people on it"
    assert "second" not in {x for sec in t["sections"] if sec["name"] != "web" for x in sec.get("sources", [])}
    assert set(s["gazette"]["views"]) == GAZETTE and "pointing" in s["gazette"]["sources"]
    for kind in ("liquidations", "receiverships", "administrations", "winding-up", "creditors' notices", "deeds of company arrangement", "removals",
                 "restorations", "amalgamations", "rectifications", "transfers out", "prohibitions"):
        assert kind in s["gazette"]["text"].lower(), kind
    assert "charities" in s["money"]["not_held"]
    assert {"courts", "insolvency", "securities"} <= set(s["not-held"]["not_held"]) and s["not-held"]["views"] == []
    assert "Disciplinary Tribunal" in s["not-held"]["text"] and "client and matter list" in s["not-held"]["text"]
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views
        assert not CAUSE.search(x["text"]) and not CAUSE.search(x["heading"]), x["name"]
        assert not NO_CONFLICT.search(x["text"]), x["name"]


def test_the_known_limits_page_and_the_checkpoint_list_exist():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    assert "namesake" in page and "not a clear" in page and "checkpoint" in page.lower() and "client" in page
    lim = toml()["limits"]
    assert any("namesake" in x for x in lim) and any("not a clear" in x for x in lim) and any("does not yet follow" in x for x in lim)
    assert any("client and matter list" in x for x in lim)
    with open(os.path.join(HERE, "checkpoint.list"), encoding="utf-8") as f:
        keys = [x.strip() for x in f if x.strip() and not x.startswith("#")]
    assert len(keys) == 12 and len(set(keys)) == 12 and all(re.match(r"^[a-z_]+:\S+$", k) for k in keys), "twelve register keys, one a line"


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "society_officers": "person", "gazette_prohibitions": "person",
        "gazette_bankruptcies": "person", "gazette_liquidators": "person", "companies": "organisation", "societies": "organisation",
        "company_addresses": "place", "gazette_company_notices": "organisation", "gazette_liquidations": "organisation",
        "party_return_donors": "figure"}
THROUGH = "a connection that passes through more than one person is listed as near, never confirmed (the design's default)"


def it(ref, view, grade="confirmed", title="X", statement=None, dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False,
       kind=None, entity_title=None, flags=()):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": kind or KIND[view], "title": title,
            "statement": statement or f"{title}: a row", "dates": {"undated": dates == "undated", "text": dates},
            "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1, "grade": grade,
            "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": list(flags), "replaced_by": None, "entity_title": entity_title}


ACME = it("companies:companies/1", "companies", title="ACME TRADING LIMITED", statement="ACME TRADING LIMITED: In Liquidation LTD, NZBN 1",
          dates="from 3 March 2011; no end filed (in the latest file)",
          row={"key": "companies/1", "nzbn": "1", "status": "In Liquidation", "entity_type": "LTD", "registered_on": "2011-03-03", "in_latest": True})
GAMMA = it("companies:companies/3", "companies", title="GAMMA BUILD LIMITED", dates="from 1 May 2015; no end filed (in the latest file)",
           row={"key": "companies/3", "status": "In Receivership", "registered_on": "2015-05-01", "in_latest": True})
GOING = it("companies:companies/4", "companies", title="DELTA LIMITED", dates="from 1 May 2001; no end filed (in the latest file)",
           row={"key": "companies/4", "status": "Registered", "registered_on": "2001-05-01", "in_latest": True})
PERSON = it("companies:companies/1/director/a", "directors", title="Jane Mary DOE", statement="Jane Mary DOE: DIRECTOR of ACME TRADING LIMITED",
            dates="from 3 March 2011; no end filed (in the latest file)",
            row={"entity_key": "companies/1", "role_type": "DIRECTOR", "appointed_on": "2011-03-03", "in_latest": True})
ON_GAMMA = it("companies:companies/3/director/a", "directors", title="Jane Mary DOE", statement="Jane Mary DOE: DIRECTOR of GAMMA BUILD LIMITED",
              dates="from 1 May 2015; no end filed (in the latest file)", row={"entity_key": "companies/3", "role_type": "DIRECTOR", "in_latest": True})
LIQ = it("gazette:gazette/2020-al1/company/1", "gazette_liquidations", title="ACME TRADING LIMITED", dates="appointed 13 July 2020",
         row={"register_key": "companies/1", "appointed_on": "2020-07-13", "published_on": "2020-07-15"}, via=ACME["ref"])
RECEIVER = it("gazette:gazette/2023-ar1/company/1", "gazette_company_notices", title="GAMMA BUILD LIMITED · receivership", dates="appointed 23 July 2023",
              row={"kind": "receivership", "action": "appointment", "register_key": "companies/3", "event_on": "2023-07-23"}, via=GAMMA["ref"])
DOCA = it("gazette:gazette/2024-ot5/company/1", "gazette_company_notices", title="DELTA LIMITED · deed of company arrangement",
          dates="published 2 February 2024", row={"kind": "deed of company arrangement", "action": "deed executed", "register_key": "companies/4"},
          via=GOING["ref"])
REMOVAL = it("gazette:gazette/2019-ds1/company/9", "gazette_company_notices", title="DELTA LIMITED · removal",
             dates="objections by 17 April 2019", row={"kind": "removal", "action": "intention to remove", "statute": "Companies Act 1993 s 318(1)(b)",
                                                       "register_key": "companies/4", "event_on": "2019-04-17"}, via=GOING["ref"])
RECTIFY = it("gazette:gazette/2025-ot9/company/2", "gazette_company_notices", title="DELTA LIMITED · rectification", dates="published 1 May 2025",
             row={"kind": "rectification", "action": "intention to rectify the register", "register_key": "companies/4", "people_named": "J M DOE"},
             via=GOING["ref"])
AMALG = it("gazette:gazette/2022-ot3/company/1", "gazette_company_notices", title="DELTA LIMITED · amalgamation", dates="published 9 June 2022",
           row={"kind": "amalgamation", "action": "amalgamation proposal", "role": "amalgamating company", "register_key": "companies/4"},
           via=GOING["ref"])
PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", title="Jane Mary Doe · prohibition",
            dates="from 22 September 2022; to 22 September 2027", row={"ends_on": "2027-09-22"})
LIQUIDATOR = it("gazette:gazette/2021-al9/liquidator/1", "gazette_liquidators", title="Jane Mary DOE · Liquidator", dates="published 3 March 2021",
                row={"role": "Liquidator", "published_on": "2021-03-03"})
CO_A = it("companies:companies/1/director/z", "directors", grade="near", title="John SMITH", via=ACME["ref"], entity_title="ACME TRADING LIMITED",
          reason=THROUGH, row={"entity_key": "companies/1", "in_latest": True})
CO_G = dict(CO_A, ref="companies:companies/3/director/z", via=GAMMA["ref"], entity_title="GAMMA BUILD LIMITED", row={"entity_key": "companies/3"})
CO_HOLDER = it("companies:companies/3/shareholder/h", "shareholders", grade="near", title="DOE HOLDINGS LIMITED", via=GAMMA["ref"], reason=THROUGH,
               dates="undated", row={"entity_key": "companies/3", "shareholder_type": "company", "in_latest": True})
NOMINEE = it("companies:companies/1/shareholder/n", "shareholders", title="ACME NOMINEES LIMITED", via=ACME["ref"], dates="undated",
             row={"entity_key": "companies/1", "shareholder_type": "person", "in_latest": True},
             flags=[{"kind": "nominee", "text": "a nominee or trustee holder", "evidence": "ACME NOMINEES LIMITED"}])
NAMESAKE = it("companies:companies/77/director/q", "directors", grade="near", title="Jane DOE")


def report(subject=PERSON, hubs=(), **sections):
    out = {"found": True, "as_of": "2026-10-21", "subject": subject, "members": [], "flags": [], "hubs": list(hubs),
           "group": {"built": True, "size": 1, "contested": False, "omitted": 0},
           "walk": {"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0}, "sections": []}
    for name in ORDER:
        items = sections.get(name.replace("-", "_"), [])
        out["sections"].append({"name": name, "heading": name, "items": items, "omitted": 0, "blank": None if items else "none found"})
    return out


def person():
    """A person on two failed companies with a co-director on both and a company co-holder; one more company with a deed of company
    arrangement, a removal, a rectification and an amalgamation; a near prohibition-free record."""
    return report(officers=[ON_GAMMA], web=[ACME, CO_A, GAMMA, CO_G, CO_HOLDER, GOING],
                  gazette=[LIQ, RECEIVER, DOCA, REMOVAL, RECTIFY, AMALG])


def company(**sections):
    return report(subject=dict(ACME, via=None), **sections)


def short(r):
    r["walk"]["entities_not_expanded"] = 3
    return r


def nearly(*xs):
    return [dict(x, grade="near", reason="reached through a near link: the two rows share a first and last name") for x in xs]


def flags_of(mod, r):
    return [fn(r) for fn in mod.RULES]


# ── the properties, each a list of what broke (empty when they hold) ────────

def properties(mod) -> list:
    """What a conflicts clerk relies on, checked on fixtures; the mutant check
    runs it on each broken copy of the rules and needs it to say something.
    First with the past roles not held (as published today), then held."""
    bad = []
    mod.HISTORY = False
    for name in HISTORY_CHECKS:
        for r in (report(web=[GOING]), report()):
            if rule(name, mod)(r)["status"] == "clear":
                bad.append(f"past roles not held: {name} cleared a person whose past companies it cannot see")
    mod.HISTORY = True
    rl = lambda n: rule(n, mod)   # noqa: E731
    starts = {"person": person(), "company": company(officers=[dict(PERSON, via=ACME["ref"])], gazette=[LIQ]),
              "other": report(subject=it("party_returns:x/A/1", "party_return_donors", title="ACME TRADING LTD · $5,000")),
              "empty": report()}
    for start, r in starts.items():
        for f in flags_of(mod, r):
            if CAUSE.search(f["text"]):
                bad.append(f"{start}: {f['rule']} says a word of cause or ownership: {f['text'][:120]}")
            if NO_CONFLICT.search(f["text"]):
                bad.append(f"{start}: {f['rule']} says there is no conflict: {f['text'][:120]}")
        if rl("client_overlap")(r)["status"] != "blocked":
            bad.append(f"{start}: client-overlap did not block: the firm's list is not an input, so no overlap is ever cleared")
    for name in PEOPLE_CHECKS:
        if rl(name)(starts["company"])["status"] == "clear":
            bad.append(f"company start: {name} cleared the people it never followed")
        if rl(name)(starts["other"])["status"] == "clear":
            bad.append(f"filed-row start: {name} cleared what it never walked")
    near_only = report(web=nearly(ACME, GAMMA), gazette=nearly(LIQ, RECEIVER))
    for name in ("insolvency_notices", "repeat_insolvency", "company_status"):
        f = rl(name)(near_only)
        if f["status"] == "fired" and f["severity"] == "red":
            bad.append(f"near only: {name} is red on a namesake's companies")
        if f["status"] == "clear":
            bad.append(f"near only: {name} cleared what a namesake's companies show")
    if rl("insolvency_notices")(report(web=[GOING], gazette=[REMOVAL, RECTIFY, AMALG]))["status"] == "fired":
        bad.append("a removal, rectification or amalgamation fired insolvency-notices: none is an insolvency")
    if rl("insolvency_notices")(report(web=[GOING], gazette=[DOCA]))["status"] != "fired":
        bad.append("a deed of company arrangement did not fire insolvency-notices")
    if rl("register_events")(report(web=[GOING], gazette=[AMALG]))["status"] == "fired":
        bad.append("an amalgamation was counted as a register event: it is its own flag")
    if rl("amalgamation")(report(web=[GOING], gazette=[AMALG]))["status"] != "fired":
        bad.append("an amalgamation proposal on the person's company did not fire amalgamation")
    for name in ("insolvency_notices", "repeat_insolvency", "register_events", "amalgamation", "shared_boards", "conflict_web"):
        if rl(name)(short(report(web=[GOING])))["status"] == "clear":
            bad.append(f"short walk: {name} cleared companies it never read")
    if rl("prohibition")(report(gazette=[dict(PROHIB, suppressed=True)]))["status"] == "fired":
        bad.append("a revoked prohibition was counted")
    hidden = [dict(CO_A, suppressed=True), dict(CO_G, suppressed=True)]
    if rl("shared_boards")(report(web=[ACME, GAMMA] + hidden))["status"] == "fired":
        bad.append("a suppressed name was counted on two boards, so shown")
    if rl("shared_boards")(report(web=[ACME, CO_A]))["status"] == "fired":
        bad.append("shared-boards fired on a name seen on one company")
    if rl("repeat_insolvency")(person())["status"] != "fired":
        bad.append("repeat-insolvency did not fire on two failed companies")
    f = rl("holders_of_record")(company(officers=[NOMINEE]))
    if f["status"] != "fired" or "holder of record" not in f["text"]:
        bad.append("a nominee holder was not shown as a holder of record")
    return bad


def test_the_properties_hold_on_the_rules_as_written(held):
    assert properties(R) == []


#: (what the mutant breaks, the text replaced, its replacement): each must be unique in rules.py and caught by properties()
MUTANTS = (
    ("a namesake's notices are red", 'return flag("insolvency-notices", V, "fired", "amber",', 'return flag("insolvency-notices", V, "fired", "red",'),
    ("a removal counts as insolvency", '"notice to creditors", "deed of company arrangement")\n',
     '"notice to creditors", "deed of company arrangement", "removal")\n'),
    ("a deed of company arrangement is not insolvency", '"notice to creditors", "deed of company arrangement")\n', '"notice to creditors")\n'),
    ("a short walk is never short", 'return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))', "return False"),
    ("a prohibition clears from a company", '    if _company_start(report):\n        return flag("prohibition"', '    if False:\n        return flag("prohibition"'),
    ("a revoked prohibition is counted", 'live = [it for it in items(report, ("gazette_prohibitions",)) if not it.get("suppressed")]',
     'live = list(items(report, ("gazette_prohibitions",)))'),
    ("a flag joins two facts", '"; each is a set of rows that share a name, near, never confirmed one person"', '"; each linked to the person"'),
    ("one shared company is a shared board", "if len(cos) >= 2)", "if len(cos) >= 1)"),
    ("a clear is given though past roles are not held", "    if HISTORY:\n        return flag(rule, V, \"clear\"",
     "    if True:\n        return flag(rule, V, \"clear\""),
    ("the client list is taken as checked", 'return flag("client-overlap", V, "blocked", "red",\n                f"the firm',
     'return flag("client-overlap", V, "clear", "red", sources_held=("pub.links",), text=\n                f"no conflict: the firm'),
    ("an amalgamation is a register event", "    return it[\"view\"] == \"gazette_company_notices\" and not _insolvency(it) and not _amalgamation(it)",
     "    return it[\"view\"] == \"gazette_company_notices\" and not _insolvency(it)"),
    ("a suppressed name is counted on the boards", 'beside = [it for it in section(report, "web")["items"] if it["view"] != "companies" and not it.get("suppressed")]',
     'beside = [it for it in section(report, "web")["items"] if it["view"] != "companies"]'),
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
        f = rule(name)(report(web=[GOING]))
        assert f["status"] == "blocked" and "current roles only" in f["text"], (name, f)
    assert rule("insolvency_notices")(person())["status"] == "fired", "what is seen still fires"
    assert rule("conflict_web")(report())["status"] == "blocked", "no company row is not a clear while past roles are not held"
    p = rule("past_roles")(report(subject=dict(PERSON, row=dict(PERSON["row"], in_latest=False))))
    assert p["status"] == "blocked" and "1 of the rows listed left the file" in p["text"]


def test_every_rule_runs_from_each_start_once_and_carries_no_common_rules_name():
    society = it("societies:societies/9", "societies", title="A CLUB INCORPORATED")
    for r in (report(), person(), company(), company(officers=[dict(PERSON, via=ACME["ref"])], gazette=[LIQ]), report(subject=society)):
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


def test_the_client_overlap_is_always_blocked_and_counts_the_names_to_compare():
    f = rule("client_overlap")(person())
    assert f["status"] == "blocked" and f["severity"] == "red" and "none is ruled out" in f["text"]
    # the party, two companies' worth of web: ACME, GAMMA, DELTA, two co-directors and a company holder, and the party's own role
    assert "compare the 8 name(s) listed" in f["text"] and "client and matter list" in f["sources_not_held"][0]
    hidden = report(web=[ACME, dict(CO_A, suppressed=True)])
    assert "compare the 2 name(s)" in rule("client_overlap")(hidden)["text"], "a suppressed name is never counted"


def test_the_conflict_web_dates_each_company_and_counts_the_undated(held):
    f = rule("conflict_web")(person())
    assert f["status"] == "fired" and f["severity"] == "info" and f["scope"] == "officer-group"
    assert "3 company(ies) (3 confirmed, 0 through a near link)" in f["text"] and "3 other director(s) and holder(s)" in f["text"]
    assert "1 undated, marked so" in f["text"] and "from 3 March 2011" in f["text"]
    assert set(f["citations"]) == {ACME["ref"], GAMMA["ref"], GOING["ref"], CO_A["ref"], CO_G["ref"], CO_HOLDER["ref"]}
    assert rule("conflict_web")(company())["status"] == "blocked" and "start a report from each person" in rule("conflict_web")(company())["text"]
    assert rule("conflict_web")(report())["status"] == "clear"


def test_insolvency_notices_on_the_company_and_on_the_persons_companies(held):
    f = rule("insolvency_notices")(person())
    assert f["status"] == "fired" and f["severity"] == "red" and set(f["citations"]) == {LIQ["ref"], RECEIVER["ref"], DOCA["ref"]}
    assert "appointed 13 July 2020" in f["text"] and "from 1 May 2015" in f["text"]
    on_co = rule("insolvency_notices")(company(gazette=[LIQ]))
    assert on_co["status"] == "fired" and on_co["scope"] == "entity" and "1 liquidation" in on_co["text"]
    assert rule("insolvency_notices")(company(gazette=[]))["status"] == "clear"
    assert rule("insolvency_notices")(short(report(web=[GOING])))["status"] == "blocked"


def test_amalgamation_and_register_events_are_apart_and_neither_is_insolvency(held):
    a = rule("amalgamation")(person())
    assert a["status"] == "fired" and "amalgamating company" in a["text"] and "not reached" in a["text"] and a["citations"] == (AMALG["ref"],)
    on_co = rule("amalgamation")(report(subject=dict(GOING, via=None), gazette=[AMALG]))
    assert on_co["status"] == "fired" and on_co["severity"] == "amber" and on_co["scope"] == "entity"
    e = rule("register_events")(person())
    assert e["status"] == "fired" and set(e["citations"]) == {REMOVAL["ref"], RECTIFY["ref"]}
    assert "1 removal" in e["text"] and "1 the Registrar's rectification" in e["text"]
    restored = dict(REMOVAL, ref="gazette:gazette/2021-ds2/company/9", row=dict(REMOVAL["row"], action="restoration"))
    assert "1 restoration" in rule("register_events")(report(web=[GOING], gazette=[restored]))["text"]
    assert "J M DOE" not in e["text"], "a person a rectification names is never printed by a flag"


def test_a_prohibition_confirmed_is_red_near_amber_revoked_never_counted():
    f = rule("prohibition")(report(gazette=[PROHIB]))
    assert f["status"] == "fired" and f["severity"] == "red" and "in force on 2026-10-21" in f["text"]
    assert rule("prohibition")(report(gazette=nearly(PROHIB)))["severity"] == "amber"
    assert rule("prohibition")(report(gazette=[dict(PROHIB, suppressed=True)]))["status"] == "clear"
    r = report()
    r["walk"]["links_omitted"] = 4
    assert rule("prohibition")(r)["status"] == "blocked"


def test_a_practitioners_own_appointments_are_named_and_blocked_from_a_company():
    f = rule("practitioner_roles")(report(gazette=[LIQUIDATOR]))
    assert f["status"] == "fired" and f["citations"] == (LIQUIDATOR["ref"],) and "liquidator in 1" in f["text"]
    assert rule("practitioner_roles")(report(gazette=nearly(LIQUIDATOR)))["scope"] == "near"
    assert rule("practitioner_roles")(report())["status"] == "clear"
    assert rule("practitioner_roles")(company())["status"] == "blocked"


def test_shared_boards_counts_names_never_people():
    f = rule("shared_boards")(person())
    assert f["status"] == "fired" and f["scope"] == "near" and "John SMITH on 2 of the companies reached, 2 of them the person's confirmed" in f["text"]
    assert "never confirmed one person" in f["text"] and set(f["citations"]) == {CO_A["ref"], CO_G["ref"]}


def test_holders_of_record_show_a_company_or_nominee_holder_as_a_holder_of_record():
    f = rule("holders_of_record")(person())
    assert f["status"] == "fired" and f["citations"] == (CO_HOLDER["ref"],) and "start a report from it" in f["text"]
    n = rule("holders_of_record")(company(officers=[NOMINEE]))
    assert n["status"] == "fired" and n["severity"] == "amber" and "nominee or trustee" in n["text"] and not CAUSE.search(n["text"])
    plain = dict(NOMINEE, title="Jane DOE", flags=[])
    assert rule("holders_of_record")(company(officers=[plain]))["status"] == "clear"
    assert rule("holders_of_record")(company())["status"] == "blocked", "no holder listed on a company is not a clear"


def test_a_busy_registered_office_is_a_hub_counted_once_per_company():
    hubs = [{"ref": ACME["ref"], "title": ACME["title"], "kind": "busy-address", "text": "a busy address: 392 companies", "evidence": {"companies": 392}},
            {"ref": ACME["ref"] + "/registered_office/1", "title": "Level 1", "kind": "busy-address", "text": "a busy address: 392 companies",
             "evidence": {"companies": 392}}]
    f = rule("shared_office")(company(hubs=hubs))
    assert f["status"] == "fired" and "1 company(ies)" in f["text"] and "392 companies at it" in f["text"] and "no connection" in f["text"]
    office = it("companies:companies/1/registered_office/1", "company_addresses", title="Level 1", via=ACME["ref"])
    assert rule("shared_office")(company(officers=[office]))["status"] == "clear"
    assert rule("shared_office")(company())["status"] == "blocked"


def test_company_status_reads_the_companys_own_status():
    own = rule("company_status")(company())
    assert own["status"] == "fired" and own["severity"] == "red" and own["scope"] == "entity" and own["citations"] == (ACME["ref"],)
    assert rule("company_status")(report(subject=dict(GOING, via=None)))["status"] == "clear"
    lp = dict(GOING, row=dict(GOING["row"], entity_type="NZ Limited Partnership"))
    assert "limited partners" in rule("company_status")(report(subject=dict(lp, via=None)))["sources_not_held"][0]
    assert rule("officers_of_record")(report(subject=dict(lp, via=None)))["status"] == "blocked"


def test_a_filed_row_that_takes_a_persons_group_is_read_as_that_person():
    don = it("party_returns:x/A/1", "party_return_donors", title="Jane DOE · $5,000")
    adopted = report(subject=don, web=[ACME, CO_A], gazette=[LIQ])
    adopted["group"] = {"built": True, "size": 3, "contested": False, "omitted": 0, "via": PERSON["ref"]}
    assert rule("insolvency_notices")(adopted)["status"] == "fired" and rule("conflict_web")(adopted)["status"] == "fired"
    assert "compare the 3 name(s)" in rule("client_overlap")(adopted)["text"]
    alone = report(subject=don, web=[ACME, CO_A], gazette=[LIQ])
    assert rule("conflict_web")(alone)["status"] == "blocked" and "figure row" in rule("conflict_web")(alone)["text"]


def test_the_registers_not_held_block_and_never_clear():
    for name in ALWAYS_BLOCKED:
        for r in (person(), company(), report()):
            assert rule(name)(r)["status"] == "blocked", name
    assert "step 5.4" in rule("court_judgments")(person())["text"]
    assert "Disciplinary Tribunal" in rule("disciplinary_findings")(person())["sources_not_held"][0]
    assert "pub.gazette_possessions" in rule("mortgagee_possession")(person())["text"]


def test_namesake_exposure_declares_the_report_partial_past_fifty():
    r = report(identity=[dict(NAMESAKE, ref=f"companies:companies/{i}/director/q") for i in range(55)])
    f = rule("namesake_exposure")(r)
    assert f["status"] == "fired" and f["severity"] == "amber" and "partial" in f["text"] and "conflict search" in f["text"]
    assert rule("namesake_exposure")(report())["status"] == "clear"


def test_money_reads_only_confirmed_rows():
    don = it("party_returns:x/A/1", "party_return_donors", grade="near", title="ACME TRADING LTD · $5,000")
    f = rule("political_money")(report(identity=[don]))
    assert f["status"] == "clear" and "namesakes" in f["text"]
    assert rule("political_money")(report(money=[dict(don, grade="confirmed")]))["status"] == "fired"


def test_the_presentation_rules_hold_on_every_flag_from_every_start(held):
    """The shape's own check (rule 9 and rule 3 on fired flags), run on the
    flags each start produces, as the builder runs it on a finished report."""
    for r in (person(), company(gazette=[LIQ]), report(), report(subject=it("societies:societies/9", "societies", title="A CLUB"))):
        r["flags"] = flags_of(R, r)
        for s in r["sections"]:
            for x in s["items"]:
                x.setdefault("cite", 1)
        problems = [p for p in CONTRACT.presentation_problems(r) if p.startswith("flag ")]
        assert problems == [], problems


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
