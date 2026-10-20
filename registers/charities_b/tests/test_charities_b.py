"""The charities_b build's tests (step 4.1). The reading's rules are tested on
rows shaped like the feed's (every name invented); the filled sample (real
pages, sample.list) against the row contract, the catch log, the ledger and
the published views; and, marked slow, a full build from every captured
page against the capture's own counts, the register's count and its own
view, built twice to show the keys and rows do not move. No model is
called and nothing is fetched."""
import datetime as dt
import json
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.charities_b import capture, check, load, read
from registers.charities_b import sample as S

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "charities_b")
SHA, SHA2 = "a" * 64, "b" * 64
#: a name of a column that would carry an officer's or a charity's contact details, or a birth date
CONTACT = ("email", "phone", "fax", "telephone", "birth", "dob", "website", "facebook", "twitter", "contact", "postal",
           "street", "residential", "home")


def _meta(s, i):
    return {"__metadata": {"type": f"Charities_ODATAModel.{s}", "uri": f"http://x/{s}({i})"}}


def _codes():
    c = read.Codes()
    c.add_page("RegistrationStatus", [{"Id": 1, "Name": "Registered", "EntityName": "Organisations"},
                                      {"Id": 2, "Name": "Deregistered", "EntityName": "Organisations"}])
    c.add_page("LegalStructure", [{"LegalStructureId": 1, "Name": "Incorporated Society"}])
    c.add_page("MainSector", [{"Id": 2, "Name": "Education / training / research", "EntityName": "Organisations"},
                              {"Id": 7, "Name": "Emergency / disaster relief", "EntityName": "Organisations"}])
    c.add_page("MainActivity", [{"Id": 6, "Name": "Provides services (e.g. care / counselling)", "EntityName": "Organisations"}])
    c.add_page("MainBeneficiary", [{"Id": 10, "Name": "General public", "EntityName": "Organisations"}])
    c.add_page("OfficerStatus", [{"Id": i, "Name": n, "EntityName": "Officers"} for i, n in
                                 enumerate(("Proposed", "Qualified", "Past", "Disqualified"), 1)])
    c.add_page("ReportingTier", [{"ReportingTierId": 4, "Name": "Tier4"}])
    c.add_page("ReportingCurrency", [{"ReportingCurrencyId": 1, "Name": "NZD"}])
    c.add_page("AuditModifiedOpinionReceived", [{"AuditModifiedOpinionReceivedId": 1, "Name": "A qualified opinion"}])
    return c


def _org(oid=101, number="CC10001", **kw):
    r = {**_meta("Organisations", oid), "OrganisationId": oid, "CharityRegistrationNumber": number,
         "Name": "The Example Trust", "RegistrationStatus": "Registered", "DateRegistered": "2008-03-05T00:00:00Z",
         "DeregistrationDate": None, "LegalStructure": "Incorporated Society", "MainSectorId": 7, "MainActivityId": 9,
         "MainBeneficiaryId": 4, "StreetAddressLine1": "1 Example Street", "StreetAddressLine2": None,
         "StreetAddressSuburb": "Exampleton", "StreetAddressCity": "Wellington", "StreetAddressPostcode": "6011",
         "PostalAddressLine1": "PO Box 1", "EMailAddress1": "someone@example.org", "Telephone1": "04 000 0000",
         "GroupId": None, "GroupType": 4, "NZBNNumber": "9429000000017", "ModifiedOn": "2026-10-08T22:33:20Z"}
    r.update(kw)
    return r


def _officer(fid=5001, oid=101, **kw):
    r = {**_meta("Officers", fid), "OfficerId": fid, "OrganisationId": oid, "FirstName": "Ann", "MiddleName": None,
         "LastName": "Example", "FullName": "Ann Example", "IsaBodyCorporate": False, "BodyCorporateName": None,
         "PositioninOrganisation": " Trustee ", "PositionAppointmentDate": "2010-01-31T00:00:00Z",
         "LastDateAsAnOfficer": None, "OfficerStatus": "Qualified", "IsNotDisqualified": True,
         "ContactId": "00000000-0000-0000-0000-000000000000", "DoNotSendMM": False, "ModifiedOn": "2025-01-01T00:00:00Z"}
    r.update(kw)
    return r


