"""The scope hook is the fence (plan: "Starting a session"). Four things it
must do, each tested here: read the scope file in the working copy; refuse
everything when there is none; allow the always-allowed paths; and outside
the repository allow writes only under the session's scratch folder. The
write shapes it sees are the old estate's (tests/test_session_scope_hook.py
at 2d3874e), carried."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, ".claude", "hooks", "scope.py")
OLD = "/home/user/Git Repos/QueryNZ_V3"
REF = "/home/user/qnz3-ref"
SESSION = "11111111-2222-3333-4444-555555555555"


def scope_text(weight="build", scratch="/tmp/qv4-test-scratch", folders=("support/scheduler/", "support/profiles/")):
    body = f"name: t\nweight: {weight}\nscratch: {scratch}\n"
    if folders:
        body += "folders:\n" + "".join(f"  {f}\n" for f in folders)
    return body


@pytest.fixture
def fake_repo():
    d = tempfile.mkdtemp()
    for sub in ("support/scheduler", "support/profiles", "registers/gazette", "cards", "lessons", "docs/status",
                "docs/decisions/queue", "docs/plan", "bin", ".claude/hooks", "merge-requests"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    with open(os.path.join(d, ".scope"), "w") as f:
        f.write(scope_text())
    yield d
    shutil.rmtree(d)


def run(repo, event, cwd=None):
    ev = dict(event)
    ev.setdefault("session_id", SESSION)
    ev.setdefault("cwd", cwd or repo)
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(ev), capture_output=True,
                       text=True, timeout=10, env={**os.environ, "CLAUDE_PROJECT_DIR": repo})
    return p.returncode, p.stderr


def edit(repo, path):
    return {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(repo, path)}}


def write(path):
    return {"tool_name": "Write", "tool_input": {"file_path": path}}


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def set_scope(repo, text):
    with open(os.path.join(repo, ".scope"), "w") as f:
        f.write(text)


# ── the four the plan names ──────────────────────────────────────────────────

def test_1_reads_the_scope_file_in_the_working_copy(fake_repo):
    assert run(fake_repo, edit(fake_repo, "support/scheduler/queue.py"))[0] == 0
    assert run(fake_repo, edit(fake_repo, "support/profiles/x.md"))[0] == 0
    rc, err = run(fake_repo, edit(fake_repo, "registers/gazette/lane.py"))
    assert rc == 2 and "outside this session's scope" in err
    assert run(fake_repo, edit(fake_repo, "keys/names.py"))[0] == 2


def test_2_no_scope_file_refuses_everything(fake_repo):
    os.remove(os.path.join(fake_repo, ".scope"))
    rc, err = run(fake_repo, edit(fake_repo, "support/scheduler/queue.py"))
    assert rc == 2 and "no scope file" in err
    assert run(fake_repo, edit(fake_repo, "cards/x.md"))[0] == 2
    assert run(fake_repo, write("/tmp/qv4-test-scratch/notes.md"))[0] == 2
    assert run(fake_repo, bash("echo hi > /tmp/anything.txt"))[0] == 2
    # reading and looking are not writes
    assert run(fake_repo, bash("git status && ls -la"))[0] == 0
    assert run(fake_repo, {"tool_name": "Read", "tool_input": {"file_path": "/etc/hosts"}})[0] == 0


def test_3_always_allowed_paths(fake_repo):
    for p in ("cards/2026-10-18-x.md", "lessons/fences.md", "docs/status/t.md",
              "docs/decisions/queue/core-limit.md", "merge-requests/t.md"):
        assert run(fake_repo, edit(fake_repo, p))[0] == 0, p
    assert run(fake_repo, bash(f"cat > {fake_repo}/cards/y.md <<'EOF'\nx\nEOF"))[0] == 0
    # generated files are never allowed to a build session; the protected paths neither
    for p in ("docs/status.md", "docs/board.md", "lessons/INDEX.md", "docs/decisions/queue.md",
              ".claude/hooks/scope.py", "bin/start-session", "docs/plan/core.md", "CLAUDE.md", ".scope"):
        rc, err = run(fake_repo, edit(fake_repo, p))
        assert rc == 2, p


def test_4_outside_the_repository_only_the_scratch_folder(fake_repo):
    assert run(fake_repo, write("/tmp/qv4-test-scratch/notes.md"))[0] == 0
    assert run(fake_repo, bash("echo x > /tmp/qv4-test-scratch/out.txt"))[0] == 0
    assert run(fake_repo, write(f"/tmp/claude-1000/-home-user-querynzv4/{SESSION}/scratchpad/a.py"))[0] == 0
    assert run(fake_repo, write("/home/user/querynzv4-work/inbox/merge-requests/t.md"))[0] == 0
    for p in ("/tmp/elsewhere.md", os.path.expanduser("~/notes.md"), "/home/user/querynzv4-work/live/stop-list.md",
              f"{OLD}/ops/x.py", f"{OLD}/ingestion/newsscrapers/registry.py",
              "/tmp/claude-1000/-home-user-querynzv4/other-session/scratchpad/a.py",
              "/home/user/.claude/projects/-home-user-querynzv4/memory/x.md"):
        rc, err = run(fake_repo, write(p))
        assert rc == 2, p
    assert run(fake_repo, bash("sed -i 's/a/b/' /tmp/outside.txt"))[0] == 2


# ── weights ──────────────────────────────────────────────────────────────────

def test_founding_and_integrator_see_the_whole_repository_and_the_protected_paths(fake_repo):
    for w in ("founding", "integrator"):
        set_scope(fake_repo, scope_text(weight=w, folders=()))
        for p in ("keys/names.py", ".claude/hooks/scope.py", "bin/start-session", "docs/plan/core.md",
                  "CLAUDE.md", "docs/status.md", "docs/board.md", ".scope"):
            assert run(fake_repo, edit(fake_repo, p))[0] == 0, (w, p)


def test_founding_may_write_the_stop_list_and_the_freeze_paths_only(fake_repo):
    set_scope(fake_repo, scope_text(weight="founding", folders=()))
    assert run(fake_repo, write("/home/user/querynzv4-work/live/stop-list.md"))[0] == 0
    assert run(fake_repo, write(f"{OLD}/ingestion/newsscrapers/registry.py"))[0] == 0
    assert run(fake_repo, write(f"{OLD}/ops/systemd/MANIFEST.json"))[0] == 0
    assert run(fake_repo, write(f"{OLD}/ingestion/SOURCES.md"))[0] == 0
    assert run(fake_repo, write(f"{OLD}/data-layer/docs/ledger/2026-10-daylogs.md"))[0] == 0
    rc, err = run(fake_repo, write(f"{OLD}/ingestion/fetchgate.py"))
    assert rc == 2 and "freeze" in err
    assert run(fake_repo, write("/tmp/elsewhere.md"))[0] == 2


def test_founding_may_write_the_reference_copy_and_a_build_session_may_not(fake_repo):
    # step 1.2: the founding session clones the old repository to the reference
    # copy, installs its environment there and later moves it to the frozen tag
    set_scope(fake_repo, scope_text(weight="founding", folders=()))
    assert run(fake_repo, write(f"{REF}/.venv/pyvenv.cfg"))[0] == 0
    assert run(fake_repo, bash(f"cd {REF} && .venv/bin/python -m pip install -e ./data-layer/testkit"))[0] == 0
    set_scope(fake_repo, scope_text())
    rc, err = run(fake_repo, write(f"{REF}/ops/x.py"))
    assert rc == 2 and "outside the repository" in err


def test_only_a_main_session_may_place_a_qv4_job_file_and_never_another(fake_repo):
    unit_dir = os.path.expanduser("~/.config/systemd/user")
    for w in ("founding", "integrator"):
        set_scope(fake_repo, scope_text(weight=w, folders=()))
        assert run(fake_repo, write(f"{unit_dir}/qv4-checks-board.service"))[0] == 0, w
        assert run(fake_repo, bash(f"cp checks/jobs/qv4-checks-board.timer {unit_dir}/qv4-checks-board.timer"))[0] == 0, w
        rc, err = run(fake_repo, write(f"{unit_dir}/ftm-release.service"))
        assert rc == 2 and "qv4-" in err, w
        assert run(fake_repo, write(f"{unit_dir}/qv4-x.service.d/override.conf"))[0] == 2, w
    set_scope(fake_repo, scope_text())
    assert run(fake_repo, write(f"{unit_dir}/qv4-checks-board.service"))[0] == 2


def test_build_session_cannot_touch_the_stop_list_or_the_old_folder(fake_repo):
    assert run(fake_repo, write("/home/user/querynzv4-work/live/stop-list.md"))[0] == 2
    rc, err = run(fake_repo, write(f"{OLD}/ops/systemd/MANIFEST.json"))
    assert rc == 2 and "live old folder" in err


def test_a_scope_file_the_hook_cannot_use_keeps_the_fix_path_open(fake_repo):
    set_scope(fake_repo, "weight: build\nfolders:\n  support/\n")   # no name, no scratch
    rc, err = run(fake_repo, edit(fake_repo, "support/scheduler/x.py"))
    assert rc == 2 and "cannot be used" in err
    assert run(fake_repo, edit(fake_repo, ".scope"))[0] == 0
    set_scope(fake_repo, scope_text(weight="heavy"))
    rc, err = run(fake_repo, edit(fake_repo, "support/scheduler/x.py"))
    assert rc == 2 and "weight" in err


# ── the carried write shapes ─────────────────────────────────────────────────

def _out(repo, p="registers/gazette/x.py"):
    return os.path.join(repo, p)


def _in(repo, p="support/scheduler/x.py"):
    return os.path.join(repo, p)


COPY_SHAPES = [
    "install -m 644 a.service {t}", "install -d {t}", "install -t {t} a b", "rsync -a src/ {t}",
    "dd if=/dev/zero of={t} bs=1 count=1", "ln -s a {t}", "patch {t} < fix.diff", "patch -p0 -o {t} < fix.diff",
    "rm {t}", "sudo nice -n 5 rm {t}", "truncate -s 0 {t}", "touch {t}", "git checkout -- {t}",
    "git checkout HEAD~1 -- {t}", "git restore --staged {t}", "git -C /tmp mv {s} {t}", "git mv {t} {s}", "git rm {t}",
    "perl -pi -e 's/a/b/' {t}", "perl -i.bak -ne 'print' {t}", "python3 -c \"open('{t}', 'w').write('x')\"",
    "perl -e 'open(F, \">\", \"{t}\"); print F 1'", "bash -c 'echo hi > {t}'", "sh -lc 'echo hi > {t}'",
    "eval 'echo hi > {t}'", "ssh -o ConnectTimeout=8 user@10.0.0.1 'echo hi > {t}'",
    "bash <<'EOF'\necho hi > {t}\nEOF", "python3 - <<'EOF'\nimport pathlib\npathlib.Path('{t}').write_text('x')\nEOF",
    ".venv/bin/python - <<'EOF'\nimport os\nos.rename('{s}', '{t}')\nEOF",
    "cd /tmp && python3 - <<'EOF'\nimport shutil\nshutil.move('{s}', '{t}')\nEOF",
]


@pytest.mark.parametrize("shape", COPY_SHAPES, ids=[s.split("\n")[0][:40] for s in COPY_SHAPES])
def test_write_shape_out_of_scope_refused_in_scope_allowed(fake_repo, shape):
    rc, err = run(fake_repo, bash(shape.format(t=_out(fake_repo), s=_in(fake_repo))))
    assert rc == 2 and "outside this session's scope" in err, f"not seen: {shape!r} ({err})"
    rc, err = run(fake_repo, bash(shape.format(t=_in(fake_repo), s=_in(fake_repo, "support/scheduler/y.py"))))
    assert rc == 0, f"in-scope refused: {shape!r} ({err})"
    rc, err = run(fake_repo, bash(shape.format(t="/tmp/qv4-test-scratch/x.py", s="/tmp/qv4-test-scratch/y.py")))
    assert rc == 0, f"scratch refused: {shape!r} ({err})"


UNRESOLVABLE_SHAPES = ["patch -p1 < fix.diff", "git stash pop", "git stash apply", "git clean -fd",
                       "git reset --hard HEAD~1", "git apply fix.diff", "git am mbox"]


@pytest.mark.parametrize("shape", UNRESOLVABLE_SHAPES)
def test_writes_the_hook_cannot_resolve_are_refused(fake_repo, shape):
    rc, err = run(fake_repo, bash(shape))
    assert rc == 2 and "cannot see which files" in err, shape


def test_unresolvable_lookalikes_pass(fake_repo):
    for c in ("git stash list", "git stash", "git reset HEAD", "git checkout main", "git checkout -b feat",
              "git log --oneline -3", "git status", "rm -f /tmp/qv4-test-scratch/x.lock",
              "rsync -a src/ node1:/home/user/x/", "git worktree add /home/user/querynzv4-work/x -b x main"):
        assert run(fake_repo, bash(c))[0] == 0, c


def test_heredoc_bodies_and_operators_are_not_targets(fake_repo):
    ok = f"""cat > {fake_repo}/support/scheduler/pyproject.toml <<'EOF'
