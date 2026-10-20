"""The parties lane's tests (step 4.1). The readers' rules are tested on
small texts shaped like the Commission's (party and person names
invented); the filled sample is tested against the row contract, the catch
log, the four known renames and the outside check. No model is called."""
import datetime as dt
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.parties import check, lifecycle, notices, register

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "parties")
SIG = "Dated at Wellington this 3rd day of May 2021. JANE EXAMPLE, Chief Electoral Officer, Electoral Commission."


def _events(text, nid="2021-au1"):
    got = notices.read(text, nid, "2021-05-04")
    assert got.unread == [], got.unread
    return [(e.kind, e.decided_on, e.name, e.new_name, e.abbreviation) for e in got.events if e.kind != "logo"]


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


# --- the notices -------------------------------------------------------------

def test_a_glued_cancellation_ends_at_the_request_and_drops_the_article():
    t = ("Cancellation of Registration of PartyPursuant to Part 4 of the Electoral Act 1993, the Electoral Commission "
         "resolved on 8 February 2012 to cancel the registration of the Example Partyat the party’s request." + SIG)
    assert _events(t) == [("cancelled", "2012-02-08", "Example Party", None, None)]


def test_a_logo_cancellation_is_not_a_party_cancellation():
    t = ("Pursuant to Part 4 of the Electoral Act 1993, the Electoral Commission resolved on 23 November 2006 to cancel "
         "the registration of the logo ofExample Partyat the party’s request." + SIG)
    got = notices.read(t, "2006-au1")
    assert [e.kind for e in got.events] == ["logo"] and got.unread == []


def test_the_three_shapes_of_a_stated_rename():
    a = ("On 6 April 2022, the Electoral Commission approved an application under Part 4 of the Electoral Act 1993 to "
         "change the party name of the Example Party to the “Example & Freedom Party”. " + SIG)
    b = ("On 12 July 2023, the Electoral Commission approved an application under Part 4 of the Electoral Act 1993 by "
         "the Example Party to change its party name to Te Pāti Tauira. " + SIG)
    c = ("Pursuant to Part 4 of the Electoral Act 1993, the Electoral Commission determined on 6 September 2023 to "
         "substitute the following party name, party abbreviation and logo: New Party Name: Examples New party "
         "abbreviation: EX Previous Party Name: Example Movement Party Secretary: Jane Example The party details and logo can "
         "be viewed at: https://elections.nz/x. " + SIG)
    assert _events(a) == [("renamed", "2022-04-06", "Example Party", "Example & Freedom Party", None)]
    assert _events(b) == [("renamed", "2023-07-12", "Example Party", "Te Pāti Tauira", None)]
    assert _events(c) == [("renamed", "2023-09-06", "Example Movement", "Examples", None),
                          ("abbreviation", "2023-09-06", "Examples", None, "EX")]


def test_one_resolution_may_approve_two_renames():
    t = ("Applications for Name ChangePursuant to Part 4 of the Electoral Act 1993, the Electoral Commission resolved on "
         "15 July 2005 to approve: (a) a change of name of First Party to:Jo Example’s First; and (b) a change of name "
         "of The Second Party Incorporated to: The Second Party for Example." + SIG)
    assert [(e[2], e[3]) for e in _events(t)] == [("First Party", "Jo Example’s First"),
                                                   ("The Second Party Incorporated", "The Second Party for Example")]


def test_a_registration_list_reads_every_entry_and_its_abbreviation_and_not_the_logo_list():
    t = ("Pursuant to Part 4 of the Electoral Act 1993, the Electoral Commission determined on 5 August 2026 to "
         "register the following political parties: Party Name: Example Alliance Party Abbreviation: Example "
         "Alliance Party Secretary: Jane Example &nbsp; &nbsp; Party Name: Free Example Party Secretary: Jo Example "
         "Pursuant to Part 4 of the Electoral Act 1993, the Electoral Commission determined on 5 August 2026 to "
         "register the logos of the following political parties: Party Name: Example Alliance " + SIG)
    assert _events(t) == [("registered", "2026-08-05", "Example Alliance", None, "Example Alliance"),
                          ("registered", "2026-08-05", "Free Example", None, None)]


