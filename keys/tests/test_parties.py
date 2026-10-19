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


# the parties lane's rows (pub.party_names joined to pub.parties), in small
ROWS = [
    {"party": "ec-party/2023-08-28/1daf", "name": "New Zealand Loyal", "kind": "name",
     "from_on": "2023-08-28", "to_on": "2024-07-26", "registered_on": "2023-08-28", "cancelled_on": "2024-07-26"},
    {"party": "ec-party/2026-08-05/1daf", "name": "New Zealand Loyal", "kind": "name",
     "from_on": "2026-08-05", "to_on": None, "registered_on": "2026-08-05", "cancelled_on": None},
    {"party": "ec-party/2026-08-05/1daf", "name": "NZ Loyal", "kind": "abbreviation",
     "from_on": "2026-08-05", "to_on": None, "registered_on": "2026-08-05", "cancelled_on": None},
    {"party": "ec-party/2004-07-09/2565", "name": "Maori Party", "kind": "name", "from_on": "2004-07-09",
     "to_on": "2023-07-12", "registered_on": "2004-06-24", "cancelled_on": None},
    {"party": "ec-party/2004-07-09/2565", "name": "Te Pāti Māori", "kind": "name", "from_on": "2023-07-12",
     "to_on": None, "registered_on": "2004-06-24", "cancelled_on": None},
    {"party": "ec-party/2020-07-09/cb4e", "name": "ONE Party", "kind": "name", "from_on": "2020-07-09",
     "to_on": "2022-11-01", "registered_on": "2020-07-09", "cancelled_on": "2026-03-30"},
    {"party": "ec-party/2020-07-09/cb4e", "name": "NewZeal", "kind": "name", "from_on": "2022-11-01",
     "to_on": "2026-03-30", "registered_on": "2020-07-09", "cancelled_on": "2026-03-30"},
    {"party": "ec-party/1995-02-17/2027", "name": "New Zealand Labour Party", "kind": "name",
     "from_on": "1995-02-17", "to_on": None, "registered_on": "1995-02-17", "cancelled_on": None},
    {"party": "ec-party/1994-12-02/af36", "name": "The New Zealand National Party", "kind": "name",
     "from_on": "1994-12-02", "to_on": None, "registered_on": "1994-12-02", "cancelled_on": None},
]


def test_the_lane_s_name_key():
    assert p.name_key("The Kiwi Party") == p.name_key("Kiwi Party") == "kiwi"
    assert p.name_key("New Conservative") != p.name_key("Conservative Party NZ")


def test_a_label_resolves_to_the_registration_live_on_the_day():
    assert p.party_name("New Zealand Loyal", ROWS, on="2024-03-01") == ("ec-party/2023-08-28/1daf", "exact")
    assert p.party_name("NZ Loyal", ROWS, on="2026-09-01")[0] == "ec-party/2026-08-05/1daf"
    assert p.party_name("New Zealand Loyal", ROWS, on=2026)[0] == "ec-party/2026-08-05/1daf"
    assert p.party_name("New Zealand Loyal", ROWS, on="2025-06-01") == (None, "unresolved")


def test_two_live_registrations_are_never_guessed_between():
    assert p.party_name("New Zealand Loyal", ROWS) == (None, "unresolved")


def test_every_name_a_registration_carried_is_the_party():
    assert p.party_name("ONE PARTY amended", ROWS, on=2021)[0] == "ec-party/2020-07-09/cb4e"
    assert p.party_name("NewZeal", ROWS, on=2024)[0] == "ec-party/2020-07-09/cb4e"
    assert p.party_name("Maori Party", ROWS, on=2019)[0] == "ec-party/2004-07-09/2565"
    assert p.party_name("Te Pati Maori", ROWS, on=2025)[0] == "ec-party/2004-07-09/2565"


def test_the_rules_hold_against_the_lane_s_rows():
    assert p.party_name("Labour", ROWS, on=2023) == ("ec-party/1995-02-17/2027", "variant")
    assert p.party_name("The N.Z. National Party", ROWS, on=2023) == ("ec-party/1994-12-02/af36", "core")
    name, basis = p.party_name("NEO ZEALAND NATIONAL PARTY", ROWS, on=2023)
    assert name == "ec-party/1994-12-02/af36" and basis.startswith("fuzzy:")
    for label in ("New Labour Party", "NZNP Amended", "Hon Pete Hodgson", "Northland"):
        assert p.party_name(label, ROWS, on=2023)[0] is None, label


def test_windows_from_the_names_alone():
    rows = [{k: v for k, v in r.items() if k not in ("registered_on", "cancelled_on")} for r in ROWS]
    w = p.windows(rows)
    assert w["ec-party/2023-08-28/1daf"] == ("2023-08-28", "2024-07-26")
    assert w["ec-party/2004-07-09/2565"] == ("2004-07-09", None)
    assert p.party_name("New Zealand Loyal", rows, on=2024)[0] == "ec-party/2023-08-28/1daf"
