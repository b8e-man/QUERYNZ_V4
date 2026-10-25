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
    "charities", "charity_officers", "charity_returns",   # charities-3 (21 October), catalogued at the construction-2 merge
    "company_lookups", "company_lookup_roles", "company_lookup_holdings", "company_changes",   # companies-2 (21 October)
    "party_board_roles", "party_board_pages",   # party-boards-1 (21 October), catalogued at the next merge
    "overseas_investment_decisions", "overseas_investment_parties",   # oio-1 (21 October), catalogued at the next merge
    "grant_publishers", "grants", "grant_recipients",   # grants-1 (21 October), catalogued at the next merge
    "commerce_commission_cases", "commerce_commission_parties", "fma_actions", "fma_parties", "worksafe_actions", "worksafe_parties",   # regulators-1 (21 October), catalogued at the next merge
    "award_notices", "award_suppliers",   # tenders-1 (21 October), catalogued at the next merge
    "iwi_directory_entities", "iwi_directory_relations", "iwi_directory_settlements",   # settlements-1 (22 October), catalogued at the procurement-1 merge
    "agency_contract_costs",   # procurement-1 (22 October), catalogued at its own merge: the view already stood on the live database
    "council_meetings", "councillor_interest_registers", "councillor_interests",   # councils-1 (23 October), catalogued at the local-elections-1 merge
    "local_election_returns", "local_election_returns_coverage",   # local-elections-1 (23 October), catalogued at the fetchgate fix merge after it
    "sanctions_lists", "sanctions_listings",   # sanctions-1 (21 October), catalogued once published
    "limited_partnerships", "limited_partnership_partners", "building_practitioner_decisions", "building_practitioners",   # sanctions-1 (21 October)
    "court_judgments", "court_judgment_parties",   # courts-1 (21 October), catalogued at the next merge
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
    registered office, in its own view, and a body-corporate charity's address for service (ruling 64)."""
    for v in cat.VIEWS:
        for c in cat.columns_shown(v):
            if v.name == "company_addresses":
                continue
            if v.name == "charities" and c == "address_for_service":   # a body corporate's, shown under ruling 64; a trust's is withheld by the view
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


def test_a_links_rule_reads_in_words_and_its_id_only_in_a_reference():
    """Ruling 84: name-only@1 reads "same name, nothing else"; the id and
    version only as "(links rule name-only, version 1)"; an unknown id is
    named, never hidden. Every id is held to the live pub.links in test_real."""
    assert cat.rule_words("name-only@1") == "same name, nothing else"
    assert cat.rule_ref("name-only@1") == "(links rule name-only, version 1)"
    assert cat.rule_words("brand-new@3") == "links rule brand-new" and cat.rule_ref("brand-new") == "(links rule brand-new)"
    for rid, words in cat.RULE_WORDS.items():
        assert words and "@" not in words and rid not in words, rid
    assert {"full-name", "name-and-address", "name-only", "company-name", "seat-and-window", "official-number",
            "organisation-name", "declared-directorship", "candidate-name-form", "filed-name", "source-identifier",
            "member-and-party-donor"} <= set(cat.RULE_WORDS)
