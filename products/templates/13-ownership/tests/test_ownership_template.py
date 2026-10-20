"""The beneficial ownership and AML checks on fixtures: the template loads on
the shape, names only published views with their licences, runs its sections
in the order a compliance analyst reads them, and its rules keep the flag
contract: the sanctions check and the question of for whom shares are held
are blocked and never clear; the chain names each company holder with its
shares and files and stops there; a nominee, trustee or custodian is a
holder of record and nothing more; a namesake company's holders are not the
entity's; from a company the people are not followed, so no check on them
clears; a suppressed name is never read; no word of cause or of ownership.
A mutant check breaks the rules file on purpose, twelve ways, and requires
these properties to catch every break.

Imports nothing of products.report (the one-way test): the shape is reached
through its command line, and the rules file is loaded by path as the shape
loads it, with the name `contract` bound to the shape's contract file
(products/report/contract.py, read by path) before it runs."""
import importlib.util
import os
import re
import subprocess
import sys
import tomllib

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ORDER = ["identity", "holders", "officers", "gazette", "exposure", "not-held"]
COMMON = ("group-standing", "hubs-met", "replaced-return")
#: words that would join two facts as cause, or call a holder of record more than that (the shape's rules 3 and 4 hold the full list)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|controlled|behind|"
                   r"owners?|owns|owned|ownership|beneficial|beneficiary|ultimately)\b", re.I)
NEVER_CLEAR = ("sanctions_lists", "ultimate_holders", "holder_hubs", "bankruptcy", "securities_register")
PEOPLE_CHECKS = ("prohibition", "public_office")


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


CONTRACT = by_path("qv4_test_report_contract_ownership", os.path.join(REPO, "products", "report", "contract.py"))


def rules_module(source: str = None):
    if source is None:
        return by_path("qv4_test_ownership_rules", os.path.join(HERE, "rules.py"), contract=CONTRACT)
    mod = type(sys)("qv4_test_ownership_mutant")
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
    line = [x for x in out.stdout.splitlines() if x.startswith("ownership ")]
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
    for unreached in ("gazette_appointments", "gazette_practitioners"):
        assert unreached not in views, "no link reaches it: reading it would print a blank that is not a clear"
    assert {"shareholders", "directors", "companies", "members", "mp_interests"} <= set(views)


def test_its_sections_run_in_the_compliance_analysts_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"] and "companies" not in s["identity"]["views"], \
        "an entity goes to the first section naming its view whatever the section's buckets: the companies head the holders"
    assert s["holders"]["views"] == ["companies", "shareholders"] and "roles" in s["holders"]["sources"]
    assert "depth limit is four hops" in s["holders"]["text"] and "never added" in s["holders"]["text"]
    assert "nominee, trustee or custodian" in s["holders"]["text"] and "holder of record" in s["holders"]["text"]
    assert "pointing" in s["gazette"]["sources"] and "insolvency" in s["gazette"]["not_held"]
    assert {"members", "mp_interests", "party_return_donors"} <= set(s["exposure"]["views"])
    assert {"sanctions", "limited_partnerships", "securities"} <= set(s["not-held"]["not_held"]) and s["not-held"]["views"] == []
    for named in ("sanctions lists", "limited partnerships register", "overseas company registers", "trusts", "Personal Property Securities Register"):
        assert named in s["not-held"]["text"], named
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views
        assert not CAUSE.search(x["text"]) and not CAUSE.search(x["heading"]), (x["name"], CAUSE.search(x["text"] + x["heading"]))


def test_the_known_limits_page_and_the_checkpoint_list_exist():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    assert "namesake" in page and "not a clear" in page and "checkpoint" in page.lower() and "sanctions" in page.lower()
    lim = toml()["limits"]
    assert any("first hop" in x for x in lim) and any("never clear" in x for x in lim) and any("Sanctions" in x for x in lim)
    with open(os.path.join(HERE, "checkpoint.list"), encoding="utf-8") as f:
        keys = [x.strip() for x in f if x.strip() and not x.startswith("#")]
    assert len(keys) == 12 and len(set(keys)) == 12 and all(re.match(r"^[a-z_]+:\S+$", k) for k in keys), "twelve register keys, one a line"


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "gazette_prohibitions": "person", "gazette_bankruptcies": "person",
        "members": "person", "candidates": "person", "companies": "organisation", "company_addresses": "place",
        "gazette_company_notices": "organisation", "gazette_liquidations": "organisation", "party_return_donors": "figure", "mp_interests": "figure"}
