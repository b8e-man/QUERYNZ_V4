"""The diagnostic report's checks and its template (9 November 2026)."""
from products.report import catalogue as cat, diagnose as D
from products.report import template as T


class Names:
    """pub.names as where_else asks it: rows (ref, register, view, full_key)."""

    def __init__(self, rows):
        self.rows = rows


def _fake_rows(names):
    def rows(conn, sql, params=()):
        if "limit 1" in sql:
            return [{"full_key": r[3], "fl_key": None} for r in names.rows if r[0] == params[0]][:1]
        return [{"register": r[1], "view": r[2], "ref": r[0]} for r in names.rows if r[3] == params[0]]
    return rows


def item(ref, view, grade="near", rule="name-only@1", undated=False):
    return {"ref": ref, "view": view, "grade": grade, "rule": rule, "dates": {"undated": undated}}


def test_a_register_where_the_name_is_filed_and_no_link_reached_shows_as_not_reached(monkeypatch):
    names = Names([("companies:d/1", "companies", "directors", "ann roe"), ("companies:d/2", "companies", "directors", "ann roe"),
                   ("insolvency:i/9", "insolvency", "insolvency_people", "ann roe"), ("hansard:h/1", "hansard", "hansard_people", "bob ray")])
    monkeypatch.setattr(D.db, "rows", _fake_rows(names))
    report = {"found": True, "ref": "companies:d/1", "subject": {"ref": "companies:d/1"},
              "sections": [{"name": "companies", "items": [item("companies:d/2", "directors", "confirmed", "full-name@1")]}]}
    got = D.where_else(None, report)
    assert got == [{"register": "insolvency", "view": "insolvency_people", "rows": 1, "reached": 0},
                   {"register": "companies", "view": "directors", "rows": 2, "reached": 2}]
    lines = D.checks(report, 1.0, got)
    assert ("register not reached", "the name is filed 1 time(s) in pub.insolvency_people (insolvency); no link reached it") in lines


def test_the_checks_name_a_confirmed_namesake_a_duplicate_an_undated_row_and_a_slow_report():
    report = {"found": True, "walk": {"links_omitted": 3},
              "sections": [{"name": "a", "items": [item("x:1", "directors", "confirmed", "name-only@1"), item("x:2", "linz_title_owners", undated=True)]},
                           {"name": "b", "items": [item("x:2", "linz_title_owners", undated=True)]}]}
    kinds = Counter_of(D.checks(report, D.LIMIT_S + 1))
    assert kinds == {"wrong link": 1, "duplicate": 1, "missing date": 1, "slow or cut short": 2}
    assert D.checks({"found": False, "why": "no such row"}, 0) == [("other", "the start row was not found: no such row")]


def Counter_of(lines):
    out = {}
    for k, _ in lines:
        out[k] = out.get(k, 0) + 1
    return out


def test_every_problem_kind_is_one_the_findings_use():
    report = {"found": True, "walk": {}, "problems": ["p"], "superseded_not_held": ["s"], "sections": []}
    assert {k for k, _ in D.checks(report, 0, [{"register": "r", "view": "nope", "rows": 1, "reached": 0}])} <= set(D.KINDS)


def test_the_diagnostic_template_reads_every_catalogued_table_and_is_as_make_writes_it():
    import os
    from products.report.templates.diagnostic import make   # noqa: F401  (the file is importable as a module)
    t = T.by_name("diagnostic")
    assert set(t.views) == set(cat.BY_NAME)
    assert set(t.buckets) >= {"members", "confirmed", "near", "officers", "office", "chain"}
    with open(os.path.join(make.HERE, "template.toml"), encoding="utf-8") as f:
        assert f.read() == make.render(), "run make.py: the catalogue changed"
