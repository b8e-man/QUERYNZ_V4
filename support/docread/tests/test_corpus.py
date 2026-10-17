"""Target ordering is a policy, and resuming is not optional at this size."""
import sys, pathlib, json, tempfile

import pytest
from support.docread import corpus
from support.docread.corpus import Target


def t(stem, year, kind):
    return Target(stem, pathlib.Path(f"/x/{stem}.pdf"), year, kind)


def test_recent_years_are_read_before_old_ones():
    """Arthur, 2026-09-23."""
    got = sorted([t("a", 2012, "party"), t("b", 2024, "party")],
                 key=Target.rank)
    assert [x.stem for x in got] == ["b", "a"]


def test_pre_2010_sorts_last_but_is_still_a_target():
    """A deprioritisation, not a cutoff."""
    got = sorted([t("old", 2005, "party"), t("mid", 2015, "party"),
                  t("new", 2023, "party")], key=Target.rank)
    assert [x.stem for x in got] == ["new", "mid", "old"]


def test_party_returns_come_before_candidate_returns_in_the_same_era():
    got = sorted([t("cand", 2023, "candidate"), t("party", 2023, "party")],
                 key=Target.rank)
    assert [x.stem for x in got] == ["party", "cand"]


def test_an_old_party_return_still_sorts_after_a_recent_candidate_one():
    """Era outranks kind: the policy is about years first."""
    got = sorted([t("oldparty", 2008, "party"),
                  t("newcand", 2023, "candidate")], key=Target.rank)
    assert [x.stem for x in got] == ["newcand", "oldparty"]


def test_within_a_year_the_order_is_stable():
    got = sorted([t("b", 2023, "party"), t("a", 2023, "party")],
                 key=Target.rank)
    assert [x.stem for x in got] == ["a", "b"]


def test_a_finished_document_is_not_read_twice():
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td) / "corpus.jsonl"
        out.write_text(json.dumps({"stem": "done-one"}) + "\n"
                       + json.dumps({"stem": "done-two"}) + "\n")
        assert corpus.done_stems(out) == {"done-one", "done-two"}


def test_a_corrupt_line_does_not_make_the_run_start_over():
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td) / "corpus.jsonl"
        out.write_text(json.dumps({"stem": "kept"}) + "\n{ broken\n")
        assert corpus.done_stems(out) == {"kept"}


def test_no_output_file_means_nothing_is_done():
    with tempfile.TemporaryDirectory() as td:
        assert corpus.done_stems(pathlib.Path(td) / "absent.jsonl") == set()


def test_a_document_that_raises_is_recorded_not_lost():
    """2,700 documents WILL contain a few that break something. A run that
    dies on one has read none of the rest."""
    bad = Target("nonexistent", pathlib.Path("/no/such.pdf"), 2024, "party")
    row = corpus.read_one(bad)
    assert row["stem"] == "nonexistent"
    assert row.get("error") and "seconds" in row


def test_the_runner_reads_only_the_pages_it_says_it_read():
    bad = Target("nonexistent", pathlib.Path("/no/such.pdf"), 2024, "party")
    row = corpus.read_one(bad, max_pages=5)
    assert row.get("pages_read", 0) <= 5


def test_the_pool_does_not_fork_from_a_threaded_parent():
    """2026-09-23: six workers, twelve minutes, nothing read. A
    ProcessPoolExecutor starts a management thread and then forks its workers;
    a child forked from a threaded parent inherits that thread's lock state
    without the thread that would release it, and every worker sleeps forever
    while the parent waits in futex_do_wait. This is why CPython's own default
    is moving off fork."""
    assert corpus.START_METHOD != "fork"
    import multiprocessing
    assert corpus.START_METHOD in multiprocessing.get_all_start_methods()


def test_the_module_does_nothing_at_import_time():
    """forkserver and spawn re-IMPORT this module in every worker, so anything
    that runs at import runs once per worker — and `main()` behind the name
    guard is what stops a worker starting its own run."""
    src = (pathlib.Path(corpus.__file__)).read_text()
    assert 'if __name__ == "__main__":' in src
    body = [l for l in src.splitlines()
            if l and not l[0].isspace()
            and not l.startswith(("import ", "from ", "def ", "class ", "@",
                                  "#", '"', "'"))]
    stray = [l for l in body if "=" in l and l.split("=")[0].strip().islower()
             and "(" in l.split("=", 1)[1] and "os.environ" not in l
             and "pathlib" not in l and "re.compile" not in l]
    assert not stray, f"work at import time: {stray}"


def test_redo_lifts_the_skip_for_the_targets_named(tmp_path, monkeypatch):
    """C433: the reader was wrong, so 47 documents have to be read AGAIN.
    The store is append-only and every consumer takes the last row for a
    stem, so a re-read is an append — never an edit, and never a reason to
    truncate the ledger."""
    out = tmp_path / "corpus.jsonl"
    out.write_text('{"stem": "already-read", "year": 2025}\n')
    t = corpus.Target(stem="already-read", pdf=tmp_path / "x.pdf",
                      year=2025, kind="party")
    monkeypatch.setattr(corpus, "_worker", lambda tt: {"stem": tt.stem})
    said = []
    assert corpus.run([t], out=out, queue=tmp_path / "q.jsonl", workers=1,
                      echo=said.append)["documents"] == 0
    assert corpus.run([t], out=out, queue=tmp_path / "q.jsonl", workers=1,
                      redo=True, echo=said.append)["documents"] == 1
    assert len(out.read_text().strip().splitlines()) == 2
