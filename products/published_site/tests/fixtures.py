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
        "pub.elections": [], "pub.electorates": [], "pub.candidates": [],
        "pub.members": [
            {"key": "m1", "election": "ge-2023", "party": "ACT", "party_registered": "ACT New Zealand", "route": "list", "to_by": None, "ended_on": None},
            {"key": "m2", "election": "ge-2023", "party": "ACT", "party_registered": "ACT New Zealand", "route": "electorate", "to_by": None, "ended_on": None},
            {"key": "m3", "election": "ge-2020", "party": "ACT", "party_registered": "ACT New Zealand", "route": "list", "to_by": "2023-10-14", "ended_on": None}],
        "pub.party_expenses": [{"party": A, "year": 2023, "total_expenses": 1000.0, "allocation": 500.0, "allocation_spent": 400.0}],
        "pub.party_expense_returns": [],
        "pub.broadcasting_allocations": [{"party": A, "year": 2023, "round": 2, "final": True, "eligible": True, "amount": 500},
                                         {"party": A, "year": 2023, "round": 1, "final": False, "eligible": True, "amount": 450}],
        "pub.promoters": [], "pub.promoter_expenses": [], "pub.promoter_people": [],
        "pub.party_financial_statements": [], "pub.party_statement_figures": [],
        "pub.names": [
            {"ref": "party_returns:r1/A/1", "register": "party_returns", "view": "party_return_donors", "key": "r1/A/1", "kind": "person", "name_key": "donor jane q"},
            {"ref": "party_returns:r1/A/2", "register": "party_returns", "view": "party_return_donors", "key": "r1/A/2", "kind": "person", "name_key": "donor jane q"},
            {"ref": "party_returns:r2/A/1", "register": "party_returns", "view": "party_return_donors", "key": "r2/A/1", "kind": "organisation", "name_key": "big co"},
            {"ref": "disclosures:d1", "register": "disclosures", "view": "disclosures", "key": "d1", "kind": "organisation", "name_key": "big co"},
            {"ref": "disclosures:d2", "register": "disclosures", "view": "disclosures", "key": "d2", "kind": "person", "name_key": "giver open year"},
            {"ref": "party_returns:r3/A/1", "register": "party_returns", "view": "party_return_donors", "key": "r3/A/1", "kind": "person", "name_key": "counted twice"},
            {"ref": "party_returns:r4/A/1", "register": "party_returns", "view": "party_return_donors", "key": "r4/A/1", "kind": "person", "name_key": "counted twice"}],
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


class NoConn:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
