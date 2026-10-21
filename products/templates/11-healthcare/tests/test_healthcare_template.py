"""Healthcare operator governance on fixtures: it loads on the shape, names
only published views with their licences, runs its sections in the order an
investor reads them, and its rules keep the flag contract: an officer's
other roles are dated beside the officer's role on the entity, a care-named
organisation that does not carry the entity's own leading name word raises
the overlap amber and a hub's never does; a prohibition on a current
officer's record (the group not contested, the prohibition in force) is red
and anything weaker amber; a notice on an officer's other company is amber,
never red; a modified audit opinion on a confirmed charity's newest return
is red; a return missing for the charity's last period fires; every charity
check blocks while the template does not read the charities register; a
start that lists no officer (a charitable trust board, a village row) and
a walk that left officers unfollowed block every officer check, never
clear; every register not held blocks; dates side by side, no word of cause
or ownership, no address and no suppressed name in a flag. A mutant check
breaks the rules file on purpose, eighteen ways, and requires these
properties to catch every break.

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
ORDER = ["identity", "standing", "governance", "charity-returns", "overlap", "gazette", "not-held"]
COMMON = ("group-standing", "hubs-met", "replaced-return")
VIEWS = {"companies", "company_states", "directors", "shareholders", "company_addresses", "societies", "society_officers",
         "gazette_liquidations", "gazette_liquidators", "gazette_company_notices", "gazette_appointments", "gazette_prohibitions",
         "gazette_bankruptcies"}
CHARITY_VIEWS = ("charities", "charity_officers", "charity_returns")
#: words that would join two facts as cause or call a holder an owner (the shape's rules 3 and 4 hold the full list on every report)
CAUSE = re.compile(r"\b(because|therefore|due to|as a result|led to|linked to|connected to|associated with|controls?|behind|owners?|owns|owned|"
                   r"beneficial)\b", re.I)
OFFICER_CHECKS = ("disqualified_officer", "officer_bankruptcy", "officer_overlap", "officer_company_notices")
CHARITY_CHECKS = ("charity_arm", "charity_returns_summary", "charity_audit_opinion", "charity_return_filed")
ALWAYS_BLOCKED = ("retirement_villages", "hdc_decisions", "certification_audits", "provider_registers", "aged_care_commissioner",
                  "court_judgments", "past_roles")


def toml():
    with open(os.path.join(HERE, "template.toml"), "rb") as f:
        return tomllib.load(f)


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


CONTRACT = by_path("qv4_test_report_contract_healthcare", os.path.join(REPO, "products", "report", "contract.py"))


def rules_module(source: str = None):
    """As the shape's loader does: `contract` bound, then the file run; a
    mutant's source is run the same way."""
    if source is None:
        return by_path("qv4_test_healthcare_rules", os.path.join(HERE, "rules.py"), contract=CONTRACT)
    mod = type(sys)("qv4_test_healthcare_mutant")
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
    line = [x for x in out.stdout.splitlines() if x.startswith("healthcare ")]
    assert line and HERE in line[0], out.stdout
    t = toml()
    assert f"{len(t['reads'])} views, {len(t['sections'])} sections, {len(R.RULES)} rules" in line[0]


def test_it_names_only_the_views_the_brief_names_each_once_with_its_licence():
    t = toml()
    views = [r["view"] for r in t["reads"]]
    assert len(views) == len(set(views)) and set(views) == VIEWS | set(CHARITY_VIEWS) and t["depth"] == 2 and t["chain_depth"] == 2
    assert all(r.get("licence") and r.get("attribution") and r.get("refresh") for r in t["reads"])
    assert "registered offices only, never a residential address" in [r for r in t["reads"] if r["view"] == "company_addresses"][0]["licence"]
    for v in CHARITY_VIEWS:
        assert "Charities Register open data" in [r for r in t["reads"] if r["view"] == v][0]["licence"], v
    src = open(os.path.join(HERE, "template.toml"), encoding="utf-8").read()
    for card in ("charity-officers-are-in-no-link-and-no-name-row", "the-not-held-list-has-no-key-for-the-health-registers"):
        assert card in src, card
    assert "14 August 2026" in src and "512" in src and "register retirement_village" in src


def test_its_sections_run_in_the_investors_order():
    t = toml()
    assert [s["name"] for s in t["sections"]] == ORDER
    s = {x["name"]: x for x in t["sections"]}
    assert s["identity"]["sources"] == ["near"] and s["identity"]["own"] is False, "a namesake is never the entity's own row"
    assert s["standing"]["own"] is True and set(s["standing"]["views"]) == {"company_states", "company_addresses"}
    assert "chain" in s["governance"]["sources"] and "charities" in s["governance"]["views"]
    assert s["charity-returns"]["views"] == ["charity_returns"]
    for named in ("period", "tier", "income", "expenditure", "surplus", "assets", "liabilities", "equity", "audited", "opinion", "newest first"):
        assert named in s["charity-returns"]["text"], named
    assert s["overlap"]["sources"] == ["officers", "second"]
    assert "officers" in s["gazette"]["sources"] and {"insolvency", "courts"} <= set(s["gazette"]["not_held"])
    assert "officers" not in {b for x in t["sections"] if x["name"] not in ("overlap", "gazette") for b in x.get("sources", [])}
    assert s["not-held"]["views"] == [] and "courts" in s["not-held"]["not_held"]
    for named in ("retirement villages file", "statutory supervisor", "Health and Disability Commissioner", "certification audits",
                  "Ministry of Health's provider registers", "Aged Care Commissioner", "court judgments"):
        assert named in s["not-held"]["text"], named
    views = {r["view"] for r in t["reads"]}
    for x in t["sections"]:
        assert set(x["views"]) <= views
        assert not CAUSE.search(x["text"]) and not CAUSE.search(x["heading"]), x["name"]


