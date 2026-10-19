"""The house lane's tests (step 4.1). The readers' rules are tested on
small pages shaped like the Commission's (names invented); the filled
sample (the lane's whole input) is tested against the row contract, the
catch log, the windows and the outside check, and the check is shown to
fail when a row is lost. No model is called."""
import datetime as dt
import os

import pytest

from support import db, lane, profiles, rowcontract, sample
from registers.house import check, elections, electorates, nominations, recognise, results

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "house")


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


def test_every_profile_recognition_names_is_proposed_and_every_proposed_one_is_recognised():
    proposed = profiles.current(os.path.join(LANE, "profile-proposed.jsonl"))
    shipped = profiles.current()
    have = {s for s in recognise.PROFILES if s in proposed or s in shipped}
    assert have == set(recognise.PROFILES)
    assert set(proposed) <= set(recognise.PROFILES)


# --- the readers, on invented pages -----------------------------------------------

def _electorate(rows, cand_total, cand_inf=3, party_total=None, title="Example Central"):
    body = "".join(f'<tr><td><div class="item odd"><span>{c}</span><span class="float-right">{v}</span></div></td>'
                   f'<td><div class="item odd"><span>{p}</span><span class="float-right">{pv}</span></div></td></tr>'
                   for c, v, p, pv in rows)
    tail = (f'<tr><td><div class="item sub-total"><label>Candidate Informals:</label><span class="float-right">{cand_inf}'
            f'</span></div></td><td><div class="item sub-total"><label>Party Informals:</label><span class="float-right">1'
            f'</span></div></td></tr><tr><td><div class="item"><label class="bold">TOTAL:</label><span class="float-right">'
            f'{cand_total}</span></div></td><td><div class="item"><label class="bold">TOTAL:</label>'
            f'<span class="float-right">{party_total or 0}</span></div></td></tr>')
    return (f'<h2>{title} - Official Result</h2><table id="electorate_details_table"></table>'
            f'<table id="partyCandidatesResultsTable"><tbody>{body}{tail}</tbody></table>').encode()


def test_a_candidate_row_carries_the_party_printed_beside_it_and_party_only_rows_are_not_candidates():
    page = _electorate([("EXAMPLE, Jo", "100", "Example Party", "90"), ("SAMPLE, Kim", "50", "", ""),
                        ("", "", "Other Party", "10")], 153, party_total=101)
    e = results.electorate_page(page)
    assert [(c[1], c[2], c[3]) for c in e.candidates] == [("EXAMPLE, Jo", "Example Party", 100), ("SAMPLE, Kim", None, 50)]
    assert e.party_only == [("Other Party", 10)] and e.problems() == []


def test_a_page_that_fails_its_own_total_is_a_problem():
    e = results.electorate_page(_electorate([("EXAMPLE, Jo", "100", "Example Party", "90")], 104))
    assert any("TOTAL 104" in p for p in e.problems())


def test_a_cancelled_poll_is_flagged_and_its_name_kept_clean():
    e = results.electorate_page(_electorate([("EXAMPLE, Jo (poll cancelled)", "0", "Example Party", "9")], 0, 0, 10))
    assert e.candidates[0][1] == "EXAMPLE, Jo" and e.candidates[0][4] is True


def test_the_successful_candidates_page_reads_party_seat_and_electorate():
    page = ('<table id="successful_candidates_table"><tbody><tr><td><h3>Example Party</h3></td><td></td></tr>'
            '<tr><td><div>EXAMPLE, Jo</div></td><td>List Seat</td></tr>'
            '<tr><td><div>SAMPLE, Kim</div></td><td><div><a href="./electorate-details-07.html">Example Central '
            'Electorate</a></div></td></tr></tbody></table>').encode()
    assert results.successful(page) == [("Example Party", "EXAMPLE, Jo", "List Seat", None),
                                        ("Example Party", "SAMPLE, Kim", "Example Central", 7)]


def test_the_index_reads_polling_days_and_sets_aside_an_undated_link():
    page = ('<h3>General Elections</h3><ul><li><a href="electionresults_2023/">2023 General Election - 14 October 2023'
            '</a></li><li><a href="x/">Election results prior to 1994</a></li></ul><h3>By-elections</h3><ul><li>'
            '<a href="2025_x/">2025 Tāmaki Makaurau By-election - 6 September 2025</a></li>'
            '<li><a href="y/">2024 Example By-election - 31 February 2024</a></li></ul>').encode()
    got, aside = elections.index(page)
    assert [(e.key, e.polled_on) for e in got] == [("ge-2023", "2023-10-14"), ("be-2025-tamaki-makaurau", "2025-09-06")]
    assert len(aside) == 2 and "not a real day" in aside[1][1]


