"""The catalogue names every published view once, every view has a register
the first pane lists, a title, something to search, and no address column of
a person; the registers not held are not also held."""
from products.board import catalogue as cat

PUBLISHED_AT_20_OCTOBER = {
    "societies", "society_officers", "society_states",   # societies-1, merged after the board (20 October)
    "promoter_expense_returns", "party_statement_figures",   # party-finance-2 (20 October)
    "gazette_company_notices", "gazette_practitioners", "gazette_bankruptcies", "gazette_appointments",   # gazette-3 (20 October)
    "party_labels",   # parties-2 (20 October)
    "gazette_possessions",   # gazette-5 (21 October)
    "company_lookups", "company_lookup_roles", "company_lookup_holdings", "company_changes",   # companies-2 (21 October)
    "candidate_return_totals", "candidate_return_donors",   # candidate-returns-1 (20 October)   # pub.* on 20 October 2026; the outside check compares with the live list
    "broadcasting_allocations", "candidates", "companies", "company_addresses", "company_states", "directors",
    "disclosure_items", "disclosures", "elections", "electorates", "gazette_celebrants", "gazette_liquidations",
    "gazette_liquidators", "gazette_notices", "gazette_prohibitions", "members", "minister_expenses", "mp_expenses",
    "mp_interest_editions", "mp_interest_returns", "mp_interests", "parties", "party_events", "party_expense_returns",
    "party_expenses", "party_financial_statements", "party_names", "party_return_donors", "party_return_loans",
    "party_return_totals", "promoter_expenses", "promoter_people", "promoters", "shareholders", "expense_release_totals"}


def test_every_published_view_is_in_the_catalogue_once():
    names = [v.name for v in cat.VIEWS]
    assert len(names) == len(set(names))
    assert set(names) == PUBLISHED_AT_20_OCTOBER


def test_every_view_has_a_register_a_title_and_a_search():
    registers = {r for r, _ in cat.REGISTERS}
    for v in cat.VIEWS:
        assert v.register in registers, v.name
        assert v.title and v.search, v.name
        assert v.kind in ("person", "organisation", "document", "event", "place", "figure"), v.name
        for j in v.joins:
            assert j.view in cat.BY_NAME, (v.name, j.view)
        if v.parent:
            assert v.parent[1] in cat.BY_NAME, (v.name, v.parent)


def test_not_held_registers_have_no_views():
    held = {v.register for v in cat.VIEWS}
    for register, _ in cat.NOT_HELD:
        assert register not in held, register


def test_no_pane_shows_a_person_s_address():
    """Hard limit 15: the only address columns the board shows are a company's
    registered office, in its own view."""
    for v in cat.VIEWS:
        for c in cat.columns_shown(v):
            if v.name == "company_addresses":
                continue
            assert not any(w in c for w in ("address", "street", "suburb", "residential")), (v.name, c)


def test_person_views_with_a_suppression_column_hide_their_names():
    for v in cat.VIEWS:
        if v.name in ("directors", "shareholders"):
            assert v.suppressed == "suppressed" and v.names
        if v.name == "gazette_prohibitions":
            assert v.hide_names == ("superseded_how", "^revoked")
        if v.name == "mp_interests":
            assert v.withheld == "withheld"


def test_fold_term_drops_macrons_and_case():
    assert cat.fold_term("  Tāmaki  Makaurau ") == "tamaki makaurau"