THROUGH = "a connection that passes through more than one person is listed as near, never confirmed (the design's default)"
FILES = "undated; in the files from companies-2026-07 to companies-2026-08"


def it(ref, view, grade="confirmed", title="X", dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False, flags=()):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": KIND[view], "title": title, "statement": f"{title}: a row",
            "dates": {"undated": dates.startswith("undated"), "text": dates}, "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1,
            "grade": grade, "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": list(flags), "replaced_by": None, "entity_title": None}


ACME = it("companies:companies/1", "companies", title="ACME TRADING LIMITED", dates="from 3 March 2011; no end filed (in the latest file)",
          row={"key": "companies/1", "name": "ACME TRADING LIMITED", "status": "Registered", "entity_type": "LTD", "registered_on": "2011-03-03",
               "in_latest": True})


def holder(n, name, kind="individual", shares=100, via="companies:companies/1", **kw):
    key = via.split(":", 1)[1]
    return it(f"companies:{key}/shareholder/{n}", "shareholders", title=name, dates=FILES, via=via,
              row={"entity_key": key, "name": name, "shareholder_type": kind, "shares": shares, "in_latest": True}, **kw)


JANE = holder("j", "Jane Mary DOE", shares=500)
HOLDCO = holder("h", "DOE HOLDINGS LIMITED", kind="company", shares=400)
NOMINEE = holder("n", "ACME NOMINEES LIMITED", kind="company", shares=100,
                 flags=[{"kind": "nominee", "text": "a nominee or trustee holder", "evidence": "ACME NOMINEES LIMITED"}])
TRUSTEE = holder("t", "SMITH FAMILY TRUSTEE COMPANY LIMITED", kind="company", shares=50)
LP = holder("p", "KAURI GROWTH FUND LIMITED PARTNERSHIP", kind="company", shares=10)
OFFSHORE = holder("o", "SOUTHERN CROSS INVESTMENTS PTY LTD", kind="company", shares=10)
HIDDEN = dict(holder("s", "SECRET NOMINEES LIMITED", kind="company", shares=5, suppressed=True), title="name suppressed")
DIRECTOR = it("companies:companies/1/director/d", "directors", title="Jane Mary DOE", via=ACME["ref"],
              row={"entity_key": "companies/1", "role_type": "DIRECTOR", "appointed_on": "2011-03-03", "in_latest": True})
LIQ = it("gazette:gazette/2020-al1/company/1", "gazette_liquidations", title="ACME TRADING LIMITED", dates="appointed 13 July 2020",
         row={"register_key": "companies/1", "appointed_on": "2020-07-13"}, via=ACME["ref"])
TWIN = it("companies:companies/2", "companies", grade="near", title="ACME TRADING (2019) LIMITED", reason="the two companies share a name",
          row={"key": "companies/2", "status": "Registered", "registered_on": "2019-01-01", "in_latest": True})
TWIN_HOLDER = dict(holder("x", "OTHER HOLDINGS LIMITED", kind="company", via=TWIN["ref"]), grade="near", reason="reached through a near link")
PERSON = it("companies:companies/9/director/a", "directors", title="Jane Mary DOE",
            row={"entity_key": "companies/9", "role_type": "DIRECTOR", "appointed_on": "2015-01-01", "in_latest": True})
BETA = it("companies:companies/9", "companies", title="BETA LIMITED", row={"key": "companies/9", "status": "Registered", "registered_on": "2015-01-01"})
CO_HOLDER = dict(holder("c", "BETA NOMINEES LIMITED", kind="company", via=BETA["ref"]), grade="near", reason=THROUGH)
MEMBER = it("house:members/1", "members", title="Jane DOE · list", row={"display_name": "Jane DOE"})
NEAR_MEMBER = dict(MEMBER, ref="house:members/2", grade="near")
DECLARED = it("mp_interests:return/1/3", "mp_interests", title="Company directorships · John SMITH", via=ACME["ref"], row={"heading": "x"})
PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", title="Jane Mary Doe · prohibition",
            dates="from 22 September 2022; to 22 September 2027", row={"ends_on": "2027-09-22"})
DONATION = it("party_returns:abc/A/1", "party_return_donors", title="ACME TRADING LIMITED · $5,000", row={"donor": "ACME TRADING LIMITED"})


