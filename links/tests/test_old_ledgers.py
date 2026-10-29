"""The copy of the old ledgers is brought level at each build (new rows
copied, withdrawals re-read), and the old estate's last word on a donation
is its latest live judgment, whatever the weights version. Cards: the
links copy the old ledgers once and the check counts them live; the old
estate's anchors moved to weights 2.3 and the copy calls them superseded.
No database: the two connections are stand-ins."""
import json

from links import build_all, old


class _Cur:
    def __init__(self, rows, cols=None):
        self.rows = rows
        self.description = [type("D", (), {"name": c})() for c in (cols or [])]

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0]


class _Old:
    """The old database: three ledgers, rows as dicts."""

    def __init__(self, tables):
        self.tables = tables

    def execute(self, sql, params=None):
        table = sql.split("registers.")[1].split()[0]
        rows = self.tables.get(table, [])
        if "WHERE id = ANY" in sql:
            want = set(params[0])
            cols = list(rows[0]) if rows else []
            return _Cur([tuple(r[c] for c in cols) for r in rows if r["id"] in want], cols)
        return _Cur([(r["id"], r.get("withdrawn_at"), r.get("withdrawn_reason")) for r in rows])


class _New:
    """links.old_decisions: old_id → {copied, source, ...}."""

    def __init__(self):
        self.held = {}
        self.updates = []

    def execute(self, sql, params=None):
        if "split_part(old_id" in sql:
            return _Cur([(k.split(":")[1], v["copied"].get("withdrawn_at"), v["copied"].get("withdrawn_reason"))
                         for k, v in self.held.items() if v["source"] == params[0]])
        if sql.lstrip().startswith("SELECT old_id, source, copied"):
            return _Cur([(k, v["source"], v["copied"]) for k, v in sorted(self.held.items())])
        raise AssertionError(sql)

    def cursor(self):
        new = self

        class W:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def execute(self, sql, params):
                assert sql.lstrip().startswith("INSERT")
                oid, copied, source = params
                new.held.setdefault(oid, {"copied": json.loads(copied), "source": source})

            def executemany(self, sql, seq):
                for params in seq:
                    if "jsonb_build_object('withdrawn_at'" in sql:
                        w_at, w_why, oid = params
                        new.held[oid]["copied"].update(withdrawn_at=json.loads(w_at), withdrawn_reason=w_why)
                    else:
                        new.updates.append(params)
        return W()

    def commit(self):
        pass


def test_ledger_changes_name_the_new_rows_and_the_withdrawals_re_read():
    # the 21 October figures: the copy held 71,319 donor anchors, the old table 71,320 (row 75929 decided 03:33)
    held = {i: (None, None) for i in range(1, 71320)}
    theirs = [(i, None, None) for i in range(1, 71320)] + [(75929, None, None)]
    theirs[41] = (42, "2026-10-21 08:00:00+13:00", "re-judged")
    missing, changed, gone = old.ledger_changes(held, theirs)
    assert missing == [75929]
    assert changed == {42: ("2026-10-21 08:00:00+13:00", "re-judged")}
    assert gone == []
    # a gap below the highest id copied is copied too, not only the rows above it
    del held[500]
    assert old.ledger_changes(held, theirs)[0] == [500, 75929]