def test_the_known_limits_page_and_the_checkpoint_list_exist():
    with open(os.path.join(HERE, "limits.md"), encoding="utf-8") as f:
        page = f.read()
    for want in ("namesake", "not a clear", "checkpoint", "retirement villages file", "never clear", "charit", "Health and Disability Commissioner"):
        assert want in page, want
    lim = toml()["limits"]
    assert any("retirement villages file is not held" in x for x in lim) and any("Charities Register's officers" in x and "matched by name" in x for x in lim)
    with open(os.path.join(HERE, "checkpoint.list"), encoding="utf-8") as f:
        keys = [x.strip() for x in f if x.strip() and not x.startswith("#")]
    assert len(keys) == 12 and len(set(keys)) == 12 and all(re.match(r"^[a-z_]+:\S+$", k) for k in keys), "twelve register keys, one a line"


# ── fixtures ────────────────────────────────────────────────────────────────

KIND = {"directors": "person", "shareholders": "person", "society_officers": "person", "gazette_prohibitions": "person",
        "gazette_bankruptcies": "person", "gazette_liquidators": "person", "companies": "organisation", "societies": "organisation",
        "company_addresses": "place", "gazette_company_notices": "organisation", "gazette_liquidations": "organisation",
        "charities": "organisation", "charity_officers": "person", "charity_returns": "figure"}
THROUGH = "reached through a person on the subject ({who}): an officer's other role is the officer's connection, not the subject's; near, never confirmed"
CONTESTED = "the group this row belongs to is contested as a whole: the watch flagged it; "


def it(ref, view, grade="confirmed", title="X", dates="from 1 January 2020", row=None, via=None, reason=None, suppressed=False, entity_title=None,
       through=None, rule_=None):
    return {"ref": ref, "view": view, "register": ref.split(":", 1)[0], "kind": KIND[view], "title": title, "statement": f"{title}: a row",
            "dates": {"undated": dates == "undated", "text": dates}, "citation": {"view": view, "key": ref.split(":", 1)[1]}, "cite": 1,
            "grade": grade, "reason": reason if grade == "confirmed" else (reason or "the two rows share a first and last name"),
            "suppressed": suppressed, "row": row or {}, "via": via, "flags": [], "replaced_by": None, "entity_title": entity_title,
            "rule": rule_, **({"through": through} if through else {})}


def company(n, title, status="Registered", registered="2014-01-17", kind="LTD", **kw):
    return it(f"companies:companies/{n}", "companies", title=title, dates=f"from {registered}",
              row={"key": f"companies/{n}", "nzbn": str(n), "status": status, "entity_type": kind, "registered_on": registered, "in_latest": True}, **kw)


def director(n, letter, title, appointed, company_title, via=None, grade="confirmed", reason=None, through=None, in_latest=True, suppressed=False):
    return it(f"companies:companies/{n}/director/{letter}", "directors", grade=grade, title=title, dates=f"from {appointed}", via=via,
              row={"entity_key": f"companies/{n}", "role_type": "DIRECTOR", "appointed_on": appointed, "in_latest": in_latest},
              reason=reason, entity_title=company_title, through=through, rule_="through-officer" if through else None, suppressed=suppressed)


OPERATOR = company(1, "KOWHAI LIVING GROUP LIMITED")
TRUST_BOARD = company(9, "KOWHAI LIVING CHARITABLE TRUST", kind="Charitable Trust Boards", registered="2005-02-07")
VILLAGE = it("companies:companies/retirement_village/77", "companies", title="KOWHAI GARDENS VILLAGE",
             row={"key": "companies/retirement_village/77", "status": "REGISTERED", "entity_type": None, "registered_on": "2007-10-19", "in_latest": True})
#: the entity's officers: Ann on its board since 2025, Bob since 2019
ANN = director(1, "a", "Ann Mary ROE", "2025-02-01", OPERATOR["title"], via=OPERATOR["ref"])
BOB = director(1, "b", "Bob James LEE", "2019-06-01", OPERATOR["title"], via=OPERATOR["ref"])
#: Ann also sits on another operator (care-named, not the entity's leading word) and on a sister of the entity's own name
ANN_RIMU = director(2, "a", "Ann Mary ROE", "2018-12-13", "RIMU LIFECARE LIMITED", grade="near", reason=THROUGH.format(who="Ann Mary ROE"),
                    through=ANN["ref"], via=ANN["ref"])
RIMU = company(2, "RIMU LIFECARE LIMITED", registered="2012-05-11", grade="near", reason=THROUGH.format(who="Ann Mary ROE"), through=ANN["ref"],
               via=ANN_RIMU["ref"], rule_="through-officer")
