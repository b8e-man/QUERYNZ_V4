"""The party-boards lane's tests (ruling 72). The page and name rules are
tested on small pages written here (people invented); the profile's shapes
are tested on the sample's real pages, read from their bytes, with what
each must come to pinned, so a change to the profile or the reader that
moves one page fails here; the filled sample is tested against the row
contract, the catch log and the outside check. No model is called."""
import datetime as dt
import gzip
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.party_boards import capture, check, page, read

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "party_boards")


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


# --- the page as lines ---------------------------------------------------------

def test_inline_markup_does_not_break_a_line_and_blocks_do():
    html = (b"<html><head><title>T</title><script>var x='Board';</script></head><body>"
            b"<h2>Executive officers:</h2><p><strong>S<span>ecretary:</span></strong> Jane Example</p>"
            b"<p>Pat Example<br><strong>Treasurer</strong></p><h4>Kim Example <small>President</small></h4></body></html>")
    got = [ln.text for ln in page.lines(html)]
    assert got == ["T", "Executive officers:", "Secretary: Jane Example", "Pat Example", "Treasurer", "Kim Example", "President"]
    lines = page.lines(html)
    assert lines[4].has("strong") and not lines[3].has("strong") and lines[6].has("h4") and lines[6].has("small")


def test_the_archive_toolbar_is_cut_and_compressed_bytes_are_opened():
    html = ("<body><!-- BEGIN WAYBACK TOOLBAR INSERT --><div>Board of Directors</div><!-- END WAYBACK TOOLBAR INSERT -->"
            "<h1>Board of Directors</h1></body>").encode()
    assert [ln.text for ln in page.lines(gzip.compress(html))] == ["Board of Directors"]
    from compression import zstd
    assert [ln.text for ln in page.lines(zstd.compress(html))] == ["Board of Directors"]
    with pytest.raises(page.Undecodable):
        page.lines(b"\x1f\x8b\x08\x00broken")


def test_table_cells_keep_their_row():
    html = b"<table><tr><td><strong>President</strong></td><td>Jane Example</td></tr><tr><td>Vice</td><td>Pat Example</td></tr></table>"
    assert [(ln.text, ln.row) for ln in page.lines(html)] == [("President", 0), ("Jane Example", 0), ("Vice", 1), ("Pat Example", 1)]


# --- the name rule ---------------------------------------------------------------

def test_a_name_loses_its_honorific_post_nominals_and_bracket_and_keeps_the_bracket_apart():
    assert read.split_name("Rt Hon Jane Example") == ("Jane Example", None)
    assert read.split_name("Pat Example ONZM") == ("Pat Example", None)
    assert read.split_name("Kim Example (Acting)") == ("Kim Example", "Acting")
    assert read.split_name("Hinewai (Hine) Example (Party President)") == ("Hinewai (Hine) Example", "Party President")
    assert read.split_name("Sir Tama Example") == ("Tama Example", None)


@pytest.mark.parametrize("text, why", [
    ("Jane Example", None), ("JANE EXAMPLE", None), ("Andrew von Example", None), ("Tama Te Example-Smith", None),
    ("vacant", "declared vacant"), ("Example", "not a name: 1 word(s)"),
    ("Board Member", "not a name: a role or heading word"), ("jane@example.nz", "a contact line, not a name"),
    ("Mobile: 021 555 0101", "a contact line, not a name"),
    ("Jane has worked here for years.", "not a name: not every word is a capitalised name word"),
])
def test_the_name_rule(text, why):
    assert read.why_not_a_name(text) == why


# --- the forms, on a profile written here ---------------------------------------

def _prof(*shapes, refuse=()):
    return {"version": 1, "config": {"shapes": list(shapes), "refuse": list(refuse)}}


CAP = capture.Capture("Example Party", "https://example.nz/board", "wayback", "20240101000000", "0" * 64, "x.html")


def test_pair_form_takes_every_role_line_and_a_name_alone_takes_the_heading_s_role():
    html = (b"<h1>Our Board</h1><div class='c'><h3>Jane Example</h3><h4>Chair</h4><p>bio.</p><h4>Treasurer</h4></div>"
            b"<div class='c'><h3>Pat Example</h3><p>Pat has served for years.</p></div><h2>Our MPs</h2><div class='c'><h3>Kim Example</h3><h4>MP</h4></div>")
    shape = dict(id="s", url="example", opens="^Our Board$", closes=["^Our MPs$"], form="pair",
                 name=["div.c", "h3"], role=["div.c", "h4"], role_default="Board member")
    got = read.read(html, "a" * 64, CAP, prof=_prof(shape))
    assert got.status == "read" and got.set_aside == []
    assert [(r["name"], r["role"], r["role_basis"]) for r in got.rows] == [
        ("Jane Example", "Chair; Treasurer", "stated"), ("Pat Example", "Board member", "heading")]
    assert all(r["key"].startswith("a" * 64 + "/s/line-") and r["tier"] == "declared" for r in got.rows)


