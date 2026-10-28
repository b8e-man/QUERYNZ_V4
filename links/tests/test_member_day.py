"""Ruling 116 (28 October 2026): a speech turn, a written question's asker
and minister, a Beehive release's minister and a diary release's minister,
read into `links.rows` with their titles off, and `member-on-the-day@1`,
which confirms each to the one member sitting in the House on the row's day.
Fast tests on the reading and the rule; slow tests on the live published
rows through the read login (nothing written), which fail when a title is
kept or the day ignored, and on the real engine (a sample-database schema,
rolled back) for the build step, check item 10 and measurement 11."""
import datetime as dt
import os

import pytest

import links
from links import rows, rules

D = dt.date
VIEWS = {"hansard_speeches": "hansard", "parliament_written_questions": "parliament", "beehive_release_ministers": "beehive",
         "minister_diary_releases": "ministers_diaries"}


def _rec(register, view, key, name, day=None, role=None, catch=None):
    r = (key, name, None, day, None, None, None, "doc", False, None, None, None) + ((role,) if role else ())
    return rows.row_record(register, view, r, catch)


def _member(key, name, from_on, to_on=None):
    r = _rec("house", "members", key, name, from_on)
    return {"ref": r[0], "key": key, "election": key.split("/")[0], "fl_key": r[10], "full_key": r[11], "has_middle": r[12],
            "from_on": from_on, "to_on": to_on}


def _row(view, name, day, role=None):
    r = _rec(VIEWS[view], view, "k1", name, day, role)
    return {"ref": r[0], "fl_key": r[10], "full_key": r[11], "has_middle": r[12], "day": day, "evidence": {}}


# ── the reading ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("printed, bare", [
    ("Edmonds, Hon Barbara", "Edmonds, Barbara"),
    ("Hipkins, Rt Hon Chris", "Hipkins, Chris"),
    ("Verrall, Hon Dr Ayesha", "Verrall, Ayesha"),
    ("Hon Dr Ayesha Verrall", "Ayesha Verrall"),
    ("Dr The Rt Hon Lockwood Smith", "Lockwood Smith"),
    ("Hon Judith Collins KC", "Judith Collins"),
    ("Hon Judith Collins, KC", "Judith Collins"),
    ("Rt Hon Winston Peters", "Winston Peters"),
    ("Sir Bill English", "Bill English"),
    ("Dame Jenny Shipley", "Jenny Shipley"),
    ("Genter, Hon Julie Anne", "Genter, Julie Anne"),
    ("Hon Brooke van Velden", "Brooke van Velden"),
    # a name that begins like a title keeps it
    ("Hon Damien O'Connor", "Damien O'Connor"),
    ("Drew Smith", "Drew Smith"),
    ("Theresa Sirett", "Theresa Sirett"),
    ("Hon", ""),
])
def test_member_name_takes_every_title_off_wherever_it_sits(printed, bare):
    assert rows.member_name(printed) == bare


def test_the_titles_are_one_list_and_cover_every_form_the_views_print():
    assert {"rt hon", "hon", "dr", "sir", "dame", "the rt hon"} <= set(rows.MEMBER_TITLES)
    assert {"kc", "qc", "mp"} <= set(rows.MEMBER_POST_NOMINALS)


@pytest.mark.parametrize("view, printed", [
    ("hansard_speeches", "Edmonds, Hon Barbara"), ("beehive_release_ministers", "Hon Barbara Edmonds"),
    ("minister_diary_releases", "Rt Hon Barbara Edmonds"), ("parliament_written_questions", "Hon Dr Barbara Edmonds KC")])
def test_each_view_keys_a_titled_member_as_the_members_view_does(view, printed):
    """A mutation that keeps the title turns this red: the key would be 'barbara hon edmonds' or the like."""
    m = _rec("house", "members", "ge-2023/seat/mangere", "EDMONDS, Barbara")
    r = _rec(VIEWS[view], view, "k1", printed, D(2024, 5, 1), "asker" if view == "parliament_written_questions" else None)
    assert (r[4], r[5], r[10], r[18], r[13]) == ("person", printed, m[10], True, None)     # the printed name kept; a politician; no entity
    assert r[9] == m[9] == "barbara edmonds"


def test_a_written_question_is_two_rows_under_its_view_and_key():
    a = _rec("parliament", "parliament_written_questions", "q1", "Hon Chris Bishop", D(2025, 1, 1), "asker")
    m = _rec("parliament", "parliament_written_questions", "q1", "Hon Simeon Brown", D(2025, 1, 1), "minister")
    assert (a[0], a[3], m[0], m[3]) == ("parliament:q1#asker", "q1", "parliament:q1#minister", "q1")
    assert a[20] is None and m[20] is None          # neither is a coupled donor's part


