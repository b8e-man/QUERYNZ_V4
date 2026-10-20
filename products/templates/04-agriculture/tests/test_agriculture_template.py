"""The agriculture counterparty template on fixtures: it loads on the shape,
names only published views with their licences, runs its sections in the
credit manager's order, and its rules keep the flag contract: the
counterparty's own register status and Gazette notices are red, a namesake's
amber, a check the walk could not have seen blocked (from a company, its
officers are not followed yet), a removal is not insolvency, dates side by
side and no word of cause or of ownership. Imports nothing of
products.report (the one-way test): the shape is reached through its
command line, and the rules file is loaded by path as the shape loads it."""
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
ORDER = ["identity", "officers", "gazette", "other-companies", "societies", "money", "not-held"]
#: words that would join two facts as cause or call a holder an owner (the shape's rules 3 and 4 hold the full list on every report)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|behind|owners?|owns|owned|"
                   r"beneficial)\b", re.I)
GAZETTE = {"gazette_prohibitions", "gazette_bankruptcies", "gazette_liquidations", "gazette_company_notices"}


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def rules_module():
    spec = importlib.util.spec_from_file_location("qv4_test_agriculture_rules", os.path.join(HERE, "rules.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R = rules_module()


def rule(name):
    for r in R.RULES:
        if r.__name__ == name:
            return r
    raise KeyError(name)


# ── the template ────────────────────────────────────────────────────────────

def test_the_shape_loads_it_by_name_with_every_view_known_and_every_rule():
    out = subprocess.run([sys.executable, "-m", "products.report", "templates"], cwd=REPO, capture_output=True, text=True, timeout=20)
    assert out.returncode == 0, out.stderr
    line = [x for x in out.stdout.splitlines() if x.startswith("agriculture ")]
    assert line and HERE in line[0], out.stdout
    t = toml()
    assert f"{len(t['reads'])} views, {len(t['sections'])} sections, {len(R.RULES)} rules" in line[0]


def test_it_names_each_view_once_with_its_licence_and_fewer_than_the_shape():
    t = toml()
    views = [r["view"] for r in t["reads"]]
    assert len(views) == len(set(views)) and t["depth"] == 1
    assert all(r.get("licence") and r.get("attribution") and r.get("refresh") for r in t["reads"])
    with open(os.path.join(REPO, "products", "report", "templates", "subject", "template.toml"), "rb") as f:
        shape = {r["view"] for r in tomllib.load(f)["reads"]}
    assert set(views) < shape, "a use-case template names fewer views than the shape's"
    assert "gazette_appointments" not in views, "no link reaches an appointment: reading it would print a blank that is not a clear"


def test_its_sections_run_in_the_credit_managers_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"], "the first section holds the namesakes and nothing confirmed"
    assert not set(s["identity"]["views"]) & GAZETTE, "a near Gazette notice stays in the Gazette section"
    assert "roles" in s["officers"]["sources"], "from a company, its directors and holders are the walk's roles"
    assert "second" not in {x for sec in t["sections"] for x in sec.get("sources", [])}, "co-directors are not the counterparty's record"
    assert set(s["gazette"]["views"]) == GAZETTE and "pointing" in s["gazette"]["sources"]
    assert {"insolvency", "courts"} <= set(s["gazette"]["not_held"]) and "charities" in s["societies"]["not_held"]
    assert {"securities", "linz", "limited_partnerships"} <= set(s["not-held"]["not_held"]) and s["not-held"]["views"] == []
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views


def test_the_known_limits_page_exists_and_the_template_states_its_limits():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    assert "namesake" in page and "not a clear" in page and "checkpoint" in page.lower()
    lim = toml()["limits"]
    assert any("namesake" in x for x in lim) and any("not a clear" in x for x in lim) and any("does not yet follow" in x for x in lim)


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "society_officers": "person", "gazette_prohibitions": "person",
        "gazette_bankruptcies": "person", "companies": "organisation", "societies": "organisation", "company_addresses": "place",
        "gazette_company_notices": "organisation", "gazette_liquidations": "organisation", "party_return_donors": "figure"}


def it(ref, view, grade="confirmed", title="X", statement=None, dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False,
       kind=None):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": kind or KIND[view], "title": title,
            "statement": statement or f"{title}: a row", "dates": {"undated": dates == "undated", "text": dates},
            "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1, "grade": grade,
            "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": [], "replaced_by": None}


