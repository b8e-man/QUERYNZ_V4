"""The reading on fakes that copy the abstract page's own markup (read 2 November 2026) with invented names: one decision
and its parties per abstract; an agency told from a person; counsel never a party; a suppression order withholds every
name, number and the penalty text, a request declined does not; the reasoning and the complainant are never kept; a
street address in the penalty is flagged; a page of another shape is set aside; the profile is pinned both ways."""
import json
import os

import pytest

from registers.real_estate_authority import capture as C
from registers.real_estate_authority import load as L
from registers.real_estate_authority import read as R

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = "a" * 64
CASE = {"case_id": 99001, "year": 2024, "decision_date": "2024-12-09", "body": "Disciplinary Tribunal Hearing"}


def pair(label, value):
    return (f'<div class="pure-g" style="margin-bottom: 5px"><div class="pure-u-sm-1-3"><h4 >{label}</h4></div>'
            f'<div class="pure-u-sm-2-3">\n\t\t\t\t<p>\n{value}\n\t\t\t\t</p>\n            </div>\n\t\t</div>')


def abstract(*pairs, sub="Appeal Decision by the Real Estate Agents Disciplinary Tribunal:&nbsp; [2024] NZREADT 47",
             complaint="C99001"):
    head = (f'<div class="pure-u-md-1-1"><h3>Complaint Number:&nbsp; {complaint}</h3>\n'
            f'<h4 style="margin-top:0px;">{sub}</h4></div>')
    history = pair("COMPLAINT HISTORY", '<table><tr><td style="width:120px;padding-right:0px;">09 Dec 2024: </td>'
                   '<td style="padding-left:0px;">Real Estate Agents Disciplinary Tribunal Appeal '
                   '<a href="/reaa/pdfs/C99001_Decision.pdf">Decision</a> 160k</td></tr>'
                   '<tr><td>28 Oct 2022: </td><td>Complaint</td></tr></table>')
    return ("<html><body>" + head + "".join(pairs) + history + "</body></html>").encode()


AGENT = pair("AGENT", 'Alex Example (Licensee <a href="https://publicregister.rea.govt.nz/?lic=10000001">10000001</a>)'
                      '<br/>Sample Realty Limited (Agency) (Licensee <a href="x">20000002</a>)<br/>'
                      'Represented by: Counsel Person<br/><br/><a href="x">Search the public register &gt;&gt;</a>')
DECISION = pair("DECISION", "Unsatisfactory Conduct<br/><em>READT upheld CAC decision</em>")
PENALTY = pair("PENALTY", "The Committee fined Mr Example $1,500<em> / Fines</em>")
REASONING = pair("REASONING", "The purchasers complained about a cottage meter.<em> / Misleading</em>")
COMPLAINANT = pair("COMPLAINANT", "Pat Member")
ACT = pair("REAL ESTATE AGENTS ACT (2008) - SECTIONS CITED",
           '[<a href="http://x" title="Section text">s89(2)(b)</a>] a determination<br/>[<a href="y">s111</a>] &nbsp; Appeal')


def test_a_decision_and_its_parties_are_read_counsel_is_not_a_party_and_reasoning_and_complainant_kept_privately():
    out = R.read_abstract(abstract(AGENT, DECISION, PENALTY, REASONING, COMPLAINANT, ACT), SHA, 1, CASE)
    d = out["decision"]
    assert (d["complaint_number"], d["decided_by"], d["appeal"], d["citation"]) == (
        "C99001", "Real Estate Agents Disciplinary Tribunal", True, "[2024] NZREADT 47")
    assert d["decision"] == "Unsatisfactory Conduct" and d["decision_note"] == "READT upheld CAC decision"
    assert d["penalty"] == "The Committee fined Mr Example $1,500" and d["penalty_kinds"] == ["Fines"]
    assert d["act_sections"] == ["s89(2)(b)", "s111"] and not d["suppressed"]
    assert d["history"][0] == {"on": "2024-12-09", "step": "Real Estate Agents Disciplinary Tribunal Appeal Decision",
                               "pdfs": ["/reaa/pdfs/C99001_Decision.pdf"]}
    names = [(p["name"], p["kind"], p["licence_number"], p["role"]) for p in out["parties"]]
    assert names == [("Alex Example", "person", "10000001", "licensee"),
                     ("Sample Realty Limited", "agency", "20000002", "licensee")]
    flat = json.dumps({"decision": d, "parties": out["parties"]}, default=str)
    assert "cottage meter" not in flat and "Pat Member" not in flat and "Counsel Person" not in flat
    # ruling 142: the reasoning text and the complainant are kept whole in the private twin (they were never kept)
    kept = {f["label"]: f["text"] for f in out["abstract_fields"]}
    assert "cottage meter" in kept["REASONING"] and kept["COMPLAINANT"] == "Pat Member" and "PENALTY" not in kept


def test_a_licence_number_printed_in_its_own_brackets_is_read():
    p = pair("AGENT", "Sample Homes (2010) Limited t/a Sample Realty (Agency) (Licensee (10050442) )<br/>")
    got = R.read_abstract(abstract(p, DECISION), SHA, 1, CASE)["parties"]
    assert [(x["name"], x["kind"], x["licence_number"]) for x in got] == [
        ("Sample Homes (2010) Limited t/a Sample Realty", "agency", "10050442")]


