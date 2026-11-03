"""The office notices the appointment reader does not take (offices.py, 2 November 2026): judges and magistrates,
Justices of the Peace lists, Directors of Area Mental Health Services, bodies appointed to control and manage a
reserve, and school boards put under a limited statutory manager or dissolved. Every name, town and street is invented."""
import json

from support import profiles
from registers.gazette import appointments as AP
from registers.gazette import check, read
from registers.gazette import offices as O

SIGNED = "Dated at Wellington this 3rd day of June 2016. ANN EXAMPLE, Attorney-General."

JUDGE = ("Pursuant to section 5 of the District Court Act 2016, Her Excellency the Governor-General has been pleased to "
         "appoint: Bob Cee Sample, Barrister and Solicitor of Exampleton as a District Court Judge, to exercise the civil and "
         "criminal jurisdiction of the court, commencing on 1 July 2016. " + SIGNED)
ACTING = ("Pursuant to section 11 of the District Courts Act 1947, His Excellency the Governor-General has been pleased to "
          "appoint Cara Dee Example, District Court Judgeto retire on 1 May 2016, to be an Acting District Court Judge, at "
          "such places and for such periods only as the Chief District Court Judge may fix, for a term of two years on and "
          "from 2 May 2016. " + SIGNED)
JP_APPOINTED = ("Pursuant to section 3(1) of the Justices of the Peace Act 1957, His Excellency the Governor-General has been "
                "pleased to appoint the following persons to be Justices of the Peace for New Zealand:Example, Ann Bea, 12 "
                "Sample Street, Exampleville, Exampleton.Sample, Bob, Flat 3, 4 Test Road, R.D. 2, Testburgh.Dee, Cara Eve, "
                "Wattle Bush, Fern Road, Gumtree. Dated at Wellington this 1st day of May 2009. ANN EXAMPLE, Secretary for Justice.")
JP_RETIRED = ("It is noted for information that, pursuant to section 3A(1) of the Justices of the Peace Act 1957, I have "
              "authorised the following persons to have the designation Justice of the Peace (“J.P.”) (retired):Ann Bea "
              "Example, of Exampleton.Bob Sample, of Palmerston Test.Dated at Wellington this 1st day of May 2009. ANN "
              "EXAMPLE, Secretary for Justice.")
JP_RUN = ("It is noted for information that Ann Bea Example, of Exampleton Bob Sample, of Testburgh have resigned their "
          "appointments as Justices of the Peace for New Zealand. Dated at Wellington this 1st day of May 2009.")
MH = ("Pursuant to section 92 of the Mental Health (Compulsory Assessment and Treatment) Act 1992, I, Ann Example, "
      "Director-General of Health: Appoint Bob Sample as Director of Area Mental Health Services in respect of the “Example "
      "Regional Forensic Mental Health Service”, and amend the principal notice by omitting the name and title “Cara Dee, "
      "psychiatrist, of Exampleton”, and substituting the name and title “Eve Fay Test, clinical psychologist, of "
      "Exampleton”. Dated at Wellington this 2nd day of March 2026.")
RESERVE = ("Under the Reserves Act 1977, the undersigned appoints the Example Valley Charitable Trust to control and manage the "
           "historic reserve described in the Schedule. Example Land District Schedule 1.0 ha Section 1 Block II Example "
           "Survey District. Dated at Exampleton this 1st day of December 2025. ANN EXAMPLE, Operations Manager.")
RESERVE_REVOKED = ("Under the Reserves Act 1977, the undersigned revokes the appointment of the Example District Council to "
                   "control and manage the reserve described in the Schedule. Dated at Exampleton this 1st day of May 2020.")
LSM = ("Under section 171 of the Education and Training Act 2020, with delegated authority from the Minister of Education, "
       "I hereby direct the appointment of a limited statutory manager for the Example College (25) Board (“Board”). The "
       "following functions are to be vested in the limited statutory manager: all functions of the Board as an employer. "
       "This notice takes effect on 1 October 2022. Dated at Wellington this 26th day of September 2022. ANN EXAMPLE, "
       "Deputy Secretary, Education Services, Ministry of Education.")
