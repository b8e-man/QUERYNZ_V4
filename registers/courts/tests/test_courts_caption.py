"""The caption grammar and the suppression rule, on small pages shaped like
the held judgments' text layers (`pdftotext -layout`: labels at the left,
names in the right-hand column). Every name, number and citation here is
invented. A mutant check breaks caption.py and read.py on purpose and
asserts these properties catch each break. No database, no model."""
import datetime as dt
import os
import sys

import pytest

from registers.courts import caption as C
from registers.courts import read as R

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L, N = " " * 15, " " * 44          # the label column and the name column


def page(*lines):
    return "\n".join(lines) + "\n"


SC = page(
    "  NOTE: ORDER PROHIBITING PUBLICATION OF NAMES, ADDRESSES OR IDENTIFYING",
    "   PARTICULARS OF APPELLANTS. SEE [2019] NZHC 999.",
    "IN THE SUPREME COURT OF NEW ZEALAND",
    "I TE KŌTI MANA NUI O AOTEAROA",
    " " * 70 + "SC 12/2099",
    " " * 66 + "[2099] NZSC 7",
    L + "BETWEEN" + " " * 22 + "A, B AND C",
    N + "Appellants",
    L + "AND" + " " * 26 + "EXAMPLE HOLDINGS AND",
    N + "SAMPLE TRADING LIMITED",
    N + "Respondent",
    "Hearing:             13 June 2098",
    "Court:               Able CJ, Baker, Carter, Dunn and",
    "                     Evans JJ",
    "Counsel:             P Q Rowe KC for Appellants",
    "                     S T Vale for Respondent",
    "Judgment:            28 November 2099",
    "                           JUDGMENT OF THE COURT",
    "         A     The appeal is dismissed.",
    "         B     Costs are reserved.",
    "___________________________________________________________________",
    "                           REASONS",
    "[1]    The appellants sought orders. In Smith v Jones the Court said:",
    "            [12]   Quoted from another judgment, indented and out of sequence.",
    "[2011] NZSC 12 is a footnote citation at the margin.",
    "[2]    The second paragraph.")

CA = page(
    "IN THE COURT OF APPEAL OF NEW ZEALAND",
    "I TE KŌTI PĪRA O AOTEAROA",
    " " * 70 + "CA274/2098",
    " " * 66 + "[2099] NZCA 41",
    L + "BETWEEN" + " " * 22 + "NEW ZEALAND EXAMPLE WORKERS AND",
    N + "RELATED TRADES UNION",
    N + "INCORPORATED",
    N + "Appellant",
    L + "AND" + " " * 26 + "ARO MERE PARATA",
    N + "First Respondent",
    N + "ATTORNEY-GENERAL",
    N + "Second Respondent",
    "Hearing:             22 February 2099",
    "Court:               Fox, Gray and Hill JJ",
    "Counsel:             J K Lee for Appellant",
    "                     M N Moe for First Respondent",
    "                     O P Nash for Second Respondent",
    "Judgment:            4 March 2099 at 11.00 am",
    "                          JUDGMENT OF THE COURT",
    "A        The appeal is allowed.")

HC_CRI = page(
    "IN THE HIGH COURT OF NEW ZEALAND",
    "EXAMPLETOWN REGISTRY",
    "I TE KŌTI MATUA O AOTEAROA",
    "TE KAINGA TAUIRA",
    " " * 66 + "CRI-2098-404-000123",
    " " * 70 + "[2099] NZHC 1303",
    " " * 39 + "THE KING",
    " " * 43 + "v",
    " " * 35 + "TAMA RIWAI &",
    " " * 35 + "HEMI TOA",
    " " * 43 + "X and S",
    "Hearing:               15 May 2099",
    "Counsel:               A Bee for Crown",
    "                       C Dee for Defendant Riwai",
    "Judgment:              15 May 2099",
    "                      SENTENCING NOTES OF WHITE J")

HC_CIV = page(
    "IN THE HIGH COURT OF NEW ZEALAND",
    "EXAMPLETOWN REGISTRY",
    "I TE KŌTI MATUA O AOTEAROA",
    " " * 66 + "CIV-2098-404-1041",
    " " * 66 + "[2099] NZHC 2279",
    L + "UNDER" + " " * 24 + "the Example Act 2016",
    L + "BETWEEN" + " " * 24 + "SAMPLE FARMS LIMITED",
    N + "First Plaintiff",
    N + "ANNA SAMPLE",
    N + "Second Plaintiff",
    L + "AND" + " " * 28 + "BEN TEST and",
    N + "CARA TEST as trustees of",
    N + "THE TEST FAMILY TRUST",
    N + "Defendants",
    " " * 70 + "(Continued over)",
    "Hearing:              4 August 2098",
    "Appearances:          D Eel for the Plaintiffs",
    "                      F Gee for the Defendants",
    "                      H Ivy for the Third Respondent",
    "Judgment:             5 August 2099",
    "                            JUDGMENT OF WHITE J",
    "      This judgment was delivered by me on 5 August 2099 at 4.30 pm")
