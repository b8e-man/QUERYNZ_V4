"""The path rule is the frozen site's: names from its 2026-10-20T0620 folder land on the same files."""
import pytest

from products.published_site import paths


def test_frozen_names_land_on_the_frozen_files():
    assert paths.path("home") == "data/home.json"
    assert paths.path("subject", "party", "ACT New Zealand") == "data/subject/party/act-new-zealand-7b1ffcdc.json"
    assert paths.path("size-bands", "ACT New Zealand") == "data/size-bands/act-new-zealand-7b1ffcdc.json"
    assert paths.path("electorate", "Auckland Central") == "data/electorate/auckland-central-bb8433b1.json"
    assert paths.path("electorates", "2017") == "data/electorates/2017-cf2c5d47.json"
    assert paths.path("electorates", "all") == "data/electorates/all-13254bc4.json"
    assert paths.path("subject", "person", "Aaron Stallard") == "data/subject/person/aaron-stallard-066cb445.json"
    assert paths.path("cite", "cdon:461330") == "data/cite/cdon-461330-9cfa84d2.json"


def test_macrons_are_hashed_and_slugged_apart():
    a, b = paths.path("subject", "party", "Te Pāti Māori"), paths.path("subject", "party", "Te Pati Maori")
    assert a != b and a.startswith("data/subject/party/te-pati-maori-") and b.startswith("data/subject/party/te-pati-maori-")


def test_only_the_ten_kinds_have_a_path():
    with pytest.raises(KeyError):
        paths.path("review", "x")
    assert paths.kind_of("data/home.json") == "home"
    assert paths.kind_of("data/subject/party/act-new-zealand-7b1ffcdc.json") == "subject"
    assert paths.kind_of("data/search-index.json") == "" and paths.kind_of("SNAPSHOT.json") == ""
    assert set(paths.KINDS) == {"home", "parties", "electorates", "pickers", "subject", "electorate", "donor",
                                "board-member", "size-bands", "cite"}
