"""The filled sample (plan 1b.6): the pages named in sample.list read into the
session's scratch schema through this branch's code, then tested against the
row contract, the hard cases the list was chosen for, the catch log, the
published views and the page reconciliation. Only identifiers are asserted;
no name is quoted. Skipped where there is no sample database environment."""
import datetime as dt
import os

import pytest

from support import db, rowcontract, sample
from registers.charities_a import load, sample as S

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "charities_a")
TABLES = ("charities", "charity_officers", "charity_returns", "charity_groups", "codes", "files", "set_aside")


def _schema() -> str:
    """The session's own scratch schema (bin/fast fills it); a fixed one when there is no scope file."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_session", os.path.join(REPO, "bin", "_session.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        name = mod.read_scope(os.path.join(REPO, ".scope")).get("name")
    except Exception:  # noqa: BLE001 — no launcher here
        name = None
    return sample.scratch_name(name or "charities-a-test")


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    schema = _schema()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        have = conn.execute("SELECT to_regclass(%s) IS NOT NULL", (load.table(schema, "runs", True),)).fetchone()[0]
        if not have:                                   # not filled by bin/fast: this lane's own fill, alone
            S.fill(conn, schema, items)
        conn.commit()

        def q(sql, *args):
            cur = conn.execute(sql, args)
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        t = {n: q(f"SELECT * FROM {load.table(schema, n, True)} ORDER BY 1") for n in TABLES}
        yield {"schema": schema, "conn": conn, "items": items, **t}


def test_every_listed_charity_is_held_once_and_nothing_else(filled):
    keys = S.keys_of(filled["items"])
    assert {c["charity_number"] for c in filled["charities"]} == keys and len(filled["charities"]) == len(keys)
    assert all(c["key"] == f"charities/{c['charity_number']}" for c in filled["charities"])


def test_each_hard_case_reads_as_the_list_says(filled):
    by = {c["charity_number"]: c for c in filled["charities"]}
    offs = {}
    for o in filled["charity_officers"]:
        offs.setdefault(o["charity_number"], []).append(o)
    rets = {}
    for r in filled["charity_returns"]:
        rets.setdefault(r["charity_number"], []).append(r)
    # CC65228: one number on two organisation rows of page 47: one row kept, the other a catch-log line
    assert by["CC65228"]["organisation_id"] in (80395, 80397)
    assert [a for a in filled["set_aside"] if a["reason"].startswith("charity number held by two")][0]["item"].endswith("OrganisationId=80397")
    assert all(o["name_note"] is None or o["full_name"] for o in filled["charity_officers"])
    # page 40 holds four rows with no charity number
    assert sum(a["count"] for a in filled["set_aside"] if a["reason"] == "no charity number" and a["stage"] == "Organisations") == 4
    # CC59877: an officer the register marks Disqualified, with the ground it flags
    d = [o for o in offs["CC59877"] if o["disqualified"]]
    assert len(d) == 1 and d[0]["status"] == "Disqualified" and "OfficerDisqualifiedByRules" in d[0]["disqualification"] and d[0]["ended_on"]
    # CC60542: a past officer with the register's own end, a current one with none, and a Tier4 return
    assert any(o["status"] == "Past" and o["ended_on"] and o["ended_on_stated"] for o in offs["CC60542"])
    assert any(o["status"] == "Qualified" and o["ended_on"] is None for o in offs["CC60542"])
    assert [r["tier"] for r in rets["CC60542"]] == ["Tier4"] and rets["CC60542"][0]["period_ended_on"] == dt.date(2026, 3, 31)
    # CC36145: a return with a modified audit opinion, by the register's own words
    assert rets["CC36145"][0]["audit_opinion"] == "A disclaimer of opinion" and rets["CC36145"][0]["audit_opinion_modified"] is True
    assert rets["CC59945"][0]["tier"] == "Tier2" and rets["CC59945"][0]["currency"] == "NZD"
    # group returns: a group key and no charity
    g = [r for r in filled["charity_returns"] if r["charity_key"] is None]
    assert len(g) == 4 and all(r["group_key"].startswith("charities/group/") for r in g)
    assert {r["group_key"] for r in g} <= {x["key"] for x in filled["charity_groups"]}
    # CC59003 deregistered with the day and the coded reason; CC59008 in a group; CC59186 removed
    assert by["CC59003"]["status"] == "Deregistered" and by["CC59003"]["deregistered_on"] == dt.date(2024, 11, 26)
    assert by["CC59003"]["deregistration_reason"].startswith("Removed on request")
    assert by["CC59008"]["group_key"] == "charities/group/206" and by["CC59008"]["group_name"]
    assert by["CC59186"]["status"] == "Removed" and by["CC59186"]["deregistered_on"] == dt.date(2026, 5, 4)
    # every charity has its lists from the vOrganisations page, cited apart
    assert all(c["lists_document"] and c["activities"] for c in filled["charities"])
    assert all(c["main_sector"] for c in filled["charities"])


def test_no_end_date_is_a_load_day_and_every_end_is_the_register_s(filled):
    loaded = {o["loaded_at"].date() for o in filled["charity_officers"]}
    assert not [o for o in filled["charity_officers"] if o["ended_on"] in loaded]
    assert all(o["ended_on_stated"] == (o["ended_on"] is not None) for o in filled["charity_officers"])


def test_no_contact_detail_birth_date_or_home_address_is_a_column(filled):
    for t in ("charities", "charity_officers", "charity_returns", "charity_groups"):
        cols = set(filled[t][0]) if filled[t] else set()
        assert not cols & set(rowcontract.FORBIDDEN_COLUMNS), t
        assert not [c for c in cols if any(w in c for w in ("mail", "phone", "fax", "website", "birth", "telephone"))], t
    assert not [a for a in filled["set_aside"] if "1965" in a["item"] + a["reason"]]


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("charities", "charity_officers", "charity_returns", "charity_groups"):
        for r in filled[t]:
            row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
            row["loaded_at"] = r["loaded_at"].isoformat()
            row["filed"] = {k: (v.isoformat() if v else None) for k, v in r.items() if k.endswith("_on")}
            row["filed"]["ended_on_stated"] = r.get("ended_on_stated")
            assert rowcontract.validate(row, today) == [], (t, r["key"])


def test_every_page_reconciles_rows_to_typed_set_aside_or_filtered(filled):
    assert filled["files"]
    for f in filled["files"]:
        assert f["typed"] + f["set_aside"] + f["filtered"] == f["rows"], (f["entity_set"], f["document"][:12])
    assert sum(a["count"] for a in filled["set_aside"]) == sum(f["set_aside"] for f in filled["files"]) + \
        sum(a["count"] for a in filled["set_aside"] if a["reason"].startswith("charity number held by two"))


def test_the_published_views_build_and_carry_no_private_column(filled):
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(load.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.charities_a_pub_"))
    views = ("charities", "charity_officers", "charity_returns", "charity_groups")
    counts = {v: conn.execute(f"SELECT count(*) FROM {schema}.charities_a_pub_{v}").fetchone()[0] for v in views}
    cols = {v: [d[0] for d in conn.execute(f"SELECT * FROM {schema}.charities_a_pub_{v} LIMIT 0").description] for v in views}
    conn.rollback()
    assert counts == {v: len(filled[v]) for v in views}
    for v, cs in cols.items():
        assert not set(cs) & set(rowcontract.FORBIDDEN_COLUMNS) and "contact_id" not in cs and "nzbn_filed" not in cs, v
        assert {"document", "place", "profile_version", "loaded_at"} <= set(cs), v
    assert "address_for_service" in cols["charities"] and "disqualification" in cols["charity_officers"]
    assert "figures" in cols["charity_returns"] and "total_gross_income" in cols["charity_returns"]
