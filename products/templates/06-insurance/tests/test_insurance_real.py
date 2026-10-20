"""Insurance underwriting on the real published tables (slow), through the
shape's own command line (`python -m products.report render REF --template
insurance`), as an underwriter's memo is made. Subjects are taken from the
tables at run time, never fixed, so the test follows the data: a director in
an uncontested group, not a hub, appointed before a liquidator was appointed
to the company and still listed; that liquidated company itself, whose people
are not followed; and a going company with directors appointed this year. A
company whose name reads as a street address is skipped: the shape refuses
any report that meets one (carded on the report lane). Every memo carries
the builder's common flags once, is not refused, and blocks the safety
record. Imports nothing of products.report (the one-way test)."""
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
SAFETY = ("safety-record", "regulator-actions", "court-judgments", "tribunals", "change-history", "status-history", "mortgagee-possession",
          "insolvency-register", "securities-register")
#: (director ref, liquidated company key): a director appointed before the liquidator, in a small uncontested group
HELD_AT = f"""
    with f as (select register_key, min(appointed_on) failed_on from pub.gazette_liquidations where register_key is not null
               and appointed_on is not null group by 1),
         grp as (select g.group_id from pub.groups g group by 1 having count(*) between 2 and 12 and not bool_or(coalesce(g.contested, false)))
    select 'companies:' || d.key, f.register_key from f
    join pub.companies c on c.key = f.register_key and c.status = 'In Liquidation' and {NOT_ADDRESS}
    join pub.directors d on d.entity_key = f.register_key and d.in_latest and d.appointed_on < f.failed_on
    join pub.groups g on g.row_key = 'companies:' || d.key join grp using (group_id)
    order by f.register_key desc limit 1"""
CHURN = f"""
    select 'companies:' || c.key from pub.companies c join pub.directors d on d.entity_key = c.key and d.in_latest
    where c.status = 'Registered' and c.registered_on < current_date - 1000 and {NOT_ADDRESS} and d.appointed_on > current_date - 300
    group by c.key having count(*) >= 3 order by c.key limit 1"""


def row(sql: str) -> tuple:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "insurance"], cwd=REPO,
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
    for name in SAFETY:
        assert flags[name]["status"] == "blocked", name
    assert "THE SAFETY RECORD: WHAT IS NOT HELD" in text and "not held: Court judgments" in text
    return {"text": text, "flags": flags}


@pytest.fixture(scope="module")
def held_at():
    return row(HELD_AT)


def test_a_director_on_the_board_when_the_liquidator_was_appointed_raises_the_sister_company_flag(held_at):
    m = memo(held_at[0])
    f = m["flags"]["sister-company-failure"]
    hub = m["flags"]["subject-hub"]["status"] == "fired"
    assert f["status"] == "fired" and f["severity"] == ("amber" if hub else "red"), f
    assert "on or before the failure date and still listed" in f["text"] and re.search(r"appointed \d{1,2} \w+ \d{4}", f["text"])
    assert m["flags"]["prohibition"]["status"] in ("clear", "fired", "blocked") and m["flags"]["officer-churn"]["status"] == "blocked"


def test_from_the_liquidated_company_its_record_is_red_and_its_people_are_not_cleared(held_at):
    m = memo(f"companies:{held_at[1]}")
    assert m["flags"]["entity-status"]["status"] == "fired" and m["flags"]["entity-status"]["severity"] == "red"
    assert m["flags"]["insolvency-event"]["status"] == "fired" and m["flags"]["insolvency-event"]["severity"] == "red"
    for name in ("sister-company-failure", "other-current-companies", "prohibition", "bankruptcy"):
        assert m["flags"][name]["status"] != "clear", f"{name} cleared from a company whose people it never followed"


def test_a_board_with_three_directors_appointed_this_year_raises_officer_churn_and_never_clears():
    m = memo(row(CHURN)[0])
    f = m["flags"]["officer-churn"]
    assert f["status"] == "fired" and f["severity"] == "amber" and "appointed in the 365 days" in f["text"]
    assert "a director who left the board before July 2026 is not seen" in f["text"]
