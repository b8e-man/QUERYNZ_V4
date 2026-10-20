"""The legal counterparty and conflict check on the real published tables
(slow), through the shape's own command line (`python -m products.report
render REF --template legal`), as a clerk's memo is made. Subjects are taken
from the tables at run time, never fixed, so the test follows the data: a
company with a deed of company arrangement, a company an amalgamation
proposal names, and a director in an uncontested group on two or more
companies. Every memo carries the builder's common flags once, is not
refused by the shape's presentation rules, and never clears the client
overlap. Imports nothing of products.report (the one-way test)."""
import os
import re
import subprocess
import sys

import pytest

from support import db as sdb

pytestmark = pytest.mark.slow

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
FLAG = re.compile(r"^  (FIRED|CLEAR|BLOCKED)\s+(red|amber|info)\s+([a-z-]+)@[\d.]+: (.*)$")
COMMON = ("group-standing", "hubs-met", "replaced-return")
HEADING = re.compile(r"^([A-Z][A-Z ,':]+?)  \((\d+) confirmed, (\d+) near\)$")
WEB = "THE COMPANIES THOSE PEOPLE SHARE, WITH DATES: THE CONFLICT WEB"
GAZETTE = "THE GAZETTE ON THE COMPANY AND ITS PEOPLE"


def one(sql: str) -> str:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got[0]


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "legal"], cwd=REPO,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    text = out.stdout
    assert "NOT FOUND" not in text, text[:400]
    assert "REFUSED" not in text, text[text.index("REFUSED"):][:1200]
    flags, sections, current = {}, {}, None
    for line in text.splitlines():
        m = FLAG.match(line)
        if m:
            flags[m.group(3)] = {"status": m.group(1).lower(), "severity": m.group(2), "text": m.group(4)}
            continue
        h = HEADING.match(line)
        if h:
            current = h.group(1)
            sections[current] = {"confirmed": int(h.group(2)), "near": int(h.group(3)), "lines": []}
            continue
        if current and line.startswith("  - ["):
            sections[current]["lines"].append(line)
        elif line and not line.startswith(" "):
            current = None
    for name in COMMON:
        assert len(re.findall(rf"^  (?:FIRED|CLEAR|BLOCKED)\s+\w+\s+{name}@", text, re.M)) == 1, name
    assert flags["client-overlap"]["status"] == "blocked", "the firm's list is not an input: no overlap is ever cleared"
    assert flags["court-judgments"]["status"] == "blocked" and "not held: Court judgments" in text
    return {"text": text, "flags": flags, "sections": sections}


def test_a_company_with_a_deed_of_company_arrangement_is_an_insolvency_and_its_people_checks_block():
    m = memo(one("""select 'companies:' || min(register_key) from pub.gazette_company_notices
                    where kind = 'deed of company arrangement' and register_key is not null"""))
    f = m["flags"]["insolvency-notices"]
    assert f["status"] == "fired" and f["severity"] == "red" and "deed of company arrangement" in f["text"], f
    assert any("deed of company arrangement" in x for x in m["sections"][GAZETTE]["lines"])
    for name in ("conflict-web", "repeat-insolvency", "prohibition", "shared-boards", "practitioner-roles"):
        assert m["flags"][name]["status"] == "blocked" and "start a report from each person" in m["flags"][name]["text"], name


def test_a_company_an_amalgamation_proposal_names_is_flagged_and_not_an_insolvency():
    m = memo(one("""select 'companies:' || min(n.register_key) from pub.gazette_company_notices n
                    where n.kind = 'amalgamation' and n.register_key is not null
                      and not exists (select 1 from pub.gazette_liquidations l where l.register_key = n.register_key)
                      and not exists (select 1 from pub.gazette_company_notices x where x.register_key = n.register_key
                                      and x.kind in ('winding-up application', 'receivership', 'administration', 'notice to creditors',
                                                     'deed of company arrangement'))"""))
    assert m["flags"]["amalgamation"]["status"] == "fired" and "not reached" in m["flags"]["amalgamation"]["text"]
    assert m["flags"]["insolvency-notices"]["status"] == "clear", "an amalgamation is not an insolvency"


def test_a_directors_conflict_web_lists_each_company_and_every_person_on_it_near():
    ref = one("""
        with grp as (select g.group_id, d.entity_key from pub.groups g join pub.directors d on 'companies:' || d.key = g.row_key
                     where not coalesce(g.contested, false)),
             agg as (select group_id, count(distinct entity_key) cos from grp group by 1)
        select min(g.row_key) from pub.groups g
        where g.group_id = (select min(group_id) from agg where cos between 2 and 6) and g.row_key like 'companies:%/director/%'""")
    m = memo(ref)
    assert m["flags"]["conflict-web"]["status"] == "fired", m["flags"]["conflict-web"]
    web = m["sections"][WEB]
    assert web["confirmed"] >= 2, "two companies at least, each heading its people"
    assert all(x.startswith("  - [near]") for x in web["lines"] if "shareholder of record" in x or ": DIRECTOR of" in x), \
        "a connection through another person is never confirmed"
    assert m["flags"]["past-roles"]["status"] == "blocked"
