"""A read stopped by a lock wait is tried again, and who held the lock is said (7 November 2026: the 08:00 read, normally
4 s, waited 120 s behind a lock on 4, 5 and 6 November and those days had no version)."""
import pytest

from products.published_site import build as B
from products.published_site import read
from products.published_site.tests import fixtures as X
from products.published_site.tests.test_build_offline import listing, offline  # noqa: F401 — the fixture


class LockNotAvailable(Exception):
    """The name psycopg gives a lock_timeout; the build matches on the name."""


class Opened(X.NoConn):
    closed = 0

    def close(self):
        Opened.closed += 1


def stalling(fails, exc=LockNotAvailable):
    state = {"left": fails, "made": 0}

    class Stalls(X.FakeTables):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            state["made"] += 1

        def get(self, view):
            if state["left"]:
                state["left"] -= 1
                raise exc("canceling statement due to lock timeout")
            return super().get(view)

    return Stalls, state


@pytest.fixture
def quick(monkeypatch, offline):  # noqa: F811
    monkeypatch.setattr(B, "READ_RETRY_S", 0)
    monkeypatch.setattr(B, "READ_TRIES", 3)
    Opened.closed = 0
    monkeypatch.setattr(read, "product_connect", lambda: Opened())


def build(tmp_path, stamp):
    listing(tmp_path, X.D.values())
    return B.build("2026-10-20T0620", str(tmp_path / "out"), stamp=stamp, listings_folder=str(tmp_path / "listings"), log=lambda s: None)


def test_a_read_that_waits_on_a_lock_is_tried_again_and_the_build_passes(quick, monkeypatch, tmp_path):
    cls, state = stalling(2)
    monkeypatch.setattr(read, "Tables", cls)
    ok, stamp, lines = build(tmp_path, "2026-10-20T0800")
    assert ok, lines
    assert state["made"] == 3 and Opened.closed == 2
    assert sum(1 for l in lines if l.startswith("  wait  read")) == 2


def test_the_tries_run_out_and_the_build_fails_plainly(quick, monkeypatch, tmp_path):
    cls, state = stalling(99)
    monkeypatch.setattr(read, "Tables", cls)
    ok, stamp, lines = build(tmp_path, "2026-10-20T0801")
    assert not ok and stamp is None
    assert state["made"] == 3
    assert lines[-1].startswith("fail  the published tables could not be read: LockNotAvailable") and "after 3 tries" in lines[-1]


def test_any_other_error_is_not_tried_again(quick, monkeypatch, tmp_path):
    cls, state = stalling(1, exc=KeyError)
    monkeypatch.setattr(read, "Tables", cls)
    ok, stamp, lines = build(tmp_path, "2026-10-20T0802")
    assert not ok and state["made"] == 1 and not any("wait  read" in l for l in lines)


class Watched:
    def __init__(self, rows):
        self.rows, self.asked = rows, []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        self.asked.append(params)
        return iter(self.rows)


def test_the_watcher_keeps_each_blocker_once():
    conn = Watched([(4242, "qv4-links-build", "active", "07:45:02", "DELETE FROM lane.rows WHERE register = ANY($1)",
                     "RowExclusiveLock", "lane.rows")])
    import time
    with read.WaitWatcher(77, connect=lambda: conn, every=0.01) as w:
        time.sleep(0.1)
    assert conn.asked and conn.asked[0] == (77,)
    assert w.lines == ["pid 4242 qv4-links-build (active, in a transaction since 07:45:02; RowExclusiveLock on lane.rows): "
                       "DELETE FROM lane.rows WHERE register = ANY($1)"]
