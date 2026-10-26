"""The check's address-shaped rule and ruling 102's flags."""
from products.board import catalogue as cat, check


def test_a_declared_boolean_flag_is_not_an_address_column():
    v = cat.BY_NAME["minister_diary_entries"]
    flags = {flag for _, flag, _ in v.flags}
    assert "location_street_only" in flags
    assert not check.address_shaped(v, "location_street_only", "boolean")


def test_the_same_name_as_text_or_undeclared_is_still_an_address_column():
    v = cat.BY_NAME["minister_diary_entries"]
    assert check.address_shaped(v, "location_street_only", "text")
    assert check.address_shaped(v, "home_address", "boolean")
    assert check.address_shaped(cat.BY_NAME["members"], "street", "text")


def test_the_registered_office_view_is_the_exception():
    assert not check.address_shaped(cat.BY_NAME["company_addresses"], "street", "text")
