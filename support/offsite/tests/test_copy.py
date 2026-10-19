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
