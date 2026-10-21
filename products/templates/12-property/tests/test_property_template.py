"""Property developer due diligence on fixtures: it loads on the shape, names
only published views with their licences, runs its sections in the order a
buyer reads them, and its rules keep the flag contract: the serial pattern
sets each dated failure of a principal's companies beside the principal's
going companies with the gap in days, and is red only on a person's own
confirmed companies with two or more insolvencies, amber through a
director, a hub or a near link, info where every failure is a removal; one
failure is not a series; the window is the reader's and cuts only when
set; an insolvency notice on the entity the latest file does not show yet
is red; a young entity and a one-person vehicle fire; a failed company at
the entity's office is amber unless the office is a hub, an accountant's or
a lawyer's office being one; a mortgagee possession on the entity is red,
on a director's other company amber, a lender's info; a prohibition in
force on the person's own record is red, anything weaker amber or info; a
start that lists no director, a director past the limit and an
unpublished link set block every people check; every register not held
blocks; no check over the principals' companies is ever clear while the
file lists current roles only; dates side by side, no word of cause or
ownership, no address and no suppressed name in a flag. A mutant check
breaks the rules file on purpose and requires these properties to catch
every break.

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
ORDER = ["identity", "standing", "principals", "chain", "history", "serial", "office", "possessions", "people-notices", "gazette", "not-held"]
COMMON = ("group-standing", "hubs-met", "replaced-return")
VIEWS = {"companies", "company_states", "directors", "shareholders", "company_addresses", "gazette_liquidations", "gazette_liquidators",
         "gazette_company_notices", "gazette_possessions", "gazette_appointments", "gazette_prohibitions", "gazette_bankruptcies", "societies",
         "society_officers"}
#: words that would join two facts as cause or call a holder an owner (the shape's rules 3 and 4 hold the full list on every report)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|behind|owners?|owns|owned|"
                   r"beneficial)\b", re.I)
PRINCIPAL_CHECKS = ("serial_pattern", "earlier_failure", "possession", "insolvency_notices")
PEOPLE_CHECKS = ("prohibition", "bankruptcy")
ALWAYS_BLOCKED = ("land_titles", "overseas_investment", "building_consents", "court_judgments", "securities_register", "insolvency_register",
                  "real_estate_authority", "building_practitioners", "past_roles")


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


CONTRACT = by_path("qv4_test_report_contract_property", os.path.join(REPO, "products", "report", "contract.py"))


def rules_module(source: str = None):
    """As the shape's loader does: `contract` bound, then the file run; a mutant's source is run the same way."""
    if source is None:
        return by_path("qv4_test_property_rules", os.path.join(HERE, "rules.py"), contract=CONTRACT)
    mod = type(sys)("qv4_test_property_mutant")
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
    assert out.returncode == 0 and "Traceback" not in out.stderr, out.stderr
    line = [x for x in out.stdout.splitlines() if x.startswith("property ")]
    assert line and HERE in line[0], out.stdout
    t = toml()
    assert f"{len(t['reads'])} views, {len(t['sections'])} sections, {len(R.RULES)} rules" in line[0]


def test_the_window_is_a_parameter_the_reader_sets_and_the_rule_reads():
    """Card the-construction-and-property-templates-declare-no-window-days-parameter: `window_days` is declared (an integer, no
    default: ruling 65 makes the window the reader's), so the shape's form offers it and `--set window_days=30` is accepted; the
    value the shape puts on the report is the one the serial pattern cuts at."""
    p = [x for x in toml().get("params", []) if x["name"] == "window_days"]
    assert p and p[0]["kind"] == "integer" and "default" not in p[0] and "every gap is shown" in p[0]["means"], p
    out = subprocess.run([sys.executable, "-m", "products.report", "render", "", "--template", "property", "--html"], cwd=REPO,
                         capture_output=True, text=True, timeout=20)
    assert out.returncode == 0 and '<input name="window_days"' in out.stdout, out.stderr[-500:]
    cut = rule("serial_pattern")(dict(developer(window=30), params={"window_days": 30}))
    assert "fall outside it and are not listed" in cut["text"] and "MATAI GROVE DEVELOPMENT LIMITED: registered" not in cut["text"]


def test_it_names_only_the_views_the_brief_names_each_once_with_its_licence():
    t = toml()
    views = [r["view"] for r in t["reads"]]
    assert len(views) == len(set(views)) and set(views) == VIEWS and t["depth"] == 2 and t["chain_depth"] == 2
    assert all(r.get("licence") and r.get("attribution") and r.get("refresh") for r in t["reads"])
    assert "registered offices only, never a residential address" in [r for r in t["reads"] if r["view"] == "company_addresses"][0]["licence"]
    assert "private tables" in [r for r in t["reads"] if r["view"] == "gazette_possessions"][0]["licence"]
    for unreached in ("charities", "charity_officers"):
        assert unreached not in views, "the catalogue does not know it: carded, named in the not-held section"
    src = open(os.path.join(HERE, "template.toml"), encoding="utf-8").read()
    for card in ("the-not-held-list-has-no-key-for-the-property-registers", "the-report-carries-no-template-parameters",
                 "the-report-cannot-reach-the-charities-register"):
        assert card in src, card
    assert "ruling 65" in src and "section 2.6" in src


def test_its_sections_run_in_the_buyers_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"] and s["identity"]["own"] is False, "a namesake is never the entity's own row"
    assert s["standing"]["own"] is True and s["standing"]["views"] == ["company_states"]
    assert "companies" not in s["principals"]["views"], "a person's own companies belong in the project history"
    assert s["chain"]["sources"] == ["chain"] and s["chain"]["own"] is False
    assert "officers" in s["history"]["sources"] and "newest first" in s["history"]["heading"]
    assert s["serial"]["own"] is False and set(s["serial"]["sources"]) == {"officers", "pointing"}
    assert "office" in s["office"]["sources"] and "office" not in {b for x in t["sections"] if x["name"] != "office" for b in x.get("sources", [])}
    assert s["possessions"]["views"] == ["gazette_possessions"] and {"securities", "linz"} <= set(s["possessions"]["not_held"])
    assert "officers" in s["people-notices"]["sources"]
    assert s["not-held"]["views"] == []
    assert {"linz", "courts", "securities", "insolvency"} <= set(s["not-held"]["not_held"])
    for named in ("land titles", "LINZ", "Overseas Investment Office", "building consents", "council minutes", "court judgments",
                  "Personal Property Securities Register", "Insolvency Register", "Real Estate Authority"):
        assert named in s["not-held"]["text"], named
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views
        assert not CAUSE.search(x["text"]) and not CAUSE.search(x["heading"]), x["name"]


def test_the_known_limits_page_and_the_checkpoint_list_exist():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    for want in ("namesake", "not a clear", "checkpoint", "never clear", "LINZ", "Overseas Investment Office", "serial", "window"):
        assert want in page, want
    with open(os.path.join(HERE, "checkpoint.list"), encoding="utf-8") as f:
        keys = [x.strip() for x in f if x.strip() and not x.startswith("#")]
    assert len(keys) == 12 and len(set(keys)) == 12 and all(re.match(r"^[a-z_]+:\S+$", k) for k in keys), "twelve register keys, one a line"


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "society_officers": "person", "gazette_prohibitions": "person",
        "gazette_bankruptcies": "person", "gazette_liquidators": "person", "companies": "organisation", "societies": "organisation",
        "company_addresses": "place", "gazette_company_notices": "organisation", "gazette_liquidations": "organisation",
        "gazette_possessions": "event", "company_states": "organisation"}
THROUGH = "reached through a person on the subject ({who}): an officer's other role is the officer's connection, not the subject's; near, never confirmed"


def it(ref, view, grade="confirmed", title="X", dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False, entity_title=None,
       through=None, rule_=None, **extra):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": KIND[view], "title": title, "statement": f"{title}: a row",
            "dates": {"undated": dates == "undated", "text": dates}, "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1,
            "grade": grade, "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": [], "replaced_by": None, "entity_title": entity_title,
            "rule": rule_, **({"through": through} if through else {}), **extra}


def company(n, title, status="Registered", registered="2014-01-17", **kw):
    return it(f"companies:companies/{n}", "companies", title=title, dates=f"from {registered}",
              row={"key": f"companies/{n}", "nzbn": str(n), "status": status, "entity_type": "LTD", "registered_on": registered, "in_latest": True}, **kw)


def director(n, letter, title, appointed, company_title, via=None, grade="confirmed", reason=None, through=None, suppressed=False):
    return it(f"companies:companies/{n}/director/{letter}", "directors", grade=grade, title=title, dates=f"from {appointed}", via=via,
              row={"entity_key": f"companies/{n}", "role_type": "DIRECTOR", "appointed_on": appointed, "in_latest": True},
              reason=reason, entity_title=company_title, through=through, rule_="through-officer" if through else None, suppressed=suppressed)


def holder(n, letter, title, company_title, via=None, grade="confirmed", through=None):
    return it(f"companies:companies/{n}/shareholder/{letter}", "shareholders", grade=grade, title=title, dates="undated", via=via,
              row={"entity_key": f"companies/{n}", "shares": 100, "in_latest": True}, entity_title=company_title, through=through)


def liquidation(n, company_title, appointed, grade="near", through=None, via=None):
    return it(f"gazette:gazette/{appointed}-al/company/{n}", "gazette_liquidations", grade=grade, title=company_title,
              dates=f"appointed {appointed}", row={"register_key": f"companies/{n}", "appointed_on": appointed, "published_on": appointed,
                                                   "appointed_by": "shareholders"},
              via=via or f"companies:companies/{n}", through=through, rule_="through-officer" if through else None,
              reason=THROUGH.format(who="Ann Mary ROE") if grade == "near" else None)


def notice(n, company_title, kind, published, grade="near", through=None, action="", via=None, basis="published"):
    return it(f"gazette:gazette/{published}-{kind[:3]}/company/{n}", "gazette_company_notices", grade=grade, title=f"{company_title} · {kind}",
              dates=f"published {published}", row={"register_key": f"companies/{n}", "kind": kind, "action": action, "published_on": published,
                                                   "event_basis": basis, "event_on": published},
              via=via or f"companies:companies/{n}", through=through, rule_="through-officer" if through else None,
              reason=THROUGH.format(who="Ann Mary ROE") if grade == "near" else None)


#: the entity: a young development company, Ann its one director, Ann and a trustee company its holders
ENTITY = company(1, "KAURI HEIGHTS DEVELOPMENT LIMITED", registered="2025-03-01")
ANN = director(1, "a", "Ann Mary ROE", "2025-03-01", ENTITY["title"], via=ENTITY["ref"])
ANN_HOLDS = holder(1, "a", "Ann Mary ROE", ENTITY["title"], via=ENTITY["ref"])
TRUSTEE_HOLDS = holder(1, "t", "KAURI TRUSTEE LIMITED", ENTITY["title"], via=ENTITY["ref"])
NEAR_ANN = THROUGH.format(who="Ann Mary ROE")
#: Ann's earlier projects, reached through her row on the entity: two failed, one going
OLD1 = company(2, "TOTARA VIEW DEVELOPMENT LIMITED", status="In Liquidation", registered="2019-01-10", grade="near", reason=NEAR_ANN,
               through=ANN["ref"], rule_="through-officer")
OLD2 = company(3, "RIMU PARK DEVELOPMENT LIMITED", status="In Receivership", registered="2021-02-01", grade="near", reason=NEAR_ANN,
               through=ANN["ref"], rule_="through-officer")
GOING = company(4, "MATAI GROVE DEVELOPMENT LIMITED", registered="2023-09-01", grade="near", reason=NEAR_ANN, through=ANN["ref"],
                rule_="through-officer")
ANN_ON = {c["ref"]: director(c["ref"].rsplit("/", 1)[1], "a", "Ann Mary ROE", c["row"]["registered_on"], c["title"], via=ANN["ref"],
                             grade="near", reason=NEAR_ANN, through=ANN["ref"]) for c in (OLD1, OLD2, GOING)}
OLD1_LIQ = liquidation(2, OLD1["title"], "2021-05-01", through=ANN["ref"])
OLD2_REC = notice(3, OLD2["title"], "receivership", "2023-06-01", through=ANN["ref"], action="appointment of receivers")
OLD2_REMOVAL = notice(3, OLD2["title"], "removal", "2024-01-15", through=ANN["ref"], action="intention to remove", basis="objections by")
OWN_LIQ = liquidation(1, ENTITY["title"], "2026-08-12", grade="confirmed", via=ENTITY["ref"])
OWN_REMOVAL = notice(1, ENTITY["title"], "removal", "2026-08-13", grade="confirmed", action="intention to remove", via=ENTITY["ref"], basis="objections by")
#: the registered offices
OFFICE = it("companies:companies/1/registered-office/2025-03-01/a", "company_addresses", title="Level 2, 10 Queen Street · Auckland 1010",
            dates="from 1 March 2025", via=ENTITY["ref"], row={"entity_key": "companies/1", "kind": "registered office", "line_1": "Level 2, 10 Queen Street",
                                                               "postcode": "1010", "started_on": "2025-03-01", "in_latest": True})
PRO_OFFICE = dict(OFFICE, row=dict(OFFICE["row"], line_1="Smith & Co Chartered Accountants", line_2="10 Queen Street"))
CARE_OF_OFFICE = dict(OFFICE, row=dict(OFFICE["row"], care_of="c/- Smith & Co"))
AT_OFFICE = company(9, "HOROEKA HOLDINGS LIMITED", status="In Liquidation", registered="2018-04-04", grade="near",
                    reason="shares the registered office with the subject", rule_="shared-office", via=OFFICE["ref"])
#: a mortgagee possession on Ann's receivership company, and one where the entity is the lender
POSSESSION = it("gazette:gazette/2023-mp1/possession/1", "gazette_possessions", grade="near", title="ACME FINANCE LIMITED · entry into possession",
                dates="entered 3 March 2023", row={"mortgagor_register_key": "companies/3", "mortgagee_register_key": "companies/77",
                                                   "entered_on": "2023-03-03"}, via=OLD2["ref"], through=ANN["ref"], reason=NEAR_ANN, rule_="through-officer")
OWN_POSSESSION = it("gazette:gazette/2026-mp2/possession/1", "gazette_possessions", title="ACME FINANCE LIMITED · entry into possession",
                    dates="entered 1 October 2026", row={"mortgagor_register_key": "companies/1", "entered_on": "2026-10-01"}, via=ENTITY["ref"])
LENDER_POSSESSION = it("gazette:gazette/2024-mp3/possession/1", "gazette_possessions", title="KAURI HEIGHTS DEVELOPMENT LIMITED · entry into possession",
                       dates="entered 1 May 2024", row={"mortgagee_register_key": "companies/1", "entered_on": "2024-05-01"}, via=ENTITY["ref"])
#: a prohibition and a bankruptcy on Ann's record
PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", grade="near", title="Ann Mary Roe · prohibition",
            dates="from 22 September 2022; to 22 September 2027", row={"ends_on": "2027-09-22"}, reason=NEAR_ANN, through=ANN["ref"], via=ANN["ref"],
            rule_="through-officer")
BANKRUPT = it("gazette:gazette/2019-ba1/person/1", "gazette_bankruptcies", grade="near", title="ROE · Ann Mary", dates="adjudicated 2 May 2019",
              row={"kind": "adjudication", "event_on": "2019-05-02"}, reason=NEAR_ANN, through=ANN["ref"], via=ANN["ref"], rule_="through-officer")
#: the holding chain above the entity
ABOVE = company(5, "KAURI TRUSTEE LIMITED", registered="2024-11-01", grade="near", rule_="chain", depth=1,
                hop_text="holds 50 shares of record in KAURI HEIGHTS DEVELOPMENT LIMITED, as filed (undated)")
PRO_HUB = {"ref": ANN["ref"], "title": "Ann Mary ROE", "kind": "professional-director", "text": "a professional director: 80 directorships"}
#: the person start: Ann's own row on the entity; her own confirmed rows on the earlier companies, and the companies confirmed
PERSON = dict(ANN, via=None)
P_OLD1, P_OLD2, P_GOING = (dict(c, grade="confirmed", reason=None, through=None, rule=None, via=f"{c['ref']}/director/a") for c in (OLD1, OLD2, GOING))
P_ON = [dict(d, grade="confirmed", reason=None, through=None, rule=None, via=PERSON["ref"]) for d in ANN_ON.values()]
P_ENTITY = dict(ENTITY, via=PERSON["ref"])
P_LIQ = dict(OLD1_LIQ, grade="confirmed", reason=None, through=None, rule=None, via=P_OLD1["ref"])
P_REC = dict(OLD2_REC, grade="confirmed", reason=None, through=None, rule=None, via=P_OLD2["ref"])
P_REMOVAL = dict(OLD2_REMOVAL, grade="confirmed", reason=None, through=None, rule=None, via=P_OLD2["ref"])
P_PROHIB = dict(PROHIB, grade="confirmed", reason=None, through=None, rule=None, via=PERSON["ref"])


def report(subject=ENTITY, hubs=(), officers_followed=1, officers_omitted=0, links_built=True, window=None, chain_stats=None, chain_notes=(),
           group_size=1, office_companies=2, office_listed=1, **sections):
    out = {"found": True, "as_of": "2026-10-21", "subject": subject, "members": [], "flags": [], "hubs": list(hubs),
           "template": {"name": "property", "reads": [{"view": v, "licence": "x", "attribution": "x", "refresh": "x"} for v in sorted(VIEWS)]},
           "group": {"built": links_built, "size": group_size, "contested": False, "omitted": 0},
           "walk": {"links_built": links_built, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0,
                    "officers_followed": officers_followed, "officers_omitted": officers_omitted, "office_companies": office_companies,
                    "office_listed": office_listed, "chain_depth": 2, "chain": chain_stats or {"depth": 1, "cut": 0}, "chain_notes": list(chain_notes),
                    "limits": {"officers": 12}, "settings": {"busy_address": 50}}, "sections": []}
    if window is not None:
        out["window_days"] = window
    for name in ORDER:
        xs = sections.get(name.replace("-", "_"), [])
        out["sections"].append({"name": name, "heading": name, "items": xs, "omitted": 0, "omitted_views": [], "blank": None if xs else "none found"})
    return out


def developer(**kw):
    """The entity, Ann its director: two of her earlier companies failed (a liquidation in 2021, a receivership in 2023), one is going."""
    parts = dict(principals=[ANN, ANN_HOLDS, TRUSTEE_HOLDS], history=[OLD1, OLD2, GOING] + list(ANN_ON.values()),
                 serial=[OLD1_LIQ, OLD2_REC], office=[OFFICE])
    parts.update(kw)
    return report(**parts)


def person(**kw):
    parts = dict(history=[P_ENTITY, P_OLD1, P_OLD2, P_GOING] + P_ON, serial=[P_LIQ, P_REC])
    parts.update(kw)
    return report(subject=PERSON, group_size=5, **parts)


def flags_of(mod, r):
    return [fn(r) for fn in mod.RULES]


# ── the properties, each a list of what broke (empty when they hold) ────────

def properties(mod) -> list:
    """What a buyer relies on, checked on fixtures; the mutant check runs it on each broken copy of the rules and needs it to say
    something."""
    bad = []
    rl = lambda n: rule(n, mod)   # noqa: E731
    mod.HISTORY = False
    other = report(subject=it("gazette:gazette/2020-x/company/1", "gazette_liquidations", title="A NOTICE"))
    starts = {"developer": developer(), "person": person(), "empty": report(), "other": other,
              "everything": developer(serial=[OLD1_LIQ, OLD2_REC, OWN_LIQ], possessions=[POSSESSION, OWN_POSSESSION], people_notices=[PROHIB, BANKRUPT],
                                      office=[PRO_OFFICE, AT_OFFICE], chain=[ABOVE])}
    for start, r in starts.items():
        for f in flags_of(mod, r):
            if CAUSE.search(f["text"]):
                bad.append(f"{start}: {f['rule']} says a word of cause or ownership: {f['text'][:120]}")
            if CONTRACT.address_shaped(f["text"]) or "Queen Street" in f["text"] or "Chartered" in f["text"] or "Smith" in f["text"]:
                bad.append(f"{start}: {f['rule']} prints an address: {f['text'][:120]}")
    for name in ALWAYS_BLOCKED:
        for r in (developer(), person(), report()):
            if rl(name)(r)["status"] != "blocked":
                bad.append(f"{name} is not blocked: the register it reads is not held")
    # nothing over the principals' companies is ever clear while the file lists current roles only
    for name in PRINCIPAL_CHECKS:
        for what, r in (("a clean developer", report(principals=[ANN], history=[GOING, ANN_ON[GOING["ref"]]], office=[OFFICE])),
                        ("a clean person", person(serial=[])), ("a director past the limit", report(principals=[ANN], officers_omitted=1)),
                        ("no director listed", report(principals=[TRUSTEE_HOLDS])), ("a notice row", other)):
            if rl(name)(r)["status"] == "clear":
                bad.append(f"{what}: {name} cleared companies it cannot have seen")
    s = rl("serial_pattern")(report(principals=[ANN], officers_omitted=3))
    if "not followed" not in s["text"]:
        bad.append("a director past the limit is not said in the serial pattern's blocked text")
    # the serial pattern
    f = rl("serial_pattern")(developer())
    if not (f["status"] == "fired" and f["severity"] == "amber" and OLD1_LIQ["ref"] in f["citations"] and OLD2_REC["ref"] in f["citations"]):
        bad.append(f"two failed companies under the entity's director did not raise serial-pattern amber with both notices cited: {f['status']} {f['severity']}")
    for want in ("registered 2019-01-10", "liquidation (liquidator appointed by the shareholders), appointed 2021-05-01", "842 days from registration",
                 "MATAI GROVE DEVELOPMENT LIMITED: registered 2023-09-01", "days after"):
        if want not in f["text"]:
            bad.append(f"the serial pattern does not state {want!r}")
    p = rl("serial_pattern")(person())
    if not (p["status"] == "fired" and p["severity"] == "red"):
        bad.append(f"a person's own two insolvent companies did not raise serial-pattern red: {p['status']} {p['severity']}")
    if rl("serial_pattern")(person(hubs=[PRO_HUB]))["severity"] == "red":
        bad.append("a professional director's serial pattern was red: a hub sits on many companies")
    if rl("serial_pattern")(developer(serial=[OLD1_LIQ]))["status"] == "fired" and rl("serial_pattern")(
            developer(history=[OLD1, GOING, ANN_ON[OLD1["ref"]], ANN_ON[GOING["ref"]]], serial=[OLD1_LIQ]))["status"] == "fired":
        bad.append("one failed company raised the serial pattern: one is not a series")
    rem = rl("serial_pattern")(person(history=[P_ENTITY, dict(P_OLD1, row=dict(P_OLD1["row"], status="Removed")),
                                               dict(P_OLD2, row=dict(P_OLD2["row"], status="Removed")), P_GOING] + P_ON,
                                      serial=[dict(P_REMOVAL), dict(P_REMOVAL, ref=P_REMOVAL["ref"] + "x", row=dict(P_REMOVAL["row"], register_key="companies/2"))]))
    if rem["status"] == "fired" and rem["severity"] != "info":
        bad.append(f"two removals raised the serial pattern above info: a removal is not an insolvency ({rem['severity']})")
    # the reader's window
    cut = rl("serial_pattern")(developer(window=30))
    if "fall outside it and are not listed" not in cut["text"] or "MATAI GROVE DEVELOPMENT LIMITED: registered" in cut["text"]:
        bad.append("the reader's window of 30 days did not cut the pairs outside it")
    if "no window is set, so every gap is shown" not in f["text"]:
        bad.append("with no window set the serial pattern does not say every gap is shown")
    if "not a whole number of days" not in rl("serial_pattern")(developer(window="a year"))["text"]:
        bad.append("a window that is not a number of days is not named as no cut")
    e = rl("earlier_failure")(developer())
    if not (e["status"] == "fired" and "KAURI HEIGHTS DEVELOPMENT LIMITED: registered 2025-03-01" in e["text"] and "days after" in e["text"]):
        bad.append(f"a principal's earlier failure is not set beside the entity's start with the gap: {e['text'][:200]}")
    if e["severity"] == "red":
        bad.append("an earlier failure reached through a director was red")
    if rl("earlier_failure")(developer(window=10))["status"] == "fired":
        bad.append("a reader's window of 10 days still listed failures years from the entity's start")
    # the entity
    st = rl("entity_status")(developer(gazette=[OWN_LIQ]))
    if not (st["status"] == "fired" and st["severity"] == "red" and "newer than the file" in st["text"]):
        bad.append("a liquidation notice on an entity the latest file still calls Registered was not red")
    pend = rl("entity_status")(developer(gazette=[dict(OWN_REMOVAL, row=dict(OWN_REMOVAL["row"], event_on="2026-11-18"))]))
    if pend["severity"] != "amber":
        bad.append(f"a removal pending on the entity was not amber: a removal is not an insolvency ({pend['severity']})")
    lapsed = rl("entity_status")(developer(gazette=[OWN_REMOVAL]))
    if lapsed["severity"] != "info" or "was not removed" not in lapsed["text"]:
        bad.append("an intention to remove that lapsed (the file still calls the entity Registered) was not read as such")
    old_intent = dict(P_REMOVAL, ref=P_REMOVAL["ref"] + "g", via=P_GOING["ref"], row=dict(P_REMOVAL["row"], register_key="companies/4"))
    if rl("serial_pattern")(person(history=[P_ENTITY, P_OLD1, P_GOING] + P_ON, serial=[P_LIQ, old_intent]))["status"] == "fired":
        bad.append("an intention to remove a company that is still registered was counted as a failure")
    if rl("young_entity")(developer())["status"] != "fired":
        bad.append("an entity registered 2025-03-01 did not raise young-entity")
    if rl("young_entity")(report(subject=company(1, "OLD LIMITED", registered="2010-01-01")))["status"] == "fired":
        bad.append("an entity registered in 2010 raised young-entity")
    if rl("sole_vehicle")(report(principals=[ANN, ANN_HOLDS]))["status"] != "fired":
        bad.append("one director who is the one holder did not raise sole-vehicle")
    if rl("sole_vehicle")(report(principals=[ANN, TRUSTEE_HOLDS]))["status"] == "fired":
        bad.append("a director and a different holder raised sole-vehicle")
    # offices
    if rl("shared_office")(developer(office=[OFFICE, AT_OFFICE]))["severity"] != "amber" or rl("shared_office")(developer(office=[OFFICE, AT_OFFICE]))["status"] != "fired":
        bad.append("a liquidated company at the entity's office did not raise shared-office amber")
    hub = rl("shared_office")(developer(office=[PRO_OFFICE, AT_OFFICE]))
    if hub["status"] == "fired" and hub["severity"] != "info":
        bad.append("a company at an accountant's office raised shared-office: an accountant's office is a hub, never a cause")
    if rl("professional_office")(developer(office=[PRO_OFFICE]))["status"] != "fired":
        bad.append("an accountant's office was not flagged a hub")
    co = rl("professional_office")(developer(office=[CARE_OF_OFFICE]))
    if co["status"] != "fired" or "kept care of another" not in co["text"]:
        bad.append("an office kept care of another was not flagged a hub")
    if rl("professional_office")(developer())["status"] == "fired":
        bad.append("an ordinary office was flagged a hub")
    # possessions
    po = rl("possession")(developer(possessions=[POSSESSION]))
    if not (po["status"] == "fired" and po["severity"] == "amber" and "entered 3 March 2023" in po["text"]):
        bad.append(f"a possession on the director's other company did not raise possession amber with its date: {po['status']} {po['severity']}")
    if rl("possession")(developer(possessions=[OWN_POSSESSION]))["severity"] != "red":
        bad.append("a possession on the entity itself was not red")
    if rl("possession")(developer(possessions=[LENDER_POSSESSION]))["severity"] != "info":
        bad.append("a possession where the entity is the lender was not info")
    # the people
    pr = rl("prohibition")(person(people_notices=[P_PROHIB]))
    if not (pr["status"] == "fired" and pr["severity"] == "red"):
        bad.append(f"a prohibition in force on the person's own record was not red: {pr['status']} {pr['severity']}")
    if rl("prohibition")(developer(people_notices=[PROHIB]))["severity"] == "red":
        bad.append("a prohibition on a director reached through the officers reach was red")
    if rl("prohibition")(person(people_notices=[dict(P_PROHIB, row={"ends_on": "2024-01-01"})]))["severity"] == "red":
        bad.append("an ended prohibition was red")
    if rl("bankruptcy")(developer(people_notices=[BANKRUPT]))["status"] != "fired":
        bad.append("a bankruptcy on a director's record did not fire")
    for name in PEOPLE_CHECKS:
        for what, r in (("no director listed", report(principals=[TRUSTEE_HOLDS])), ("a director past the limit", report(principals=[ANN], officers_omitted=1)),
                        ("no links published", report(principals=[ANN], links_built=False)), ("a notice row", other)):
            if rl(name)(r)["status"] == "clear":
                bad.append(f"{what}: {name} cleared people it never read")
        if rl(name)(report(principals=[ANN]))["status"] != "clear":
            bad.append(f"a director followed with nothing on the record did not clear {name}")
    # the Gazette
    ins = rl("insolvency_notices")(developer(gazette=[OWN_LIQ]))
    if not (ins["status"] == "fired" and ins["severity"] == "red"):
        bad.append("a liquidation on the entity did not raise insolvency-notices red")
    if rl("insolvency_notices")(report(principals=[ANN], gazette=[OWN_REMOVAL]))["status"] == "fired":
        bad.append("a removal on the entity raised insolvency-notices")
    if rl("holding_chain")(developer(chain=[ABOVE], chain_notes=[{"text": "A TRUST: not followed", "via": "x", "depth": 1}]))["status"] != "blocked":
        bad.append("a holder the chain could not follow did not block holding-chain")
    hr = rl("history_reach")(report(principals=[ANN]))
    if hr["status"] != "blocked":
        bad.append("a director who reached no other company did not block history-reach")
    # no suppressed name in a flag
    # the shape masks a suppressed row's title; the rules keep their own guard, so a row marked suppressed is never named even unmasked
    hidden = dict(ANN, suppressed=True)
    hidden_on = [dict(d, suppressed=True) for d in ANN_ON.values()]
    r = developer(principals=[hidden], history=[OLD1, OLD2, GOING] + hidden_on, people_notices=[dict(PROHIB, suppressed=True)])
    for fl in flags_of(mod, r):
        if "Ann Mary" in fl["text"] or "Roe" in fl["text"]:
            bad.append(f"{fl['rule']} printed a suppressed director's name")
    if rl("serial_pattern")(r)["status"] != "fired":
        bad.append("a suppressed director's companies were dropped from the serial pattern; the row and the dates stay")
    return bad


def test_the_properties_hold_on_the_rules_as_written():
    assert properties(R) == []


#: (what the mutant breaks, the text replaced, its replacement): each must be unique in rules.py and caught by properties()
MUTANTS = (
    ("a series through a director is red", "sev = _evidence_grade(report, p) if len(insolvencies) >= SERIAL_AT else", "sev = \"red\" if len(insolvencies) >= SERIAL_AT else"),
    ("a hub's series is red", "return \"red\" if p[\"grade\"] == \"confirmed\" and not p[\"hub\"] else \"amber\"", "return \"red\" if p[\"grade\"] == \"confirmed\" else \"amber\""),
    ("one failure is a series", "        if len(failed) < SERIAL_AT:\n            continue", "        if len(failed) < 1:\n            continue"),
    ("a clear is given though past roles are not held", "    if HISTORY:\n        return flag(rule, V, \"clear\", severity, text, **kw)",
     "    if True:\n        return flag(rule, V, \"clear\", severity, text, **kw)"),
    ("a removal is an insolvency", "return it[\"view\"] == \"gazette_company_notices\" and r.get(\"kind\") in INSOLVENCY_KINDS and", "return it[\"view\"] == \"gazette_company_notices\" and"),
    ("the reader's window cuts nothing", "out.append((f, g, days, window is None or abs(days) <= window))", "out.append((f, g, days, True))"),
    ("the window is never read", "    w = report.get(WINDOW_KEY)\n    if w is None", "    w = None\n    if w is None"),
    ("a lapsed intention to remove is a failure", " and _ending(by_ref[c]) != \"going\" else None", " else None"),
    ("a notice newer than the file is not read", "    if st == \"insolvent\" or ins:", "    if st == \"insolvent\":"),
    ("the entity is never young", "        if days < YOUNG_DAYS:", "        if days < 0:"),
    ("any one director and one holder is a one-person vehicle", "and _fold(ds[0][\"title\"]) == _fold(hs[0][\"title\"])", ""),
    ("a hub office is compared", "        if mine and any(_office_hub(report, s[\"ref\"], it) for it in mine):", "        if False:"),
    ("an accountant's office is not seen", "return bool(PROFESSIONAL_OFFICE.search(", "return bool(False and PROFESSIONAL_OFFICE.search("),
    ("a possession through a director is red", "        sev = \"red\" if own else \"amber\"", "        sev = \"red\""),
    ("a lender's possession is the developer's", "    as_lender = [it for it in ps if it not in as_borrower]\n    if as_borrower:",
     "    as_lender = []\n    as_borrower = ps\n    if as_borrower:"),
    ("a prohibition through a director is red", "red = [it for it in conf if _person_start(report) and", "red = [it for it in rows if"),
    ("an ended prohibition is red", "and (view != \"gazette_prohibitions\" or _in_force(it, as_of))]", "]"),
    ("a company with no director clears its people", "        if not _own_people(report):\n            return \"the companies file lists no current director",
     "        if False:\n            return \"the companies file lists no current director"),
    ("a director past the limit clears", "        if w.get(\"officers_omitted\"):\n            return f\"{w['officers_omitted']} director(s) past the walk's limit were not followed\"",
     "        if False:\n            return f\"{w['officers_omitted']} director(s) past the walk's limit were not followed\""),
    ("unpublished links clear the people", "    if not w.get(\"links_built\"):\n        return \"no links are published", "    if False:\n        return \"no links are published"),
    ("a director past the limit is not said", "    if _company_start(report) and w.get(\"officers_omitted\"):", "    if False:"),
    ("an empty history is a clean one", "    empty = [p for p in principals.values() if len(p[\"companies\"]) <= 1]", "    empty = []"),
    ("a suppressed director is named", "\"a director whose name is suppressed\" if d.get(\"suppressed\") else d[\"title\"]", "d[\"title\"]"),
    ("an insolvency on the entity is amber", "        sev = \"red\" if own or (conf and _person_start(report)) else \"amber\"", "        sev = \"amber\""),
    ("a holder the chain cannot follow is ignored", "    if notes or st.get(\"cut\"):", "    if st.get(\"cut\"):"),
    ("a failure's text quotes an address-shaped name", "return f\"the company cited ({it['ref']})\" if UNSAFE.search(t) or contract.address_shaped(t) else t",
     "return t"),
)


@pytest.mark.parametrize("what,old,new", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_a_mutant_of_the_rules_is_caught(what, old, new):
    with open(os.path.join(HERE, "rules.py"), encoding="utf-8") as f:
        src = f.read()
    assert src.count(old) == 1, f"the mutant's target is not unique in rules.py: {old!r}"
    caught = properties(rules_module(src.replace(old, new)))
    if what == "a failure's text quotes an address-shaped name":
        caught = caught or _address_named_company_is_masked(rules_module(src.replace(old, new)))
    assert caught, f"the mutant '{what}' passed every property: a check that cannot fail"


def _address_named_company_is_masked(mod) -> list:
    """A company registered under an address-shaped name ("12 SHEA TERRACE LIMITED") is never quoted in a flag."""
    named = dict(OLD1, title="12 SHEA TERRACE LIMITED")
    r = developer(history=[named, OLD2, GOING] + list(ANN_ON.values()))
    return [f["rule"] for f in flags_of(mod, r) if "SHEA TERRACE" in f["text"]]


def test_an_address_shaped_company_name_is_never_quoted_in_a_flag():
    assert _address_named_company_is_masked(R) == []


# ── each rule, on fixtures ──────────────────────────────────────────────────

def test_every_rule_runs_from_each_start_once_and_carries_no_common_rules_name():
    soc = it("societies:societies/9", "societies", title="A SOCIETY INCORPORATED", row={"status": "registered"})
    for r in (report(), developer(), person(), report(subject=soc)):
        flags = flags_of(R, r)
        assert len({f["rule"] for f in flags}) == len(flags) == len(R.RULES)
        assert not {f["rule"] for f in flags} & set(COMMON), "the builder runs the common rules; no copy here"
    assert R.flag is CONTRACT.flag and R.items is CONTRACT.items and R.section is CONTRACT.section and R.all_items is CONTRACT.all_items
    assert "common_rules" not in toml(), "the template keeps the builder's common rules"


def test_the_serial_pattern_sets_out_each_failure_in_the_order_registered_with_its_gap():
    f = rule("serial_pattern")(developer())
    assert f["status"] == "fired" and f["scope"] == "principals"
    assert "Ann Mary ROE: 2 of 4 companies failed (2 an insolvency, 0 a removal from the register, which is not an insolvency), in the order registered: " \
           "TOTARA VIEW DEVELOPMENT LIMITED (registered 2019-01-10;" in f["text"]
    assert f["text"].index("TOTARA VIEW") < f["text"].index("RIMU PARK")
    assert "receivership, published 2023-06-01, 850 days from registration" in f["text"]
    assert "start a report from the director for the confirmed record" in f["text"]
    assert "of 4 pair(s), nearest first, 0 within 90 days and 1 within 365 days" in f["text"]
    p = rule("serial_pattern")(person())
    assert p["severity"] == "red" and "the person's own confirmed companies" in p["text"]


def test_every_register_not_held_blocks():
    for name in ALWAYS_BLOCKED:
        for r in (developer(), person(), report()):
            f = rule(name)(r)
            assert f["status"] == "blocked" and f["text"].startswith("not held: "), name
    assert "Overseas Investment Office" in rule("overseas_investment")(report())["text"]
    assert "council minutes" in rule("building_consents")(report())["text"]


def test_the_presentation_rules_hold_on_every_flag_from_every_start():
    """The shape's own check (rule 9 and rule 3 on fired flags), run on the flags each start produces, as the builder runs it."""
    for r in (developer(), developer(serial=[OLD1_LIQ, OLD2_REC, OWN_LIQ], possessions=[POSSESSION, OWN_POSSESSION, LENDER_POSSESSION],
                                     people_notices=[PROHIB, BANKRUPT], office=[PRO_OFFICE, AT_OFFICE], chain=[ABOVE]),
              person(people_notices=[P_PROHIB]), report()):
        r["flags"] = flags_of(R, r)
        problems = [p for p in CONTRACT.presentation_problems(r) if p.startswith("flag ")]
        assert problems == [], problems


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
