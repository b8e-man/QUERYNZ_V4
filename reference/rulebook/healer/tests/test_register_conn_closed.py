"""Queue 8 (2026-09-17; audit 2026-09-14 MED): `heal_role_title_prefix`
opened a register connection every cycle and never closed it — one leaked
connection per crawler cycle against the register box. The heal now closes
it on every exit path (as do the post-nominal fold and the anchor lane,
which closed theirs only on the happy path). Fails on the old code: the
fake register connection is never closed."""
import pytest

from healer import crawler


class _Cur:
    def __init__(self, rows): self.rows = rows
    def fetchall(self): return self.rows
    def fetchone(self): return self.rows[0] if self.rows else None


class _Graph:
    def __init__(self, rows, boom_on=None):
        self.rows, self.boom_on, self.commits = rows, boom_on, 0
    def execute(self, sql, *_a, **_k):
        if self.boom_on and self.boom_on in sql:
            raise RuntimeError("graph fell over mid-heal")
        if "array_agg(id)" in sql:
            return _Cur([{"ids": []}])
        return _Cur(self.rows)
    def commit(self): self.commits += 1


class _Reg:
    def __init__(self): self.closed = 0
    def close(self): self.closed += 1


def _rows():
    return [{"id": 1, "name": "Prime Minister Chris Hipkins", "type": "person"}]


def test_role_title_heal_closes_its_register_connection(monkeypatch):
    reg = _Reg()
    monkeypatch.setattr("reviewer.corroborate.register_conn", lambda: reg)
    monkeypatch.setattr("claim_graph.remediate.rename_entity", lambda *a, **k: None)
    g = _Graph(_rows())
    assert crawler.heal_role_title_prefix(g) == 1
    assert reg.closed == 1, "the register connection leaked"
    assert g.commits >= 1


def test_role_title_heal_closes_it_when_the_heal_raises(monkeypatch):
    reg = _Reg()
    monkeypatch.setattr("reviewer.corroborate.register_conn", lambda: reg)
    g = _Graph(_rows(), boom_on="array_agg(id)")
    with pytest.raises(RuntimeError):
        crawler.heal_role_title_prefix(g)
    assert reg.closed == 1, "an exception path must close the register connection too"


def test_close_quietly_tolerates_none_and_a_broken_close():
    crawler._close_quietly(None)

    class _Broken:
        def close(self): raise OSError("already gone")
    crawler._close_quietly(_Broken())
