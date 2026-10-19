"""Which document profile a held file is, by its shape and never by a
reading (contract: the document profile, 2; profiles before readers).

An HTML page is known by its landmarks (the results site's element ids and
classes, vote.nz's accordion), the workbook by its one sheet's header row,
the PDF by its page count and text layer, Stats NZ's files by their name
fields. Every file is exactly one of:

  a profile this lane reads                 PROFILES
  a page this lane holds and does not read  NOT_READ (the reason)
  a failed read                             FAILED (a challenge, a Not Found)

and a file that is none of them is a catch-log line ("not recognised").

    recognise(data, name)   (what, reason): what is a profile slug, a NOT_READ kind or a FAILED kind
"""
import json
import re
import xml.etree.ElementTree as ET
import zipfile

from registers.house import workbook

PROFILES = (
    "ec-results-overall", "ec-results-electorate-status", "ec-results-successful-candidates",
    "ec-results-electorate-page", "ec-results-elections-index", "ec-byelection-result-page",
    "ec-electorate-candidates-workbook", "votenz-party-lists-page", "ec-party-lists-pdf",
    "ec-candidate-lists-release", "statsnz-electorates-2020",
)
NOT_READ = {
    "advance-votes": "the advance-vote count: a part of the official count, no candidate or seat in it",
    "referendums": "the 2020 referendums: no candidate or seat in it",
    "overall-root": "the results site's front page for that election: the same report as its index page",
}
FAILED = {
    "challenge": "the results site answered with a challenge page; a challenged read is a failed read",
    "not-found": "the results site answered Not Found",
    "fetch-error": "the old job's browser failed before the page loaded; it kept only its error",
}


def _has(t: str, *marks) -> bool:
    return all(m in t for m in marks)


def _html(data: bytes, name: str):
    t = data.decode("utf-8", "replace")
    if t.lstrip().startswith("<!-- fetch error:"):
        return "fetch-error", FAILED["fetch-error"]
    if "cf-error-details" in t or "<title>Attention Required! | Cloudflare</title>" in t:
        return "challenge", FAILED["challenge"]
    if re.search(r"<title>\s*404 Not Found", t) or _has(t, "<h1>Not Found</h1>"):
        return "not-found", FAILED["not-found"]
    if 'id="electorate_details_table"' in t and 'id="partyCandidatesResultsTable"' in t:
        return "ec-results-electorate-page", ""
    if 'id="electorate_details_table"' in t and 'id="by_election_table"' in t:
        return "ec-byelection-result-page", ""
    if 'id="successful_candidates_table"' in t:
        return "ec-results-successful-candidates", ""
    if 'id="electorate-status-table"' in t:
        return "ec-results-electorate-status", ""
    if 'id="referendum-results-table"' in t:
        return "referendums", NOT_READ["referendums"]
    if 'id="overall-results-table"' in t:
        if re.search(r"electionresults-\d{4}\.html$", name):
            return "overall-root", NOT_READ["overall-root"]
        return "ec-results-overall", ""
    if re.search(r"<th[^>]*>\s*List Seats", t) and re.search(r"<th[^>]*>\s*Electorate Seats", t):
        return "advance-votes", NOT_READ["advance-votes"]
    if 'class="accordion__title"' in t and "<ol>" in t:
        return "votenz-party-lists-page", ""
    if re.search(r"<td[^>]*>\s*<strong>\s*Registered party", t):
        return "ec-candidate-lists-release", ""
    if re.search(r"<h3>\s*General Elections\s*</h3>", t) and re.search(r"<h3>\s*By-elections\s*</h3>", t):
        return "ec-results-elections-index", ""
    return None, "not recognised: no profile's landmarks are on the page"


def _xlsx(data: bytes):
    try:
        first = workbook.rows(data)[:1]
    except (zipfile.BadZipFile, KeyError, IndexError, ET.ParseError):
        return None, "not recognised: not a workbook"
    if first and [c.strip() for c in first[0][1][:3]] == ["Name", "Electorate", "Party"]:
        return "ec-electorate-candidates-workbook", ""
    return None, "not recognised: a workbook whose header is not Name, Electorate, Party"


def _pdf(data: bytes):
    pages = len(re.findall(rb"/Type\s*/Page(?![s\w])", data))
    if 1 <= pages <= 6 and b"/Font" in data:
        return "ec-party-lists-pdf", ""
    return None, f"not recognised: a PDF of {pages} pages"


def _geojson(data: bytes):
    try:
        d = json.loads(data)
        props = d["features"][0]["properties"]
    except (ValueError, KeyError, IndexError, TypeError):
        return None, "not recognised: not a feature collection"
    if {"GED2020_V1_00", "GED2020_V1_00_NAME"} <= set(props) or {"MED2020_V1_00", "MED2020_V1_00_NAME"} <= set(props):
        return "statsnz-electorates-2020", ""
    return None, "not recognised: a feature collection without Stats NZ's 2020 electorate fields"


def recognise(data: bytes, name: str) -> tuple:
    n = name.lower()
    if n.endswith((".html", ".htm")):
        return _html(data, n)
    if n.endswith(".xlsx"):
        return _xlsx(data)
    if n.endswith(".pdf") or data[:5] == b"%PDF-":
        return _pdf(data)
    if n.endswith(".geojson"):
        return _geojson(data)
    return None, "not recognised: no profile for this kind of file"
