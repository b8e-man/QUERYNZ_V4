"""One fill of the sample schema for every test file of the lane (the fill is the slow part of the fast tier:
about 45 s for the 38 modules; two module fixtures filled it twice)."""
import os

import pytest

from support import db


def schema_name() -> str:
    from support import sample
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), repo):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_hansard"


@pytest.fixture(scope="session")
def sample_schema() -> str:
    """The session's scratch schema in the sample database, filled once through this branch's code."""
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    from support import sample
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    schema = schema_name()
    sample.fill_schema(schema, lambda: db.connect(db.OWNER_KEY, "querynz_v4_sample"), repo, log=lambda *a: None)
    return schema