def test_a_suppression_order_withholds_names_numbers_and_penalty_a_request_declined_does_not():
    ordered = pair("PENALTY", "Censure and fine of $1,500. Orders made suppressing the licensee’s name<em> / Fines</em>")
    out = R.read_abstract(abstract(AGENT, DECISION, ordered), SHA, 1, CASE)
    assert out["decision"]["suppressed"] and out["decision"]["penalty"] is None
    assert all(p["name"] is None and p["licence_number"] is None and p["suppressed"] for p in out["parties"])
    # ruling 142: the names, numbers and penalty the order covers are kept whole in the private twin, keyed by the rows
    priv = {x["key"]: x for x in out["suppressed_parties"]}
    assert [priv[p["key"]]["name"] for p in out["parties"]] == ["Alex Example", "Sample Realty Limited"]
    assert priv[out["parties"][0]["key"]]["licence_number"] == "10000001"
    assert "$1,500" in {f["label"]: f["text"] for f in out["abstract_fields"]}["PENALTY"]
    declined = pair("REASONING", "In relation to the Licensee’s request for suppression, the Committee considers that "
                                 "there is insufficient reason to grant it.")
    out = R.read_abstract(abstract(AGENT, DECISION, PENALTY, declined), SHA, 1, CASE)
    assert not out["decision"]["suppressed"] and out["parties"][0]["name"] == "Alex Example"


def test_a_prosecution_s_defendant_is_a_party_and_a_committee_decision_has_no_citation():
    out = R.read_abstract(abstract(pair("DEFENDANT", "Example Homes Limited<br/><br/>Search the public register &gt;&gt;"),
                                   pair("DECISION", "Charges Proven"), pair("SENTENCE", "Fine of $13,000<em> / Fines</em>"),
                                   pair("JUDGE", "Judge Example"),
                                   sub="Decision by the Complaints Assessment Committee (CAC)"), SHA, 1, CASE)
    d = out["decision"]
    assert d["decided_by"] == "Complaints Assessment Committee" and not d["appeal"] and d["citation"] is None
    assert d["penalty"] == "Fine of $13,000" and d["chairperson"] == "Judge Example"
    assert [(p["name"], p["role"], p["kind"]) for p in out["parties"]] == [("Example Homes Limited", "defendant", "organisation")]


def test_a_prosecution_heading_with_no_complaint_number_is_read():
    """Nine abstracts held (2 November 2026) print the court's heading as their <h3> and no complaint number."""
    page = ('<div class="pure-u-md-1-1"><h3>Appeal Decision by the High Court (Wellington):&nbsp; CRI 2011-485-82</h3>'
            + pair("DEFENDANT", "Pat Defendant <br/><a>Search the public register &gt;&gt;</a>")
            + pair("CHARGE", "Unlicensed trading<em> / Offence</em>") + pair("DECISION", "Charges Proven")).encode()
    assert R.recognise(page)
    d = R.read_abstract(page, SHA, 1, CASE)
    assert (d["decision"]["complaint_number"], d["decision"]["decided_by"], d["decision"]["citation"], d["decision"]["appeal"]) == (
        None, "High Court (Wellington)", "CRI 2011-485-82", True)
    assert [(p["name"], p["kind"], p["role"]) for p in d["parties"]] == [("Pat Defendant", "person", "defendant")]
    assert not R.recognise(b"<h3>Appeal Decision by the High Court:</h3>" + pair("DECISION", "x").encode()), "no defendant: not this shape"


def test_a_street_address_in_the_penalty_is_flagged_beside_it():
    p = pair("PENALTY", "Refund the deposit for 12 Example Street to the purchaser<em> / Refund</em>")
    assert R.read_abstract(abstract(DECISION, p), SHA, 1, CASE)["decision"]["penalty_names_address"]
    assert not R.read_abstract(abstract(DECISION, PENALTY), SHA, 1, CASE)["decision"]["penalty_names_address"]


def test_the_profile_is_pinned_both_ways():
    assert R.recognise(abstract(DECISION))
    listing = b'<div class="container dn-results"><h4>Complaints Assessment Committee Hearing</h4>Search Results (3)</div>'
    assert not R.recognise(listing)
    assert not R.recognise(b"<h3>Complaint Number: C1</h3>" + DECISION.encode()), "no complaint history: not this shape"
    out = R.read_abstract(listing, SHA, 1, CASE)
    assert out["decision"] is None and out["set_aside"][0]["stage"] == "recognise"
    with open(os.path.join(LANE, "profile-proposed.jsonl"), encoding="utf-8") as f:
        prof = [json.loads(l) for l in f if l.strip()]
    assert [p["slug"] for p in prof] == [R.PROFILE] and prof[0]["version"] == 1


def test_the_capture_makes_only_its_own_tables_and_the_reading_s_are_apart():
    cap, rd = C.tables_sql("s"), C.reading_sql("s")
    assert "s.cases" in cap and "s.decisions" not in cap and "s.parties" not in cap
    assert "s.decisions" in rd and "s.parties" in rd and "s.read_set_aside" in rd and "s.cases" not in rd


def test_the_build_reconciles_and_every_column_is_one_the_reader_writes():
    out = R.read_abstract(abstract(AGENT, DECISION, PENALTY), SHA, 1, CASE)
    assert set(L.COLUMNS["decisions"]) <= set(out["decision"])
    assert set(L.COLUMNS["parties"]) <= set(out["parties"][0])


def test_the_published_views_withhold_a_suppressed_name_and_carry_no_reasoning_or_complainant():
    with open(os.path.join(LANE, "publish.sql"), encoding="utf-8") as f:
        sql = f.read().lower()
    assert "create or replace view pub.rea_decisions" in sql and "create or replace view pub.rea_parties" in sql
    assert "when p.suppressed then 'name withheld by the authority'" in sql
    assert "when d.suppressed then null else d.penalty" in sql
    body = "\n".join(l for l in sql.splitlines() if not l.startswith("--") and "comment on" not in l and not l.startswith("  '"))
    assert "reasoning" not in body and "complainant" not in body
