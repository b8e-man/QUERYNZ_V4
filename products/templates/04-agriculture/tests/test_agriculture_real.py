"""The agriculture template on the real published tables (slow), through the
shape's own command line (`python -m products.report render REF --template
agriculture`), as a credit manager's memo is made. Subjects are taken from
the tables at run time, never fixed: a farm company in receivership with
its Gazette notice, a director of several companies in liquidation, a
farming limited partnership, and a company whose only notice is a removal.
Imports nothing of products.report (the one-way test)."""
import os
import re
import subprocess
import sys

import pytest

from support import db as sdb

pytestmark = pytest.mark.slow

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
FLAG = re.compile(r"^  (FIRED|CLEAR|BLOCKED)\s+(red|amber|info)\s+([a-z-]+)@[\d.]+: (.*)$")
HEADING = re.compile(r"^([A-Z][A-Z ,';-]+?)  \((\d+) confirmed, (\d+) near\)$")
ROLES = "ITS OFFICERS AND HOLDERS OF RECORD, WITH THEIR DATES"
OTHER = "THE PEOPLE'S OTHER COMPANIES, AND WHAT BECAME OF THEM"


def one(sql: str) -> str:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got[0]


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "agriculture"], cwd=REPO,
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
    return {"text": text, "flags": flags, "sections": sections}


def test_a_farm_company_in_receivership_is_red_on_its_status_and_its_notice_and_blocked_on_its_people():
    ref = one("""
        select 'companies:' || c.key from pub.companies c
        where c.status = 'In Receivership' and c.name ~* '(farm|dairy|orchard|station)' and c.in_latest
          and exists (select 1 from pub.gazette_company_notices n where n.register_key = c.key and n.kind = 'receivership')
          and exists (select 1 from pub.directors d where d.entity_key = c.key and d.in_latest and not coalesce(d.suppressed, false))
        order by c.key limit 1""")
    m = memo(ref)
    f = m["flags"]
    assert f["register-status"]["status"] == "fired" and f["register-status"]["severity"] == "red" and "In Receivership" in f["register-status"]["text"]
    assert f["entity-insolvency"]["status"] == "fired" and f["entity-insolvency"]["severity"] == "red"
    for name in ("officer-group-insolvency", "prohibition", "other-companies", "bankruptcy", "practitioner-repeat"):
        assert f[name]["status"] == "blocked", name
    assert any("DIRECTOR of" in x for x in m["sections"][ROLES]["lines"])


def test_a_director_of_several_companies_in_liquidation_is_red_with_each_company_listed():
    ref = one("""
        with d as (select g.group_id, d.key, d.entity_key from pub.groups g join pub.directors d on 'companies:' || d.key = g.row_key
                   where not coalesce(g.contested, false) and not coalesce(d.suppressed, false))
        select min('companies:' || d.key) from d
        where d.group_id in (select d2.group_id from d d2 join pub.gazette_liquidations l on l.register_key = d2.entity_key
                             group by 1 having count(distinct d2.entity_key) between 3 and 6)
        group by d.group_id having count(*) <= 12 order by 1 limit 1""")
    m = memo(ref)
    f = m["flags"]["officer-group-insolvency"]
    assert f["status"] == "fired" and f["severity"] == "red"
    assert m["flags"]["register-status"]["status"] == "blocked"
    assert m["sections"][OTHER]["confirmed"] >= 3


def test_a_farming_limited_partnership_says_its_partners_are_not_held():
    ref = one("""
        select 'companies:' || key from pub.companies where entity_type = 'NZ Limited Partnership' and in_latest
          and name ~* '(farm|dairy|orchard)' order by key limit 1""")
    m = memo(ref)
    assert m["flags"]["officers-of-record"]["status"] == "blocked" and "partners" in m["flags"]["officers-of-record"]["text"]
    assert "not held: " in m["text"] and "Limited partnerships' partners" in m["text"]


def test_a_company_with_only_a_removal_notice_is_not_an_insolvency():
    ref = one("""
        select 'companies:' || c.key from pub.companies c join pub.gazette_company_notices n on n.register_key = c.key and n.kind = 'removal'
        where c.name ~* 'farm'
          and not exists (select 1 from pub.gazette_company_notices x where x.register_key = c.key and x.kind <> 'removal')
          and not exists (select 1 from pub.gazette_liquidations x where x.register_key = c.key)
        order by c.key limit 1""")
    m = memo(ref)
    assert m["flags"]["entity-insolvency"]["status"] == "clear"
    assert m["flags"]["register-removals"]["status"] == "fired" and m["flags"]["register-removals"]["severity"] == "amber"