def _return(aid=9001, oid=101, gid=None, **kw):
    r = {**_meta("AnnualReturn", aid), "AnnualReturnId": aid, "OrganisationId": oid, "GroupId": gid,
         "YearEnded": "2025-03-31T00:00:00Z", "AsAtDate": "2025-03-31T00:00:00Z", "ReportingTierId": 4, "Status": 10,
         "TotalGrossIncome": 120000, "TotalExpenditure": 100000.0, "NetSurplusDeficitForTheYear": 20000,
         "TotalAssets": 50000, "TotalLiabilities": 1000, "DonationsKoha": 30000, "NumberOfFulltimeEmployees": 3,
         "AvgNoVolunteersPerWeek": 12, "IsFinancialReportAudited": True, "IsModifiedAuditOpinionReceived": False,
         "Total_Gross_Income_LastYear": "110000.50", "MaterialExpense1": 4000, "MaterialExpense1Label": "Rent",
         "AuditName": "An Auditor", "CertifyingOfficerName": "Ann Example", "ReportingCurrency": None,
         "ModifiedOn": "2025-06-01T00:00:00Z"}
    r.update(kw)
    return r


def test_the_lane_folder_has_the_shape():
    assert lane.check_folder(LANE) == []


def test_a_feed_day_is_the_day_written_and_a_moment_is_its_day_in_new_zealand():
    assert read.feed_date("2026-09-02T00:00:00Z") == "2026-09-02"
    assert read.feed_date("2019-06-30T12:00:00Z") == "2019-07-01"       # NZ midnight, written in UTC
    assert read.feed_date("/Date(1561896000000)/") == "2019-07-01"
    assert read.feed_date(None) is None and read.feed_date("") is None


def test_a_register_number_is_kept_whole_suffix_and_all():
    assert read.charity_number(" cc 12345 ") == "CC12345"
    assert read.charity_number("CC12345-1") == "CC12345-1"
    from keys.numbers import charity_number
    assert charity_number("CC12345-1") == "CC12345"       # why the shared reading is not used for the key
    assert read.charity_number("12345") is None and read.charity_number(None) is None


def test_a_charity_is_keyed_by_its_number_and_its_codes_resolve_as_the_register_s_view_names_them():
    notes = __import__("collections").Counter()
    r, why = read.read_organisation(_org(), SHA, _codes(), {}, notes)
    assert why is None and r["key"] == "charities/CC10001" and r["registered_on"] == "2008-03-05"
    assert r["main_sector"] == "Education / training / research"            # id 7 on an organisation row
    assert r["main_activity"] == "Provides services (e.g. care / counselling)" and r["main_beneficiary"] == "General public"
    assert r["address_for_service"] == "1 Example Street, Exampleton, Wellington, 6011"
    assert r["place"] == "OrganisationId=101" and r["document"] == SHA and r["page"] == 1
    assert not [k for k in r if any(w in k for w in CONTACT)]


def test_a_code_whose_name_the_code_list_does_not_hold_resolves_to_nothing_and_is_counted():
    notes = __import__("collections").Counter()
    r, _ = read.read_organisation(_org(MainSectorId=1), SHA, _codes(), {}, notes)   # "Accommodation / housing": not listed here
    assert r["main_sector_id"] == 1 and r["main_sector"] is None
    assert notes["organisation MainSectorId not in its code list"] == 1


def test_an_email_in_an_address_part_is_dropped_and_a_bad_nzbn_left_empty():
    notes = __import__("collections").Counter()
    r, _ = read.read_organisation(_org(StreetAddressLine2="someone@example.org", NZBNNumber="9429000000018"), SHA,
                                  _codes(), {}, notes)
    assert "@" not in r["address_for_service"] and r["nzbn"] is None
    assert notes["address part holding an email address dropped"] == 1 and notes["NZBN failing its check digit, left empty"] == 1


def test_an_organisation_with_no_number_is_set_aside():
    r, why = read.read_organisation(_org(number=None), SHA, _codes(), {}, __import__("collections").Counter())
    assert r is None and why == "no registration number" and read.stage_of(why) == "key"


def test_an_officer_carries_role_window_status_and_no_contact_detail():
    charities = {101: ("charities/CC10001", None)}
    r, _ = read.read_officer(_officer(LastDateAsAnOfficer="2015-04-01T00:00:00Z", OfficerStatus="Past"), SHA, _codes(),
                             charities, __import__("collections").Counter())
    assert r["key"] == "charities/officers/5001" and r["charity_key"] == "charities/CC10001"
    assert (r["role"], r["started_on"], r["ended_on"], r["ended_on_stated"]) == ("Trustee", "2010-01-31", "2015-04-01", True)
    assert not [k for k in r if any(w in k for w in CONTACT)] and "ContactId" not in json.dumps(r, default=str)


