"""The catalogue is sound: every view names its register, a title, and a way
to date a connection or declares it has none; the registers list and the
not-held list do not overlap; the spec carries its five lines."""
import os

from products.report import catalogue as cat

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_every_view_has_a_register_a_title_and_a_kind():
    registers = {r for r, _ in cat.REGISTERS}
    for v in cat.VIEWS:
        assert v.register in registers, v.name
        assert v.title and v.kind in ("person", "organisation", "figure", "event", "place", "document"), v.name
        assert cat.columns_read(v) >= set(v.title)


def test_a_role_view_dates_its_connection_or_falls_back_to_the_files():
    for v in cat.VIEWS:
        assert v.start or v.on or v.year or v.period or v.undated, f"{v.name} has no way to date or bound a connection"
    assert all(len(v.undated) > 30 for v in cat.VIEWS if v.undated)   # an undated view says why, in words


def test_not_held_and_held_do_not_overlap():
    held = {r for r, _ in cat.REGISTERS}
    assert not held & {r for r, _ in cat.NOT_HELD}


def test_the_not_held_list_carries_the_health_and_property_keys_and_keeps_the_rest():
    """healthcare-1's five and property-1's three, each with the key the
    template cites; the keys report-3 added stay; charities is no longer
    among them (it is held)."""
    assert "retirement_villages" not in cat.NOT_HELD_NAME and cat.SUPERSEDED_NOT_HELD["retirement_villages"] == "companies"   # read 2 November 2026
    for key in ("insolvency", "linz", "sanctions", "building_practitioners"):   # published; the old keys kept as superseded (9 November 2026)
        assert key not in cat.NOT_HELD_NAME and cat.SUPERSEDED_NOT_HELD[key] in dict(cat.REGISTERS), key
    for key, word in (("hdc", "Health and Disability Commissioner"), ("certification", "rest homes"),
                      ("health_providers", "Ministry of Health"), ("aged_care_commissioner", "Aged Care Commissioner"),
                      ("building_consents", "code compliance")):
        assert key in cat.NOT_HELD_NAME and word in cat.NOT_HELD_NAME[key], key
    for key in ("court_coverage", "securities", "fsp", "tender_coverage", "overseas",
                "trusts", "unincorporated", "company_history", "nzbn_interface", "credit_bureau", "mpi", "fire", "employment",
                "disputes", "tribunals", "disciplinary"):
        assert key in cat.NOT_HELD_NAME, key
    assert "building_practitioners" not in cat.NOT_HELD_NAME   # the licence register, published (9 November 2026)
    assert "charities" not in cat.NOT_HELD_NAME and len(cat.NOT_HELD) == len(set(k for k, _ in cat.NOT_HELD))
    # the Real Estate Authority's decisions are read since 2 November 2026: held, and the old key kept as superseded
    assert "rea" not in cat.NOT_HELD_NAME and cat.SUPERSEDED_NOT_HELD.get("rea") == "real_estate_authority" and "real_estate_authority" in dict(cat.REGISTERS)
    for v in ("rea_decisions", "rea_parties", "grants", "society_states", "councillor_interests"):
        assert v in cat.BY_NAME, v


def test_the_spec_carries_its_five_lines():
    spec = open(os.path.join(HERE, "spec.md"), encoding="utf-8").read()
    for line in ("owns:", "reads:", "publishes:", "outside check:", "jobs:"):
        assert line in spec, line
    assert "local network only" in spec and "never shown as cause" in spec


def test_every_published_table_is_read_or_left_out_with_a_reason():
    """The diagnostic report's inventory (9 November 2026): a table a lane defines is in the catalogue, the links
    lane's, or in NOT_READ with why; never both; and every catalogued table's register is in the register list."""
    import glob
    import os
    import re
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    defined = set()
    for f in glob.glob(os.path.join(root, "registers", "*", "publish.sql")) + [os.path.join(root, "links", "publish.sql")]:
        defined |= {v.lower() for v in re.findall(r"VIEW\s+pub\.([a-z_0-9]+)", open(f, encoding="utf-8").read(), re.I)}
    placed = set(cat.BY_NAME) | set(cat.LINKS_VIEWS) | set(cat.NOT_READ)
    assert not defined - placed, sorted(defined - placed)
    assert not set(cat.BY_NAME) & set(cat.NOT_READ)
    assert all(len(why) > 20 for why in cat.NOT_READ.values())
    assert {v.register for v in cat.VIEWS} <= {r for r, _ in cat.REGISTERS}



def test_a_text_date_the_registers_print_is_read_and_anything_else_is_left_as_printed():
    import datetime as dt
    from products.report import rows
    assert rows.as_date("16 February 2026") == dt.date(2026, 2, 16)
    assert rows.as_date("11/03/2025") == dt.date(2025, 3, 11)                 # day first, as New Zealand writes it
    assert rows.as_date("2026-02-16") == dt.date(2026, 2, 16)
    assert rows.as_date("31/02/2025") == "31/02/2025" and rows.as_date("about 2019") == "about 2019"
    v = cat.BY_NAME["councillor_interests"]
    assert rows.dates(v, {"as_at": "16 February 2026"})["on"] == dt.date(2026, 2, 16)


def test_an_annulled_bankruptcy_says_it_was_annulled_and_never_no_end_filed():
    """Finding 11 (9 November 2026): an annulment ends an estate as a discharge does; a search answer gives no date."""
    import datetime as dt
    from products.report import rows
    v = cat.BY_NAME["insolvency_people"]
    start = dt.date(2024, 5, 1)
    said = lambda r: rows.dates(v, {"adjudicated_on": start, **r})["text"]
    assert "annulled 3 June 2025" in said({"annulled_on": dt.date(2025, 6, 3), "status": "Annulled"})
    assert "annulled; the date is in the estate's detail, not yet read" in said({"status": "Annulled"})
    assert "no end filed" in said({"status": "Currently Bankrupt/NAP"})
    assert "no end filed" not in said({"status": "Annulled"})
