"""The reader on the real pages sample.list names, from the document store (their addresses from the names the
landing wrapper kept): each page's count, years, seats and shape as the council published them on 22 October 2026,
and every row held to the register's rules. Fails the day the reader misreads a shape it was measured on. Skips
where the store or the sample database is absent."""
import os

import pytest

from support import sample
from support.docstore.landing import path_for, read_bytes
from registers.local_elections import capture, check, load, read

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [i.split()[-1] for i in sample.read_list(os.path.join(LANE, "sample.list")) if i.startswith("key: page ")]


@pytest.fixture(scope="module")
def pages():
    if not os.path.exists(path_for(PAGES[0])):
        pytest.skip("the document store is not on this box")
    try:
        from support import db
        from registers.local_elections import sample as fill
        with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
            got = fill.pages_of([f"key: page {h}" for h in PAGES], conn)
    except Exception as exc:  # noqa: BLE001 — no database here
        pytest.skip(f"the sample database is not reachable: {type(exc).__name__}")
    seeds = {u: ys for _, ys, u in capture.seeds()}
    out = {}
    for p in got:
        ys = seeds.get(p["url"], [])
        o = read.read_listing(read_bytes(p["sha256"]), p["url"], p["council"], ys[0] if len(ys) == 1 else None,
                              capture.council_words(p["council"], p["url"]))
        o["rows"] = [r for r in o["rows"] if (r["election_year"] or 9999) >= read.WINDOW_FROM]
        out[p["sha256"][:12]] = (p, o)
    return out


def _page(pages, prefix):
    return next(v for k, v in pages.items() if k.startswith(prefix))


#: page → (returns in window, years, combined files, profile)
EXPECT = {
    "6700de41d2b5": (21, {2025}, 0, "council-returns-listing"),
    "297b4a3e7992": (19, {2019}, 0, "council-returns-listing"),
    "686e7439575e": (77, {2025}, 0, "council-returns-listing"),
    "a984f41380c7": (43, {2025}, 0, "council-returns-results-table"),
    "00243da80e2b": (52, {2022}, 0, "council-returns-listing"),
    "325c026d6dda": (30, {2025}, 0, "council-returns-results-table"),
    "bbb716a41f1a": (0, set(), 0, "council-returns-hub"),
    "9ede67eaa66f": (67, {2025}, 0, "council-returns-results-table"),
    "f480be9a12bd": (71, {2024}, 0, "council-returns-listing"),
}


@pytest.mark.parametrize("prefix", sorted(EXPECT))
def test_each_page_reads_as_the_council_published_it(pages, prefix):
    p, o = _page(pages, prefix)
    n, years, several, profile = EXPECT[prefix]
    got = {r["file_url"] for r in o["rows"]}
    assert len(got) == n, f"{p['council']}: {len(got)} returns"
    assert {r["election_year"] for r in o["rows"]} == years
    assert sum(r["covers"] == "several candidates" for r in o["rows"]) == several
    assert load.shape_of(o) == profile


def test_northland_s_rows_each_name_a_candidate_and_a_constituency(pages):
    for prefix in ("6700de41d2b5", "297b4a3e7992"):
        _, o = _page(pages, prefix)
        assert all(read.looks_like_a_name(r["candidate_as_listed"]) for r in o["rows"])
        assert all(r["position"].lower().endswith("constituency") for r in o["rows"])


def test_waitaki_s_combined_files_name_nobody_and_each_names_its_seat(pages):
    _, o = _page(pages, "0d79439954f4")
    assert o["rows"] and all(r["covers"] == "several candidates" and r["candidate_as_listed"] == "" and r["position"]
                             for r in o["rows"])
    assert {r["election_year"] for r in o["rows"]} == {2019, 2022, 2025}


def test_no_row_on_any_sample_page_breaks_a_register_rule(pages):
    vals = []
    for p, o in pages.values():
        for r in o["rows"]:
            assert r["covers"] == "several candidates" or read.looks_like_a_name(r["candidate_as_listed"]) or \
                r["candidate_as_listed"], r["file_url"]
            vals += [(r["file_url"], c, r[c]) for c in check.TEXT_COLUMNS]
    assert check.value_problems(vals) == []
