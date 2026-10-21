"""Against the real published tables and this session's scan tables (slow):
the two proving scans run, their lines cite rows that exist today, the
planted wrong key is caught by the check, the stale rule answers, and a
run over a whole-register join records its time."""
import pytest

from products.scan import check, db, lines as L, run as R, state, template as tpl

pytestmark = pytest.mark.slow


def test_the_two_proving_scans_run_and_every_citation_resolves_and_a_planted_key_is_caught():
    with db.pub_connect() as pub, db.state_connect() as st_w:
        pub.autocommit = True
        if not db.has_relation(st_w, db.state_target()[1], "runs"):
            state.apply()
    for name in ("society-officers-liquidations", "donors-named-as-companies"):
        out = R.run(tpl.by_name(name), limit=40, note="test", log=lambda s: None)
        assert out["lines"] > 0 and out["problems"] == [] and out["seconds"] < 300
        assert all(v["loaded_at"] for v in out["views"])
        with db.pub_connect() as pub, db.state_read_connect() as st:
            pub.autocommit = True
            cites = state.citations(st, out["run_id"])
            assert cites and check.citations_resolve(pub, cites) == []
            bad = [dict(cites[0], key=cites[0]["key"] + "-not-a-row")]
            assert len(check.citations_resolve(pub, bad)) == 1
            lines, total = state.lines(st, out["run_id"], 1, 10)
            assert total == out["lines"] and len(lines) == min(10, total) and all(s["cite"] for ln in lines for s in ln["steps"])
    d = R.run(tpl.by_name("donors-named-as-companies"), limit=40, note="test", log=lambda s: None)
    assert d["grades"]["near"] == d["lines"]
    s = R.run(tpl.by_name("society-officers-liquidations"), limit=40, note="test", log=lambda s: None)
    assert s["grades"]["confirmed"] + s["grades"]["contested"] == s["lines"]


def test_the_stale_rule_answers_for_every_scan():
    with db.pub_connect() as pub, db.state_read_connect() as st:
        pub.autocommit = True
        got = R.stale(pub, st)
    assert {x["scan"] for x in got} == set(tpl.folders())
    for x in got:
        assert x["never_run"] or isinstance(x["stale"], list)


def test_a_suppressed_director_row_if_any_is_titled_suppressed_through_the_line_builder():
    from products.scan import views as cat
    with db.pub_connect() as pub:
        pub.autocommit = True
        got = db.rows(pub, "select key, full_name, suppressed, appointed_on, ended_on, first_file, last_file from pub.directors where coalesce(suppressed, false) limit 1")
    if not got:
        pytest.skip("no suppressed director row today")
    v = cat.BY_NAME["directors"]
    assert L.title(v, got[0]) == L.SUPPRESSED
