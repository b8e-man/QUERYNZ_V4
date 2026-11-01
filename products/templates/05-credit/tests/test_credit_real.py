"""The business credit and monitoring template on the real published tables
(slow), through the shape's own command line (`python -m products.report
render REF --template credit`), as a credit team's memo is made. Subjects
are taken from the tables at run time, never fixed, so the test follows the
data: a company whose directors changed between the two monthly files and
that has a Gazette liquidation; a company first shown in the latest file; a
director of the first. Every memo carries the builder's common flags once
and is not refused by the shape's presentation rules. Imports nothing of
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
CHANGES = "WHAT CHANGED, MONTH BY MONTH: DIRECTORS, HOLDERS OF RECORD AND REGISTERED OFFICES, EACH DATED BY THE FILE THAT FIRST SHOWS IT"
PEOPLE = "ITS PEOPLE: THE PEOPLE BESIDE THEM, AND THEIR SOCIETY AND CHARITY ROLES"
LATEST = "(select max(last_file) from pub.directors)"
CHANGED_AND_LIQUIDATED = f"""
    select 'companies:' || c.key from pub.companies c
    where c.in_latest
      and exists (select 1 from pub.directors d where d.entity_key = c.key and not d.in_latest)
      and exists (select 1 from pub.directors d where d.entity_key = c.key and d.first_file = {LATEST})
      and exists (select 1 from pub.gazette_liquidations l where l.register_key = c.key)
    order by c.key limit 1"""
NEW_IN_LATEST = f"""
    select 'companies:' || c.key from pub.companies c
    where c.first_file = {LATEST} and c.status = 'Registered' and c.registered_on >= current_date - 365
      and exists (select 1 from pub.directors d where d.entity_key = c.key)
    order by c.key limit 1"""


def one(sql: str) -> str:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got[0]


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "credit"], cwd=REPO,
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
    assert "could not run" not in text, "a rule broke on real rows"
    return {"text": text, "flags": flags, "sections": sections}


def test_a_company_whose_directors_changed_lists_each_change_by_its_file_and_its_liquidation():
    ref = one(CHANGED_AND_LIQUIDATED)
    m = memo(ref)
    f = m["flags"]["monthly-changes"]
    assert f["status"] == "fired" and " left as " in f["text"] and " arrived as " in f["text"], f
    assert "a month and not a day" in f["text"] and "read from the earlier states" in f["text"]
    assert m["flags"]["insolvency-notices"]["status"] == "fired" and m["flags"]["insolvency-notices"]["severity"] == "red"
    assert m["flags"]["officer-churn"]["status"] == "fired"
    assert m["sections"][CHANGES]["confirmed"] >= 2
    for name in ("people-failed-companies", "prohibition", "bankruptcy", "other-current-companies"):
        f = m["flags"][name]   # from a company the officers the walk followed are read (2 November 2026): a clear says how many
        assert "start a report from each person" not in f["text"] and "officer" in f["text"], (name, f["text"][:200])
        assert f["status"] != "clear" or "officer(s) the walk followed one step" in f["text"], name
    for name in ("since-date", "interface-freshness", "securities-register", "insolvency-register", "credit-bureau"):
        assert m["flags"][name]["status"] == "blocked", name


def test_a_company_first_shown_in_the_latest_file_is_a_change_and_young():
    m = memo(one(NEW_IN_LATEST))
    assert m["flags"]["young-entity"]["status"] == "fired"
    f = m["flags"]["monthly-changes"]
    assert f["status"] == "fired" and "first shown in the" in f["text"], f
    assert m["flags"]["entity-status"]["status"] == "clear"


def test_a_director_of_that_company_reads_the_persons_companies_and_the_people_beside_are_near():
    company = one(CHANGED_AND_LIQUIDATED)
    key = company.split(":", 1)[1]
    ref = one(f"select 'companies:' || key from pub.directors where entity_key = '{key}' and in_latest and not suppressed order by key limit 1")
    m = memo(ref)
    assert m["flags"]["insolvency-notices"]["status"] == "fired"
    assert m["flags"]["officer-churn"]["status"] == "blocked" and m["flags"]["entity-status"]["status"] == "blocked"
    assert all(x.startswith("  - [near]") for x in m["sections"][PEOPLE]["lines"] if "DIRECTOR of" in x or "shareholder of record" in x), \
        "a connection through another person is never confirmed"


TURNED = """
    select 'companies:' || c.key from pub.companies c join pub.company_states s on s.entity_key = c.key
    where c.in_latest and s.status ilike 'registered' and c.status ilike 'in liquidation'
    order by c.key limit 1"""


def test_a_company_a_later_file_put_into_liquidation_is_a_red_status_change_on_the_real_rows():
    """Read on the real tables (1 November 2026): an earlier state in pub.company_states reaches the report, and a status that
    turned to liquidation between the files is red in status-name-changes and recent-adverse-change and listed in monthly-changes."""
    m = memo(one(TURNED))
    f = m["flags"]
    assert f["status-name-changes"]["status"] == "fired" and f["status-name-changes"]["severity"] == "red", f["status-name-changes"]
    assert "status changed: Registered in the July 2026 file" in f["status-name-changes"]["text"]
    assert f["recent-adverse-change"]["status"] == "fired" and f["recent-adverse-change"]["severity"] == "red"
    assert "status changed" in f["monthly-changes"]["text"]
