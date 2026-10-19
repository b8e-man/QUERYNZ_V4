"""The interests lane's tests (fast tier). The parser is tested on pages laid
out like the measured editions, written out here with example names; the
filled sample is tested against the row contract, the catch log's sums,
each edition's own list of categories, and hard limit 15. No model is
called."""
import datetime as dt
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.mp_interests import check, parse

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "mp_interests")

TITLE = """                                            J. 7
Register of Pecuniary and
Other Specified Interests of
Members of Parliament:
Summary of annual returns as at
31 January 2018
"""
INTRO = """REGISTER OF PECUNIARY AND OTHER SPECIFIED INTERESTS OF MEMBERS OF PARLIAMENT: SUMMARY OF
ANNUAL RETURNS                                                                             J. 7
Introduction
The interests that are required to be registered are listed below.
1      Company directorships and controlling interests (clause 5(1)(a))
2      Interests (such as shares and bonds) in companies and business
       entities (clause 5(1)(b) and (2))
6      Real property (clause 5(1)(f) and (1)(g))
9      Debtors (clauses 5(1)(j), 5(4), 6, and 7)
10     Creditors (clauses 5(1)(k), 5(4), 6, and 7)
12     Gifts (clause 8(1)(b) and (3))
Appendix B of the Standing Orders sets out the rules.
                                           3
"""
MEMBERS = """REGISTER OF PECUNIARY AND OTHER SPECIFIED INTERESTS OF MEMBERS OF PARLIAMENT: SUMMARY OF
ANNUAL RETURNS                                                                             J. 7


Hon Alex Example (Green, Somewhere)
1     Company directorships and controlling interests
      Example Farms Limited – farming
6     Real property
      Family home (jointly owned), Exampleton
9     Debtors
      Example Bank – bank deposit
12    Gifts
      Tickets to a test match and hospitality at the ground, given by the national body for the
      sport, valued above the threshold – Example Rugby



Sam (Sammy) Sample (National, List)
10    Creditors
      Example Bank – mortgage (refinanced in March
      2018)
*
  Interest rate payable in relation to the debt is less than the normal market interest rate
that applied at the time the debt was incurred.



Kim Sample (Exampletown)*
4     Beneficial interests in, and trusteeships of, trusts
      Sample Family Trust (trustee and beneficiary)
11    Overseas travel costs
      Travel to a conference – Example Foundation


Lee Example (Labour, List)
No interests declared under the categories set out in clauses 5 to 8 of Appendix B
of the Standing Orders of the House of Representatives.
                                           4
"""
ANNEX = """REGISTER OF PECUNIARY AND OTHER SPECIFIED INTERESTS OF MEMBERS OF PARLIAMENT: SUMMARY OF
STANDING ORDERS—APPENDIX B
1      Purpose of the Register
       The purpose of the register is to record members' interests.
19     Responsibilities of members and registrar
       A member is responsible for the return.
"""
PAGES = {1: TITLE, 2: INTRO, 3: MEMBERS, 4: ANNEX}


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


def test_the_edition_s_date_and_its_own_category_list_are_read_from_its_front():
    ed = parse.edition(PAGES)
    assert ed.as_at == dt.date(2018, 1, 31)
    assert ed.categories["2"] == ("Interests (such as shares and bonds) in companies and business entities",
                                  "business-interests"), "a wrapped heading, its clause reference dropped"
    assert ed.categories["9"][1] == "debts-owed-to-member" and ed.categories["10"][1] == "debts-owed-by-member"


def test_the_reprinted_rules_after_the_last_member_are_nobody_s_declarations():
    ed = parse.edition(PAGES)
    assert ed.annex_at == (4, 2)
    assert not any("Responsibilities" in d.text or "purpose of the register" in d.text.lower() for d in ed.declarations)


def test_members_are_read_with_nicknames_independents_and_statements():
    ed = parse.edition(PAGES)
    assert [(m.name, m.party, m.electorate) for m in ed.members] == [
        ("Hon Alex Example", "Green", "Somewhere"), ("Sam (Sammy) Sample", "National", "List"),
        ("Kim Sample", None, "Exampletown"), ("Lee Example", "Labour", "List")]
    assert ed.members[3].statement.startswith("No interests declared") and ed.members[3].statement.endswith("Representatives.")


def test_a_declaration_is_filed_by_its_heading_never_its_number():
    ed = parse.edition(PAGES)
    got = [(ed.members[d.member].name, d.number, d.category) for d in ed.declarations]
    assert ("Hon Alex Example", "9", "debts-owed-to-member") in got
    assert ("Sam (Sammy) Sample", "10", "debts-owed-by-member") in got
    assert ("Kim Sample", "11", "overseas-travel") in got
    old = parse.edition({**PAGES, 3: MEMBERS.replace("9     Debtors", "9     Creditors")})
    assert [d.category for d in old.declarations if d.number == "9"] == ["debts-owed-by-member"], \
        "before 2018, 9 is Creditors: the heading decides"


