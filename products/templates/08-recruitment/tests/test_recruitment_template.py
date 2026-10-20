"""The recruitment template on fixtures: it loads on the shape, names only
published views with their licences, runs its sections in the consultant's
order, and its rules keep the flag contract: a red only on the subject's
confirmed rows, amber on a namesake's, a blocked check where the registers
held cannot see, dates side by side and no word of cause, a revoked
prohibition never counted. Imports nothing of products.report (the one-way
test): the shape is reached through its command line, and the rules file is
loaded by path as the shape loads it."""
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


def rules_module():
    spec = importlib.util.spec_from_file_location("qv4_test_recruitment_rules", os.path.join(HERE, "rules.py"))
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
    assert "charities" in s["societies"]["not_held"] and {"insolvency", "courts"} <= set(s["gazette"]["not_held"])
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
        "gazette_company_notices": "organisation", "gazette_liquidations": "organisation"}


def it(ref, view, grade="confirmed", title="X", statement=None, dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False,
       kind=None):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": kind or KIND[view], "title": title, "statement": statement or f"{title}: a row",
            "dates": {"undated": dates == "undated", "text": dates}, "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1,
            "grade": grade, "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": [], "replaced_by": None}


SUBJECT = it("companies:companies/1/director/a", "directors", title="Jane Mary DOE", statement="Jane Mary DOE: DIRECTOR of ACME LIMITED",
             dates="from 3 March 2011; no end filed (in the latest file)", row={"entity_key": "companies/1", "role_type": "DIRECTOR"})


def report(**sections):
    out = {"found": True, "as_of": "2026-10-20", "subject": SUBJECT, "members": [], "flags": [], "hubs": [],
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


def test_charity_checks_say_the_charities_register_is_not_held():
    clear = rule("charity_officer_roles")(report())
    assert clear["status"] == "clear" and any("Charities" in x for x in clear["sources_not_held"])
    off = it("societies:societies/9/officer/1", "society_officers", statement="Jane DOE: officer of A CLUB INCORPORATED (Active)", via="societies:societies/9")
    assert rule("charity_officer_roles")(report(societies=[off]))["status"] == "fired"
    assert rule("charity_integrity_marks")(report())["status"] == "blocked"
    assert rule("comcom_coverage")(report())["status"] == "blocked"


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


def test_identity_is_amber_on_a_contested_group_and_blocked_with_no_links():
    r = report()
    r["group"].update(contested=True, size=12)
    assert rule("identity")(r)["severity"] == "amber"
    r["group"] = {"built": False}
    assert rule("identity")(r)["status"] == "blocked"


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