def test_disqualified_is_the_register_s_status_never_the_declaration():
    ch, c = {101: ("charities/CC10001", None)}, _codes()
    n = __import__("collections").Counter()
    a, _ = read.read_officer(_officer(OfficerStatus="Disqualified", IsNotDisqualified=True), SHA, c, ch, n)
    b, _ = read.read_officer(_officer(OfficerStatus="Past", IsNotDisqualified=False), SHA, c, ch, n)
    assert a["disqualified"] and not b["disqualified"] and b["declared_not_disqualified"] is False


def test_a_body_corporate_officer_is_named_by_the_body_and_a_nameless_row_is_set_aside():
    ch, c, n = {101: ("charities/CC10001", None)}, _codes(), __import__("collections").Counter()
    r, _ = read.read_officer(_officer(IsaBodyCorporate=True, BodyCorporateName="Example Trustee Limited", FullName=None,
                                      FirstName=None, LastName=None), SHA, c, ch, n)
    assert r["kind"] == "body corporate" and r["full_name"] == "Example Trustee Limited" and r["last_name"] is None
    r, why = read.read_officer(_officer(FullName=None, FirstName=None, LastName=None), SHA, c, ch, n)
    assert r is None and why == "no name"


def test_an_officer_of_a_set_aside_organisation_is_set_aside_with_it():
    r, why = read.read_officer(_officer(), SHA, _codes(), {101: (None, "no registration number")},
                               __import__("collections").Counter())
    assert r is None and why == "its organisation is set aside (no registration number)" and read.stage_of(why) == "link"
    r, why = read.read_officer(_officer(oid=999), SHA, _codes(), {}, __import__("collections").Counter())
    assert why == "its organisation is not in the held pages"


def test_a_return_keeps_every_financial_field_and_nothing_else():
    ch = {101: ("charities/CC10001", None)}
    r, _ = read.read_return(_return(), SHA, _codes(), ch, {}, __import__("collections").Counter())
    assert r["key"] == "charities/returns/9001" and r["period_end"] == "2025-03-31" and r["tier"] == "Tier4"
    assert r["total_gross_income"] == 120000 and r["total_expenditure"] == 100000 and r["net_surplus"] == 20000
    f = r["figures"]
    assert f["DonationsKoha"] == 30000 and str(f["Total_Gross_Income_LastYear"]) == "110000.50"
    assert not set(f) & {"NumberOfFulltimeEmployees", "AvgNoVolunteersPerWeek", "Status", "ReportingTierId",
                         "OrganisationId", "IsFinancialReportAudited", "MaterialExpense1"}
    assert r["material_expenses"] == [{"label": "Rent", "amount": 4000}]
    assert "An Auditor" not in json.dumps(r, default=str) and "Ann Example" not in json.dumps(r, default=str)


def test_a_return_filed_by_a_group_alone_cites_the_group_and_one_naming_neither_is_set_aside():
    groups = {7: {"key": "charities/CC50001", "number": "CC50001", "name": "An Example Group"}}
    n = __import__("collections").Counter()
    r, _ = read.read_return(_return(oid=None, gid=7), SHA, _codes(), {}, groups, n)
    assert r["charity_key"] is None and r["group_key"] == "charities/CC50001"
    r, why = read.read_return(_return(oid=None, gid=None), SHA, _codes(), {}, groups, n)
    assert r is None and why == "names no organisation and no group"
    r, _ = read.read_return(_return(ReportingTierId=-1), SHA, _codes(), {101: ("charities/CC10001", None)}, groups, n)
    assert r["tier_id"] == -1 and r["tier"] is None and n["return tier not in its code list"] == 1


def test_a_row_read_again_on_a_later_page_keeps_the_later_reading_whatever_the_landing_order():
    pages = {SHA: json.dumps({"d": {"results": [_org(name := 101, Name="Old Name"), _org(102, "CC10002")]}}).encode(),
             SHA2: json.dumps({"d": {"results": [_org(101, Name="New Name")]}}).encode()}
    got = list(read.newest_first([SHA, SHA2], "Organisations", pages.__getitem__))
    kept = [(sha, r["Name"]) for sha, r, line in got if r is not None]
    lines = [line for _, r, line in got if line is not None]
    assert kept == [(SHA2, "New Name"), (SHA, "The Example Trust")]
    assert len(lines) == 1 and lines[0]["stage"] == "supersede" and lines[0]["document"] == SHA


def test_a_page_of_another_set_is_refused():
    pages = {SHA: json.dumps({"d": [_officer()]}).encode()}
    with pytest.raises(ValueError, match="Officers row in the Organisations pages"):
        list(read.newest_first([SHA], "Organisations", pages.__getitem__))


