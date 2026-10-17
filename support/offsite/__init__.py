"""The new database's nightly off-site copy (plan step 1.8), until track B
replaces it.

The old nightly job copies only the three old databases, and changing it
would be a change to the frozen estate. So this small job of our own dumps
`querynz_v4` each night (its decisions and run records cannot be
regenerated), encrypts the dump the way the old job does (gpg, AES256,
symmetric; the passphrase travels on a pipe, never in argv or the
environment) and sends it to the same bucket under its own name,
`querynz_v4/<stamp>/querynz_v4.dump.gpg`, with a sha256 manifest line. A
local copy is kept on the second hard disk, the newest fourteen. The sample
database is skipped: it is refilled from its lists.

The bucket's address, the key id, the secret and the passphrase are read
from the old estate's off-site credential file at the moment of use and
never printed (hard limit 1). The upload retries each part with a pause
(old lesson: one transient error once failed a 25 GB upload).

    python -m support.offsite             dump, encrypt, upload, record
    python -m support.offsite --local     dump and encrypt only (no network)

Record: a run record (support.jobrun) and `<live>/checks/offsite-last.json`
with the stamp, the size, the sha256 and whether the upload went, which a
board check reads. Tests: support/offsite/tests/ (fakes; no network, no
database)."""
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time

from support import db, jobrun

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
RECORD = os.path.join(LIVE, "checks", "offsite-last.json")
LOCAL_DIR = os.environ.get("QV4_DUMP_DIR") or "/mnt/hdd2/qv4-dumps"
ENV_FILE = os.environ.get("QV4_OFFSITE_ENV") or os.path.join(db.CRED_DIR, "offsite.env")
DATABASE = "querynz_v4"
PREFIX = "querynz_v4"
KEEP_LOCAL = 14
UPLOAD_ATTEMPTS = 5
JOB = "qv4-offsite-dump"


def read_env(path: str = None) -> dict:
    """The off-site credentials as a dict. Never print it or any value."""
    env = {}
    with open(path or ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("\"'")
    return env


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dump(out_path: str, url: str, run=subprocess.run) -> None:
    """pg_dump -Fc, then pg_restore --list to prove the archive reads."""
    with open(out_path, "wb") as f:
        r = run(["pg_dump", "-Fc", "--no-owner", "--no-privileges", "-d", url], stdout=f, stderr=subprocess.PIPE)
    if r.returncode:
        raise RuntimeError(f"pg_dump failed: rc={r.returncode} {r.stderr.decode(errors='replace')[-300:]}")
    chk = run(["pg_restore", "--list", out_path], capture_output=True)
    if chk.returncode:
        raise RuntimeError("the dump does not read back")


def encrypt(src: str, dst: str, passphrase: str, run=subprocess.run) -> None:
    """gpg symmetric AES256; the passphrase goes down a pipe on fd 3."""
    r_fd, w_fd = os.pipe()
    try:
        os.write(w_fd, passphrase.encode("utf-8"))
        os.close(w_fd)
        r = run(["gpg", "--batch", "--yes", "--quiet", "--symmetric", "--cipher-algo", "AES256",
                 "--passphrase-fd", str(r_fd), "--output", dst, src], pass_fds=(r_fd,), capture_output=True)
    finally:
        os.close(r_fd)
    if r.returncode:
        raise RuntimeError(f"gpg failed: rc={r.returncode}")


def s3_client(env: dict):
    import boto3
    return boto3.client("s3", region_name=env.get("OFFSITE_REGION", "ap-southeast-2"),
                        aws_access_key_id=env["OFFSITE_KEY_ID"], aws_secret_access_key=env["OFFSITE_SECRET"])


def upload(client, bucket: str, key: str, path: str, attempts: int = UPLOAD_ATTEMPTS, sleep=time.sleep) -> None:
    last = None
    for i in range(attempts):
        try:
            client.upload_file(path, bucket, key)
            return
        except Exception as exc:  # noqa: BLE001 — retried, then raised
            last = exc
            sleep(min(60, 5 * (2 ** i)))
    raise RuntimeError(f"upload failed after {attempts} attempts: {type(last).__name__}")


def prune_local(folder: str, keep: int = KEEP_LOCAL) -> list:
    """Remove the oldest local dumps beyond `keep`; they are regenerated
    nightly and the off-site copy holds the rest."""
    names = sorted(n for n in os.listdir(folder) if n.endswith(".dump.gpg"))
    gone = names[:-keep] if len(names) > keep else []
    for n in gone:
        os.remove(os.path.join(folder, n))
    return gone


def run_job(local_only: bool = False, *, now: dt.datetime = None, env_path: str = None, local_dir: str = None,
            record_path: str = None, runs_path: str = None, run=subprocess.run, client_factory=s3_client,
            url_fn=db.url) -> dict:
    started = now or dt.datetime.now().astimezone()
    stamp = started.strftime("%Y%m%dT%H%M%S")
    local_dir = local_dir or LOCAL_DIR
    os.makedirs(local_dir, exist_ok=True)
    plain = os.path.join(local_dir, f"{DATABASE}-{stamp}.dump")
    sealed = plain + ".gpg"
    rec = {"stamp": stamp, "database": DATABASE, "sent": False, "why": ""}
    try:
        env = read_env(env_path)
        dump(plain, url_fn(db.OWNER_KEY, DATABASE), run=run)
        encrypt(plain, sealed, env["OFFSITE_PASSPHRASE"], run=run)
        os.remove(plain)
        rec["bytes"] = os.path.getsize(sealed)
        rec["sha256"] = sha256(sealed)
        rec["local"] = sealed
        if not local_only:
            key = f"{PREFIX}/{stamp}/{DATABASE}.dump.gpg"
            client = client_factory(env)
            upload(client, env["OFFSITE_BUCKET"], key, sealed)
            manifest = json.dumps({"stamp": stamp, "key": key, "bytes": rec["bytes"], "sha256": rec["sha256"]}) + "\n"
            client.put_object(Bucket=env["OFFSITE_BUCKET"], Key=f"{PREFIX}/{stamp}/manifest.jsonl", Body=manifest.encode())
            rec["sent"] = True
            rec["key"] = key
        rec["pruned"] = prune_local(local_dir)
        ok = True
    except Exception as exc:  # noqa: BLE001 — the record and the alarm carry it
        rec["why"] = f"{type(exc).__name__}: {exc}"
        ok = False
        if os.path.exists(plain):
            os.remove(plain)
    rec["at"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    rec["ok"] = ok
    record_path = record_path or RECORD
    os.makedirs(os.path.dirname(record_path), exist_ok=True)
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    jobrun.record(JOB, ok, rec["why"] or (f"{rec.get('bytes', 0):,} bytes" + (" sent" if rec["sent"] else " kept locally")),
                  started, {"bytes": rec.get("bytes"), "sent": rec["sent"]}, path=runs_path)
    return rec


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    rec = run_job(local_only="--local" in argv)
    print(f"offsite: {rec['stamp']} {'ok' if rec['ok'] else 'FAILED'} {rec.get('bytes', 0):,} bytes "
          f"{'sent' if rec['sent'] else 'not sent'} {rec['why']}")
    if not rec["ok"]:
        from support import alarm
        alarm.send(f"qv4 {os.uname().nodename}: off-site dump failed", rec["why"])
    return 0 if rec["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