ANN_SISTER = director(3, "a", "Ann Mary ROE", "2025-03-01", "KOWHAI VILLAGES LIMITED", grade="near", reason=THROUGH.format(who="Ann Mary ROE"),
                      through=ANN["ref"], via=ANN["ref"])
#: Bob sits on a consultancy
BOB_ACME = director(4, "b", "Bob James LEE", "2010-03-03", "ACME CONSULTING LIMITED", grade="near", reason=THROUGH.format(who="Bob James LEE"),
                    through=BOB["ref"], via=BOB["ref"])
#: a liquidator appointed to Ann's other company in 2023
RIMU_LIQ = it("gazette:gazette/2023-al1/company/2", "gazette_liquidations", grade="near", title="RIMU LIFECARE LIMITED", dates="appointed 13 July 2023",
              row={"register_key": "companies/2", "appointed_on": "2023-07-13", "published_on": "2023-07-15", "appointed_by": "shareholders"},
              via=RIMU["ref"], reason=THROUGH.format(who="Ann Mary ROE"), through=ANN["ref"], rule_="through-officer", entity_title="RIMU LIFECARE LIMITED")
#: a prohibition on Bob's record, in force to 2027
BOB_PROHIB = it("gazette:gazette/2022-ot1/prohibition/1", "gazette_prohibitions", grade="near", title="Bob James Lee · prohibition",
                dates="from 22 September 2022; to 22 September 2027", row={"ends_on": "2027-09-22"}, reason=THROUGH.format(who="Bob James LEE"),
                through=BOB["ref"], via=BOB["ref"], rule_="through-officer")
BOB_BANKRUPT = it("gazette:gazette/2019-ba1/person/1", "gazette_bankruptcies", grade="near", title="LEE · Bob James", dates="adjudicated 2 May 2019",
                  row={"kind": "adjudication", "event_on": "2019-05-02"}, reason=THROUGH.format(who="Bob James LEE"), through=BOB["ref"], via=BOB["ref"],
                  rule_="through-officer")
OWN_LIQ = it("gazette:gazette/2026-al5/company/1", "gazette_liquidations", title="KOWHAI LIVING GROUP LIMITED", dates="appointed 1 August 2026",
             row={"register_key": "companies/1", "appointed_on": "2026-08-01", "published_on": "2026-08-03"}, via=OPERATOR["ref"])
OWN_REMOVAL = it("gazette:gazette/2026-ds5/company/1", "gazette_company_notices", title="KOWHAI LIVING GROUP LIMITED · removal",
                 dates="objections by 17 August 2026", via=OPERATOR["ref"],
                 row={"kind": "removal", "action": "intention to remove", "event_basis": "objections by", "register_key": "companies/1"})
#: the charity arm, its returns, and a disqualified trustee
CHARITY = it("charities:charities/CC10001", "charities", title="KOWHAI LIVING CHARITABLE TRUST",
             row={"key": "charities/CC10001", "status": "Registered", "year_end_month": 6, "year_end_day": 30, "registered_on": "2008-01-01"})


def ret(n, period_end, modified=False, audited=True, grade="confirmed"):
    return it(f"charities:charities/returns/{n}", "charity_returns", grade=grade, title=f"return to {period_end}", dates=f"period to {period_end}",
              via=CHARITY["ref"], row={"charity_key": "charities/CC10001", "period_end": period_end, "tier": "Tier 2", "audited": audited,
                                       "modified_opinion": modified, "opinion": "Qualified" if modified else None, "total_gross_income": 2_500_000,
                                       "total_expenditure": 2_400_000, "net_surplus": 100_000, "total_assets": 9_000_000,
                                       "total_liabilities": 1_000_000, "total_equity": 8_000_000})


RET_2025 = ret(1, "2025-06-30")
RET_2024 = ret(2, "2024-06-30")
RET_MOD = ret(3, "2025-06-30", modified=True)
TRUSTEE_DQ = it("charities:charities/officers/5", "charity_officers", grade="near", title="Bob James LEE", reason=THROUGH.format(who="Bob James LEE"),
                row={"charity_key": "charities/CC10001", "role": "Trustee", "status": "Disqualified", "disqualified": True}, through=BOB["ref"],
                via=BOB["ref"], rule_="through-officer")
#: a charity officer row matched to Bob by name only (rule same-name), the register's mark on it: amber at most
BY_NAME_DQ = dict(TRUSTEE_DQ, ref="charities:charities/officers/6", rule="same-name",
                  reason="no link joins the Charities Register's officers to any other row yet, so this officer row is matched to the subject by name")
#: a charitable trust board's own charity by its business number, and the trustees the register files on it
BOARD_CHARITY = it("charities:charities/CC20002", "charities", title="KOWHAI LIVING CHARITABLE TRUST", via="companies:companies/9",
                   row={"key": "charities/CC20002", "status": "Registered", "nzbn": "9", "year_end_month": 3, "year_end_day": 31}, rule_="official-number")
BOARD_TRUSTEE = it("charities:charities/officers/20", "charity_officers", title="Mere Ana TAMA", via=BOARD_CHARITY["ref"],
                   row={"charity_key": "charities/CC20002", "role": "Trustee", "status": "Qualified", "disqualified": False})