def test_an_electorate_joins_stats_nz_exactly_or_folded_and_never_by_abbreviation():
    stats = [("1", "Example Central", "general"), ("2", "Ōtaki", "general"), ("3", "Mount Example", "general")]
    got = electorates.join(["Example Central", "Otaki", "Mt Example"], stats)
    assert got["Example Central"][3] == "exact" and got["Otaki"][1] == "Ōtaki" and "Mt Example" not in got


def test_the_list_and_electorate_join_takes_the_same_name_or_a_unique_surname_and_first_name():
    ele = [(2, "EXAMPLE, Jo", "A", "Example Party"), (3, "SAMPLE, Kim Lee", "B", "Example Party"),
           (4, "TWIN, Ana", "C", "Example Party"), (5, "TWIN, Ana Maria", "D", "Example Party")]
    lists = [("Example Party", 1, "EXAMPLE, Jo"), ("Example Party", 2, "SAMPLE, Kim"), ("Example Party", 3, "TWIN, Ana B")]
    joined, used = nominations.join(ele, lists)
    assert joined[2] == (0, "name") and joined[3][1].startswith("surname and first given name")
    assert 4 not in joined and 5 not in joined and used == {0, 1}


def test_a_pdf_pair_needs_a_surname_in_capitals():
    pairs = nominations.pdf_pairs(["   1 EXAMPLE, Jo                12 van DONGEN, Ann\n 3 Page 2, of 4"])
    assert pairs == [(1, "EXAMPLE, Jo"), (12, "van DONGEN, Ann")]


def test_a_challenged_page_and_a_browser_error_are_failed_reads():
    assert recognise.recognise(b"<html><title>Attention Required! | Cloudflare</title>cf-error-details", "x.html")[0] == "challenge"
    assert recognise.recognise(b"<!-- fetch error: Page.goto: net::ERR -->", "x.html")[0] == "fetch-error"
    assert recognise.recognise(b"<html><p>hello</p></html>", "x.html")[0] is None


# --- the check, on invented rows ---------------------------------------------------

def _fig(e, what, party, v, key):
    return {"election": e, "what": what, "party": party, "value": v, "key": key}


def test_the_seat_check_fails_when_a_member_is_missing():
    members = [{"election": "ge-1", "party": "Example Party", "route": "list"},
               {"election": "ge-1", "party": "Example Party", "route": "electorate"}]
    figs = [_fig("ge-1", "total seats", "Example Party", 2, "ge-1/seats/example/total"),
            _fig("ge-1", "list seats", "Example Party", 1, "ge-1/seats/example/list")]
    assert check.failed(check.compare([], members, [], figs)) == []
    assert check.failed(check.compare([], members[:1], [], figs))


def test_the_nominations_check_fails_when_a_list_only_candidate_is_missing():
    cands = [{"election": "ge-1", "party": "Example Party", "electorate": "e", "list_place": 1},
             {"election": "ge-1", "party": "Example Party", "electorate": None, "list_place": 2}]
    figs = [_fig("ge-1", "candidates", None, 2, "ge-1/nominations/candidates"),
            _fig("ge-1", "list_only", None, 1, "ge-1/nominations/list-only"),
            _fig("ge-1", "list candidates", "Example Party", 2, "ge-1/nominations/example/list")]
    assert check.failed(check.compare(cands, [], [], figs)) == []
    assert len(check.failed(check.compare(cands[:1], [], [], figs))) == 3


# --- the filled sample (the whole input) --------------------------------------------

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_house"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    schema = _schema()
    sample.fill_schema(schema, lambda: db.connect(db.OWNER_KEY, "querynz_v4_sample"), REPO, log=lambda *a: None)
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        def q(t):
            cur = conn.execute(f"SELECT * FROM {schema}.house_{t}")
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        yield {"schema": schema, "conn": conn, **{t: q(t) for t in
               ("elections", "electorates", "candidates", "members", "figures", "files", "set_aside")}}


def test_every_file_is_read_held_or_a_catch_log_line(filled):
    files = filled["files"]
    assert len(files) == 167
    failed = [f for f in files if f["status"] in ("failed read", "not recognised")]
    capture_lines = [a for a in filled["set_aside"] if a["stage"] == "capture"]
    assert len(failed) == len(capture_lines) == 6
    assert not [f for f in files if f["status"] == "not recognised"]