def test_a_title_and_no_name_is_set_aside_with_its_reason():
    catch = {}
    assert _rec("beehive", "beehive_release_ministers", "b1", "Hon", catch=catch) is None
    assert catch == {"a title and no name": 1}


def test_the_four_views_are_sources_under_their_lane_folders_and_politicians():
    regs = {v: r for r, v, _ in rows.SOURCES}
    assert {v: regs.get(v) for v in VIEWS} == VIEWS
    assert set(VIEWS) == set(rows.MEMBER_DAY_VIEWS) and set(VIEWS) <= rows.POLITICIAN_VIEWS
    sql = dict((v, s) for _, v, s in rows.SOURCES)["parliament_written_questions"]
    assert "'asker' AS role" in sql and "'minister'" in sql and "'No Minister'" in sql


# ── the rule ─────────────────────────────────────────────────────────────

HELD = D(2020, 10, 17)
BISHOP_20 = _member("ge-2020/seat/list/national-party/bishop-chris", "BISHOP, Chris", D(2020, 10, 17), D(2023, 10, 14))
BISHOP_23 = _member("ge-2023/seat/hutt-south", "BISHOP, Chris", D(2023, 10, 14))


def test_one_member_sitting_on_the_day_confirms():
    got, j = rules.member_on_the_day(_row("hansard_speeches", "Bishop, Hon Chris", D(2025, 3, 4)), [BISHOP_20, BISHOP_23], HELD)
    assert got == rules.DAY_ONE and [(m, x["grade"]) for m, x in j] == [(BISHOP_23["ref"], "confirmed")]
    assert j[0][1]["rule"] == rules.RULE_MEMBER_DAY == "member-on-the-day@1"
    assert j[0][1]["evidence"]["members_of_the_name"] == 2 and j[0][1]["evidence"]["members_sitting"] == 1


def test_the_day_decides_which_term_and_the_polling_day_is_the_new_term():
    """A mutation that ignores the day turns this red: both terms would fit, and the row would stay near as two."""
    for day, seat in ((D(2022, 1, 5), BISHOP_20), (D(2023, 10, 13), BISHOP_20), (D(2023, 10, 14), BISHOP_23)):
        got, j = rules.member_on_the_day(_row("beehive_release_ministers", "Hon Chris Bishop", day), [BISHOP_20, BISHOP_23], HELD)
        assert (got, [m for m, _ in j]) == (rules.DAY_ONE, [seat["ref"]]), day


def test_two_members_of_the_name_sitting_stay_near_with_the_reason():
    other = _member("ge-2023/seat/list/act-party/bishop-chris", "BISHOP, Chris", D(2023, 10, 14))
    got, j = rules.member_on_the_day(_row("minister_diary_releases", "Hon Chris Bishop", D(2024, 6, 30)), [BISHOP_23, other], HELD)
    assert got == rules.DAY_TWO and {(m, x["grade"], x["reason"]) for m, x in j} == {
        (BISHOP_23["ref"], "near", rules.NEAR_DAY_TWO), (other["ref"], "near", rules.NEAR_DAY_TWO)}


def test_a_member_of_the_name_who_did_not_sit_on_the_day_is_near_as_none():
    belich = _member("ge-2020/seat/list/labour-party/belich-camilla", "BELICH, Camilla", D(2020, 10, 17), D(2023, 10, 14))
    got, j = rules.member_on_the_day(_row("parliament_written_questions", "Camilla Belich", D(2025, 2, 1), "asker"), [belich], HELD)
    assert got == rules.DAY_NONE and [(m, x["grade"], x["reason"]) for m, x in j] == [(belich["ref"], "near", rules.NEAR_DAY_NONE)]


def test_no_member_of_the_name_or_a_day_the_view_does_not_hold_makes_no_link():
    assert rules.member_on_the_day(_row("hansard_speeches", "Hernandez, Francisco", D(2025, 2, 1)), [], HELD) == (rules.DAY_NO_MEMBER, [])
    assert rules.member_on_the_day(_row("parliament_written_questions", "Hon Chris Bishop", D(2019, 2, 1), "minister"),
                                   [BISHOP_20, BISHOP_23], HELD) == (rules.DAY_BEFORE, [])
    assert rules.member_on_the_day(_row("hansard_speeches", "Bishop, Chris", None), [BISHOP_23], HELD) == (rules.DAY_UNDATED, [])


def test_middle_names_that_differ_on_both_take_the_member_out():
    seymour = _member("ge-2023/seat/epsom", "SEYMOUR, David Breen", D(2023, 10, 14))
    assert rules.member_on_the_day(_row("hansard_speeches", "Seymour, Hon David", D(2024, 1, 1)), [seymour], HELD)[0] == rules.DAY_ONE
    assert rules.member_on_the_day(_row("hansard_speeches", "Seymour, David John", D(2024, 1, 1)), [seymour], HELD)[0] == rules.DAY_NO_MEMBER


