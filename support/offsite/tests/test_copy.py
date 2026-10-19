"""Track B's copy and restore, without a database or the network: the delete
rule's sorting, the nightly and weekly cadence, sealing and opening, and a
tree copied nightly and restored to equality (gpg and zstd run for real)."""
import datetime as dt
import os

import pytest

from support.offsite import copy as C
from support.offsite import pieces as P
from support.offsite import restore as R

ENV = {"OFFSITE_PASSPHRASE": "test-pass"}
SUNDAY = dt.datetime(2026, 10, 25, 20, 0).astimezone()
MONDAY = dt.datetime(2026, 10, 26, 20, 0).astimezone()


def test_rebuildable_tables_are_out_and_the_rest_are_sent():
    assert P.fate("extractions", "candidates", "candidate")[0] == P.OUT
    assert P.fate("incoming_news", "public", "article_embeddings")[0] == P.LOCAL
    assert P.fate("extractions", "v3", "claims")[0] == P.SEND
    assert P.fate("nzbn_canonical", "bulk", "a_table_added_next_month")[0] == P.SEND


def test_every_rule_names_a_rebuild_that_must_exist():
    assert P.missing_rebuilds(exists=lambda p: True) == []
    bad = P.missing_rebuilds(exists=lambda p: False)
    assert len(bad) == len(P.RULES) and all("no such rebuild" in b for b in bad)


def test_the_press_graph_is_frozen_and_nothing_else_is():
    assert [d for d, c in P.DATABASES.items() if c["frozen"]] == ["extractions"]


def test_object_names_are_safe():
    assert C.object_name("extractions:v3.claims") == "extractions--v3.claims"
    assert C.object_name('x:we"ird schema.t/1') == "x--we_ird_schema.t_1"


def run_at(now, prev, spool):
    r = C.Run.__new__(C.Run)
    r.now, r.prev, r.spool = now, prev, spool
    r.man = {"stamp": now.strftime("%Y%m%dT%H%M%S"), "kind": "full" if now.weekday() == P.FULL_WEEKDAY else "nightly"}
    return r


def test_cadence(tmp_path):
    week_ago = (MONDAY - dt.timedelta(days=8)).strftime("%Y%m%dT%H%M%S")
    old = (MONDAY - dt.timedelta(days=P.REFRESH_DAYS)).strftime("%Y%m%dT%H%M%S")
    prev = {"pieces": {"a:s.t": {"sig": "1:0:0:0", "stamp": week_ago},
                       "a:s.old": {"sig": "1:0:0:0", "stamp": old}}}
    night = run_at(MONDAY, prev, str(tmp_path))
    assert night.wants("a:s.t", "1:0:0:0", P.SEND, False, False) == ""
    assert night.wants("a:s.t", "1:5:0:0", P.SEND, False, False) == "changed"
    assert night.wants("a:s.new", "1:0:0:0", P.SEND, False, False) == "first copy"
    assert night.wants("a:s.t", "1:0:0:0", P.SEND, False, True) == "write counters restarted"
    sunday = run_at(SUNDAY, prev, str(tmp_path))
    assert sunday.wants("a:s.t", "1:0:0:0", P.SEND, False, False) == "weekly full"
    # frozen: not at the weekly full, only when changed or near the bucket's retention
    assert sunday.wants("a:s.t", "1:0:0:0", P.SEND, True, False) == ""
    assert sunday.wants("a:s.t", "2:0:0:0", P.SEND, True, False) == "changed"
    assert night.wants("a:s.old", "1:0:0:0", P.SEND, True, False) == "refresh"
    # kept on the box: only when it changed
    assert sunday.wants("a:s.t", "1:0:0:0", P.LOCAL, False, False) == ""


def test_sealed_round_trip(tmp_path):
    dst = str(tmp_path / "o" / "x.zst.gpg")
    s = C.Sealed(dst, "pw")
    s.write(b"a\tb\n")
    s.write(memoryview(b"c\td\n"))
    meta = s.close()
    assert meta["rows"] == 2 and meta["plain_bytes"] == 8 and meta["bytes"] > 0
    assert b"a\tb" not in open(dst, "rb").read()
    gpg, zstd = C.opened(dst, "pw")
    assert zstd.stdout.read() == b"a\tb\nc\td\n"
    assert zstd.wait() == 0 and gpg.wait() == 0


def test_scan_tree_excludes_and_skips_links(tmp_path):
    (tmp_path / "keep").mkdir()
    (tmp_path / "keep" / "a.pdf").write_bytes(b"x")
    (tmp_path / "llama").mkdir()
    (tmp_path / "llama" / "big.bin").write_bytes(b"y")
    os.symlink(tmp_path / "keep" / "a.pdf", tmp_path / "link.pdf")
    assert set(C.scan_tree(str(tmp_path), ("llama",))) == {"keep/a.pdf"}


def no_database(*a):
    raise AssertionError("a tree test touched a database")