requires = ["setuptools>=68"]
> a blockquote line
x > {fake_repo}/registers/gazette/not_a_target.py
EOF
echo done"""
    assert run(fake_repo, bash(ok))[0] == 0
    assert run(fake_repo, bash("ls 2>&1 | grep x; cmd &> /dev/null; test 3 >= 2"))[0] == 0
    assert run(fake_repo, bash(f"cat > {fake_repo}/registers/gazette/x.py <<'EOF'\nharmless\nEOF"))[0] == 2


def test_unexpanded_variable_target_refused(fake_repo):
    rc, err = run(fake_repo, bash("D=/x; cat > $D/pyproject.toml <<'EOF'\nx\nEOF"))
    assert rc == 2 and "unexpanded variable" in err


def test_angle_brackets_in_prose_are_not_redirects(fake_repo):
    msg = 'git commit -q -m "x\n\nCo-Authored-By: Claude <noreply@anthropic.com>" && git push origin main'
    assert run(fake_repo, bash(msg))[0] == 0
    assert run(fake_repo, bash(f"echo 2> {fake_repo}/registers/gazette/err.log"))[0] == 2


def test_sed_script_is_not_a_target(fake_repo):
    assert run(fake_repo, bash(f"sed -i 's/| n agrees on a 1 % sample |/| 10 % |/' {fake_repo}/support/scheduler/README.md"))[0] == 0
    assert run(fake_repo, bash(f"sed -i -e 's#a/b#c#' {fake_repo}/registers/gazette/x.py"))[0] == 2


def test_a_relative_write_is_judged_where_the_command_cd_ed(fake_repo):
    cmd = (f'cd "{fake_repo}/support/scheduler" && python3 - <<\'EOF\'\n'
           'p = "test_queue.py"; s = open(p, encoding="utf-8").read()\n'
           'open(p, "w", encoding="utf-8").write(s)\n'
           'EOF')
    assert run(fake_repo, bash(cmd))[0] == 0
    cmd = (f'cd "{fake_repo}/registers/gazette" && python3 - <<\'EOF\'\n'
           'open("lane.py", "w").write("x")\n'
           'EOF')
    assert run(fake_repo, bash(cmd))[0] == 2


def test_the_events_cwd_is_where_relative_targets_resolve(fake_repo):
    assert run(fake_repo, bash("echo x > queue.py"), cwd=os.path.join(fake_repo, "support/scheduler"))[0] == 0
    assert run(fake_repo, bash("echo x > lane.py"), cwd=os.path.join(fake_repo, "registers/gazette"))[0] == 2


def test_a_filename_in_the_content_is_not_a_target(fake_repo):
    cmd = ("python3 - <<'EOF'\n"
           'from pathlib import Path\n'
           'p = Path("support/scheduler/thing.py"); s = p.read_text()\n'
           'new = """\nSTATE = os.path.join("registers", "gazette", "finders.json")\n"""\n'
           's = s.replace("old", new)\n'
           'p.write_text(s)\n'
           'EOF')
    rc, err = run(fake_repo, bash(cmd))
    assert rc == 0, err


def test_a_batch_edit_over_a_dict_of_paths_is_seen(fake_repo):
    cmd = ("python3 - <<'EOF'\n"
           'fixes = {"support/scheduler/a.py": 1, "registers/gazette/b.py": 2}\n'
           'for p, n in fixes.items():\n'
           '    open(p, "w").write("x")\n'
           'EOF')
    rc, err = run(fake_repo, bash(cmd))
    assert rc == 2 and "registers/gazette/b.py" in err, err


def test_a_path_built_at_run_time_is_refused_not_ignored(fake_repo):
    cmd = "python3 - <<'EOF'\nimport os\nopen(os.environ[\"P\"], \"w\").write(\"x\")\nEOF"
    rc, err = run(fake_repo, bash(cmd))
    assert rc == 2 and "run time" in err, err


def test_module_level_writes_are_still_caught(fake_repo):
    for body in ('import os\nos.rename("support/scheduler/a.py", "registers/gazette/b.py")',
                 'import shutil\nshutil.move("support/scheduler/a.py", "registers/gazette/b.py")',
                 'import os\nos.remove("registers/gazette/b.py")',
                 'from shutil import rmtree\nrmtree("registers/gazette/b")',
                 'from pathlib import Path\nPath("registers/gazette/b.py").unlink()'):
        rc, err = run(fake_repo, bash("python3 - <<'EOF'\n" + body + "\nEOF"))
        assert rc == 2, f"not caught: {body}"


def test_a_body_that_only_reads_names_no_target(fake_repo):
    out = _out(fake_repo)
    assert run(fake_repo, bash(f"python3 - <<'EOF'\nprint(open('{out}').read())\nEOF"))[0] == 0
    assert run(fake_repo, bash(f"python3 -c \"print(open('{out}').read())\""))[0] == 0
    assert run(fake_repo, bash(f"perl -ne 'print' {out}"))[0] == 0


# ── step 1b.1: the question and fix weights ──────────────────────────────────

def test_a_question_session_changes_nothing_inside_the_repository(fake_repo):
    set_scope(fake_repo, scope_text(weight="question", folders=()))
    for p in ("keys/names.py", "cards/x.md", "lessons/x.md", "docs/status/t.md", "docs/decisions/queue/q.md", "README.md"):
        rc, err = run(fake_repo, edit(fake_repo, p))
        assert rc == 2 and "changes nothing" in err, p
    assert run(fake_repo, bash(f"echo x > {fake_repo}/keys/notes.txt"))[0] == 2
    assert run(fake_repo, write("/tmp/qv4-test-scratch/working.md"))[0] == 0
    assert run(fake_repo, write("/home/user/querynzv4-work/inbox/cards/a-fault.md"))[0] == 0
    assert run(fake_repo, write("/home/user/querynzv4-work/inbox/merge-requests/t.md"))[0] == 2
    assert run(fake_repo, write("/home/user/querynzv4-work/live/stop-list.md"))[0] == 2
    assert run(fake_repo, write(f"{OLD}/ingestion/newsscrapers/registry.py"))[0] == 2


def test_a_fix_session_is_fenced_like_a_build_session(fake_repo):
    set_scope(fake_repo, scope_text(weight="fix", folders=("support/scheduler/",)))
    assert run(fake_repo, edit(fake_repo, "support/scheduler/queue.py"))[0] == 0
    assert run(fake_repo, edit(fake_repo, "support/profiles/x.py"))[0] == 2
    assert run(fake_repo, edit(fake_repo, "lessons/x.md"))[0] == 0
    for p in (".claude/hooks/scope.py", "bin/fix", "docs/plan/core.md", "CLAUDE.md", ".scope"):
        rc, err = run(fake_repo, edit(fake_repo, p))
        assert rc == 2 and "founding or integrator" in err, p
    assert run(fake_repo, write("/home/user/querynzv4-work/inbox/merge-requests/t.md"))[0] == 0
    assert run(fake_repo, write("/home/user/querynzv4-work/inbox/cards/t.md"))[0] == 2
