"""The release copy (card the-scheduler-s-worker-runs-the-main-checkout-…,
finding 2): it holds one pushed commit of origin/main, detached, never a
branch, never edited, and moves only by `release`. Real git, in a temp
folder: a bare origin, a clone that pushes, and the copy."""
from __future__ import annotations

import json
import os
import subprocess

import pytest

from support.installer import release as rel


def git(path, *args):
    return subprocess.run(["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def commit(work, path, text, msg, push="main"):
    f = work / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", msg)
    if push:
        git(work, "push", "-q", "origin", f"HEAD:{push}")
    return git(work, "rev-parse", "HEAD")


@pytest.fixture
def estate(tmp_path):
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    work = tmp_path / "main-checkout"
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True)
    git(work, "checkout", "-q", "-b", "main")
    first = commit(work, "requirements.txt", "pytest>=8\n", "one")
    return {"origin": origin, "work": work, "copy": tmp_path / "release", "log": tmp_path / "live" / "release.log",
            "first": first}


def go(e, sha=None, **k):
    lines = []
    rec = rel.release(str(e["copy"]), sha, repo=str(e["work"]), log_path=str(e["log"]), venv=False, log=lines.append, **k)
    return rec, lines


def head(e):
    return git(e["copy"], "rev-parse", "HEAD")


def test_the_copy_is_made_detached_at_origin_main_with_no_branch_and_one_line_logged(estate):
    rec, lines = go(estate)
    c = estate["copy"]
    assert head(estate) == estate["first"] == rec["commit"]
    assert subprocess.run(["git", "-C", str(c), "symbolic-ref", "-q", "HEAD"]).returncode != 0, "detached, never a branch"
    assert git(c, "for-each-ref", "refs/heads") == "", "no local branch is left in the copy"
    assert git(c, "status", "--porcelain") == "", "the record lives in .git and never dirties the copy"
    assert rel.record(str(c))["commit"] == estate["first"] and rec["created"] and rec["worker_restart"] == "owed"
    assert rec["previous"] is None, "a new copy had no commit before"
    assert (c / "requirements.txt").read_text() == "pytest>=8\n", "the tree is checked out, not just the index"
    log = estate["log"].read_text().splitlines()
    assert len(log) == 1 and log == lines and "created at " + estate["first"][:12] in log[0]
    st = rel.state(str(c))
    assert st["on_origin_main"] and st["branch"] is None and st["dirty"] == 0


def test_a_move_follows_a_push_and_says_when_the_worker_must_restart(estate):
    go(estate)
    w = estate["work"]
    lane = commit(w, "registers/x/load.py", "x = 1\n", "a lane")
    rec, _ = go(estate)
    assert head(estate) == lane and rec["previous"] == estate["first"] and rec["worker_restart"] == "not needed"
    rec, lines = go(estate)
    assert rec["worker_restart"] == "not needed" and f"stays at {lane[:12]} by" in lines[0], "a rerun is harmless"
    cat = commit(w, "support/scheduler/jobs.toml", "version = 1\n", "the catalogue")
    rec, _ = go(estate)
    assert head(estate) == cat and rec["worker_restart"] == "not needed", "the catalogue reloads itself"
    code = commit(w, "support/scheduler/queue.py", "q = 1\n", "the worker's own code")
    rec, lines = go(estate)
    assert head(estate) == code and rec["worker_restart"] == "owed"
    assert rec["worker_code_changed"] == ["support/scheduler/queue.py"]
    assert f"moved to {code[:12]} (was {cat[:12]})" in lines[0]
    assert len(estate["log"].read_text().splitlines()) == 5


def test_a_commit_not_on_origin_main_is_refused_and_the_copy_is_untouched(estate):
    go(estate)
    w = estate["work"]
    git(w, "checkout", "-q", "-b", "integrate/x")
    branch_tip = commit(w, "registers/y/load.py", "y = 1\n", "integrate", push="integrate/x")
    with pytest.raises(rel.Refused, match="not on origin/main"):
        go(estate, branch_tip)
    local = commit(w, "registers/z/load.py", "z = 1\n", "merged locally, not pushed", push=None)
    with pytest.raises(rel.Refused):
        go(estate, local)
    assert head(estate) == estate["first"]
    assert len(estate["log"].read_text().splitlines()) == 1, "a refusal moves nothing and logs no release line"


def test_an_older_commit_of_origin_main_may_be_released(estate):
    go(estate)
    commit(estate["work"], "registers/x/load.py", "x = 1\n", "a lane")
    go(estate)
    rec, _ = go(estate, estate["first"])
    assert head(estate) == estate["first"] and rec["previous"] != estate["first"]


@pytest.mark.parametrize("edit", ["tracked", "untracked", "branch"])
def test_an_edited_copy_or_a_branch_is_refused_and_nothing_moves(estate, edit):
    go(estate)
    c = estate["copy"]
    commit(estate["work"], "registers/x/load.py", "x = 1\n", "a lane")
    if edit == "tracked":
        (c / "requirements.txt").write_text("edited\n")
    elif edit == "untracked":
        (c / "stray.txt").write_text("a job wrote here\n")
    else:
        git(c, "checkout", "-q", "-b", "main")
    with pytest.raises(rel.Refused, match="edited|branch main"):
        go(estate)
    assert head(estate) == estate["first"]


def test_a_path_that_is_not_a_clone_is_never_touched(estate):
    estate["copy"].mkdir()
    (estate["copy"] / "keep.txt").write_text("mine\n")
    with pytest.raises(rel.Refused, match="not a clone"):
        go(estate)
    assert os.listdir(estate["copy"]) == ["keep.txt"]


def test_the_copys_own_venv_is_made_once_and_rebuilt_only_when_requirements_change(tmp_path):
    copy = tmp_path / "c"
    copy.mkdir()
    (copy / "requirements.txt").write_text("pytest>=8\n")
    calls = []

    def sh(cmd, **k):
        calls.append(cmd)
        if cmd[1:3] == ["-m", "venv"]:
            os.makedirs(os.path.join(cmd[3], "bin"))
            open(os.path.join(cmd[3], "bin", "python"), "w").close()
        return 0, ""

    assert rel.ensure_venv(str(copy), sh)["action"] == "create"
    assert [c[1:3] for c in calls] == [["-m", "venv"], ["install", "-q"]]
    assert calls[1][0] == str(copy / ".venv" / "bin" / "pip") and calls[1][-1] == str(copy / "requirements.txt"), \
        "pip is the copy's own, nothing installed outside it"
    calls.clear()
    assert rel.ensure_venv(str(copy), sh)["action"] == "same" and calls == []
    (copy / "requirements.txt").write_text("pytest>=8\npsycopg[binary]==3.3.4\n")
    assert rel.ensure_venv(str(copy), sh)["action"] == "install" and len(calls) == 1
    with pytest.raises(rel.Refused, match="pip failed"):
        (copy / "requirements.txt").write_text("broken\n")
        rel.ensure_venv(str(copy), lambda cmd, **k: (1, "no such package"))


def test_the_cli_refuses_with_exit_1(estate, capsys):
    from support.installer import __main__ as cli
    go(estate)
    (estate["copy"] / "stray.txt").write_text("x\n")
    assert cli.main(["release", "--copy", str(estate["copy"]), "--repo", str(estate["work"])]) == 1
    assert "release refused" in capsys.readouterr().err
    assert json.loads(json.dumps(rel.record(str(estate["copy"]))))["commit"] == estate["first"]
