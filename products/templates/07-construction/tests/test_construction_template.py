"""Subcontractor vetting and phoenix detection on fixtures: it loads on the
shape, names only published views with their licences, runs its sections in
the order a procurement lead reads them, and its rules keep the flag
contract: the phoenix flag is raised only on a shared person or a shared
registered office together with a dated failure, whatever the gap, never on a
name alone, every pair shown nearest first with its gap and counted within 90
and 365 days, a window cutting only when the reader sets one (ruling 65), never red through a hub or a removal or a near link; the office a
company takes at its liquidation (its liquidator's) is never compared; a
check the walk could not have seen is blocked (from a company its officers
are not followed; a short walk; past roles not held); a suppressed name is
never counted; dates side by side, no word of cause or ownership and no
address in a flag. A mutant check breaks the rules file on purpose, seventeen
ways, and requires these properties to catch every break.

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
ORDER = ["identity", "officers", "phoenix", "office", "people-notices", "people", "gazette", "not-held"]
COMMON = ("group-standing", "hubs-met", "replaced-return")
VIEWS = {"companies", "directors", "shareholders", "company_addresses", "gazette_liquidations", "gazette_liquidators", "gazette_company_notices",
         "gazette_appointments", "gazette_prohibitions", "gazette_bankruptcies", "societies", "society_officers"}
#: words that would join two facts as cause or call a holder an owner (the shape's rules 3 and 4 hold the full list on every report)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|behind|owners?|owns|owned|"
                   r"beneficial)\b", re.I)
HISTORY_CHECKS = ("phoenix_signature", "insolvency_notices", "repeat_failure", "register_events", "other_current_companies")
PEOPLE_CHECKS = ("phoenix_signature", "repeat_failure", "other_current_companies", "prohibition", "bankruptcy", "practitioner_roles", "society_roles")
ALWAYS_BLOCKED = ("practitioner_repeat", "change_history", "building_practitioners", "insolvency_register", "court_judgments",
                  "employment_determinations", "securities_register", "mortgagee_possession")


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


CONTRACT = by_path("qv4_test_report_contract_construction", os.path.join(REPO, "products", "report", "contract.py"))


def rules_module(source: str = None):
    """As the shape's loader does: `contract` bound, then the file run; a
    mutant's source is run the same way."""
    if source is None:
        return by_path("qv4_test_construction_rules", os.path.join(HERE, "rules.py"), contract=CONTRACT)
    mod = type(sys)("qv4_test_construction_mutant")
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
    line = [x for x in out.stdout.splitlines() if x.startswith("construction ")]
    assert line and HERE in line[0], out.stdout
    t = toml()
    assert f"{len(t['reads'])} views, {len(t['sections'])} sections, {len(R.RULES)} rules" in line[0]


def test_it_names_only_the_views_the_brief_names_each_once_with_its_licence():
    t = toml()
    views = [r["view"] for r in t["reads"]]
    assert len(views) == len(set(views)) and set(views) == VIEWS and t["depth"] == 2
    assert all(r.get("licence") and r.get("attribution") and r.get("refresh") for r in t["reads"])
    assert "registered offices only, never a residential address" in [r for r in t["reads"] if r["view"] == "company_addresses"][0]["licence"]
    for unreached in ("gazette_practitioners", "company_states", "gazette_possessions"):
        assert unreached not in views, "the catalogue does not know it, or no link reaches it: carded, named in the flags"


