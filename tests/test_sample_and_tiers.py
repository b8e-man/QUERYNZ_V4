"""The sample (1b.6) and the two tiers (1b.7): lists are hashes and keys
only; every module with a list fills its own tables through its own code;
two fills of different schemas run side by side; the fast tier fails an
unmarked six-second test; the full tier's loading step takes only touched
modules that carry a load.py; the nightly record reaches the board."""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading

import pytest

from checks import full_tier
from support import sample, staging

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeConn:
    """Records the SQL it is given; schemas and rows are kept per fake."""

    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.store.setdefault("sql", []).append(sql)

    def commit(self):
        self.store["commits"] = self.store.get("commits", 0) + 1


def toy_repo(with_sample=True):
    d = tempfile.mkdtemp()
    for sub in ("registers/gazette", "keys", "tests"):
        os.makedirs(os.path.join(d, sub))
    if with_sample:
        with open(os.path.join(d, "registers", "gazette", "sample.list"), "w") as f:
            f.write("# two notices\n" + "a" * 64 + "\nkey: notice-2024-1\n")
        with open(os.path.join(d, "registers", "gazette", "sample.py"), "w") as f:
            f.write("def fill(conn, schema, items):\n    conn.execute(f'CREATE TABLE {schema}.notices (k text)')\n"
                    "    for it in items:\n        conn.execute(f'INSERT INTO {schema}.notices VALUES (%s)', (it,))\n    return len(items)\n")
    return d


def test_lists_are_hashes_and_keys_only(tmp_path):
    p = tmp_path / "sample.list"
    p.write_text("# ok\n" + "b" * 64 + "\nkey: x\n")
    assert sample.read_list(str(p)) == ["b" * 64, "key: x"]
    p.write_text("12 Example Street\n")
    with pytest.raises(ValueError):
        sample.read_list(str(p))


def test_fill_schema_runs_every_modules_own_code(monkeypatch, tmp_path):
    d = toy_repo()
    monkeypatch.setattr(sample, "WORK", str(tmp_path))
    try:
        store = {}
        out = sample.fill_schema("scratch_t1", lambda: FakeConn(store), d, log=lambda *a: None)
        assert out == {"registers/gazette": 2}
        assert "CREATE SCHEMA IF NOT EXISTS scratch_t1" in store["sql"] and "CREATE SCHEMA IF NOT EXISTS scratch_t1_private" in store["sql"]
        assert "CREATE TABLE scratch_t1.notices (k text)" in store["sql"]
        with pytest.raises(ValueError):
            sample.fill_schema("bad name", lambda: FakeConn({}), d, log=lambda *a: None)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_two_fills_of_different_schemas_at_the_same_time_do_not_disturb_each_other(monkeypatch, tmp_path):
    d = toy_repo()
    monkeypatch.setattr(sample, "WORK", str(tmp_path))
    stores = {"a": {}, "b": {}}
    errors = []

    def go(name):
        try:
            sample.fill_schema(f"scratch_{name}", lambda: FakeConn(stores[name]), d, log=lambda *a: None)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)
    try:
        ts = [threading.Thread(target=go, args=(n,)) for n in ("a", "b")]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        assert not errors
        assert any("scratch_a.notices" in s for s in stores["a"]["sql"]) and not any("scratch_b" in s for s in stores["a"]["sql"])
        assert any("scratch_b.notices" in s for s in stores["b"]["sql"]) and not any("scratch_a" in s for s in stores["b"]["sql"])
    finally:
        shutil.rmtree(d, ignore_errors=True)


