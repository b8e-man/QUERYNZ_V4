"""The thin slice's tests (plan 1.11), the first proof of the fast tier:
they fill the session's sample schema through this branch's own code, call
no model, and run in well under a minute. The declaration reader is tested
on page texts shaped like the ones measured; the filled sample is tested
against the row contract and against the frozen site's figures."""
import datetime as dt
import glob
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.party_returns import check, declaration, read

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "party_returns")

PAGE = """                                               the year ending 31 December 2023
1.   Party name:
                                                                                COMPLETING THE RETURN
      Example Party of Aotearoa
      Party secretary name:
2.   TOTAL PARTY DONATIONS
 2      complete Parts A to G on pages 2 to 10 if you have any donations to declare.
     Part A: Party donations of more than $15,000                          $ 1,000.00
     Part C: Anonymous party donations of more than $1,500                    $ 0.00
     Part D: Overseas party donations of more than $50                     0
     Part F: Donations protected from disclosure                                          Step 1 completed
                                                                              $ 500.00
     Part G: Other party donations up to $15,000
                                                                            218464.7            the return
                                                                                    219964.7    documentation supplied
                                              Total (A + C + D + F + G)
     Total Monetary Party Donations
                                                                            $ 219,964.70
3.   TOTAL PARTY LOANS
     Part H: Party loans exceeding $15,000                                    $ 99.00
"""

OCR_PAGE = """            TE KAITIAKI TAKE KOWHIRI          the year ending 31 December 2023
•I Party name:
                                                                                           or by hand.
      NZ Example Party
      Part A: Party donations of more than $5,000                         $1 ,879,585.14   party loans disclosed In Parts H
      Part C: Anonymous party donations of more than $1,500                   $0.00
      Part D: Overseas party donations of more than $50                       $0.00
      Port Fi Donations protected from disclosure                                          Step 1 completed
                                                                              $0.00
      Part 0: Other party donations up to $5,000
                                                                          $2,889,810.12
                           Total Party Donations (A+C+D+F+0)              $ 4,769,395.26
3. TOTALPARTyLOANS
"""


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


def test_figures_are_paired_on_the_line_below_and_above_their_labels():
    d = declaration.read(PAGE)
    assert d.year == 2023 and d.party_label == "Example Party of Aotearoa"
    assert d.parts == {"A": 1000.0, "C": 0.0, "D": 0.0, "F": 500.0, "G": 218464.7}
    assert d.total == 219964.7 and d.total_letters == "A+C+D+F+G"
    assert d.problems() == [] and d.check == "parts-sum"


def test_a_scanner_s_ocr_layer_is_read_by_the_words_of_each_label():
    d = declaration.read(OCR_PAGE)
    assert d.parts == {"A": 1879585.14, "C": 0.0, "D": 0.0, "F": 0.0, "G": 2889810.12}
    assert d.total == 4769395.26 and d.total_letters == "A+C+D+F+0"      # as printed, not trusted
    assert d.problems() == []


def test_an_unreconciled_page_is_a_problem_not_a_number():
    short = PAGE.replace("     Part F: Donations protected from disclosure                                          Step 1 completed\n"
                         "                                                                              $ 500.00\n", "")
    d = declaration.read(short)
    probs = d.problems()
    assert any("part F not read" in p for p in probs)
    assert any("parts sum to" in p for p in probs)
    wrong = PAGE.replace("219964.7    documentation", "219964.8    documentation")
    assert declaration.read(wrong).problems() == ["parts sum to 219964.70 but the declared total is 219964.80"]
    assert declaration.read("no declaration here").problems()[0] == "no year on the declaration page"


def test_a_declared_nil_is_a_complete_return():
    page = ("   the year ending 31 December 2021\n1.   Party name:\n      Example Party\n"
            "                                                                     NIL\n"
            "                                              Total (A + C + D + F + G)\n3.   TOTAL PARTY LOANS\n")
    d = declaration.read(page)
    assert d.total == 0.0 and d.total_is_nil and d.problems() == [] and d.check == "declared-nil"


def test_a_mixed_document_is_not_recognised_by_the_text_profile():
    prof = read.current_profile()
    texts = {1: "x" * 3000, 2: "y" * 3000, 3: ""}
    assert "page reader" in read.recognise(texts, prof)
    assert read.recognise({1: "x" * 3000, 2: "y" * 3000}, prof) == ""
    assert "page 1" in read.recognise({1: "x" * 100, 2: "y" * 6000}, prof)


def test_compare_names_equal_differing_and_unmatched():
    frozen = {("Example Party", 2023): (219964.7, "example-2023.pdf"), ("Example Party", 2022): (10.0, "e22.pdf")}
    rows = [{"party": "Example Party", "year": 2023, "declared_total": 219964.7, "document": "a" * 64},
            {"party": "Example Party", "year": 2023, "declared_total": 1.0, "document": "b" * 64},
            {"party": "Example Party", "year": 2022, "declared_total": 11.0, "document": "c" * 64},
            {"party": None, "party_label": "Nobody", "year": 2022, "declared_total": 5.0, "document": "d" * 64}]
    out = check.compare(rows, frozen)
    assert [e["document"][0] for e in out["equal"]] == ["a"]
    assert [o["document"][0] for o in out["other_returns"]] == ["b"]
    assert [d["document"][0] for d in out["differ"]] == ["c"]
    assert [u["document"][0] for u in out["unmatched"]] == ["d"]


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
    return "scratch_gate_party_returns"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    schema = _schema()
    sample.fill_schema(schema, lambda: db.connect(db.OWNER_KEY, "querynz_v4_sample"), REPO, log=lambda *a: None)
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        cur = conn.execute(f"SELECT * FROM {schema}.returns ORDER BY party, year, document")
        rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        aside = conn.execute(f"SELECT document, stage, reason FROM {schema}.set_aside").fetchall()
        yield {"schema": schema, "rows": rows, "aside": aside, "conn": conn}