def test_its_sections_run_in_the_procurement_leads_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"] and "companies" not in s["identity"]["views"], \
        "an entity is filed in the first section naming its view: a confirmed company never lands with the namesakes"
    assert s["officers"]["views"] == ["directors", "shareholders"] and "roles" in s["officers"]["sources"]
    assert s["phoenix"]["views"] == ["companies"] and "pointing" not in s["phoenix"]["sources"]
    assert s["office"]["views"] == ["company_addresses"]
    assert set(s["people-notices"]["views"]) == {"gazette_prohibitions", "gazette_bankruptcies"}
    assert "second" in s["people"]["sources"] and "second" not in {x for sec in t["sections"] if sec["name"] != "people" for x in sec.get("sources", [])}
    assert "pointing" in s["gazette"]["sources"] and "pointing" not in {x for sec in t["sections"] if sec["name"] != "gazette"
                                                                       for x in sec.get("sources", [])}
    assert {"building_practitioners", "insolvency", "courts"} <= set(s["not-held"]["not_held"]) and s["not-held"]["views"] == []
    for named in ("building practitioners", "Official Assignee", "court judgments", "Employment Relations Authority", "16 August 2026"):
        assert named in s["not-held"]["text"], named
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views
        assert not CAUSE.search(x["text"]) and not CAUSE.search(x["heading"]), x["name"]


def test_the_known_limits_page_and_the_checkpoint_list_exist():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    for want in ("namesake", "not a clear", "checkpoint", "liquidator", "window", "14.2 million"):
        assert want in page, want
    lim = toml()["limits"]
    assert any("never the phoenix signature" in x for x in lim) and any("does not yet follow" in x for x in lim)
    with open(os.path.join(HERE, "checkpoint.list"), encoding="utf-8") as f:
        keys = [x.strip() for x in f if x.strip() and not x.startswith("#")]
    assert len(keys) == 12 and len(set(keys)) == 12 and all(re.match(r"^[a-z_]+:\S+$", k) for k in keys), "twelve register keys, one a line"


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "society_officers": "person", "gazette_prohibitions": "person",
        "gazette_bankruptcies": "person", "gazette_liquidators": "person", "companies": "organisation", "societies": "organisation",
        "company_addresses": "place", "gazette_company_notices": "organisation", "gazette_liquidations": "organisation",
        "party_return_donors": "figure"}
THROUGH = "a connection that passes through more than one person is listed as near, never confirmed (the design's default)"
SAME_REASON = "two companies under one name; only the official number confirms a company"


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


def office(n, line_1, postcode, started, in_latest=True, grade="confirmed", flags=()):
    return it(f"companies:companies/{n}/registered-office/{started}/x", "company_addresses", grade=grade, title=f"{line_1} · Town",
              statement=f"a company: registered office at {line_1} · Town", dates=f"from {started}", via=f"companies:companies/{n}",
              row={"entity_key": f"companies/{n}", "kind": "registered office", "line_1": line_1, "postcode": postcode, "started_on": started,
                   "in_latest": in_latest}, reason=THROUGH if grade == "near" else None, flags=flags)


FAILED = company(1, "ACME BUILD LIMITED", "In Liquidation", "2011-03-03")
NEWCO = company(2, "KEA FORMWORK LIMITED", "Registered", "2020-09-01")         # 50 days after FAILED's liquidator was appointed
GAMMA = company(3, "GAMMA CIVIL LIMITED", "In Receivership", "2015-05-01")
OLDCO = company(4, "DELTA LIMITED", "Registered", "2001-05-01")                # long before every failure
LIQ = it("gazette:gazette/2020-al1/company/1", "gazette_liquidations", title="ACME BUILD LIMITED", dates="appointed 13 July 2020",
         row={"register_key": "companies/1", "appointed_on": "2020-07-13", "published_on": "2020-07-15", "appointed_by": "court"}, via=FAILED["ref"])
RECEIVER = it("gazette:gazette/2023-ar1/company/1", "gazette_company_notices", title="GAMMA CIVIL LIMITED · receivership",
              dates="appointed 23 July 2023", via=GAMMA["ref"],
              row={"kind": "receivership", "action": "appointment", "event_basis": "appointment", "register_key": "companies/3", "event_on": "2023-07-23"})
REMOVAL = it("gazette:gazette/2020-ds1/company/9", "gazette_company_notices", title="DELTA LIMITED · removal", via=OLDCO["ref"],
             dates="objections by 17 August 2020; published 20 July 2020",
             row={"kind": "removal", "action": "intention to remove", "event_basis": "objections by", "register_key": "companies/4",
                  "event_on": "2020-08-17", "published_on": "2020-07-20"})