def test_every_read_results_page_is_an_electorate_and_its_candidates_reconcile(filled):
    pages = {f["document"] for f in filled["files"] if f["kind"] == "ec-results-electorate-page"}
    held = [e for e in filled["electorates"] if e["election"] in ("ge-2020", "ge-2023") and e["result_held"]]
    assert len(pages) == len(held) == 142
    unheld = [e["key"] for e in filled["electorates"] if e["election"] in ("ge-2020", "ge-2023") and not e["result_held"]]
    lines = {a["item"] for a in filled["set_aside"] if a["stage"] == "results"}
    assert sorted(unheld) == ["ge-2020/mana", "ge-2020/rongotai"] and set(unheld) <= lines
    for e in held:
        if e["poll_cancelled"]:
            continue
        votes = sum(c["votes"] for c in filled["candidates"] if c["electorate"] == e["key"])
        assert votes + e["candidate_informals"] == e["candidate_total"], e["key"]


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("elections", "electorates", "candidates", "members", "figures"):
        for r in filled[t]:
            row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
            row["loaded_at"] = r["loaded_at"].isoformat()
            row["filed"] = {k: (v.isoformat() if v else None) for k, v in r.items()
                            if k.endswith(("_on", "_by")) and not isinstance(v, bool)}
            assert rowcontract.validate(row, today) == [], (t, r["key"])
    for t in ("candidates", "members"):
        assert not set(filled[t][0]) & set(rowcontract.FORBIDDEN_COLUMNS)


def test_the_outside_check_passes_on_the_whole_input(filled):
    out = check.compare(filled["candidates"], filled["members"], filled["electorates"], filled["figures"])
    assert check.failed(out) == []
    assert out["electorates"] == {"ge-2020": (72, 72), "ge-2023": (72, 72)}
    tot = {e: next(r for r in rows if r[1] == "Total" and r[0] == "total seats") for e, rows in out["seats"].items()}
    assert tot["ge-2020"][2:] == (120, 120) and tot["ge-2023"][2:] == (122, 122)
    assert next(r for r in out["nominations"]["ge-2026"] if r[0] == "candidates")[2:] == (530, 530)


def test_the_outside_check_fails_when_one_member_or_one_candidate_is_lost(filled):
    m = [x for x in filled["members"] if x["key"] != "ge-2023/seat/epsom"]
    c = [x for x in filled["candidates"] if not (x["election"] == "ge-2026" and x["electorate"] is None)][1:]
    assert any("ACT New Zealand" in w for w in check.failed(check.compare(filled["candidates"], m, filled["electorates"], filled["figures"])))
    assert len(check.failed(check.compare(c, filled["members"], filled["electorates"], filled["figures"]))) >= 2


def test_each_seat_has_a_window_from_a_stated_polling_day_and_none_is_dated_by_the_load(filled):
    for m in filled["members"]:
        assert m["from_on"] is not None and m["ended_on"] is None, m["key"]
        assert m["to_by"] is None or m["to_by"] > m["from_on"]
    seat = {m["key"]: m for m in filled["members"]}
    assert str(seat["ge-2020/seat/tauranga"]["to_by"]) == "2022-06-18"
    assert str(seat["ge-2023/seat/tamaki-makaurau"]["to_by"]) == "2025-09-06"
    assert str(seat["ge-2020/seat/epsom"]["to_by"]) == "2023-10-14"
    by = seat["be-2025-tamaki-makaurau/seat/tamaki-makaurau"]
    assert by["route"] == "by-election" and by["to_by"] is None and by["party"] == "Te Pāti Māori"


def test_the_missing_by_elections_are_catch_log_lines_not_silence(filled):
    lines = {a["item"] for a in filled["set_aside"] if a["stage"] == "by-elections"}
    assert lines == {"be-2023-port-waikato", "be-2022-hamilton-west", "be-2022-tauranga"}


def test_the_published_views_build_on_the_lane_s_tables(filled):
    from registers.house import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.house_pub_"))
    n = {v: conn.execute(f"SELECT count(*) FROM {schema}.house_pub_{v}").fetchone()[0]
         for v in ("elections", "electorates", "candidates", "members")}
    conn.rollback()
    assert n == {"elections": len(filled["elections"]), "electorates": len(filled["electorates"]),
                 "candidates": len(filled["candidates"]), "members": len(filled["members"])}