def test_a_glued_name_ends_where_the_next_block_begins_and_a_signature_is_never_a_name():
    t = ("Pursuant to Part 4 of the Electoral Act 1993, the Electoral Commission determined on 13 May 2014 to register "
         "the following political party and logo: Party Name: Example PartyThe Example Party logo can be viewed at "
         "www.elections.org.nzDated at Wellington this 13th day of May 2014.JANE EXAMPLE, Chief Electoral Officer, "
         "Electoral Commission.")
    u = ("Pursuant to Part 4 of the Electoral Act 1993, the Electoral Commission resolved on 24 June 2011 to register "
         "the following political party: Party Name: MANA Example JANE EXAMPLE, Chief Electoral Officer")
    assert _events(t)[0][2] == "Example Party"
    assert _events(u)[0][2] == "MANA Example", "a capital A begins no new block: 'MANA' stays whole"


def test_a_corrigendum_names_its_notice_and_the_text_it_replaces():
    t = ("In the notice titled Amendment to Register of Political Parties and Logos, published in the New Zealand "
         "Gazette, 28 January 2026, Notice No. 2026-au9 the following text: “New Party Name: The Example Party” is "
         "replaced as “New Party Name: Example Party” " + SIG)
    e = notices.read(t, "2026-au10").events
    assert [(x.kind, x.ref, x.name, x.new_name) for x in e] == [
        ("corrected", "2026-au9", "New Party Name: The Example Party", "New Party Name: Example Party")]


def test_the_year_s_list_registers_with_no_day():
    t = ("Pursuant to the Electoral Act 1993, during the year to date, the following registration changes have been "
         "approvedby the Electoral Commission.The following parties have been registered:First Example;Second "
         "Example Party. A logo or substitute logo has been registered for the following parties:First Example." + SIG)
    assert _events(t) == [("registered", None, "First Example", None, None),
                          ("registered", None, "Second Example Party", None, None)]


def test_a_resolution_the_reader_cannot_read_is_set_aside_never_guessed():
    t = "Pursuant to Part 4 of the Electoral Act 1993, on 1 May 2021 the Electoral Commission amended something new."
    got = notices.read(t, "2021-au2")
    assert got.events == [] and got.unread == [("2021-au2 clause 1", "a resolution the reader could not read")]


# --- the register page -------------------------------------------------------

BLOCK = ('<div class="parties__party-info"><h2>{name}</h2><div><h3>Party registered:</h3> {reg} </div>'
         '<div><h3>Component parties:</h3> None</div><div><h3>Abbreviation:</h3> {abbr}</div>'
         '<div><h3>Logo registered:</h3> 2 August 2019</div>'
         '<div><h3>Party secretary name and contact details:</h3><p>Jane Example<br>Party Secretary<br>'
         '1 Invented Street<br>Sometown 1000</p><p>Ph: 000<br>Email: <a href="mailto:x@example.nz">x@example.nz</a></p>'
         '<p><strong>Deadline for providing financial statements:</strong><br>30 June</p></div>'
         '<div><h3>Website:</h3><a href="https://example.nz/"><span>example.nz<svg><path d="M0"></path></svg></span></a></div>'
         '<div class="parties__party-info__logos"><h3>Previous registered logos:</h3><span>Registered: 30 Sep 2016</span></div></div>')


def _page(*blocks):
    return ("<html><body>" + "".join(BLOCK.format(**b) for b in blocks) +
            '<a href="/assets/pagecomponent-file-files/Register.pdf">Register</a><footer>x</footer></body></html>').encode()


def test_a_page_block_reads_its_fields_and_keeps_the_contact_lines_apart():
    p = register.read(_page({"name": "Example Party", "reg": "17 February 1995", "abbr": "Example (used on the ballot paper)"}))
    e = p.entries[0]
    assert (e.name, e.registered_on, e.abbreviation, e.abbreviation_on_ballot) == ("Example Party", "1995-02-17", "Example", True)
    assert (e.logo_registered_on, e.previous_logos, e.statement_deadline, e.website) == ("2019-08-02", ["2016-09-30"], "30 June", "example.nz")
    assert e.secretary == "Jane Example" and "1 Invented Street" in e.contact
    assert "Invented" not in " ".join(str(v) for k, v in vars(e).items() if k != "contact")


# --- the lifecycle -----------------------------------------------------------

def _ev(kind, on, name, new=None, abbr=None, nid="n", n=1):
    return notices.Event(notice=f"{on[:4] if on else '2008'}-{nid}", ordinal=n, kind=kind, decided_on=on, name=name,
                         new_name=new, abbreviation=abbr)


def _entry(name, reg, n=1, abbr=None):
    return register.Entry(ordinal=n, name=name, registered_on=reg, abbreviation=abbr)


