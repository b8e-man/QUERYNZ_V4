"""The beneficial ownership and AML checks on the real published tables
(slow), through the shape's own command line (`python -m products.report
render REF --template ownership`), as an analyst's memo is made. Subjects
are taken from the tables at run time, never fixed: a registered company
with a company holder and a nominee holder, and a removed company with no
holder. Every memo carries the builder's common flags once, is not refused
by the presentation rules, and never clears the sanctions check or names
anyone for whom shares are held. Imports nothing of products.report."""
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


def one(sql: str) -> str:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got[0]


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "ownership"], cwd=REPO,
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
    assert flags["sanctions-lists"]["status"] == "blocked" and "not held: Sanctions lists" in text
    assert flags["ultimate-holders"]["status"] == "blocked"
    return {"text": text, "flags": flags}


def test_a_company_with_a_company_holder_and_a_nominee_names_both_and_stops():
    ref = one("""with n as (select distinct entity_key from pub.shareholders
                            where in_latest and shareholder_type = 'company' and name like '%NOMINEES LIMITED' limit 200)
                 select 'companies:' || min(c.key) from n join pub.companies c on c.key = n.entity_key
                 where c.status = 'Registered' and (select count(*) from pub.shareholders s where s.entity_key = c.key) < 30""")
    m = memo(ref)
    chain = m["flags"]["holding-chain"]
    assert chain["status"] == "fired" and "the registers reach 1" in chain["text"] and "shares filed for the holding" in chain["text"]
    assert m["flags"]["custodial-holders"]["status"] == "fired" and "holder of record" in m["flags"]["custodial-holders"]["text"]
    for name in ("prohibition", "public-office"):
        assert m["flags"][name]["status"] == "blocked", "from a company its people are not followed"


def test_a_removed_company_with_no_holder_blocks_the_chain():
    ref = one("""select 'companies:' || min(c.key) from pub.companies c
                 where c.status = 'Removed' and c.registered_on > '2015-01-01'
                   and not exists (select 1 from pub.shareholders s where s.entity_key = c.key)""")
    m = memo(ref)
    assert m["flags"]["holding-chain"]["status"] == "blocked" and "not a finding" in m["flags"]["holding-chain"]["text"]
    assert m["flags"]["company-status"]["status"] == "fired"
