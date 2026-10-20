"""The banking director history template on fixtures: it loads on the shape,
names only published views with their licences, runs its sections in the
credit analyst's order, and its rules keep the flag contract: the person's
confirmed companies' endings and notices are red or amber, a namesake's
amber at most, a check the walk could not have seen blocked (from a company
its officers are not followed; a short walk; a role that left the file with
no end), a removal is not insolvency, dates side by side and no word of cause
or of ownership. A mutant check breaks the rules file on purpose, nine ways,
and requires these properties to catch every break.

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
ORDER = ["identity", "roles", "endings", "person-notices", "beside", "money", "not-held"]
COMMON = ("group-standing", "hubs-met", "replaced-return")
#: words that would join two facts as cause or call a holder an owner (the shape's rules 3 and 4 hold the full list on every report)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|behind|owners?|owns|owned|"
                   r"beneficial)\b", re.I)
GAZETTE_CO = {"gazette_liquidations", "gazette_company_notices"}
GAZETTE_PERSON = {"gazette_prohibitions", "gazette_bankruptcies"}
HISTORY_CHECKS = ("company_endings", "insolvency_notices", "repeat_insolvency", "left_before_notice", "register_removals")
PEOPLE_CHECKS = ("repeat_insolvency", "left_before_notice", "prohibition", "shared_boards", "charity_officer_roles", "bankruptcy")


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


CONTRACT = by_path("qv4_test_report_contract", os.path.join(REPO, "products", "report", "contract.py"))


def rules_module(source: str = None):
    """As the shape's loader does: `contract` bound, then the file run; a
    mutant's source is run the same way."""
    if source is None:
        return by_path("qv4_test_banking_rules", os.path.join(HERE, "rules.py"), contract=CONTRACT)
    mod = type(sys)("qv4_test_banking_mutant")
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
    line = [x for x in out.stdout.splitlines() if x.startswith("banking ")]
    assert line and HERE in line[0], out.stdout
    t = toml()
    assert f"{len(t['reads'])} views, {len(t['sections'])} sections, {len(R.RULES)} rules" in line[0]


def test_it_names_each_view_once_with_its_licence_and_fewer_than_the_shape():
    t = toml()
    views = [r["view"] for r in t["reads"]]
    assert len(views) == len(set(views)) and t["depth"] == 2, "depth 2: the people beside are the walk's second step"
    assert all(r.get("licence") and r.get("attribution") and r.get("refresh") for r in t["reads"])
    with open(os.path.join(REPO, "products", "report", "templates", "subject", "template.toml"), "rb") as f:
        shape = {r["view"] for r in tomllib.load(f)["reads"]}
    assert set(views) < shape, "a use-case template names fewer views than the shape's"
    for unreached in ("gazette_appointments", "gazette_liquidators", "gazette_practitioners"):
        assert unreached not in views, "no link reaches it: reading it would print a blank that is not a clear"


def test_its_sections_run_in_the_credit_analysts_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"], "the first section holds the namesakes and nothing confirmed"
    assert not set(s["identity"]["views"]) & (GAZETTE_CO | GAZETTE_PERSON), "a near Gazette notice stays in its own section"
    assert "roles" in s["roles"]["sources"] and "companies" not in s["roles"]["views"], \
        "a company heads the endings section, its notices beneath it"
    assert s["endings"]["views"][0] == "companies" and set(s["endings"]["views"][1:]) == GAZETTE_CO and "pointing" in s["endings"]["sources"]
    assert set(s["person-notices"]["views"]) == GAZETTE_PERSON
    assert s["beside"]["sources"] == ["second"], "the people beside are the walk's second step and nothing else"
    assert "second" not in {x for sec in t["sections"] if sec["name"] != "beside" for x in sec.get("sources", [])}
    assert "charities" in s["money"]["not_held"]
    assert {"securities", "insolvency", "courts"} <= set(s["not-held"]["not_held"]) and s["not-held"]["views"] == []
    assert "securities" in s["not-held"]["not_held"] and "Personal Property Securities Register" in s["not-held"]["text"]
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views
        assert not CAUSE.search(x["text"]) and not CAUSE.search(x["heading"]), x["name"]