FARM = it("companies:companies/1", "companies", title="HILL FARM LIMITED", statement="HILL FARM LIMITED: Registered LTD, NZBN 1",
          dates="from 3 March 2011; no end filed (in the latest file)",
          row={"key": "companies/1", "nzbn": "1", "status": "Registered", "entity_type": "LTD", "registered_on": "2011-03-03", "in_latest": True})
PERSON = it("companies:companies/1/director/a", "directors", title="Jane Mary DOE", statement="Jane Mary DOE: DIRECTOR of HILL FARM LIMITED",
            dates="from 3 March 2011; no end filed (in the latest file)",
            row={"entity_key": "companies/1", "role_type": "DIRECTOR", "in_latest": True})
DIRECTOR = dict(PERSON, via=FARM["ref"])
HOLDER = it("companies:companies/1/shareholder/b", "shareholders", title="DOE FAMILY TRUSTEE LIMITED", via=FARM["ref"], dates="undated",
            row={"entity_key": "companies/1", "shareholder_type": "company", "in_latest": True})
RECEIVER = it("gazette:gazette/2025-ar1/company/1", "gazette_company_notices", title="HILL FARM LIMITED · receivership", dates="23 July 2025",
              row={"kind": "receivership", "register_key": "companies/1"}, via=FARM["ref"])
REMOVAL = it("gazette:gazette/2024-ar2/company/1", "gazette_company_notices", title="HILL FARM LIMITED · removal", dates="17 December 2024",
             row={"kind": "removal", "register_key": "companies/1"}, via=FARM["ref"])
OTHER = it("companies:companies/2", "companies", title="OLD DAIRY LIMITED", dates="from 1 May 2005; to 2 June 2019",
           row={"key": "companies/2", "status": "In Liquidation", "registered_on": "2005-05-01", "in_latest": True}, via=PERSON["ref"])
OTHER_LIQ = it("gazette:gazette/2018-al1/company/1", "gazette_liquidations", title="Old Dairy Limited", dates="13 July 2018",
               row={"register_key": "companies/2"}, via=OTHER["ref"])
PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", title="Jane Mary Doe · prohibition",
            dates="from 22 September 2022; to 22 September 2026", row={"ends_on": "2026-09-22"})


