"""The Follow the Money template holds its five things, its ten sections and the frozen site's settings."""
import json

import pytest

import products.templates as tp
from products.templates import ftm


def test_the_template_passes_the_contract_and_names_the_ten_kinds():
    t = ftm.load()
    assert tp.validate(t) == []
    assert t.shape == "published-site" and t.use_case == 1
    assert tuple(t.sections) == ftm.KINDS and len(ftm.KINDS) == 10
    assert all(r.table.startswith("pub.") for r in t.reads)
    assert "pub.party_return_totals" in {r.table for r in t.reads}
    assert "pub.disclosures" in {r.table for r in t.reads}


def test_the_settings_are_the_frozen_site_s():
    s = ftm.settings()
    assert s["window_from"] == 2017 and s["named_from"] == "2017-09-24" and s["line"] == 15000
    assert ftm.races(s) == {2020: [2018, 2019, 2020], 2023: [2021, 2022, 2023], 2026: [2024, 2025, 2026]}
    assert ftm.race_of(2017, s) is None and ftm.race_of(2019, s) == 2020 and ftm.race_of(2026, s) == 2026
    assert len(s["headline_parties"]) == 7 and len(set(s["headline_parties"])) == 7


def test_the_rules_say_what_the_plan_fixes():
    t = ftm.load()
    text = " ".join(t.rules)
    for want in ("home address", "suppressed name", "the return is the record", "no press", "renamed party"):
        assert want in text, want
    assert t.known_limits.startswith("Nothing before 2017")


def test_a_defective_template_is_refused(tmp_path):
    d = json.load(open(ftm.PATH, encoding="utf-8"))
    d["sections"] = ["home"]
    p = tmp_path / "ftm.json"
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="ten kinds"):
        ftm.load(str(p))
    d["sections"] = list(ftm.KINDS)
    del d["settings"]["races"]
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="races"):
        ftm.load(str(p))
