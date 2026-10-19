"""The gazette lane's tests (step 4.1). The celebrant reader's rules are
tested on small texts shaped like the Registrar-General's (every name and
address invented); the filled sample is tested against the row contract,
the catch log, the private address table and the outside check. No model
is called."""
import datetime as dt
import json
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.gazette import celebrants as K
from registers.gazette import check, notices, read

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "gazette")
SIG = "Dated at Wellington this 2nd day of May 2016. JANE EXAMPLE, Registrar-General."
PUB_S8 = ("Pursuant to the provisions of section 8 of the Marriage Act 1955, the following names of marriage celebrants "
          "within the meaning of the said Act are published for general information:")


def _names(r):
    return [(x.surname, x.given_names, x.organisation, x.address) for x in r.records]


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


# --- recognising a celebrant list ---------------------------------------------

def test_a_bankruptcy_list_has_the_shape_and_not_the_subject_word():
    t = "Example, Ann, unemployed.Sample, Bob, retired.Test, Cy, builder.Dated this 1st day of May 2016."
    assert K.recognise("Bankruptcies", t) == []


def test_a_society_named_for_celebrants_is_not_a_list_of_them():
    t = "Pursuant to section 28 of the Incorporated Societies Act 1908, the Example Celebrants Society Incorporated is dissolved."
    assert K.recognise("Dissolution of Incorporated Societies", t) == []


def test_the_title_or_the_head_with_the_act_recognises_it():
    assert K.recognise("Marriage Celebrants for 2016 Notice No. 3", "x")
    assert K.recognise("LIST OF MARRIAGE", PUB_S8 + "Able, Ann, Baptist.")


# --- the shapes ------------------------------------------------------------------

def test_stops_records_run_together_with_their_organisation_and_a_leading_particle():
    r = K.read(PUB_S8 + "Aroha, Mere Ana, Example Church.Brown, Tama, Anglican.du Plessis, Pieter, Baptist." + SIG)
    assert r.mode == "stops" and r.action == "publication" and r.statute == "Marriage Act 1955 s 8"
    assert _names(r) == [("Aroha", "Mere Ana", "Example Church", None), ("Brown", "Tama", "Anglican", None),
                         ("du Plessis", "Pieter", "Baptist", None)]


def test_an_address_list_keeps_every_third_field_private_a_bare_town_included():
    t = ("Pursuant to the provisions of sections 26 and 27 of the Civil Union Act 2004, the following persons have been "
         "appointed as civil union celebrants for the period 24 July 2014 to 31 January 2015:Able, Ann Marie, 1 Example "
         "Street, Exampletown.Baker, Ben, 2A Sample Road, Sampleton, Wellington.Carter, Cy, Exampletown." + SIG)
    r = K.read(t)
    assert r.mode == "address" and r.action == "appointment"
    assert (r.period_from, r.period_to) == ("24 July 2014", "31 January 2015")
    assert [x.organisation for x in r.records] == [None, None, None]
    assert [x.surname for x in r.records] == ["Able", "Baker", "Carter"]
    assert all(x.address for x in r.records)


def test_a_located_field_in_a_list_of_organisations_is_still_private():
    r = K.read(PUB_S8 + "Able, Ann, Baptist.Baker, Ben, Anglican.Carter, Cy, 3 Test Street, Town.Doe, Dee, Methodist." + SIG)
    assert r.mode == "stops"
    assert [(x.organisation, bool(x.address)) for x in r.records] == [
        ("Baptist", False), ("Anglican", False), (None, True), ("Methodist", False)]


def test_a_chain_cuts_at_the_last_word_and_keeps_a_particle_with_the_surname():
    t = ("Pursuant to the provisions of section 11 of the Marriage Act 1955, the following names of marriage celebrants "
         "within the meaning of the said Act are published for general information: Able, Ann Baker, Ben van Dijk, "
         "Carl Doe, Dee Dated at Wellington this 14th day of January 2021. JANE EXAMPLE, Registrar-General.")
    r = K.read(t)
    assert r.mode == "chain" and r.unread == []
    assert [(x.surname, x.given_names) for x in r.records] == [
        ("Able", "Ann"), ("Baker", "Ben"), ("van Dijk", "Carl"), ("Doe", "Dee")]


def test_a_glued_annual_list_under_its_printed_header_cuts_at_the_glue_and_not_inside_mcdonald():
    t = ("This list of marriage celebrants, under the Marriage Act 1955, is published for general information and comes "
         "into force on 31 January 2022.JANE EXAMPLE, Registrar-General.Pursuant to the provisions of sections 8 and 10 "
         "of the Marriage Act 1955, the following persons have been appointed as Marriage Celebrants.Surname, First "
         "Name’Aho, Sione’Ake, MeleAble, Jean PaulMcDonald, Sue (Su)’Uta, Tevita")
    r = K.read(t)
    assert r.action == "annual list" and r.mode == "chain"
    assert [(x.surname, x.given_names) for x in r.records] == [
        ("’Aho", "Sione"), ("’Ake", "Mele"), ("Able", "Jean Paul"), ("McDonald", "Sue (Su)"), ("’Uta", "Tevita")]
    assert {x.split for x in r.records[1:]} == {"glue"}


