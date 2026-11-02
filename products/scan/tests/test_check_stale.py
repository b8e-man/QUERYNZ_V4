"""A stale scan is reported stale, once, and its lines are not read back against tables that have loaded since (step 8.5,
2 November 2026: the procurement read-back went red when the links were rebuilt and no re-run followed; the companies
package's publish turned every citation of seven scans into a mismatch)."""
from types import SimpleNamespace

from products.scan import check


def test_a_stale_run_gives_one_problem_naming_the_views_and_the_re_run(monkeypatch):
    monkeypatch.setattr(check.state, "latest", lambda st, name: {"run_id": 7, "lines": 3})
    called = []
    monkeypatch.setattr(check, "citations_resolve", lambda pub, cites: called.append(1) or ["a mismatch"])
    t = SimpleNamespace(name="procurement-directors-donors")
    got = check.check_run(None, None, t, {}, {"scan": t.name, "run_id": 7, "stale": ["companies", "links"], "never_run": False})
    assert got == ["procurement-directors-donors: stale: companies, links loaded since run 7; a re-run is owed (qv4-scan-rerun)"]
    assert not called, "a stale run's citations are not read back against today's tables"


def test_a_current_run_is_still_read_back(monkeypatch):
    class ReadBack(Exception):
        pass

    def resolve(pub, cites):
        raise ReadBack

    monkeypatch.setattr(check.state, "latest", lambda st, name: {"run_id": 7, "lines": 0, "settings": {}})
    monkeypatch.setattr(check.state, "citations", lambda st, run, *a: [])
    monkeypatch.setattr(check, "citations_resolve", resolve)
    t = SimpleNamespace(name="x")
    import pytest
    with pytest.raises(ReadBack):
        check.check_run(None, None, t, {"chains": {"value": 1}, "through_people": {"value": 1}},
                        {"scan": "x", "run_id": 7, "stale": [], "never_run": False})