CEASED = it("gazette:gazette/2020-ar9/company/1", "gazette_company_notices", title="DELTA LIMITED · receivership", via=OLDCO["ref"],
            dates="ceased to act 14 July 2020", row={"kind": "receivership", "action": "ceased to act", "event_basis": "ceased to act",
                                                     "register_key": "companies/4", "event_on": "2020-07-14", "published_on": "2020-07-16"})
PERSON = it("companies:companies/1/director/a", "directors", title="Jane Mary DOE", statement="Jane Mary DOE: DIRECTOR of ACME BUILD LIMITED",
            dates="from 3 March 2011; no end filed (in the latest file)",
            row={"entity_key": "companies/1", "role_type": "DIRECTOR", "appointed_on": "2011-03-03", "in_latest": True})
ON_NEWCO = it("companies:companies/2/director/a", "directors", title="Jane Mary DOE", statement="Jane Mary DOE: DIRECTOR of KEA FORMWORK LIMITED",
              dates="from 1 September 2020; no end filed (in the latest file)",
              row={"entity_key": "companies/2", "role_type": "DIRECTOR", "appointed_on": "2020-09-01", "in_latest": True})
#: the failed company's office before its failure, the office it took at its liquidation (its liquidator's), and the going company's
FAILED_BEFORE = office(1, "1 Main Road", "1010", "2015-01-01", in_latest=False)
FAILED_LIQUIDATOR = office(1, "Level 5 Insolvency House", "1011", "2020-07-13")
NEWCO_OFFICE = office(2, "1 Main Road", "1010", "2020-09-01")
NEWCO_AT_LIQUIDATOR = office(2, "Level 5 Insolvency House", "1011", "2020-09-01")
#: from a company: a company of the same name that failed, reached by the links lane's company-name rule, near
SAME = dict(company(9, "KEA FORMWORK LIMITED", "In Liquidation", "2012-01-01", via=NEWCO["ref"], rule_="company-name@1"), grade="near",
            reason=SAME_REASON)
SAME_LIQ = dict(LIQ, ref="gazette:gazette/2020-al2/company/9", title="KEA FORMWORK LIMITED", via=SAME["ref"], grade="near",
                reason=f"reached through a near link: {SAME_REASON}", row=dict(LIQ["row"], register_key="companies/9", appointed_on="2020-06-01"))
SAME_BEFORE = office(9, "1 Main Road", "1010", "2013-01-01", in_latest=False, grade="near")
SAME_DIRECTOR = it("companies:companies/9/director/q", "directors", grade="near", title="Jane Mary DOE", via=SAME["ref"],
                   reason=f"reached through a near link: {SAME_REASON}", row={"entity_key": "companies/9", "in_latest": True})
NEWCO_DIRECTOR = dict(ON_NEWCO, via=NEWCO["ref"])
PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", title="Jane Mary Doe · prohibition",
            dates="from 22 September 2022; to 22 September 2027", row={"ends_on": "2027-09-22"})
BANKRUPT = it("gazette:gazette/2019-ba1/person/1", "gazette_bankruptcies", title="DOE · Jane Mary", dates="adjudicated 2 May 2019",
              row={"kind": "adjudication", "event_on": "2019-05-02"})
CO_A = it("companies:companies/1/director/z", "directors", grade="near", title="John SMITH", via=FAILED["ref"], entity_title="ACME BUILD LIMITED",
          reason=THROUGH, row={"entity_key": "companies/1", "in_latest": True})
PRO_HUB = {"ref": PERSON["ref"], "title": "Jane Mary DOE", "kind": "professional-director", "text": "a professional director: 80 directorships",
           "evidence": {"directorships": 80}}
