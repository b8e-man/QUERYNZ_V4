"""Ruling 114 (28 October 2026): the eight people views the lane left out,
read into `links.rows` as the existing sources are. Fast tests on the
reading; slow tests on the live published rows through the read login
(nothing written), which fail when a view's name parts are read in the
wrong order, and which hold the lane's keys equal to the board's fold
(`products/board/collapse.py` `row_name_keys`, copied here: links may not
import products)."""
import re

import pytest

from keys import names as kn
from links import rows

NEW_VIEWS = ("charity_officers", "gazette_celebrants", "gazette_practitioners", "limited_partnership_partners", "party_board_roles",
             "local_election_returns", "building_practitioner_decisions", "councillor_interests")


def _source(view):
    return next((reg, sql) for reg, v, sql in rows.SOURCES if v == view)


def _rec(view, key, name, first=None, middle=None, last=None, suppressed=False, entity=None, catch=None):
    return rows.row_record(_source(view)[0], view, (key, name, entity, None, None, None, None, "doc", suppressed, first, middle, last), catch)


def test_the_eight_views_are_read_once_each_under_their_lane_folders():
    regs = {v: r for r, v, _ in rows.SOURCES}
    assert {v: regs.get(v) for v in NEW_VIEWS} == {
        "charity_officers": "charities", "gazette_celebrants": "gazette", "gazette_practitioners": "gazette",
        "limited_partnership_partners": "limited_partnerships", "party_board_roles": "party_boards",
        "local_election_returns": "local_elections", "building_practitioner_decisions": "building_practitioners",
        "councillor_interests": "councillor_interests"}
    for v in ("charity_officers", "limited_partnership_partners"):
        assert "WHERE kind = 'person'" in _source(v)[1], v          # the view's own type column says who is a person
    assert "'charities:' || charity_key" in _source("charity_officers")[1]
    assert "'limited_partnerships:' || partnership_key" in _source("limited_partnership_partners")[1]
    assert "'parties:' || party" in _source("party_board_roles")[1]
    assert {"local_election_returns", "councillor_interests"} <= rows.POLITICIAN_VIEWS


def test_a_celebrant_is_read_given_names_then_surname_from_its_two_fields():
    r = _rec("gazette_celebrants", "c1", "Jāne Mary HART", "Jāne Mary", None, "HART")
    assert (r[0], r[4], r[6], r[7], r[8]) == ("gazette:c1", "person", "Jāne", "Mary", "HART")
    assert (r[10], r[11], r[12]) == ("jane hart", "jane mary hart", True)
    # a two-word surname stays a surname
    s = _rec("gazette_celebrants", "c2", "Anna van der BERG", "Anna", None, "van der BERG")
    assert (s[8], s[10]) == ("van der BERG", "anna van der berg")


def test_a_charity_officer_and_a_partner_are_read_from_their_parts_with_the_entity():
    r = _rec("charity_officers", "charities/officers/1", "Graeme Richard Hart", "Graeme", "Richard", "Hart", entity="charities:charities/CC1")
    assert (r[0], r[10], r[11], r[13]) == ("charities:charities/officers/1", "graeme hart", "graeme richard hart", "charities:charities/CC1")
    p = _rec("limited_partnership_partners", "lp/1", "Hazel JONES", "Hazel", None, "JONES")
    assert (p[1], p[10], p[12]) == ("limited_partnerships", "hazel jones", False)


def test_a_local_candidate_as_the_council_lists_the_return():
    r = _rec("local_election_returns", "l1", "McAULEY, Graeme (Horace)")
    assert (r[10], r[18]) == ("graeme mcauley", True)                         # surname first, nickname off; a politician
    assert _rec("local_election_returns", "l2", "YUNG, Karen (Kaz) (Independent)")[10] == "karen yung"


def test_a_suppressed_withheld_bracketed_or_bare_initial_name_gets_no_row():
    catch = {}
    assert _rec("building_practitioner_decisions", "b1", "Smith", suppressed=True, catch=catch) is None
    assert _rec("local_election_returns", "l3", "(combined)", catch=catch) is None
    assert _rec("gazette_practitioners", "g1", "J.", catch=catch) is None
    assert _rec("charity_officers", "o1", "name suppressed", catch=catch) is None
    assert catch == {"suppressed or withheld": 2, "no name": 1, "a bare initial": 1}
    assert _rec("building_practitioner_decisions", "b2", "Smith")[9] == "smith"   # a surname alone is a name, keyed, never confirming
    assert _rec("gazette_practitioners", "g2", "JO")[9] == "jo"


