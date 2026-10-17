"""The one reading of names, with the old estate's cases carried: macrons
kept and decomposed, never deleted; honorifics off; the inversion turned
round; a bare 2–3 word name order-free; nicknames and initials never fold;
person against organisation by shape and the director register's given
names; a joint filed name flagged or left unexamined."""
import pytest

from keys import names as n


def test_diacritics_are_decomposed_not_deleted():
    assert n.fold_diacritics("Te Pāti Māori") == "Te Pati Maori"
    assert n.fold_diacritics("Chlöe Swarbrick") == "Chloe Swarbrick"
    assert n.fold_diacritics("Ricardo Menéndez March") == "Ricardo Menendez March"
    assert n.fold_diacritics("Rāwiri") == "Rawiri"
    assert n.person_key("Rāwiri Waititi") == n.person_key("Rawiri Waititi") == "rawiri waititi"
    assert n.person_name("Rāwiri Waititi").given == "Rāwiri"      # display keeps the macron


def test_honorifics_and_post_nominals_come_off():
    assert n.strip_honorifics("Rt Hon Dr Winston Peters") == "Winston Peters"
    assert n.strip_honorifics("Hon Judith Collins, KC") == "Judith Collins"
    assert n.strip_honorifics("Dr. Shane Reti MP") == "Shane Reti"
    assert n.person_name("Hon. Simon Bridges, MP").full == "Simon Bridges"


def test_the_inversion_and_the_trailing_comma():
    p = n.person_name("Cartmell, Brian")
    assert (p.given, p.family, p.inverted) == ("Brian", "Cartmell", True)
    assert n.person_name("Oliver Bruce,").full == "Oliver Bruce"
    assert n.person_key("Cartmell, Brian") == n.person_key("Brian Cartmell") == "brian cartmell"
    assert n.person_key("MILLS PHILLIP") == n.person_key("Phillip Mills")
    assert n.person_name("Phillip John Mills").middle == "John"
    assert n.person_name("Madonna").family == "Madonna"


def test_nicknames_initials_and_spellings_never_fold():
    assert n.person_key("Bill English") != n.person_key("William English")
    assert n.person_key("J. A. Smith") != n.person_key("John Adam Smith")
    assert n.person_key("Jon Smith") != n.person_key("John Smith")
    assert n.person_key("Talley's") == n.person_key("Talleys")   # an apostrophe is not a spelling


def test_organisation_key_folds_the_corporate_shell_and_not_the_party_word():
    k = n.organisation_key
    assert k("Talley's Group Limited") == k("Talleys Group Ltd") == "talleys group"
    assert k("The NZ National Party") == "new zealand national party"
    assert k("Northland") != k("Northland Party")
    assert k("Shorts Transport Ltd.") == "shorts transport"
    assert k("Hauraki Chambers (Inc)") == "hauraki chambers"


def test_person_against_organisation_by_shape_and_given_name():
    assert n.is_organisation("Toorak Chambers") is True
    assert n.is_organisation("Richard Chambers") is False
    assert n.is_organisation("Chambers Limited") is True
    assert n.is_organisation("Canterbury Nationalist Trust") is True
    assert n.is_organisation("NZLP Dunedin South Branch") is True
    assert n.is_organisation("John Key") is False
    assert n.is_organisation("Bell Gully Trust Account") is True
    g = n.given_names()
    assert len(g) > 5000
    for name in ("richard", "diane", "hine", "whetu", "aroha", "wiremu"):
        assert name in g, name
    for name in ("toorak", "tees", "canterbury", "trust", "limited"):
        assert name not in g, name


def test_name_kind_estate_party_then_the_rest():
    party_keys = {n.organisation_key("The New Zealand National Party")}
    assert n.name_kind("Estate of Richard Chambers") == "estate"
    assert n.name_kind("The New Zealand National Party", party_keys) == "party"
    assert n.name_kind("MA Capital Ltd via Ross George") == "organisation"
    assert n.name_kind("Richard Chambers") == "person"
    assert n.split_via("MA Capital Ltd via Ross George") == ("MA Capital Ltd", "Ross George")


@pytest.mark.parametrize("name", [
    "Laurence & Katrina Day", "Brendan & Jocelyn Lindsay", "Jim and Noelene Glass",
    "Keith & Joanne Thompson", "Edward & Catherine Goldsmith", "Willard & Lindy Cheung",
    "Dirk and Janet De Lu", "Sophie and Frieder Guy", "Mr & Mrs McCabe", "Dr & Mrs GMO Becroft",
    "Wares, Robert John & Irina", "Meehan, Christopher & Michaela", "Mills, Phillip & Jackie",
    "Smale, Greg & Felicity", "McBride, Murray & Necia",
])
def test_joint_people_are_flagged(name):
    assert n.is_joint_name(name) is True, name


@pytest.mark.parametrize("name", [
    "Christopher & Banks Limited", "Christopher & Banks Ltd", "Christopher & Banks Ltd via Peter Huljich",
    "MH&K Ltd, Waitemata Trust", "RAIL & MARITIME TRANSPORT UNION", "Rail & Maritime Transport Union",
    "Service & Food Workers Union", "John Key", "Rank Group Limited", "Talley's Group Ltd",
])
def test_one_donor_is_not_flagged(name):
    assert n.is_joint_name(name) is False, name


@pytest.mark.parametrize("name", [
    "Christopher & Banks", "M & J Ruka", "G & J Barfoot", "Mr L & Mrs D Coombes",
    "Mr Y S & Mrs C C C Lay", "Drury & Alo, Rod & Rebecca",
])
def test_an_unjudgeable_shape_abstains(name):
    assert n.is_joint_name(name) is None, name
