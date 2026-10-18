"""The shipped page set and keys: hashes, page numbers and figures only;
every shape and kind; the named cases; text or scan per page."""
import json
import os
import re

import pytest

from support.trials import keys, pageset

HEX = re.compile(r"^[0-9a-f]{64}$")


def test_the_shipped_page_set_is_hashes_and_shapes_only():
    h = pageset.header()
    docs = pageset.load()
    assert h["version"] == 1 and h["documents"] == len(docs) == 255
    assert h["pages"] == sum(len(d["selected_pages"]) for d in docs)
    assert all(HEX.match(d["sha256"]) for d in docs)
    assert len({d["sha256"] for d in docs}) == len(docs)
    kinds = {d["kind"] for d in docs}
    assert kinds == {"party-return", "candidate-return", "disclosure-20k", "party-expenses", "financial-statements", "promoter-return"}
    shapes = {d["shape"] for d in docs}
    assert {"text", "scan", "mixed", "image-first-page", "raster"} <= shapes
    assert min(d["year"] for d in docs) >= pageset.WINDOW_FROM
    text = open(pageset.PAGESET, encoding="utf-8").read()
    assert not re.search(r"\d+ [A-Z][a-z]+ (Road|Street|Avenue|Drive|Place)\b", text)   # no street address in the set


def test_text_or_scan_is_decided_per_page():
    for d in pageset.load():
        for p in d["selected_pages"]:
            assert p["read_from"] == ("pixels" if p["chars"] < pageset.PAGE_TEXT_MIN else "text")
        if d["shape"] == "scan":
            assert all(p["read_from"] == "pixels" for p in d["selected_pages"])
        if d["shape"] == "image-first-page":
            assert d["selected_pages"][0] == {"page": 1, "read_from": "pixels", "chars": d["selected_pages"][0]["chars"]}


def test_the_named_cases_are_in_with_every_page():
    docs = {d["named_case"]: d for d in pageset.load() if d["named_case"]}
    assert set(docs) == {"nz-first-2023", "one-party-2020", "maori-party-2020", "vision-nz-2020-handwritten"}
    for d in docs.values():
        assert len(d["selected_pages"]) == d["pages"]


def test_twenty_is_fixed_half_scan_half_text():
    t = pageset.twenty()
    assert len(t) == 20 and t == pageset.twenty()
    docs = {d["sha256"]: d for d in pageset.load()}
    hows = [next(p["read_from"] for p in docs[s]["selected_pages"] if p["page"] == pg) for s, pg in t]
    assert hows.count("pixels") == 10 and hows.count("text") == 10


def test_shape_of():
    assert pageset.shape_of({1: "x" * 100, 2: "y" * 100}, False) == "text"
    assert pageset.shape_of({1: "", 2: ""}, False) == "scan"
    assert pageset.shape_of({1: "", 2: "y" * 100}, False) == "image-first-page"
    assert pageset.shape_of({1: "x" * 100, 2: ""}, False) == "mixed"
    assert pageset.shape_of({}, True) == "raster"


def test_label_of_strips_the_tree_prefix_only():
    assert pageset.label_of("a/Party-donations-and-loans__2021-returns__ACT-Annual-Return-2020.pdf") == "ACT-Annual-Return-2020"
    assert pageset.label_of("x/2026-20k+-donations__A_Donor_1_May_2026.pdf") == "A_Donor_1_May_2026"


def test_the_keys_hold_figures_not_donors():
    k = keys.load()
    assert len(k) == 255 and set(k) == {d["sha256"] for d in pageset.load()}
    text = open(keys.KEYS, encoding="utf-8").read()
    assert "donor" not in text.lower().replace("gold_confirmed", "")
    with_ec = [r for r in k.values() if r.get("ec_table")]
    assert any(r["ec_table"]["excepted"] for r in with_ec), "the Commission's two wrong 2020 figures are marked, never a key"
    named = {r["label"]: r for r in k.values() if r["kind"] == "party-return" and r["year"] == 2020}
    flagged = {lab: (r.get("ec_table") or {}).get("excepted") for lab, r in named.items() if "Maori" in lab or "Advance" in lab}
    assert flagged and all(flagged.values()), flagged


def test_same_party_meets_file_labels_and_commission_labels():
    assert keys.same_party("ACT New Zealand", "ACT-New-Zealand-Annual-Return-2020")
    assert keys.same_party("Labour Party", "Labour-Party-amended-Annual-Return-2020")
    assert not keys.same_party("ACT New Zealand", "Labour-Party-Annual-Return-2020")


@pytest.mark.skipif(not os.path.isdir(pageset.STAGING), reason="the old folder is not on this box")
def test_locate_finds_bytes_that_hash_to_the_key():
    d = pageset.load()[0]
    data = pageset.read_bytes(d["sha256"])
    assert len(data) == d["bytes"]