# ── live, read-only ──────────────────────────────────────────────────────

def _live(sql, args=()):
    from support import db
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        return conn.execute(sql, args).fetchall()


def _live_members():
    out = []
    for key, name, from_on, to_by, ended_on in _live("SELECT key, name, from_on, to_by, ended_on FROM pub.members"):
        out.append(_member(key, name, from_on, ended_on or to_by))
    return out


@pytest.mark.slow
@pytest.mark.parametrize("view", list(VIEWS))
def test_live_rows_of_each_view_find_their_sitting_member(view):
    """Through each view's own source SQL on a fixed slice of live rows, against the live members view: a titled name finds
    its member, nearly every dated row the members view covers confirms, and none finds two. A title kept turns the titled
    rows to no member; the day ignored turns every re-elected member's rows to two."""
    reg, sql = next((r, s) for r, v, s in rows.SOURCES if v == view)
    mem = _live_members()
    held = min(m["from_on"] for m in mem)
    by = {}
    for m in mem:
        by.setdefault(m["fl_key"], []).append(m)
    got, titled = {}, {}
    for r in _live(f"SELECT * FROM ({sql}) q ORDER BY md5(key) LIMIT 3000"):
        rec = rows.row_record(reg, view, r)
        if rec[14] is None or rec[14] < held:
            continue
        row = {"ref": rec[0], "fl_key": rec[10], "full_key": rec[11], "has_middle": rec[12], "day": rec[14], "evidence": {}}
        c, _ = rules.member_on_the_day(row, by.get(rec[10], []), held)
        got[c] = got.get(c, 0) + 1
        if rows.member_name(rec[5]) != rec[5]:
            titled[c] = titled.get(c, 0) + 1
    n = sum(got.values())
    assert n > 500, got
    assert got.get(rules.DAY_TWO, 0) == 0, got
    assert got.get(rules.DAY_ONE, 0) >= 0.85 * n, got
    assert sum(titled.values()) > 100 and titled.get(rules.DAY_ONE, 0) >= 0.9 * sum(titled.values()), titled


@pytest.mark.slow
def test_live_written_question_askers_are_read_from_the_title():
    reg, sql = next((r, s) for r, v, s in rows.SOURCES if v == "parliament_written_questions")
    got = _live(f"SELECT q.key, q.name, w.title FROM ({sql}) q JOIN pub.parliament_written_questions w ON w.key = q.key "
                f"WHERE q.role = 'asker' ORDER BY md5(q.key) LIMIT 2000")
    assert len(got) == 2000
    for key, name, title in got:
        assert title.split(". ", 1)[1].startswith(name + " to the "), key


# ── the build, check item 10 and measurement 11 on the real engine ───────

class _NoCommit:
    def __init__(self, conn):
        self.conn = conn

    def commit(self):
        pass

    def __getattr__(self, name):
        return getattr(self.conn, name)


