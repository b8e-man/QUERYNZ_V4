"""Many writers at once leave every line whole: processes here, and the same test across the NFS mount
(`QV4_APPENDLINE_SHARED=<a path both boxes see>`, run on both boxes at once) for the real proof."""
import json
import multiprocessing as mp
import os

from support import appendline

N_PROC, N_LINES = 8, 400
PAD = "x" * 3000           # longer than one page, so a torn or interleaved write shows


def _writer(path, who):
    for i in range(N_LINES):
        appendline.append_json(path, {"who": who, "i": i, "pad": PAD})


def _check(path, writers):
    seen = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)            # a torn line fails here
            assert row["pad"] == PAD
            seen.setdefault(row["who"], []).append(row["i"])
    for w in writers:
        assert seen.get(w) == list(range(N_LINES)), w
    return sum(len(v) for v in seen.values())


def test_many_processes_leave_every_line_whole(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    ps = [mp.get_context("fork").Process(target=_writer, args=(path, f"p{k}")) for k in range(N_PROC)]
    [p.start() for p in ps]
    [p.join() for p in ps]
    assert _check(path, [f"p{k}" for k in range(N_PROC)]) == N_PROC * N_LINES


def test_a_newline_is_added_once_and_lines_keep_their_order(tmp_path):
    path = str(tmp_path / "sub" / "a.jsonl")
    appendline.append(path, "one")
    appendline.append(path, ["two\n", "three"])
    assert open(path).read() == "one\ntwo\nthree\n"
    assert appendline.append(path, []) == 0


def test_across_boxes():
    """Run with QV4_APPENDLINE_SHARED set on node1 and node2 at the same moment; each box writes under its
    own name and checks only that every line in the file is whole and its own lines are all there."""
    path = os.environ.get("QV4_APPENDLINE_SHARED")
    if not path:
        import pytest
        pytest.skip("QV4_APPENDLINE_SHARED not set: the cross-box proof is run by hand")
    box = os.uname().nodename
    ps = [mp.get_context("fork").Process(target=_writer, args=(path, f"{box}-{k}")) for k in range(4)]
    [p.start() for p in ps]
    [p.join() for p in ps]
    _check(path, [f"{box}-{k}" for k in range(4)])
