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


def known_donor(conn) -> tuple:
    """A donor row whose name is a company's, where that company has directors
    in the latest file: (donor ref, company key). Taken from the tables at run
    time, never fixed, so the test follows the data."""
    got = db.rows(conn, """
        select l.row_b as donor_ref, split_part(l.row_a, ':', 2) as company_key
        from pub.links l
        where l.rule = 'organisation-name@1' and l.row_a like 'companies:%%' and l.row_b like 'party_returns:%%'
          and exists (select 1 from pub.directors d where d.entity_key = split_part(l.row_a, ':', 2) and d.in_latest and not coalesce(d.suppressed, false))
        order by l.row_b limit 1""")
    assert got, "no donor row is name-linked to a company with directors"
    return got[0]["donor_ref"], got[0]["company_key"]


def test_the_walk_from_a_known_donor_reaches_the_company_and_its_directors_each_dated_or_undated():
    from products.report import walk
    allowed = {v.name for v in cat.VIEWS}
    with db.read_connect() as conn:
        donor_ref, company_key = known_donor(conn)
        w = walk.walk(conn, donor_ref, allowed)
    assert w["found"] and w["start"]["view"] == "party_return_donors"
    companies = [e for e in w["entities"] if e["view"] == "companies"]
    assert any(e["ref"] == f"companies:{company_key}" for e in companies)
    company = [e for e in companies if e["ref"] == f"companies:{company_key}"][0]
    assert company["grade"] == "near" and "name match" in company["reason"]
    directors = [r for r in w["roles"] if r.get("view") == "directors" and r["via"] == company["ref"]]
    assert directors, "the company's directors were not walked"
    for it in [w["start"]] + w["members"] + w["near"] + w["confirmed"] + w["roles"] + w["second"]:
        if "omitted" in it or it.get("missing"):
            continue
        assert it["dates"]["text"], it["ref"]
        assert it["dates"]["undated"] == ("undated" in it["dates"]["text"]), it["ref"]
        assert it["citation"]["view"] and it["citation"]["key"], it["ref"]
    returns = [e for e in w["entities"] if e["view"] == "party_return_totals"]
    assert returns and returns[0].get("context_only"), "the subject's return is context, not expanded into other donors"
    assert not any(r.get("view") == "party_return_donors" and r["via"] == returns[0]["ref"] for r in w["roles"])


def test_a_report_on_a_known_donor_names_its_returns_the_company_and_its_directors_each_cited():
    """The done-when of plan 5.1, on the real tables."""
    from products.report import build, template as tpl
    t = tpl.by_name("subject")
    with db.read_connect() as conn:
        donor_ref, company_key = known_donor(conn)
        r = build.build(conn, donor_ref, t)
    assert r["found"] and r["problems"] == [], r["problems"]
    money = [s for s in r["sections"] if s["name"] == "money"][0]
    assert any(it["view"] == "party_return_totals" for it in money["items"]), "the subject's own return is not named"
    companies = [s for s in r["sections"] if s["name"] == "companies"][0]
    company = [it for it in companies["items"] if it["ref"] == f"companies:{company_key}"]
    assert company and company[0]["grade"] == "near" and "name match" in company[0]["reason"]
    directors = [it for it in companies["items"] if it["view"] == "directors" and it["via"] == f"companies:{company_key}"]
    assert directors
    for it in [r["subject"]] + money["items"] + companies["items"]:
        assert it["cite"] and r["citations"][it["cite"] - 1]["key"] == it["citation"]["key"]
    for s in r["sections"]:
        if not s["items"]:
            assert s["blank"].startswith("none found in") or s["blank"].startswith("not held:")
    assert r["flags"] and all(f["status"] in ("fired", "clear", "blocked") for f in r["flags"])