def report(subject=PERSON, hubs=(), omitted=None, **sections):
    out = {"found": True, "as_of": "2026-10-21", "subject": subject, "members": [], "flags": [], "hubs": list(hubs),
           "group": {"built": True, "size": 1, "contested": False, "omitted": 0},
           "walk": {"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0}, "sections": []}
    for name in ORDER:
        rows = sections.get(name.replace("-", "_"), [])
        out["sections"].append({"name": name, "heading": name, "items": rows, "omitted": (omitted or {}).get(name, 0),
                                "blank": None if rows else "none found"})
    return out


def company(**sections):
    return report(subject=dict(ACME, via=None), **sections)


def person(**sections):
    return report(holders=sections.pop("holders", [BETA, CO_HOLDER]), **sections)


def flags_of(mod, r):
    return [fn(r) for fn in mod.RULES]


# ── the properties, each a list of what broke (empty when they hold) ────────

def properties(mod) -> list:
    """What a compliance analyst relies on, checked on fixtures; the mutant
    check runs it on each broken copy of the rules and needs it to say something."""
    bad = []
    rl = lambda n: rule(n, mod)   # noqa: E731
    full = company(holders=[ACME, JANE, HOLDCO, NOMINEE, TRUSTEE, LP, OFFSHORE, HIDDEN, TWIN, TWIN_HOLDER], officers=[DIRECTOR], gazette=[LIQ])
    starts = {"company": full, "bare company": company(), "person": person(),
              "other": report(subject=it("party_returns:x/A/1", "party_return_donors", title="ACME TRADING LTD · $5,000")), "empty": report()}
    for start, r in starts.items():
        for f in flags_of(mod, r):
            if CAUSE.search(f["text"]):
                bad.append(f"{start}: {f['rule']} says a word of cause or ownership: {CAUSE.search(f['text']).group(0)!r} in {f['text'][:100]}")
            if "SECRET" in f["text"] or (HIDDEN["ref"] in f["citations"] and f["rule"] != "holding-chain"):
                bad.append(f"{start}: {f['rule']} read a suppressed name (the row stays, and only the chain cites it, by its row)")
        for name in NEVER_CLEAR:
            if rl(name)(r)["status"] == "clear":
                bad.append(f"{start}: {name} cleared: nothing held can clear it")
        if rl("sanctions_lists")(r)["status"] != "blocked":
            bad.append(f"{start}: sanctions-lists did not block: no list is held")
    for name in PEOPLE_CHECKS:
        if rl(name)(company(holders=[JANE], officers=[DIRECTOR]))["status"] == "clear":
            bad.append(f"company start: {name} cleared the people it never followed")
    chain = rl("holding_chain")(full)
    if chain["status"] != "fired" or HOLDCO["ref"] not in chain["citations"] or "400 shares" not in chain["text"]:
        bad.append("holding-chain did not name the company holder with its shares")
    if TWIN_HOLDER["ref"] in chain["citations"]:
        bad.append("holding-chain counted a namesake company's holder as the entity's")
    if JANE["ref"] in chain["citations"]:
        bad.append("holding-chain named an individual as a company holder")
    if rl("holding_chain")(company(holders=[JANE]))["status"] != "clear":
        bad.append("holding-chain did not clear a company whose every holder is an individual")
    if rl("holding_chain")(company())["status"] == "clear":
        bad.append("holding-chain cleared a company with no holder listed: an empty list is not a finding")
    if rl("holding_chain")(report(subject=dict(ACME, via=None), omitted={"holders": 3}, holders=[JANE]))["status"] == "clear":
        bad.append("holding-chain cleared with holder rows past the walk's limit")
    if rl("holding_chain")(person())["status"] == "clear":
        bad.append("holding-chain cleared from a person: the chain is read from a company")
    cust = rl("custodial_holders")(full)
    if cust["status"] != "fired" or not {NOMINEE["ref"], TRUSTEE["ref"]} <= set(cust["citations"]) or "holder of record" not in cust["text"]:
        bad.append("a nominee or trustee holder was not shown as a holder of record")
    if JANE["ref"] in cust["citations"] or HOLDCO["ref"] in cust["citations"]:
        bad.append("custodial-holders named a holder its name does not mark")
    if rl("partnership_holders")(full)["status"] != "fired" or LP["ref"] not in rl("partnership_holders")(full)["citations"]:
        bad.append("a limited partnership holder was not flagged")
    if rl("overseas_holders")(full)["status"] != "fired" or OFFSHORE["ref"] not in rl("overseas_holders")(full)["citations"]:
        bad.append("an overseas holder was not flagged")
    if rl("prohibition")(report(gazette=[dict(PROHIB, grade="near")]))["severity"] == "red":
        bad.append("a namesake's prohibition is red")
    if rl("prohibition")(report(gazette=[dict(PROHIB, suppressed=True)]))["status"] == "fired":
        bad.append("a revoked prohibition was counted")
    if rl("public_office")(company(exposure=[DECLARED]))["status"] != "fired":
        bad.append("a member's declared interest naming the company did not fire public-office")
    if rl("public_office")(report(identity=[NEAR_MEMBER]))["severity"] != "info":
        bad.append("a namesake's seat is more than info")
    return bad


def test_the_properties_hold_on_the_rules_as_written():
    assert properties(R) == []


#: (what the mutant breaks, the text replaced, its replacement): each must be unique in rules.py and caught by properties()
MUTANTS = (
    ("the sanctions check clears", 'return flag("sanctions-lists", V, "blocked", "red",',
     'return flag("sanctions-lists", V, "clear", "red", sources_held=("pub.links",), text='),
    ("the holders of record are taken for the people held for", 'return flag("ultimate-holders", V, "blocked", "red", f"{counted}.',
     'return flag("ultimate-holders", V, "clear", "red", sources_held=("pub.shareholders",), text=f"{counted}.'),
    ("a company holder is not seen", "companies = [it for it in holders if _is_company_holder(it)]", "companies = []"),
    ("a namesake company's holders are the entity's", "return [it for it in rows if _on_subject(report, it)]", "return rows"),
    ("an empty holder list clears", '    if not holders:\n        return flag("holding-chain"', '    if False:\n        return flag("holding-chain"'),
    ("holders past the limit clear", '    if omitted:\n        return flag("holding-chain"', '    if False:\n        return flag("holding-chain"'),
    ("a nominee is called an owner", 'custodian: each is shown as a holder of record, "', 'custodian: each is the owner, "'),
    ("a suppressed name is read", 'return "" if it.get("suppressed") else (it["row"].get("name") or "")', 'return it["row"].get("name") or ""'),
    ("a prohibition clears from a company", '    if _company_start(report):\n        return flag("prohibition"', '    if False:\n        return flag("prohibition"'),
    ("a namesake's prohibition is red", 'return flag("prohibition", V, "fired", "amber",', 'return flag("prohibition", V, "fired", "red",'),
    ("public office clears from a company", '    if _company_start(report):\n        return flag("public-office"', '    if False:\n        return flag("public-office"'),
    ("a hub-free holder list clears", 'return flag("holder-hubs", V, "blocked", "info", "no holder',
     'return flag("holder-hubs", V, "clear", "info", sources_held=("pub.shareholders",), text="no holder'),
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
    for r in (report(), person(), company(), company(holders=[JANE, HOLDCO], officers=[DIRECTOR], gazette=[LIQ]),
              report(subject=it("party_returns:x/A/1", "party_return_donors"))):
        flags = flags_of(R, r)
        assert len({f["rule"] for f in flags}) == len(flags) == len(R.RULES)
        assert not {f["rule"] for f in flags} & set(COMMON), "the builder runs the common rules; no copy here"
    assert R.flag is CONTRACT.flag and R.items is CONTRACT.items and R.section is CONTRACT.section and R.all_items is CONTRACT.all_items
    assert "common_rules" not in toml(), "the template keeps the builder's common rules"


def test_the_chain_names_each_first_hop_with_its_shares_files_and_depth_limit():
    f = rule("holding_chain")(company(holders=[JANE, HOLDCO, NOMINEE]))
    assert f["status"] == "fired" and f["severity"] == "amber" and f["scope"] == "entity"
    assert set(f["citations"]) == {HOLDCO["ref"], NOMINEE["ref"]} and "2 of the 3 holder(s) of record are companies" in f["text"]
    assert "DOE HOLDINGS LIMITED: 400 shares filed for the holding (undated; in the files from companies-2026-07" in f["text"]
    assert "the depth limit is 4 hops and the registers reach 1" in f["text"] and "no fraction is computed" in f["text"]
    removed = dict(ACME, row=dict(ACME["row"], status="Removed"))
    b = rule("holding_chain")(report(subject=removed))
    assert b["status"] == "blocked" and "off the register" in b["text"]


def test_for_whom_shares_are_held_is_always_blocked_and_counts_what_was_read():
    f = rule("ultimate_holders")(company(holders=[JANE, HOLDCO, TRUSTEE]))
    assert f["status"] == "blocked" and f["severity"] == "red"
    assert "3 holder(s) of record listed: 1 filed as individuals, 2 as companies, 1 named as a nominee, trustee or custodian" in f["text"]
    assert any("register of trusts" in x for x in f["sources_not_held"])
    assert rule("ultimate_holders")(person())["status"] == "blocked"


def test_a_custodial_holder_is_a_holder_of_record_amber_on_the_company_info_beside_a_person():
    f = rule("custodial_holders")(company(holders=[JANE, NOMINEE, TRUSTEE]))
    assert f["status"] == "fired" and f["severity"] == "amber" and set(f["citations"]) == {NOMINEE["ref"], TRUSTEE["ref"]}
    g = rule("custodial_holders")(person())
    assert g["status"] == "fired" and g["severity"] == "info" and g["citations"] == (CO_HOLDER["ref"],)
    assert rule("custodial_holders")(company(holders=[JANE]))["status"] == "clear"
    assert rule("custodial_holders")(company())["status"] == "blocked"


def test_sanctions_name_the_three_lists_and_count_the_names_a_screen_would_read():
    f = rule("sanctions_lists")(company(holders=[JANE, HOLDCO], officers=[DIRECTOR]))
    assert f["status"] == "blocked" and f["severity"] == "red" and len(f["sources_not_held"]) == 3
    assert "4 name(s) on this report" in f["text"], "the company, two holders and a director"
    assert "Russia Sanctions Act" in f["text"] and "United Nations" in f["text"] and "Terrorism Suppression Act" in f["text"]


def test_public_office_a_seat_is_amber_a_declaration_naming_the_company_fires_and_a_company_start_blocks():
    assert rule("public_office")(person(exposure=[MEMBER]))["status"] == "fired"
    assert rule("public_office")(person(exposure=[MEMBER]))["severity"] == "amber"
    d = rule("public_office")(company(exposure=[DECLARED]))
    assert d["status"] == "fired" and "declared interest(s) name the company" in d["text"]
    assert rule("public_office")(company())["status"] == "blocked"
    assert rule("public_office")(person())["status"] == "clear"


def test_political_money_is_the_companys_own_from_a_company():
    f = rule("political_money")(company(exposure=[DONATION]))
    assert f["status"] == "fired" and f["citations"] == (DONATION["ref"],)
    c = rule("political_money")(company())
    assert c["status"] == "clear" and "directors' and holders' are not read" in c["text"]


def test_the_company_its_status_and_its_notices_with_their_own_dates():
    liq = dict(ACME, row=dict(ACME["row"], status="In Liquidation"))
    assert rule("company_status")(report(subject=liq))["severity"] == "red"
    assert rule("company_status")(company())["status"] == "clear"
    f = rule("insolvency_notices")(company(gazette=[LIQ]))
    assert f["status"] == "fired" and "appointed 13 July 2020" in f["text"]
    assert rule("insolvency_notices")(company())["status"] == "clear"
    assert rule("insolvency_notices")(person())["status"] == "blocked", "a person's past companies are not held: no clear"


def test_officers_of_record_fire_when_no_current_director_is_filed():
    assert rule("officers_of_record")(company())["status"] == "fired"
    assert rule("officers_of_record")(company(officers=[DIRECTOR]))["status"] == "clear"


def test_a_holder_hub_fires_on_the_walks_flag_and_otherwise_blocks():
    assert rule("holder_hubs")(company(holders=[NOMINEE]))["status"] == "fired"
    assert rule("holder_hubs")(company(holders=[JANE]))["status"] == "blocked"


def test_the_subject_named_as_a_trustee_is_a_hub():
    trustee = dict(ACME, row=dict(ACME["row"], name="KAURI TRUSTEES LIMITED"), title="KAURI TRUSTEES LIMITED")
    assert rule("subject_hub")(report(subject=trustee))["status"] == "fired"
    assert rule("subject_hub")(company())["status"] == "clear"


def test_the_presentation_rules_hold_on_a_fixture_report_with_its_flags():
    r = company(holders=[ACME, JANE, HOLDCO, NOMINEE], officers=[DIRECTOR], gazette=[LIQ])
    r["flags"] = flags_of(R, r)
    assert CONTRACT.presentation_problems(r) == []


def test_the_rules_file_imports_nothing_of_the_shape():
    with open(os.path.join(HERE, "rules.py"), encoding="utf-8") as f:
        src = f.read()
    assert not re.search(r"^\s*(from|import)\s+products", src, re.M)