def test_a_marked_list_is_cut_by_its_letters_and_keeps_them():
    t = ("Pursuant to the provisions of sections 26 and 27 of the Civil Union Act 2004, the persons named in the list with "
         "a “CU” before his or her name have been appointed as civil union celebrants for the period 1 May 2019 to 30 April "
         "2020.CU = Civil Union Celebrant M = Independent Marriage Celebrant M CU Able, Ann M Baker, Ben Carl M, CU van "
         "Dijk, Dee" + SIG)
    r = K.read(t)
    assert r.mode == "marked" and r.unread == []
    assert [(x.surname, x.given_names, x.marks) for x in r.records] == [
        ("Able", "Ann", "M CU"), ("Baker", "Ben Carl", "M"), ("van Dijk", "Dee", "M CU")]


def test_a_marked_list_that_prints_addresses_is_set_aside_whole():
    t = ("CU = Civil Union Celebrant M = Independent Marriage Celebrant M CU Able, Ann, 12 Example Street, Town M Baker, "
         "Ben, 3 Test Road, Town" + SIG)
    r = K.read(t)
    assert r.mode == "marked" and r.records == [] and r.unread[0][0] == "list"


def test_a_printed_table_is_set_aside_whole():
    r = K.read("LIST OF MARRIAGE CELEBRANTS Name of Celebrant Name of Organisation Able, Ann Bee Methodist Baker, Ben Baptist")
    assert r.mode == "table" and r.records == [] and r.unread


def test_an_address_list_with_no_stops_is_set_aside_not_guessed():
    t = (PUB_S8 + " Able, Ann, 12 Example Street, Town Baker, Ben, 3 Test Road, Town " + SIG)
    r = K.read(t)
    assert r.records == [] and r.unread and r.unread[0][0] == "list"


# --- the action ------------------------------------------------------------------

def test_the_action_is_the_notice_s_own_words():
    rem = "it is hereby notified that the following names will be removed from the list of marriage celebrants"
    app = "the following persons have been appointed as civil union celebrants"
    pub = "are published for general information"
    assert K.action(rem) == "removal" and K.action(app) == "appointment" and K.action(pub) == "publication"
    assert K.action(app + ". This list is published for general information") == "annual list"
    assert K.action(rem + app) is None


def test_a_list_that_removes_and_appoints_gives_no_rows_only_a_catch_log_line():
    t = ("Pursuant to section 13 of the Marriage Act 1955, the following names will be removed from the list of marriage "
         "celebrants and the following persons have been appointed:Able, Ann, Baptist.Baker, Ben, Anglican.Carter, Cy, Methodist." + SIG)
    line = {"notice": "2016-go9", "article": "a", "old_article": "a", "url": "u", "title": "Marriage Celebrants for 2016 Notice No. 9",
            "published_on": "2016-05-05", "posted_on": "2016-05-05", "old_type": "celebrant", "text": t}
    res = read.read((json.dumps(line) + "\n").encode(), "0" * 64)
    assert res.celebrants == [] and res.notices[0]["filed"]["status"] == "set aside"
    assert any(stage == "celebrants" and "more than one thing" in why for _, stage, why in res.set_aside)


# --- the notices -----------------------------------------------------------------

def test_the_number_is_the_gazette_s_own_and_a_second_capture_is_set_aside():
    assert notices.number("2025-go7375") == (2025, "go", 7375) and notices.number("x") is None
    a = {"notice": "2025-pn1", "article": "a", "old_article": "b"}
    b = {"notice": "2025-pn1", "article": "b", "old_article": "b"}
    kept, others = notices.pick([a, b])
    assert kept is b and [o for o, _ in others] == [a] and "old classifier" in others[0][1]


def test_the_reading_reconciles_and_keys_are_stable_across_reads():
    t = PUB_S8 + "Able, Ann, Baptist.Baker, Ben, Anglican.Carter, Cy, Methodist." + SIG
    base = {"url": "u", "published_on": "2016-05-05", "posted_on": None, "old_type": None}
    lines = [{**base, "notice": "2016-go1", "article": "a", "old_article": "a", "title": "Marriage Celebrants for 2016 Notice No. 1", "text": t},
             {**base, "notice": "2016-go1", "article": "z", "old_article": "a", "title": "Marriage Celebrants for 2016 Notice No. 1", "text": t + " "},
             {**base, "notice": "2016-al2", "article": "c", "old_article": "c", "title": "Example Limited (in liquidation)", "text": "Notice of Appointment of Liquidator"}]
    data = ("\n".join(json.dumps(l) for l in lines) + "\n").encode()
    one, two = read.read(data, "0" * 64), read.read(data, "0" * 64)
    assert one.counts["notices"] == 2 and one.counts["captured_twice"] == 1 and one.counts["celebrants"] == 3
    assert [r["key"] for r in one.celebrants] == [r["key"] for r in two.celebrants]
    assert {r["filed"]["format"] for r in one.notices} == {"gazette-celebrant-list", "not read"}
    assert read.read(data, "0" * 64, only={"2016-al2"}).counts["notices"] == 1


