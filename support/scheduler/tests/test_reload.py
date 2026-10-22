"""The worker reads its catalogue only from a checkout that stands, unedited,
at a commit of origin/main (card the-scheduler-s-worker-runs-the-main-
checkout-…, finding 2; the release copy always does): an integrate branch,
a merge not yet pushed or an edited tree keeps the last good catalogue and
says why in one line, once per change. No database: the answer and the
catalogue are monkeypatched; two tests ask git itself."""
from __future__ import annotations

import subprocess

from support.scheduler import registry as reg
from support.scheduler import worker as wk
from support.scheduler.tests import fixtures as fx


HELD = "the checkout stands at 0123456789ab (on integrate/procurement-1), not a commit of origin/main"


def worker(monkeypatch, why, tmp_path):
    """A worker reading its catalogue from the files (no registry passed),
    against the fixture catalogue, with the release answer set by `why`
    (None: at a commit of origin/main)."""
    j, p = fx.write(tmp_path)
    state = {"why": why, "jobs": j}
    monkeypatch.setattr(wk, "release_state", lambda path: state["why"])
    load, profiles, queueing = reg.load, reg.profiles, reg.queueing
    monkeypatch.setattr(reg, "load", lambda path=None: load(state["jobs"]))
    monkeypatch.setattr(reg, "profiles", lambda path=None: profiles(p))
    monkeypatch.setattr(reg, "queueing", lambda path=None: queueing(state["jobs"]))
    monkeypatch.setattr(reg, "problems", lambda *a, **k: [])
    lines = []
    w = wk.Worker("t", "node2", log=lines.append)
    return w, state, lines


def grown(tmp_path):
    sub = tmp_path / "grown"
    sub.mkdir()
    j, _ = fx.write(sub, jobs=fx.JOBS + '\n[jobs.newjob]\nneeds = "processor"\nmemory_gb = 0.1\ndeadline_s = 60\n'
                                        'query_timeout_s = 10\npriority = 50\ncommand = ["true"]\nat_utc = "03:30"\n')
    return j


def test_off_origin_main_the_last_good_catalogue_is_kept_and_said_once_per_change(monkeypatch, tmp_path):
    w, state, lines = worker(monkeypatch, None, tmp_path)
    before = set(w.registry)
    assert before and lines == []
    state["jobs"] = grown(tmp_path)
    state["why"] = HELD
    w.reload_catalogue()
    w.reload_catalogue()
    assert set(w.registry) == before, "an integrate branch's new job never enters the catalogue"
    assert lines == [f"catalogue not reloaded: {HELD}; the last good catalogue is kept"], lines
    state["why"] = "the checkout's tracked files are edited (1 path(s))"
    w.reload_catalogue()
    w.reload_catalogue()
    assert set(w.registry) == before
    assert len(lines) == 2 and "edited" in lines[1], lines
    state["why"] = None
    w.reload_catalogue()
    assert set(w.registry) == before | {"newjob"}, "at a pushed commit of main, the merged catalogue loads"
    assert "origin/main again" in lines[2] and lines[3].startswith("catalogue reloaded"), lines


def test_a_worker_started_off_origin_main_runs_nothing_until_it_is(monkeypatch, tmp_path):
    w, state, lines = worker(monkeypatch, HELD, tmp_path)
    assert w.registry == {} and len(lines) == 1, lines
    state["why"] = None
    w.reload_catalogue()
    assert w.registry and "newjob" not in w.registry


def test_a_catalogue_passed_in_is_never_checked_or_replaced(monkeypatch, tmp_path):
    asked = []
    monkeypatch.setattr(wk, "release_state", lambda path: asked.append(path) or HELD)
    reg_, prof, rules = fx.catalogue(tmp_path)
    w = wk.Worker("t", "node2", registry=reg_, profiles=prof, rules=rules, log=lambda m: None)
    w.reload_catalogue()
    assert asked == [] and w.registry is reg_


def test_checkout_branch_asks_git_by_path(tmp_path):
    repo = tmp_path / "r"
    run = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)  # noqa: E731
    repo.mkdir()
    run("init", "-q", "-b", "main")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "one")
    (repo / "sub").mkdir()
    assert wk.checkout_branch(repo / "sub") == "main"
    run("checkout", "-q", "-b", "integrate/x")
    assert wk.checkout_branch(repo / "sub") == "integrate/x"
    run("checkout", "-q", "--detach")
    assert wk.checkout_branch(repo) == "HEAD"
    assert wk.checkout_branch(tmp_path / "nowhere") is None
    assert wk.checkout_branch(reg.JOBS.parent), "the shipped catalogue sits in a checkout git can name"


def test_release_state_asks_git_whether_the_commit_is_on_origin_main(tmp_path):
    """The real answers, from a bare origin, the main checkout and a
    release copy made by the installer's own command."""
    from support.installer import release as rel
    origin, work = tmp_path / "origin.git", tmp_path / "main"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True)
    run = lambda *a: subprocess.run(["git", "-C", str(work), "-c", "user.name=t", "-c", "user.email=t@t", *a],  # noqa: E731
                                    check=True, capture_output=True)
    run("checkout", "-q", "-b", "main")
    (work / "support" / "scheduler").mkdir(parents=True)
    (work / "support" / "scheduler" / "jobs.toml").write_text("version = 1\n")
    run("add", "-A")
    run("commit", "-q", "-m", "one")
    run("push", "-q", "origin", "main")
    cat = work / "support" / "scheduler"
    assert wk.release_state(cat) is None, "main, pushed"
    run("checkout", "-q", "-b", "integrate/x")
    (cat / "jobs.toml").write_text("version = 1\n[jobs.new]\n")
    run("commit", "-qam", "the branch")
    why = wk.release_state(cat)
    assert why and "integrate/x" in why and "not a commit of origin/main" in why
    run("checkout", "-q", "main")
    run("merge", "-q", "--no-ff", "-m", "merged, not yet pushed", "integrate/x")
    assert "not a commit of origin/main" in wk.release_state(cat), "a merge is not released until it is pushed"
    run("push", "-q", "origin", "main")
    assert wk.release_state(cat) is None
    (cat / "jobs.toml").write_text("edited\n")
    assert "edited" in wk.release_state(cat)
    assert "git cannot say" in wk.release_state(tmp_path / "nowhere")
    copy = tmp_path / "release"
    rel.release(str(copy), repo=str(work), log_path=str(tmp_path / "log"), venv=False, log=lambda m: None)
    assert wk.release_state(copy / "support" / "scheduler") is None, "the release copy always passes"
