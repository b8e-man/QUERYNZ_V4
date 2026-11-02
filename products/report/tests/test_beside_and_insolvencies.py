"""Step 8.1 (2 November 2026): the walk's beside step and the companies file's insolvency appointments in a company's failure, on a
canned register (no database)."""
import datetime as dt

from products.report import walk


def director(key, entity, name, appointed):
    return {"key": key, "entity_key": entity, "full_name": name, "role_type": "DIRECTOR", "appointed_on": dt.date(*appointed),
            "ended_on": None, "in_latest": True, "suppressed": False}


class Beside:
    """pub.directors for company 3: the followed officer's own row and three others, one past the limit."""
    def __init__(self):
        self.calls = []

    def rows(self, conn, sql, params=()):
        assert "from pub.directors where entity_key" in sql and "ended_on is null" in sql, sql
        key, own, limit = params
        self.calls.append((key, list(own), limit))
        everyone = [director("companies/3/director/a", "companies/3", "Jane Mary DOE", (2015, 5, 1)),
                    director("companies/3/director/b", "companies/3", "John SMITH", (2016, 1, 1)),
                    director("companies/3/director/c", "companies/3", "Mere TAMA", (2017, 1, 1)),
                    director("companies/3/director/d", "companies/3", "Ari NGATA", (2018, 1, 1))]
        left = [dict(r) for r in everyone if r["key"] not in own]
        return [dict(r, total=len(left)) for r in left[:limit]]


OFFICER = {"ref": "companies:companies/1/director/a", "view": "directors", "title": "Jane Mary DOE", "suppressed": False}
ON_GAMMA = {"ref": "companies:companies/3/director/a", "view": "directors", "title": "Jane Mary DOE", "through": OFFICER["ref"]}
GAMMA = {"ref": "companies:companies/3", "view": "companies", "title": "GAMMA BUILD LIMITED", "through": OFFICER["ref"]}
NEAR_CO = {"ref": "companies:companies/8", "view": "companies", "title": "A NAMESAKE'S LIMITED", "through": OFFICER["ref"], "near_link": True}


def test_beside_lists_the_other_directors_of_each_officers_company_near_to_the_limit_and_counts_the_rest(monkeypatch):
    fake = Beside()
    monkeypatch.setattr(walk.db, "rows", fake.rows)
    monkeypatch.setitem(walk.LIMITS, "beside", 2)
    skipped = []
    out = walk.beside_officers(None, "companies:companies/1", [OFFICER, ON_GAMMA, GAMMA, NEAR_CO], {"directors"}, skipped)
    assert fake.calls == [("companies/3", ["companies/3/director/a"], 2)], "only the officer's own company; a near link's is never read"
    got = [x for x in out if "omitted" not in x]
    assert [x["title"] for x in got] == ["John SMITH", "Mere TAMA"], "the officer's own row is left out"
    assert all(x["grade"] == "near" and x["beside"] and x["through"] == OFFICER["ref"] and x["via"] == GAMMA["ref"] for x in got)
    assert all("Jane Mary DOE" in x["reason"] and "GAMMA BUILD LIMITED" in x["reason"] for x in got)
    assert [x for x in out if "omitted" in x] == [{"omitted": 1, "view": "directors", "via": GAMMA["ref"]}]
    assert walk.beside_officers(None, "companies:companies/1", [OFFICER, GAMMA], set(), skipped) == [] and skipped == ["directors"]


class Failures:
    """Company 4: no insolvent status, no Gazette notice, a solvent winding-up in 2019 and a liquidator after none in 2024; company 5:
    a Gazette notice in 2023 and the file's earlier appointment in 2022."""
    def rows(self, conn, sql, params=()):
        if "from pub.companies" in sql:
            return [{"key": "companies/4", "status": "Registered"}, {"key": "companies/5", "status": "In Liquidation"}]
        if "from pub.gazette_liquidations" in sql:
            return [{"register_key": "companies/5", "key": "gazette/2023-al1/company/5", "published_on": dt.date(2023, 5, 1)}]
        if "from pub.company_insolvencies" in sql:
            assert "not coalesce(resolution_of_solvency, false)" in sql, "a solvent winding-up is no failure"
            return [{"entity_key": "companies/4", "key": "company_insolvencies/4/2", "appointed_on": dt.date(2024, 3, 2)},
                    {"entity_key": "companies/5", "key": "company_insolvencies/5/1", "appointed_on": dt.date(2022, 9, 9)}]
        raise AssertionError(sql)


def test_a_companys_failure_is_dated_by_the_companies_files_appointment_where_the_gazette_gave_none_or_a_later_one(monkeypatch):
    monkeypatch.setattr(walk.db, "rows", Failures().rows)
    f = walk.company_failures(None, ["companies/4", "companies/5"])
    assert f["companies/4"]["on"] == "2024-03-02" and f["companies/4"]["notice"].endswith("company_insolvencies/4/2")
    assert f["companies/5"]["on"] == "2022-09-09" and f["companies/5"]["status"] == "In Liquidation"
