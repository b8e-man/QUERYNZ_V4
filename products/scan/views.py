"""What a scan knows about each published view it may read: the register
the row belongs to (the prefix of its ref, as `pub.names` and `pub.groups`
name a row), what a row is, how it is titled, which columns are names and
when they are suppressed, which columns date it, and which columns cite it.
Written from each lane's publish.sql; a scan reads `pub.*` only (the
one-way test). Pure data and pure functions: no database here.

The subject report keeps a fuller catalogue of the same views in its own
folder; a product may not import another product's, so this one holds
what a scan needs (carded: a shared catalogue of the published views)."""
from __future__ import annotations

import re
from dataclasses import dataclass

MACRONS = ("āēīōūĀĒĪŌŪ", "aeiouAEIOU")
COLUMN = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
#: a column a scan never reads, whatever a template says (hard limit 15): a home address lives in no published view, but
#: an address-shaped column of any kind stays out of a list
ADDRESS_COLUMN = re.compile(r"address|street|suburb|postal|^line_\d|postcode|residential", re.I)


@dataclass(frozen=True)
class View:
    name: str                   # the pub view
    register: str               # the ref prefix: `<register>:<key>`
    kind: str                   # person | organisation | figure | event
    title: tuple                # columns joined with ' · ' for the row's title
    names: tuple = ()           # name columns: shown as "name suppressed" when the row is suppressed
    suppressed: str = ""        # a column that, when true, suppresses every name column
    start: str = ""             # the date the row's connection begins, as filed
    end: str = ""               # the date it ends, as filed
    on: str = ""                # one date the row is dated by
    on_label: str = ""          # what `on` dates
    on_basis: str = ""          # a column whose value says what `on` dates
    published: str = ""         # the day a notice was published
    year: str = ""              # a year column, when that is all the dating a row has
    period: tuple = ()          # (first_file, last_file): the files the row was seen in, when nothing else dates it
    url: str = ""               # a column carrying the source's own page for the row
    person_row: bool = False    # True when pub.names carries the view's rows (a person step may land on it)
    key_col: str = "key"


V = View
VIEWS: tuple = (
    V("companies", "companies", "organisation", ("name",), names=("name",), start="registered_on", end="removed_on", period=("first_file", "last_file")),
    V("directors", "companies", "person", ("full_name",), names=("full_name",), suppressed="suppressed", start="appointed_on", end="ended_on",
      period=("first_file", "last_file"), person_row=True),
    V("shareholders", "companies", "person", ("name",), names=("name",), suppressed="suppressed", period=("first_file", "last_file"), person_row=True),
    V("societies", "societies", "organisation", ("name",), names=("name",), start="registered_on", end="removed_on"),
    V("society_officers", "societies", "person", ("full_name",), names=("full_name",), suppressed="suppressed", start="started_on", end="ended_on",
      period=("first_read_on", "last_read_on"), person_row=True),
    V("charities", "charities", "organisation", ("name",), names=("name",), start="registered_on", end="deregistered_on"),
    V("charity_officers", "charities", "person", ("full_name",), names=("full_name",), suppressed="suppressed", start="started_on", end="ended_on"),
    V("party_return_totals", "party_returns", "figure", ("party", "year"), year="year"),
    V("party_return_donors", "party_returns", "figure", ("donor",), names=("donor",), year="year", person_row=True),
    V("party_return_loans", "party_returns", "figure", ("lender",), names=("lender",), year="year"),
    V("disclosures", "disclosures", "figure", ("donor_name", "party"), names=("donor_name",), on="received_on", on_label="received", url="href", person_row=True),
    V("disclosure_items", "disclosures", "figure", ("contributor",), names=("contributor",), on="first_date", person_row=True),
    V("candidate_return_totals", "candidate_returns", "figure", ("surname", "given_names", "electorate", "year"), names=("surname", "given_names"),
      year="year", person_row=True),
    V("candidate_return_donors", "candidate_returns", "figure", ("donor",), names=("donor",), year="year", person_row=True),
    V("gazette_liquidations", "gazette", "organisation", ("company",), names=("company",), on="appointed_on", on_label="appointed", published="published_on"),
    V("gazette_company_notices", "gazette", "organisation", ("company", "kind"), names=("company",), on="event_on", on_basis="event_basis", published="published_on"),
    V("gazette_liquidators", "gazette", "person", ("name", "role"), names=("name",), on="published_on", on_label="published", person_row=True),
    V("gazette_prohibitions", "gazette", "person", ("name", "action"), names=("name",), start="starts_on", end="ends_on", person_row=True),
    V("gazette_bankruptcies", "gazette", "person", ("surname", "given_names"), names=("surname", "given_names"), on="event_on", person_row=True),
    V("gazette_appointments", "gazette", "person", ("name", "role"), names=("name",), start="starts_on", end="ends_on", person_row=True),
    V("candidates", "house", "person", ("display_name", "election"), names=("display_name",), year="election", person_row=True),
    V("members", "house", "person", ("display_name", "route"), names=("display_name",), start="from_on", end="ended_on", person_row=True),
    V("mp_interest_returns", "mp_interests", "person", ("name", "as_at"), names=("name",), on="as_at", on_label="as at", person_row=True),
    V("mp_interests", "mp_interests", "figure", ("heading", "name"), names=("name",), on="as_at", on_label="as at", person_row=True),
    V("parties", "parties", "organisation", ("name",), names=("name",), start="registered_on", end="cancelled_on"),
    V("promoters", "party_finance", "organisation", ("promoter", "year"), names=("promoter",), on="registered_on", on_label="registered"),
    V("promoter_people", "party_finance", "person", ("name", "role"), names=("name",), year="year", person_row=True),
)
BY_NAME = {v.name: v for v in VIEWS}
#: what links/ publishes: read for a person or link step, never as a register of answers
LINKS_VIEWS = ("links", "groups", "names")
ON_BASIS_WORD = {"hearing": "to be heard", "objections by": "objections by", "appointment": "appointed", "ceased to act": "ceased to act",
                 "meeting": "meeting", "claims by": "claims by", "dividend": "dividend", "published": "published"}
REGISTER_NAME = {
    "companies": "Companies, directors and shareholders", "societies": "Incorporated societies and their officers",
    "charities": "Charities and their officers", "party_returns": "Party donation and loan returns",
    "disclosures": "Large-donation disclosures", "candidate_returns": "Candidate donation and expense returns",
    "gazette": "Gazette notices", "house": "Candidates and the House", "mp_interests": "MPs' declared interests",
    "parties": "Registered political parties", "party_finance": "Registered promoters",
}


def columns_read(v: View) -> set:
    """Every column the shape itself reads from this view."""
    out = set(v.title) | set(v.names) | {v.key_col, "document", "page", "place"}
    for c in (v.suppressed, v.start, v.end, v.on, v.on_basis, v.published, v.year, v.url):
        if c:
            out.add(c)
    out |= {c for c in v.period if c}
    return out


def fold(term: str) -> str:
    out = (term or "").strip().lower().translate(str.maketrans(MACRONS[0], MACRONS[1]))
    return " ".join(out.split())


def ref_of(v: View, key) -> str:
    return f"{v.register}:{key}"