def _items():
    return [i for i in sample.read_list(os.path.join(LANE, "sample.list")) if not i.startswith("key:")]


def test_every_sample_document_is_a_row_or_set_aside_and_never_both(filled):
    rows = {r["document"] for r in filled["rows"]}
    aside = {a[0] for a in filled["aside"]}
    assert rows | aside == set(_items())
    assert not (rows & aside)
    assert len(rows) >= 20, "the slice reads the text-layer returns; fewer than twenty means the reader broke"


def test_the_mixed_return_is_set_aside_at_recognition(filled):
    stages = {a[0]: (a[1], a[2]) for a in filled["aside"]}
    mixed = [i for i in open(os.path.join(LANE, "sample.list"), encoding="utf-8") if "mixed" in i and not i.startswith("#")][0].split()[0]
    assert stages[mixed][0] == "recognise" and "page reader" in stages[mixed][1]


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for r in filled["rows"]:
        row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
        row["loaded_at"] = r["loaded_at"].isoformat()
        row["filed"] = {"year": r["year"], "declared_total": r["declared_total"]}
        assert rowcontract.validate(row, today) == [], r["key"]
        assert r["key"] == r["document"] + "/declaration" and r["read_from"] == "text"
        assert r["party"] is not None, f"{r['party_label']!r} did not resolve to a registered party"
        assert r["total_check"] in ("parts-sum", "declared-nil")


def test_each_declared_total_equals_the_frozen_site_or_has_a_card(filled):
    assert os.path.exists(check.HOME_JSON), f"the frozen site's figures are read from {check.HOME_JSON}, which is not here"
    out = check.compare(filled["rows"], check.frozen_series())
    assert out["unmatched"] == [], out["unmatched"]
    cards = " ".join(open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(REPO, "cards", "*.md")))
    uncarded = [d for d in out["differ"] if d["document"] not in cards]
    assert uncarded == [], "differences from the frozen site with no card: " + "; ".join(
        f"{d['party']} {d['year']} ours {d['ours']:.2f} frozen {d['frozen']:.2f} document {d['document']}" for d in uncarded)
    assert len(out["equal"]) >= 20


def test_the_published_view_builds_on_the_lane_s_table(filled):
    from registers.party_returns import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema).replace("pub.", f"{schema}."))
    n = conn.execute(f"SELECT count(*) FROM {schema}.party_return_totals").fetchone()[0]
    conn.rollback()
    assert n == len(filled["rows"])


def test_nil_at_step_two_above_the_parts_is_not_a_part_s_figure():
    page = ("   the year ending 31 December 2021\n1.   Party name:\n      Example Party\n"
            "2.   TOTAL PARTY DONATIONS\n"
            "                                                                            Nil              step 3 on this page\n"
            "     Part A: Party donations of more than $15,000                                  $ 0.00\n"
            "     Part C: Anonymous party donations of more than $1,500                         $ 0.00\n"
            "     Part D: Overseas party donations of more than $50                             $ 0.00\n"
            "     Part F: Donations protected from disclosure                                            entered at step 2 and/or step 3\n"
            "                                                                                    $ 0.00\n"
            "     Part G: Other party donations up to $15,000                                   $ 0.00   the return\n"
            "                                              Total (A + C + D + F + G)             $ 0.00   documentation supplied\n")
    d = declaration.read(page)
    assert d.parts == {"A": 0.0, "C": 0.0, "D": 0.0, "F": 0.0, "G": 0.0} and d.total == 0.0 and d.problems() == []


def test_an_ocr_layer_s_mangled_label_words_still_name_the_part():
    page = ("           TE KAITIAKI TAKE KOWHIRI            the year ending 31 December 2020\n1. Party name:\n     Example Party\n"
            "     Part At Party donations of more than $15,000                              $ 769,786.92\n"
            "     Part G! Anoiiymous party donations of more than $1,500                       $0.00\n"
            "     Part D! Overseas party donations of more than $50                            $0.00\n"
            "     Part F: Donations protected from disclosure                                  $0.00       tho return\n"
            "     Part Os Other party donations up to $15,000                                              All relevant supporting\n"
            "                                                                               $ 730,520.63\n"
            "                                                                              $1,500,307.55   Auditor stamped\n"
            "                                              Total(A+C+D+F+G) I\n3. TOTAL PAFiTY LOANS\n")
    d = declaration.read(page)
    assert d.parts == {"A": 769786.92, "C": 0.0, "D": 0.0, "F": 0.0, "G": 730520.63}
    assert d.total == 1500307.55 and d.problems() == []
