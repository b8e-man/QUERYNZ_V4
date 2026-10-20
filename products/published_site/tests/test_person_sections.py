"""The person page's frozen sections (plan 4.4, tranche 4): list-only candidacies, the member's own interests register returns, and what stays not held."""
import json

from products.published_site import paths
from products.published_site.tests import fixtures as X
from products.published_site.tests.test_kinds import load, vdir   # noqa: F401


def test_list_only_candidacies_come_from_the_seats_and_the_published_list(vdir):
    k = load(vdir, paths.path("subject", "person", "Karen CHHOUR"))
    assert len(k["candidacies"]) == 1
    c = k["candidacies"][0]
    assert c["route"] == "list" and c["electorate"] is None and c["elected"] is True and c["year"] == 2023 and c["party"] == "ACT New Zealand"
    assert c["list_place"] is None and "party list itself is not held" in c["elected_basis"] and c["declared"]["held"] is False
    lena = load(vdir, paths.path("subject", "person", "Lena LIST"))
    assert lena["candidacies"][0]["list_place"] == 7 and lena["candidacies"][0]["elected"] is None and lena["candidacies"][0]["cite"]["document"] == X.D["h"]
    assert lena["sitting_mp"] is False and "interests" not in lena and lena["positions"] == []          # never a member: no return to hold
    gone = load(vdir, paths.path("subject", "person", "Pat GONE"))
    assert [c["year"] for c in gone["candidacies"]] == [2020] and gone["candidacies"][0]["route"] == "list"


def test_the_interests_register_attaches_under_the_shared_reading_and_withholds_property(vdir):
    p = load(vdir, paths.path("subject", "person", "David SEYMOUR"))
    reg = p["interests"]
    assert reg["editions"] == ["2026-01-31", "2025-01-31"] and reg["latest"] == "2026-01-31"          # 2016 is before the window
    assert reg["categories"] == {"directorships": 1, "gifts": 1, "real-property": 1}
    pos = p["positions"]
    assert len(pos) == 1 and pos[0]["text"] == "Seymour Holdings Limited – property" and pos[0]["editions"] == 2
    assert pos[0]["first_seen"] == "2025-01-31" and pos[0]["last_seen"] == "2026-01-31" and pos[0]["cite"]["page"] == 9 and pos[0]["cite"]["place"] == "l2"
    prop = p["properties"]
    assert len(prop) == 1 and prop[0]["withheld"] is True and prop[0]["text"] is None and "withheld" in p["basis"]["properties"]
    extra = p["interests_extra"]
    assert len(extra) == 1 and extra[0]["category"] == "gifts" and extra[0]["rows"][0]["text"] == "Tickets to a rugby game – a union"
    assert p["interests_tree"]["held"] is False and p["public_expenses"]["held"] is False and p["exposure"]["held"] is False and p["industry_exposure"]["held"] is False and p["donations_received_not_shown"] == 0
    assert "A pen" not in json.dumps(p)                                                               # the 2016 edition is outside the window