HC_CIV_2 = page(
    L + "AND" + " " * 28 + "EXAMPLE DISTRICT COUNCIL",
    N + "Third Respondent",
    "",
    "[1]    The plaintiffs claim.")


#: the High Court's "… continued over" above the labels, page 2 running straight on with the last block's names and
#: roles, no AND (two of the 3 November check's four; 27 judgments of the corpus)
HC_OVER = page(
    "IN THE HIGH COURT OF NEW ZEALAND",
    "EXAMPLETOWN REGISTRY",
    " " * 66 + "CIV-2098-404-1042",
    " " * 66 + "[2099] NZHC 2280",
    L + "BETWEEN" + " " * 24 + "SAMPLE ORCHARDS LIMITED",
    N + "Plaintiff",
    L + "AND" + " " * 28 + "DAN TEST",
    N + "First Defendant",
    N + "EVE TEST",
    N + "Second Defendant",
    " " * 70 + "… continued over",
    "Hearing:              On the papers",
    "Appearances:          D Eel for Plaintiff",
    "                      F Gee for Third and Fourth Defendants",
    "Judgment:             5 August 2099",
    "                            JUDGMENT OF WHITE J")
HC_OVER_2 = page(
    "SAMPLE HOLDINGS LIMITED",
    "Third Defendant",
    "EXAMPLE TRUSTEE LIMITED",
    "Fourth Defendant",
    "[1]      The plaintiff applies.")


def hc_two_sided(first, second, counsel):
    """A High Court caption of two parties and its counsel lines."""
    return page(
        "IN THE HIGH COURT OF NEW ZEALAND", "EXAMPLETOWN REGISTRY", " " * 66 + "CIV-2098-404-1043", " " * 66 + "[2099] NZHC 2281",
        L + "BETWEEN" + " " * 24 + "ANNA SAMPLE", N + first, L + "AND" + " " * 28 + "EXAMPLE DISTRICT COUNCIL", N + second,
        "Hearing:              4 August 2098", "Appearances:          " + counsel[0],
        *("                      " + c for c in counsel[1:]), "Judgment:             5 August 2099",
        "                            JUDGMENT OF WHITE J")


def parse(p1, p2="", name=""):
    return C.parse({1: p1, 2: p2} if p2 else {1: p1}, name)


# --- the header ------------------------------------------------------------------

def test_the_citation_is_the_line_under_the_case_numbers_never_the_banner_s():
    j = parse(SC, name="2099-NZSC-7.pdf")
    assert j.citation == "[2099] NZSC 7" and j.court == "NZSC" and j.court_name == "SUPREME COURT"
    assert j.case_numbers == ["SC 12/2099"] and j.notes == []


def test_a_citation_that_disagrees_with_the_file_name_is_noted():
    assert parse(SC, name="2099-NZSC-8.pdf").notes == ["the file name says [2099] NZSC 8"]


def test_the_registry_and_the_judgment_date_and_the_judges():
    j = parse(CA)
    assert j.registry is None and j.judgment_date == dt.date(2099, 3, 4) and j.date_basis == "label"
    assert j.judges == "Fox, Gray and Hill JJ" and j.heading == "JUDGMENT"
    h = parse(HC_CIV, HC_CIV_2)
    assert h.registry == "EXAMPLETOWN" and h.judges == "WHITE J" and h.case_numbers == ["CIV-2098-404-1041"]
    s = parse(SC)
    assert s.judges == "Able CJ, Baker, Carter, Dunn and Evans JJ"


# --- the parties -------------------------------------------------------------------

def test_initials_on_one_line_are_three_anonymised_parties_never_expanded():
    j = parse(SC)
    apps = [p for p in j.parties if p.role == "Appellants"]
    assert [(p.name, p.anonymised) for p in apps] == [("A", True), ("B", True), ("C", True)]