def test_wrapped_lines_join_and_the_debt_footnote_is_not_a_declaration():
    ed = parse.edition(PAGES)
    gift = next(d for d in ed.declarations if d.category == "gifts")
    assert gift.text.endswith("valued above the threshold – Example Rugby") and "given by the national" in gift.text
    mortgage = next(d for d in ed.declarations if d.category == "debts-owed-by-member")
    assert mortgage.text == "Example Bank – mortgage (refinanced in March 2018)", "a line that closes a bracket is a wrap"
    assert not any("Interest rate payable" in d.text for d in ed.declarations)
    assert len(ed.declarations) == 7 and ed.set_aside == []


def test_a_one_bracket_declaration_is_never_a_member():
    page = MEMBERS.replace("Kim Sample (Exampletown)*", "      Example Family Trust (beneficiary)")
    ed = parse.edition({**PAGES, 3: page})
    assert [m.name for m in ed.members] == ["Hon Alex Example", "Sam (Sammy) Sample", "Lee Example"]


def test_an_unseen_heading_is_not_guessed():
    assert parse.heading_of("Debts owed to you") == "debts-owed-to-member"
    assert parse.heading_of("Interests in boats") is None


def test_the_outside_check_names_a_number_whose_heading_disagrees_with_the_edition_s_list():
    rows = [{"as_at": "2018-01-31", "number": 9, "intro_heading": "Debtors", "intro_category": "debts-owed-to-member",
             "body_headings": "Debtors", "body_category": "debts-owed-to-member", "agrees": True},
            {"as_at": "2018-01-31", "number": 10, "intro_heading": "Creditors", "intro_category": "debts-owed-by-member",
             "body_headings": "Overseas travel costs", "body_category": "overseas-travel", "agrees": False}]
    out = check.compare(rows)
    assert len(out["agree"]) == 1 and [r["number"] for r in out["differ"]] == [10]


# --- the filled sample -------------------------------------------------------

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_mp_interests"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    from registers.mp_interests import sample as S
    schema = _schema()
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}_private")
        S.fill(conn, schema, sample.read_list(os.path.join(LANE, "sample.list")))
        conn.commit()

        def q(t, s=schema):
            cur = conn.execute(f"SELECT * FROM {s}.mp_interests_{t}")
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        yield {"schema": schema, "conn": conn, "private": q("declaration_text", schema + "_private"),
               **{t: q(t) for t in ("files", "set_aside", "editions", "members", "declarations", "numbering")}}


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("editions", "members", "declarations"):
        for r in filled[t]:
            row = {**r, "loaded_at": r["loaded_at"].isoformat()}
            assert rowcontract.validate(row, today) == [], (t, r["key"])
    assert all(d["key"].startswith(d["document"] + "/p") for d in filled["declarations"])


def test_every_edition_is_read_and_its_numbering_agrees_with_its_own_list(filled):
    assert len(filled["editions"]) == 7 and not [a for a in filled["set_aside"] if a["stage"] in ("edition", "verbatim")]
    assert all(n["agrees"] for n in filled["numbering"])
    assert sorted(e["as_at"].year for e in filled["editions"]) == [2006, 2011, 2015, 2017, 2018, 2019, 2026]


def test_nine_means_creditors_before_2018_and_debtors_after(filled):
    by_year = {}
    for d in filled["declarations"]:
        if d["number_printed"] == "9":
            by_year.setdefault(d["as_at"].year, set()).add(d["category"])
    assert by_year[2017] == {"debts-owed-by-member"} and by_year[2018] == {"debts-owed-to-member"}


def test_the_members_the_old_parser_missed_are_read(filled):
    m = {(x["as_at"].year, x["member"]): x for x in filled["members"]}
    assert (2019, "Jami-Lee Ross") in m and m[(2019, "Jami-Lee Ross")]["party_label"] is None
    assert m[(2026, "Mariameno Kapa-Kingi")]["electorate"] == "Te Tai Tokerau"
    assert any(y == 2006 and x["party_label"] == "Progressive" for (y, _), x in m.items())
    assert sum(1 for x in filled["members"] if x["statement"] == "Return not received by due date") == 2


def test_no_published_declaration_carries_a_real_property_text(filled):
    rp = [d for d in filled["declarations"] if d["category"] == "real-property"]
    assert rp and all(d["text"] is None and d["withheld"] for d in rp)
    assert {p["key"] for p in filled["private"]} == {d["key"] for d in rp}
    assert all(d["text"] for d in filled["declarations"] if d["category"] != "real-property")


def test_a_rebuild_gives_every_row_the_same_key(filled):
    from registers.mp_interests import sample as S
    conn, schema = filled["conn"], filled["schema"]
    S.fill(conn, schema, sample.read_list(os.path.join(LANE, "sample.list")))
    again = {r[0] for r in conn.execute(f"SELECT key FROM {schema}.mp_interests_declarations")}
    assert again == {d["key"] for d in filled["declarations"]}
    conn.rollback()


def test_the_published_views_build_on_the_lane_s_tables(filled):
    from registers.mp_interests import load as L
    conn, schema = filled["conn"], filled["schema"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.pub_mp_interests_"))
    n = conn.execute(f"SELECT count(*) FROM {schema}.pub_mp_interests_mp_interests WHERE text IS NOT NULL").fetchone()[0]
    leak = conn.execute(f"SELECT count(*) FROM {schema}.pub_mp_interests_mp_interests "
                        f"WHERE category = 'real-property' AND text IS NOT NULL").fetchone()[0]
    assert n > 0 and leak == 0
    conn.rollback()