def test_the_published_views_name_no_contact_column():
    text = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read().lower()
    selects = " ".join(part.split("from")[0] for part in text.split("select")[1:])
    assert not [w for w in CONTACT if w in selects]
    assert "declared_not_disqualified" not in selects and "organisation_id" not in selects


def test_this_build_publishes_nothing_until_it_is_kept():
    said = []
    assert load.KEPT is False
    load.publish(None, "staging_x", log=said.append)       # never touches the connection
    assert said and "nothing published" in said[0]


# ── the filled sample ───────────────────────────────────────────────────────────

SAMPLE_SCHEMA = "scratch_charities_b"


def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def _rows(conn, sql):
    cur = conn.execute(sql)
    return [dict(zip([d[0] for d in cur.description], r)) for r in cur]


def _digest(conn, schema, shared):
    """Every table's rows, loaded_at aside, as one hash per table."""
    out = {}
    for t in load.TABLES:
        name = load.table(schema, t, shared)
        order = "key" if "key" in load.COLUMNS[t] else ", ".join(load.COLUMNS[t])
        out[t] = conn.execute(f"SELECT count(*), md5(coalesce(string_agg(md5((to_jsonb(x) - 'loaded_at')::text), '' "
                              f"ORDER BY {order}), '')) FROM {name} x").fetchone()
    return out


@pytest.fixture(scope="module")
def filled():
    _db_or_skip()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SAMPLE_SCHEMA}")
        S.fill(conn, SAMPLE_SCHEMA, items)
        conn.commit()
        T = lambda t: load.table(SAMPLE_SCHEMA, t, True)
        yield {"conn": conn, "items": items, **{t: _rows(conn, f"SELECT * FROM {T(t)}") for t in load.TABLES}}


def test_every_listed_organisation_is_a_charity_or_set_aside_and_nothing_else(filled):
    want = S.keys_of(filled["items"])["Organisations"]
    typed = {c["organisation_id"] for c in filled["charities"]}
    aside = {int(a["place"].split("=")[1]) for a in filled["set_aside"] if a["entity_set"] == "Organisations"}
    assert typed | aside == want and not typed & aside


def test_each_case_reads_as_its_comment_says(filled):
    by = {c["organisation_id"]: c for c in filled["charities"]}
    assert by[51802]["number"].endswith("-1") and by[51802]["key"] == "charities/" + by[51802]["number"]
    assert by[33055]["group_key"] and by[33055]["status"] == "Registered"
    assert by[32584]["status"] == "Deregistered" and by[32584]["deregistered_on"]
    assert by[32680]["status"] == "Removed"
    assert by[44934]["address_for_service"] and "@" not in by[44934]["address_for_service"]
    assert by[34292]["nzbn"] is None
    reasons = {(a["place"], a["reason"]) for a in filled["set_aside"]}
    assert ("OrganisationId=80395", "the register's number is held by 2 organisations") in reasons
    assert ("OrganisationId=69084", "no registration number") in reasons
    assert ("OfficerId=1324059", "no name") in reasons
    assert ("AnnualReturnId=167205", "names no organisation and no group") in reasons
    assert any(p == "OfficerId=1756874" and r.startswith("its organisation is set aside") for p, r in reasons)
    assert any(p == "AnnualReturnId=167198" and r.startswith("its organisation is set aside") for p, r in reasons)
    off = {o["officer_id"]: o for o in filled["officers"]}
    assert off[1167671]["disqualified"] and not off[1168154]["disqualified"]
    assert off[1176315]["ended_on"] and off[1224386]["ended_on"] is None and off[1322312]["kind"] == "body corporate"
    ret = {r["return_id"]: r for r in filled["returns"]}
    assert ret[175439]["tier"] is None and ret[175439]["tier_id"] == -1
    assert ret[395815]["currency"] == "AUD" and ret[375930]["opinion"] == "A qualified opinion"
    assert ret[434560]["charity_key"] is None and ret[434560]["group_key"]
    assert ret[238632]["charity_key"] == by[33055]["key"]


def test_the_codes_resolve_as_the_register_s_own_view_names_them(filled):
    from support.docstore.landing import read_bytes
    view = S.pages_of(filled["items"])["vOrganisations"]
    got = check.resolution(filled["conn"], SAMPLE_SCHEMA, view, read_bytes, shared=True)
    assert got.get("compared", 0) + got.get("moved between the two captures", 0) == 3 and got.get("compared")
    assert not {k: v for k, v in got.items() if k.endswith("differs")}
    assert all(c["main_sector"] for c in filled["charities"] if c["organisation_id"] in (33055, 32584, 32680)
               and c["main_sector_id"] is not None)


