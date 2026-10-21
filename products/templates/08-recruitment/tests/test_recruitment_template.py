"""The recruitment template on fixtures: it loads on the shape, names only
published views with their licences, runs its sections in the consultant's
order, and its rules keep the flag contract: a red only on the subject's
confirmed rows, amber on a namesake's, a blocked check where the registers
held cannot see, dates side by side and no word of cause, a revoked
prohibition never counted. Imports nothing of products.report (the one-way
test): the shape is reached through its command line, and the rules file is
loaded by path as the shape loads it, with the name `contract` bound to the
shape's contract file (products/report/contract.py, read by path) before it
runs."""
import importlib.util
import inspect
import os
import re
import subprocess
import sys
import tomllib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ORDER = ["identity", "companies", "gazette", "societies", "money", "public", "not-held"]
#: words that would join two facts as cause or call a holder an owner (the shape's rules 3 and 4 hold the full list on every report)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|behind|owners?|owns|owned)\b", re.I)
GAZETTE = {"gazette_prohibitions", "gazette_bankruptcies", "gazette_liquidations", "gazette_company_notices"}


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


def rules_module():
    """As the shape's loader does: `contract` bound, then the file run."""
    contract = by_path("qv4_test_report_contract", os.path.join(REPO, "products", "report", "contract.py"))
    return by_path("qv4_test_recruitment_rules", os.path.join(HERE, "rules.py"), contract=contract)


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
    line = [x for x in out.stdout.splitlines() if x.startswith("recruitment ")]
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
    assert "gazette_appointments" not in views, "no link reaches an appointment yet: reading it would print a blank that is not a clear"


def test_its_sections_run_in_the_consultants_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"], "the first section holds the namesakes and nothing confirmed"
    assert not set(s["identity"]["views"]) & GAZETTE, "a near Gazette notice stays in the Gazette section"
    assert not {"second", "roles"} & set(s["companies"]["sources"]), "co-directors are not the subject's record"
    assert {"charities", "charity_officers", "charity_returns"} <= set(s["societies"]["views"]) and "named" in s["societies"]["sources"]
    assert not any("charities" in x.get("not_held", []) for x in t["sections"]) and {"insolvency", "courts"} <= set(s["gazette"]["not_held"])
    assert s["not-held"]["views"] == [] and s["not-held"]["not_held"]
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views


def test_the_known_limits_page_exists_and_the_template_states_its_limits():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    assert "namesake" in page and "not a clear" in page
    assert any("namesake" in x for x in toml()["limits"]) and any("not a clear" in x for x in toml()["limits"])


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "society_officers": "person", "gazette_prohibitions": "person",
        "gazette_bankruptcies": "person", "members": "person", "companies": "organisation", "societies": "organisation",
        "gazette_company_notices": "organisation", "gazette_liquidations": "organisation",
        "charities": "organisation", "charity_officers": "person", "charity_returns": "figure"}


def it(ref, view, grade="confirmed", title="X", statement=None, dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False,
       kind=None):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": kind or KIND[view], "title": title, "statement": statement or f"{title}: a row",
            "dates": {"undated": dates == "undated", "text": dates}, "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1,
            "grade": grade, "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": [], "replaced_by": None}


SUBJECT = it("companies:companies/1/director/a", "directors", title="Jane Mary DOE", statement="Jane Mary DOE: DIRECTOR of ACME LIMITED",
             dates="from 3 March 2011; no end filed (in the latest file)", row={"entity_key": "companies/1", "role_type": "DIRECTOR"})


