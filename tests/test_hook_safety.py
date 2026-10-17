"""The safety hook must refuse the irreversible shapes and FAIL CLOSED. Drives
the hook exactly as Claude Code does: JSON on stdin, exit status is the
verdict (0 = allow, 2 = refuse). The carried cases are the old estate's
(tests/test_autonomy_denylist.py at 2d3874e); the new estate's four
additions follow them."""
import json
import os
import subprocess
import sys
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, ".claude", "hooks", "safety.py")
OLD = "/home/user/Git Repos/QueryNZ_V3"


@pytest.fixture
def fake_repo(tmp_path):
    """A working copy with a scope file of the given weight, and a stop list
    of its own so the live one is never read or touched."""
    def make(weight="build", stop=""):
        d = tmp_path / "repo"
        d.mkdir(exist_ok=True)
        (d / ".scope").write_text(f"name: t\nweight: {weight}\nscratch: {tmp_path}/scratch\nfolders:\n  support/\n")
        (tmp_path / "stop-list.md").write_text(stop)
        return str(d)
    return make


def run(event, repo=None, stop_list=None):
    data = event if isinstance(event, str) else json.dumps(event)
    env = {**os.environ}
    if repo:
        env["CLAUDE_PROJECT_DIR"] = repo
    env["QV4_STOP_LIST"] = stop_list or os.path.join(tempfile.gettempdir(), "qv4-no-such-stop-list.md")
    p = subprocess.run([sys.executable, HOOK], input=data, capture_output=True, text=True, timeout=10, env=env)
    return p.returncode, p.stderr


