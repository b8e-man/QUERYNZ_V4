"""The reaches added 2 November 2026, on canned rows: a followed officer's name looked for among the rows no link reaches yet
(officers_named: near, through the officer, set apart as a namesake's, a suppressed officer never looked for); a company start's
own registered name looked for among the Real Estate Authority's agencies (organisation_named: whole name, the legal ending off,
a one-word name never); the walk states how many officers the company lists and how many are suppressed."""
from products.report import catalogue as cat, walk
from products.report.tests.test_reaches import item


def test_a_followed_officers_name_reaches_the_name_only_rows_near_and_through_the_officer(monkeypatch):
    ann = item(ref="companies:companies/9/director/a", title="Ann ROE", row={"full_name": "Ann ROE"})
    hidden = item(ref="companies:companies/9/director/b", title="Bea POE", row={"full_name": "Bea POE"}, suppressed=True)
    seen = []

    def joined(conn, people, allowed, skipped):
        seen.extend(p["ref"] for p in people)
        return {ann["ref"]: [item(ref="rea:rea_parties/1", view="rea_parties", title="Ann ROE", grade="near",
                                  reason="the two rows share a name", rule="same-name")]}, 2

    monkeypatch.setattr(walk, "name_joined", joined)
    got = walk.officers_named(None, [ann, hidden], {"rea_parties"}, [])
    assert seen == [ann["ref"]], "a suppressed officer's name is never looked for"
    row, more = got
    assert row["through"] == ann["ref"] and row["near_link"] is True and row["depth"] == 1 and row["grade"] == "near"
    assert row["rule"] == "same-name" and "Ann ROE" in row["reason"] and "the two rows share a name" in row["reason"]
    assert more == {"omitted": 2, "view": walk.NAME_JOIN_TO[0][0], "via": ann["ref"]}


def test_a_company_starts_own_name_reaches_an_agency_by_its_whole_name_with_the_legal_ending_off(monkeypatch):
    sv = cat.BY_NAME["companies"]
    asked = []

    def rows(conn, sql, params):
        asked.append(params)
        return [{"rea_party_key": "1", "key": "1", "name": "Acme Realty Ltd", "kind": "agency", "decision_key": "d1"},
                {"rea_party_key": "2", "key": "2", "name": "Acme Realty Group Limited", "kind": "agency", "decision_key": "d2"}]

    monkeypatch.setattr(walk.db, "rows", rows)
    monkeypatch.setattr(walk.rows, "title", lambda v, r: r["name"])
    got = walk.organisation_named(None, sv, {"key": "companies/9", "name": "ACME REALTY LIMITED"}, {"rea_parties"}, [])
    assert asked and asked[0][1] == "acme realty" and list(asked[0][0]) == ["agency", "organisation"]
    assert [it["row"]["name"] for it in got] == ["Acme Realty Ltd"], "the whole name only, never a longer one"
    assert got[0]["grade"] == "near" and got[0]["rule"] == "same-name"
    assert walk.org_fold("Acme Realty Limited") == walk.org_fold("ACME REALTY LTD.") == "acme realty"
    asked.clear()
    assert walk.organisation_named(None, sv, {"key": "companies/8", "name": "ACME LIMITED"}, {"rea_parties"}, []) == [] and not asked
    skipped = []
    assert walk.organisation_named(None, sv, {"key": "companies/9", "name": "ACME REALTY LIMITED"}, set(), skipped) == []
    assert skipped == ["rea_parties"]