def test_the_sample_reconciles_page_by_page(filled):
    assert all(p["typed"] + p["set_aside"] + p["skipped"] == p["rows"] for p in filled["pages"])
    listed = S.pages_of(filled["items"])
    assert {p["document"] for p in filled["pages"]} == {sha for s, v in listed.items() for sha in v if s != "vOrganisations"}


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("charities", "officers", "returns", "groups"):
        assert filled[t], t
        for r in filled[t]:
            row = {k: r[k] for k in rowcontract.REQUIRED if k != "loaded_at"}
            row["loaded_at"] = r["loaded_at"].isoformat()
            row["filed"] = {k: (v.isoformat() if v else None) for k, v in r.items() if k.endswith("_on")}
            if t == "officers":
                row["filed"]["ended_on_stated"] = r["ended_on_stated"]
            assert rowcontract.validate(row, today) == [], (t, r["key"])


def test_no_table_holds_a_contact_detail_or_a_birth_date(filled):
    for t in load.TABLES:
        assert not [c for c in load.COLUMNS[t] if any(w in c for w in CONTACT)], t
        if filled[t]:
            assert not [c for c in filled[t][0] if any(w in c for w in CONTACT)], t


def test_the_published_views_build_on_the_sample_and_match_the_tables(filled):
    conn = filled["conn"]
    conn.execute(load.sql("publish.sql", SAMPLE_SCHEMA, shared=True).replace("pub.", f"{SAMPLE_SCHEMA}.charities_b_pub_"))
    n = {v: conn.execute(f"SELECT count(*) FROM {SAMPLE_SCHEMA}.charities_b_pub_{v}").fetchone()[0]
         for v in ("charities", "charity_officers", "charity_returns")}
    cols = [d[0] for v in ("charities", "charity_officers", "charity_returns")
            for d in conn.execute(f"SELECT * FROM {SAMPLE_SCHEMA}.charities_b_pub_{v} LIMIT 0").description]
    conn.rollback()
    assert n == {"charities": len(filled["charities"]), "charity_officers": len(filled["officers"]),
                 "charity_returns": len(filled["returns"])}
    assert not set(cols) & set(rowcontract.FORBIDDEN_COLUMNS) and "document" in cols and "place" in cols


def test_a_second_fill_gives_the_same_rows_under_the_same_keys(filled):
    conn = filled["conn"]
    before = _digest(conn, SAMPLE_SCHEMA, True)
    S.fill(conn, SAMPLE_SCHEMA, filled["items"])
    conn.commit()
    assert _digest(conn, SAMPLE_SCHEMA, True) == before


# ── the full build (slow: every captured page) ──────────────────────────────────

FULL_SCHEMA = "scratch_charities_b_slow"


@pytest.fixture(scope="module")
def full():
    _db_or_skip()
    from support.docstore.landing import read_bytes
    with db.connect(db.READ_KEY, "querynz_v4") as src, db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        src.execute("SET statement_timeout = '60s'")
        pages = load.listings(src)
        if not pages["Organisations"]:
            pytest.skip("the capture holds no finished pass of Organisations")
        with conn.transaction():
            counts = load.build(conn, FULL_SCHEMA, pages)
        yield {"src": src, "conn": conn, "pages": pages, "counts": counts, "read_bytes": read_bytes}


@pytest.mark.slow
def test_the_full_build_reconciles_every_row_of_every_captured_page(full):
    assert check.reconcile(full["conn"], FULL_SCHEMA, full["pages"]) == []
    landed = sum(capture.stated(full["src"], s)[1] for s in ("Organisations", "Officers", "AnnualReturn"))
    c = full["counts"]
    assert c["rows_in"] >= landed > 1_000_000


@pytest.mark.slow
def test_the_full_build_meets_the_register_s_counts_and_its_own_view(full):
    f = check.figures(full["conn"], FULL_SCHEMA, full["src"], full["read_bytes"])
    assert f["reconciles"], f["problems"]
    assert f["counts"]["registered"]["ok"], f["counts"]["registered"]
    assert f["resolution"].get("compared", 0) > 40_000
    assert not {k: v for k, v in f["resolution"].items() if k.endswith("differs")}
    assert f["ok"]


@pytest.mark.slow
def test_a_second_full_build_gives_the_same_rows_under_the_same_keys(full):
    conn = full["conn"]
    before = _digest(conn, FULL_SCHEMA, False)
    with conn.transaction():
        load.build(conn, FULL_SCHEMA, full["pages"])
    assert _digest(conn, FULL_SCHEMA, False) == before