def bash(cmd: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def read(path: str) -> dict:
    return {"tool_name": "Read", "tool_input": {"file_path": path}}


BLOCKED = [
    # 1. recursive delete, in every spelling
    bash("rm -rf build/"), bash("rm -fr /tmp/x"), bash("rm -r -f x"),
    bash("cd data && rm -rf ."), bash("sudo rm -rf /var/lib/pg"),
    bash("find . -name '*.pyc' | xargs rm -rf"),
    # 2. DROP / TRUNCATE on a live database
    bash('psql "$DSN" -c "DROP TABLE v3.claims"'),
    bash("psql -h 10.0.0.1 incoming_news -c 'truncate articles'"),
    bash('psql "$DSN" -f drop_schema.sql'),
    bash('.venv/bin/python -c "conn.execute(\'TRUNCATE TABLE mentions\')"'),
    bash("echo 'drop schema v3 cascade' | psql"),
    bash('psql "$DSN" <<EOF\nTRUNCATE articles;\nEOF'),
    bash(".venv/bin/python - <<'EOF'\nconn.execute(\"DROP TABLE IF EXISTS v3.claims\")\nEOF"),
    # 3. force push
    bash("git push --force origin main"), bash("git push -f"),
    bash("git push --force-with-lease origin main"), bash("git push origin +main"),
    # 4. credentials
    read(os.path.expanduser("~/.querynz/v4.env")),
    read("/home/user/.querynz/v4.env"),
    bash("cat ~/.querynz/v4.env"),
    bash("grep -r DSN /home/user/.querynz/"),
    bash("sed -n 1,5p ~/.querynz/x.env"),
    bash("source ~/.querynz/v4.env && env"),
    # 5. the same shapes carried by a remote or nested shell
    bash("ssh user@10.0.0.1 'rm -rf /var/lib/pgsql/data'"),
    bash('ssh node1 "psql -d extractions -c \'DROP TABLE v3.claims\'"'),
    bash("ssh -o ConnectTimeout=8 user@10.0.0.1 'cat ~/.querynz/factory-db.env'"),
    bash("bash -c 'rm -rf build'"), bash('sh -c "psql \\"$DSN\\" -c \\"truncate articles\\""'),
    bash("bash -lc 'git push --force origin main'"),
    # 6. destructive postgres CLIs carry no SQL text
    bash("dropdb extractions"), bash("sudo -u postgres dropdb -f incoming_news"),
    bash("ssh node1 'dropuser querynz'"),
    # 7. the audited bypasses
    bash('psql "$DSN" --file=drop_schema.sql'),
    bash('psql "$DSN" -c "\\i drop_schema.sql"'),
    bash('psql "$DSN" < drop_schema.sql'),
    bash('cat drop_schema.sql | psql "$DSN"'),
    bash("PSQL=\"psql $DSN\"; echo 'drop table v3.claims' | $PSQL"),
    bash('psql "$DSN" -c "DROP /* x */ TABLE v3.claims"'),
    bash('psql "$DSN" -c "DROP TABLE -- x\nv3.claims"'),
    bash("psql \"$DSN\" -c 'TRUNCATE articles RESTART IDENTITY'"),
    bash("sudo -iu postgres dropdb extractions"),
    bash("/usr/bin/rm -rf build/"), bash("/bin/rm -r build/"),
    bash("eval 'rm -rf build'"), bash("eval rm -rf build"),
    bash("nice -n 10 dropdb extractions"),
    bash("systemd-run --user --unit=x rm -r build"),
    bash("find . -name '*.pyc' -delete"),
    bash("rm -r build/"),
    bash("/usr/bin/git push -f origin main"),
    bash("git push --mirror origin"), bash("git push origin :old-branch"), bash("git push origin --delete old"),
    bash("find . -name x | xargs -I{} sh -c 'rm -rf {}'"),
    bash("F=~/.querynz/x.env; cat $F"),
    bash('export F=/home/user/.querynz/x.env && head -1 "$F"'),
    bash("find ~/.querynz -type f -exec cat {} \\;"),
    bash("find ~/.querynz -type f | xargs cat"),
    bash("cat ~/.query*/x.env"), bash("cat /home/*/.querynz/x.env"), bash("cd ~ && cat .querynz/x.env"),
    bash("cat /proc/1234/environ"), bash("tr '\\0' '\\n' < /proc/$(pgrep -x llama-server)/environ"),
    {"tool_name": "Grep", "tool_input": {"pattern": "DSN", "path": "/home/user/.querynz"}},
    {"tool_name": "Glob", "tool_input": {"pattern": "**/.querynz/*.env"}},
    {"tool_name": "Glob", "tool_input": {"pattern": "*.env", "path": os.path.expanduser("~/.querynz")}},
    {"tool_name": "Read", "tool_input": {"file_path": "/proc/self/environ"}},
    # ── the new estate's four additions (step 1.1) ──
    # 5. a release without --dry-run publishes to the public site
    bash("python3 ops/pi_release.py"),
    bash(f'cd "{OLD}" && .venv/bin/python ops/pi_release.py --verbose'),
    bash(f'"{OLD}/.venv/bin/python" "{OLD}/ops/pi_release.py"'),
    # 6. deploy tools
    bash("python3 ops/pi_cloudflare.py"), bash("wrangler pages deploy dist"),
    bash(f'ssh node1 "cd \'{OLD}\' && python3 ops/pi_cloudflare.py"'),
    # 7. job control without the prefix, and the carve-out whatever the list says
    bash("systemctl --user stop querynz-crawler.service"),
    bash("systemctl --user disable --now v3-extract.timer"),
    bash("systemctl --user restart newsscrapers"),
    bash("ssh node1 'systemctl --user stop gazette-derive.timer'"),
    bash("sudo systemctl restart postgresql-18.service"),
    bash("systemctl --user stop ec-disclosures.timer"),
    bash("systemctl --user restart querynz-gpu-gateway"),
    bash("systemctl --user disable ftm-release.timer"),
    bash("systemctl --user mask querynz-vip.service"),
    bash("systemctl --user kill querynz-agent-llm"),
    # 8. writes and runs in the live old folder
    bash(f'echo x > "{OLD}/ops/x.py"'),
    bash(f'sed -i "s/a/b/" "{OLD}/ingestion/fetchgate.py"'),
    bash(f'cd "{OLD}" && .venv/bin/pytest tests/test_invariants.py'),
    bash(f'cd "{OLD}" && python3 ops/board.py'),
    bash(f'"{OLD}/.venv/bin/python" "{OLD}/ops/lessons_for.py" hooks'),
    {"tool_name": "Write", "tool_input": {"file_path": f"{OLD}/ops/x.py"}},
    {"tool_name": "Edit", "tool_input": {"file_path": f"{OLD}/ingestion/newsscrapers/registry.py"}},  # not founding
    bash(f'git -C "{OLD}" commit -m x'),
    bash(f'cd "{OLD}" && git add ops/systemd/MANIFEST.json && git commit -m freeze'),
]

ALLOWED = [
    bash("rm build/x.pyc"), bash("rm -f /tmp/x.lock"),
    bash("git push origin main"), bash("git log --oneline -5"),
    bash('psql "$DSN" -Atc "select count(*) from v3.claims"'),
    bash("grep -n 'DROP TABLE' registers/gazette/schema.sql"),
    bash("export V4=$(grep ^QV4_OWNER_URL= ~/.querynz/v4.env | cut -d= -f2-); psql \"$V4\" -c 'select 1'"),
    bash("ls ~/.querynz/"),
    bash(".venv/bin/python - <<'EOF'\ns = 'the hook blocks on DROP/TRUNCATE or on a file it cannot read'\nopen('x.md','w').write(s)\nEOF"),
    bash("git commit -m 'safety: DROP/TRUNCATE against a live database now judged per statement'"),
    read("/home/user/querynzv4/docs/PLAN.md"),
    bash("ssh user@10.0.0.1 'ls ~/.querynz/; systemctl --user is-active v3-extract.service'"),
    bash("bash -c 'ls -la build && rm -f build/x.lock'"),
    bash("bash /tmp/claude-1000/scratch/launcher.sh"),
    {"tool_name": "Edit", "tool_input": {"file_path": "x.py"}},
    bash("find . -name '*.pyc' -exec rm {} \\;"),
    bash("timeout 60 psql \"$DSN\" -Atc 'select 1'"),
    bash("xargs -n1 echo < list.txt"),
    bash("git push origin main --tags"), bash("git stash drop"),
    bash("git commit -m 'docs: drop the old table of contents; truncate the ledger header'"),
    bash("find ~/.querynz -name '*.env'"), bash("ls -la ~/.querynz/ | wc -l"),
    bash("F=~/.querynz/x.env; K=$(grep ^KEY= $F | cut -d= -f2-); echo ${#K}"),
    bash("cat /proc/cpuinfo | head -3"), bash("cat /proc/self/status"),
    bash('git commit -q -m "safety: reads the file a psql is handed\n\nCo-Authored-By: Claude <noreply@anthropic.com>"'),
    {"tool_name": "Grep", "tool_input": {"pattern": "querynz", "path": "/home/user/querynzv4/support"}},
    {"tool_name": "Glob", "tool_input": {"pattern": "**/*.env.example"}},
    # the new estate: its own jobs, reads of the old folder, the dry run's lookalikes
    bash("systemctl --user restart qv4-watcher.service"),
    bash("systemctl --user disable --now qv4-checks.timer"),
    bash("systemctl --user stop qv4-worker@1.service"),
    bash("systemctl --user status ftm-release.timer"),
    bash("systemctl --user is-active ec-disclosures.timer"),
    bash("systemctl --user list-timers"),
    bash("systemctl --user start querynz-crawler.service"),     # starting is not stopping
    bash(f'cat "{OLD}/ingestion/fetchgate.py"'),
    bash(f'grep -rn robots "{OLD}/ingestion/" | head'),
    bash(f'git -C "{OLD}" log --oneline -3'),
    bash(f'cd "{OLD}" && git status --short | head'),
    bash("python3 ops/pi_release.py --dry-run"),
    bash("grep -n 'pi_release.py' docs/plan/step-1.md"),
    bash("echo 'never run pi_cloudflare.py' >> docs/status.md"),
    bash("/home/user/qnz3-ref/.venv/bin/pytest /home/user/qnz3-ref/tests/test_fetchgate.py"),
]


@pytest.mark.parametrize("event", BLOCKED, ids=[json.dumps(e["tool_input"])[:60] for e in BLOCKED])
def test_irreversibles_are_refused(event, fake_repo):
    rc, err = run(event, repo=fake_repo("build"))
    assert rc == 2, f"allowed: {event} ({err})"
    assert err.strip(), "a refusal must say why"


@pytest.mark.parametrize("event", ALLOWED, ids=[json.dumps(e["tool_input"])[:60] for e in ALLOWED])
def test_ordinary_work_passes(event, fake_repo):
    rc, err = run(event, repo=fake_repo("build"))
    assert rc == 0, f"refused: {event} ({err})"


@pytest.mark.parametrize("garbage", ["", "not json", "{}", '{"tool_name": "Bash"}',
                                     '{"tool_name": "Bash", "tool_input": null}'])
def test_fails_closed_on_malformed_input(garbage):
    rc, _ = run(garbage)
    assert rc == 2


def test_a_readable_sql_file_without_ddl_passes(tmp_path):
    f = tmp_path / "q.sql"
    f.write_text("select count(*) from v3.claims;\n")
    for shape in (f'psql "$DSN" -f {f}', f'psql "$DSN" --file={f}', f'psql "$DSN" < {f}', f'cat {f} | psql "$DSN"',
                  f'psql "$DSN" -c "\\i {f}"'):
        rc, err = run(bash(shape))
        assert rc == 0, f"{shape}: {err}"
    f.write_text("-- tidy\ntruncate v3.claims;\n")
    for shape in (f'psql "$DSN" --file={f}', f'psql "$DSN" < {f}', f'cat {f} | psql "$DSN"', f'psql "$DSN" -c "\\ir {f}"'):
        rc, err = run(bash(shape))
        assert rc == 2 and "TRUNCATE" in err, shape


def test_stop_list_lets_a_listed_job_stop_but_never_the_carve_out(fake_repo, tmp_path):
    repo = fake_repo("founding", stop="# step 1.4 batch 1\nquerynz-crawler\nv3-extract.timer\nftm-release\n")
    sl = str(tmp_path / "stop-list.md")
    assert run(bash("systemctl --user stop querynz-crawler.service"), repo, sl)[0] == 0
    assert run(bash("systemctl --user disable --now v3-extract.timer"), repo, sl)[0] == 0
    assert run(bash("ssh node1 'systemctl --user disable --now v3-extract.timer'"), repo, sl)[0] == 0
    rc, err = run(bash("systemctl --user stop querynz-sweep.timer"), repo, sl)
    assert rc == 2 and "stop list" in err
    rc, err = run(bash("systemctl --user stop ftm-release.timer"), repo, sl)   # listed, and still refused
    assert rc == 2 and "carve-out" in err
    rc, err = run(bash("systemctl --user restart querynz-vision-ocr"), repo, sl)
    assert rc == 2 and "carve-out" in err


def test_founding_session_may_make_the_freeze_commits_and_nothing_else_in_the_old_folder(fake_repo):
    repo = fake_repo("founding")
    ok = [
        {"tool_name": "Edit", "tool_input": {"file_path": f"{OLD}/ingestion/newsscrapers/registry.py"}},
        {"tool_name": "Edit", "tool_input": {"file_path": f"{OLD}/ops/systemd/MANIFEST.json"}},
        bash(f'cd "{OLD}" && git add ops/systemd/MANIFEST.json && git commit -m "freeze: manifest"'),
        bash(f'git -C "{OLD}" tag v3-frozen'),
        bash(f'cd "{OLD}" && .venv/bin/python ops/pi_release.py --dry-run'),
    ]
    for ev in ok:
        rc, err = run(ev, repo)
        assert rc == 0, f"{ev}: {err}"
    bad = [
        {"tool_name": "Edit", "tool_input": {"file_path": f"{OLD}/ingestion/fetchgate.py"}},
        bash(f'echo x >> "{OLD}/ops/pi_release.py"'),
        bash(f'cd "{OLD}" && .venv/bin/pytest tests/test_invariants.py'),
        bash(f'cd "{OLD}" && .venv/bin/python ops/pi_release.py'),
    ]
    for ev in bad:
        rc, err = run(ev, repo)
        assert rc == 2, f"allowed: {ev}"


def test_no_scope_file_means_no_weight_and_the_old_folder_is_closed(tmp_path):
    repo = tmp_path / "bare"
    repo.mkdir()
    rc, _ = run({"tool_name": "Edit", "tool_input": {"file_path": f"{OLD}/ops/systemd/MANIFEST.json"}}, str(repo))
    assert rc == 2