@pytest.mark.slow
def test_the_build_confirms_by_name_and_day_and_check_ten_goes_red_on_planted_faults():
    import support.db as db
    from links import build, check, measure
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    s = "scratch_links_member_day_test"
    members = [("ge-2020/seat/hutt-south", "BISHOP, Chris", "2020-10-17", "2023-10-14"), ("ge-2023/seat/hutt-south", "BISHOP, Chris", "2023-10-14", None),
               ("ge-2020/seat/list/labour-party/belich-camilla", "BELICH, Camilla", "2020-10-17", "2023-10-14")]
    view_rows = [("hansard", "hansard_speeches", "2025-03-04/1/1", "Bishop, Hon Chris", "2025-03-04", None),
                 ("parliament", "parliament_written_questions", "q1", "Camilla Belich", "2025-02-01", "asker"),
                 ("parliament", "parliament_written_questions", "q1", "Hon Chris Bishop", "2025-02-01", "minister"),
                 ("parliament", "parliament_written_questions", "q2", "Hon Chris Bishop", "2019-02-01", "minister"),
                 ("beehive", "beehive_release_ministers", "https://b/r#minister/1", "Hon Chris Bishop", "2023-10-14", None),
                 ("ministers_diaries", "minister_diary_releases", "d1.pdf", "Hon Chris Bishop", "2022-05-31", None)]
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        conn = _NoCommit(raw)
        try:
            conn.execute(f"CREATE SCHEMA {s}")
            conn.execute(links.ddl(s))
            conn.execute("CREATE TEMP TABLE members_116 (key text, election text, name text, from_on date, to_by date, ended_on date)")
            with conn.cursor() as w:
                for key, name, f, t in members:
                    w.execute("INSERT INTO members_116 VALUES (%s, %s, %s, %s, %s, NULL)", (key, key.split("/")[0], name, f, t))
                    rec = _rec("house", "members", key, name, D.fromisoformat(f))
                    w.execute(f"INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key, fl_key, full_key, "
                              f"has_middle, entity_ref, started_on, ended_on, election, electorate, politician, document, part_of) "
                              f"VALUES ({', '.join(['%s'] * 21)})", rec)
                for reg, view, key, name, day, role in view_rows:
                    rec = _rec(reg, view, key, name, D.fromisoformat(day), role)
                    w.execute(f"INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key, fl_key, full_key, "
                              f"has_middle, entity_ref, started_on, ended_on, election, electorate, politician, document, part_of) "
                              f"VALUES ({', '.join(['%s'] * 21)})", rec)
            got = build.member_day_links(conn, s, members="members_116")
            assert got["rows"] == {"hansard_speeches": {rules.DAY_ONE: 1}, "parliament_written_questions#asker": {rules.DAY_NONE: 1},
                                   "parliament_written_questions#minister": {rules.DAY_ONE: 1, rules.DAY_BEFORE: 1},
                                   "beehive_release_ministers": {rules.DAY_ONE: 1}, "minister_diary_releases": {rules.DAY_ONE: 1}}
            stored = {(a, b): (g, r) for a, b, g, r in conn.execute(f"SELECT row_a, row_b, grade, reason FROM {s}.links").fetchall()}
            assert stored == {
                ("hansard:2025-03-04/1/1", "house:ge-2023/seat/hutt-south"): ("confirmed", None),
                ("house:ge-2020/seat/list/labour-party/belich-camilla", "parliament:q1#asker"): ("near", rules.NEAR_DAY_NONE),
                ("house:ge-2023/seat/hutt-south", "parliament:q1#minister"): ("confirmed", None),
                ("beehive:https://b/r#minister/1", "house:ge-2023/seat/hutt-south"): ("confirmed", None),       # the polling day: the new term
                ("house:ge-2020/seat/hutt-south", "ministers_diaries:d1.pdf"): ("confirmed", None)}
            assert check.check_ruling_116(conn, s, members="members_116")[0]["ok"], check.check_ruling_116(conn, s, members="members_116")
            m = measure.m11_ruling_116(conn, s)
            assert m["rows"]["parliament_written_questions#minister"] == {"rows": 2, rules.DAY_ONE: 1, rules.DAY_BEFORE: 1}
            assert m["finding_none"]["parliament_written_questions#asker"] == [["Camilla Belich", 1]]
            assert m["confirmed_pairs"]["hansard_speeches"] == [["Bishop, Hon Chris", "BISHOP, Chris", "ge-2023/seat/hutt-south", "2025-03-04"]]

            def ok():
                return check.check_ruling_116(conn, s, members="members_116")[0]

            # planted: the member's term ends before the turn's day (a rule that ignored the day would have confirmed it)
            conn.execute("UPDATE members_116 SET to_by = '2024-01-01' WHERE key = 'ge-2023/seat/hutt-south'")
            assert ok()["member_not_sitting_on_the_day"] == 2 and not ok()["ok"]
            conn.execute("UPDATE members_116 SET to_by = NULL WHERE key = 'ge-2023/seat/hutt-south'")
            assert ok()["ok"]
            # planted: a second member of the name sitting on the day
            conn.execute("INSERT INTO members_116 VALUES ('ge-2023/seat/list/x/bishop-chris', 'ge-2023', 'BISHOP, Chris', '2023-10-14', NULL, NULL)")
            rec = _rec("house", "members", "ge-2023/seat/list/x/bishop-chris", "BISHOP, Chris", D(2023, 10, 14))
            conn.execute(f"INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key, fl_key, full_key, "
                         f"has_middle, entity_ref, started_on, ended_on, election, electorate, politician, document, part_of) "
                         f"VALUES ({', '.join(['%s'] * 21)})", rec)
            assert ok()["another_member_of_the_name_sitting"] == 3 and not ok()["ok"]
            conn.execute(f"DELETE FROM {s}.rows WHERE ref = %s", (rec[0],))
            conn.execute("DELETE FROM members_116 WHERE key = 'ge-2023/seat/list/x/bishop-chris'")
            assert ok()["ok"]
            # planted: a row confirmed to a member of another name, and to two members
            conn.execute(f"""INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade) VALUES
                ('hansard:2025-03-04/1/1', 'house:ge-2020/seat/list/labour-party/belich-camilla', %s, '{{}}', 'confirmed')""",
                         (rules.RULE_MEMBER_DAY,))
            r = ok()
            assert (r["not_a_member_of_the_row_s_name"], r["rows_confirmed_to_two_members"], r["ok"]) == (1, 1, False)
        finally:
            raw.rollback()