def test_a_singular_role_holds_one_party_however_its_name_wraps():
    j = parse(CA)
    assert [(p.name, p.role) for p in j.parties] == [
        ("NEW ZEALAND EXAMPLE WORKERS AND RELATED TRADES UNION INCORPORATED", "Appellant"),
        ("ARO MERE PARATA", "First Respondent"), ("ATTORNEY-GENERAL", "Second Respondent")]
    assert [p.block for p in j.parties] == [1, 2, 2]
    assert j.parties[2].crown and not j.parties[1].crown
    sc = parse(SC)
    assert [p.name for p in sc.parties if p.role == "Respondent"] == ["EXAMPLE HOLDINGS AND SAMPLE TRADING LIMITED"]


def test_a_block_holds_several_name_and_role_pairs_and_a_capacity_qualifies_its_names():
    j = parse(HC_CIV, HC_CIV_2)
    assert [(p.name, p.role) for p in j.parties] == [
        ("SAMPLE FARMS LIMITED", "First Plaintiff"), ("ANNA SAMPLE", "Second Plaintiff"),
        ("BEN TEST", "Defendants"), ("CARA TEST", "Defendants"), ("EXAMPLE DISTRICT COUNCIL", "Third Respondent")]
    assert {p.capacity for p in j.parties if p.role == "Defendants"} == {"as trustees of THE TEST FAMILY TRUST"}
    assert j.notes == ["caption continued on page 2"] and j.unrecognised == []


def test_the_criminal_caption_prosecutor_above_the_v_each_defendant_below():
    j = parse(HC_CRI)
    assert j.caption_shape == "criminal"
    assert [(p.name, p.role, p.anonymised, p.crown) for p in j.parties] == [
        ("THE KING", "Prosecutor", False, True), ("TAMA RIWAI", "Defendant", False, False),
        ("HEMI TOA", "Defendant", False, False), ("X", "Defendant", True, False), ("S", "Defendant", True, False)]
    assert j.heading == "SENTENCING NOTES" and j.judges == "WHITE J" and j.registry == "EXAMPLETOWN"


def test_a_matter_is_a_party_only_with_a_role_under_it():
    p = page("IN THE SUPREME COURT OF NEW ZEALAND", " " * 66 + "[2099] NZSC 9",
             L + "IN THE MATTER OF" + " " * 13 + "SOLICITOR-GENERAL'S REFERENCE",
             N + "(NO 1 OF 2099) FROM CA441/2098", N + "Referrer", "Hearing:   1 May 2099", "Judgment:  2 May 2099")
    j = parse(p)
    assert j.caption_shape == "matter" and [(x.name, x.role) for x in j.parties] == [
        ("SOLICITOR-GENERAL'S REFERENCE (NO 1 OF 2099) FROM CA441/2098", "Referrer")]
    q = p.replace(N + "Referrer\n", "")
    assert parse(q).parties == [] and parse(q).status == "partial"


def test_a_wrapped_list_of_people_is_split_and_marked_low():
    p = page("IN THE HIGH COURT OF NEW ZEALAND", " " * 66 + "[2099] NZHC 5",
             L + "BETWEEN" + " " * 22 + "ANA ROA, BEN",
             N + "TAI AND CY WAHO",
             N + "Applicants",
             L + "AND" + " " * 26 + "EXAMPLE LIMITED", N + "Respondent", "Hearing:  1 May 2099", "Judgment:  2 May 2099")
    j = parse(p)
    assert [(x.name, x.confidence) for x in j.parties if x.role == "Applicants"] == [
        ("ANA ROA", "low"), ("BEN TAI", "low"), ("CY WAHO", "low")]


def test_the_counsel_roles_are_held_by_the_parties_or_reported():
    assert C.roles_unaccounted(parse(CA)) == []
    assert C.roles_unaccounted(parse(SC)) == []
    j = parse(HC_CIV, HC_CIV_2)
    assert C.roles_unaccounted(j) == []
    j.parties = [p for p in j.parties if p.role != "Third Respondent"]
    assert C.roles_unaccounted(j) == ["Third Respondent"]


def test_a_plural_group_in_the_caption_holds_every_ordinal_of_its_role():
    j = C.Judgment(counsel_roles=["Applicant", "First And Sixth Respondents", "Second Respondent"], caption_shape="between")
    j.parties = [C.Party(name="", role=r, position=0, block=0) for r in ("Applicant", "Respondents")]
    assert C.roles_unaccounted(j) == []
    j.parties = [C.Party(name="", role=r, position=0, block=0) for r in ("Applicant", "Respondent")]
    assert C.roles_unaccounted(j) == ["First And Sixth Respondents", "Second Respondent"], "a single Respondent holds no ordinal"


