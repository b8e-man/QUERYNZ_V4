"""The recruitment template on the real published tables (slow), through the
shape's own command line (`python -m products.report render REF --template
recruitment`), as a consultant's memo is made. Subjects are taken from the
tables at run time, never fixed, so the test follows the data: a director
confirmed to a prohibition notice, a director whose company has only a
removal notice, and a director under the first and last name the most
people share. Every memo carries the builder's common flags (group-standing,
hubs-met, replaced-return) once, and no copy of them. Imports nothing of
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
HEADING = re.compile(r"^([A-Z][A-Z ,']+?)  \((\d+) confirmed, (\d+) near\)$")


def one(sql: str) -> str:
    with sdb.connect(sdb.READ_KEY, "querynz_v4", options="-c statement_timeout=60000", autocommit=True) as conn:
        got = conn.execute(sql).fetchone()
    assert got and got[0], sql
    return got[0]


def memo(ref: str) -> dict:
    out = subprocess.run([sys.executable, "-m", "products.report", "render", ref, "--template", "recruitment"], cwd=REPO,
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
    assert "identity" not in flags, "the template's copy of group-standing is gone"
    return {"text": text, "flags": flags, "sections": sections}


def test_a_director_confirmed_to_a_prohibition_gets_a_red_flag_and_the_notice_is_listed_confirmed():
    ref = one("""
        select min(n.ref) filter (where n.view = 'directors') from pub.groups g join pub.names n on n.ref = g.row_key
        where g.group_id in (select g2.group_id from pub.groups g2 join pub.names n2 on n2.ref = g2.row_key
                             where n2.view = 'gazette_prohibitions' and not coalesce(g2.contested, false))
        group by g.group_id having count(*) filter (where n.view = 'directors') between 1 and 3
        order by 1 limit 1""")
    m = memo(ref)
    p = m["flags"]["prohibition"]
    assert p["status"] == "fired" and p["severity"] == "red"
    assert ("in force on" in p["text"]) or ("ended before" in p["text"])
    gazette = m["sections"]["GAZETTE INSOLVENCY, BANKRUPTCY AND PROHIBITION NOTICES"]
    assert any("[confirmed]" in x and "prohibition" in x for x in gazette["lines"])


def test_a_company_with_only_a_removal_notice_is_not_an_insolvency():
    ref = one("""
        select 'companies:' || d.key from pub.gazette_company_notices n
        join pub.directors d on d.entity_key = n.register_key and d.in_latest and not coalesce(d.suppressed, false)
        left join pub.groups g on g.row_key = 'companies:' || d.key
        where n.kind = 'removal' and g.row_key is null
          and not exists (select 1 from pub.gazette_company_notices x where x.register_key = n.register_key and x.kind <> 'removal')
          and not exists (select 1 from pub.gazette_liquidations x where x.register_key = n.register_key)
        limit 1""")
    m = memo(ref)
    assert m["flags"]["liquidation-history"]["status"] == "clear"
    assert m["flags"]["register-removals"]["status"] == "fired" and m["flags"]["register-removals"]["severity"] == "info"


MOST_SHARED = """
    with pair as (select lower(first_name) f, lower(last_name) l from pub.directors where in_latest
                  group by 1, 2 order by count(distinct lower(coalesce(middle_names, ''))) desc limit 1)
    select 'companies:' || min(d.key) from pub.directors d join pair on lower(d.first_name) = pair.f and lower(d.last_name) = pair.l
    where d.in_latest and not coalesce(d.suppressed, false) and d.middle_names is not null"""


def test_the_most_shared_name_keeps_its_namesakes_apart_and_never_confirmed():
    m = memo(one(MOST_SHARED))
    ident = m["sections"]["WHO THIS IS, AND THE NAMESAKES SET APART"]
    assert ident["confirmed"] == 0
    assert all(x.startswith("  - [near]") for x in ident["lines"])
    assert m["flags"]["namesake-exposure"]["status"] == "fired"
    assert m["flags"]["bankruptcy"]["status"] == "blocked"
    marks = m["flags"]["charity-integrity-marks"]   # read since fix-templates-1: an officer row by name is near, so a mark on one is amber
    assert marks["status"] == "clear" or (marks["status"] == "fired" and marks["severity"] == "amber"), marks
    assert "not held: Charities register and officers" not in m["text"]   # held since charities-3; the key superseded at fix-report-2


@pytest.mark.xfail(strict=True, reason="cards/the-report-walk-reads-a-namesake-star-one-hop-so-a-spoke-sees-only-the-centre.md: since 28 October the "
                                        "name-only@1 star is centred on a building practitioner row, so the subject's group holds one near link, "
                                        "to a view the template does not read; the walk must follow the star through its centre")
def test_the_most_shared_name_lists_its_namesakes_whichever_row_carries_the_star():
    ident = memo(one(MOST_SHARED))["sections"]["WHO THIS IS, AND THE NAMESAKES SET APART"]
    assert ident["near"] > 0
