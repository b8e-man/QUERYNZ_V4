"""Property developer due diligence on the real published tables (slow),
through the shape's own command line (`python -m products.report render REF
--template property`), as a buyer's memo is made. Subjects are taken from
the tables at run time, never fixed, so the test follows the data: a going
development company one of whose directors, by a confirmed link, sits on
two or more companies in liquidation or receivership; a company the
Gazette has put into liquidation that the latest monthly file still calls
Registered; and a company named as mortgagor in a mortgagee's entry into
possession. Every memo carries the builder's common flags once, is not
refused, breaks no rule, and blocks every register not held. Imports
nothing of products.report (the one-way test)."""
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
NOT_HELD = ("land-titles", "overseas-investment", "building-consents", "court-judgments", "securities-register", "insolvency-register",
            "real-estate-authority", "building-practitioners", "past-roles")
#: a going development company with one to four current directors, one of whom has confirmed rows as director of two or more
#: companies in liquidation or receivership
SERIAL = """
    with c as (select c.key from pub.companies c where c.status = 'Registered' and c.name ~* 'develop' and c.name !~ '^[0-9]'
               and (select count(*) from pub.directors d where d.entity_key = c.key and d.in_latest) between 1 and 4)
    select 'companies:' || c.key from c
    join pub.directors d on d.entity_key = c.key and d.in_latest
    join pub.groups g on g.row_key = 'companies:' || d.key
    join pub.groups g2 on g2.group_id = g.group_id and g2.row_key <> g.row_key
    join pub.directors d2 on 'companies:' || d2.key = g2.row_key and d2.in_latest and d2.entity_key <> c.key
    join pub.companies c2 on c2.key = d2.entity_key and c2.status ~* 'liquidation|receivership'
    group by c.key having count(distinct c2.key) >= 2 order by c.key limit 1"""
#: a company with a Gazette liquidation the latest file does not show yet
NEWER = """
    select 'companies:' || c.key from pub.companies c join pub.gazette_liquidations l on l.register_key = c.key
    where c.status = 'Registered' and c.name !~ '^[0-9]' order by l.appointed_on desc nulls last, c.key limit 1"""
POSSESSED = """
    select 'companies:' || p.mortgagor_register_key from pub.gazette_possessions p join pub.companies c on c.key = p.mortgagor_register_key
    order by p.entered_on desc nulls last, p.key limit 1"""


def row(sql: str) -> tuple:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "property"], cwd=REPO,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    text = out.stdout
    assert "NOT FOUND" not in text, text[:400]
    assert "REFUSED" not in text, text[text.index("REFUSED"):][:1200]
    flags = {}
    for line in text.splitlines():
        m = FLAG.match(line)
        if m:
            flags[m.group(3)] = {"status": m.group(1).lower(), "severity": m.group(2), "text": m.group(4)}
    for name in COMMON:
        assert len(re.findall(rf"^  (?:FIRED|CLEAR|BLOCKED)\s+\w+\s+{name}@", text, re.M)) == 1, name
    assert "could not run" not in text, "a rule broke on real rows"
    for name in NOT_HELD:
        assert flags[name]["status"] == "blocked", name
    for name in ("serial-pattern", "earlier-failure", "possession", "insolvency-notices"):
        assert flags[name]["status"] != "clear", f"{name} cleared: past roles are not held"
    assert "WHAT IS NOT HELD" in text and re.search(r"^  not held: LINZ titles, Overseas Investment Office decisions, Building consents, code compliance certificates and "
                                                   r"council minutes, Court judgments, .*Real Estate Authority decisions", text, re.M)
    return {"text": text, "flags": flags}


def test_a_director_with_two_failed_companies_raises_the_serial_pattern_with_each_gap_in_days():
    m = memo(row(SERIAL)[0])
    f = m["flags"]["serial-pattern"]
    assert f["status"] == "fired" and f["severity"] in ("amber", "info"), f
    assert re.search(r"\d+ of \d+ companies failed \(\d+ an insolvency", f["text"]) and "days from registration" in f["text"]
    assert "no window is set, so every gap is shown" in f["text"] and "start a report from the director" in f["text"]
    assert "THE PRINCIPALS' OTHER COMPANIES: THE PROJECT HISTORY, NEWEST FIRST" in m["text"] and "rule through-officer" in m["text"]


def test_a_liquidation_newer_than_the_file_is_red_on_the_entity():
    m = memo(row(NEWER)[0])
    f = m["flags"]["entity-status"]
    assert f["status"] == "fired" and f["severity"] == "red" and "newer than the file" in f["text"], f


def test_a_mortgagee_possession_on_the_entity_is_red_and_dated_by_entry():
    m = memo(row(POSSESSED)[0])
    f = m["flags"]["possession"]
    assert f["status"] == "fired" and f["severity"] == "red" and "entered " in f["text"] and "the mortgagor is the entity itself" in f["text"], f