def test_the_known_limits_page_and_the_checkpoint_list_exist():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    assert "namesake" in page and "not a clear" in page and "checkpoint" in page.lower()
    lim = toml()["limits"]
    assert any("namesake" in x for x in lim) and any("not a clear" in x for x in lim) and any("does not yet follow" in x for x in lim)
    with open(os.path.join(HERE, "checkpoint.list"), encoding="utf-8") as f:
        keys = [x.strip() for x in f if x.strip() and not x.startswith("#")]
    assert len(keys) == 12 and all(re.match(r"^[a-z_]+:\S+$", k) for k in keys), "twelve register keys, one a line, nothing else"


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "society_officers": "person", "gazette_prohibitions": "person",
        "gazette_bankruptcies": "person", "companies": "organisation", "societies": "organisation", "company_addresses": "place",
        "gazette_company_notices": "organisation", "gazette_liquidations": "organisation", "party_return_donors": "figure"}


def it(ref, view, grade="confirmed", title="X", statement=None, dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False,
       kind=None, entity_title=None):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": kind or KIND[view], "title": title,
            "statement": statement or f"{title}: a row", "dates": {"undated": dates == "undated", "text": dates},
            "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1, "grade": grade,
            "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": [], "replaced_by": None, "entity_title": entity_title}


ACME = it("companies:companies/1", "companies", title="ACME TRADING LIMITED", statement="ACME TRADING LIMITED: In Liquidation LTD, NZBN 1",
          dates="from 3 March 2011; no end filed (in the latest file)",
          row={"key": "companies/1", "nzbn": "1", "status": "In Liquidation", "entity_type": "LTD", "registered_on": "2011-03-03", "in_latest": True})
BETA = it("companies:companies/2", "companies", title="BETA HOLDINGS LIMITED", dates="from 1 May 2005; to 2 June 2019",
          row={"key": "companies/2", "status": "Removed", "registered_on": "2005-05-01", "removed_on": "2019-06-02", "in_latest": True})
GAMMA = it("companies:companies/3", "companies", title="GAMMA BUILD LIMITED", dates="from 1 May 2015; no end filed (in the latest file)",
           row={"key": "companies/3", "status": "In Receivership", "registered_on": "2015-05-01", "in_latest": True})
GOING = it("companies:companies/4", "companies", title="DELTA LIMITED", dates="from 1 May 2001; no end filed (in the latest file)",
           row={"key": "companies/4", "status": "Registered", "registered_on": "2001-05-01", "in_latest": True})
PERSON = it("companies:companies/1/director/a", "directors", title="Jane Mary DOE", statement="Jane Mary DOE: DIRECTOR of ACME TRADING LIMITED",
            dates="from 3 March 2011; to 1 March 2020",
            row={"entity_key": "companies/1", "role_type": "DIRECTOR", "appointed_on": "2011-03-03", "ended_on": "2020-03-01", "in_latest": True})
ON_GAMMA = it("companies:companies/3/director/a", "directors", title="Jane Mary DOE", statement="Jane Mary DOE: DIRECTOR of GAMMA BUILD LIMITED",
              dates="from 1 May 2015; no end filed (in the latest file)", row={"entity_key": "companies/3", "role_type": "DIRECTOR", "in_latest": True})
LIQ = it("gazette:gazette/2020-al1/company/1", "gazette_liquidations", title="ACME TRADING LIMITED", dates="appointed 13 July 2020",
         row={"register_key": "companies/1", "appointed_on": "2020-07-13", "published_on": "2020-07-15"}, via=ACME["ref"])
RECEIVER = it("gazette:gazette/2023-ar1/company/1", "gazette_company_notices", title="GAMMA BUILD LIMITED · receivership", dates="appointed 23 July 2023",
              row={"kind": "receivership", "action": "appointment", "register_key": "companies/3", "event_on": "2023-07-23"}, via=GAMMA["ref"])
REMOVAL = it("gazette:gazette/2019-ds1/company/9", "gazette_company_notices", title="BETA HOLDINGS LIMITED · removal",
             dates="objections by 17 April 2019", row={"kind": "removal", "action": "intention to remove", "statute": "Companies Act 1993 s 318(1)(b)",
                                                       "register_key": "companies/2", "event_on": "2019-04-17"}, via=BETA["ref"])