BOARD_TRUSTEE_DQ = it("charities:charities/officers/21", "charity_officers", title="Tom Rua WIRI", via=BOARD_CHARITY["ref"],
                      row={"charity_key": "charities/CC20002", "role": "Trustee", "status": "Disqualified", "disqualified": True})
PRO_HUB = {"ref": ANN["ref"], "title": "Ann Mary ROE", "kind": "professional-director", "text": "a professional director: 80 directorships"}
#: the person start: Ann's own row on the entity, and her own confirmed role on another operator
PERSON = dict(ANN, via=None)
PERSON_RIMU = director(2, "a", "Ann Mary ROE", "2018-12-13", "RIMU LIFECARE LIMITED", via=PERSON["ref"])
PERSON_RIMU2 = director(5, "a", "Ann Mary ROE", "2016-01-01", "TOTARA REST HOME LIMITED", via=PERSON["ref"])
CONTESTED_ROW = director(6, "z", "Ann Mary ROE", "2017-01-01", "MATAI CARE LIMITED", grade="near", reason=CONTESTED + "and more")


def reads(charities=False):
    views = sorted(VIEWS) + (list(CHARITY_VIEWS) if charities else [])
    return [{"view": v, "licence": "x", "attribution": "x", "refresh": "x"} for v in views]


def report(subject=OPERATOR, hubs=(), charities=False, officers_followed=2, officers_omitted=0, buckets=("officers", "second", "near", "chain"),
           **sections):
    out = {"found": True, "as_of": "2026-10-21", "subject": subject, "members": [], "flags": [], "hubs": list(hubs),
           "template": {"name": "healthcare", "reads": reads(charities)},
           "group": {"built": True, "size": 1, "contested": False, "omitted": 0},
           "walk": {"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0, "buckets": list(buckets),
                    "officers_followed": officers_followed, "officers_omitted": officers_omitted}, "sections": []}
    for name in ORDER:
        xs = sections.get(name.replace("-", "_"), [])
        out["sections"].append({"name": name, "heading": name, "items": xs, "omitted": 0, "omitted_views": [], "blank": None if xs else "none found"})
    return out


def operator(**kw):
    """The operator with two officers followed: Ann on another care-named operator (which a liquidator was appointed to in 2023) and on
    a sister carrying the entity's name word; Bob on a consultancy, with a prohibition and a bankruptcy on his record."""
    parts = dict(governance=[ANN, BOB], overlap=[ANN_RIMU, RIMU, ANN_SISTER, BOB_ACME], gazette=[RIMU_LIQ, BOB_PROHIB, BOB_BANKRUPT])
    parts.update(kw)
    return report(**parts)


def with_charity(*rets, **kw):
    parts = dict(governance=[ANN, BOB, CHARITY], charity_returns=list(rets))
    parts.update(kw)
    return report(charities=True, **parts)


def person(**kw):
    parts = dict(governance=[PERSON_RIMU, PERSON_RIMU2])
    parts.update(kw)
    return report(subject=PERSON, **parts)


def flags_of(mod, r):
    return [fn(r) for fn in mod.RULES]


# ── the properties, each a list of what broke (empty when they hold) ────────

