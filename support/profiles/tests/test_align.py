"""The lane and its profiles aligned (support/profiles/align.py): an invented lane, every problem made once."""
import pytest

import support.profiles as pr
from support.profiles import align


def _it(field, n, by, lands, private=False, kinds=None):
    return {"field": field, "iteration": n, "by": by, "ask": "read it", "private": private, "kinds": kinds,
            "lands": lands, "links": []}


TABLES = {"rulings": ("key", "citation", "outcome", "status", "document", "loaded_at"),
          "names": ("key", "name", "role", "document"),
          "toy_private.details": ("key", "kind", "value", "document")}
EXTRACT = [_it("citation", 1, "rules", ["rulings.citation"]), _it("outcome", 1, "rules", ["rulings.outcome"]),
           _it("people", 1, "model", ["names.name", "names.role"]),
           _it("details", 2, "pattern", ["toy_private.details.kind", "toy_private.details.value"], True, ["email", "phone"])]
PRODUCES = {"citation": ("rules", None), "outcome": ("rules", None), "people": ("model", None),
            "details": ("pattern", ("email", "phone"))}


def _lane(produces=PRODUCES, tables=TABLES):
    return align.Lane("toy", tables, {"toy-ruling": dict(produces)}, frozenset({"status"}))


def _profiles(extract=EXTRACT):
    return {"toy-ruling": {"slug": "toy-ruling", "version": 2, "extract": extract}}


def test_an_aligned_lane_has_no_problem():
    for it in EXTRACT:
        pr.check_extract([it])
    assert align.problems(_lane(), _profiles()) == []


@pytest.mark.parametrize("lane, profiles, why", [
    (_lane({**PRODUCES, "judges": ("rules", None)}), _profiles(), "the toy lane produces judges (rules); the profile's extract list lacks it"),
    (_lane({k: v for k, v in PRODUCES.items() if k != "outcome"}), _profiles(), "the profile lists outcome (iteration 1); no code"),
    (_lane({**PRODUCES, "people": ("rules", None)}), _profiles(), "people is by rules in the lane's code, by model in the profile"),
    (_lane({**PRODUCES, "details": ("pattern", ("email", "phone", "nzbn"))}), _profiles(), "details's kinds differ"),
    (_lane(), _profiles(EXTRACT[:1] + [_it("outcome", 1, "rules", ["rulings.result"])] + EXTRACT[2:]),
     "outcome lands in rulings.result, which is not a column"),
    (_lane(tables={**TABLES, "names": TABLES["names"] + ("for_party",)}), _profiles(),
     "names.for_party: a column of the toy lane's tables that no profile's field lands in"),
    (_lane(), {}, "the toy lane reads a profile the ledger does not hold"),
    (_lane(), _profiles([]), "the profile lists nothing it extracts"),
])
def test_each_misalignment_is_a_problem(lane, profiles, why):
    got = align.problems(lane, profiles)
    assert any(why in p for p in got), got


def test_housekeeping_is_never_asked_of_a_profile():
    lane = _lane()
    assert lane.is_housekeeping("rulings.loaded_at") and lane.is_housekeeping("rulings.status")
    assert not lane.is_housekeeping("rulings.outcome")


class _Conn:
    """The catalog as a dict: (schema, table) → columns."""
    def __init__(self, have):
        self.have = have

    def execute(self, sql, args):
        rows = [(c,) for c in self.have.get(tuple(args), ())]
        return type("R", (), {"fetchall": lambda self: rows})()


def test_a_lands_column_the_database_lacks_is_red():
    where = lambda t: ("toy_private", t.split(".")[1]) if "." in t else ("toy", t)  # noqa: E731
    full = {("toy", "rulings"): TABLES["rulings"], ("toy", "names"): TABLES["names"],
            ("toy_private", "details"): TABLES["toy_private.details"]}
    assert align.live_problems(_Conn(full), _lane(), where, _profiles()) == []
    short = {**full, ("toy", "names"): ("key", "name", "document")}
    assert align.live_problems(_Conn(short), _lane(), where, _profiles()) == [
        "toy.names has no column role, which a profile's field lands in"]
    gone = {k: v for k, v in full.items() if k[0] != "toy_private"}
    assert align.live_problems(_Conn(gone), _lane(), where, _profiles()) == [
        "toy_private.details does not exist, and a profile's field lands in it"]