OFFICE_HUB = [{"ref": NEWCO["ref"], "title": NEWCO["title"], "kind": "busy-address", "text": "a busy address: 300 companies",
               "evidence": {"companies": 300}}]


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
    """A director of a company liquidated on 13 July 2020 and of a company registered 50 days later; a third company in
    receivership in 2023; a fourth registered in 2001 with a removal notice; the first's office before its failure is the second's now."""
    parts = dict(officers=[ON_NEWCO], phoenix=[FAILED, NEWCO, GAMMA, OLDCO], office=[FAILED_BEFORE, FAILED_LIQUIDATOR, NEWCO_OFFICE],
                 people=[CO_A], gazette=[LIQ, RECEIVER, REMOVAL])
    parts.update(kw)
    return report(**parts)


def from_company(subject=NEWCO, **kw):
    """Started from the going company: its director and office; a company of the same name liquidated on 1 June 2020, whose office
    before then is the going company's office now, with a director of the same name."""
    parts = dict(officers=[NEWCO_DIRECTOR, SAME_DIRECTOR], phoenix=[SAME], office=[NEWCO_OFFICE, SAME_BEFORE], gazette=[SAME_LIQ])
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
    """What a procurement lead relies on, checked on fixtures; the mutant check
    runs it on each broken copy of the rules and needs it to say something.
    First with the past roles not held (as published today), then held."""
    bad = []
    mod.HISTORY = False
    for name in HISTORY_CHECKS:
        for r in (report(phoenix=[OLDCO]), report()):
            if rule(name, mod)(r)["status"] == "clear":
                bad.append(f"past roles not held: {name} cleared a person whose past companies it cannot see")
    mod.HISTORY = True
    rl = lambda n: rule(n, mod)   # noqa: E731
    starts = {"person": person(), "company": from_company(), "other": report(subject=it("societies:societies/9", "societies", title="A CLUB")),
              "empty": report()}
    for start, r in starts.items():
        for f in flags_of(mod, r):
            if CAUSE.search(f["text"]):
                bad.append(f"{start}: {f['rule']} says a word of cause or ownership: {f['text'][:120]}")
            if CONTRACT.address_shaped(f["text"]):
                bad.append(f"{start}: {f['rule']} prints an address: {f['text'][:120]}")
    for name in PEOPLE_CHECKS:
        for r in (from_company(phoenix=[], office=[NEWCO_OFFICE], gazette=[]), starts["other"]):
            if rl(name)(r)["status"] == "clear":
                bad.append(f"{r['subject']['view']} start: {name} cleared the people it never followed")
    # the signature: a shared person and a dated insolvency, red whatever the gap; the window is the reader's (ruling 65)
    f = rl("phoenix_signature")(person())
    if not (f["status"] == "fired" and f["severity"] == "red" and NEWCO["ref"] in f["citations"] and LIQ["ref"] in f["citations"]):
        bad.append(f"a confirmed failure 50 days before a going company's start did not raise the phoenix flag red: {f['status']} {f['severity']}")
    if "of 4 pair(s), nearest first, 1 within 90 days and 1 within 365 days" not in f["text"]:
        bad.append(f"the phoenix flag does not count its pairs within 90 and 365 days: {f['text'][-300:]}")
    late = dict(NEWCO, row=dict(NEWCO["row"], registered_on="2024-01-01"))
    g = rl("phoenix_signature")(person(phoenix=[FAILED, late]))
    if not (g["status"] == "fired" and g["severity"] == "red" and "1267 days after" in g["text"]):
        bad.append(f"a going company registered three and a half years after the failure was cut with no window set: {g['status']} {g['severity']}")
    if rl("phoenix_signature")(dict(person(phoenix=[FAILED, late]), window_days=365))["status"] == "fired":
        bad.append("the reader's window of 365 days did not cut a going company registered three and a half years after the failure")
    if rl("phoenix_signature")(dict(person(phoenix=[FAILED, late]), window_days="1500"))["status"] != "fired":
        bad.append("the reader's window of 1,500 days, passed as text, cut a pair 1,267 days apart")
    two = person(phoenix=[FAILED, dict(late, ref="companies:companies/6", row=dict(late["row"], key="companies/6")), NEWCO])
    t = rl("phoenix_signature")(two)["text"]
    if not (0 <= t.find("50 days after") < t.find("1267 days after")):
        bad.append("the phoenix flag's pairs are not ordered by their gap, nearest first")
    if rl("phoenix_signature")(person(phoenix=[FAILED, NEWCO], gazette=[], office=[]))["severity"] == "red" and \
            rl("phoenix_signature")(person(phoenix=[FAILED, NEWCO], gazette=[], office=[]))["status"] == "fired":
        bad.append("an undated failure (status only) raised the phoenix flag red: no window can be measured")
    removal_only = person(phoenix=[dict(OLDCO, ref="companies:companies/5", row=dict(OLDCO["row"], key="companies/5")), NEWCO],
                          gazette=[dict(REMOVAL, via="companies:companies/5", row=dict(REMOVAL["row"], register_key="companies/5"))])
    if rl("phoenix_signature")(removal_only)["severity"] == "red":
        bad.append("a removal from the register raised the phoenix flag red: a removal is not an insolvency")
    ceased_only = person(phoenix=[OLDCO, NEWCO], gazette=[CEASED])
    if rl("phoenix_signature")(ceased_only)["status"] == "fired":
        bad.append("a receiver's ceasing to act dated a failure: it ends a receivership and dates nothing")
    hub = person()
    hub["hubs"] = [PRO_HUB]
    if rl("phoenix_signature")(hub)["severity"] == "red":
        bad.append("the phoenix flag was red through a professional director: a hub joins many companies")
    near_only = person(phoenix=nearly(FAILED, NEWCO), gazette=nearly(LIQ))
    if rl("phoenix_signature")(near_only)["severity"] == "red":
        bad.append("the phoenix flag was red on a namesake's companies")
    # from a company: a name alone is never the signature; a shared office before the failure is, the liquidator's office never
    if rl("phoenix_signature")(from_company())["status"] != "fired":
        bad.append("from a company: a same-name company that failed and had the entity's office before its failure did not raise the flag")
    name_only = from_company(office=[NEWCO_OFFICE])
    for name in ("phoenix_signature", "same_name_failed"):
        g = rl(name)(name_only)
        if g["status"] == "fired" and g["severity"] == "red":
            bad.append(f"from a company: {name} was red on a name alone")
    if rl("phoenix_signature")(name_only)["status"] == "clear":
        bad.append("from a company: the phoenix flag cleared though the people are not followed")
    liq_office = from_company(office=[NEWCO_AT_LIQUIDATOR, dict(FAILED_LIQUIDATOR, ref="companies:companies/9/registered-office/x", via=SAME["ref"],
                                                                row=dict(FAILED_LIQUIDATOR["row"], entity_key="companies/9", started_on="2020-06-01"))])
    if rl("phoenix_signature")(liq_office)["status"] == "fired" or rl("shared_office")(liq_office)["status"] == "fired":
        bad.append("the office a company took at its liquidation (its liquidator's) was compared as a shared office")
    busy = from_company(hubs=OFFICE_HUB)
    if rl("phoenix_signature")(busy)["status"] == "fired" or rl("shared_office")(busy)["status"] == "fired":
        bad.append("an office fifty or more companies share raised the signature: a hub joins nothing")
    if rl("shared_office")(person())["status"] != "fired":
        bad.append("shared-office did not fire on a failed company's office before its failure that a going company has now")
    if rl("shared_office")(person(office=[NEWCO_OFFICE]))["status"] == "clear":
        bad.append("shared-office cleared though the companies at an office are counted, not listed")
    # a short walk; the people's notices; the notices that are not insolvency
    for name in ("phoenix_signature", "insolvency_notices", "repeat_failure", "register_events", "other_current_companies", "same_name_failed"):
        if rl(name)(short(report(phoenix=[OLDCO])))["status"] == "clear":
            bad.append(f"short walk: {name} cleared companies it never read")
    if rl("insolvency_notices")(report(phoenix=[OLDCO], gazette=[REMOVAL, CEASED]))["status"] == "fired":
        bad.append("a removal or a receiver ceasing to act fired insolvency-notices")
    if rl("repeat_failure")(person())["status"] != "fired":
        bad.append("repeat-failure did not fire on two failed companies")
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
    ("the reader's window is never applied", "out.append((f, g, days, window is None or abs(days) <= window))", "out.append((f, g, days, True))"),
    ("a window is cut when the reader sets none", '    if w is None or w == "" or isinstance(w, bool):\n        return None',
     '    if w is None or w == "" or isinstance(w, bool):\n        return 365'),
    ("the pairs are not nearest first", "    out.sort(key=lambda p: (abs(p[2]),", "    out.sort(key=lambda p: (-abs(p[2]),"),
    ("the old defaults are not counted", "OLD_WINDOWS = (90, 365)", "OLD_WINDOWS = ()"),
    ("a removal raises the flag red", "red = bool(insolvent) and not hub", "red = not hub"),
    ("a hub raises the flag red", "red = bool(insolvent) and not hub", "red = bool(insolvent)"),
    ("a name alone is the signature from a company", "by_office = _office_pairs(report, failed, [s]) if _ending(s) == \"going\" else []",
     "by_office = [p + (p[0][\"company\"], s) for p in _pairs(failed, [s])] if _ending(s) == \"going\" else []"),
    ("the liquidator's office is compared", "if st and st < fdate and not _office_hub(report, f, it)}", "if not _office_hub(report, f, it)}"),
    ("an office hub joins companies", 'if it["row"].get("in_latest", True) and not _office_hub(report, g, it)]', 'if it["row"].get("in_latest", True)]'),
    ("a namesake's pair is red", 'return flag("phoenix-signature", V, "fired", "amber",\n                    f"{len(near_pairs)}',
     'return flag("phoenix-signature", V, "fired", "red",\n                    f"{len(near_pairs)}'),
    ("a short walk is never short", 'return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))', "return False"),
    ("a person's notice clears from a company", '    if _company_start(report):\n        return flag(rule, V, "blocked", severity',
     '    if False:\n        return flag(rule, V, "blocked", severity'),
    ("a clear is given though past roles are not held", "    if HISTORY:\n        return flag(rule, V, \"clear\"",
     "    if True:\n        return flag(rule, V, \"clear\""),
    ("a removal is an insolvency", 'kind = "insolvency" if _insolvency(n) else "removal" if _removal(n) else None',
     'kind = "insolvency" if _insolvency(n) or _removal(n) else None'),
    ("a receiver ceasing dates a failure", ' and "ceas" not in (r.get("action") or "").lower()', ""),
    ("a revoked prohibition is counted", "live = [it for it in items(report, (view,)) if not it.get(\"suppressed\")]", "live = list(items(report, (view,)))"),
    ("a flag joins two facts", 'carry {what} in the Gazette, each set beside "', 'carry {what} in the Gazette, because of the person, each set beside "'),
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
        f = rule(name)(report(phoenix=[OLDCO]))
        if name == "other_current_companies":
            assert f["status"] == "fired" and f["severity"] == "info", "a listing fires on what it sees"
            f = rule(name)(report())
        assert f["status"] == "blocked" and "current roles only" in f["text"], (name, f)
    assert rule("phoenix_signature")(person())["status"] == "fired", "what is seen still fires"
    p = rule("past_roles")(report(subject=dict(PERSON, row=dict(PERSON["row"], in_latest=False))))
    assert p["status"] == "blocked" and "1 of the rows listed left the file" in p["text"]


