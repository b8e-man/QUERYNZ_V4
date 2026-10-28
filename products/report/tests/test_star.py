"""The name-only star read through its centre, on a fixture: the links lane
draws one `name-only@1` link from the centre's anchor to every other
component's anchor (links/spec.md, the contract for readers), so a spoke
holds one link, to the centre, and reaches the other spokes only through it."""
from products.report import walk

CENTRE, S1, S2, S3 = "building_practitioners:bp/1", "companies:d/1", "companies:d/2", "charities:o/3"
OTHER_NAME = "companies:d/9"


def link(a, b, key="jane doe", rule=walk.NAME_ONLY, grade="near"):
    return {"link_id": 0, "row_a": a, "row_b": b, "rule": rule, "evidence": {"first_last": key, "as_filed": ["x", "y"]}, "grade": grade,
            "reason": "the lane's reason for this pair", "watch": [], "decision": None, "relation": None}


LINKS = [link(CENTRE, S1), link(CENTRE, S2), link(CENTRE, S3), link(S2, "companies:d/2b", rule="full-name@1", grade="confirmed"),
         link(CENTRE, OTHER_NAME, key="john roe")]   # a link of another name key on the centre: never read as this star's


class FakeDB:
    """db.rows over LINKS for the two queries links_of makes."""

    def __init__(self, links):
        self.links, self.calls = links, []

    def rows(self, conn, sql, params=()):
        self.calls.append(sql)
        if "where rule = %s" in sql:
            rule, ends, _, limit = params
            got = [l for l in self.links if l["rule"] == rule and (l["row_a"] in ends or l["row_b"] in ends)]
        else:
            refs, _, limit = params
            got = [l for l in self.links if l["row_a"] in refs or l["row_b"] in refs]
        got = sorted(got, key=lambda l: (l["row_a"].encode(), l["row_b"].encode()))
        return [dict(l, total=len(got)) for l in got[:limit]]


def setup(monkeypatch, links=LINKS):
    fake = FakeDB(links)
    monkeypatch.setattr(walk.db, "rows", fake.rows)
    monkeypatch.setattr(walk, "links_built", lambda conn: True)
    return fake


def test_a_spoke_finds_both_other_spokes_through_the_centre_each_once(monkeypatch):
    setup(monkeypatch)
    L = walk.links_of(None, [S2, "companies:d/2b"])
    near = {l["other"]: l for l in L["near"]}
    assert set(near) == {CENTRE, S1, S3}, near
    assert len(L["near"]) == 3 and OTHER_NAME not in near
    assert near[S1]["path"] == [S2, CENTRE, S1] and near[S3]["path"] == [S2, CENTRE, S3]
    assert near[S1]["reason"] == walk.NEAR_NAMESAKE and near[S1]["grade"] == "near"
    assert near[CENTRE].get("path") is None   # the one link the spoke holds is its own, with the lane's reason
    assert [l["other"] for l in L["confirmed"]] == ["companies:d/2b"]   # confirmed links unchanged


def test_what_a_spoke_sees_does_not_depend_on_which_row_is_the_centre(monkeypatch):
    rows_ = [CENTRE, S1, S2, S3]
    seen = []
    for centre in rows_:
        setup(monkeypatch, [link(centre, r) for r in rows_ if r != centre])
        for subject in rows_:
            seen.append((subject, frozenset(l["other"] for l in walk.links_of(None, [subject])["near"])))
    for subject in rows_:
        assert {s for (x, s) in seen if x == subject} == {frozenset(set(rows_) - {subject})}, subject


def test_the_centre_reads_its_own_links_and_gains_nothing_twice(monkeypatch):
    setup(monkeypatch)
    L = walk.links_of(None, [CENTRE])
    assert sorted(l["other"] for l in L["near"]) == sorted([S1, S2, S3, OTHER_NAME]) and not any(l.get("path") for l in L["near"])


def test_the_star_read_past_its_limit_is_counted(monkeypatch):
    many = [link(CENTRE, f"companies:d/{i:04d}") for i in range(walk.LIMITS["star"] + 5)]
    setup(monkeypatch, many)
    L = walk.links_of(None, ["companies:d/0000"])
    assert L["omitted"] == 5 and len(L["near"]) == walk.LIMITS["star"]   # the centre, and every spoke but the subject's own within the limit


def test_a_group_is_read_with_its_id_first_and_in_byte_order(monkeypatch):
    calls = []

    def rows(conn, sql, params=()):
        calls.append((sql, params))
        if "where row_key = %s" in sql:
            return [{"group_id": "companies:G", "row_key": params[0], "contested": False, "settings": None}]
        return [{"row_key": "companies:G", "total": 2}, {"row_key": "a:x", "total": 2}]
    monkeypatch.setattr(walk.db, "rows", rows)
    monkeypatch.setattr(walk.db, "has_relation", lambda *a: True)
    g = walk.group_of(None, "a:x")
    sql = calls[-1][0]
    assert 'collate "C"' in sql and "row_key = group_id desc" in sql
    assert g["rows"][0] == "companies:G"