def test_without_a_role_default_a_name_with_no_role_is_set_aside_not_guessed():
    html = b"<h1>Our Board</h1><h3>Jane Example</h3><h4>Chair</h4><h3>Pat Example</h3>"
    shape = dict(id="s", url="example", opens="^Our Board$", form="pair", name=["h3"], role=["h4"])
    got = read.read(html, "a" * 64, CAP, prof=_prof(shape))
    assert [r["name"] for r in got.rows] == ["Jane Example"]
    assert got.set_aside == [("line 3", "a name with no role beside it, and no role the heading declares")]


def test_cells_form_reads_role_and_name_cells_and_sets_a_vacancy_aside():
    html = (b"<p>BOARD</p><table><tr><td><strong>President</strong></td><td>Jane Example</td><td><a>j@x.nz</a></td></tr>"
            b"<tr><td><strong>South</strong></td><td>vacant</td></tr></table><p>MANAGEMENT</p>"
            b"<table><tr><td>Manager</td><td>Pat Example</td></tr></table>")
    shape = dict(id="t", url="example", opens="^BOARD$", closes=["^MANAGEMENT$"], form="cells", cells=[0, 1])
    got = read.read(html, "a" * 64, CAP, prof=_prof(shape))
    assert [(r["name"], r["role"]) for r in got.rows] == [("Jane Example", "President")]
    assert [why for _, why in got.set_aside] == ["declared vacant"]


def test_line_form_splits_two_names_under_one_role_only_where_the_shape_says():
    html = b"<h2>Executive officers:</h2><h2>Co-Leaders: Jane Example &amp; Pat Example</h2><h2>Party Vote: Example Party</h2>"
    shape = dict(id="l", url="example", opens="^Executive officers:$", closes=["^Party Vote:"], form="line",
                 pattern=r"^(?P<role>[^:]{2,50}?)\s*:\s*(?P<name>.+)$")
    unsplit = read.read(html, "a" * 64, CAP, prof=_prof(shape))
    assert unsplit.rows == [] and [w for _, w in unsplit.set_aside] == ["not a name: not every word is a capitalised name word"]
    got = read.read(html, "a" * 64, CAP, prof=_prof({**shape, "split": r"\s+(?:&|and)\s+"}))
    assert [(r["name"], r["role"], r["place"]) for r in got.rows] == [
        ("Jane Example", "Co-Leaders", "line 1 name 1"), ("Pat Example", "Co-Leaders", "line 1 name 2")]


def test_a_page_no_shape_knows_a_refused_page_and_a_dropped_layout_are_drop_notes_with_their_reason():
    html = b"<h1>Our Board</h1><h3>John Doe</h3><h4>Chair</h4><p>Enter member description here</p>"
    shape = dict(id="s", url="example", opens="^Our Board$", form="pair", name=["h3"], role=["h4"])
    other = capture.Capture("Example Party", "https://elsewhere.nz/", "current", "20240101000000", "0" * 64, "x.html")
    assert read.read(html, "a" * 64, other, prof=_prof(shape)).reason == "no shape for this page's address"
    assert read.read(b"<h1>About</h1>", "a" * 64, CAP, prof=_prof(shape)).reason == "no board heading the profile knows on the page"
    refused = read.read(html, "a" * 64, CAP, prof=_prof(shape, refuse=[{"pattern": "Enter member description", "reason": "placeholder"}]))
    assert (refused.status, refused.reason, refused.rows) == ("drop-note", "placeholder", [])
    dropped = read.read(html, "a" * 64, CAP, prof=_prof({**shape, "drop": "columns that do not pair"}))
    assert (dropped.status, dropped.shape, dropped.reason) == ("drop-note", "s", "columns that do not pair")


def test_requires_chooses_between_two_themes_under_one_heading():
    cards = b"<h2>Board</h2><div class='card-body'><h3>Jane Example</h3><h4>Chair</h4></div>"
    boxes = b"<h2>Board</h2><div class='box'><p>Jane Example<br><strong>Chair</strong></p></div>"
    a = dict(id="cards", url="example", opens="^Board$", requires=["div.card-body", "h3"], form="pair",
             name=["div.card-body", "h3"], role=["div.card-body", "h4"])
    b = dict(id="boxes", url="example", opens="^Board$", requires=["div.box"], form="pair",
             name=["div.box", "!strong"], role=["div.box", "strong"])
    for html, want in ((cards, "cards"), (boxes, "boxes")):
        got = read.read(html, "a" * 64, CAP, prof=_prof(a, b))
        assert got.shape == want and [(r["name"], r["role"]) for r in got.rows] == [("Jane Example", "Chair")]