def test_a_renamed_party_is_the_same_registration_and_each_name_has_its_window():
    life = lifecycle.build([_ev("registered", "2017-03-06", "Example Party (EX)"),
                            _ev("renamed", "2026-01-28", "Example Party (EX)", "Example Party", nid="r")],
                           [_entry("Example Party", "2017-03-06")], "2026-10-19")
    (r,) = life.registrations
    names = [(n.name, n.from_on, n.to_on, n.basis) for n in r.names if n.kind == "name"]
    assert names == [("Example Party (EX)", "2017-03-06", "2026-01-28", "registered"), ("Example Party", "2026-01-28", None, "stated")]
    assert (r.page_basis, r.window) == ("name", "same day")


def test_a_party_cancelled_and_registered_again_is_two_registrations():
    life = lifecycle.build([_ev("registered", "2023-08-28", "Example Loyal"), _ev("cancelled", "2024-07-26", "Example Loyal", nid="c"),
                            _ev("registered", "2026-08-05", "Example Loyal", nid="r2")],
                           [_entry("Example Loyal", "2026-08-05")], "2026-10-19")
    assert sorted((r.registered_on, r.cancelled_on, r.entry is not None) for r in life.registrations) == [
        ("2023-08-28", "2024-07-26", False), ("2026-08-05", None, True)]
    assert len({r.key for r in life.registrations}) == 2


def test_a_party_first_met_at_its_cancellation_was_registered_before_the_reach():
    life = lifecycle.build([_ev("cancelled", "2005-05-13", "Old Example")], [], "2026-10-19")
    (r,) = life.registrations
    assert (r.registered_on, r.registered_by, r.cancelled_on) == (None, lifecycle.REACH, "2005-05-13")
    assert r.key.startswith("ec-party/before-2000/")


def test_the_window_joins_a_page_party_the_notices_reach_by_no_name_unique_on_both_sides_or_not_at_all():
    one = lifecycle.build([_ev("registered", "2004-07-09", "Example Party")], [_entry("Te Tauira", "2004-06-24")], "2026-10-19")
    (r,) = one.registrations
    assert (r.page_basis, r.window, r.name) == ("window", "within the gazettal lag", "Te Tauira")
    # scarcity is not identity: two notice registrations fit one page date, so neither is taken
    two = lifecycle.build([_ev("registered", "2023-08-28", "First Example"), _ev("registered", "2023-08-28", "Second Example", nid="b", n=2)],
                          [_entry("Third Example", "2023-08-28")], "2026-10-19")
    assert [r.page_basis for r in two.registrations if r.entry is not None] == ["page only"]
    assert any("two registrations fit" in why for _, _, why in two.set_aside)


def test_a_cancellation_two_live_parties_answer_to_is_set_aside():
    life = lifecycle.build([_ev("registered", "2014-07-24", "Example Party and Other Movement"),
                            _ev("registered", "2014-07-24", "Example Party and Other", nid="b", n=2),
                            _ev("cancelled", "2014-12-18", "Example Party and Other Mov", nid="c")], [], "2026-10-19")
    assert [s for _, s, _ in life.set_aside] == ["lifecycle"]


def test_name_key_folds_the_article_nz_and_a_trailing_party_and_keeps_new():
    k = lifecycle.name_key
    assert k("The Example Party") == k("example party") == k("Example")
    assert k("NZ Example Coalition") == k("New Zealand Example Coalition")
    assert k("New Example") != k("Example Party NZ")


# --- the outside check -------------------------------------------------------

def test_the_check_fails_when_the_page_s_date_is_not_the_notice_s():
    evs = [_ev("registered", "2017-03-06", "Example Party")]
    ok = check.compare(evs, [_entry("Example Party", "2017-03-06")], "2026-10-19")
    bad = check.compare(evs, [_entry("Example Party", "2016-01-01")], "2026-10-19")
    assert ok["differs"] == [] and bad["differs"] == [("Example Party", "2016-01-01", "2017-03-06")]
    assert any("the page says 2016-01-01" in w for w in check.failed(bad))


def test_a_party_logo_cancelled_by_section_70a_is_not_the_party_cancelled():
    t = ("At its meeting on 22 July 2011, the Electoral Commission Board considered the application to cancel a party "
         "logo under Part 4 of the Electoral Act 1993:Cancellation of logo, at the request of the following political "
         "party:Example Party.The Electoral Commission resolved to cancel the registration of the Example Party logo in "
         "accordance with section 70A of the Electoral Act 1993.The Register will be updated accordingly.")
    got = notices.read(t, "2011-au1")
    assert {e.kind for e in got.events} == {"logo"} and got.unread == []
    t2 = ("Pursuant to Part 4 of the Electoral Act 1993, the Electoral Commission resolved on 20 June 2023 to cancel the "
          "registration of the Example Party and its logo, at the party’s request." + SIG)
    assert _events(t2) == [("cancelled", "2023-06-20", "Example Party", None, None)]


