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
        assert v.start or v.on or v.year or v.period, f"{v.name} has no way to date or bound a connection"


def test_not_held_and_held_do_not_overlap():
    held = {r for r, _ in cat.REGISTERS}
    assert not held & {r for r, _ in cat.NOT_HELD}


def test_the_not_held_list_carries_the_health_and_property_keys_and_keeps_the_rest():
    """healthcare-1's five and property-1's three, each with the key the
    template cites; the keys report-3 added stay; charities is no longer
    among them (it is held)."""
    for key, word in (("retirement_villages", "statutory supervisor"), ("hdc", "Health and Disability Commissioner"), ("certification", "rest homes"),
                      ("health_providers", "Ministry of Health"), ("aged_care_commissioner", "Aged Care Commissioner"),
                      ("oio", "Overseas Investment Office"), ("building_consents", "code compliance"), ("rea", "Real Estate Authority")):
        assert key in cat.NOT_HELD_NAME and word in cat.NOT_HELD_NAME[key], key
    for key in ("courts", "insolvency", "securities", "linz", "fsp", "sanctions", "tenders", "limited_partnerships", "building_practitioners", "overseas",
                "trusts", "unincorporated", "company_history", "nzbn_interface", "credit_bureau", "worksafe", "regulators", "mpi", "fire", "employment",
                "disputes", "tribunals", "disciplinary"):
        assert key in cat.NOT_HELD_NAME, key
    assert "charities" not in cat.NOT_HELD_NAME and len(cat.NOT_HELD) == len(set(k for k, _ in cat.NOT_HELD))


def test_the_spec_carries_its_five_lines():
    spec = open(os.path.join(HERE, "spec.md"), encoding="utf-8").read()
    for line in ("owns:", "reads:", "publishes:", "outside check:", "jobs:"):
        assert line in spec, line
    assert "local network only" in spec and "never shown as cause" in spec
