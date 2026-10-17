"""The one party-name function, with the old cases: exact, variant, core,
the pixel-read garbles, abstention on junk, amendment markers, renames, and
the two labels the old functions disagreed on."""
import pytest

from keys import parties as p


def r(label):
    return p.party_name(label)


def test_exact_variant_core():
    assert r("The New Zealand National Party") == ("The New Zealand National Party", "exact")
    assert r("National Party") == ("The New Zealand National Party", "variant")
    assert r("New Zealand National") == ("The New Zealand National Party", "variant")
    assert r("NEW ZEALAND NATIONAL PARTY") == ("The New Zealand National Party", "exact")
    assert r("Green Party of Aotearoa New Zealand")[0] == "The Green Party of Aotearoa New Zealand"
    assert r("Greens, The Green Party of Aotearoa NZ") == ("The Green Party of Aotearoa New Zealand", "variant")
    assert r("Labour") == ("New Zealand Labour Party", "variant")
    assert r("New Zealand First")[0] == "New Zealand First Party"
    assert r("NZ First")[0] == "New Zealand First Party"
    assert r("The N.Z. National Party") == ("The New Zealand National Party", "core")


def test_a_renamed_party_is_the_same_party():
    for old in ("Maori Party", "Te Pati Maori", "Te Pāti Māori", "TE PATI MAORI"):
        assert r(old)[0] == "Te Pāti Māori", old
    assert r("Opportunities Party")[0] == "Opportunity Party"
    assert r("TOP")[0] == "Opportunity Party"
    assert r("Conservative")[0] == "Conservative Party NZ"


def test_the_pixel_read_garbles_resolve_and_say_so():
    for garble in ("NEO ZEALAND NATIONAL PARTY", "New Zealand National Pati", "New Zealand National Paty"):
        name, basis = r(garble)
        assert name == "The New Zealand National Party", (garble, name, basis)
        assert basis.startswith("fuzzy:") or basis == "core", (garble, basis)


def test_abstains_on_junk_persons_and_doubtful_garbles():
    for label in ("", "Hon Pete Hodgson", "A'Z UUxxiv /)ai/^-vi", "Wew 2Eacanoe Fest 7", "Te Kaitiaki Take Tawhenua",
                  "New Zealand Alatorel Party"):
        assert r(label)[0] is None, label


@pytest.mark.parametrize("label,party", [
    ("Amended Maori Party", "Te Pāti Māori"),
    ("Amended Te Pati Maori", "Te Pāti Māori"),
    ("Amended NZ First", "New Zealand First Party"),
    ("Labour Party amended", "New Zealand Labour Party"),
])
def test_an_amendment_marker_names_the_filing_not_the_party(label, party):
    assert r(label)[0] == party


@pytest.mark.parametrize("label", [
    "Amended DemocracyNZ EC Party", "Amended Heartland NZ", "NZNP Amended",
    "New Conservatives 2024 amended May 2025", "ONE Party amended",
])
def test_the_five_that_do_not_resolve_stay_none(label):
    assert r(label)[0] is None, label


def test_the_fuzzy_arm_never_joins_two_parties():
    assert r("New Labour Party")[0] is None          # the old fuzzy rule folded it into Labour
    assert r("Labour Party")[0] == "New Zealand Labour Party"
    assert r("Northland")[0] is None


def test_without_amendment():
    assert p.without_amendment("New Conservatives 2024 amended May 2025") == "New Conservatives"
    assert p.without_amendment("Amended NZ First") == "NZ First"


def test_a_caller_may_pass_its_own_register():
    reg = (("Example Party", "EP"),)
    assert p.party_name("example party", reg) == ("Example Party", "exact")
    assert p.party_name("National Party", reg)[0] is None