def test_every_rule_runs_from_each_start_once_and_carries_no_common_rules_name():
    society = it("societies:societies/9", "societies", title="A CLUB INCORPORATED")
    for r in (report(), person(), from_company(), from_company(phoenix=[], office=[], gazette=[]), report(subject=society)):
        flags = flags_of(R, r)
        assert len({f["rule"] for f in flags}) == len(flags) == len(R.RULES)
        assert not {f["rule"] for f in flags} & set(COMMON), "the builder runs the common rules; no copy here"
    assert R.flag is CONTRACT.flag and R.items is CONTRACT.items and R.section is CONTRACT.section and R.all_items is CONTRACT.all_items
    assert "common_rules" not in toml(), "the template keeps the builder's common rules"


def test_the_phoenix_signature_sets_every_failure_beside_each_going_start_whatever_the_gap_nearest_first(held):
    f = rule("phoenix_signature")(person())
    assert f["status"] == "fired" and f["severity"] == "red" and f["scope"] == "officer-group"
    assert "ACME BUILD LIMITED: liquidation (liquidator appointed by the court), appointed 13 July 2020" in f["text"]
    assert "KEA FORMWORK LIMITED: registered 2020-09-01, 50 days after" in f["text"]
    assert "2 of the person's companies carry an insolvency" in f["text"] and "2 going company(ies)" in f["text"]
    # ruling 65: the window is the reader's; a company registered nineteen years before the liquidation is listed, after the nearer ones
    assert "WINDOW_DAYS" not in open(os.path.join(HERE, "rules.py"), encoding="utf-8").read()
    assert "DELTA LIMITED: registered 2001-05-01, 7013 days before" in f["text"], "a going company far from the failure is paired"
    assert f["text"].index("50 days after") < f["text"].index("1055 days before") < f["text"].index("7013 days before")
    assert "of 4 pair(s), nearest first, 1 within 90 days and 1 within 365 days; no window is set, so every gap is shown" in f["text"]
    assert "and 1 more pair(s)" in f["text"]
    assert set(f["citations"]) == {FAILED["ref"], LIQ["ref"], NEWCO["ref"], GAMMA["ref"], RECEIVER["ref"], OLDCO["ref"]}
    cut = rule("phoenix_signature")(dict(person(), window_days=365))
    assert cut["status"] == "fired" and "DELTA LIMITED" not in cut["text"] and "GAMMA" not in cut["text"]
    assert "the reader's window is 365 days either side of the failure's Gazette date, and 3 of them fall outside it and are not listed" in cut["text"]
    assert set(cut["citations"]) == {FAILED["ref"], LIQ["ref"], NEWCO["ref"]}
    nonsense = rule("phoenix_signature")(dict(person(), window_days="a year"))
    assert "is not a whole number of days, so no cut is applied" in nonsense["text"] and "DELTA LIMITED" in nonsense["text"]
    none_inside = rule("phoenix_signature")(dict(person(phoenix=[FAILED, OLDCO], gazette=[LIQ]), window_days=90))
    assert none_inside["status"] == "clear" and "no pair is listed" in none_inside["text"] and "1 of them fall outside it" in none_inside["text"]
    before = person(phoenix=[FAILED, dict(NEWCO, row=dict(NEWCO["row"], registered_on="2020-03-01"))])
    assert "134 days before" in rule("phoenix_signature")(before)["text"], "a new firm set up before the liquidation is in the window too"
    gamma_only = person(phoenix=[GAMMA, dict(NEWCO, row=dict(NEWCO["row"], registered_on="2023-10-01"))], gazette=[RECEIVER])
    g = rule("phoenix_signature")(gamma_only)
    assert g["status"] == "fired" and "receivership, appointed 23 July 2023" in g["text"]
    hub = person()
    hub["hubs"] = [PRO_HUB]
    h = rule("phoenix_signature")(hub)
    assert h["status"] == "fired" and h["severity"] == "amber" and "the person is a hub (professional-director)" in h["text"]


