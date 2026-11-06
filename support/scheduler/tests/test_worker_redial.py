"""A row's lease renewal across a database switchover (6 November 2026): a renewal that raises dials the
database again and keeps the child while the lease can still be the row's; past that, the row is lost."""
import time

from support.scheduler import queue as q
from support.scheduler import worker as wk


class FakeConn:
    def __init__(self):
        self.redials = 0

    def redial(self):
        self.redials += 1


def a_worker():
    w = object.__new__(wk.Worker)
    w.schema, w.log = "s", (lambda m: None)
    w.rules = type("R", (), {"lease_seconds": 90})()
    return w


def a_row():
    r = object.__new__(wk.Running)
    r.claim, r.lost = {"id": 1, "token": "t"}, False
    r.last_renew = r.renewed_ok = time.monotonic() - 31        # a renewal is due
    return r


def test_a_renewal_that_raises_dials_again_and_renews(monkeypatch):
    calls = []

    def renew(conn, *a, **kw):
        calls.append(1)
        if len(calls) == 1:
            raise OSError("server closed the connection unexpectedly")
        return True

    monkeypatch.setattr(q, "renew", renew)
    w, r, c = a_worker(), a_row(), FakeConn()
    assert w._renew_if_due(c, r) is True and c.redials == 1 and len(calls) == 2 and not r.lost
    assert time.monotonic() - r.renewed_ok < 1


def test_an_unreachable_database_keeps_the_child_inside_the_lease_then_gives_the_row_up(monkeypatch):
    def renew(conn, *a, **kw):
        raise OSError("no route")

    monkeypatch.setattr(q, "renew", renew)
    w, r, c = a_worker(), a_row(), FakeConn()
    assert w._renew_if_due(c, r) is True and not r.lost, "31 s since the last confirmed renewal: keep going"
    assert time.monotonic() - r.last_renew > 90 / 3 - wk.RENEW_RETRY_S - 1, "the next try comes within seconds"
    r.renewed_ok = time.monotonic() - 85
    r.last_renew = time.monotonic() - 31
    assert w._renew_if_due(c, r) is False and r.lost, "the lease may have run out: the row is given up"


def test_a_refused_renewal_is_still_a_lost_lease(monkeypatch):
    monkeypatch.setattr(q, "renew", lambda *a, **kw: False)
    w, r, c = a_worker(), a_row(), FakeConn()
    assert w._renew_if_due(c, r) is False and r.lost and c.redials == 0
