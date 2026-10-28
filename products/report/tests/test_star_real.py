"""The name-only star read through its centre, against the real published
tables (slow): from every component of a Gazette prohibition's star the walk
reaches the prohibition row, and a spoke of the largest star the subject's
templates read reaches more namesakes than the centre alone. Rows are taken
from the tables at run time; nothing is printed but refs' counts."""
import pytest

from products.report import catalogue as cat
from products.report import db, walk

pytestmark = pytest.mark.slow


def reached(conn, ref: str) -> set:
    g = walk.group_of(conn, ref)
    L = walk.links_of(conn, [ref] + [r for r in g["rows"] if r != ref])
    return {l["other"] for l in L["near"] + L["confirmed"]}


def test_a_prohibition_row_that_is_a_spoke_is_reached_from_every_other_spoke():
    with db.read_connect() as conn:
        got = db.rows(conn, """select p.ref, min(case when l.row_a = p.ref then l.row_b else l.row_a end) as centre
            from (select 'gazette:' || key as ref from pub.gazette_prohibitions) p
            join pub.links l on l.rule = %s and (l.row_a = p.ref or l.row_b = p.ref)
            group by p.ref having count(*) = 1 order by p.ref limit 20""", (walk.NAME_ONLY,))
        tried = 0
        for x in got:
            spokes = [r["s"] for r in db.rows(conn, "select case when row_a = %s then row_b else row_a end as s from pub.links "
                                                    "where rule = %s and (row_a = %s or row_b = %s)", (x["centre"],) + (walk.NAME_ONLY, x["centre"], x["centre"]))]
            if len(spokes) < 3:
                continue   # a star of the centre and this row alone: nothing to reach through it
            tried += 1
            for s in spokes[:10]:
                if s != x["ref"]:
                    assert x["ref"] in reached(conn, s), (x["ref"], s)
            if tried >= 3:
                break
        assert tried, "no prohibition row is a spoke of a star of three or more today"


def test_a_spoke_of_the_largest_star_lists_namesakes_beyond_the_centre():
    with db.read_connect() as conn:
        centre = db.rows(conn, """select c from (select row_a as c from pub.links where rule = %s union all
                                  select row_b from pub.links where rule = %s) s group by c order by count(*) desc, c limit 1""",
                         (walk.NAME_ONLY, walk.NAME_ONLY))[0]["c"]
        spoke = db.rows(conn, "select s from (select case when row_a = %s then row_b else row_a end as s from pub.links where rule = %s "
                              "and (row_a = %s or row_b = %s) and (row_a like 'companies:%%' or row_b like 'companies:%%') "
                              ') x order by s collate "C" limit 1', (centre, walk.NAME_ONLY, centre, centre))
        assert spoke
        w = walk.walk(conn, spoke[0]["s"], {v.name for v in cat.VIEWS})
        star = [it for it in w["near"] if it.get("path")]
        assert len(star) > 1 and all(it["grade"] == "near" and it["path"][1] == centre for it in star)
        assert len({it["ref"] for it in star}) == len(star)
