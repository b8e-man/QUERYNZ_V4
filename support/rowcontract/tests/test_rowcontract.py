"""Every published row cites its document, page and place, names its reader
and profile, says whether it read text or pixels, carries no home address,
and dates an ending to the file, never the load day."""
import datetime as dt

import support.rowcontract as rc

GOOD = {"key": "ec:ab12/p3/r7", "document": "a" * 64, "page": 3, "place": "row 7", "reader": "docread 1",
        "profile": "ec-party-return-text", "profile_version": 3, "read_from": "text",
        "loaded_at": "2026-10-18T02:00:00+13:00", "filed": {"received_on": "2023-05-16", "amount": 5000}}


def test_a_good_row_passes():
    assert rc.validate(dict(GOOD), dt.date(2026, 10, 18)) == []


def test_missing_and_malformed_fields_are_named():
    bad = dict(GOOD)
    del bad["place"]
    assert rc.validate(bad) == ["missing place"]
    bad = dict(GOOD, document="not-a-hash", page=0, read_from="guess", profile_version=0)
    probs = rc.validate(bad)
    assert any("sha256" in p for p in probs) and any("page" in p for p in probs)
    assert any("read_from" in p for p in probs) and any("profile_version" in p for p in probs)


def test_no_home_address_on_a_published_row():
    probs = rc.validate(dict(GOOD, address="12 Example Street"))
    assert probs == ["a published row must not carry address (hard limit 15)"]
    assert rc.validate(dict(GOOD, private_ref="companies_private:1234")) == []


def test_an_ending_dated_to_the_load_day_is_refused_unless_stated():
    row = dict(GOOD, filed={"ended_on": "2026-10-18"})
    assert rc.validate(row, dt.date(2026, 10, 18)) == [
        "ended_on equals the load day and the document does not state it (contract: dates)"]
    row = dict(GOOD, filed={"ended_on": "2026-10-18", "ended_on_stated": True})
    assert rc.validate(row, dt.date(2026, 10, 18)) == []
    row = dict(GOOD, filed={"ended_on": "yesterday"})
    assert rc.validate(row) == ["filed.ended_on is not an ISO date: 'yesterday'"]