@pytest.mark.slow
def test_the_fast_tier_fails_an_unmarked_six_second_test_and_passes_a_marked_one(tmp_path):
    d = toy_repo(with_sample=False)
    try:
        os.makedirs(os.path.join(d, "bin"))
        for tool in ("fast", "_session.py"):
            shutil.copy(os.path.join(REPO, "bin", tool), os.path.join(d, "bin", tool))
        shutil.copy(os.path.join(REPO, "conftest.py"), os.path.join(d, "conftest.py"))
        with open(os.path.join(d, "pytest.ini"), "w") as f:
            f.write("[pytest]\ntestpaths = tests\nmarkers =\n    slow: slow\naddopts = -p no:cacheprovider -q\n")
        with open(os.path.join(d, "tests", "test_sleepy.py"), "w") as f:
            f.write("import time\n\ndef test_sleepy():\n    time.sleep(6)\n    assert True\n")
        env = {**os.environ, "QV4_WORK": str(tmp_path), "QV4_NO_DB": "1", "CLAUDE_PROJECT_DIR": d}
        env.pop("QV4_FAST", None)
        p = subprocess.run([sys.executable, "bin/fast", "--no-fill"], cwd=d, capture_output=True, text=True, env=env)
        assert p.returncode == 1 and "not marked slow" in p.stdout and "fast tier: RED" in p.stdout
        with open(os.path.join(d, "tests", "test_sleepy.py"), "w") as f:
            f.write("import pytest, time\n\n@pytest.mark.slow\ndef test_sleepy():\n    time.sleep(6)\n\ndef test_quick():\n    assert True\n")
        p = subprocess.run([sys.executable, "bin/fast", "--no-fill"], cwd=d, capture_output=True, text=True, env=env)
        assert p.returncode == 0 and "fast tier: green" in p.stdout
        rows = [json.loads(l) for l in open(tmp_path / "times" / "fast-tier.jsonl")]
        assert [r["result"] for r in rows] == ["RED", "green"] and rows[0]["scope"] == "all"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_staging_takes_only_touched_modules_that_carry_a_load(tmp_path):
    repo = str(tmp_path / "repo")
    os.makedirs(os.path.join(repo, "registers", "gazette"))
    os.makedirs(os.path.join(repo, "keys"))

    def sh(*cmd):
        subprocess.run(cmd, cwd=repo, check=True, capture_output=True, env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                                                           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
    sh("git", "init", "-q", "-b", "main")
    open(os.path.join(repo, "keys", "x.py"), "w").write("x = 1\n")
    sh("git", "add", "-A")
    sh("git", "commit", "-q", "-m", "init")
    sh("git", "checkout", "-q", "-b", "session/gaz")
    with open(os.path.join(repo, "registers", "gazette", "load.py"), "w") as f:
        f.write("def load(conn, schema):\n    conn.execute(f'CREATE TABLE {schema}.notices (k text)')\n    return 3\n"
                "def publish(conn, staging):\n    conn.execute(f'ALTER TABLE {staging}.notices SET SCHEMA gazette')\n")
    open(os.path.join(repo, "keys", "x.py"), "a").write("y = 2\n")
    sh("git", "add", "-A")
    sh("git", "commit", "-q", "-m", "gaz")
    assert staging.touched_modules(repo, "session/gaz") == ["registers/gazette"]     # keys has no load.py
    store = {}
    out = staging.run(repo, "session/gaz", lambda: FakeConn(store), log=lambda *a: None)
    assert out == {"registers/gazette": 3}
    schema = staging.staging_schema("session/gaz", "registers/gazette")
    assert schema.startswith("staging_session_gaz") and f"CREATE TABLE {schema}.notices (k text)" in store["sql"]
    assert any("SET SCHEMA gazette" in s for s in store["sql"])


def test_the_full_tier_record_reaches_the_board(tmp_path):
    now = dt.datetime(2026, 10, 18, 7, 30, tzinfo=dt.timezone(dt.timedelta(hours=13)))
    p = str(tmp_path / "full-tier-last.json")
    r = full_tier.check(now=now, path=p)
    assert not r["ok"] and "never run" in r["items"][0]["detail"]
    json.dump({"at": (now - dt.timedelta(hours=3)).isoformat(), "seconds": 40.0, "ok": True, "summary": "620 passed in 40.0s"}, open(p, "w"))
    r = full_tier.check(now=now, path=p)
    assert r["ok"] and r["items"][1]["detail"] == "620 passed in 40.0s"
    json.dump({"at": (now - dt.timedelta(hours=30)).isoformat(), "seconds": 40.0, "ok": False, "summary": "1 failed"}, open(p, "w"))
    r = full_tier.check(now=now, path=p)
    assert not r["ok"] and all(not i["ok"] for i in r["items"])