def test_a_criminal_caption_s_counsel_lines_name_its_sides_by_the_stage():
    """A Supreme Court leave judgment of 2005 to 2012: "X v THE QUEEN", no printed role, and "for Applicant" and
    "for Crown" on the counsel lines (23 of the live check's 200 before this; a role no party holds is still reported)."""
    p = "\n".join(["IN THE SUPREME COURT OF NEW ZEALAND", " " * 66 + "SC 59/2099", " " * 62 + "[2099] NZSC 80", "",
                   " " * 36 + "TAMA RIWAI", "", " " * 40 + "v", "", " " * 36 + "THE QUEEN", "",
                   "Hearing:        24 November 2099", "Court:          Able CJ, Baker and Carter JJ",
                   "Counsel:        J Haigh KC for Applicant", "                B J Horsley for Crown",
                   "Judgment:       8 December 2099", "", "         JUDGMENT OF THE COURT", "",
                   "   The application for leave to appeal is dismissed.", "[1]  The applicant seeks leave."]) + "\n"
    j = parse(p)
    assert j.caption_shape == "criminal" and [x.role for x in j.parties] == ["Defendant", "Prosecutor"] or \
        [x.role for x in j.parties] == ["Prosecutor", "Defendant"]
    assert j.counsel_roles == ["Applicant"] and C.roles_unaccounted(j) == []
    j.counsel_roles = ["Second Appellant"]
    assert C.roles_unaccounted(j) == ["Second Appellant"], "an ordinal needs that many defendants"
    j.counsel_roles = ["Intervener"]
    assert C.roles_unaccounted(j) == ["Intervener"], "a side the criminal caption has no word for is still reported"
    j.parties = []
    assert C.roles_unaccounted(j) == ["Intervener"]


def test_a_caption_continued_over_runs_straight_on_at_the_top_of_page_2():
    """2 of the 3 November four: "… continued over" on page 1, page 2 opening on the last block's next name and
    role with no AND; the counsel line for Third and Fourth Defendants was reported as a role no party holds."""
    j = parse(HC_OVER, HC_OVER_2)
    assert [p.role for p in j.parties] == ["Plaintiff", "First Defendant", "Second Defendant", "Third Defendant", "Fourth Defendant"]
    assert j.notes == ["caption continued on page 2"] and j.unrecognised == []
    assert j.counsel_roles == ["Plaintiff", "Third And Fourth Defendants"] and C.roles_unaccounted(j) == []
    assert C.roles_source_exception(j) is None
    alone = parse(HC_OVER)
    assert C.roles_unaccounted(alone) == ["Third And Fourth Defendants"], "without its page 2 the role is still short"
    assert C.roles_source_exception(alone) is None, "a parse miss is never the source's own"


def test_the_source_s_own_inconsistencies_are_named_and_a_parse_miss_is_not():
    """The other two of the 3 November four: the court's own printing, counted apart with a reason."""
    inter = parse(hc_two_sided("Applicant", "Respondent", ["Applicant in person", "G Hay for Respondent", "J Ivy for Intervener"]))
    assert C.roles_unaccounted(inter) == ["Intervener"] and C.roles_source_exception(inter) == C.INTERVENER_UNLISTED
    appeal = parse(hc_two_sided("Plaintiff", "Defendant", ["D Eel for the appellant", "F Gee for the respondent"]))
    assert C.roles_unaccounted(appeal) == ["Appellant", "Respondent"]
    assert C.roles_source_exception(appeal) == C.APPEAL_UNDER_FIRST_INSTANCE
    # a role the grammar missed beside the intervener, or an ordinal on an appeal's line, stays a parse miss
    mixed = parse(hc_two_sided("Applicant", "Respondent", ["G Hay for Second Respondent", "J Ivy for Intervener"]))
    assert C.roles_unaccounted(mixed) == ["Intervener", "Second Respondent"] and C.roles_source_exception(mixed) is None
    ordinal = parse(hc_two_sided("Plaintiff", "Defendant", ["D Eel for the appellant", "F Gee for the second respondent"]))
    assert C.roles_source_exception(ordinal) is None
    j = parse(HC_CIV, HC_CIV_2)
    j.parties = [p for p in j.parties if p.role != "Third Respondent"]
    assert C.roles_source_exception(j) is None


def _hc(caption_lines, counsel):
    """A High Court page of the given caption lines and counsel lines (every name invented)."""
    return page("IN THE HIGH COURT OF NEW ZEALAND", "EXAMPLETOWN REGISTRY", " " * 66 + "CIV-2098-404-1043",
                " " * 66 + "[2099] NZHC 2281", *caption_lines, "Hearing:              4 August 2098",
                "Appearances:          " + counsel[0], *("                      " + c for c in counsel[1:]),
                "Judgment:             5 August 2099", "                            JUDGMENT OF WHITE J")