def test_from_a_company_the_signature_is_a_shared_office_and_a_dated_failure_never_a_name():
    f = rule("phoenix_signature")(from_company())
    assert f["status"] == "fired" and f["severity"] == "red" and f["scope"] == "office"
    assert "had, before the failure, the registered office the entity has now" in f["text"] and "start a report from each director" in f["text"]
    assert {SAME["ref"], SAME_LIQ["ref"], SAME_BEFORE["ref"], NEWCO_OFFICE["ref"]} <= set(f["citations"])
    assert "1 Main Road" not in f["text"], "the office is shown in its section, never printed by a flag"
    blocked = rule("phoenix_signature")(from_company(office=[NEWCO_OFFICE]))
    assert blocked["status"] == "blocked" and "start a report from each person listed" in blocked["text"] and "1 failed" in blocked["text"]
    s = rule("same_name_failed")(from_company(office=[NEWCO_OFFICE]))
    assert s["status"] == "fired" and s["severity"] == "amber" and s["scope"] == "near"
    assert "1 with an officer of the same name on both" in s["text"] or "1 of those with an officer of the same name on both" in s["text"]
    assert "names, never one firm or one person" in s["text"]
    no_officer = rule("same_name_failed")(from_company(officers=[NEWCO_DIRECTOR], office=[NEWCO_OFFICE]))
    assert no_officer["severity"] == "info", "a company name alone is information"


