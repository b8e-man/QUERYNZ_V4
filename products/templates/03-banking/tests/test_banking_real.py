"""The banking director history on the real published tables (slow), through
the shape's own command line (`python -m products.report render REF
--template banking`), as an analyst's memo is made. Subjects are taken from
the tables at run time, never fixed, so the test follows the data: a
director whose uncontested group sat on two or more liquidated companies, the
company one of those liquidations names, and a director whose company has
only a removal notice. Every memo carries the builder's common flags once and
is not refused by the shape's presentation rules. Imports nothing of
products.report (the one-way test)."""
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
ENDINGS = "HOW EACH COMPANY ENDED: REGISTER STATUS AND GAZETTE NOTICES, DATED"
BESIDE = "THE PEOPLE THEY SAT BESIDE, AND THE COMPANIES THOSE PEOPLE SHARE WITH THEM"
TWICE_LIQUIDATED = """
    with grp as (select g.group_id, d.entity_key from pub.groups g join pub.directors d on 'companies:' || d.key = g.row_key
                 where not coalesce(g.contested, false)),
         agg as (select group_id, count(distinct entity_key) cos, count(distinct l.register_key) liq
                 from grp left join pub.gazette_liquidations l on l.register_key = grp.entity_key group by 1)
    select min(g.row_key) from pub.groups g
    where g.group_id = (select min(group_id) from agg where cos between 2 and 10 and liq >= 2) and g.row_key like 'companies:%/director/%'"""


def one(sql: str) -> str:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got[0]


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "banking"], cwd=REPO,
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
    assert "identity" not in flags
    return {"text": text, "flags": flags, "sections": sections}


def test_a_director_of_two_liquidated_companies_gets_the_repeat_and_every_beside_row_is_near():
    m = memo(one(TWICE_LIQUIDATED))
    f = m["flags"]["repeat-insolvency"]
    assert f["status"] == "fired" and f["severity"] == "red", f
    assert m["flags"]["insolvency-notices"]["status"] in ("fired", "blocked")
    endings = m["sections"][ENDINGS]
    assert endings["confirmed"] >= 4, "two companies, each with at least its liquidation notice beneath it"
    assert any("[confirmed]" in x and ("Liquidation" in x or "Removed" in x) for x in endings["lines"])
    assert all(x.startswith("  - [near]") for x in m["sections"][BESIDE]["lines"]), "a connection through another person is never confirmed"
    assert m["flags"]["securities-register"]["status"] == "blocked"
    assert "not held: The Personal Property Securities Register" in m["text"]


def test_from_the_company_a_liquidation_names_the_people_checks_block():
    company = one(f"""
        select 'companies:' || l.register_key from pub.gazette_liquidations l
        join pub.directors d on d.entity_key = l.register_key and 'companies:' || d.key = ({TWICE_LIQUIDATED})
        limit 1""")
    m = memo(company)
    assert m["flags"]["insolvency-notices"]["status"] == "fired" and m["flags"]["insolvency-notices"]["severity"] == "red"
    assert m["flags"]["company-endings"]["status"] in ("fired", "clear")
    for name in ("repeat-insolvency", "left-before-notice", "prohibition", "shared-boards", "charity-officer-roles"):
        assert m["flags"][name]["status"] == "blocked", name
        assert name == "charity-officer-roles" or "start a report from each person" in m["flags"][name]["text"], name


def test_a_company_with_only_a_removal_notice_is_not_an_insolvency_and_nothing_clears_while_past_roles_are_not_held():
    ref = one("""
        select 'companies:' || min(d.key) from pub.gazette_company_notices n
        join pub.directors d on d.entity_key = n.register_key and d.in_latest and not coalesce(d.suppressed, false)
        left join pub.groups g on g.row_key = 'companies:' || d.key
        where n.kind = 'removal' and g.row_key is null and n.register_key like 'companies/94290000%'
          and not exists (select 1 from pub.gazette_company_notices x where x.register_key = n.register_key and x.kind <> 'removal')
          and not exists (select 1 from pub.gazette_liquidations x where x.register_key = n.register_key)""")
    m = memo(ref)
    for name in ("insolvency-notices", "repeat-insolvency"):
        assert m["flags"][name]["status"] == "blocked" and "current roles only" in m["flags"][name]["text"], (name, "past roles are not held")
    assert m["flags"]["register-removals"]["status"] == "fired" and m["flags"]["register-removals"]["severity"] == "info"
    assert m["flags"]["past-roles"]["status"] == "blocked" and m["flags"]["past-roles"]["severity"] == "red"