# ── the live rows (read login, nothing written) ─────────────────────────────

def _live(sql, args=()):
    from support import db
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        return conn.execute(sql, args).fetchall()


def board_keys(whole=None, first=None, middle=None, last=None):
    """The board's fallback key (products/board/collapse.py row_name_keys, 28 October 2026), copied: (fl, full, has_middle)
    from a row's first declared Name, by parts or as a whole; None where it names nobody or carries an organisation word."""
    bracketed = re.compile(r"\s*\([^()]*\)")

    def key_fold(s):
        return " ".join(kn.fold_diacritics(s or "").lower().replace("'", "").replace("’", "").split())
    if whole is not None:
        text = whole
    else:
        text = " ".join(p for p in (first or "", middle or "", last or "") if p)
    if not text.strip() or text.strip().lower() == "name suppressed" or kn.ORG_WORDS.search(text):
        return None
    if whole is not None:
        n = kn.person_name(bracketed.sub("", text))
        given, mid, family = n.given, n.middle, n.family
    else:
        givens = kn.squash(bracketed.sub("", f"{first or ''} {middle or ''}")).split()
        given, mid, family = (givens[0] if givens else ""), " ".join(givens[1:]), kn.squash(last or "")
    fl = key_fold(f"{given} {family}") if given and family else None
    full = key_fold(" ".join(p for p in (given, mid, family) if p)) or None
    return fl, full, bool(mid)


def _read_live(view, limit=400):
    """The view's own source SQL, as the gather runs it, on a fixed slice of live rows → {key: record}."""
    reg, sql = _source(view)
    out = {}
    for r in _live(f"SELECT * FROM ({sql}) q ORDER BY 1 LIMIT {limit}"):
        rec = rows.row_record(reg, view, r)
        if rec:
            out[r[0]] = rec
    return out


@pytest.mark.slow
def test_live_celebrants_key_given_name_then_surname_and_agree_with_the_board():
    """Fails when the source reads a celebrant's surname as the given name: the keys are checked against the
    view's own two fields, read apart from the source's SQL."""
    got = _read_live("gazette_celebrants")
    assert len(got) > 300
    fields = {k: (g, s) for k, g, s in _live("SELECT key, given_names, surname FROM pub.gazette_celebrants WHERE key = ANY(%s)", (list(got),))}
    agree = 0
    for key, rec in got.items():
        given, surname = fields[key]
        first_given = kn.squash(re.sub(r"\s*\([^()]*\)", "", given or "")).split()[0]
        assert rec[6] == first_given and rec[8] == kn.squash(surname), key
        assert rec[10] == " ".join(kn.fold_diacritics(f"{first_given} {kn.squash(surname)}").lower().replace("'", "").split()), key
        b = board_keys(first=given, last=surname)
        if b is not None and rec[4] == "person":
            assert (rec[10], rec[11], rec[12]) == b, key
            agree += 1
    assert agree > 300


@pytest.mark.slow
def test_live_charity_officers_agree_with_the_board_and_carry_their_charity():
    got = _read_live("charity_officers")
    assert len(got) > 300
    fields = {k: (f, m, l, c) for k, f, m, l, c in _live(
        "SELECT key, first_name, middle_name, last_name, charity_key FROM pub.charity_officers WHERE key = ANY(%s)", (list(got),))}
    agree = 0
    for key, rec in got.items():
        f, m, l, charity = fields[key]
        assert rec[13] == f"charities:{charity}", key
        b = board_keys(first=f, middle=m, last=l)
        if b is not None and rec[4] == "person":
            assert (rec[10], rec[11], rec[12]) == b, key
            agree += 1
    assert agree > 300


@pytest.mark.slow
def test_live_body_partners_and_body_officers_are_never_person_rows():
    reg, sql = _source("limited_partnership_partners")
    n_sql = _live(f"SELECT count(*) FROM ({sql}) q")[0][0]
    persons, bodies = _live("SELECT count(*) FILTER (WHERE kind = 'person'), count(*) FILTER (WHERE kind <> 'person') FROM pub.limited_partnership_partners")[0]
    assert n_sql == persons and bodies > 0
    reg, sql = _source("charity_officers")
    n_sql = _live(f"SELECT count(*) FROM ({sql}) q")[0][0]
    persons, bodies = _live("SELECT count(*) FILTER (WHERE kind = 'person'), count(*) FILTER (WHERE kind <> 'person') FROM pub.charity_officers")[0]
    assert n_sql == persons and bodies > 0