# --- the profile, on the sample's real pages -----------------------------------

def test_the_profile_is_well_formed_and_every_shape_names_a_form_the_reader_has():
    prof = read.profile()
    assert prof["slug"] == read.PROFILE and int(prof["version"]) >= 1 and prof["recognise"]["landmarks"]
    ids = [s["id"] for s in prof["config"]["shapes"]]
    assert len(ids) == len(set(ids))
    for s in prof["config"]["shapes"]:
        assert s["form"] in read.FORMS, s["id"]
        assert any(s["id"] in lm for lm in prof["recognise"]["landmarks"]), s["id"]


#: what each sample page must come to: (status, shape, rows, set aside), measured 21 October 2026
EXPECTED = {
    "73ce45e5049d": ("read", "act-board-table", 8, 0),
    "a7c10e6b6464": ("read", "act-board-table", 8, 0),
    "6057cc3993d0": ("read", "act-board-table", 9, 1),
    "0438e6f045a2": ("drop-note", None, 0, 0),
    "55f4d95a76ab": ("read", "ajp-team-elementor", 3, 0),
    "2a74f29288af": ("read", "ajp-team-bricks", 3, 0),
    "6da107e0ba85": ("drop-note", None, 0, 0),
    "4572a5a7854f": ("read", "alcp-officers-2018", 9, 0),
    "7fbd7e3ca4ff": ("drop-note", "alcp-leadership-2020", 0, 0),
    "3df412749cc2": ("read", "alcp-team-2026", 6, 0),
    "86424f29442e": ("read", "conservative-board-list", 4, 0),
    "543c467bcda4": ("read", "nzofp-board", 4, 0),
    "a6abde8d0783": ("read", "nzfirst-board-boxes", 11, 0),
    "768a4bb4ba8b": ("read", "nzfirst-board-cards", 9, 0),
    "7943e28c08d9": ("read", "nzfirst-board-cards", 8, 1),
    "d3a51bff6bef": ("drop-note", None, 0, 0),
    "b91bff84c299": ("board section, no names", "labour-nz-council-2017", 0, 0),
    "447c21529888": ("read", "opportunity-board-2026-03", 6, 0),
    "bd593c87f47c": ("read", "opportunity-board", 5, 0),
    "4de16b4821c2": ("read", "tpm-national-executive", 3, 0),
    "268515745dbd": ("drop-note", None, 0, 0),
    "fb6dc414ae73": ("read", "national-directors-2018", 9, 0),
    "6bfe3b205f85": ("read", "national-board-2020", 9, 0),
    "c82eed4fe841": ("read", "national-bod-2022", 9, 0),
    "4ea386174104": ("read", "national-bod-2023", 9, 0),
    "185edb0bb583": ("drop-note", None, 0, 0),
    "0a6d93afc607": ("read", "wrp-executive", 1, 0),
}


def _items():
    return [i.split()[0] for i in sample.read_list(os.path.join(LANE, "sample.list")) if not i.startswith("key:")]


@pytest.fixture(scope="module")
def pages():
    """sha256 → (Capture, bytes) for every sample page in the window, from
    the document store, else the old folder; skipped where neither is here."""
    from support.docstore.landing import path_for, read_bytes
    try:
        by = capture.by_document(capture.manifest())
    except OSError:
        pytest.skip("the old capture's manifest is not on this box")
    out = {}
    for sha in _items():
        c = by[sha][0]
        if not capture.in_window(c):
            continue
        if os.path.exists(path_for(sha)):
            out[sha] = (c, read_bytes(sha))
        elif os.path.exists(c.path):
            with open(c.path, "rb") as f:
                out[sha] = (c, f.read())
        else:
            pytest.skip(f"sample page {sha[:12]} is neither in the store nor in the old folder")
    return out


@pytest.fixture(scope="module")
def readings(pages):
    return {sha: read.read(data, sha, c) for sha, (c, data) in pages.items()}


def test_the_sample_names_a_page_for_every_party_in_the_capture_and_every_shape(pages, readings):
    by = capture.by_document(capture.manifest())
    assert {c.party for c in capture.manifest() if capture.in_window(c)} <= {by[s][0].party for s in _items()}
    assert {s["id"] for s in read.shapes()} <= {r.shape for r in readings.values()}


def test_each_sample_page_comes_to_what_was_measured(readings):
    got = {sha[:12]: (r.status, r.shape, len(r.rows), len(r.set_aside)) for sha, r in readings.items()}
    assert got == EXPECTED