def test_the_entity_itself_failed_or_ended_is_red():
    own = rule("entity_status")(report(subject=dict(FAILED, via=None)))
    assert own["status"] == "fired" and own["severity"] == "red" and "itself a failed firm" in own["text"]
    assert rule("entity_status")(report(subject=dict(NEWCO, via=None)))["status"] == "clear"
    n = rule("insolvency_notices")(report(subject=dict(FAILED, via=None), gazette=[LIQ]))
    assert n["status"] == "fired" and n["scope"] == "entity" and "1 liquidation" in n["text"]
    assert rule("insolvency_notices")(report(subject=dict(NEWCO, via=None)))["status"] == "clear"


def test_young_entity_is_amber_on_the_entity():
    young = dict(NEWCO, row=dict(NEWCO["row"], registered_on="2025-06-01"))
    f = rule("young_entity")(report(subject=dict(young, via=None)))
    assert f["status"] == "fired" and f["severity"] == "amber" and "2025-06-01" in f["text"]
    assert rule("young_entity")(report(subject=dict(NEWCO, via=None)))["status"] == "clear"


def test_register_events_are_not_insolvency_and_a_receiver_ceasing_dates_nothing(held):
    e = rule("register_events")(person())
    assert e["status"] == "fired" and e["citations"] == (REMOVAL["ref"],) and "none is an insolvency" in e["text"]
    assert rule("insolvency_notices")(report(phoenix=[OLDCO], gazette=[CEASED]))["status"] != "fired"


