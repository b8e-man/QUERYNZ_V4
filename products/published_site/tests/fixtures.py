"""Fixture rows in the shape of the published views, enough for every rule: two parties, a year with two
returns held, Part A rows across the 2017 split, a disclosure a return covers and one in the open year."""
A, B = "ec-party/1995-02-17/a28c696c2e25", "ec-party/1994-12-02/af3607addd1b"
D = {n: chr(97 + i) * 64 for i, n in enumerate("a b c d e f g h".split())}


def tables():
    return {
        "pub.parties": [
            {"key": A, "name": "ACT New Zealand", "first_name": None, "abbreviation": "The ACT Party", "website": "www.act.org.nz", "on_register": True,
             "registered_on": "1995-02-17", "cancelled_on": None, "secretary": "S", "document": D["g"], "page": 1, "place": "row 1"},
            {"key": B, "name": "The New Zealand National Party", "first_name": None, "abbreviation": "National Party", "website": "x", "on_register": True,
             "registered_on": "1994-12-02", "cancelled_on": None, "secretary": "T", "document": D["g"], "page": 1, "place": "row 2"}],
        "pub.party_names": [{"party": A, "name": "ACT New Zealand", "name_key": "act", "kind": "registered", "from_on": "1995-02-17", "to_on": None}],
        "pub.party_return_totals": [
            {"key": "r1", "document": D["a"], "page": 1, "party": "ACT New Zealand", "party_key": A, "party_label": "ACT", "year": 2017,
             "declared_total": 1000.0, "part_a": 600.0, "declared_parts": "A+C", "total_check": "parts-sum", "read_from": "text", "replaced_by": None, "loans_total": None},
            {"key": "r2", "document": D["b"], "page": 1, "party": "ACT New Zealand", "party_key": A, "party_label": "ACT", "year": 2023,
             "declared_total": 50000.0, "part_a": 40000.0, "declared_parts": "A+C", "total_check": "parts-sum", "read_from": "pixels", "replaced_by": None, "loans_total": 0},
            {"key": "r3", "document": D["c"], "page": 1, "party": "The New Zealand National Party", "party_key": B, "party_label": "National", "year": 2022,
             "declared_total": 100.0, "part_a": 100.0, "declared_parts": "A", "total_check": "parts-sum", "read_from": "text", "replaced_by": None, "loans_total": None},
            {"key": "r4", "document": D["d"], "page": 1, "party": "The New Zealand National Party", "party_key": B, "party_label": "National amended", "year": 2022,
             "declared_total": 120.0, "part_a": 120.0, "declared_parts": "A", "total_check": "parts-sum", "read_from": "text", "replaced_by": None, "loans_total": None},
            {"key": "r5", "document": D["h"], "page": 1, "party": "The New Zealand National Party", "party_key": B, "party_label": "National", "year": 2020,
             "declared_total": 9.0, "part_a": 9.0, "declared_parts": "A", "total_check": "parts-sum", "read_from": "text", "replaced_by": "r6", "loans_total": None}],
        "pub.party_return_donors": [
            {"key": "r1/A/1", "return_key": "r1", "document": D["a"], "page": 2, "ordinal": 1, "party": "ACT New Zealand", "party_key": A, "party_label": "ACT",
             "year": 2017, "donor": "Jane Q Donor", "amount": 100.0, "dates": "01/03/2017", "read_from": "text", "replaced_by": None},
            {"key": "r1/A/2", "return_key": "r1", "document": D["a"], "page": 2, "ordinal": 2, "party": "ACT New Zealand", "party_key": A, "party_label": "ACT",
             "year": 2017, "donor": "Jane Q. Donor", "amount": 500.0, "dates": "30/09/2017", "read_from": "text", "replaced_by": None},
            {"key": "r2/A/1", "return_key": "r2", "document": D["b"], "page": 2, "ordinal": 1, "party": "ACT New Zealand", "party_key": A, "party_label": "ACT",
             "year": 2023, "donor": "Big Co Limited", "amount": 40000.0, "dates": "", "read_from": "pixels", "replaced_by": None},
            {"key": "r3/A/1", "return_key": "r3", "document": D["c"], "page": 2, "ordinal": 1, "party": "The New Zealand National Party", "party_key": B,
             "party_label": "National", "year": 2022, "donor": "Twice Counted", "amount": 100.0, "dates": "", "read_from": "text", "replaced_by": None},
            {"key": "r4/A/1", "return_key": "r4", "document": D["d"], "page": 2, "ordinal": 1, "party": "The New Zealand National Party", "party_key": B,
             "party_label": "National amended", "year": 2022, "donor": "Twice Counted", "amount": 120.0, "dates": "", "read_from": "text", "replaced_by": None}],
        "pub.party_return_loans": [],
        "pub.disclosures": [
            {"key": "d1", "document": D["e"], "page": 1, "place": None, "regime": "over-20000-from-2023", "party": "ACT New Zealand", "party_label": "ACT",
             "donor_name": "Big Co Limited", "amount": 40000.0, "received_on": "2023-05-01", "given_on": None, "amendment": "none", "withdrawn_on": None,
             "href": "/assets/x.pdf", "declaration_document": D["f"]},
            {"key": "d2", "document": D["e"], "page": 1, "place": None, "regime": "over-20000-from-2023", "party": "ACT New Zealand", "party_label": "ACT",
             "donor_name": "Open Year Giver", "amount": 25000.0, "received_on": "2026-02-02", "given_on": None, "amendment": "none", "withdrawn_on": None,
             "href": "/assets/y.pdf", "declaration_document": None},
            {"key": "d3", "document": D["e"], "page": 1, "place": None, "regime": "over-20000-from-2023", "party": "ACT New Zealand", "party_label": "ACT",
             "donor_name": "Withdrawn Giver", "amount": 99999.0, "received_on": "2026-03-03", "given_on": None, "amendment": "amendment withdrawn",
             "withdrawn_on": None, "href": None, "declaration_document": None}],
        "pub.disclosure_items": [],
        "pub.candidate_return_totals": [
            {"key": "cr-2023-epsom-seymour", "document": D["c"], "page": 1, "place": "declaration", "year": 2023, "surname": "SEYMOUR", "given_names": "David",
             "electorate": "Epsom", "party": "ACT New Zealand", "status": "current", "replaced_by": None, "placed_by": "listing link",
             "donations": 1000.0, "part_a": 1000.0, "part_c": 0, "part_d": 0, "donations_check": "parts-sum", "expenses": 500.0, "part_f": 500.0, "part_g": 0,
             "expenses_check": "parts-sum", "loans": 0.0, "loans_check": "declared-nil", "signed": "yes",
             "commission_donations": 1200.0, "commission_expenses": 500.0, "commission_loans": None, "commission_file": "2023-candidate-returns.csv",
             "commission_key": "2023/Epsom/SEYMOUR", "read_from": "text", "reader": "x", "profile": "p", "profile_version": 1, "donors_check": "parts-sum"},
            {"key": "cr-2023-epsom-other", "document": D["d"], "page": 1, "place": "declaration", "year": 2023, "surname": "OTHER", "given_names": "Ann",
             "electorate": "Epsom", "party": "Nobody Party", "status": "current", "replaced_by": None, "placed_by": "listing link",
             "donations": 0.0, "part_a": None, "part_c": 0, "part_d": 0, "donations_check": "declared-nil", "expenses": 0.0, "part_f": 0, "part_g": 0,
             "expenses_check": "declared-nil", "loans": 0.0, "loans_check": "declared-nil", "signed": "yes",
             "commission_donations": 0.0, "commission_expenses": 0.0, "commission_loans": None, "commission_file": "2023-candidate-returns.csv",
             "commission_key": "2023/Epsom/OTHER", "read_from": "pixels", "reader": "x", "profile": "p", "profile_version": 1, "donors_check": "declared-nil"},
            {"key": "cr-2023-epsom-nobody", "document": D["f"], "page": 1, "place": "declaration", "year": 2023, "surname": "NOBODY", "given_names": "Ghost",
             "electorate": "Epsom", "party": "Ghost Party", "status": "unlisted", "replaced_by": None, "placed_by": "file name",
             "donations": 77.0, "part_a": 77.0, "part_c": 0, "part_d": 0, "donations_check": "parts-sum", "expenses": 7.0, "part_f": 7.0, "part_g": 0,
             "expenses_check": "parts-sum", "loans": 0.0, "loans_check": "declared-nil", "signed": "yes",
             "commission_donations": None, "commission_expenses": None, "commission_loans": None, "commission_file": None,
             "commission_key": None, "read_from": "text", "reader": "x", "profile": "p", "profile_version": 1, "donors_check": "parts-sum"},
            {"key": "cr-2018-epsom-bye", "document": D["f"], "page": 1, "place": "declaration", "year": 2018, "surname": "BYE", "given_names": "Election",
             "electorate": "Epsom", "party": "Nobody Party", "status": "current", "replaced_by": None, "placed_by": "listing link",
             "donations": 9.0, "part_a": 9.0, "part_c": 0, "part_d": 0, "donations_check": "parts-sum", "expenses": 1.0, "part_f": 1.0, "part_g": 0,
             "expenses_check": "parts-sum", "loans": 0.0, "loans_check": "declared-nil", "signed": "yes",
             "commission_donations": 9.0, "commission_expenses": 1.0, "commission_loans": None, "commission_file": "2018-by-election.csv",
             "commission_key": "2018/Epsom/BYE", "read_from": "text", "reader": "x", "profile": "p", "profile_version": 1, "donors_check": "parts-sum"},
            {"key": "cr-2023-epsom-seymour-old", "document": D["e"], "page": 1, "place": "declaration", "year": 2023, "surname": "SEYMOUR", "given_names": "David",
             "electorate": "Epsom", "party": "ACT New Zealand", "status": "replaced", "replaced_by": "cr-2023-epsom-seymour", "placed_by": "listing link",
             "donations": 5.0, "part_a": 5.0, "part_c": 0, "part_d": 0, "donations_check": "parts-sum", "expenses": 5.0, "part_f": 5.0, "part_g": 0,
             "expenses_check": "parts-sum", "loans": 0.0, "loans_check": "declared-nil", "signed": "yes",
             "commission_donations": None, "commission_expenses": None, "commission_loans": None, "commission_file": None,
             "commission_key": None, "read_from": "text", "reader": "x", "profile": "p", "profile_version": 1, "donors_check": "parts-sum"}],
        "pub.candidate_return_donors": [
            {"key": "cr-2023-epsom-seymour/A/1", "return_key": "cr-2023-epsom-seymour", "document": D["c"], "page": 2, "ordinal": 1, "year": 2023, "surname": "SEYMOUR",
             "given_names": "David", "electorate": "Epsom", "party": "ACT New Zealand", "status": "current", "replaced_by": None,
             "donor": "Big Co Limited", "amount": 600.0, "dates": "01/02/2023", "contributions": None, "read_from": "text", "reader": "x", "profile": "p", "profile_version": 1, "place": None},
            {"key": "cr-2023-epsom-seymour/A/2", "return_key": "cr-2023-epsom-seymour", "document": D["c"], "page": 2, "ordinal": 2, "year": 2023, "surname": "SEYMOUR",
             "given_names": "David", "electorate": "Epsom", "party": "ACT New Zealand", "status": "current", "replaced_by": None,
             "donor": "Local Giver", "amount": 400.0, "dates": "02/02/2023", "contributions": None, "read_from": "text", "reader": "x", "profile": "p", "profile_version": 1, "place": None},
            {"key": "cr-2023-epsom-seymour/A/3", "return_key": "cr-2023-epsom-seymour", "document": D["c"], "page": 2, "ordinal": 3, "year": 2023, "surname": "SEYMOUR",
             "given_names": "David", "electorate": "Epsom", "party": "ACT New Zealand", "status": "current", "replaced_by": None,
             "donor": "ACT Epsom Electorate Committee", "amount": 200.0, "dates": "03/03/2023", "contributions": None, "read_from": "text", "reader": "x", "profile": "p", "profile_version": 1, "place": None},
            {"key": "cr-2023-epsom-nobody/A/1", "return_key": "cr-2023-epsom-nobody", "document": D["f"], "page": 2, "ordinal": 1, "year": 2023, "surname": "NOBODY",
             "given_names": "Ghost", "electorate": "Epsom", "party": "Ghost Party", "status": "unlisted", "replaced_by": None,
             "donor": "Local Giver", "amount": 77.0, "dates": "", "contributions": None, "read_from": "text", "reader": "x", "profile": "p", "profile_version": 1, "place": None}],
        "pub.elections": [
            {"key": "ge-2023", "kind": "general", "name": "2023 General Election", "electorate": None, "polled_on": "2023-10-14", "document": D["g"], "page": 1},
            {"key": "ge-2026", "kind": "general", "name": "2026 General Election", "electorate": None, "polled_on": None, "document": D["g"], "page": 1},
            {"key": "ge-2020", "kind": "general", "name": "2020 General Election", "electorate": None, "polled_on": "2020-10-17", "document": D["g"], "page": 1},
            {"key": "ge-2014", "kind": "general", "name": "2014 General Election", "electorate": None, "polled_on": "2014-09-20", "document": D["g"], "page": 1}],
        "pub.electorates": [
            {"key": "ge-2023/epsom", "election": "ge-2023", "name": "Epsom", "number": 1, "statsnz_code": "01", "statsnz_name": "Epsom", "layer": "general",
             "votes_counted": 100, "candidate_total": 90, "party_total": 95, "result_held": True, "poll_cancelled": False, "document": D["g"], "page": 2, "place": "row 1"},
            {"key": "ge-2026/epsom", "election": "ge-2026", "name": "Epsom", "number": None, "result_held": False, "poll_cancelled": False, "document": D["g"], "page": 3},
            {"key": "ge-2014/epsom", "election": "ge-2014", "name": "Epsom", "number": 1, "result_held": True, "poll_cancelled": False, "document": D["g"], "page": 4}],
        "pub.candidates": [
            {"key": "ge-2023/seymour-david/epsom", "election": "ge-2023", "name": "SEYMOUR, David", "display_name": "David SEYMOUR", "name_key": "david seymour",
             "party": "ACT", "party_registered": "ACT New Zealand", "electorate": "ge-2023/epsom", "list_place": 1, "votes": 60, "poll_cancelled": False, "document": D["g"], "page": 2},
            {"key": "ge-2023/other-ann/epsom", "election": "ge-2023", "name": "OTHER, Ann", "display_name": "Ann OTHER", "name_key": "ann other",
             "party": "Nobody Party", "party_registered": None, "electorate": "ge-2023/epsom", "list_place": None, "votes": 30, "poll_cancelled": False, "document": D["g"], "page": 2},
            {"key": "ge-2026/seymour-david/epsom", "election": "ge-2026", "name": "SEYMOUR, David", "display_name": "David SEYMOUR", "name_key": "david seymour",
             "party": "ACT", "party_registered": "ACT New Zealand", "electorate": "ge-2026/epsom", "list_place": None, "votes": None, "poll_cancelled": False, "document": D["g"], "page": 3},
            {"key": "ge-2026/list-lena/list", "election": "ge-2026", "name": "LIST, Lena", "display_name": "Lena LIST", "name_key": "lena list",
             "party": "ACT", "party_registered": "ACT New Zealand", "electorate": None, "list_place": 7, "votes": None, "poll_cancelled": False, "document": D["g"], "page": 6,
             "list_document": D["h"], "list_place_cite": "ACT New Zealand item 7"},
            {"key": "ge-2014/old-bob/epsom", "election": "ge-2014", "name": "OLD, Bob", "display_name": "Bob OLD", "name_key": "bob old",
             "party": None, "party_registered": None, "electorate": "ge-2014/epsom", "list_place": None, "votes": 5, "poll_cancelled": False, "document": D["g"], "page": 4}],
        "pub.members": [
            {"key": "m1", "election": "ge-2023", "name": "CHHOUR, Karen", "display_name": "Karen CHHOUR", "name_key": "chhour karen", "party": "ACT",
             "party_registered": "ACT New Zealand", "route": "list", "electorate": None, "candidate": None, "from_on": "2023-10-14", "to_by": None, "ended_on": None, "document": D["g"], "page": 5},
            {"key": "m2", "election": "ge-2023", "name": "SEYMOUR, David", "display_name": "David SEYMOUR", "name_key": "david seymour", "party": "ACT",
             "party_registered": "ACT New Zealand", "route": "electorate", "electorate": "ge-2023/epsom", "candidate": "ge-2023/seymour-david/epsom",
             "from_on": "2023-10-14", "to_by": None, "ended_on": None, "document": D["g"], "page": 5},
            {"key": "m3", "election": "ge-2020", "name": "GONE, Pat", "display_name": "Pat GONE", "name_key": "gone pat", "party": "ACT",
             "party_registered": "ACT New Zealand", "route": "list", "electorate": None, "candidate": None, "from_on": "2020-10-17", "to_by": "2023-10-14", "ended_on": None, "document": D["g"], "page": 5}],
        "pub.party_expenses": [{"party": A, "year": 2023, "total_expenses": 1000.0, "allocation": 500.0, "allocation_spent": 400.0}],
        "pub.party_expense_returns": [],
        "pub.broadcasting_allocations": [{"party": A, "year": 2023, "round": 2, "final": True, "eligible": True, "amount": 500},
                                         {"party": A, "year": 2023, "round": 1, "final": False, "eligible": True, "amount": 450}],
        "pub.promoters": [{"key": "pr-2023-1", "document": D["g"], "page": 9, "place": "row 1", "year": 2023, "promoter": "Vote Loud Limited", "registered_on": "2023-08-01",
                           "registered_for": "2023 General Election", "statement": None, "read_from": "text"}],
        "pub.promoter_expenses": [{"key": "pe-2023-1", "document": D["g"], "page": 10, "place": "row 1", "year": 2023, "promoter": "Vote Loud Limited", "note": None,
                                   "election_expenses": 300000.0, "cannabis_referendum_expenses": None, "end_of_life_referendum_expenses": None, "printed": "300,000.00",
                                   "return_document": D["h"], "read_from": "text", "election_return": 300000.0, "election_agrees": True,
                                   "cannabis_referendum_return": None, "cannabis_referendum_agrees": None, "end_of_life_referendum_return": None, "end_of_life_referendum_agrees": None},
                                  {"key": "pe-2020-1", "document": D["g"], "page": 10, "place": "row 2", "year": 2020, "promoter": "Yes Please Trust", "note": None,
                                   "election_expenses": 0.0, "cannabis_referendum_expenses": 50000.0, "end_of_life_referendum_expenses": 25000.0, "printed": "0",
                                   "return_document": None, "read_from": "text", "election_return": None, "election_agrees": None,
                                   "cannabis_referendum_return": None, "cannabis_referendum_agrees": None, "end_of_life_referendum_return": None, "end_of_life_referendum_agrees": None}],
        "pub.promoter_people": [{"key": "pp-1", "promoter_key": "pr-2023-1", "document": D["g"], "page": 9, "place": "row 1", "year": 2023, "promoter": "Vote Loud Limited",
                                 "role": "authorised representative", "name": "Loud Person", "read_from": "text"}],
        "pub.party_financial_statements": [
            {"key": "fs-list/2025/row/1", "document": D["g"], "page": 1, "place": "row 1", "filed_year": 2025, "party": A, "party_label": "ACT New Zealand",
             "party_basis": "exact", "note": None, "mark": None, "balance_date": "2024-12-31", "deadline": "2025-06-30", "date_filed": "2025-06-27",
             "audit_requirement": "No audit required", "statements": [D["h"]], "read_from": "text"},
            {"key": "fs-list/2026/row/1", "document": D["g"], "page": 1, "place": "row 2", "filed_year": 2026, "party": A, "party_label": "ACT New Zealand",
             "party_basis": "exact", "note": None, "mark": None, "balance_date": None, "deadline": None, "date_filed": None,
             "audit_requirement": "No audit required", "statements": [], "read_from": "text"},
            {"key": "fs-list/2016/row/1", "document": D["g"], "page": 1, "place": "row 3", "filed_year": 2016, "party": A, "party_label": "ACT New Zealand",
             "party_basis": "exact", "note": None, "mark": None, "balance_date": "2015-12-31", "deadline": None, "date_filed": None,
             "audit_requirement": "No audit required", "statements": [D["h"]], "read_from": "text"}],
        "pub.party_statement_figures": [
            {"key": D["h"] + "/income", "document": D["h"], "page": 3, "place": "col 2", "roster_row": "fs-list/2025/row/1", "filed_year": 2025, "balance_date": "2024-12-31",
             "party": A, "party_label": "ACT", "party_basis": "exact", "current": True, "figure": "income", "amount": 1565672.0, "prior_amount": 4554215.0, "scale": 1,
             "figure_check": "income-less-expenditure", "printed": "1,565,672", "read_from": "text"},
            {"key": D["h"] + "/expenditure", "document": D["h"], "page": 3, "place": "col 2", "roster_row": "fs-list/2025/row/1", "filed_year": 2025, "balance_date": "2024-12-31",
             "party": A, "party_label": "ACT", "party_basis": "exact", "current": True, "figure": "expenditure", "amount": 1500000.0, "prior_amount": None, "scale": 1,
             "figure_check": "income-less-expenditure", "printed": "1,500,000", "read_from": "text"},
            {"key": D["h"] + "/income/old", "document": D["h"], "page": 3, "place": "col 2", "roster_row": "fs-list/2025/row/1", "filed_year": 2025, "balance_date": "2024-12-31",
             "party": A, "party_label": "ACT", "party_basis": "exact", "current": False, "figure": "income", "amount": 99.0, "prior_amount": None, "scale": 1,
             "figure_check": "superseded", "printed": "99", "read_from": "text"}],
        "pub.mp_interest_returns": [
            {"key": D["h"] + "/p9/l1", "document": D["h"], "page": 9, "place": "l1", "as_at": "2026-01-31", "printed": "SEYMOUR, David (ACT, Epsom)", "member": "Hon David Seymour",
             "name": "David Seymour", "party_label": "ACT", "party": A, "party_basis": "exact", "electorate": "Epsom", "statement": None, "declarations": 3, "read_from": "text"},
            {"key": D["h"] + "/p9/l9", "document": D["h"], "page": 9, "place": "l9", "as_at": "2025-01-31", "printed": "SEYMOUR, David (ACT, Epsom)", "member": "Hon David Seymour",
             "name": "David Seymour", "party_label": "ACT", "party": A, "party_basis": "exact", "electorate": "Epsom", "statement": None, "declarations": 2, "read_from": "text"},
            {"key": D["h"] + "/p1/l1", "document": D["h"], "page": 1, "place": "l1", "as_at": "2016-01-31", "printed": "SEYMOUR, David (ACT, Epsom)", "member": "David Seymour",
             "name": "David Seymour", "party_label": "ACT", "party": A, "party_basis": "exact", "electorate": "Epsom", "statement": None, "declarations": 1, "read_from": "text"}],
        "pub.mp_interests": [
            {"key": D["h"] + "/p9/l2", "document": D["h"], "page": 9, "place": "l2", "as_at": "2026-01-31", "member": "Hon David Seymour", "name": "David Seymour", "party_label": "ACT",
             "party": A, "party_basis": "exact", "electorate": "Epsom", "category": "directorships", "heading": "Company directorships and controlling interests", "number_printed": 1,
             "text": "Seymour Holdings Limited – property", "withheld": False, "member_return": D["h"] + "/p9/l1", "read_from": "text"},
            {"key": D["h"] + "/p9/l10", "document": D["h"], "page": 9, "place": "l10", "as_at": "2025-01-31", "member": "Hon David Seymour", "name": "David Seymour", "party_label": "ACT",
             "party": A, "party_basis": "exact", "electorate": "Epsom", "category": "directorships", "heading": "Company directorships and controlling interests", "number_printed": 1,
             "text": "Seymour Holdings Limited – property", "withheld": False, "member_return": D["h"] + "/p9/l9", "read_from": "text"},
            {"key": D["h"] + "/p9/l3", "document": D["h"], "page": 9, "place": "l3", "as_at": "2026-01-31", "member": "Hon David Seymour", "name": "David Seymour", "party_label": "ACT",
             "party": A, "party_basis": "exact", "electorate": "Epsom", "category": "real-property", "heading": "Real property", "number_printed": 6,
             "text": "", "withheld": True, "member_return": D["h"] + "/p9/l1", "read_from": "text"},
            {"key": D["h"] + "/p9/l4", "document": D["h"], "page": 9, "place": "l4", "as_at": "2026-01-31", "member": "Hon David Seymour", "name": "David Seymour", "party_label": "ACT",
             "party": A, "party_basis": "exact", "electorate": "Epsom", "category": "gifts", "heading": "Gifts", "number_printed": 9,
             "text": "Tickets to a rugby game – a union", "withheld": False, "member_return": D["h"] + "/p9/l1", "read_from": "text"},
            {"key": D["h"] + "/p1/l2", "document": D["h"], "page": 1, "place": "l2", "as_at": "2016-01-31", "member": "David Seymour", "name": "David Seymour", "party_label": "ACT",
             "party": A, "party_basis": "exact", "electorate": "Epsom", "category": "gifts", "heading": "Gifts", "number_printed": 9,
             "text": "A pen", "withheld": False, "member_return": D["h"] + "/p1/l1", "read_from": "text"}],
        "pub.names": [
            {"ref": "mp_interests:" + D["h"] + "/p9/l1", "register": "mp_interests", "view": "mp_interest_returns", "key": D["h"] + "/p9/l1", "name_filed": "David Seymour", "kind": "person", "name_key": "david seymour", "politician": True},
            {"ref": "mp_interests:" + D["h"] + "/p9/l9", "register": "mp_interests", "view": "mp_interest_returns", "key": D["h"] + "/p9/l9", "name_filed": "David Seymour", "kind": "person", "name_key": "david seymour", "politician": True},
            {"ref": "mp_interests:" + D["h"] + "/p1/l1", "register": "mp_interests", "view": "mp_interest_returns", "key": D["h"] + "/p1/l1", "name_filed": "David Seymour", "kind": "person", "name_key": "david seymour", "politician": True},
            {"ref": "party_returns:r1/A/1", "register": "party_returns", "view": "party_return_donors", "key": "r1/A/1", "name_filed": "Jane Q Donor", "kind": "person", "name_key": "donor jane q"},
            {"ref": "party_returns:r1/A/2", "register": "party_returns", "view": "party_return_donors", "key": "r1/A/2", "name_filed": "Jane Q. Donor", "kind": "person", "name_key": "donor jane q"},
            {"ref": "party_returns:r2/A/1", "register": "party_returns", "view": "party_return_donors", "key": "r2/A/1", "name_filed": "Big Co Limited", "kind": "organisation", "name_key": "big co"},
            {"ref": "disclosures:d1", "register": "disclosures", "view": "disclosures", "key": "d1", "name_filed": "Big Co Limited", "kind": "organisation", "name_key": "big co"},
            {"ref": "disclosures:d2", "register": "disclosures", "view": "disclosures", "key": "d2", "name_filed": "Open Year Giver", "kind": "person", "name_key": "giver open year"},
            {"ref": "party_returns:r3/A/1", "register": "party_returns", "view": "party_return_donors", "key": "r3/A/1", "name_filed": "Twice Counted", "kind": "person", "name_key": "counted twice"},
            {"ref": "party_returns:r4/A/1", "register": "party_returns", "view": "party_return_donors", "key": "r4/A/1", "name_filed": "Twice Counted", "kind": "person", "name_key": "counted twice"}],
        "pub.groups": [], "pub.decisions": [],
    }


