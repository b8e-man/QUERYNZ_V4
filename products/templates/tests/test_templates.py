"""A template holds its five things and reads only published tables."""
import json

import products.templates as tp


def good():
    return tp.Template(name="follow-the-money", shape="published-site", use_case=1,
                       reads=(tp.Read("pub.party_returns", "Electoral Act filings, public", "", "daily"),
                              tp.Read("pub.disclosures", "Electoral Act filings, public", "", "daily")),
                       sections=("home", "parties", "donors"), rules=("a failed company restarted under a new name",),
                       known_limits="Nothing before 2017. Unreadable names are shown as unreadable.",
                       owner="founding", version=1, settings={"window_from": 2017})


def test_a_complete_template_passes():
    assert tp.validate(good()) == []


def test_each_missing_thing_is_named():
    t = good()
    bare = tp.Template(name="x", shape="pamphlet", use_case=1, reads=(), sections=(), rules=(), known_limits=" ",
                       owner="", version=0)
    probs = tp.validate(bare)
    for want in ("shape must be", "names the published tables", "has sections", "known-limits", "has an owner", "version from 1"):
        assert any(want in p for p in probs), want
    inside = tp.Template(**{**t.__dict__, "reads": (tp.Read("party_returns.rows", "x", "", "daily"),
                                                     tp.Read("pub.ok", "", "", "hourly"))})
    probs = tp.validate(inside)
    assert any("reads only pub.* views" in p for p in probs)
    assert any("refresh must be" in p for p in probs) and any("licence" in p for p in probs)


def test_load_from_json(tmp_path):
    p = tmp_path / "ftm.json"
    p.write_text(json.dumps({"name": "ftm", "shape": "published-site", "use_case": 1,
                             "reads": [{"table": "pub.x", "licence": "public", "attribution": "", "refresh": "daily"}],
                             "sections": ["home"], "rules": [], "known_limits": "none yet", "owner": "o", "version": 2}))
    t = tp.load(str(p))
    assert t.version == 2 and t.reads[0].table == "pub.x" and tp.validate(t) == []
    assert [x.name for x in tp.all_templates(str(tmp_path))] == ["ftm"]
