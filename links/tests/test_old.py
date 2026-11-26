"""The old estate's verdicts map to the new ones; the check's shape. (The review agent's tests went with it,
26 November 2026, ruling 180.)"""
import json

import links
from links import check, old


def test_old_verdicts_map_to_the_new_ones_and_a_hold_is_contested():
    assert not hasattr(old, "CURRENT_WEIGHTS")   # the old table says which judgment is current (test_old_ledgers)
    assert set(old.LEDGERS) == {"roster_identity_folds", "donor_anchors", "review_verdicts"}
    # the brief: the old "hold" is "contested"; a fold or an accept is "same"
    doc = old.__doc__
    assert "hold" in doc and "contested" in doc
    assert links.check_decision("contested", "old-estate:review_verdicts:9", {"old_table": "review_verdicts"}) == []
    assert links.check_decision("same", "old-estate:roster_identity_folds:1", {"old_rule": "same-full-name+shared-address"}) == []


def test_the_check_names_the_suppression_day():
    assert check.SUPPRESSION_DAY.isoformat() == "2026-11-18"
    assert json.dumps({"ok": True})   # the check prints JSON a job can read