# --- the labels --------------------------------------------------------------

def _label_rows():
    """Two registrations of one name a year apart, and a party renamed."""
    regs = {"r/a": {"key": "r/a", "name": "Example Loyal", "registered_on": "2021-03-01", "cancelled_on": "2022-02-01"},
            "r/b": {"key": "r/b", "name": "Example Loyal", "registered_on": "2022-09-01", "cancelled_on": None},
            "r/c": {"key": "r/c", "name": "Te Pāti Tauira", "registered_on": "2004-07-09", "cancelled_on": None}}
    names = [("r/a", "Example Loyal", "name", "2021-03-01", "2022-02-01"),
             ("r/b", "Example Loyal", "name", "2022-09-01", None),
             ("r/c", "Tauira Party", "name", "2004-07-09", "2023-07-12"),
             ("r/c", "Te Pāti Tauira", "name", "2023-07-12", None)]
    rows = [{"party": p, "name": n, "kind": k, "from_on": f, "to_on": to, "registered_on": regs[p]["registered_on"],
             "cancelled_on": regs[p]["cancelled_on"]} for p, n, k, f, to in names]
    return rows, regs


def test_a_label_in_a_name_two_registrations_carried_joins_the_one_live_that_day_and_says_so():
    from registers.parties import labels
    rows, regs = _label_rows()
    a = labels.resolve("Example Loyal", "2021-06-30", rows, regs)
    b = labels.resolve("Example Loyal", "2023", rows, regs)
    assert a["party"] == "r/a" and b["party"] == "r/b"
    assert "2 registrations" in a["same_name"] and "r/a" in a["same_name"] and "r/b" in a["same_name"]
    both = labels.resolve("Example Loyal", "2022", rows, regs)
    assert both["party"] is None and "2 registrations of this name were live within 2022" in both["why"]


def test_a_renamed_party_s_old_name_is_the_same_registration_and_a_bracket_is_tried_both_ways():
    from registers.parties import labels
    rows, regs = _label_rows()
    assert labels.resolve("Tauira Party", "2020", rows, regs)["party"] == "r/c"
    got = labels.resolve("The Tauira Party (Te Pati Tauira)", "2021", rows, regs)
    assert got["party"] == "r/c" and got["basis"].startswith("before its bracket")
    assert labels.resolve("Independent", "2020", rows, regs)["basis"] == "not a party"
    nothing = labels.resolve("Example Freedom", "2020", rows, regs)
    assert nothing["party"] is None and nothing["why"].startswith("no registration live then")


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
    return "scratch_gate_parties"


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
               "regs": q(f"SELECT * FROM {schema}.parties_registrations ORDER BY key"),
               "names": q(f"SELECT * FROM {schema}.parties_names"),
               "events": q(f"SELECT * FROM {schema}.parties_events"),
               "labels": q(f"SELECT * FROM {schema}.parties_labels"),
               "files": q(f"SELECT * FROM {schema}.parties_files"),
               "aside": q(f"SELECT * FROM {schema}.parties_set_aside"),
               "private": q(f"SELECT key FROM {schema}_private.parties_secretary_contacts")}


def test_everything_is_read_and_the_catch_log_holds_only_what_the_old_folder_lost(filled):
    assert [a for a in filled["aside"] if a["stage"] not in ("capture", "labels")] == []
    assert all("not published here" in a["reason"] for a in filled["aside"] if a["stage"] == "labels")
    assert len({e["notice"] for e in filled["events"]}) == 137
    on = [r for r in filled["regs"] if r["on_register"]]
    assert len(on) == 17 and len(filled["private"]) == 17
    assert {f["status"] for f in filled["files"]} == {"read", "held, not read", "read, compared, not cited"}


def test_every_notice_is_the_gazette_lane_s_copy_cited_to_its_document(filled):
    from registers.parties import capture
    assert {e["document"] for e in filled["events"]} == {capture.GAZETTE_EXPORT_SHA}
    assert {e["source_note"] for e in filled["events"]} == {capture.GAZETTE_NOTE}
    assert all(e["place"].startswith(f"notice {e['notice']} resolution ") for e in filled["events"])