def test_counterclaim_roles_and_ordinal_ranges_are_roles():
    """Two of the 5 November four: "Plaintiff/First Counterclaim Defendant" and "Second Counterclaim Defendant" in a
    claim with a counterclaim; "First to Fourth Plaintiffs" and "First to Fiftieth Third Parties" in a group action.
    Neither caption gave a party before; the counsel lines were reported as roles no party holds."""
    j = parse(_hc([L + "BETWEEN" + " " * 24 + "ANNA SAMPLE LIMITED", N + "Plaintiff/First Counterclaim Defendant",
                   L + "AND" + " " * 28 + "EXAMPLE HOLDINGS LP", N + "Defendant/Counterclaim Plaintiff",
                   L + "AND" + " " * 28 + "BEN SAMPLE", N + "Second Counterclaim Defendant"],
                  ["H Able for the Plaintiff/First Counterclaim Defendant", "E Baker for the Defendant/Counterclaim Plaintiff",
                   "S Cole for the Second Counterclaim Defendant"]))
    assert [p.role for p in j.parties] == ["Plaintiff/First Counterclaim Defendant", "Defendant/Counterclaim Plaintiff",
                                           "Second Counterclaim Defendant"] and j.unrecognised == []
    assert j.counsel_roles == ["Defendant", "Plaintiff", "Second Counterclaim Defendant"] and C.roles_unaccounted(j) == []
    g = parse(_hc([L + "BETWEEN" + " " * 24 + "OWNERS OF EXAMPLE TOWERS AND", N + "OTHERS", N + "First to Fourth Plaintiffs",
                   L + "AND" + " " * 28 + "EXAMPLE BUILDERS LIMITED", N + "Defendant",
                   L + "AND" + " " * 28 + "EXAMPLE CITY COUNCIL AND OTHERS", N + "First to Fiftieth Third Parties"],
                  ["N Dee for plaintiffs", "D Eel for defendant"]))
    assert list(dict.fromkeys(p.role for p in g.parties)) == ["First to Fourth Plaintiffs", "Defendant",
                                                              "First to Fiftieth Third Parties"]
    assert C.roles_unaccounted(g) == []
    assert not C.ROLE.match("First to Fourth"), "an ordinal range is a role only with its base"


def test_an_application_in_the_matter_with_no_parties_is_the_source_s_own_and_a_party_s_role_is_not():
    """One of the 5 November four: "IN THE MATTER of an application by ..." and no BETWEEN; the counsel line is for
    the Applicant, whom the matter's words name. Counted apart with its reason; any other role stays a parse miss."""
    lines = [L + "IN THE MATTER" + " " * 18 + "of the Example Act 2007", L + "AND",
             L + "IN THE MATTER" + " " * 18 + "of an application by ANNA SAMPLE for an order"]
    j = parse(_hc(lines, ["T Able for Applicant"]))
    assert j.caption_shape == "matter" and j.parties == []
    assert C.roles_unaccounted(j) == ["Applicant"] and C.roles_source_exception(j) == C.MATTER_APPLICANT
    assert C.roles_source_exception(parse(_hc(lines, ["T Able for Second Applicant"]))) is None, "an ordinal is a miss"
    assert C.roles_source_exception(parse(_hc(lines, ["T Able for Applicant", "R Bee for Respondent"]))) is None
    assert C.roles_source_exception(parse(hc_two_sided("Plaintiff", "Defendant", ["T Able for Applicant"]))) is None


# --- suppression, paragraphs, outcome -----------------------------------------------

def test_a_banner_flags_suppression_and_its_kinds_are_a_closed_list():
    j = parse(SC)
    assert j.suppression and j.suppression_kinds == ["banner"]
    b = page("NOTE: PUBLICATION OF NAME, ADDRESS, OCCUPATION OR IDENTIFYING PARTICULARS OF COMPLAINANT",
             "PROHIBITED BY S 203 OF THE CRIMINAL PROCEDURE ACT 2011 UNTIL FURTHER ORDER.") + CA
    assert parse(b).suppression_kinds == ["banner", "CPA s 203", "until"]
    assert not parse(CA).suppression


def test_an_order_in_the_text_flags_suppression_without_a_banner():
    t = CA + "[2]    There is an order suppressing the name of the first respondent.\n"
    assert parse(t).suppression_kinds == ["order in the text"]
    t2 = CA + "[2]    I suppress the identity of the witness.\n"
    assert parse(t2).suppression