# --- the outside check -------------------------------------------------------------

def test_the_check_fails_on_a_numbered_celebrant_notice_the_lane_did_not_read():
    rows = [(f"{y}-al1", "Example Limited", "not read") for y in range(check.CLOSED_FROM, check.CLOSED_TO + 1)]
    good = rows + [("2016-go5", "Marriage Celebrants for 2016 Notice No. 2", check.CELEBRANT)]
    assert check.failed(check.figures(good)) == []
    bad = good + [("2016-go9", "Marriage Celebrants for 2016 Notice No. 3", "not read")]
    assert any("2016-go9" in w for w in check.failed(check.figures(bad)))
    assert any("2003" in w for w in check.failed(check.figures([r for r in good if not r[0].startswith("2003")])))
    f = check.figures(good)
    assert f["celebrants"][("Marriage", 2016)]["printed"] == 2 and f["celebrants"][("Marriage", 2016)]["held"] == 1


# --- the filled sample ---------------------------------------------------------------

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_gazette"


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
               "notices": q(f"SELECT * FROM {schema}.gazette_notices ORDER BY key"),
               "celebrants": q(f"SELECT * FROM {schema}.gazette_celebrants ORDER BY key"),
               "aside": q(f"SELECT * FROM {schema}.gazette_set_aside"),
               "private": q(f"SELECT key FROM {schema}_private.gazette_celebrant_addresses")}


def test_every_listed_notice_is_held_once_and_the_second_capture_is_a_catch_log_line(filled):
    from registers.gazette import sample as S
    listed = S.notices_of(sample.read_list(os.path.join(LANE, "sample.list")))
    assert {n["notice"] for n in filled["notices"]} == listed
    assert sum(1 for a in filled["aside"] if "captured twice" in a["reason"]) == 1


def test_each_case_reads_as_its_comment_says(filled):
    by = {n["notice"]: n for n in filled["notices"]}
    assert by["2004-go1177"]["status"] == "set aside" and by["2014-go6947"]["status"] == "set aside"
    assert by["2025-al4914"]["format"] == by["2018-ba414"]["format"] == by["2002-is8379"]["format"] == "not read"
    shapes = {}
    for c in filled["celebrants"]:
        shapes.setdefault(c["notice"], set()).add(c["list_shape"])
    assert shapes["2016-go3394"] == {"stops"} and shapes["2007-go3988"] == {"address"}
    assert shapes["2024-go4242"] == {"chain"} and shapes["2022-go134"] == {"chain"} and shapes["2025-go486"] == {"marked"}
    assert {c["action"] for c in filled["celebrants"] if c["notice"] == "2013-go541"} == {"annual list"}
    for n in by.values():
        assert n["records"] == sum(1 for c in filled["celebrants"] if c["notice"] == n["notice"])


def test_an_address_is_private_and_no_published_row_carries_one(filled):
    addressed = {c["key"] for c in filled["celebrants"] if c["list_shape"] == "address"}
    assert addressed and addressed <= {p["key"] for p in filled["private"]}
    assert all(c["organisation"] is None for c in filled["celebrants"] if c["key"] in addressed)
    assert not set(filled["celebrants"][0]) & {"address", "text"}
    assert "text" not in filled["notices"][0]


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("notices", "celebrants"):
        for r in filled[t]:
            row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
            row["loaded_at"] = r["loaded_at"].isoformat()
            row["filed"] = {k: (v.isoformat() if v else None) for k, v in r.items() if k.endswith("_on")}
            assert rowcontract.validate(row, today) == [], (t, r["key"])


def test_the_outside_check_reads_every_numbered_celebrant_notice_in_the_sample(filled):
    f = check.figures([(n["notice"], n["title"], n["format"]) for n in filled["notices"]])
    assert f["celebrants"] and all(c["not_recognised"] == [] for c in f["celebrants"].values())


def test_the_published_views_build_on_the_lane_s_tables(filled):
    from registers.gazette import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.gazette_pub_"))
    n = conn.execute(f"SELECT count(*) FROM {schema}.gazette_pub_gazette_celebrants").fetchone()[0]
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {schema}.gazette_pub_gazette_notices LIMIT 0").description]
    conn.rollback()
    assert n == len(filled["celebrants"]) and "text" not in cols and "old_type" not in cols
