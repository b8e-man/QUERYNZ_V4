"""The roles the business-number register states (pub.company_lookup_roles, 1 November 2026): a company's past directors are its
roles, confirmed by the company; a role whose held_key names the monthly file's own director row is that row and is listed once,
from the file; a person's name finds a role no file held, near."""
from products.report import catalogue as cat, walk

COMPANY = {"key": "companies/9429000000001", "name": "ACME LIMITED", "nzbn": "9429000000001"}
FILE_ROLE = {"key": "companies/9429000000001/role/1/aa", "entity_key": COMPANY["key"], "full_name": "Jane DOE", "role_type": "Director",
             "role_status": "ACTIVE", "started_on": None, "ended_on": None, "held_key": "companies/9429000000001/director/x", "suppressed": False}
PAST_ROLE = dict(FILE_ROLE, key="companies/9429000000001/role/2/aa", full_name="John ROE", role_status="INACTIVE", held_key=None)


def test_the_catalogue_knows_the_register_roles_as_a_companys_people():
    v = cat.BY_NAME["company_lookup_roles"]
    assert v.register == "companies" and v.kind == "person" and v.entity == ("companies", "entity_key") and v.suppressed == "suppressed"
    assert ("company_lookup_roles", "entity_key", "ended_on desc") in walk.ROLES_ON["companies"]
    assert walk.ALREADY_LISTED["company_lookup_roles"] == "held_key"
    assert "company_lookup_roles" in [x[0] for x in walk.NAME_JOIN_TO]


def test_a_register_role_the_file_already_holds_is_listed_once_and_a_past_role_is_the_companys(monkeypatch):
    def rows_where(conn, view, column, value, order):
        return (2, [FILE_ROLE, PAST_ROLE]) if view == "company_lookup_roles" else (0, [])
    monkeypatch.setattr(walk, "rows_where", rows_where)
    skipped = []
    got = walk.roles_on(None, cat.BY_NAME["companies"], COMPANY, {"company_lookup_roles"}, skipped)
    roles = [it for it in got if it.get("view") == "company_lookup_roles"]
    assert [it["ref"] for it in roles] == ["companies:" + PAST_ROLE["key"]], "the file's own director is not listed a second time"
    assert roles[0]["via"] == "companies:" + COMPANY["key"]
    assert not walk.roles_on(None, cat.BY_NAME["companies"], COMPANY, set(), skipped) and "company_lookup_roles" in skipped


def test_a_company_that_is_a_general_partner_lists_each_partnership_titled_by_the_partnership(monkeypatch):
    gp = {"key": "limited_partnerships/9429000000002/partner/a/b", "partnership_key": "limited_partnerships/9429000000002", "kind": "body",
          "full_name": "ACME LIMITED", "body_nzbn": COMPANY["nzbn"], "suppressed": False, "current": True, "status": "Active",
          "started_on": None, "ended_on": None}
    asked = []

    def rows_where(conn, view, column, value, order):
        asked.append((view, column, value))
        return (1, [gp]) if view == "limited_partnership_partners" else (0, [])

    def db_rows(conn, sql, params):
        assert "pub.limited_partnerships" in sql and params == (["limited_partnerships/9429000000002"],)
        return [{"key": "limited_partnerships/9429000000002", "name": "ACME FUND LP", "status": "Registered", "number": "1"}]
    monkeypatch.setattr(walk, "rows_where", rows_where)
    monkeypatch.setattr(walk.db, "rows", db_rows)
    got = walk.roles_on(None, cat.BY_NAME["companies"], COMPANY, {"limited_partnership_partners"}, [])
    assert ("limited_partnership_partners", "body_nzbn", COMPANY["nzbn"]) in asked, "joined by the company's business number"
    assert len(got) == 1 and got[0]["via"] == "companies:" + COMPANY["key"] and "general partner of ACME FUND LP" in got[0]["statement"]
    assert walk.roles_on(None, cat.BY_NAME["companies"], dict(COMPANY, nzbn=None), {"limited_partnership_partners"}, []) == []


def test_a_holder_is_joined_to_its_company_by_name_whatever_the_case(monkeypatch):
    """Arthur, 2 November 2026: ignore case when matching a holder of record to its company by name."""
    asked = []

    def db_rows(conn, sql, params):
        asked.append((sql, params))
        return [{"key": "companies/7", "name": "CENTRAL CHERRY ORCHARD LIMITED PARTNERSHIP", "nzbn": "7"},
                {"key": "companies/8", "name": "TWIN NAME LIMITED", "nzbn": "8"}, {"key": "companies/9", "name": "Twin Name Limited", "nzbn": "9"}]
    monkeypatch.setattr(walk.db, "rows", db_rows)
    got = walk.resolve_holders(None, [{"key": "h1", "name": " Central Cherry Orchard Limited Partnership "},
                                      {"key": "h2", "name": "twin name limited"}])
    assert "upper(name)" in asked[0][0] and asked[0][1] == (["CENTRAL CHERRY ORCHARD LIMITED PARTNERSHIP", "TWIN NAME LIMITED"],)
    assert got["h1"][0]["key"] == "companies/7" and got["h1"][1:] == ("name", 1)
    assert got["h2"] == (None, "name", 2), "two companies whose names differ only in case: not followed, both counted"