def test_paragraphs_are_numbered_in_sequence_skipping_citations_and_quotes():
    assert parse(SC).paragraphs == [(1, 1), (2, 1)]


def test_the_outcome_is_a_closed_vocabulary_from_the_orders():
    assert parse(SC).outcome == ["appeal dismissed"] and parse(CA).outcome == ["appeal allowed"]


# --- the suppression rule (read.rows) ------------------------------------------------

def _rows(*parsed, orders=()):
    res = R.Result()
    return R.rows(res, [({"source": "courtsofnz.govt.nz", "url": f"x/{i}.pdf"}, sha, "courts-nzca-judgment", 1, j)
                        for i, (sha, j) in enumerate(parsed)], orders, "2099-12-01T00:00:00+13:00")


def test_a_suppressed_judgment_withholds_every_name_but_the_crown_s_and_an_initial():
    banner = page("NOTE: ORDER PROHIBITING PUBLICATION OF NAMES OF THE RESPONDENTS.") + CA
    res = _rows(("a" * 64, parse(banner)))
    shown = {(p["role"], p["name"], p["withheld"]) for p in res.parties}
    assert shown == {("Appellant", None, True), ("First Respondent", None, True), ("Second Respondent", "ATTORNEY-GENERAL", False)}
    assert {(w["key"][65:], w["name"]) for w in res.withheld} == {
        ("party/1", "NEW ZEALAND EXAMPLE WORKERS AND RELATED TRADES UNION INCORPORATED"), ("party/2", "ARO MERE PARATA")}
    # ruling 142: each name kept whole, flagged, with the source's words and where it belongs
    assert all(w["suppressed"] and w["held_in"] == "judgment_parties" and w["document"] == "a" * 64
               and "banner" in w["suppression_words"] for w in res.withheld)
    assert res.judgments[0]["withheld"] == R.WITHHELD_MARKER and len(res.parties) == 3
    sc = _rows(("b" * 64, parse(SC)))
    assert {p["name"] for p in sc.parties} == {"A", "B", "C", None}


def test_capacity_is_withheld_with_the_name():
    j = parse(HC_CIV, HC_CIV_2)
    j.suppression, j.suppression_kinds = True, ["banner"]
    res = _rows(("c" * 64, j))
    assert all(p["capacity"] is None for p in res.parties)
    assert {w["capacity"] for w in res.withheld} == {None, "as trustees of THE TEST FAMILY TRUST"}


def test_one_suppressed_document_of_a_citation_withholds_the_names_on_the_other():
    plain, marked = parse(CA), parse(page("ORDER PROHIBITING PUBLICATION OF NAME OF THE FIRST RESPONDENT.") + CA)
    res = _rows(("d" * 64, plain), ("e" * 64, marked))
    first = [j for j in res.judgments if j["document"] == "d" * 64][0]
    assert first["suppression_kinds"] == ["another document of the citation"]
    assert sum(p["withheld"] for p in res.parties) == 4


def test_a_ledger_order_binds_by_citation_or_by_document_and_says_why():
    res = _rows(("f" * 64, parse(CA)), orders=[{"citation": "[2099] NZCA 41", "document": None, "reason": "s 200 order"}])
    assert res.judgments[0]["withheld"] == "suppression order: s 200 order" and "ledger" in res.judgments[0]["suppression_kinds"]
    assert sum(p["withheld"] for p in res.parties) == 2
    by_doc = _rows(("f" * 64, parse(CA)), orders=[{"citation": None, "document": "f" * 64, "reason": "x"}])
    assert sum(p["withheld"] for p in by_doc.parties) == 2
    other = _rows(("f" * 64, parse(CA)), orders=[{"citation": "[2099] NZCA 42", "document": None, "reason": "x"}])
    assert sum(p["withheld"] for p in other.parties) == 0


def test_every_row_meets_the_row_contract():
    from support import rowcontract
    res = _rows(("a" * 64, parse(SC)), ("b" * 64, parse(CA)))
    for r in res.judgments + res.parties:
        assert rowcontract.validate(r) == [], r["key"]


# --- the mutant check ----------------------------------------------------------------