LSM_REVOKED = ("Under section 171(4) of the Education and Training Act 2020, with delegated authority from the Minister of "
               "Education, I revoke the Notice of Direction to Appoint a Limited Statutory Manager for the Example College (25) "
               "Board, (as published in the New Zealand Gazette, 29 September 2022, Notice No. 2022-go4000). Dated at "
               "Wellington this 1st day of December 2023. BOB SAMPLE, Deputy Secretary, Ministry of Education.")
DISSOLVED = ("Under section 78N(1) of the Education Act 1989, the Example Street School (Exampleton) (1772) Board of Trustees "
             "is now dissolved and I direct the Group Manager to appoint a commissioner to replace that board. Dated at "
             "Wellington this 2nd day of March 2015. ANN EXAMPLE, Deputy Secretary, Ministry of Education.")


def test_the_families_are_recognised_by_section_and_title_and_never_take_an_appointment_title():
    assert O.family("go", "District Court Judge Appointed") == O.JUDICIAL
    assert O.family("go", "Acting District Court Judges Appointed") == O.JUDICIAL
    assert O.family("go", "Acting Judge of High Court Appointed") == O.JUDICIAL
    assert O.family("go", "Law Commissioner Appointment") == O.JUDICIAL
    assert O.family("go", "Justices of the Peace Appointed") == O.JP
    assert O.family("go", "Corrigendum—Justices of the Peace (Retired)") == O.JP
    assert O.family("go", "Justices of the Peace Resignations") == O.JP
    assert O.family("go", "Amending a Notice—Appointment of Director of Area Mental Health Services") == O.MENTAL_HEALTH
    assert O.family("go", "Notice of Direction to Appoint a Limited Statutory Manager for the Example College (25) Board") == O.INTERVENTION
    assert O.family("go", "Revocation of Notice of Direction to Appoint a Limited Statutory Manager for the Example School (1) Board") == O.INTERVENTION
    assert O.family("ln", "Appointment of the Example Trust to Control and Manage a Reserve", RESERVE) == O.RESERVE
    # pinned the other way: the appointment reader's own titles, other sections and other notices are never a family's
    assert O.family("go", "Appointment of Judges of the District Court") is None
    assert O.family("go", "Notice of Appointment of a Limited Statutory Manager for the Example School (1) Board") is None
    assert O.family("al", "District Court Judge Appointed") is None and O.family("ln", "Justices of the Peace Appointed") is None
    assert O.family("ln", "Appointment of an Advisory Committee", "the Minister appoints the following to the committee") is None
    assert O.family("go", "Marriage Celebrants for 2016") is None


def test_a_judge_reads_the_office_given_and_never_who_they_were_before():
    r = O.judicial("District Court Judge Appointed", JUDGE)
    assert [(p.name, p.role) for p in r.people] == [("Bob Cee Sample", "District Court Judge")]
    assert r.body == "District Court Judge" and r.by_whom == "Governor-General" and r.starts_on == "2016-07-01"
    assert "Barrister" not in repr(r.people) and "Exampleton" not in repr(r.people)
    a = O.judicial("Acting District Court Judge Appointed", ACTING)
    assert [(p.name, p.role) for p in a.people] == [("Cara Dee Example", "Acting District Court Judge")], \
        "the office given, never 'as the Chief District Court Judge may fix'"