RESTORED = it("gazette:gazette/2021-ds2/company/9", "gazette_company_notices", title="BETA HOLDINGS LIMITED · removal", dates="published 1 May 2021",
              row={"kind": "removal", "action": "restoration", "statute": "Companies Act 1993 s 328", "register_key": "companies/2"}, via=BETA["ref"])
OVERSEAS = it("gazette:gazette/2022-ds3/company/1", "gazette_company_notices", title="OVERSEAS CO PTY · removal", dates="published 1 May 2022",
              row={"kind": "removal", "action": "intention to remove", "statute": "Companies Act 1993 s 341(3)", "register_key": "companies/2"}, via=BETA["ref"])
PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", title="Jane Mary Doe · prohibition",
            dates="from 22 September 2022; to 22 September 2027", row={"ends_on": "2027-09-22"})
CO_A = it("companies:companies/1/director/z", "directors", grade="near", title="John SMITH", via=ACME["ref"], entity_title="ACME TRADING LIMITED",
          reason="a connection that passes through more than one person is listed as near, never confirmed (the design's default)",
          row={"entity_key": "companies/1", "in_latest": True})
CO_G = dict(CO_A, ref="companies:companies/3/director/z", via=GAMMA["ref"], entity_title="GAMMA BUILD LIMITED", row={"entity_key": "companies/3"})
CO_HOLDER = it("companies:companies/3/shareholder/h", "shareholders", grade="near", title="DOE NOMINEES LIMITED", via=GAMMA["ref"],
               reason="a connection that passes through more than one person is listed as near, never confirmed (the design's default)",
               row={"entity_key": "companies/3", "shareholder_type": "company", "in_latest": True})
NAMESAKE = it("companies:companies/77/director/q", "directors", grade="near", title="Jane DOE")


