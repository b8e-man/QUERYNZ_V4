"""bin/ask makes a throwaway question copy and prunes old ones; bin/fix
takes only a module folder, refuses one a build session holds, numbers its
copies and reopens a refused one. Driven against a throwaway repository."""
import os
import shutil
import subprocess
import sys
import tempfile
import time

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd, cwd, env=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    if check and p.returncode:
        raise AssertionError(f"{cmd}: {p.stdout}{p.stderr}")
    return p


@pytest.fixture
def toy():
    d = tempfile.mkdtemp()
    repo = os.path.join(d, "repo")
    os.makedirs(os.path.join(repo, "bin"))
    for sub in ("tests", "support/scheduler", "support/alarm", "keys", "links", "registers/gazette", ".claude/hooks"):
        os.makedirs(os.path.join(repo, sub))
    for tool in ("start-session", "ask", "fix", "_session.py"):
        shutil.copy(os.path.join(REPO, "bin", tool), os.path.join(repo, "bin", tool))
    with open(os.path.join(repo, "CLAUDE.md"), "w") as f:
        f.write("# toy\n\n## A question session\n\nYou change nothing: answer from what is published.\n\n## Paths\n\nx\n")
    with open(os.path.join(repo, ".gitignore"), "w") as f:
        f.write(".scope\nmerge-requests\n")
    with open(os.path.join(repo, "tests", "test_ok.py"), "w") as f:
        f.write("def test_ok():\n    assert True\n")
    sh(["git", "init", "-q", "-b", "main"], repo)
    sh(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], repo)
    sh(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"], repo)
    work = os.path.join(d, "work")
    yield {"repo": repo, "work": work, "env": {"QV4_WORK": work, "QV4_NO_DB": "1"}}
    sh(["git", "worktree", "prune"], repo, check=False)
    shutil.rmtree(d, ignore_errors=True)


def test_ask_makes_a_question_copy_with_cards_inbox_and_the_rules(toy):
    repo, work, env = toy["repo"], toy["work"], toy["env"]
    p = sh([sys.executable, "bin/ask"], repo, env)
    folders = [n for n in os.listdir(work) if n.startswith("ask-")]
    assert len(folders) == 1
    folder = os.path.join(work, folders[0])
    assert f"Start in: {folder}" in p.stdout and "You change nothing" in p.stdout
    scope = open(os.path.join(folder, ".scope")).read()
    assert "weight: question\n" in scope and scope.endswith("folders:\n")
    assert os.path.isdir(os.path.join(work, "inbox", "cards")) and os.path.isdir(os.path.join(work, "inbox", "merge-requests"))
    assert sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], folder).stdout.strip() == "HEAD"     # detached, no branch
    assert sh([sys.executable, "bin/ask", "why"], repo, env, check=False).returncode == 1


def test_ask_prunes_copies_older_than_a_day_that_nobody_sits_in(toy):
    repo, work, env = toy["repo"], toy["work"], toy["env"]
    sh([sys.executable, "bin/ask"], repo, env)
    old = [n for n in os.listdir(work) if n.startswith("ask-")][0]
    stale = time.time() - 2 * 24 * 3600
    os.utime(os.path.join(work, old), (stale, stale))
    time.sleep(1.1)
    sh([sys.executable, "bin/ask"], repo, env)
    now = [n for n in os.listdir(work) if n.startswith("ask-")]
    assert old not in now and len(now) == 1


def test_fix_takes_only_a_module_folder(toy):
    repo, env = toy["repo"], toy["env"]
    for bad in (".claude/hooks", "bin", "support", "docs/plan", "keys/names.py", "registers"):
        p = sh([sys.executable, "bin/fix", bad], repo, env, check=False)
        assert p.returncode == 1 and "not a module folder" in p.stderr, bad
    for good in ("keys", "links/", "support/scheduler", "registers/gazette/"):
        assert sh([sys.executable, "bin/fix", good], repo, env).returncode == 0, good


def test_fix_numbers_its_copies_and_reopens_a_refused_one(toy):
    repo, work, env = toy["repo"], toy["work"], toy["env"]
    p = sh([sys.executable, "bin/fix", "support/scheduler"], repo, env)
    one = os.path.join(work, "fix-support-scheduler-1")
    assert f"Start in: {one}" in p.stdout and os.path.islink(os.path.join(one, "merge-requests"))
    scope = open(os.path.join(one, ".scope")).read()
    assert "weight: fix\n" in scope and "  support/scheduler/\n" in scope
    assert sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], one).stdout.strip() == "fix/support-scheduler-1"
    p = sh([sys.executable, "bin/fix", "support/scheduler"], repo, env)
    assert f"Start in: {os.path.join(work, 'fix-support-scheduler-2')}" in p.stdout
    with open(os.path.join(work, "inbox", "merge-requests", "fix-support-scheduler-1.md"), "w") as f:
        f.write("branch: fix/support-scheduler-1\nclaims: x\nresult: REFUSED — a test failed\n")
    p = sh([sys.executable, "bin/fix", "support/scheduler"], repo, env)
    assert f"Start in: {one}" in p.stdout and "Reopened" in p.stdout


def test_fix_refuses_a_folder_a_build_session_holds(toy):
    repo, work, env = toy["repo"], toy["work"], toy["env"]
    sh([sys.executable, "bin/start-session", "sched", "support/scheduler"], repo, env)
    p = sh([sys.executable, "bin/fix", "support/scheduler"], repo, env, check=False)
    assert p.returncode == 1 and "held by the build session" in p.stderr
    assert sh([sys.executable, "bin/fix", "support/alarm"], repo, env).returncode == 0
    sh([sys.executable, "bin/start-session", "allkeys", "keys"], repo, env)
    assert sh([sys.executable, "bin/fix", "keys"], repo, env, check=False).returncode == 1