def properties(c, r) -> list:
    """The properties above, run against a (possibly mutant) caption and read module."""
    fails = []
    def check(name, fn):
        try:
            if not fn():
                fails.append(name)
        except Exception:  # noqa: BLE001 — a mutant that raises is caught too
            fails.append(name)
    P = lambda p1, p2="", name="": c.parse({1: p1, 2: p2} if p2 else {1: p1}, name)  # noqa: E731
    check("banner citation", lambda: P(SC).citation == "[2099] NZSC 7")
    check("anonymised", lambda: [x.anonymised for x in P(SC).parties][:3] == [True, True, True])
    check("singular wrap", lambda: len(P(CA).parties) == 3)
    check("block pairs", lambda: len(P(HC_CIV, HC_CIV_2).parties) == 5)
    check("criminal", lambda: [x.name for x in P(HC_CRI).parties][1:3] == ["TAMA RIWAI", "HEMI TOA"])
    check("suppression banner", lambda: P(SC).suppression and not P(CA).suppression)
    check("paragraphs", lambda: P(SC).paragraphs == [(1, 1), (2, 1)])
    check("counsel", lambda: c.roles_unaccounted(P(CA)) == [])
    check("continued over", lambda: c.roles_unaccounted(P(HC_OVER, HC_OVER_2)) == [] and len(P(HC_OVER, HC_OVER_2).parties) == 5)
    check("source's own", lambda: c.roles_source_exception(P(hc_two_sided("Applicant", "Respondent", ["J Ivy for Intervener"])))
          == c.INTERVENER_UNLISTED and c.roles_source_exception(P(hc_two_sided("Plaintiff", "Defendant",
          ["D Eel for the appellant", "F Gee for the respondent"]))) == c.APPEAL_UNDER_FIRST_INSTANCE)
    check("a miss is no exception", lambda: c.roles_unaccounted(P(HC_OVER)) != []
          and c.roles_source_exception(P(HC_OVER)) is None
          and c.roles_source_exception(P(hc_two_sided("Applicant", "Respondent", ["G Hay for Second Respondent",
                                                                                 "J Ivy for Intervener"]))) is None)

    def withheld():
        res = r.rows(r.Result(), [({"source": "x", "url": "x"}, "a" * 64, "s", 1,
                                   P(page("NOTE: ORDER PROHIBITING PUBLICATION OF NAMES.") + CA))], [], "t")
        return [p["name"] for p in res.parties] == [None, None, "ATTORNEY-GENERAL"]
    check("withheld", withheld)
    return fails


def _module(name, path, old, new, bind=None):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    assert src.count(old) == 1, f"the mutant's target is not unique in {os.path.basename(path)}: {old!r}"
    mod = type(sys)(name)
    mod.__dict__.update({"__file__": path, **(bind or {})})
    exec(compile(src.replace(old, new), f"{os.path.basename(path)} (mutant)", "exec"), mod.__dict__)
    return mod


MUTANTS = [
    ("caption", "the first citation anywhere", "        m = CITE_LINE.match(ln)\n        if m and not out.citation:",
     "        m = CITE.search(head)\n        if m and not out.citation:"),
    ("caption", "anonymised never flagged", 'ANON = re.compile(r"^(?:[A-Z]{1,3}|', 'ANON = re.compile(r"^(?:[a-z]{9}|'),
    ("caption", "every role treated as plural", "    plural = bool(PLURAL.search(role))", "    plural = True"),
    ("caption", "a role ends the block", "            pending = []            # the block runs on",
     "            pending, mode = [], None  # the block runs on"),
    ("caption", "the banner not read", 'out.suppression_kinds = suppression_kinds(banner, body)',
     'out.suppression_kinds = suppression_kinds("", body)'),
    ("caption", "paragraphs out of sequence kept", "            if m and int(m.group(2)) == want:", "            if m:"),
    ("caption", "an ampersand never splits defendants", 'm = re.search(r"\\s+(?:&|AND)$", l)', "m = None"),
    ("caption", "continued over without an AND ignored", " or _marked_over(p1[cl.end():]))", ")"),
    ("caption", "an ellipsis before continued over", r'OVER = re.compile(r"^\s*(?:…|\.{2,})?\s*', r'OVER = re.compile(r"^\s*'),
    ("caption", "every short role the source's own", "        return None\n    held = set()",
     "        return None\n    return INTERVENER_UNLISTED\n    held = set()"),
    ("caption", "an intervener beside a miss excepted", "    if all(b and b <= {\"intervener\"", "    if any(b and b <= {\"intervener\""),
    ("read", "the suppression rule off", "            hide = bool(withheld) and not p.crown and not p.anonymised",
     "            hide = False"),
    ("read", "the Crown withheld too", "            hide = bool(withheld) and not p.crown and not p.anonymised",
     "            hide = bool(withheld) and not p.anonymised"),
]


def test_the_properties_hold_on_the_real_modules():
    assert properties(C, R) == []