def test_each_build_copies_the_new_rows_and_re_reads_withdrawn_at():
    rows = [{"id": i, "band": "accept", "weights_version": "donor-anchor-2.3", "withdrawn_at": None, "withdrawn_reason": None}
            for i in (1, 2, 3)]
    the_old = _Old({"donor_anchors": rows, "roster_identity_folds": [], "review_verdicts": []})
    new = _New()
    first = old.copy_ledgers(the_old, new, "s", log=lambda *a: None)
    assert first["donor_anchors"]["copied"] == 3 and len(new.held) == 3
    # the old estate decides a fourth row and withdraws the second
    rows.append({"id": 7, "band": "accept", "weights_version": "donor-anchor-2.3", "withdrawn_at": None, "withdrawn_reason": None})
    rows[1].update(withdrawn_at="2026-10-21 03:33:18+13:00", withdrawn_reason="judged again")
    second = old.copy_ledgers(the_old, new, "s", log=lambda *a: None)
    assert second["donor_anchors"] == {"held": 3, "copied": 1, "withdrawal_re_read": 1, "gone_from_the_old_table": 0}
    assert set(new.held) == {"donor_anchors:1", "donor_anchors:2", "donor_anchors:3", "donor_anchors:7"}
    assert new.held["donor_anchors:2"]["copied"]["withdrawn_at"] == "2026-10-21 03:33:18+13:00"
    assert new.held["donor_anchors:2"]["copied"]["withdrawn_reason"] == "judged again"
    # level: a third build copies nothing and re-reads nothing
    third = old.copy_ledgers(the_old, new, "s", log=lambda *a: None)
    assert (third["donor_anchors"]["copied"], third["donor_anchors"]["withdrawal_re_read"]) == (0, 0)


def test_the_build_brings_the_copy_level_and_maps_it_before_promoting(monkeypatch):
    seen = []
    for mod, name in ((build_all.rows, "gather"), (build_all.build, "build_links"), (build_all.build, "build_watch"),
                      (build_all.build, "build_groups"), (build_all.build, "build_entities"), (build_all.pairs, "draw")):
        monkeypatch.setattr(mod, name, lambda *a, _n=name, **k: seen.append(_n) or {})
    monkeypatch.setattr(build_all.measure, "run", lambda *a, **k: seen.append("measure") or {})
    monkeypatch.setattr(build_all.old, "copy_ledgers", lambda o, c, s, log=None: seen.append("copy") or {})
    monkeypatch.setattr(build_all.old, "map_all", lambda o, c, s, log=None: seen.append("map") or {})
    monkeypatch.setattr(build_all.old, "promote", lambda c, s, log=None: seen.append("promote") or {})

    class Conn:
        def execute(self, sql, params=None):
            return _Cur([(1,)])
    build_all.run(Conn(), Conn(), "s", log=lambda *a: None, oldconn=object())
    assert seen.index("gather") < seen.index("copy") < seen.index("map") < seen.index("promote")
    assert seen.index("build_groups") < seen.index("build_entities") < seen.index("draw")   # the entities follow the groups (ruling 123)


def _anchor(i, version, key, band="accept", withdrawn=None):
    return (f"donor_anchors:{i}", {"id": i, "weights_version": version, "source": "party", "row_key": key,
                                   "donation_id": i, "band": band, "withdrawn_at": withdrawn})


def _old_estate_2_2_and_2_3():
    """The 21 October reload's figures: 9,025 anchors at donor-anchor-2.2
    (8,523 not withdrawn, decided 7 to 30 September), then 6,466 at
    donor-anchor-2.3 (30 September to 21 October). Here 6,000 of the 2.3
    judgments re-judge a live 2.2 donation and 466 judge a donation first
    anchored after 30 September."""
    rows, i = [], 0
    for n in range(9025):
        i += 1
        rows.append(_anchor(i, "donor-anchor-2.2", f"d{n}", withdrawn="2026-09-30" if n >= 8523 else None))
    for n in range(6000):
        i += 1
        rows.append(_anchor(i, "donor-anchor-2.3", f"d{n}"))
    for n in range(466):
        i += 1
        rows.append(_anchor(i, "donor-anchor-2.3", f"new{n}"))
    return rows