def test_the_declared_roles_of_known_pages(readings):
    def roles(prefix):
        return [(r["role"], r["role_basis"]) for r in next(v for k, v in readings.items() if k.startswith(prefix)).rows]
    assert [r for r, _ in roles("73ce45e5049d")] == ["Party Leader", "President", "Vice President", "Auckland North",
                                                     "Auckland South", "Central North Island", "Lower North Island", "South Island"]
    assert [r for r, _ in roles("4572a5a7854f")][:2] == ["Co-Leaders", "Co-Leaders"]          # one line, two people
    assert roles("fb6dc414ae73")[1] == ("Leader of the National Party; Leader of the Opposition", "stated")
    assert sorted(b for _, b in roles("bd593c87f47c")) == ["heading"] * 4 + ["stated"]
    assert roles("86424f29442e") == [("Board member", "heading")] * 3 + [("Secretary General", "stated")]
    nick = next(v for k, v in readings.items() if k.startswith("543c467bcda4")).rows
    assert nick[-1]["role"] == "Party President" and "(" in nick[-1]["name"]        # a nickname's bracket stays in the name
    caps = next(v for k, v in readings.items() if k.startswith("4ea386174104")).rows[0]
    assert caps["name_as_declared"].isupper() and caps["name"] == caps["name_as_declared"]


def test_no_row_carries_a_contact_line_or_a_promoter_statement(readings):
    for r in readings.values():
        for row in r.rows:
            for k in ("name_as_declared", "name", "qualifier", "role", "section"):
                v = row.get(k) or ""
                assert "@" not in v and "authorised by" not in v.lower() and not any(ch.isdigit() for ch in v), (row["key"], k)


# --- the filled sample -------------------------------------------------------

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_party_boards"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    schema = _schema()
    sample.fill_schema(schema, lambda: db.connect(db.OWNER_KEY, "querynz_v4_sample"), REPO, log=lambda *a: None)
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        def q(sql):
            cur = conn.execute(sql)
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        yield {"schema": schema, "conn": conn,
               "roles": q(f"SELECT * FROM {schema}.party_boards_roles ORDER BY key"),
               "pages": q(f"SELECT * FROM {schema}.party_boards_pages"),
               "aside": q(f"SELECT * FROM {schema}.party_boards_set_aside")}


def test_every_capture_is_a_page_row_and_the_outside_check_passes_on_the_sample(filled):
    held = {p["document"] for p in filled["pages"]}
    assert held == set(_items())
    manifest = [c for c in capture.manifest() if c.sha256 in held]
    assert len(filled["pages"]) == len(manifest) == len(_items()) + 1          # one page captured on two days
    assert check.against_manifest(filled["pages"], manifest, filled["roles"]) == []
    assert [p for p in filled["pages"] if p["status"] == "before the window, not landed"][0]["document"].startswith("d5b10d9431aa")


def test_rows_and_the_catch_log_add_up_and_the_counts_say_so(filled):
    assert len(filled["roles"]) == sum(v[2] for v in EXPECTED.values())
    assert len(filled["aside"]) == sum(v[3] for v in EXPECTED.values())
    assert sorted(a["reason"] for a in filled["aside"]) == ["declared vacant", "the name repeats the role line"]
    c = check.counts(filled["roles"], filled["pages"])
    assert c["unrecognised"] == sum(1 for v in EXPECTED.values() if v[0] == "drop-note") + 1    # + the second capture
    assert c["by_party"]["New Zealand Labour Party"]["rows"] == 0 and c["by_party"]["The New Zealand National Party"]["rows"] == 36


def test_every_row_keeps_the_row_contract_and_cites_its_capture(filled):
    today = dt.date.today()
    keys = [r["key"] for r in filled["roles"]]
    assert len(keys) == len(set(keys))
    for r in filled["roles"]:
        row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
        row["loaded_at"] = r["loaded_at"].isoformat()
        row["filed"] = {"captured_on": r["captured_on"].isoformat()}
        assert rowcontract.validate(row, today) == [], r["key"]
        assert r["tier"] == "declared" and r["url"].startswith("http") and r["captured_on"] <= r["last_captured_on"]
        assert (r["archive_url"] or "").startswith("https://web.archive.org/web/") == (r["capture_kind"] == "wayback")


def test_the_published_views_build_on_the_lane_s_tables(filled):
    from registers.party_boards import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.party_boards_pub_"))
    n = conn.execute(f"SELECT count(*) FROM {schema}.party_boards_pub_party_board_roles").fetchone()[0]
    m = conn.execute(f"SELECT count(*) FROM {schema}.party_boards_pub_party_board_pages").fetchone()[0]
    conn.rollback()
    assert n == len(filled["roles"]) and m == len(filled["pages"])