def test_the_heartland_cancellation_only_the_gazette_lane_holds_closes_its_registration(filled):
    hit = [r for r in filled["regs"] if lifecycle.name_key(r["name"]) == lifecycle.name_key("Heartland New Zealand Party")]
    assert len(hit) == 1 and str(hit[0]["cancelled_on"]) == "2023-06-20" and hit[0]["off_register_by"] is None
    assert hit[0]["cancelled_place"] == "notice 2023-au2700 resolution 1"


def test_a_logo_cancellation_makes_no_second_registration(filled):
    one = [r for r in filled["regs"] if lifecycle.name_key(r["name"]) == lifecycle.name_key("One New Zealand Party")]
    assert len(one) == 1 and str(one[0]["cancelled_on"]) == "2006-09-27"
    assert len(filled["regs"]) == 77


def test_two_registrations_of_one_name_are_kept_apart_and_say_so(filled):
    loyal = sorted((r for r in filled["regs"] if r["name"] == "New Zealand Loyal"), key=lambda r: r["key"])
    assert len(loyal) == 2 and loyal[0]["same_name_as"] == loyal[1]["key"] and loyal[1]["same_name_as"] == loyal[0]["key"]
    assert "2023-08-28 to 2024-07-26" in loyal[0]["same_name_note"] and "2026-08-05 to now" in loyal[0]["same_name_note"]
    assert all(r["same_name_as"] is None for r in filled["regs"] if lifecycle.name_key(r["name"]) not in (
        "newzealandloyal", "unitedfuturenewzealand"))


def test_every_label_row_reconciles_keeps_the_row_contract_and_says_why_it_joins_nothing(filled):
    today = dt.date.today()
    keys = [r["key"] for r in filled["labels"]]
    assert len(keys) == len(set(keys))
    regs = {r["key"] for r in filled["regs"]}
    for r in filled["labels"]:
        row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
        row["loaded_at"] = r["loaded_at"].isoformat()
        assert rowcontract.validate(row, today) == [], r["key"]
        assert (r["party"] in regs) if r["party"] else bool(r["why"]), r["key"]
        assert r["rows"] == sum(int(p.rsplit(" ", 1)[1]) for p in r["sources"].split("; "))


def test_every_row_keeps_the_row_contract_and_no_contact_line_is_published(filled):
    today = dt.date.today()
    for t in ("regs", "names", "events"):
        for r in filled[t]:
            row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
            row["loaded_at"] = r["loaded_at"].isoformat()
            row["filed"] = {k: (v.isoformat() if v else None) for k, v in r.items() if k.endswith("_on") and not isinstance(v, bool)}
            assert rowcontract.validate(row, today) == [], (t, r["key"])
    cols = set(filled["regs"][0])
    assert not cols & {"contact", "address", "phone", "email"}


def test_the_four_known_renames_are_one_registration_each(filled):
    by_party = {}
    for n in filled["names"]:
        by_party.setdefault(n["party"], set()).add(n["name_key"])
    regs = {r["key"]: r for r in filled["regs"]}
    for old, new in check.KNOWN_RENAMES:
        hit = [regs[p] for p, keys in by_party.items()
               if lifecycle.name_key(old) in keys and regs[p]["on_register"] and lifecycle.name_key(regs[p]["name"]) == lifecycle.name_key(new)]
        assert len(hit) == 1, (old, new)
        assert hit[0]["window"] in ("same day", "within the gazettal lag")
        stated = [n for n in filled["names"] if n["party"] == hit[0]["key"] and n["basis"] == "stated" and n["kind"] == "name"]
        assert stated, f"{new}: the Commission's statement of the change is read"


def test_the_outside_check_passes_on_the_sample(filled):
    from support.docstore.landing import read_bytes
    regs = filled["regs"]
    page = next(r for r in regs if r["register_document"])
    events, pub = check.notices_of({(e["notice"], e["document"]) for e in filled["events"]})
    out = check.compare(events, register.read(read_bytes(page["register_document"])).entries, str(page["register_seen_on"]), pub)
    assert check.failed(out, sum(1 for r in regs if r["on_register"])) == []
    assert len(out["joined"]) + len(out["window"]) + len(out["before_reach"]) + len(out["no_notice_held"]) == out["page"]


def test_the_published_views_build_on_the_lane_s_tables(filled):
    from registers.parties import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.parties_pub_"))
    n = conn.execute(f"SELECT count(*) FROM {schema}.parties_pub_parties").fetchone()[0]
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {schema}.parties_pub_parties LIMIT 0").description]
    conn.rollback()
    assert n == len(filled["regs"]) and "contact" not in cols
