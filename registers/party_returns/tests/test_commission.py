"""The outside check against the Commission's own by-year table
(`commission.py`). The parser is tested on a page shaped like the
listing, with made-up parties; the filled sample is compared with the
listing the old folder holds, and every difference must have a card."""
import glob
import os

import pytest

from registers.party_returns import amendments, capture, commission
from registers.party_returns.tests.test_party_returns import REPO, filled  # noqa: F401 — the module's filled sample

PAGE = """
<button class="accordion__title">
    2023 party donations and loans returns
</button>
<h3>Summary of donations and loans</h3>
<table><tr><th>Party</th><th>Total party donations</th><th>Total party loans</th><th>Audit report</th></tr>
<tr><td><a href="/assets/Annual-Returns/2023/Example-Party-2023-amended.pdf">Example Party (amended 5/6/2024)</a> [PDF, 1MB]
    <a href="/assets/Annual-Returns/2023/Example-Party-2023.pdf">Example Party</a> [PDF, 2MB]</td>
    <td>$1,234.56</td><td>$19,000.00</td><td>Yes</td></tr>
<tr><td><a href="/assets/Annual-Returns/2023/Sample-Party-2023.pdf">Sample Party</a> [PDF, 1MB]</td>
    <td>NIL</td><td>NIL</td><td>Not required</td></tr>
</table>
<button class="accordion__title">
    2019 party donations and loans returns
</button>
<table><tr><th>Party</th><th>Total Party Donations</th><th>Total Party Loans</th></tr>
<tr><td>Example New Zealand Party</td><td>$ 2,000.00</td><td>Nil</td></tr>
<tr><td>Nobody's Party</td><td>$ 5.00</td><td>Nil</td></tr>
</table>
<h3>Downloads</h3>
<a href="/assets/Annual-Returns/2019/Example-NZ-Annual-Return-2019.pdf">Download the Example NZ annual return 2019 (PDF, 1MB)</a>
<button class="accordion__title">
    2016 party donations and loans returns
</button>
<table><tr><th>Party</th><th>Total party donations</th><th>Total party loans</th></tr>
<tr><td>Example Party</td><td>$ 9.00</td><td>Nil</td></tr></table>
"""


def test_the_summary_tables_give_each_party_year_its_figures_and_its_files():
    rows = commission.summary(PAGE)
    got = [(r.year, r.label, r.donations, r.loans, r.files) for r in rows]
    assert got == [
        (2023, "Example Party", 1234.56, 19000.0, ["Example-Party-2023-amended.pdf", "Example-Party-2023.pdf"]),
        (2023, "Sample Party", 0.0, 0.0, ["Sample-Party-2023.pdf"]),
        (2019, "Example New Zealand Party", 2000.0, 0.0, ["Example-NZ-Annual-Return-2019.pdf"]),
        (2019, "Nobody's Party", 5.0, 0.0, []),
    ], "2016 is before the lane's first year; a row with no list item of its own words gets no files"


def test_the_current_return_is_compared_to_the_cent_and_nothing_is_guessed():
    rows = commission.summary(PAGE)
    by_name = {"example-party-2023-amended.pdf": "new", "example-party-2023.pdf": "old",
               "sample-party-2023.pdf": "s", "example-nz-annual-return-2019.pdf": "e19"}
    returns = [
        {"document": "new", "year": 2023, "party_label": "Example Party", "declared_total": 1234.56, "loans_total": 15000.0},
        {"document": "old", "year": 2023, "party_label": "Example Party", "declared_total": 999.0, "loans_total": 0},
        {"document": "e19", "year": 2019, "party_label": "Example Party", "declared_total": 2000.01, "loans_total": 0},
        {"document": "x", "year": 2020, "party_label": "Unlisted Party", "declared_total": 1.0, "loans_total": 0},
    ]
    out = commission.compare(rows, returns, by_name, replaced={"old"}, aside={"s": "declaration"})
    assert [d["document"] for d in out["equal"]] == ["new"]
    assert [(d["document"], d["commission"], d["ours"]) for d in out["loans_differ"]] == [("new", 19000.0, 15000.0)]
    assert [(d["document"], d["ours"]) for d in out["differ"]] == [("e19", 2000.01)], "a cent is a difference"
    assert [d["stages"] for d in out["set_aside"]] == [["declaration"]]
    assert [d["label"] for d in out["unmatched"]] == ["Nobody's Party"]
    assert [d["document"] for d in out["not_listed"]] == ["x"]


def test_each_declared_total_equals_the_commission_s_table_or_has_a_card(filled):  # noqa: F811
    path = amendments.listing_file()
    assert os.path.exists(path), f"the Commission's listing is read from {path}, which is not here"
    conn, schema = filled["conn"], filled["schema"]
    replaced = {r[0] for r in conn.execute(f"SELECT document FROM {schema}.amendments")}
    aside = {r[0]: r[1] for r in filled["aside"]}
    out = commission.compare(commission.summary(commission.listing()), filled["rows"],
                             amendments.held_by_name(capture.old_index()), replaced, aside)
    cards = " ".join(open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(REPO, "cards", "*.md")))
    uncarded = [d for d in out["differ"] + out["loans_differ"] if d["document"] not in cards]
    assert uncarded == [], "differences from the Commission's table with no card: " + "; ".join(
        f"{d['label']} {d['year']} ours {d['ours']:.2f} Commission {d['commission']:.2f} document {d['document']}"
        for d in uncarded)
    assert len(out["equal"]) >= 25