@pytest.mark.parametrize("which,what,old,new", MUTANTS, ids=[m[1] for m in MUTANTS])
def test_a_mutant_is_caught(which, what, old, new):
    if which == "caption":
        c, r = _module("qv4_courts_caption_mutant", os.path.join(HERE, "caption.py"), old, new), R
        r = _module("qv4_courts_read_with_mutant", os.path.join(HERE, "read.py"), "from registers.courts import caption\n",
                    "\n", bind={"caption": c})
    else:
        c, r = C, _module("qv4_courts_read_mutant", os.path.join(HERE, "read.py"), old, new)
    assert properties(c, r), f"the mutant '{what}' passed every property: a check that cannot fail"


def test_a_court_code_has_one_spelling_and_a_transcript_s_court_line_with_the_case_number_beside_it_names_the_court():
    from registers.courts import caption as C
    assert C.court_code("NZEMPC") == "NZEmpC" and C.court_code("nzsc") == "NZSC" and C.court_code("NZXYZ") == "NZXYZ"
    assert C.file_citation("2021-NZEMPC-77-Judgment.pdf") == "[2021] NZEmpC 77"
    page = "IN THE EMPLOYMENT COURT OF NEW ZEALAND\nAUCKLAND REGISTRY\n[2021] NZEMPC 77\nEMPC 12/2021\n\nBETWEEN   SAMPLE BODY LIMITED\n" \
           "                 Plaintiff\nAND       A PUBLIC AGENCY\n                 Defendant\n\nHearing: 1 June 2021\n\nJudgment: 2 June 2021\n\nJUDGMENT OF THE COURT\n[1] Text.\n"
    j = C.parse({1: page}, "2021-NZEMPC-77.pdf")
    assert j.court == "NZEmpC" and j.citation == "[2021] NZEmpC 77" and j.court_name == "EMPLOYMENT COURT"
    assert not any("file name" in n for n in j.notes), "one spelling: the file name agrees with the text"
    # a hearing transcript's cover sheet: the court line with the case number beside it, no citation anywhere
    cover = "IN THE SUPREME COURT OF NEW ZEALAND                               SC 12/2016\n\n\n           BETWEEN                SAMPLE BODY LIMITED\n" \
            "                                                                   Appellant\n\n               AND                A PUBLIC AGENCY\n" \
            "                                                            Respondent\n\nHearing: 1 June 2016\n"
    t = C.parse({1: cover}, "transcript.pdf")
    assert t.court_name == "SUPREME COURT" and t.court == "NZSC" and t.citation is None and t.status == "unparsed"
    assert t.case_numbers == ["SC 12/2016"]


def test_a_printers_slip_year_is_never_a_date_and_the_address_date_stands():
    """3 November 2026: an Environment Court filing printed "17 October 3023"; the lane published it dated 3023. A year
    no court document can carry is refused, and the date its own address carries stands in."""
    import datetime as dt
    from registers.courts import caption, read
    assert caption._date("17 October 3023") is None
    assert caption._date("17 October 1839") is None
    assert caption._date("17 October 2023") == dt.date(2023, 10, 17)
    assert read._impossible_date("Minute\n17 October 3023\n") and not read._impossible_date("17 October 2023")
    url = "https://environmentcourt.govt.nz/assets/Documents/Publications/2023-10-17-Muaupoko-legal-subs-for-24-October-EC-hearing.pdf"
    assert read._url_date(url) == dt.date(2023, 10, 17)
    assert read._url_date("https://environmentcourt.govt.nz/2023-10-17/file.pdf") is None    # the file's own name only
    assert read._url_date("https://x.nz/3023-10-17-a.pdf") is None


def test_a_suppressed_name_is_kept_whole_with_the_source_s_words_never_lost():
    """Ruling 142 (4 November 2026): a suppression is a flag beside the row; the name, its capacity, where it belongs and
    the source's words are all kept for the private table. Before, the private row held the name and capacity only."""
    from registers.courts import load as courts_load
    j = parse(HC_CIV, HC_CIV_2)
    j.suppression, j.suppression_kinds = True, ["banner"]
    res = _rows(("c" * 64, j))
    hidden = [p for p in res.parties if p["withheld"]]
    assert hidden and {w["key"] for w in res.withheld} == {p["key"] for p in hidden}
    for w in res.withheld:
        assert set(w) == set(courts_load.WITHHELD_COLUMNS) and w["name"] and w["suppressed"] is True
        assert w["held_in"] == "judgment_parties" and w["document"] == "c" * 64 and "banner" in w["suppression_words"]
