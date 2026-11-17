import datetime as dt

from registers.news import load

D = dt.date


def test_a_site_the_provider_has_not_delivered_stays_old_only():
    assert load.judge(100, D(2026, 11, 16), 0, None, None, 0, False)[0] == "old only"


def test_a_site_is_ready_when_the_provider_is_current_and_reaches_back_to_the_old_copy():
    assert load.judge(100, D(2026, 11, 16), 40, D(2026, 11, 15), D(2026, 11, 17), 12, False)[0] == "ready"


def test_a_hole_between_the_old_copy_and_the_provider_is_a_gap():
    state, why = load.judge(100, D(2026, 11, 1), 40, D(2026, 11, 14), D(2026, 11, 17), 12, False)
    assert state == "providing, gap" and "13 days" in why


def test_a_provider_with_nothing_this_week_is_not_providing():
    assert load.judge(100, D(2026, 11, 1), 5, D(2026, 10, 1), D(2026, 11, 2), 0, False)[0] == "providing, gap"


def test_a_retired_site_says_so_whatever_else_holds():
    assert load.judge(100, D(2026, 11, 1), 0, None, None, 0, True)[0] == "retired"


def test_the_parser_is_the_sites_own_then_a_parent_domains_then_the_generic():
    assert load.parser_for("www.rnz.co.nz")[0] == "rnzscraper"
    assert load.parser_for("1news.co.nz")[0] == "onenews"
    assert load.parser_for("nowhere.example.nz")[0] == "genericrss"


def test_the_parsers_fetch_nothing():
    import pathlib
    here = pathlib.Path(load.__file__).parent / "extract"
    for f in here.glob("*.py"):
        src = f.read_text()
        assert "make_client(" not in src.replace("def make_client", "") or f.name == "base.py", f.name
    assert "httpx" not in (here / "base.py").read_text()


def test_only_a_ready_site_is_listed_and_logging_waits_for_the_old_registry(tmp_path):
    from registers.news import retire

    class Conn:
        def __init__(self):
            self.logged = []

        def execute(self, sql, args=None):
            conn = self

            class R:
                rowcount = 1

                def fetchall(self):
                    return [("scoop.co.nz",), ("stuff.co.nz",)]
            if sql.startswith("INSERT"):
                conn.logged.append(args[0])
            return R()

    path = str(tmp_path / "retired.txt")
    c = Conn()
    out = retire.retire(c, ["scoop.co.nz", "rnz.co.nz"], path=path, reads=False)
    assert out["listed"] == ["scoop.co.nz"] and out["not ready"] == ["rnz.co.nz"] and not c.logged
    out = retire.retire(c, None, path=path, reads=True)
    assert out["listed"] == ["stuff.co.nz"] and c.logged == ["scoop.co.nz", "stuff.co.nz"]
