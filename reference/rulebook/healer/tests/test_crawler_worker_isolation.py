"""crawler.judge: no DB handle of the caller's is reachable from a worker
thread, and the worker's own connection is a SIBLING of the caller's —
never claim_graph.store.connect(), which reaches the configured
production graph regardless of where the caller's `g` points (the keys
test-leak incident, 2026-08-22; reviewer SPEC carried crawler.py as
"same hazard, B4"). Written failing-first against the `_store.connect()`
per-worker shape."""
import threading

from healer import crawler


class _Cur:
    def __init__(self, rows): self.rows = rows
    def fetchall(self): return self.rows
    def fetchone(self): return self.rows[0] if self.rows else None


class _FakeConn:
    """A per-worker connection: accepts any SQL, records the thread."""
    def __init__(self, log): self.log = log
    def execute(self, *_a, **_k):
        self.log.append(threading.current_thread().name); return _Cur([])
    def commit(self): pass
    def rollback(self): pass
    def close(self): self.log.append("closed")


class _MainThreadOnly:
    """The caller's connection: hands out one queued case; any use off the
    main thread is a violation."""
    def __init__(self): self.violations = []
    def _guard(self):
        if threading.current_thread() is not threading.main_thread():
            self.violations.append(threading.current_thread().name)
            raise RuntimeError("caller's connection touched from a worker thread")
    def execute(self, sql, *_a, **_k):
        self._guard()
        if "RETURNING m.entity_id" in sql:
            return _Cur([{"entity_id": 7, "name": "OCR", "type": "organisation",
                          "pattern": "crawler-acronym-org"}])
        return _Cur([])
    def commit(self): self._guard()
    def rollback(self): self._guard()


def test_workers_use_a_sibling_connection_never_the_callers(monkeypatch):
    monkeypatch.setattr(crawler.model, "judge",
                        lambda *a, **k: {"verdict": "abstain", "confidence": 0.3,
                                         "reasoning": "test", "model_reasoning": ""})
    monkeypatch.setattr(crawler, "_mirror", lambda row: None)
    worker_log: list[str] = []
    monkeypatch.setattr(crawler, "_worker_connect", lambda g: _FakeConn(worker_log))
    g = _MainThreadOnly()
    n = crawler.judge(g, limit=1, concurrency=2)
    assert g.violations == [], g.violations
    assert n == 1
    assert "closed" in worker_log, "the worker connection was not closed"
    assert any(t != "MainThread" and t != "closed" for t in worker_log), "the worker never ran"


def test_no_store_connect_in_a_worker():
    import pathlib
    src = (pathlib.Path(crawler.__file__)).read_text()
    assert "_store.connect()" not in src and "store.connect()" not in src, \
        "a worker connection must be a sibling of the caller's (keys._worker_connect shape)"
