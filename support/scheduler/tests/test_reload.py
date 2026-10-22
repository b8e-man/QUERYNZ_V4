"""The worker reads its catalogue only from a checkout on main (card
the-scheduler-s-worker-runs-the-main-checkout-…, finding 2): an integrate
branch, another branch or a detached head keeps the last good catalogue and
says why in one line, once per change. No database: the branch answer and
the catalogue are monkeypatched; one test asks git itself."""
from __future__ import annotations

import subprocess

from support.scheduler import registry as reg
from support.scheduler import worker as wk
from support.scheduler.tests import fixtures as fx


def worker(monkeypatch, branch, tmp_path):
    """A worker reading its catalogue from the files (no registry passed),
    against the fixture catalogue, with the branch answer set by `branch`."""
    j, p = fx.write(tmp_path)
    state = {"branch": branch, "jobs": j}
    monkeypatch.setattr(wk, "checkout_branch", lambda path: state["branch"])
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


def test_off_main_the_last_good_catalogue_is_kept_and_said_once_per_change(monkeypatch, tmp_path):
    w, state, lines = worker(monkeypatch, "main", tmp_path)
    before = set(w.registry)
    assert before and lines == []
    state["jobs"] = grown(tmp_path)
    state["branch"] = "integrate/procurement-1"
    w.reload_catalogue()
    w.reload_catalogue()
    assert set(w.registry) == before, "an integrate branch's new job never enters the catalogue"
    assert lines == ["catalogue not reloaded: the checkout is on integrate/procurement-1, not main; "
                     "the last good catalogue is kept"], lines
    state["branch"] = "HEAD"
    w.reload_catalogue()
    w.reload_catalogue()
    assert set(w.registry) == before
    assert len(lines) == 2 and "detached head" in lines[1], lines
    state["branch"] = None
    w.reload_catalogue()
    assert set(w.registry) == before and len(lines) == 3 and "git cannot say" in lines[2], lines
    state["branch"] = "main"
    w.reload_catalogue()
    assert set(w.registry) == before | {"newjob"}, "back on main, the merged catalogue loads"
    assert "back on main" in lines[3] and lines[4].startswith("catalogue reloaded"), lines


def test_a_worker_started_off_main_runs_nothing_until_main(monkeypatch, tmp_path):
    w, state, lines = worker(monkeypatch, "integrate/settlements-1", tmp_path)
    assert w.registry == {} and len(lines) == 1, lines
    state["branch"] = "main"
    w.reload_catalogue()
    assert w.registry and "newjob" not in w.registry


def test_a_catalogue_passed_in_is_never_checked_or_replaced(monkeypatch, tmp_path):
    asked = []
    monkeypatch.setattr(wk, "checkout_branch", lambda path: asked.append(path) or "integrate/x")
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