NOW_HOLDING = {"key": "companies/9429000000001/holding/a/aa", "entity_key": COMPANY["key"], "holder_type": "individual", "name": "Jane DOE",
               "shares": 100, "allocation": 0, "started_on": None, "ended_on": None, "current": True, "suppressed": False}
PAST_HOLDING = dict(NOW_HOLDING, key="companies/9429000000001/holding/b/aa", name="John ROE", shares=None, current=False,
                    started_on="2013-09-23", ended_on="2017-01-26")


def test_a_past_holding_the_register_states_is_the_companys_and_a_current_one_is_left_to_the_file(monkeypatch):
    """pub.company_lookup_holdings (2 November 2026): a holding the register still calls current is the monthly file's holder, listed
    once from the file; a past one is the company's, with its dates; a person's name finds a past holding elsewhere, near."""
    v = cat.BY_NAME["company_lookup_holdings"]
    assert v.register == "companies" and v.entity == ("companies", "entity_key") and v.suppressed == "suppressed" and "past holder" in v.statement
    assert walk.ALREADY_LISTED["company_lookup_holdings"] == "current"
    assert "company_lookup_holdings" in [x[0] for x in walk.NAME_JOIN_TO]

    def rows_where(conn, view, column, value, order):
        return (2, [NOW_HOLDING, PAST_HOLDING]) if view == "company_lookup_holdings" else (0, [])
    monkeypatch.setattr(walk, "rows_where", rows_where)
    got = walk.roles_on(None, cat.BY_NAME["companies"], COMPANY, {"company_lookup_holdings"}, [])
    held = [it for it in got if it.get("view") == "company_lookup_holdings"]
    assert [it["ref"] for it in held] == ["companies:" + PAST_HOLDING["key"]] and held[0]["via"] == "companies:" + COMPANY["key"]


def test_the_name_joins_read_every_order_by_the_one_shared_reading():
    """keys.names reads both sides (2 November 2026): 'MCINDOE, Johanna Maria' meets 'Johanna Maria MCINDOE', a title is not a
    name, and the walk keeps no turn of its own."""
    assert walk.name_keys("MCINDOE, Johanna Maria") == walk.name_keys("Johanna Maria MCINDOE") == ("johanna maria mcindoe", "johanna mcindoe")
    assert walk.name_keys("Hon Dr Jane SMITH")[1] == walk.name_keys("SMITH, Jane")[1] == "jane smith"
    assert walk.name_keys("Rāwiri WAITITI") == walk.name_keys("Rawiri Waititi")
    assert not hasattr(walk, "given_first") and not hasattr(walk, "SURNAME_FIRST")
    sql, params = walk.words_clause("name", [["johanna", "mcindoe"], ["johanna", "mcindoe"], []])
    assert params == [["johanna", "mcindoe"]] and sql.count("@>") == 1


def test_a_surname_first_holding_is_found_for_a_given_first_director(monkeypatch):
    """The name join, end to end on fakes: the query narrows by the words in any order; keys.names decides."""
    person = {"ref": "companies:companies/1/director/a", "view": "directors", "suppressed": False,
              "row": {"full_name": "Johanna Maria MCINDOE"}}
    rows_seen = []

    def fake_rows(conn, sql, params):
        rows_seen.append(sql)
        if "pub.company_lookup_holdings" in sql:
            assert "@>" in sql and ["johanna", "mcindoe"] in params
            return [dict(PAST_HOLDING, name="MCINDOE, Johanna Maria", key="companies/2/holding/a/aa", entity_key="companies/2"),
                    dict(PAST_HOLDING, name="MCINDOE, Johanna", key="companies/3/holding/a/aa", entity_key="companies/3"),
                    dict(PAST_HOLDING, name="MCINDOE, Peter Johanna", key="companies/4/holding/a/aa", entity_key="companies/4")]
        return []
    monkeypatch.setattr(walk.db, "rows", fake_rows)
    out, omitted = walk.name_joined(None, [person], {"company_lookup_holdings"}, [])
    got = sorted(it["ref"] for it in out[person["ref"]])
    assert got == ["companies:companies/2/holding/a/aa", "companies:companies/3/holding/a/aa"], "whole, or first and last; never a middle name"
    assert all(it["grade"] == "near" for it in out[person["ref"]]) and omitted == 0
