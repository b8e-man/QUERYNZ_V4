"""Healthcare operator governance on the real published tables (slow),
through the shape's own command line (`python -m products.report render REF
--template healthcare`), as an investor's memo is made. Subjects are taken
from the tables at run time, never fixed, so the test follows the data: a
care-named company with a small board, one of whose directors also sits,
by a confirmed link, on another care-named company that does not share its
leading name word; a charitable trust board, whose trustees the companies
register does not list; and a care-named company with a Gazette
liquidation. Every memo carries the builder's common flags once, is not
refused, breaks no rule, and blocks every charity check and every register
not held. Imports nothing of products.report (the one-way test)."""
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
CARE = r"'(rest home|lifecare|healthcare|retirement|village)'"
NOT_HELD = ("retirement-villages", "hdc-decisions", "certification-audits", "provider-registers", "aged-care-commissioner", "court-judgments",
            "past-roles", "charity-arm", "charity-returns", "charity-audit-opinion", "charity-return-filed")
#: a care-named company with two to six current directors, one of whom has a confirmed row as director of another care-named company
OVERLAP = f"""
    with c as (select c.key, c.name from pub.companies c where c.status = 'Registered' and c.name ~* {CARE} and c.name !~ '^[0-9]'
               and (select count(*) from pub.directors d where d.entity_key = c.key and d.in_latest) between 2 and 6)
    select 'companies:' || c.key from c
    join pub.directors d on d.entity_key = c.key and d.in_latest
    join pub.groups g on g.row_key = 'companies:' || d.key
    join pub.groups g2 on g2.group_id = g.group_id and g2.row_key <> g.row_key
    join pub.directors d2 on 'companies:' || d2.key = g2.row_key and d2.in_latest and d2.entity_key <> c.key
    join pub.companies c2 on c2.key = d2.entity_key and c2.name ~* {CARE} and split_part(c2.name, ' ', 1) <> split_part(c.name, ' ', 1)
    order by c.key limit 1"""
TRUST_BOARD = f"select 'companies:' || key from pub.companies where entity_type = 'Charitable Trust Boards' and status = 'Registered' and name ~* {CARE} order by key limit 1"
LIQUIDATED = f"""
    select 'companies:' || c.key from pub.companies c join pub.gazette_liquidations l on l.register_key = c.key
    where c.name ~* {CARE} and c.name !~ '^[0-9]' order by l.appointed_on desc nulls last, c.key limit 1"""


def row(sql: str) -> tuple:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "healthcare"], cwd=REPO,
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
    line = [x for x in text.splitlines() if x.startswith("  not held: The retirement villages file") and "Court judgments" in x]
    assert "WHAT IS NOT HELD" in text and line, "the not-held section's line names the health keys, then the courts"
    assert all(n in line[0] for n in ("Health and Disability Commissioner decisions", "Certification audits", "provider registers",
                                      "Aged Care Commissioner"))
    assert "not held: Charities register and officers" not in text   # held since charities-3; the key superseded at fix-report-2
    return {"text": text, "flags": flags}


def test_an_officer_on_another_care_named_operator_raises_the_overlap_with_both_roles_dated():
    m = memo(row(OVERLAP)[0])
    f = m["flags"]["officer-overlap"]
    assert f["status"] == "fired" and f["severity"] in ("amber", "info"), f
    assert re.search(r"of the entity, from \d{4}-\d\d-\d\d\): \d+ other current role", f["text"]) and "a sign to read, not a finding" in f["text"]
    assert "OFFICER OVERLAP: THE SAME PEOPLE ON OTHER COMPANIES" in m["text"] and "rule through-officer" in m["text"]


def test_a_charitable_trust_board_lists_no_officer_and_clears_no_officer_check():
    m = memo(row(TRUST_BOARD)[0])
    for name in ("disqualified-officer", "officer-bankruptcy", "officer-overlap", "officer-company-notices"):
        assert m["flags"][name]["status"] == "blocked" and "trustees are filed with the Charities Register" in m["flags"][name]["text"], name


def test_a_liquidated_care_company_is_red_on_its_own_record():
    m = memo(row(LIQUIDATED)[0])
    assert m["flags"]["insolvency-notice"]["status"] == "fired" and m["flags"]["insolvency-notice"]["severity"] == "red"
    assert re.search(r"^\d+ Gazette insolvency notice\(s\) on the entity, earliest first: [a-z -]+, (appointed|to be heard|published) \d{1,2} \w+ \d{4}",
                     m["flags"]["insolvency-notice"]["text"])