def report(subject=PERSON, **sections):
    out = {"found": True, "as_of": "2026-10-20", "subject": subject, "members": [], "flags": [], "hubs": [],
           "group": {"built": True, "size": 1, "contested": False, "omitted": 0},
           "walk": {"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0}, "sections": []}
    for name in ORDER:
        items = sections.get(name.replace("-", "_"), [])
        out["sections"].append({"name": name, "heading": name, "items": items, "omitted": 0, "blank": None if items else "none found"})
    return out


def history():
    """A person with three companies: one liquidated (notice four months after the role's filed end), one in receivership, one removed
    and restored; a co-director on two of them; a company co-holder."""
    return report(roles=[ON_GAMMA], endings=[ACME, LIQ, GAMMA, RECEIVER, BETA, REMOVAL, RESTORED], beside=[CO_A, CO_G, CO_HOLDER])


def company(**sections):
    return report(subject=dict(ACME, via=None), **sections)


def short(r):
    r["walk"]["entities_not_expanded"] = 3
    return r


def nearly(*xs):
    return [dict(x, grade="near", reason="reached through a near link: the two rows share a first and last name") for x in xs]


# ── the properties, each a list of what broke (empty when they hold) ────────

def properties(mod) -> list:
    """What a credit analyst relies on, checked on fixtures; the mutant check
    runs it on each broken copy of the rules and needs it to say something.
    First with the past roles not held (as published today), then with them
    held, the setting under which every other clear is possible."""
    bad = []
    mod.HISTORY = False
    for name in HISTORY_CHECKS:
        for r in (report(endings=[GOING]), report()):
            if rule(name, mod)(r)["status"] == "clear":
                bad.append(f"past roles not held: {name} cleared a person whose past companies it cannot see")
    if rule("past_roles", mod)(history())["status"] != "blocked":
        bad.append("past roles not held: past-roles did not block")
    mod.HISTORY = True
    rl = lambda n: rule(n, mod)   # noqa: E731
    starts = {"person": history(), "company": company(roles=[dict(PERSON, via=ACME["ref"])], endings=[LIQ]), "other": report(
        subject=it("party_returns:x/A/1", "party_return_donors", title="ACME TRADING LTD · $5,000"))}
    for start, r in starts.items():
        for f in (fn(r) for fn in mod.RULES):
            if CAUSE.search(f["text"]):
                bad.append(f"{start}: {f['rule']} says a word of cause or ownership: {f['text'][:120]}")
    for name in PEOPLE_CHECKS:
        if rl(name)(starts["company"])["status"] == "clear":
            bad.append(f"company start: {name} cleared the people it never followed")
        if rl(name)(starts["other"])["status"] == "clear":
            bad.append(f"filed-row start: {name} cleared what it never walked")
    near_only = report(endings=nearly(ACME, LIQ, GAMMA, RECEIVER))
    for name in ("insolvency_notices", "repeat_insolvency", "company_endings"):
        f = rl(name)(near_only)
        if f["status"] == "fired" and f["severity"] == "red":
            bad.append(f"near only: {name} is red on a namesake's companies")
        if f["status"] == "clear":
            bad.append(f"near only: {name} cleared what a namesake's companies show")
    if rl("insolvency_notices")(report(endings=[BETA, REMOVAL]))["status"] == "fired":
        bad.append("a removal notice fired insolvency-notices: a removal is not insolvency")
    for name in ("insolvency_notices", "repeat_insolvency", "left_before_notice", "register_removals", "shared_boards"):
        if rl(name)(short(report(endings=[GOING])))["status"] == "clear":
            bad.append(f"short walk: {name} cleared companies it never read")
    left_file = dict(ON_GAMMA, row=dict(ON_GAMMA["row"], in_latest=False))
    if rl("left_before_notice")(report(roles=[left_file], endings=[GAMMA, RECEIVER]))["status"] == "clear":
        bad.append("a role that left the file with no end cleared left-before-notice")
    if rl("prohibition")(report(person_notices=[dict(PROHIB, suppressed=True)]))["status"] == "fired":
        bad.append("a revoked prohibition was counted")
    one = report(endings=[ACME], beside=[CO_A])
    if rl("shared_boards")(one)["status"] == "fired":
        bad.append("shared-boards fired on a name seen on one company")
    if rl("repeat_insolvency")(history())["status"] != "fired":
        bad.append("repeat-insolvency did not fire on two failed companies")
    return bad


def test_the_properties_hold_on_the_rules_as_written(held):
    assert properties(R) == []


#: (what the mutant breaks, the text replaced, its replacement): each must be unique in rules.py and caught by properties()
MUTANTS = (
    ("a namesake's notices are red", 'return flag("insolvency-notices", V, "fired", "amber",', 'return flag("insolvency-notices", V, "fired", "red",'),
    ("a removal counts as insolvency", '"notice to creditors")\n', '"notice to creditors", "removal")\n'),
    ("a short walk is never short", 'return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))', "return False"),
    ("a prohibition clears from a company", '    if _company_start(report):\n        return flag("prohibition"', '    if False:\n        return flag("prohibition"'),
    ("a revoked prohibition is counted", 'live = [it for it in items(report, ("gazette_prohibitions",)) if not it.get("suppressed")]',
     'live = list(items(report, ("gazette_prohibitions",)))'),
    ("a role with no end filed is passed over", "    if unknown:\n", "    if False:\n"),
    ("a flag joins two facts", '"; each is a set of rows that share a name, near, never confirmed one person"', '"; each linked to the person"'),
    ("an insolvency status is not read", "    if INSOLVENT_STATUS.search(st):\n        return \"insolvent\"", "    if False:\n        return \"insolvent\""),
    ("one shared company is a shared board", "if len(cos) >= 2)", "if len(cos) >= 1)"),
    ("a clear is given though past roles are not held", "    if HISTORY:\n        return flag(rule, V, \"clear\"",
     "    if True:\n        return flag(rule, V, \"clear\""),
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
    assert R.HISTORY is False and "HISTORY = False" in open(os.path.join(HERE, "rules.py"), encoding="utf-8").read()
    for name in HISTORY_CHECKS:
        f = rule(name)(report(endings=[GOING]))
        assert f["status"] == "blocked" and "current roles only" in f["text"], (name, f)
    assert rule("insolvency_notices")(history())["status"] == "fired", "what is seen still fires"
    p = rule("past_roles")(report(subject=dict(PERSON, row=dict(PERSON["row"], in_latest=False))))
    assert p["status"] == "blocked" and p["severity"] == "red" and "1 of the rows listed left the file" in p["text"]
    assert "the company's past officers" in rule("past_roles")(company())["text"]


def test_every_rule_runs_from_each_start_once_and_carries_no_common_rules_name():
    society = it("societies:societies/9", "societies", title="A CLUB INCORPORATED")
    for r in (report(), history(), company(), company(roles=[dict(PERSON, via=ACME["ref"])], endings=[LIQ]), report(subject=society)):
        flags = [f(r) for f in R.RULES]
        assert len({f["rule"] for f in flags}) == len(flags) == len(R.RULES)
        assert not {f["rule"] for f in flags} & (set(COMMON) | {"identity"}), "the builder runs the common rules; no copy here"
    assert R.flag is CONTRACT.flag and R.items is CONTRACT.items and R.section is CONTRACT.section and R.all_items is CONTRACT.all_items
    assert "common_rules" not in toml(), "the template keeps the builder's common rules"


def test_the_flag_contract_is_the_shapes():
    with pytest.raises(ValueError, match="cite"):
        R.flag("r", "0.1", "fired", "red", "x")
    with pytest.raises(ValueError, match="sources"):
        R.flag("r", "0.1", "clear", "red", "x")


def test_company_endings_classes_each_company_and_dates_it(held):
    f = rule("company_endings")(history())
    assert f["status"] == "fired" and f["severity"] == "amber"
    assert "2 with an insolvency status" in f["text"] and "1 removed or ended" in f["text"] and "In Receivership" in f["text"]
    assert set(f["citations"]) == {ACME["ref"], GAMMA["ref"], BETA["ref"]} and "to 2 June 2019" in f["text"]
    assert rule("company_endings")(report(endings=[GOING]))["status"] == "clear"
    only_removed = rule("company_endings")(report(endings=[BETA]))
    assert only_removed["status"] == "fired" and only_removed["severity"] == "info"
    own = rule("company_endings")(company())
    assert own["status"] == "fired" and own["severity"] == "red" and own["scope"] == "entity" and own["citations"] == (ACME["ref"],)
    omitted = report(endings=[GOING])
    omitted["walk"]["entities_omitted"] = 9
    assert rule("company_endings")(omitted)["status"] == "blocked"


def test_insolvency_notices_sit_beside_the_persons_dates_and_a_removal_is_not_one(held):
    f = rule("insolvency_notices")(history())
    assert f["status"] == "fired" and f["severity"] == "red" and set(f["citations"]) == {LIQ["ref"], RECEIVER["ref"]}
    assert "appointed 13 July 2020" in f["text"] and "from 1 May 2015" in f["text"]
    assert rule("insolvency_notices")(report(endings=[BETA, REMOVAL]))["status"] == "clear"
    assert rule("insolvency_notices")(short(report(endings=[GOING])))["status"] == "blocked"
    on_co = rule("insolvency_notices")(company(endings=[LIQ]))
    assert on_co["status"] == "fired" and on_co["scope"] == "entity"


def test_repeat_insolvency_needs_two_companies_and_a_namesakes_make_it_amber(held):
    f = rule("repeat_insolvency")(history())
    assert f["status"] == "fired" and f["severity"] == "red" and "2 of the person's companies" in f["text"]
    assert "2020-07-13" in f["text"] and "2023-07-23" in f["text"]
    assert rule("repeat_insolvency")(report(endings=[ACME, LIQ]))["status"] == "clear"
    mixed = rule("repeat_insolvency")(report(endings=[ACME, LIQ] + nearly(GAMMA, RECEIVER)))
    assert mixed["status"] == "fired" and mixed["severity"] == "amber" and mixed["scope"] == "near"
    assert rule("repeat_insolvency")(company())["status"] == "blocked"


def test_left_before_notice_sets_two_dates_side_by_side(held):
    f = rule("left_before_notice")(history())
    assert f["status"] == "fired" and f["severity"] == "amber" and f["citations"] == (PERSON["ref"],)
    assert "2020-03-01" in f["text"] and "2020-07-13" in f["text"] and "134 days apart" in f["text"]
    long_gone = dict(PERSON, row=dict(PERSON["row"], ended_on="2015-01-01"))
    assert rule("left_before_notice")(report(subject=long_gone, endings=[ACME, LIQ]))["status"] == "clear"
    left_file = dict(ON_GAMMA, row=dict(ON_GAMMA["row"], in_latest=False))
    assert rule("left_before_notice")(report(roles=[left_file], endings=[GAMMA, RECEIVER]))["status"] == "blocked"


def test_register_removals_name_each_kind_and_are_not_insolvency(held):
    f = rule("register_removals")(report(endings=[BETA, REMOVAL, RESTORED, OVERSEAS]))
    assert f["status"] == "fired" and f["severity"] == "info"
    assert "1 restoration" in f["text"] and "1 an overseas company ceasing" in f["text"] and "1 removal" in f["text"]
    soc = dict(REMOVAL, ref="gazette:gazette/2024-ds9/company/1", row=dict(REMOVAL["row"], statute="Incorporated Societies Act 2022 s 175(1)(b)"))
    assert "a society dissolved or removed" in rule("register_removals")(report(endings=[soc]))["text"]
    assert rule("register_removals")(short(report()))["status"] == "blocked"


def test_a_prohibition_confirmed_is_red_near_amber_revoked_never_counted():
    f = rule("prohibition")(report(person_notices=[PROHIB]))
    assert f["status"] == "fired" and f["severity"] == "red" and "in force on 2026-10-20" in f["text"]
    assert rule("prohibition")(report(person_notices=nearly(PROHIB)))["severity"] == "amber"
    assert rule("prohibition")(report(person_notices=[dict(PROHIB, suppressed=True)]))["status"] == "clear"
    r = report()
    r["walk"]["links_omitted"] = 4
    assert rule("prohibition")(r)["status"] == "blocked"
    assert "start a report from each person" in rule("prohibition")(company())["text"]


def test_shared_boards_counts_names_never_people():
    f = rule("shared_boards")(history())
    assert f["status"] == "fired" and f["scope"] == "near" and "John SMITH on 2 of the person's companies" in f["text"]
    assert "never confirmed one person" in f["text"] and set(f["citations"]) == {CO_A["ref"], CO_G["ref"]}
    assert rule("shared_boards")(report(beside=[CO_A]))["status"] == "clear"
    hidden = [dict(CO_A, suppressed=True), dict(CO_G, suppressed=True)]
    assert rule("shared_boards")(report(beside=hidden))["status"] == "clear", "a suppressed name is never counted, so never shown"


def test_a_company_holder_beside_the_person_is_shown_as_a_holder_of_record():
    f = rule("company_holders")(history())
    assert f["status"] == "fired" and f["citations"] == (CO_HOLDER["ref"],) and not CAUSE.search(f["text"])


def test_namesake_exposure_declares_the_report_partial_past_fifty():
    r = report(identity=[dict(NAMESAKE, ref=f"companies:companies/{i}/director/q") for i in range(55)])
    f = rule("namesake_exposure")(r)
    assert f["status"] == "fired" and f["severity"] == "amber" and "partial" in f["text"]
    assert rule("namesake_exposure")(report(identity=[NAMESAKE] * 6))["severity"] == "info"
    assert rule("namesake_exposure")(report())["status"] == "clear"


def test_walk_coverage_and_young_entity():
    assert rule("walk_coverage")(short(report()))["status"] == "fired"
    assert rule("walk_coverage")(report())["status"] == "clear"
    young = dict(GOING, row=dict(GOING["row"], registered_on="2025-06-27"))
    f = rule("young_entity")(report(endings=[young]))
    assert f["status"] == "fired" and "2025-06-27" in f["text"]
    assert rule("young_entity")(company())["status"] == "clear"


def test_officers_of_record_from_a_company_start():
    going = dict(ACME, row=dict(ACME["row"], status="Registered"))
    gone = dict(PERSON, via=ACME["ref"])
    assert rule("officers_of_record")(report(subject=going, roles=[gone]))["status"] == "fired"
    assert rule("officers_of_record")(report(subject=going, roles=[dict(ON_GAMMA, via=ACME["ref"])]))["status"] == "clear"


def test_the_registers_not_held_block_and_never_clear():
    for name in ("bankruptcy", "charity_integrity_marks", "comcom_coverage", "securities_register"):
        f = rule(name)(history())
        assert f["status"] == "blocked", name
    assert "Personal Property Securities Register" in rule("securities_register")(history())["text"]


def test_money_reads_only_confirmed_rows():
    don = it("party_returns:x/A/1", "party_return_donors", grade="near", title="ACME TRADING LTD · $5,000")
    f = rule("political_money")(report(identity=[don]))
    assert f["status"] == "clear" and "namesakes" in f["text"]
    assert rule("political_money")(report(money=[dict(don, grade="confirmed")]))["status"] == "fired"


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
