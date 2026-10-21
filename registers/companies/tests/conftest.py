"""The lane's filled sample, once for every test module of the lane."""
import os

import pytest

from support import db, sample

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_companies"


@pytest.fixture(scope="session")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    schema = _schema()
    sample.fill_schema(schema, lambda: db.connect(db.OWNER_KEY, "querynz_v4_sample"), REPO, log=lambda *a: None)
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        def q(sql):
            cur = conn.execute(sql)
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        t = {n: q(f"SELECT * FROM {schema}.companies_{n} ORDER BY key") for n in
             ("entities", "entity_states", "directors", "shareholders", "registered_offices")}
        yield {"schema": schema, "conn": conn, **t,
               "aside": q(f"SELECT * FROM {schema}.companies_set_aside"),
               "private": q(f"SELECT key FROM {schema}_private.companies_residential_addresses")}


