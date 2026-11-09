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
        # the walk's own query shape (row_a = any or row_b = any): a join on pub.links with an OR times out since the
        # land titles' links (9 November 2026)
        refs = [r["ref"] for r in db.rows(conn, "select 'gazette:' || key as ref from pub.gazette_prohibitions")]
        ends = {}
        for l in db.rows(conn, "select row_a, row_b from pub.links where rule = %s and (row_a = any(%s) or row_b = any(%s))",
                         (walk.NAME_ONLY, refs, refs)):
            for me, other in ((l["row_a"], l["row_b"]), (l["row_b"], l["row_a"])):
                if me in refs:
                    ends.setdefault(me, []).append(other)
        got = [{"ref": ref, "centre": os[0]} for ref, os in sorted(ends.items()) if len(os) == 1][:20]
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
        # the largest star among a bounded sample of the rule's links leaving a company's row: a count over every
        # name-only link times out since the land titles' links (9 November 2026)
        import collections
        sample = db.rows(conn, "select row_a, row_b from pub.links where rule = %s and row_a like 'companies:%%' limit 5000", (walk.NAME_ONLY,))
        seen = collections.Counter(r for l in sample for r in (l["row_a"], l["row_b"]))
        spoke = []
        for centre in sorted(seen, key=lambda r: (-seen[r], r))[:20]:      # the largest with a company's row among its spokes
            spoke = sorted(({"s": l["row_b"] if l["row_a"] == centre else l["row_a"]}
                            for l in db.rows(conn, "select row_a, row_b from pub.links where rule = %s and (row_a = any(%s) or row_b = any(%s))",
                                             (walk.NAME_ONLY, [centre], [centre]))
                            if (l["row_b"] if l["row_a"] == centre else l["row_a"]).startswith("companies:")),
                           key=lambda x: x["s"].encode())[:1]
            if spoke:
                break
        assert spoke
        w = walk.walk(conn, spoke[0]["s"], {v.name for v in cat.VIEWS})
        star = [it for it in w["near"] if it.get("path")]
        assert len(star) > 1 and all(it["grade"] == "near" and it["path"][1] == centre for it in star)
        assert len({it["ref"] for it in star}) == len(star)
