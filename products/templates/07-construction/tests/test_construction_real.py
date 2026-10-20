"""Subcontractor vetting and phoenix detection on the real published tables
(slow), through the shape's own command line (`python -m products.report
render REF --template construction`), as a procurement lead's memo is made.
Subjects are taken from the tables at run time, never fixed, so the test
follows the data: a director in an uncontested group, not a hub, who sits on
a company liquidated and on a going company registered within the window;
that going company, from which the people are not followed; the liquidated
company itself; and a going company that only shares a name with a company
liquidated within the window. A company whose name reads as a street address
is skipped: the shape refuses any report that meets one (carded on the
report lane). Every memo carries the builder's common flags once and is not
refused. Imports nothing of products.report (the one-way test)."""
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
NOT_ADDRESS = "c.name !~ '^[0-9]'"
#: (director ref, failed company key, going company key): the first in key order
PAIR = f"""
    with f as (select register_key, min(coalesce(appointed_on, published_on)) failed_on from pub.gazette_liquidations
               where register_key is not null group by 1),
         grp as (select g.group_id from pub.groups g group by 1 having count(*) between 2 and 12 and not bool_or(coalesce(g.contested, false))),
         fd as (select g.group_id, f.register_key, f.failed_on from f join pub.companies fc on fc.key = f.register_key and fc.status = 'In Liquidation'
                join pub.directors d on d.entity_key = f.register_key and d.in_latest
                join pub.groups g on g.row_key = 'companies:' || d.key join grp using (group_id)),
         cd as (select g.group_id, c.key, c.registered_on, d.key as dkey from pub.directors d join pub.groups g on g.row_key = 'companies:' || d.key
                join grp using (group_id) join pub.companies c on c.key = d.entity_key where c.status = 'Registered' and d.in_latest and {NOT_ADDRESS})
    select 'companies:' || cd.dkey, fd.register_key, cd.key from fd join cd using (group_id)
    where cd.key <> fd.register_key and cd.registered_on between fd.failed_on - 300 and fd.failed_on + 300
    order by cd.key limit 1"""
SAME_NAME = f"""
    with f as (select 'companies:' || register_key as ref, min(coalesce(appointed_on, published_on)) failed_on from pub.gazette_liquidations
               where register_key is not null group by 1),
         p as (select row_a, row_b from pub.links where rule like 'company-name%' and (row_a in (select ref from f) or row_b in (select ref from f))),
         q as (select case when p.row_a = f.ref then p.row_b else p.row_a end as other, f.failed_on from p join f on f.ref in (p.row_a, p.row_b))
    select q.other from q join pub.companies c on 'companies:' || c.key = q.other
    where c.status = 'Registered' and {NOT_ADDRESS} and c.registered_on between q.failed_on - 300 and q.failed_on + 300
    limit 1"""


def row(sql: str) -> tuple:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "construction"], cwd=REPO,
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
    return {"text": text, "flags": flags}


@pytest.fixture(scope="module")
def pair():
    return row(PAIR)


def test_a_director_on_a_liquidated_and_a_new_company_raises_the_phoenix_flag(pair):
    m = memo(pair[0])
    f = m["flags"]["phoenix-signature"]
    hub = m["flags"]["subject-hub"]["status"] == "fired"
    assert f["status"] == "fired" and f["severity"] == ("amber" if hub else "red"), f
    assert "the window is 365 days either side" in f["text"] and re.search(r"registered \d{4}-\d\d-\d\d, \d+ days (after|before)", f["text"])
    assert m["flags"]["insolvency-notices"]["status"] == "fired"
    for name in ("building-practitioners", "insolvency-register", "court-judgments", "employment-determinations", "change-history"):
        assert m["flags"][name]["status"] == "blocked", name
    assert "not held: Licensed building practitioners" in m["text"]


def test_from_the_new_company_the_people_are_listed_and_the_signature_blocks(pair):
    m = memo(f"companies:{pair[2]}")
    for name in ("phoenix-signature", "repeat-failure", "other-current-companies", "prohibition", "bankruptcy"):
        assert m["flags"][name]["status"] in ("blocked", "fired"), name
        assert m["flags"][name]["status"] != "clear", f"{name} cleared from a company whose people it never followed"
    assert "start a report from each person listed" in m["flags"]["phoenix-signature"]["text"] or m["flags"]["phoenix-signature"]["status"] == "fired"


def test_the_failed_company_itself_is_red(pair):
    m = memo(f"companies:{pair[1]}")
    assert m["flags"]["entity-status"]["status"] == "fired" and m["flags"]["entity-status"]["severity"] == "red"
    assert m["flags"]["insolvency-notices"]["status"] == "fired" and m["flags"]["insolvency-notices"]["severity"] == "red"


def test_a_company_that_only_shares_a_failed_companys_name_is_never_red():
    m = memo(row(SAME_NAME)[0])
    f = m["flags"]["same-name-failed"]
    assert f["status"] == "fired" and f["severity"] in ("info", "amber") and "never one firm or one person" in f["text"]
    assert not (m["flags"]["phoenix-signature"]["status"] == "fired" and "share" not in m["flags"]["phoenix-signature"]["text"])
