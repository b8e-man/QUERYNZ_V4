"""The launcher makes a fenced working copy; the merge gate refuses a branch
with a failing test and merges one that passes. Both are driven against a
throwaway repository so the real main checkout and working copies are never
touched."""
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCHER = os.path.join(REPO, "bin", "start-session")
GATE = os.path.join(REPO, "bin", "merge-gate")


def sh(cmd, cwd, env=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    if check and p.returncode:
        raise AssertionError(f"{cmd}: {p.stdout}{p.stderr}")
    return p


@pytest.fixture
def toy():
    """A git repository shaped like ours, with a passing test on main, a
    work directory of its own, and the launcher and gate copied in."""
    d = tempfile.mkdtemp()
    repo = os.path.join(d, "repo")
    os.makedirs(os.path.join(repo, "bin"))
    for sub in ("tests", "support/scheduler", "docs/briefs", "keys"):
        os.makedirs(os.path.join(repo, sub))
    shutil.copy(LAUNCHER, os.path.join(repo, "bin", "start-session"))
    shutil.copy(GATE, os.path.join(repo, "bin", "merge-gate"))
    with open(os.path.join(repo, "tests", "test_ok.py"), "w") as f:
        f.write("def test_ok():\n    assert True\n")
    with open(os.path.join(repo, "pytest.ini"), "w") as f:
        f.write("[pytest]\ntestpaths = tests\naddopts = -p no:cacheprovider -q\n")
    with open(os.path.join(repo, ".gitignore"), "w") as f:
        f.write(".scope\nmerge-requests\n")
    sh(["git", "init", "-q", "-b", "main"], repo)
    sh(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], repo)
    sh(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"], repo)
    yield {"repo": repo, "work": os.path.join(d, "work"), "env": {"QV4_WORK": os.path.join(d, "work"),
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}}
    sh(["git", "worktree", "prune"], repo, check=False)
    shutil.rmtree(d, ignore_errors=True)


def test_launcher_makes_a_fenced_working_copy(toy):
    repo, work, env = toy["repo"], toy["work"], toy["env"]
    p = sh([sys.executable, "bin/start-session", "sched", "support/scheduler", "keys"], repo, env)
    folder = os.path.join(work, "sched")
    assert f"Start in: {folder}" in p.stdout and "Brief to paste" in p.stdout
    scope = open(os.path.join(folder, ".scope")).read()
    assert scope == f"name: sched\nweight: build\nscratch: {work}/scratch/sched\nfolders:\n  support/scheduler/\n  keys/\n"
    assert os.path.isdir(os.path.join(work, "scratch", "sched"))
    assert os.path.islink(os.path.join(folder, "merge-requests"))
    assert os.path.isdir(os.path.join(work, "inbox", "merge-requests"))
    assert sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], folder).stdout.strip() == "session/sched"
    # a name is used once; a folder must exist and be a module root
    assert sh([sys.executable, "bin/start-session", "sched", "keys"], repo, env, check=False).returncode == 1
    assert sh([sys.executable, "bin/start-session", "other", "nope"], repo, env, check=False).returncode == 1
    assert sh([sys.executable, "bin/start-session", "Bad Name", "keys"], repo, env, check=False).returncode == 1


def test_launcher_takes_the_brief_from_next_md(toy):
    repo, env = toy["repo"], toy["env"]
    with open(os.path.join(repo, "docs", "briefs", "next.md"), "w") as f:
        f.write("# next\n\n## gaz\n\nLauncher: bin/start-session gaz keys\n\nDo the gazette lane.\n\n## other\n\nnot this\n")
    p = sh([sys.executable, "bin/start-session", "gaz", "keys"], repo, env)
    assert "Do the gazette lane." in p.stdout and "not this" not in p.stdout


def test_launcher_main_writes_the_whole_repository_scope(toy):
    repo, work, env = toy["repo"], toy["work"], toy["env"]
    p = sh([sys.executable, "bin/start-session", "--main", "integrator"], repo, env)
    scope = open(os.path.join(repo, ".scope")).read()
    assert "weight: integrator\n" in scope and "folders:\n  .\n" in scope
    assert f"Start in: {repo}" in p.stdout
    assert sh([sys.executable, "bin/start-session", "--main", "build"], repo, env, check=False).returncode == 1


def _branch_with_test(toy, name, body):
    repo, env = toy["repo"], toy["env"]
    sh(["git", "checkout", "-q", "-b", name], repo, env)
    with open(os.path.join(repo, "tests", f"test_{name}.py"), "w") as f:
        f.write(body)
    sh(["git", "add", "-A"], repo, env)
    sh(["git", "commit", "-q", "-m", name], repo, env)
    sh(["git", "checkout", "-q", "main"], repo, env)


def test_gate_refuses_a_failing_branch_and_merges_a_passing_one(toy):
    repo, work, env = toy["repo"], toy["work"], toy["env"]
    _branch_with_test(toy, "red", "def test_red():\n    assert 1 == 2\n")
    _branch_with_test(toy, "green", "def test_green():\n    assert 1 == 1\n")
    before = sh(["git", "rev-parse", "main"], repo).stdout
    p = sh([sys.executable, "bin/merge-gate", "red"], repo, env, check=False)
    assert p.returncode == 1 and p.stdout.startswith("REFUSED red")
    assert sh(["git", "rev-parse", "main"], repo).stdout == before, "a refused branch must not move main"
    assert os.path.isfile(os.path.join(work, "gate", "red.log"))
    assert not os.path.exists(os.path.join(work, "gate", "red")), "the gate working copy is removed"
    p = sh([sys.executable, "bin/merge-gate", "green", "--no-merge"], repo, env)
    assert p.stdout.startswith("GREEN green")
    assert sh(["git", "rev-parse", "main"], repo).stdout == before
    p = sh([sys.executable, "bin/merge-gate", "green"], repo, env)
    assert p.stdout.startswith("MERGED green")
    log = sh(["git", "log", "--oneline", "-1", "main"], repo).stdout
    assert "merge green: gate green" in log
    assert sh([sys.executable, "bin/merge-gate", "nope"], repo, env, check=False).returncode == 1


def test_gate_refuses_to_merge_from_a_dirty_or_wrong_checkout(toy):
    repo, env = toy["repo"], toy["env"]
    _branch_with_test(toy, "green", "def test_green():\n    assert 1 == 1\n")
    with open(os.path.join(repo, "tests", "test_ok.py"), "a") as f:
        f.write("# dirty\n")
    p = sh([sys.executable, "bin/merge-gate", "green"], repo, env, check=False)
    assert p.returncode == 1 and "uncommitted" in p.stderr
    sh(["git", "checkout", "-q", "--", "tests/test_ok.py"], repo)
    sh(["git", "checkout", "-q", "green"], repo)
    p = sh([sys.executable, "bin/merge-gate", "green"], repo, env, check=False)
    assert p.returncode == 1 and "must be on main" in p.stderr