def test_other_current_companies_lists_the_going_ones_newest_first(held):
    f = rule("other_current_companies")(person())
    assert f["status"] == "fired" and "2 registered" in f["text"] and f["text"].index("KEA FORMWORK") < f["text"].index("DELTA")


def test_the_registers_not_held_block_and_never_clear():
    for name in ALWAYS_BLOCKED:
        for r in (person(), from_company(), report()):
            assert rule(name)(r)["status"] == "blocked", name
    assert "16 August 2026" in rule("change_history")(person())["text"]
    assert "building practitioner" in rule("building_practitioners")(person())["sources_not_held"][0]
    assert "Employment Relations Authority" in rule("employment_determinations")(person())["text"]
    assert "pub.gazette_possessions" in rule("mortgagee_possession")(person())["text"]


def test_a_register_name_with_a_word_of_cause_is_not_quoted_in_a_flag(held):
    behind = dict(FAILED, title="BEHIND THE SCENES LIMITED")
    f = rule("phoenix_signature")(person(phoenix=[behind, NEWCO]))
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
    for r in (person(), from_company(), report(), report(subject=it("societies:societies/9", "societies", title="A CLUB"))):
        r["flags"] = flags_of(R, r)
        problems = [p for p in CONTRACT.presentation_problems(r) if p.startswith("flag ")]
        assert problems == [], problems


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
