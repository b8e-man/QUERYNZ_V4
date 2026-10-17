"""The database shape: every lane has a private twin, the session reader is
granted everything but the private schemas and the seal, the product reader
pub only; a connection string is read from its file and never printed.
The apply itself runs against the sample database, marked slow."""
import os

import pytest

import support.db as db


def test_schemas_pair_every_lane_with_a_private_twin():
    s = db.schemas()
    for lane in db.LANES:
        assert lane in s and lane + "_private" in s
    for p in db.PRODUCTS:
        assert p in s
    assert {"pub", "links", "links_private", "docs", "sealed"} <= set(s)
    assert len(s) == len(set(s))


def test_private_is_the_suffix_and_the_seal():
    assert db.is_private("companies_private") and db.is_private("sealed") and db.is_private("links_private")
    assert not db.is_private("companies") and not db.is_private("pub")


def test_plan_grants_read_everything_but_private_and_product_pub_only():
    sql = db.plan_sql()
    assert "CREATE SCHEMA IF NOT EXISTS pub AUTHORIZATION qv4_owner;" in sql
    assert "GRANT USAGE ON SCHEMA companies TO qv4_read;" in sql
    assert "ALTER DEFAULT PRIVILEGES FOR ROLE qv4_owner IN SCHEMA companies GRANT SELECT ON TABLES TO qv4_read;" in sql
    assert "REVOKE ALL ON SCHEMA companies_private FROM qv4_read, qv4_product;" in sql
    assert "GRANT USAGE ON SCHEMA companies_private TO qv4_read" not in sql
    assert "REVOKE ALL ON SCHEMA sealed FROM qv4_read, qv4_product;" in sql
    assert "GRANT USAGE ON SCHEMA pub TO qv4_product;" in sql
    assert "GRANT USAGE ON SCHEMA companies TO qv4_product" not in sql
    assert "REVOKE ALL ON SCHEMA companies FROM qv4_product;" in sql
    assert "DROP" not in sql.upper().replace("DROP", "DROP") or "DROP SCHEMA" not in sql.upper()


def test_a_bad_schema_name_is_refused():
    with pytest.raises(ValueError):
        db.plan_sql(extra_schemas=("bad name;",))
    with pytest.raises(ValueError):
        db.scratch_sql("x" * 80)
    assert db.scratch_sql("founding-1") == "CREATE SCHEMA IF NOT EXISTS scratch_founding_1 AUTHORIZATION qv4_owner;\n"


def test_url_reads_one_key_and_can_swap_the_database(tmp_path, monkeypatch):
    (tmp_path / "v4.env").write_text("# creds\nQV4_OWNER_URL=postgresql://u:p@10.0.0.10:5432/querynz_v4\nQV4_OLD_READ_URL=x\n")
    monkeypatch.setattr(db, "CRED_DIR", str(tmp_path))
    assert db.url(db.OWNER_KEY) == "postgresql://u:p@10.0.0.10:5432/querynz_v4"
    assert db.url(db.OWNER_KEY, "querynz_v4_sample") == "postgresql://u:p@10.0.0.10:5432/querynz_v4_sample"
    with pytest.raises(RuntimeError):
        db.url(db.READ_KEY)           # that file is absent here
    (tmp_path / "v4-read.env").write_text("OTHER=1\n")
    with pytest.raises(RuntimeError):
        db.url(db.READ_KEY)           # the key is absent


@pytest.mark.slow
def test_apply_to_the_sample_database_and_check_it():
    """Needs the owner login and the server: the fast tier skips it unless
    the credential file is there."""
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    db.apply("querynz_v4_sample", log=lambda *a: None)
    assert db.check("querynz_v4_sample") == []
    with db.connect(db.READ_KEY, "querynz_v4_sample") as conn:
        seen = {r[0] for r in conn.execute(
            "select nspname from pg_namespace where has_schema_privilege(current_user, nspname, 'USAGE')")}
    assert "pub" in seen and "companies" in seen
    assert "companies_private" not in seen and "sealed" not in seen
    with db.connect(db.PRODUCT_KEY, "querynz_v4_sample") as conn:
        seen = {r[0] for r in conn.execute(
            "select nspname from pg_namespace where has_schema_privilege(current_user, nspname, 'USAGE')")}
    assert "pub" in seen and "companies" not in seen and "links" not in seen
