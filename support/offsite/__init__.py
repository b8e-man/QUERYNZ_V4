"""The off-site copy (track B): every table and file tree the delete rule
keeps, changes nightly with a weekly full checkpoint (ruling 21), sealed
and sent to the old estate's bucket under `qv4/`, and a restore rehearsal
that brings the newest copy back to equality. It replaced step 1.8's
nightly dump of `querynz_v4` once a copy restored from the bucket to
equality (19 October).

    pieces.py    what is copied, sorted by the delete rule
    copy.py      the nightly copy           python -m support.offsite copy [--full] [--local]
                                            python -m support.offsite plan
    restore.py   the rehearsal              python -m support.offsite restore [--source local]

This file holds what both use: the old estate's off-site credentials, read
from their file at the moment of use and never printed (hard limit 1), and
an upload that retries each object with a pause (old lesson: one transient
error once failed a 25 GB upload). Tests: support/offsite/tests/ (no
network, no database)."""
import os
import time

from support import db

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
ENV_FILE = os.environ.get("QV4_OFFSITE_ENV") or os.path.join(db.CRED_DIR, "offsite.env")
UPLOAD_ATTEMPTS = 5


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
