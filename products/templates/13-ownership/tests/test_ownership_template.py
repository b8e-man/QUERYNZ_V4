"""The beneficial ownership and AML checks on fixtures: the template loads on
the shape, names only published views with their licences, runs its sections
in the order a compliance analyst reads them, and its rules keep the flag
contract: the sanctions check and the question of for whom shares are held
are blocked and never clear; the chain names each company holder with its
shares and files and stops there; a nominee, trustee or custodian is a
holder of record and nothing more; a namesake company's holders are not the
entity's; from a company the people are not followed, so no check on them
clears; a suppressed name is never read; no word of cause or of ownership.
A mutant check breaks the rules file on purpose, fifteen ways, and requires
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
ORDER = ["identity", "holders", "chain", "officers", "gazette", "exposure", "charities", "not-held"]
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
    assert "followed up the chain in the next section" in s["holders"]["text"] and "never added" in s["holders"]["text"]
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


def test_it_reads_the_charities_register_in_a_section_of_its_own():
    """Card the-ownership-template-can-now-read-the-charities-register-and-the-reaches (the charities half): the three views read with
    their licence, in a charities section before what is not held (a company's charity by business number, `roles`; a person's
    officer rows by name, `named`), and `charities` out of every not-held line and out of the not-held text."""
    t = toml()
    reads = {r["view"]: r for r in t["reads"]}
    for v in ("charities", "charity_officers", "charity_returns"):
        assert "Charities Register open data" in reads[v]["licence"] and reads[v]["attribution"].startswith("Charities Services")
    s = {x["name"]: x for x in t["sections"]}
    assert s["charities"]["views"] == ["charities", "charity_officers", "charity_returns"] and s["charities"]["sources"][:2] == ["named", "roles"]
    assert "never added across returns" in s["charities"]["text"] and not CAUSE.search(s["charities"]["text"] + s["charities"]["heading"])
    assert not any("charities" in x.get("not_held", []) for x in t["sections"]) and "charities" not in s["not-held"]["text"]


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
ACC = holder("a", "ACCIDENT COMPENSATION CORPORATION", kind="company", shares=2466123)
RSA = holder("r", "Gore District Memorial RSA Inc", kind="company", shares=10)
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


#: the chain above ACME: DOE HOLDINGS LIMITED by its business number (confirmed, 1 up), its holder of record a nominee and its director;
#: above it KAHU CAPITAL LIMITED by a name one company carries (near, 2 up, where the chain goes on), a receivership on it; and a holder
#: the chain could not place
NEAR_BY_NAME = ("the holder of record is matched to its own register row by name only (1 company carries the name; the file gives no business "
                "number for a holder): near, never confirmed")
UP1 = dict(it("companies:companies/21", "companies", title="DOE HOLDINGS LIMITED", via=HOLDCO["ref"], row={"key": "companies/21", "status": "Registered"}),
           depth=1, rule="chain", hop_text="holds 400 shares of record in ACME TRADING LIMITED, as filed (undated)")
UP1_HOLDER = dict(holder("u", "KAHU CAPITAL LIMITED", kind="company", shares=1000, via=UP1["ref"]), depth=1, rule="chain")
UP1_NOMINEE = dict(holder("v", "CUSTODIAL SERVICES NOMINEES LIMITED", kind="company", shares=5, via=UP1["ref"]), depth=1, rule="chain")
UP1_DIRECTOR = dict(it("companies:companies/21/director/a", "directors", title="Jane Mary DOE", via=UP1["ref"], row={"in_latest": True}),
                    above=True, depth=1, through=UP1["ref"])
UP2 = dict(it("companies:companies/22", "companies", grade="near", title="KAHU CAPITAL LIMITED", via=UP1_HOLDER["ref"], reason=NEAR_BY_NAME,
              row={"key": "companies/22", "status": "In Receivership"}), depth=2, rule="chain", chain_goes_on=True,
           hop_text="holds 1,000 shares of record in DOE HOLDINGS LIMITED, as filed (undated)")
UP2_REC = dict(it("gazette:gazette/2025-ar1/company/22", "gazette_company_notices", grade="near", title="KAHU CAPITAL LIMITED · receivership",
                  dates="appointed 2 February 2025", via=UP2["ref"], reason=NEAR_BY_NAME, row={"kind": "receivership", "register_key": "companies/22"}),
               above=True, depth=2, through=UP2["ref"])
CHAIN_NOTE = {"text": "SOUTHERN TRUST: not followed; no company of this name in the register (an overseas company, a trust or a body of another kind)",
              "via": "companies:companies/21/shareholder/w", "depth": 2}
CHAIN = [UP1, UP1_HOLDER, UP1_NOMINEE, UP1_DIRECTOR, UP2, UP2_REC]


def report(subject=PERSON, hubs=(), omitted=None, chain_depth=0, chain_notes=(), **sections):
    out = {"found": True, "as_of": "2026-10-21", "subject": subject, "members": [], "flags": [], "hubs": list(hubs),
           "group": {"built": True, "size": 1, "contested": False, "omitted": 0},
           "walk": {"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0, "chain_depth": chain_depth,
                    "chain_notes": list(chain_notes), "chain": {"depth": 2 if chain_depth else 0, "cut": 1 if chain_depth else 0}}, "sections": []}
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
    # the chain above: the holder's rows, never the company's own
    up = company(holders=[JANE, HOLDCO], chain=CHAIN, chain_depth=2, chain_notes=[CHAIN_NOTE])
    if rl("insolvency_notices")(up)["severity"] == "red" or UP2_REC["ref"] not in rl("insolvency_notices")(up)["citations"]:
        bad.append("a receivership on a company two up the chain was the company's own, or went unsaid")
    conf_up = company(holders=[JANE, HOLDCO], chain=[UP1, dict(UP2_REC, grade="confirmed", reason=None, depth=1, via=UP1["ref"])], chain_depth=2)
    if rl("insolvency_notices")(conf_up)["severity"] == "red":
        bad.append("a confirmed notice on the company one up the chain was red: it is the holder's, not the company's")
    if "goes on" not in rl("holding_chain")(up)["text"]:
        bad.append("a chain cut at its depth did not say it goes on")
    if UP1_NOMINEE["ref"] not in rl("custodial_holders")(up)["citations"]:
        bad.append("a nominee holding shares of record a company up the chain was not read")
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
    short = person(holders=[BETA, dict(CO_HOLDER, row=dict(CO_HOLDER["row"], name="BETA HOLDINGS LIMITED"))])
    short["walk"]["entities_omitted"] = 111
    if rl("custodial_holders")(short)["status"] == "clear":
        bad.append("custodial-holders cleared a walk that stopped before its companies' holders were read")
    unread = person()
    unread["walk"]["links_omitted"] = 177
    if rl("political_money")(unread)["status"] == "clear":
        bad.append("political-money cleared with links unread past the walk's limit")
    if rl("partnership_holders")(full)["status"] != "fired" or LP["ref"] not in rl("partnership_holders")(full)["citations"]:
        bad.append("a limited partnership holder was not flagged")
    if rl("overseas_holders")(full)["status"] != "fired" or OFFSHORE["ref"] not in rl("overseas_holders")(full)["citations"]:
        bad.append("an overseas holder was not flagged")
    if rl("overseas_holders")(company(holders=[ACC, RSA]))["status"] == "fired":
        bad.append("a New Zealand statutory corporation was flagged as overseas")
    if rl("prohibition")(report(gazette=[dict(PROHIB, grade="near")]))["severity"] == "red":
        bad.append("a namesake's prohibition is red")
    if rl("prohibition")(report(gazette=[dict(PROHIB, suppressed=True)]))["status"] == "fired":
        bad.append("a revoked prohibition was counted")
    if rl("public_office")(company(exposure=[DECLARED]))["status"] != "fired":
        bad.append("a member's declared interest naming the company did not fire public-office")
    if rl("political_money")(company(identity=[dict(DONATION, grade="near")]))["status"] == "clear":
        bad.append("political-money cleared a company with a donation filed under its name, near")
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
    ("a notice above is the company's own", "if _insolvency(it) and _on_subject(report, it) and not it.get(\"above\")]",
     "if _insolvency(it) and (_on_subject(report, it) or it.get(\"above\"))]"),
    ("a notice above goes unsaid", "        up = [it for it in _chain(report) if it[\"view\"] in INSOLVENCY_VIEWS and _insolvency(it)]", "        up = []"),
    ("a nominee up the chain is not read", "    hit = [it for it in holders + _chain_holders(report) if CUSTODIAL", "    hit = [it for it in holders if CUSTODIAL"),
    ("a cut chain does not say it goes on", "    if cut:\n        bits.append(f\"the chain goes on", "    if False:\n        bits.append(f\"the chain goes on"),
    ("a namesake company's holders are the entity's", "return [it for it in rows if _on_subject(report, it)]", "return rows"),
    ("an empty holder list clears", '    if not holders:\n        return flag("holding-chain"', '    if False:\n        return flag("holding-chain"'),
    ("holders past the limit clear", '    if omitted:\n        return flag("holding-chain"', '    if False:\n        return flag("holding-chain"'),
    ("a nominee is called an owner", 'custodian: each is shown as a holder of record, "', 'custodian: each is the owner, "'),
    ("a suppressed name is read", 'return "" if it.get("suppressed") else (it["row"].get("name") or "")', 'return it["row"].get("name") or ""'),
    ("a prohibition clears from a company", '    if _company_start(report):\n        return flag("prohibition"', '    if False:\n        return flag("prohibition"'),
    ("a namesake's prohibition is red", 'return flag("prohibition", V, "fired", "amber",', 'return flag("prohibition", V, "fired", "red",'),
    ("public office clears from a company", '    if _company_start(report):\n        return flag("public-office"', '    if False:\n        return flag("public-office"'),
    ("near money clears", "    if near_money:\n        return flag(\"political-money\"", "    if False:\n        return flag(\"political-money\""),
    ("a short walk clears the custodial check", 'if section(report, "holders").get("omitted") or _walk_short(report):',
     'if section(report, "holders").get("omitted"):'),
    ("unread links clear the money", "    if (report.get(\"walk\") or {}).get(\"links_omitted\"):\n        return flag(\"political-money\"",
     "    if False:\n        return flag(\"political-money\""),
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
    assert "the depth limit is 4 hops" in f["text"] and "no fraction is computed" in f["text"]
    assert "The chain is not followed past the first hop (the template sets no chain depth)" in f["text"]
    import decimal
    dec = rule("holding_chain")(company(holders=[dict(HOLDCO, row=dict(HOLDCO["row"], shares=decimal.Decimal("1200")))]))
    assert "1,200 shares filed for the holding" in dec["text"], "the view's numeric column arrives as a Decimal"
    removed = dict(ACME, row=dict(ACME["row"], status="Removed"))
    b = rule("holding_chain")(report(subject=removed))
    assert b["status"] == "blocked" and "off the register" in b["text"]


def test_the_chain_above_is_followed_two_up_with_its_holders_directors_and_notices_the_holders_not_the_companys():
    """Card the-ownership-template-can-now-read-the-charities-register-and-the-reaches (the companies above): chain_depth 2 and a chain
    section naming `chain` with the companies, holders, directors and Gazette views; holding-chain counts what was read up the chain;
    a notice above is the holder's, beside the company's own; a nominee two up is a holder of record up the chain."""
    t = toml()
    assert t["chain_depth"] == 2
    s = {x["name"]: x for x in t["sections"]}
    assert s["chain"]["sources"] == ["chain"] and set(s["chain"]["views"]) == {"companies", "shareholders", "directors", "gazette_liquidations",
                                                                              "gazette_company_notices"}
    assert not any("chain" in x.get("sources", []) for x in t["sections"] if x["name"] != "chain"), "a chain row is listed in one section"
    assert "never added or turned into a fraction" in s["chain"]["text"] and "the chain goes on" in s["chain"]["text"]
    assert not any("registers reach one" in x for x in t["limits"]) and "carries no business number in the file" not in s["holders"]["text"]
    r = company(holders=[JANE, HOLDCO], chain=CHAIN, chain_depth=2, chain_notes=[CHAIN_NOTE])
    f = rule("holding_chain")(r)
    assert f["status"] == "fired" and f["severity"] == "amber" and {UP1["ref"], UP2["ref"]} <= set(f["citations"])
    assert "Up the chain, followed 2 up: 2 company(ies) reached, 1 by business number (confirmed) and 1 by a name one company carries (near)" in f["text"]
    assert "DOE HOLDINGS LIMITED (1 up, confirmed; holds 400 shares of record in ACME TRADING LIMITED, as filed (undated))" in f["text"]
    assert "1 holder(s) not followed: SOUTHERN TRUST: not followed" in f["text"] and "the chain goes on past 2 up at 1 company(ies)" in f["text"]
    assert "on the companies above, 2 holder(s) of record, 1 current director(s) and 1 Gazette notice(s) are listed" in f["text"]
    n = rule("insolvency_notices")(r)
    assert (n["status"], n["severity"], n["scope"]) == ("fired", "amber", "chain") and "2 up, near" in n["text"] and UP2_REC["ref"] in n["citations"]
    both = rule("insolvency_notices")(company(holders=[JANE, HOLDCO], gazette=[LIQ], chain=CHAIN, chain_depth=2))
    assert both["severity"] == "red" and both["text"].startswith("1 Gazette insolvency notice(s) on the company") and "beside it, 1" in both["text"]
    c = rule("custodial_holders")(r)
    assert c["status"] == "fired" and "on the company or up its holding chain" in c["text"] and "on a company 1 up the chain, confirmed" in c["text"]
    assert UP1_NOMINEE["ref"] in c["citations"]
    clear = rule("insolvency_notices")(company(holders=[JANE, HOLDCO], chain=[UP1, UP1_HOLDER], chain_depth=2))
    assert clear["status"] == "clear" and "the companies the chain reaches above were read too" in clear["text"]


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
    n = rule("political_money")(company(identity=[dict(DONATION, grade="near")]))
    assert n["status"] == "fired" and n["scope"] == "near" and "never a number" in n["text"]
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