def test_a_jp_list_puts_each_name_and_its_town_on_the_row_and_keeps_the_rest_of_the_entry_privately():
    r = O.jp_list("Justices of the Peace Appointed", JP_APPOINTED)
    assert r.kind == "appointed" and r.statute == "Justices of the Peace Act 1957 s 3(1)" and r.dated_on == "2009-05-01"
    assert r.people == [(1, "Example, Ann Bea", "Exampleton"), (2, "Sample, Bob", "Testburgh"), (3, "Dee, Cara Eve", "Gumtree")]
    shown = repr(r.people)
    for word in ("12", "Sample Street", "Exampleville", "Flat", "Test Road", "R.D.", "Wattle Bush", "Fern Road"):
        assert word not in shown, word
    kept = {p: v for p, k, v in r.private if k == "the entry's address as printed"}
    assert set(kept) == {"person 1", "person 2", "person 3"} and "12 Sample Street" in kept["person 1"] \
        and "Wattle Bush" in kept["person 3"], "the rest of each entry is kept for the private twin (ruling 142)"
    t = O.jp_list("Justices of the Peace (Retired)", JP_RETIRED)
    assert t.kind == "retired" and t.people == [(1, "Ann Bea Example", "Exampleton"), (2, "Bob Sample", "Palmerston Test")]
    run = O.jp_list("Justices of the Peace Resignations", JP_RUN)
    assert run.kind == "resigned" and run.people == [] and \
        [w for _, w in run.unread] == ["names run together with no separator: which town is whose cannot be told"]
    assert [k for _, k, _ in run.private] == ["an entry not taken"], "an entry not taken is kept whole"


def test_a_town_is_kept_only_when_it_is_no_street():
    assert O.town(" Exampleton.") == "Exampleton" and O.town("Example Bay 1234") == "Example Bay"
    for street in ("4 Test Road", "Test Road", "R.D. 2", "Flat 3", "PO Box 9", "Example Estate", "12A"):
        assert O.town(street) is None, street


def test_a_mental_health_director_is_read_from_an_amendment_with_the_area():
    got, unread = O.mental_health(MH)
    assert got == [("Bob Sample", "Example Regional Forensic Mental Health Service"),
                   ("Eve Fay Test", "Example Regional Forensic Mental Health Service")] and unread == []
    none, why = O.mental_health("The Schedule lists the directors. Dated at Wellington this 2nd day of March 2026.")
    assert none == [] and why


def test_a_reserve_reads_the_body_and_never_the_land():
    assert O.reserve("Appointment to Control and Manage a Reserve", RESERVE) == (
        "Example Valley Charitable Trust", "appointed to control and manage a reserve")
    assert O.reserve("Revocation of Appointment", RESERVE_REVOKED) == (
        "Example District Council", "appointment to control and manage a reserve revoked")


def test_a_board_intervention_reads_board_number_action_signature_and_the_notice_it_names():
    d = O.intervention("Notice of Direction to Appoint a Limited Statutory Manager for the Example College (25) Board", LSM)
    assert (d.action, d.board, d.institution_number, d.statute, d.dated_on) == (
        "statutory manager directed", "Example College (25) Board", "25", "Education and Training Act 2020 s 171", "2022-09-26")
    assert d.directed_by.startswith("ANN EXAMPLE, Deputy Secretary")
    v = O.intervention("Revocation of Notice of Direction to Appoint a Limited Statutory Manager for the Example College (25) Board",
                       LSM_REVOKED)
    assert v.action == "statutory manager direction revoked" and v.names_notices == ["2022-go4000"] and v.board == "Example College (25) Board"
    x = O.intervention("Notice of Dissolution of the Example Street School (Exampleton) (1772) Board of Trustees and Direction to "
                       "Appoint a Commissioner", DISSOLVED)
    assert x.action == "board dissolved; commissioner directed" and x.institution_number == "1772"
    assert x.board == "Example Street School (Exampleton) (1772) Board of Trustees"


def _export(lines):
    return "\n".join(json.dumps({"notice": n, "title": t, "text": x, "published_on": "2022-10-01", "url": f"u/{n}",
                                 "article": i, "old_article": i}) for i, (n, t, x) in enumerate(lines, 1)).encode()