def tree_run(spool, now, full=None):
    r = C.Run(full=full, local_only=False, now=now, spool=spool, env=ENV, client=object(), connect=no_database,
              log=lambda *a: None)
    r.send = lambda name: None       # no network
    return r


def test_tree_nightly_then_restore_to_equality(tmp_path, monkeypatch):
    root, spool = tmp_path / "tree", str(tmp_path / "spool")
    (root / "d").mkdir(parents=True)
    (root / "d" / "one.txt").write_bytes(b"one")
    (root / "two.txt").write_bytes(b"two")
    trees = {"t": (str(root), P.SEND, "test", ())}
    first = tree_run(spool, MONDAY).run(databases={}, trees=trees)
    assert first["kind"] == "full" and first["trees"]["t"]["sent_files"] == 2

    (root / "two.txt").write_bytes(b"two, changed")
    os.utime(root / "two.txt", ns=(1, 1))
    (root / "three.txt").write_bytes(b"three")
    second = tree_run(spool, MONDAY + dt.timedelta(days=1)).run(databases={}, trees=trees)
    assert second["kind"] == "nightly" and second["trees"]["t"]["sent_files"] == 2
    files = second["trees"]["t"]["files"]
    assert files["d/one.txt"][3] == first["stamp"] and files["three.txt"][3] == second["stamp"]

    src = R.Source("local", str(tmp_path / "work"), spool=spool)
    rec = R.restore_tree("t", second["trees"]["t"], src, "test-pass", str(tmp_path / "back"), log=lambda *a: None)
    assert rec == {**rec, "files": 3, "equal": 3, "bad": 0}
    assert (tmp_path / "back" / "trees" / "t" / "two.txt").read_bytes() == b"two, changed"

    second["trees"]["t"]["files"]["three.txt"][2] = "0" * 64     # the check can fail
    rec = R.restore_tree("t", second["trees"]["t"], src, "test-pass", str(tmp_path / "back2"), log=lambda *a: None)
    assert rec["bad"] == 1


def test_a_local_only_run_keeps_its_own_state(tmp_path):
    r = C.Run(full=True, local_only=True, now=MONDAY, spool=str(tmp_path), env=ENV, log=lambda *a: None)
    assert r.spool == str(tmp_path / "local-only")


def test_a_killed_run_resumes_and_does_not_send_twice(tmp_path):
    spool = str(tmp_path)
    r = tree_run(spool, MONDAY, full=True)
    r.man["uploaded"] = ["x"]
    r.save_progress()
    again = tree_run(spool, MONDAY + dt.timedelta(hours=3))
    assert again.stamp == r.stamp and again.man["uploaded"] == ["x"]
    stale = tree_run(spool, MONDAY + dt.timedelta(hours=C.RESUME_HOURS + 1))
    assert stale.stamp != r.stamp


def test_summary_names_a_frozen_table_that_moved():
    man = {"stamp": "S", "kind": "nightly", "sent": True, "trees": {},
           "databases": {"extractions": {"frozen": True, "stamp": "S"}, "q": {"frozen": False, "stamp": "S"}},
           "pieces": {"extractions:v3.claims": {"stamp": "S", "why": "changed", "bytes": 5},
                      "extractions:v3.alias": {"stamp": "OLD", "why": "first copy"},
                      "q:s.t": {"stamp": "S", "why": "changed", "bytes": 1}}}
    s = C.summary(man)
    assert s["frozen_moved"] == ["extractions:v3.claims"] and s["copied"] == 2 and s["sealed_bytes"] == 6


@pytest.mark.parametrize("path", ["../escape.txt", "/etc/passwd"])
def test_restore_tree_refuses_paths_outside(tmp_path, path):
    import io
    import tarfile
    spool = tmp_path / "spool"
    name = C.object_name("tree:t") + ".tar.zst.gpg"
    out = C.Sealed(str(spool / "objects" / "S" / name), "pw")
    with tarfile.open(fileobj=out, mode="w|") as tar:
        info = tarfile.TarInfo(path)
        info.size = 1
        tar.addfile(info, io.BytesIO(b"x"))
    out.close()
    src = R.Source("local", str(tmp_path / "w"), spool=str(spool))
    rec = R.restore_tree("t", {"files": {path: [1, 0, "x", "S"]}}, src, "pw", str(tmp_path / "b"), log=lambda *a: None)
    assert rec["bad"] == 1 and not (tmp_path / "escape.txt").exists()


class PagedTable:
    """A fake cursor over one table: `pages[p]` is the text of heap page p,
    served for `COPY (SELECT ... WHERE ctid >= '(lo,0)' [AND ctid < '(hi,0)']) TO STDOUT`."""

    def __init__(self, pages):
        self.pages, self.reads = pages, []

    def copy(self, sql):
        import contextlib
        import re
        lo = int(re.search(r"ctid >= '\((\d+),0\)'", sql).group(1))
        m = re.search(r"ctid < '\((\d+),0\)'", sql)
        hi = int(m.group(1)) if m else len(self.pages)
        self.reads.append((lo, hi))
        return contextlib.nullcontext(iter([b"".join(self.pages[lo:hi])]))