def report(subject=SUBJECT, **sections):
    out = {"found": True, "as_of": "2026-10-20", "subject": subject, "members": [], "flags": [], "hubs": [],
           "group": {"built": True, "size": 1, "contested": False, "omitted": 0},
           "walk": {"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0}, "sections": []}
    for name in ORDER:
        items = sections.get(name.replace("-", "_"), [])
        out["sections"].append({"name": name, "heading": name, "items": items, "blank": None if items else "none found in Gazette notices"})
    return out


ACME = it("companies:companies/1", "companies", title="ACME LIMITED", row={"registered_on": "2011-03-03"}, via=SUBJECT["ref"])
LIQ = it("gazette:gazette/2018-aw1/company/1", "gazette_company_notices", title="ACME LIMITED · winding-up application", dates="13 July 2018",
         row={"kind": "winding-up application"}, via="companies:companies/1")
REMOVAL = it("gazette:gazette/2024-ar1/company/1", "gazette_company_notices", title="ACME LIMITED · removal", dates="17 December 2024",
             row={"kind": "removal"}, via="companies:companies/1")
PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", title="Jane Mary Doe · prohibition",
            dates="from 22 September 2022; to 22 September 2026", row={"ends_on": "2026-09-22"})


def test_every_rule_runs_on_a_bare_report_and_on_a_full_one_and_no_flag_says_cause_or_owner():
    for r in (report(), report(companies=[ACME], gazette=[LIQ, REMOVAL, PROHIB])):
        flags = [f(r) for f in R.RULES]
        assert len({f["rule"] for f in flags}) == len(flags) == len(R.RULES)
        for f in flags:
            assert not CAUSE.search(f["text"]), (f["rule"], f["text"])


def test_the_flag_contract_is_held_at_construction():
    import pytest
    with pytest.raises(ValueError, match="cite"):
        R.flag("r", "0.1", "fired", "red", "x")
    with pytest.raises(ValueError, match="sources"):
        R.flag("r", "0.1", "clear", "red", "x")
    with pytest.raises(ValueError, match="why"):
        R.flag("r", "0.1", "blocked", "red", "")


def test_a_confirmed_insolvency_notice_is_red_with_both_dates_side_by_side_and_no_word_of_cause():
    f = rule("liquidation_history")(report(companies=[ACME], gazette=[LIQ]))
    assert f["status"] == "fired" and f["severity"] == "red" and f["citations"] == (LIQ["ref"],)
    assert "13 July 2018" in f["text"] and "from 3 March 2011" in f["text"]
    assert not CAUSE.search(f["text"])


def test_a_removal_notice_is_not_insolvency_and_is_its_own_info_flag():
    r = report(companies=[ACME], gazette=[REMOVAL])
    assert rule("liquidation_history")(r)["status"] == "clear"
    f = rule("register_removals")(r)
    assert f["status"] == "fired" and f["severity"] == "info" and "17 December 2024" in f["text"]


def test_a_notice_reached_through_a_namesake_is_amber_and_says_so():
    near_liq = dict(LIQ, grade="near", reason="reached through a near link: the two rows share a first and last name")
    f = rule("liquidation_history")(report(gazette=[near_liq]))
    assert f["status"] == "fired" and f["severity"] == "amber" and f["scope"] == "near" and "namesake" in f["text"]


def test_a_walk_that_stopped_short_gives_no_clear_on_the_companies_it_did_not_read():
    r = report(companies=[ACME])
    r["walk"]["entities_not_expanded"] = 3
    assert rule("liquidation_history")(r)["status"] == "blocked"


def test_a_prohibition_confirmed_is_red_and_says_whether_it_is_in_force():
    f = rule("prohibition")(report(gazette=[PROHIB]))
    assert f["status"] == "fired" and f["severity"] == "red" and "ended before 2026-10-20" in f["text"]
    live = dict(PROHIB, row={"ends_on": "2027-01-01"})
    assert "in force on 2026-10-20" in rule("prohibition")(report(gazette=[live]))["text"]


def test_a_prohibition_under_a_near_name_is_amber_and_a_revoked_one_is_never_counted():
    near_p = dict(PROHIB, grade="near", reason="the two rows share a first and last name but their middle names differ")
    f = rule("prohibition")(report(gazette=[near_p]))
    assert f["status"] == "fired" and f["severity"] == "amber" and "middle names differ" in f["text"]
    revoked = dict(PROHIB, suppressed=True)
    f = rule("prohibition")(report(gazette=[revoked]))
    assert f["status"] == "clear" and revoked["ref"] not in f["citations"]


def test_a_prohibition_gives_no_clear_when_links_went_unread_or_the_start_is_not_a_person():
    r = report()
    r["walk"]["links_omitted"] = 12
    assert rule("prohibition")(r)["status"] == "blocked"
    r = report()
    r["subject"] = dict(SUBJECT, kind="figure", view="party_return_donors")
    assert rule("prohibition")(r)["status"] == "blocked" and "person row" in rule("prohibition")(r)["text"]
    assert rule("liquidation_history")(r)["status"] == "blocked"
    assert rule("prohibition")(report())["status"] == "clear"


def test_bankruptcy_is_blocked_while_no_link_reaches_a_bankruptcy_notice():
    f = rule("bankruptcy")(report())
    assert f["status"] == "blocked" and "not a clear" in f["text"]
    b = it("gazette:gazette/2019-ab1/bankruptcy/1", "gazette_bankruptcies", title="DOE · Jane Mary", dates="1 May 2019")
    assert rule("bankruptcy")(report(gazette=[b]))["severity"] == "red"


def test_young_entity_reads_the_companys_own_registration_date():
    young = dict(ACME, row={"registered_on": "2025-06-05"}, title="NEW CO LIMITED")
    f = rule("young_entity")(report(companies=[young]))
    assert f["status"] == "fired" and "2025-06-05" in f["text"]
    assert rule("young_entity")(report(companies=[ACME]))["status"] == "clear"
    near_young = dict(young, grade="near")
    assert rule("young_entity")(report(companies=[near_young]))["status"] == "clear", "a namesake's company is not the subject's"


def test_namesake_exposure_fires_at_five_namesakes_and_on_a_contested_group():
    names = [it(f"companies:companies/{i}/director/x", "directors", grade="near") for i in range(5)]
    assert rule("namesake_exposure")(report(identity=names))["status"] == "fired"
    assert rule("namesake_exposure")(report(identity=names[:2]))["status"] == "clear"
    r = report()
    r["group"]["contested"] = True
    f = rule("namesake_exposure")(r)
    assert f["status"] == "fired" and f["citations"] == (SUBJECT["ref"],)


def test_charity_officer_roles_read_society_roles_and_comcom_is_blocked():
    off = it("societies:societies/9/officer/1", "society_officers", statement="Jane DOE: officer of A CLUB INCORPORATED (Active)", via="societies:societies/9")
    assert rule("charity_officer_roles")(report(societies=[off]))["status"] == "fired"
    assert rule("comcom_coverage")(report())["status"] == "blocked"


PERSON = SUBJECT


def company(**sections):
    return report(subject=dict(ACME, via=None), **sections)


# the Charities Register (card the-recruitment-template-can-now-read-the-charities-register)
CHARITY = it("charities:charities/CC1", "charities", title="ACME TRUST", statement="ACME TRUST: registered charity CC1, Registered; Trust",
             row={"key": "charities/CC1", "status": "Registered", "nzbn": "1"}, via=ACME["ref"])
TRUSTEE = it("charities:charities/CC1/officer/1", "charity_officers", title="John SMITH", via=CHARITY["ref"],
             statement="John SMITH: Trustee of ACME TRUST (Qualified; disqualified as the register states it: False)",
             row={"charity_key": "charities/CC1", "status": "Qualified", "disqualified": False})
BANNED = dict(TRUSTEE, ref="charities:charities/CC1/officer/2", title="Ann BLOGGS", row=dict(TRUSTEE["row"], status="Disqualified", disqualified=True),
              statement="Ann BLOGGS: Trustee of ACME TRUST (Disqualified; disqualified as the register states it: True)")
BY_NAME = it("charities:charities/CC9/officer/7", "charity_officers", grade="near", title="Jane Mary DOE", via=PERSON["ref"],
             reason="no link joins the Charities Register's officers to any other row yet, so this officer row is matched to the subject by name",
             statement="Jane Mary DOE: Treasurer of A CLUB TRUST (Past; disqualified as the register states it: False)",
             row={"charity_key": "charities/CC9", "status": "Past", "disqualified": False})
BY_NAME["rule"] = "same-name"
BY_NAME_BANNED = dict(BY_NAME, ref="charities:charities/CC9/officer/8", row=dict(BY_NAME["row"], status="Removed as Disqualified", disqualified=True),
                      statement="Jane Mary DOE: Treasurer of A CLUB TRUST (Removed as Disqualified; disqualified as the register states it: True)")
READS = {"reads": [{"view": v} for v in ("companies", "directors", "society_officers", "charities", "charity_officers", "charity_returns")]}


def test_the_charity_flags_read_the_register_by_name_and_by_number():
    marks, roles = rule("charity_integrity_marks"), rule("charity_officer_roles")
    assert "CHARITIES_NOT_HELD" not in open(os.path.join(HERE, "rules.py"), encoding="utf-8").read()
    # a person: the rows carrying the person's name are near, so a mark on one is amber, never red
    f = marks(dict(report(societies=[BY_NAME_BANNED]), template=READS))
    assert f["status"] == "fired" and f["severity"] == "amber" and f["scope"] == "near" and BY_NAME_BANNED["ref"] in f["citations"], f
    assert "Removed as Disqualified" in f["text"] and "a namesake's until a rule confirms it" in f["text"]
    f = roles(dict(report(societies=[BY_NAME]), template=READS))
    assert f["status"] == "fired" and f["severity"] == "info" and "carry the person's name, near" in f["text"] and BY_NAME["ref"] in f["citations"]
    # nothing found under the person's name: clear, naming the register it was read in
    f = marks(dict(report(), template=READS))
    assert f["status"] == "clear" and any("pub.charity_officers" in x for x in f["sources_held"]), f
    assert roles(dict(report(), template=READS))["status"] == "clear"
    # a clear needs the name looked up: a holder's row is not looked up, a skipped view or rows past the limit are not read
    holder = it("companies:companies/1/shareholder/a", "shareholders", title="Jane Mary DOE")
    assert marks(dict(report(subject=holder), template=READS))["status"] == "blocked"
    skipped = dict(report(), template=READS)
    skipped["walk"] = dict(skipped["walk"], skipped=["charity_officers"])
    assert marks(skipped)["status"] == "blocked" and roles(skipped)["status"] == "blocked"
    left = dict(report(), template=READS)
    left["sections"][ORDER.index("societies")].update(omitted=4, omitted_views=["charity_officers"])
    assert marks(left)["status"] == "blocked"
    # a company: its charity by business number is confirmed, and a mark on an officer of it is red
    f = marks(dict(company(societies=[CHARITY, TRUSTEE, BANNED]), template=READS))
    assert f["status"] == "fired" and f["severity"] == "red" and f["citations"] == (BANNED["ref"],), f
    f = roles(dict(company(societies=[CHARITY, TRUSTEE]), template=READS))
    assert f["status"] == "fired" and "the company's charity by its business number" in f["text"] and "1 officer row(s) on it" in f["text"]
    assert CHARITY["ref"] in f["citations"]
    f = marks(dict(company(societies=[CHARITY, TRUSTEE]), template=READS))
    assert f["status"] == "blocked" and "carry no disqualified mark" in f["text"], "its directors' own charity rows are not read from a company"
    for r in (company(societies=[CHARITY, TRUSTEE, BANNED]), report(societies=[BY_NAME_BANNED])):
        for fn in (marks, roles):
            assert not CAUSE.search(fn(dict(r, template=READS))["text"])


def test_public_life_is_info_and_reads_only_confirmed_rows():
    seat = it("house:ge-2023/doe-jane/dunedin", "members", title="Jane DOE · electorate")
    assert rule("public_life")(report(public=[seat]))["severity"] == "info"
    assert rule("public_life")(report(identity=[dict(seat, grade="near")]))["status"] == "clear"


def test_the_subject_hub_fires_only_on_the_subjects_own_rows():
    r = report()
    r["hubs"] = [{"ref": SUBJECT["ref"], "title": "Jane Mary DOE", "kind": "professional-director", "text": "a professional director: 80 directorships"},
                 {"ref": "companies:companies/2/director/b", "title": "Other", "kind": "professional-director", "text": "x"}]
    f = rule("subject_hub")(r)
    assert f["status"] == "fired" and f["citations"] == (SUBJECT["ref"],)
    r["hubs"] = r["hubs"][1:]
    assert rule("subject_hub")(r)["status"] == "clear"


COMMON = {"group-standing", "hubs-met", "replaced-return"}


def test_the_common_rules_are_the_builders_and_not_copied_here():
    names = {f["rule"] for f in (r(report()) for r in R.RULES)}
    assert not names & (COMMON | {"identity"}), names & (COMMON | {"identity"})
    assert toml().get("common_rules", True), "the screen keeps the builder's common rules"
    assert R.flag is R.contract.flag and R.items is R.contract.items and R.all_items is R.contract.all_items
    src = inspect.getsource(R)
    assert not re.search(r"^def (flag|items|section|_all|group_standing|hubs_met|replaced_rows|identity)\(", src, re.M)


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