class FakeTables:
    """Stands in for read.Tables: the same get() and refusal, no database."""

    def __init__(self, template, conn=None, window_from=2017, data=None):
        self.template = template
        self.allowed = {r.table for r in template.reads}
        self._cache = {}
        self.counts = {}
        self.data = data or tables()
        self.window_from = int(window_from)

    def get(self, view):
        if view not in self.allowed:
            raise PermissionError(view)
        if view not in self._cache:
            self._cache[view] = list(self.data.get(view, []))
            self.counts[view] = len(self._cache[view])
        return self._cache[view]

    def has_view(self, view):
        return view in self.data


#: what the Commission's table says for the fixture rows (the gate reads it again by SQL)
COMMISSION_TABLE = [("ACT New Zealand", 2023, 40000.0, 1), ("ACT New Zealand", 2026, 25000.0, 1)]
#: what the party-finance lane's tables say, re-counted by SQL: party key, statements in the window, income
STATEMENTS_TABLE = [(A, 2, 1565672.0)]
#: the Commission's candidate table re-summed by SQL: year, electorate, declared (the Commission's figure where it has one), returns
CANDIDATE_TABLE = [(2023, "Epsom", 1277.0, 3), (2018, "Epsom", 9.0, 1)]


class NoConn:
    """A connection that answers the few SQL statements the gates run, by their table name, and nothing else."""

    def __init__(self, answers=None):
        self.answers = answers or {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        for table, rows in self.answers.items():
            if table in sql:
                return iter(rows)
        if "party_financial_statements" in sql:
            return iter(STATEMENTS_TABLE)
        if "candidate_return_totals" in sql:
            return iter(CANDIDATE_TABLE)
        return iter(COMMISSION_TABLE)
