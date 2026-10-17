"""The off-site job dumps, encrypts, uploads with retries, records, prunes,
and never lets a secret into a record or a log; all with fakes."""
import json
import os
import subprocess

import pytest

import support.offsite as off


class FakeRun:
    """Stands in for subprocess.run: pg_dump writes bytes to stdout, gpg
    writes the output file, pg_restore --list succeeds."""

    def __init__(self):
        self.calls = []

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        if cmd[0] == "pg_dump":
            kw["stdout"].write(b"PGDMP fake dump bytes")
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        if cmd[0] == "pg_restore":
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        if cmd[0] == "gpg":
            out = cmd[cmd.index("--output") + 1]
            with open(out, "wb") as f:
                f.write(b"encrypted " + open(cmd[-1], "rb").read())
            assert "--passphrase-fd" in cmd and "secret-pass" not in " ".join(cmd)
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        raise AssertionError(cmd)


class FakeClient:
    def __init__(self, fail_first=0):
        self.uploads, self.objects, self.fail_first = [], [], fail_first

    def upload_file(self, path, bucket, key):
        if self.fail_first:
            self.fail_first -= 1
            raise ConnectionError("blip")
        self.uploads.append((bucket, key, os.path.getsize(path)))

    def put_object(self, Bucket, Key, Body):
        self.objects.append((Bucket, Key, Body))


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / "offsite.env"
    p.write_text("OFFSITE_BUCKET=bkt\nOFFSITE_KEY_ID=AKIA\nOFFSITE_SECRET=sekret\nOFFSITE_PASSPHRASE=secret-pass\n")
    return str(p)


def run(tmp_path, env_file, **kw):
    kw.setdefault("run", FakeRun())
    kw.setdefault("url_fn", lambda key, database=None: "postgresql://u:p@h/" + (database or "x"))
    return off.run_job(env_path=env_file, local_dir=str(tmp_path / "dumps"), record_path=str(tmp_path / "last.json"),
                       runs_path=str(tmp_path / "runs.jsonl"), **kw)


def test_dump_encrypt_upload_and_record(tmp_path, env_file, monkeypatch):
    monkeypatch.setattr(off.time, "sleep", lambda s: None)
    client = FakeClient()
    rec = run(tmp_path, env_file, client_factory=lambda env: client)
    assert rec["ok"] and rec["sent"]
    assert client.uploads[0][0] == "bkt" and client.uploads[0][1] == f"querynz_v4/{rec['stamp']}/querynz_v4.dump.gpg"
    assert client.objects[0][1].endswith("manifest.jsonl")
    assert os.path.exists(rec["local"]) and rec["local"].endswith(".dump.gpg")
    assert not os.path.exists(rec["local"][:-4])          # the plain dump is gone
    text = open(tmp_path / "last.json").read() + open(tmp_path / "runs.jsonl").read()
    for secret in ("sekret", "secret-pass", "AKIA"):
        assert secret not in text


def test_upload_retries_then_succeeds(tmp_path, env_file):
    sleeps = []
    client = FakeClient(fail_first=2)
    off.upload(client, "bkt", "k", env_file, attempts=5, sleep=sleeps.append)
    assert len(client.uploads) == 1 and sleeps == [5, 10]
    with pytest.raises(RuntimeError):
        off.upload(FakeClient(fail_first=9), "bkt", "k", env_file, attempts=3, sleep=lambda s: None)


def test_local_only_keeps_the_copy_and_sends_nothing(tmp_path, env_file):
    rec = run(tmp_path, env_file, local_only=True, client_factory=lambda env: (_ for _ in ()).throw(AssertionError("no client")))
    assert rec["ok"] and not rec["sent"] and os.path.exists(rec["local"])


def test_a_failed_dump_is_recorded_not_raised(tmp_path, env_file):
    def bad_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 1, b"", b"boom")
    rec = run(tmp_path, env_file, run=bad_run)
    assert not rec["ok"] and "pg_dump failed" in rec["why"]
    last = json.loads(open(tmp_path / "runs.jsonl").read().splitlines()[-1])
    assert last["job"] == "qv4-offsite-dump" and not last["ok"]


def test_prune_keeps_the_newest(tmp_path):
    d = tmp_path / "dumps"
    d.mkdir()
    for i in range(5):
        (d / f"querynz_v4-2026101{i}T030000.dump.gpg").write_bytes(b"x")
    gone = off.prune_local(str(d), keep=3)
    assert gone == ["querynz_v4-20261010T030000.dump.gpg", "querynz_v4-20261011T030000.dump.gpg"]
    assert len(os.listdir(d)) == 3


def test_job_files_carry_prefix_and_deadline():
    jobs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jobs")
    names = sorted(os.listdir(jobs))
    assert names == ["qv4-offsite-dump.service", "qv4-offsite-dump.timer"]
    svc = open(os.path.join(jobs, names[0])).read()
    assert "TimeoutStartSec=" in svc and "-m support.offsite" in svc
    assert "Persistent=true" in open(os.path.join(jobs, names[1])).read()
