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
    assert {(k[65:], n) for k, n, _ in res.withheld} == {
        ("party/1", "NEW ZEALAND EXAMPLE WORKERS AND RELATED TRADES UNION INCORPORATED"), ("party/2", "ARO MERE PARATA")}
    assert res.judgments[0]["withheld"] == R.WITHHELD_MARKER and len(res.parties) == 3
    sc = _rows(("b" * 64, parse(SC)))
    assert {p["name"] for p in sc.parties} == {"A", "B", "C", None}


def test_capacity_is_withheld_with_the_name():
    j = parse(HC_CIV, HC_CIV_2)
    j.suppression, j.suppression_kinds = True, ["banner"]
    res = _rows(("c" * 64, j))
    assert all(p["capacity"] is None for p in res.parties)
    assert {c for _, _, c in res.withheld} == {None, "as trustees of THE TEST FAMILY TRUST"}


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