def test_the_latest_live_judgment_of_each_donation_is_applied_whatever_its_version():
    rows = _old_estate_2_2_and_2_3()
    applied, seen = old.applied_anchors(rows)
    assert seen["latest_decision_version"] == "donor-anchor-2.3"
    assert seen["versions"] == {"donor-anchor-2.2": {"rows": 9025, "live": 8523, "applied": 8523 - 6000},
                                "donor-anchor-2.3": {"rows": 6466, "live": 6466, "applied": 6466}}
    by = dict(rows)
    # a donation the old estate re-decided: the 2.3 reading stands, the 2.2 one is the record
    assert applied["donor_anchors:1"] == "superseded by donor_anchors:9026 (weights donor-anchor-2.3)"
    assert applied["donor_anchors:9026"] is None
    # a donation first anchored after 30 September has its decision applied
    assert by["donor_anchors:15491"]["row_key"] == "new465" and applied["donor_anchors:15491"] is None
    # a donation 2.3 has not reached keeps its 2.2 decision
    assert applied["donor_anchors:8000"] is None
    assert applied["donor_anchors:9000"] == "withdrawn"
    # every version applied comes from the table: none is named in the code
    assert not hasattr(old, "CURRENT_WEIGHTS")


def test_the_latest_is_by_order_of_decision_never_by_a_version_sorted_as_text():
    rows = [_anchor(1, "donor-anchor-2.9", "d"), _anchor(2, "donor-anchor-2.10", "d")]
    applied, seen = old.applied_anchors(rows)
    assert applied == {"donor_anchors:1": "superseded by donor_anchors:2 (weights donor-anchor-2.10)", "donor_anchors:2": None}
    assert seen["latest_decision_version"] == "donor-anchor-2.10"
    # a withdrawn latest gives the word back to the one before it
    rows = [_anchor(1, "donor-anchor-2.2", "d"), _anchor(2, "donor-anchor-2.3", "d", withdrawn="2026-10-20")]
    assert old.applied_anchors(rows)[0] == {"donor_anchors:1": None, "donor_anchors:2": "withdrawn"}
    # a 1.0 or 1.1 row has no content key: it cannot be told which later judgment re-read its donation, so it is never the word
    keyless = _anchor(3, "donor-anchor-1.1", None)
    assert old.applied_anchors([keyless])[0]["donor_anchors:3"].startswith("names no donation key")


def test_a_hold_applies_only_while_the_anchors_it_read_are_applied(monkeypatch):
    def corroborated(i, version, key, pk):
        oid, c = _anchor(i, version, key, band="corroborated")
        c["features"] = {"person_key": pk}
        return oid, c
    new = _New()
    for oid, c in (corroborated(1, "donor-anchor-2.2", "a", "11"), corroborated(2, "donor-anchor-2.2", "b", "22"),
                   corroborated(3, "donor-anchor-2.3", "a", "11")):
        new.held[oid] = {"source": "donor_anchors", "copied": c}
    for i, pk in ((1, "11"), (2, "22")):
        new.held[f"review_verdicts:{i}"] = {"source": "review_verdicts",
                                            "copied": {"id": i, "card_key": pk, "weights_version": "donor-anchor-2.2", "verdict": "hold"}}
    monkeypatch.setattr(old, "director_map", lambda o, c, s, ids: {i: (f"directors:{i}", "name, company and appointment date") for i in ids})
    monkeypatch.setattr(old, "donation_map", lambda o, c, s, anchors: {f"donor_anchors:{a['id']}": (f"party_returns:{a['row_key']}", "donor") for a in anchors})
    monkeypatch.setattr(old.links, "pair", lambda a, b: tuple(sorted((a, b))))
    tally = old.map_all(None, new, "s", log=lambda *a: None)
    how = {u[4]: u[3] for u in new.updates}
    assert how["donor_anchors:1"].startswith("superseded by donor_anchors:3")
    assert not how["donor_anchors:3"].startswith(("superseded", "withdrawn"))
    # identity 11's 2.2 anchor was judged again at 2.3: Arthur's 2.2 hold read a reading that is no longer the word
    assert how["review_verdicts:1"].startswith("superseded")
    # identity 22's 2.2 anchor is still the latest: the hold stands
    assert not how["review_verdicts:2"].startswith(("superseded", "withdrawn"))
    assert tally["donor_anchors_versions"]["latest_decision_version"] == "donor-anchor-2.3"