def properties(mod) -> list:
    """What an investor relies on, checked on fixtures; the mutant check runs
    it on each broken copy of the rules and needs it to say something."""
    bad = []
    rl = lambda n: rule(n, mod)   # noqa: E731
    mod.HISTORY = False
    starts = {"operator": operator(), "charity": with_charity(RET_MOD, RET_2024), "person": person(),
              "trust board": report(subject=TRUST_BOARD), "village": report(subject=VILLAGE),
              "other": report(subject=it("gazette:gazette/2020-x/company/1", "gazette_liquidations", title="A NOTICE")), "empty": report()}
    for start, r in starts.items():
        for f in flags_of(mod, r):
            if CAUSE.search(f["text"]):
                bad.append(f"{start}: {f['rule']} says a word of cause or ownership: {f['text'][:120]}")
            if CONTRACT.address_shaped(f["text"]):
                bad.append(f"{start}: {f['rule']} prints an address: {f['text'][:120]}")
    for name in ALWAYS_BLOCKED:
        for r in (operator(), person(), report()):
            if rl(name)(r)["status"] != "blocked":
                bad.append(f"{name} is not blocked: the register it reads is not held")
    for name in CHARITY_CHECKS:
        for r in (operator(), person(), report(subject=TRUST_BOARD)):
            f = rl(name)(r)
            if f["status"] != "blocked" or "the template does not read" not in f["text"]:
                bad.append(f"{name} ran though the template does not read the charities register")
    # an organisation start whose officers were not all read never clears an officer check
    for name in OFFICER_CHECKS:
        for what, r in (("no officer listed (a trust board)", report(subject=TRUST_BOARD)), ("a village row", report(subject=VILLAGE)),
                        ("an officer past the limit", report(governance=[ANN, BOB], officers_omitted=1)),
                        ("the officers reach not run", report(governance=[ANN, BOB], buckets=("near",)))):
            if rl(name)(r)["status"] == "clear":
                bad.append(f"{what}: {name} cleared officers it never read")
    # the overlap
    f = rl("officer_overlap")(operator())
    if not (f["status"] == "fired" and f["severity"] == "amber" and ANN_RIMU["ref"] in f["citations"] and ANN["ref"] in f["citations"]):
        bad.append(f"an officer on another care-named operator did not raise officer-overlap amber with both rows cited: {f['status']} {f['severity']}")
    if "from 2018-12-13" not in f["text"] or "from 2025-02-01" not in f["text"]:
        bad.append("the overlap does not set the officer's two roles' dates side by side")
    if rl("officer_overlap")(operator(overlap=[ANN_SISTER, BOB_ACME]))["severity"] == "amber":
        bad.append("an officer on a sister carrying the entity's own name word raised officer-overlap amber")
    if rl("officer_overlap")(operator(hubs=[PRO_HUB]))["severity"] == "amber" and \
            rl("officer_overlap")(operator(hubs=[PRO_HUB], overlap=[ANN_RIMU, BOB_ACME]))["severity"] == "amber":
        bad.append("a professional director's overlap raised officer-overlap amber: a hub sits on many boards")
    if rl("officer_overlap")(report(governance=[ANN, BOB], overlap=[]))["status"] != "clear":
        bad.append("officers followed with no other role did not clear officer-overlap")
    p = rl("officer_overlap")(person())
    if not (p["status"] == "fired" and p["severity"] == "amber"):
        bad.append("a person on two care-named operators did not raise officer-overlap amber")
    pc = person(governance=[CONTESTED_ROW])
    pc["group"]["contested"] = True
    if rl("officer_overlap")(pc)["status"] != "fired":
        bad.append("a contested group's other rows were dropped from the overlap instead of counted near")
    # the people
    d = rl("disqualified_officer")(operator())
    if not (d["status"] == "fired" and d["severity"] == "red" and BOB["ref"] in d["citations"]):
        bad.append(f"a prohibition in force on a current officer's record did not raise disqualified-officer red: {d['status']} {d['severity']}")
    contested = dict(BOB_PROHIB, reason=CONTESTED + BOB_PROHIB["reason"])
    if rl("disqualified_officer")(operator(gazette=[contested]))["severity"] == "red":
        bad.append("a prohibition through a contested group was red")
    ended = dict(BOB_PROHIB, row={"ends_on": "2024-01-01"})
    if rl("disqualified_officer")(operator(gazette=[ended]))["severity"] == "red":
        bad.append("an ended prohibition was red")
    if rl("disqualified_officer")(operator(gazette=[dict(BOB_PROHIB, suppressed=True)]))["status"] == "fired":
        bad.append("a revoked (suppressed) prohibition was counted")
    f = rl("disqualified_officer")(with_charity(RET_2025, governance=[ANN, BOB, CHARITY, BY_NAME_DQ]))
    if f["status"] == "fired" and f["severity"] == "red":
        bad.append("a disqualified mark on a charity officer row matched only by name is red")
    f = rl("disqualified_officer")(report(subject=TRUST_BOARD, charities=True, governance=[BOARD_CHARITY, BOARD_TRUSTEE, BOARD_TRUSTEE_DQ]))
    if not (f["status"] == "fired" and f["severity"] == "red"):
        bad.append(f"a trustee the register marks disqualified on the trust board's own charity was not raised red: {f['status']} {f['severity']}")
    if rl("disqualified_officer")(with_charity(RET_2025, governance=[ANN, BOB, CHARITY, TRUSTEE_DQ]))["status"] != "fired":
        bad.append("a charity officer the register marks disqualified did not raise disqualified-officer")
    if rl("officer_bankruptcy")(operator())["status"] != "fired":
        bad.append("a bankruptcy on an officer's record did not fire")
    if rl("disqualified_officer")(report(governance=[ANN, BOB]))["status"] != "clear":
        bad.append("officers followed with nothing on their records did not clear disqualified-officer")
    # the Gazette
    o = rl("officer_company_notices")(operator())
    if not (o["status"] == "fired" and o["severity"] == "amber" and RIMU_LIQ["ref"] in o["citations"]):
        bad.append(f"a liquidation on an officer's other company did not raise officer-company-notices amber: {o['status']} {o['severity']}")
    if "appointed 13 July 2023" not in o["text"] or "from 2018-12-13" not in o["text"]:
        bad.append("the notice's date and the officer's role on that company are not set side by side")
    if rl("officer_company_notices")(report(governance=[ANN, BOB]))["status"] == "clear":
        bad.append("past roles not held: officer-company-notices cleared companies the officers left")
    own = rl("insolvency_notice")(report(gazette=[OWN_LIQ]))
    if not (own["status"] == "fired" and own["severity"] == "red"):
        bad.append("a liquidation on the entity did not raise insolvency-notice red")
    if rl("insolvency_notice")(report(gazette=[OWN_REMOVAL]))["status"] == "fired":
        bad.append("a removal on the entity raised insolvency-notice")
    young = dict(OPERATOR, row=dict(OPERATOR["row"], registered_on="2025-06-01"))
    if rl("young_entity")(report(subject=young))["status"] != "fired":
        bad.append("an entity registered 16 months ago did not raise young-entity")
    if rl("young_entity")(report())["status"] == "fired":
        bad.append("an entity registered twelve years ago raised young-entity")
    # the charity arm
    a = rl("charity_audit_opinion")(with_charity(RET_MOD, RET_2024))
    if not (a["status"] == "fired" and a["severity"] == "red"):
        bad.append(f"a modified opinion on a confirmed charity's newest return did not raise red: {a['status']} {a['severity']}")
    if rl("charity_audit_opinion")(with_charity(dict(RET_MOD, grade="near")))["severity"] == "red":
        bad.append("a modified opinion on a namesake charity's return was red")
    if rl("charity_audit_opinion")(with_charity(RET_2025, RET_2024))["status"] != "clear":
        bad.append("unmodified returns did not clear charity-audit-opinion")
    late = rl("charity_return_filed")(with_charity(RET_2024))
    if late["status"] != "fired" or "2025-06-30" not in late["text"]:
        bad.append("a charity whose newest return is a year short of its last balance date did not raise charity-return-filed")
    if rl("charity_return_filed")(with_charity(RET_2025, RET_2024))["status"] != "clear":
        bad.append("a charity filed to its last balance date did not clear charity-return-filed")
    if rl("charity_arm")(with_charity(governance=[ANN, BOB]))["status"] == "clear":
        bad.append("charity-arm cleared: a charity the links do not join cannot be seen")
    # no suppressed name in a flag
    hidden = operator(governance=[ANN, dict(BOB, suppressed=True, title="name suppressed")])
    for f in flags_of(mod, hidden):
        if "Bob James LEE" in f["text"] and f["rule"] in ("disqualified-officer", "officer-overlap"):
            bad.append(f"{f['rule']} printed a suppressed officer's name")
    return bad