def report(subject=FARM, **sections):
    out = {"found": True, "as_of": "2026-10-20", "subject": subject, "members": [], "flags": [], "hubs": [],
           "group": {"built": True, "size": 1, "contested": False, "omitted": 0},
           "walk": {"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0}, "sections": []}
    for name in ORDER:
        items = sections.get(name.replace("-", "_"), [])
        out["sections"].append({"name": name, "heading": name, "items": items, "omitted": 0, "blank": None if items else "none found in Gazette notices"})
    return out


def full():
    return report(officers=[DIRECTOR, HOLDER], gazette=[RECEIVER, REMOVAL])


def person(**sections):
    return report(subject=PERSON, **sections)


def test_every_rule_runs_on_bare_and_full_reports_from_each_start_and_no_flag_says_cause_or_owner():
    society = it("societies:societies/9", "societies", title="A FARMERS CLUB INCORPORATED")
    for r in (report(), full(), person(), person(officers=[PERSON], gazette=[OTHER_LIQ, PROHIB], other_companies=[OTHER]), report(subject=society)):
        flags = [f(r) for f in R.RULES]
        assert len({f["rule"] for f in flags}) == len(flags) == len(R.RULES)
        for f in flags:
            assert not CAUSE.search(f["text"]), (f["rule"], f["text"])


def test_the_flag_contract_is_held_at_construction():
    with pytest.raises(ValueError, match="cite"):
        R.flag("r", "0.1", "fired", "red", "x")
    with pytest.raises(ValueError, match="sources"):
        R.flag("r", "0.1", "clear", "red", "x")
    with pytest.raises(ValueError, match="why"):
        R.flag("r", "0.1", "blocked", "red", "")


def test_register_status_reads_the_counterpartys_own_status():
    assert rule("register_status")(report())["status"] == "clear"
    for status, sev in (("In Receivership", "red"), ("Removed", "red"), ("In Liquidation and Receivership", "red"), ("deregistered", "red")):
        f = rule("register_status")(report(subject=dict(FARM, row=dict(FARM["row"], status=status))))
        assert f["status"] == "fired" and f["severity"] == sev and status in f["text"] and f["citations"] == (FARM["ref"],)
    gone = rule("register_status")(report(subject=dict(FARM, row=dict(FARM["row"], in_latest=False))))
    assert gone["status"] == "fired" and gone["severity"] == "amber"
    assert rule("register_status")(person())["status"] == "blocked", "a sole trader's business-number entry is not held"
    lp = rule("register_status")(report(subject=dict(FARM, row=dict(FARM["row"], entity_type="NZ Limited Partnership"))))
    assert lp["status"] == "clear" and any("partners" in x for x in lp["sources_not_held"])


def test_an_insolvency_notice_on_the_counterparty_is_red_and_a_removal_is_not_insolvency():
    f = rule("entity_insolvency")(full())
    assert f["status"] == "fired" and f["severity"] == "red" and f["citations"] == (RECEIVER["ref"],) and "23 July 2025" in f["text"]
    only_removal = report(officers=[DIRECTOR], gazette=[REMOVAL])
    assert rule("entity_insolvency")(only_removal)["status"] == "clear"
    rm = rule("register_removals")(only_removal)
    assert rm["status"] == "fired" and rm["severity"] == "amber" and "17 December 2024" in rm["text"]


def test_from_a_company_the_officers_checks_are_blocked_never_clear():
    r = full()
    for name in ("officer_group_insolvency", "prohibition", "other_companies", "charity_officer_roles", "practitioner_repeat", "bankruptcy"):
        f = rule(name)(r)
        assert f["status"] == "blocked", (name, f)
    assert "start a report from each person" in rule("prohibition")(r)["text"]


def test_from_a_person_the_companies_notices_sit_beside_the_persons_dates_and_are_red():
    r = person(officers=[PERSON], gazette=[OTHER_LIQ], other_companies=[OTHER])
    f = rule("officer_group_insolvency")(r)
    assert f["status"] == "fired" and f["severity"] == "red" and "13 July 2018" in f["text"]
    assert rule("entity_insolvency")(r)["status"] == "clear"
    oc = rule("other_companies")(r)
    assert oc["status"] == "fired" and oc["severity"] == "amber" and "In Liquidation" in oc["text"] and oc["citations"] == (OTHER["ref"],)
    assert rule("practitioner_repeat")(r)["status"] == "blocked", "the practitioners' names are not reached from a notice"


def test_a_namesakes_notice_is_amber_and_says_so():
    near_liq = dict(OTHER_LIQ, grade="near", reason="reached through a near link: the two rows share a first and last name")
    f = rule("officer_group_insolvency")(person(gazette=[near_liq], other_companies=[dict(OTHER, grade="near")]))
    assert f["status"] == "fired" and f["severity"] == "amber" and f["scope"] == "near" and "namesake" in f["text"]


def test_a_walk_that_stopped_short_gives_no_clear_on_the_companies_it_did_not_read():
    r = person(other_companies=[dict(OTHER, row=dict(OTHER["row"], status="Registered"))])
    r["walk"]["entities_not_expanded"] = 3
    assert rule("officer_group_insolvency")(r)["status"] == "blocked"
    assert rule("other_companies")(r)["status"] == "blocked"
    assert rule("practitioner_repeat")(r)["status"] == "blocked"


def test_a_prohibition_confirmed_is_red_with_its_force_and_a_revoked_one_is_never_counted():
    f = rule("prohibition")(person(gazette=[PROHIB]))
    assert f["status"] == "fired" and f["severity"] == "red" and "ended before 2026-10-20" in f["text"]
    assert rule("prohibition")(person(gazette=[dict(PROHIB, grade="near")]))["severity"] == "amber"
    f = rule("prohibition")(person(gazette=[dict(PROHIB, suppressed=True)]))
    assert f["status"] == "clear" and PROHIB["ref"] not in f["citations"]
    r = person()
    r["walk"]["links_omitted"] = 4
    assert rule("prohibition")(r)["status"] == "blocked"


def test_officers_of_record_flags_a_going_company_with_no_current_director_but_not_a_partnership_or_a_removed_one():
    ended = dict(DIRECTOR, row=dict(DIRECTOR["row"], ended_on="2020-01-01"))
    f = rule("officers_of_record")(report(officers=[ended]))
    assert f["status"] == "fired" and f["severity"] == "amber"
    assert rule("officers_of_record")(report(officers=[DIRECTOR]))["status"] == "clear"
    lp = report(subject=dict(FARM, row=dict(FARM["row"], entity_type="NZ Limited Partnership")))
    assert rule("officers_of_record")(lp)["status"] == "blocked"
    removed = report(subject=dict(FARM, row=dict(FARM["row"], status="Removed")), officers=[ended])
    assert rule("officers_of_record")(removed)["status"] == "clear"


def test_a_company_holder_and_a_nominee_are_flagged_and_never_called_owners():
    f = rule("company_holders")(full())
    assert f["status"] == "fired" and f["citations"] == (HOLDER["ref"],) and not CAUSE.search(f["text"])
    r = full()
    r["hubs"] = [{"ref": HOLDER["ref"], "title": HOLDER["title"], "kind": "nominee", "text": "a nominee: never as an owner", "evidence": "x"},
                 {"ref": FARM["ref"], "title": FARM["title"], "kind": "busy-address", "text": "a busy address", "evidence": {"companies": 497}}]
    h = rule("hubs_met")(r)
    assert h["status"] == "fired" and "497" in h["text"] and "holder of record for others" in h["text"] and not CAUSE.search(h["text"])
    assert rule("hubs_met")(report())["status"] == "clear"


def test_young_entity_reads_the_counterpartys_own_registration_date():
    young = dict(FARM, row=dict(FARM["row"], registered_on="2025-06-27"))
    f = rule("young_entity")(report(subject=young))
    assert f["status"] == "fired" and "2025-06-27" in f["text"]
    assert rule("young_entity")(report())["status"] == "clear"


def test_a_society_start_does_not_count_its_own_officers_as_the_counterpartys_roles():
    soc = it("societies:societies/9", "societies", title="A FARMERS CLUB INCORPORATED")
    off = it("societies:societies/9/officer/1", "society_officers", via=soc["ref"])
    r = report(subject=soc, societies=[off])
    assert rule("charity_officer_roles")(r)["status"] == "blocked"
    assert rule("register_status")(r)["status"] == "blocked" and "an organisation row" in rule("register_status")(r)["text"]
    assert rule("charity_officer_roles")(person(societies=[dict(off, via=None)]))["status"] == "fired"


def test_money_reads_only_confirmed_rows_and_names_the_namesakes():
    don = it("party_returns:x/A/1", "party_return_donors", grade="near", title="HILL FARM LTD · $5,000")
    f = rule("political_money")(report(identity=[don]))
    assert f["status"] == "clear" and "namesakes" in f["text"]
    assert rule("political_money")(report(money=[dict(don, grade="confirmed")]))["status"] == "fired"


def test_mpi_charity_marks_and_bankruptcy_are_blocked_while_not_held():
    for name in ("mpi_coverage", "charity_integrity_marks", "bankruptcy"):
        assert rule(name)(person())["status"] == "blocked"
    assert "not a clear" in rule("bankruptcy")(person())["text"]


def test_identity_is_amber_on_a_contested_group():
    r = person()
    r["group"].update(contested=True, size=7)
    assert rule("identity")(r)["severity"] == "amber"
    assert rule("identity")(report())["status"] == "clear" and "NZBN 1" in rule("identity")(report())["text"]


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
