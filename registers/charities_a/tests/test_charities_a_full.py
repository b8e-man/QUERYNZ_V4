"""The slow tier: every page the capture lane lists, read into this
session's full scratch schema (`scratch_charities_a_full` in the sample
database; the real database is the gate's), reconciled page by page, and
the build's count measured against the register's own count on the capture
day. Idempotent: a listing already loaded is not reloaded, so a second run
is seconds. Needs the real database's listing (read-only) and the document
store: marked slow."""
import os
import time

import pytest

from support import db
from registers.charities_a import check, load

SCHEMA = "scratch_charities_a_full"
pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def built():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no database environment here (QV4_NO_DB, or no credential file)")
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn, db.connect(db.READ_KEY, "querynz_v4") as listing:
        conn.execute("SET statement_timeout = '900s'")
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        conn.commit()
        t0 = time.monotonic()
        n = load.load(conn, SCHEMA, shared=True, listing_conn=listing, log=lambda *a: None)
        seconds = round(time.monotonic() - t0, 1)
        f = check.figures(conn, SCHEMA, True, listing)
        yield {"loaded": n, "seconds": seconds, "figures": f}


def test_the_full_build_reconciles_every_page_and_meets_the_register_s_count(built):
    f = built["figures"]
    assert check.failed(f) == [], check.failed(f)
    assert f["tables"]["charities"] > 40000 and f["tables"]["charity_officers"] > 500000 and f["tables"]["charity_returns"] > 400000
    assert f["registered"] > 29000
    assert f["load_seconds"] < 600, f["load_seconds"]


def test_a_second_load_over_the_same_listing_reloads_nothing(built):
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn, db.connect(db.READ_KEY, "querynz_v4") as listing:
        lines = []
        n = load.load(conn, SCHEMA, shared=True, listing_conn=listing, log=lines.append)
    assert n == -1 and lines and "nothing reloaded" in lines[0]