def test_the_reading_puts_each_family_in_its_table_marks_a_revoked_direction_and_reconciles():
    res = read.read(_export([
        ("2016-go1", "District Court Judge Appointed", JUDGE),
        ("2009-go2", "Justices of the Peace Appointed", JP_APPOINTED),
        ("2009-go3", "Justices of the Peace Resignations", JP_RUN),
        ("2022-go4000", "Notice of Direction to Appoint a Limited Statutory Manager for the Example College (25) Board", LSM),
        ("2023-go5", "Revocation of Notice of Direction to Appoint a Limited Statutory Manager for the Example College (25) Board", LSM_REVOKED),
        ("2025-ln6", "Appointment of the Example Valley Charitable Trust to Control and Manage a Reserve", RESERVE),
        ("2026-go7", "Amending a Notice—Appointment of Director of Area Mental Health Services", MH),
    ]), "0" * 64)
    fmt = {n["filed"]["notice"]: (n["filed"]["format"], n["filed"]["status"]) for n in res.notices}
    assert fmt["2016-go1"] == (O.JUDICIAL, "read") and fmt["2009-go2"] == (O.JP, "read")
    assert fmt["2009-go3"] == (O.JP, "set aside") and fmt["2025-ln6"] == (O.RESERVE, "read")
    assert fmt["2022-go4000"] == (O.INTERVENTION, "read") and fmt["2026-go7"] == (O.MENTAL_HEALTH, "read")
    by = {a["key"]: a["filed"] for a in res.appointments}
    assert by["gazette/2009-go2/appointee/1"]["locality"] == "Exampleton" and by["gazette/2009-go2/appointee/1"]["action"] == "appointed"
    assert by["gazette/2025-ln6/appointee/1"]["appointee_kind"] == "body"
    assert all(a["profile"] in O.PROFILES for a in res.appointments)
    iv = {r["filed"]["notice"]: r["filed"] for r in res.board_interventions}
    assert iv["2022-go4000"]["revoked_by"] == "2023-go5" and iv["2023-go5"]["names_notices"] == "2022-go4000"
    assert res.counts["jp_list_notices"] == 2 and res.counts["jp_list_notices_set_aside"] == 1
    assert res.counts["board_interventions"] == 2 and res.counts["office_holders"] == 1 + 3 + 1 + 2
    assert any(w == "names run together with no separator: which town is whose cannot be told" for i, s, w in res.set_aside)
    shown = repr([a["filed"] for a in res.appointments])
    assert "Sample Street" not in shown and "Test Road" not in shown and "Barrister" not in shown


def test_the_check_fails_on_an_office_notice_not_taken_by_its_profile():
    rows = [("2016-go1", "District Court Judge Appointed", O.JUDICIAL),
            ("2009-go2", "Justices of the Peace Appointed", "not read"),
            ("2025-ln6", "Appointment of the Example Trust to Control and Manage a Reserve", "not read")]
    f = check.office_figures(rows)
    assert f[O.JUDICIAL] == {"titled": 1, "taken": 1, "not_read": []}
    assert f[O.JP]["not_read"] == ["2009-go2"] and f[O.RESERVE]["not_read"] == ["2025-ln6"]
    from registers.gazette.tests.test_gazette_lane import _closed_years
    base = _closed_years() + [("2016-go5", "Marriage Celebrants for 2016 Notice No. 2", check.CELEBRANT),
                              ("2016-ot5", "Notice Prohibiting Person From Managing Companies", check.PROHIBITION)]
    good = base + [(n, t, O.JUDICIAL if n == "2016-go1" else O.JP if n == "2009-go2" else O.RESERVE) for n, t, _ in rows]
    assert check.failed(check.figures(good)) == []
    why = check.failed(check.figures(base + rows))
    assert any("2009-go2" in w for w in why) and any("2025-ln6" in w for w in why) and not any("2016-go1" in w for w in why)
    # an 'Appointment…' title under go is the appointment profile's, never an office family's
    assert check.office_figures([("2016-go3", "Appointment of District Court Judge", "gazette-public-appointment")]) == {}


def test_the_five_profiles_are_in_the_ledger():
    cur = profiles.current()
    for slug in O.PROFILES:
        assert slug in cur and cur[slug]["tooling"]["parse"] == "registers/gazette/offices.py", slug