def chunk_run(tmp_path, now, prev, full=False):
    r = C.Run.__new__(C.Run)
    r.now, r.prev, r.spool, r.env, r.log = now, prev, str(tmp_path), ENV, (lambda *a: None)
    r.man = {"stamp": now.strftime("%Y%m%dT%H%M%S"), "kind": "full" if full else "nightly"}
    return r


def test_a_big_table_sends_only_the_ranges_that_changed(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "CHUNK_TARGET", 10)        # 2 pages of 5 bytes per range
    monkeypatch.setattr(C, "CHUNK_MIN_PAGES", 1)
    pages = [f"r{p}\tx\n".encode() for p in range(5)]
    first = chunk_run(tmp_path, MONDAY, None).copy_chunked(PagedTable(pages), "d:s.t", "s", "t", 5, 25, "first copy")
    assert [(c["lo"], c["hi"]) for c in first["chunks"]] == [(0, 2), (2, 4), (4, None)]
    assert first["sent_chunks"] == 3 and first["rows"] == 5

    pages[4] = b"r4\tchanged\n"
    pages.append(b"r5\tnew\n")                        # the table grew a page
    prev = {"pieces": {"d:s.t": first}}
    night = chunk_run(tmp_path, MONDAY + dt.timedelta(days=1), prev)
    second = night.copy_chunked(PagedTable(pages), "d:s.t", "s", "t", 6, 30, "changed")
    assert second["sent_chunks"] == 1 and second["rows"] == 6
    assert [c["stamp"] for c in second["chunks"]] == [first["chunks"][0]["stamp"]] * 2 + [night.stamp]
    assert C.objects_of(second, night.stamp) == [second["chunks"][2]["object"]]

    # the restore's check: the rows read back in any order
    want = R.Multiset()
    for c in second["chunks"]:
        want.feed(b"".join(pages[c["lo"]:c["hi"]]))
    back = R.Multiset()
    back.feed(b"".join(reversed(pages)))
    assert back.digest() == want.digest() == (want.digest()[0], 6)


def test_a_full_copy_sends_every_range(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "CHUNK_TARGET", 10)
    monkeypatch.setattr(C, "CHUNK_MIN_PAGES", 1)
    pages = [f"r{p}\tx\n".encode() for p in range(4)]
    first = chunk_run(tmp_path, MONDAY, None).copy_chunked(PagedTable(pages), "d:s.t", "s", "t", 4, 20, "first copy")
    full = chunk_run(tmp_path, SUNDAY + dt.timedelta(days=7), {"pieces": {"d:s.t": first}}, full=True)
    again = full.copy_chunked(PagedTable(pages), "d:s.t", "s", "t", 4, 20, "weekly full")
    assert again["sent_chunks"] == len(again["chunks"]) == 2 and again["sha256"] == first["sha256"]


def test_the_multiset_check_ignores_order_and_nothing_else():
    def digest(*blocks):
        m = R.Multiset()
        for b in blocks:
            m.feed(b)
        return m.digest()
    assert digest(b"a\t1\nb\t2\n") == digest(b"b\t2\na", b"\t1\n")
    assert digest(b"a\t1\nb\t2\n") != digest(b"a\t1\nb\t3\n")
    assert digest(b"a\t1\n") != digest(b"a\t1\na\t1\n")
    with pytest.raises(ValueError):
        digest(b"a\t1")


def test_two_runs_never_share_a_spool(tmp_path):
    import fcntl
    os.makedirs(tmp_path, exist_ok=True)
    with open(tmp_path / "lock", "w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        with pytest.raises(RuntimeError, match="another copy is running"):
            tree_run(str(tmp_path), MONDAY).run(databases={}, trees={})


def test_objects_needed_follow_the_restore_order():
    man = {"databases": {"b": {"stamp": "S2", "schema": "b--_schema.dump.gpg"},
                         "a": {"stamp": "S1", "schema": "a--_schema.dump.gpg"}},
           "pieces": {"a:s.t": {"fate": "send", "stamp": "S1", "object": "a--s.t.copy.zst.gpg"},
                      "a:s.big": {"fate": "send", "chunks": [{"stamp": "S1", "object": "r0"}, {"stamp": "S2", "object": "r1"}]},
                      "a:s.vec": {"fate": "local", "stamp": "S1", "object": "v"},
                      "b:s.gone": {"fate": "out"}},
           "trees": {"t": {"files": {"x": [1, 0, "h", "S2"], "y": [1, 0, "h", "S1"]}}}}
    assert R.objects_needed(man) == [
        ("S1", "a--_schema.dump.gpg"), ("S1", "r0"), ("S2", "r1"), ("S1", "a--s.t.copy.zst.gpg"),
        ("S2", "b--_schema.dump.gpg"), ("S1", "tree--t.tar.zst.gpg"), ("S2", "tree--t.tar.zst.gpg")]