def test_the_properties_hold_on_the_rules_as_written():
    assert properties(R) == []


#: (what the mutant breaks, the text replaced, its replacement): each must be unique in rules.py and caught by properties()
MUTANTS = (
    ("a hub's overlap is amber", "if len(care) > len(own_name) and not hub:", "if len(care) > len(own_name):"),
    ("a sister of the entity's own name is another operator", "own_name = [r for r in care if word and _lead_word(r.get(\"entity_title\")) == word]",
     "own_name = []"),
    ("the officer's role on the entity is never dated", "mine = f\"{_who(o)} ({_role(o)} of the entity, {'from ' + _start_of(o).isoformat() if _start_of(o) else 'no start filed'})\" if o else oref",
     "mine = f\"{_who(o)}\" if o else oref"),
    ("a trust board with no officer listed clears", "    if _no_officers(report):\n        return _no_officers(report)\n", ""),
    ("an officer past the limit is ignored", "    if w.get(\"officers_omitted\"):\n        return f\"the walk followed", "    if False:\n        return f\"the walk followed"),
    ("the officers reach is assumed to have run", "    if \"officers\" not in (w.get(\"buckets\") or []):", "    if False:"),
    ("a contested group's prohibition is red", "red = [it for it in on_officers if it.get(\"rule\") != \"same-name\" and not _contested(it) and",
     "red = [it for it in on_officers if it.get(\"rule\") != \"same-name\" and"),
    ("a by-name charity row is red", "red = [it for it in on_officers if it.get(\"rule\") != \"same-name\" and", "red = [it for it in on_officers if"),
    ("the entity's own charity's trustees are not read", "    if own_marks:", "    if False:"),
    ("an ended prohibition is red", " and _in_force(report, it) and it[\"through\"] in officer_rows", " and it[\"through\"] in officer_rows"),
    ("a revoked prohibition is counted", "live = [it for it in items(report, (view,)) if not it.get(\"suppressed\")]", "live = list(items(report, (view,)))"),
    ("the charity register's disqualification is not read", "if it[\"row\"].get(\"disqualified\") and not it.get(\"suppressed\")]", "if False]"),
    ("a notice on an officer's company is red", 'return flag("officer-company-notices", V, "fired", "amber",\n                        f"{len(hits)} Gazette insolvency notice(s) on {len',
     'return flag("officer-company-notices", V, "fired", "red",\n                        f"{len(hits)} Gazette insolvency notice(s) on {len'),
    ("a clear is given though past roles are not held", "    if HISTORY:\n        return flag(rule, V, \"clear\", severity, text, **kw)",
     "    if True:\n        return flag(rule, V, \"clear\", severity, text, **kw)"),
    ("a removal is an insolvency", "return it[\"view\"] == \"gazette_company_notices\" and r.get(\"kind\") in INSOLVENCY_KINDS and", "return it[\"view\"] == \"gazette_company_notices\" and"),
    ("a namesake charity's opinion is red", "red = [it for it in modified if it[\"ref\"] in newest and it[\"grade\"] == \"confirmed\"]", "red = list(modified)"),
    ("a charity check runs without the register", "    if missing:\n        return (\"the template does not read pub.", "    if False:\n        return (\"the template does not read pub."),
    ("a return a period short is filed", "if newest is None or (due - newest).days > PERIOD_SLACK_DAYS:", "if newest is None:"),
    ("the entity is never young", "if (as_of - reg).days < YOUNG_DAYS:\n        return flag(\"young-entity\", V, \"fired\", \"amber\"",
     "if (as_of - reg).days < 0:\n        return flag(\"young-entity\", V, \"fired\", \"amber\""),
    ("a contested group's roles are dropped", "    if not (report.get(\"group\") or {}).get(\"contested\"):\n        return []\n    return [it",
     "    if True:\n        return []\n    return [it"),
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
    for r in (report(), operator(), person(), with_charity(RET_2025), report(subject=TRUST_BOARD), report(subject=VILLAGE),
              report(subject=it("societies:societies/9", "societies", title="A SOCIETY INCORPORATED", row={"status": "registered"}))):
        flags = flags_of(R, r)
        assert len({f["rule"] for f in flags}) == len(flags) == len(R.RULES)
        assert not {f["rule"] for f in flags} & set(COMMON), "the builder runs the common rules; no copy here"
    assert R.flag is CONTRACT.flag and R.items is CONTRACT.items and R.section is CONTRACT.section and R.all_items is CONTRACT.all_items
    assert "common_rules" not in toml(), "the template keeps the builder's common rules"


def test_the_overlap_sets_each_officers_roles_side_by_side_and_counts_care_named_operators_apart():
    f = rule("officer_overlap")(operator())
    assert f["status"] == "fired" and f["severity"] == "amber" and f["scope"] == "officer-group"
    assert "Ann Mary ROE (DIRECTOR of the entity, from 2025-02-01): 2 other current role(s), 2 on a care-named organisation (1 carrying the " \
           "entity's own leading name word)" in f["text"]
    assert "DIRECTOR of RIMU LIFECARE LIMITED (from 2018-12-13)" in f["text"]
    assert "1 officer(s), not hubs, sit on another organisation" in f["text"] and "a sign to read, not a finding" in f["text"]
    sister_only = rule("officer_overlap")(operator(overlap=[ANN_SISTER, BOB_ACME]))
    assert sister_only["status"] == "fired" and sister_only["severity"] == "info"
    hub = rule("officer_overlap")(operator(hubs=[PRO_HUB]))
    assert hub["severity"] == "info" and "a hub (professional-director)" in hub["text"]
    p = rule("officer_overlap")(person())
    assert p["severity"] == "amber" and "3 organisation(s), 3 whose registered name reads as care" in p["text"]


def test_a_start_with_no_officer_listed_blocks_every_officer_check():
    for subject, why in ((TRUST_BOARD, "trustees are filed with the Charities Register"), (VILLAGE, "names no operator and no officer")):
        for name in OFFICER_CHECKS:
            f = rule(name)(report(subject=subject))
            assert f["status"] == "blocked" and why in f["text"], (name, f)
        assert rule("walk_coverage")(report(subject=subject))["status"] == "fired"
    society_row = company(8, "A CARE SOCIETY INCORPORATED", kind="Incorporated Society")
    assert "start the report from that row" in rule("officer_overlap")(report(subject=society_row))["text"]


def test_a_prohibition_on_an_officers_record_is_dated_beside_the_officers_role_on_the_entity():
    f = rule("disqualified_officer")(operator())
    assert f["status"] == "fired" and f["severity"] == "red" and f["scope"] == "officer-group"
    assert "Bob James LEE: DIRECTOR of the entity, from 2019-06-01 | Bob James Lee · prohibition, from 22 September 2022; to 22 September 2027" in f["text"]
    hub = {"ref": BOB["ref"], "title": "Bob James LEE", "kind": "nominee", "text": "a nominee"}
    assert rule("disqualified_officer")(operator(hubs=[hub]))["severity"] == "amber"
    b = rule("officer_bankruptcy")(operator())
    assert b["status"] == "fired" and "adjudicated 2 May 2019" in b["text"]
    clear = rule("disqualified_officer")(report(governance=[ANN, BOB]))
    assert clear["status"] == "clear" and "2 officer(s)" in clear["text"] and any("Charities Register" in x for x in clear["sources_not_held"])


def test_the_charity_checks_block_until_the_template_reads_the_register_and_then_read_its_returns():
    for name in CHARITY_CHECKS:
        f = rule(name)(operator())
        assert f["status"] == "blocked" and "the template does not read" in f["text"] and "pub.charity_returns" in f["text"], name
    s = rule("charity_returns_summary")(with_charity(RET_2024, RET_2025))
    assert s["status"] == "fired" and s["citations"] == (RET_2025["ref"],)
    for want in ("period to 2025-06-30", "Tier 2", "income $2,500,000", "expenditure $2,400,000", "surplus $100,000", "assets $9,000,000",
                 "liabilities $1,000,000", "equity $8,000,000", "audited"):
        assert want in s["text"], want
    a = rule("charity_audit_opinion")(with_charity(RET_MOD, RET_2024))
    assert a["severity"] == "red" and "opinion Qualified" in a["text"]
    late = rule("charity_return_filed")(with_charity(RET_2024))
    assert late["status"] == "fired" and "period to 2025-06-30 | newest return held: period to 2024-06-30, Tier 2" in late["text"]
    none = rule("charity_return_filed")(with_charity())
    assert none["status"] == "fired" and "newest return held: none" in none["text"]
    assert rule("charity_arm")(with_charity(RET_2025))["status"] == "fired"
    assert rule("charity_arm")(with_charity(governance=[ANN]))["status"] == "blocked"


def test_the_charities_register_is_read_by_number_and_by_name():
    """Card the-healthcare-template-can-now-read-the-charities-register-and-the-reaches (the charities half): the three views read,
    `charities` out of every not-held line; a trust board's trustees on its own charity are read for the register's mark and named as
    not followed; a by-name row is amber at most; the charity arm lists by-name rows near."""
    t = toml()
    assert {"charities", "charity_officers", "charity_returns"} <= {r["view"] for r in t["reads"]}
    sec = {x["name"]: x for x in t["sections"]}
    assert {"charities", "charity_officers"} <= set(sec["governance"]["views"]) and "named" in sec["governance"]["sources"]
    assert sec["charity-returns"]["views"] == ["charity_returns"] and "roles" in sec["charity-returns"]["sources"]
    assert not any("charities" in x.get("not_held", []) for x in t["sections"])
    board = dict(subject=TRUST_BOARD, charities=True)
    f = rule("disqualified_officer")(report(governance=[BOARD_CHARITY, BOARD_TRUSTEE, BOARD_TRUSTEE_DQ], **board))
    assert f["status"] == "fired" and f["severity"] == "red" and f["citations"] == (BOARD_TRUSTEE_DQ["ref"],) and f["scope"] == "entity", f
    ended = dict(BOARD_TRUSTEE_DQ, row=dict(BOARD_TRUSTEE_DQ["row"], ended_on="2020-01-01"))
    assert rule("disqualified_officer")(report(governance=[BOARD_CHARITY, ended], **board))["severity"] == "amber"
    o = rule("officer_overlap")(report(governance=[BOARD_CHARITY, BOARD_TRUSTEE], **board))
    assert o["status"] == "blocked" and "1 officer row(s) on its charity" in o["text"] and "not followed" in o["text"], o
    o = rule("officer_overlap")(report(**board))
    assert o["status"] == "blocked" and "no charity row carries this board's business number" in o["text"]
    p = rule("disqualified_officer")(report(subject=PERSON, charities=True, governance=[PERSON_RIMU, dict(BY_NAME_DQ, through=None, via=PERSON["ref"])]))
    assert p["status"] == "fired" and p["severity"] == "amber", p
    c = rule("disqualified_officer")(report(subject=PERSON, charities=True, governance=[PERSON_RIMU]))
    assert c["status"] == "clear" and any("pub.charity_officers" in x for x in c["sources_held"]), c
    holder = it("companies:companies/1/shareholder/a", "shareholders", title="Ann Mary ROE", via=None)
    assert rule("disqualified_officer")(report(subject=holder, charities=True))["status"] == "blocked", "a holder's name is not looked up"
    a = rule("charity_arm")(report(subject=PERSON, charities=True, governance=[dict(BY_NAME_DQ, through=None, via=PERSON["ref"], entity_title="A TRUST")]))
    assert a["status"] == "fired" and a["scope"] == "near" and "A TRUST" in a["text"] and "namesake" in a["text"]


def test_every_register_not_held_blocks_and_a_village_row_is_named_as_such():
    for name in ALWAYS_BLOCKED:
        for r in (operator(), person(), report()):
            assert rule(name)(r)["status"] == "blocked", name
    v = rule("retirement_villages")(report(subject=VILLAGE))
    assert "a village's own register row, which names no operator and no supervisor" in v["text"]
    near_village = dict(VILLAGE, grade="near", reason="two companies under one name")
    n = rule("retirement_villages")(report(identity=[near_village]))
    assert n["citations"] == (VILLAGE["ref"],) and "not the operator's until the file says so" in n["text"]
    assert "Code of Rights" in rule("hdc_decisions")(report())["text"]
    assert rule("entity_status")(report(subject=VILLAGE))["sources_not_held"]


def test_the_entitys_own_record_is_dated_from_each_notice():
    f = rule("insolvency_notice")(report(gazette=[OWN_REMOVAL, OWN_LIQ]))
    assert f["status"] == "fired" and f["severity"] == "red" and f["citations"] == (OWN_LIQ["ref"],) and "appointed 1 August 2026" in f["text"]
    assert rule("insolvency_notice")(report())["status"] == "clear"
    s = rule("entity_status")(report(subject=company(7, "A REST HOME LIMITED", status="In Liquidation")))
    assert s["status"] == "fired" and s["severity"] == "red"
    soc = it("societies:societies/9", "societies", title="A SOCIETY INCORPORATED", row={"status": "registered"})
    assert rule("insolvency_notice")(report(subject=soc))["status"] == "blocked"


def test_the_presentation_rules_hold_on_every_flag_from_every_start():
    """The shape's own check (rule 9 and rule 3 on fired flags), run on the
    flags each start produces, as the builder runs it on a finished report."""
    for r in (operator(), with_charity(RET_MOD, RET_2024, governance=[ANN, BOB, CHARITY, TRUSTEE_DQ]), person(), report(),
              report(subject=TRUST_BOARD), report(subject=VILLAGE)):
        r["flags"] = flags_of(R, r)
        problems = [p for p in CONTRACT.presentation_problems(r) if p.startswith("flag ")]
        assert problems == [], problems


def test_the_rules_file_imports_nothing_of_the_shape():
    src = inspect.getsource(R)
    assert not re.search(r"^\s*(from|import) products", src, re.M)
