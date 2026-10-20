"""Against the real published tables through the session reader (slow)."""
import pytest

from products.report import catalogue as cat
from products.report import db, rows

pytestmark = pytest.mark.slow


def test_a_donor_ref_and_a_director_ref_locate_and_cite():
    with db.read_connect() as conn:
        d = db.rows(conn, "select key from pub.party_return_donors where donor is not null order by amount desc nulls last, key limit 1")[0]["key"]
        v, r = rows.locate(conn, f"party_returns:{d}")
        assert v.name == "party_return_donors" and r["key"] == d
        c = rows.citation(v, r)
        assert c["document"] and len(c["document"]) == 64
        ev, e = rows.entity_of(conn, v, r)
        assert ev.name == "party_return_totals" and e
        k = db.rows(conn, "select key from pub.directors where coalesce(suppressed, false) order by key limit 1")
        if k:
            v2, r2 = rows.locate(conn, f"companies:{k[0]['key']}")
            assert v2.name == "directors" and rows.title(v2, r2) == rows.SUPPRESSED
        c2 = db.rows(conn, "select key from pub.companies order by key limit 1")[0]["key"]
        v3, r3 = rows.locate(conn, f"companies:{c2}")
        assert v3.name == "companies"


def test_every_column_the_catalogue_reads_exists_in_its_view():
    with db.read_connect() as conn:
        held = db.pub_views(conn)
        for v in cat.VIEWS:
            assert v.name in held, v.name
            cols = {x["column_name"] for x in db.rows(conn, "select column_name from information_schema.columns where table_schema='pub' and table_name=%s", (v.name,))}
            missing = cat.columns_read(v) - cols
            assert not missing, f"{v.name}: {sorted(missing)}"
