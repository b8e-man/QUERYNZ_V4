"""What the report knows about each published view it may read: the
register it belongs to, what a row is, how a row is titled, which columns
are names (and when they are suppressed), which columns date the connection
the row makes, which row of another view it sits on (a role sits on a
company, a donation on a return), and the sentence that states it. Written
from each lane's `pane.md`; the report reads only `pub.*` (the one-way
test). Pure data and pure functions: no database here.

A register the plan names but no lane has published yet is listed under
NOT_HELD so a blank can say "not held" rather than "none found"."""
from __future__ import annotations

from dataclasses import dataclass

MACRONS = ("āēīōūĀĒĪŌŪ", "aeiouAEIOU")


@dataclass(frozen=True)
class View:
    name: str                   # the pub view
    register: str               # the lane folder, as the board and pub.names name it
    kind: str                   # person | organisation | figure | event | place | document
    title: tuple                # columns joined with ' · ' for the row's title
    names: tuple = ()           # name columns: replaced by "name suppressed" when the row is suppressed
    suppressed: str = ""        # a column that, when true, suppresses every name column
    hide_names: tuple = ()      # (column, regex): names hidden when the column's value matches
    withheld: str = ""          # a column that, when true, hides `text`
    start: str = ""             # the date the connection begins, as filed
    end: str = ""               # the date it ends, as filed
    on: str = ""                # one date the row is dated by (published, received, polled)
    year: str = ""              # a year column, when that is all the dating a row has
    period: tuple = ()          # (first_file, last_file): the files the row was seen in, when nothing else dates it
    entity: tuple = ()          # (view, column): the row of another view this row sits on
    role: str = ""              # the column naming the role
    amount: str = ""            # the money column
    statement: str = ""         # the sentence, with {title} {role} {entity} {amount} {year} {party}
    note: str = ""              # a line every item of this view carries
    key_col: str = "key"


V = View
VIEWS: tuple = (
    # ── companies (copied; the original file is not held) ───────────────────
    V("companies", "companies", "organisation", ("name",), names=("name",),
      start="registered_on", end="removed_on", statement="{title}: {status} {entity_type}, NZBN {nzbn}",
      note="taken from the old estate's tables; original not held"),
    V("directors", "companies", "person", ("full_name",), names=("full_name",), suppressed="suppressed",
      start="appointed_on", end="ended_on", period=("first_file", "last_file"), entity=("companies", "entity_key"),
      role="role_type", statement="{title}: {role} of {entity}",
      note="a role that has left the latest file carries no end date: the file states none"),
    V("shareholders", "companies", "person", ("name",), names=("name",), suppressed="suppressed",
      period=("first_file", "last_file"), entity=("companies", "entity_key"), role="shareholder_type",
      statement="{title}: shareholder of record in {entity}, {shares} shares, {allocation_status}",
      note="a shareholding is shown as the register states it: a holder of record, never an owner"),
    V("company_addresses", "companies", "place", ("line_1", "line_2", "line_3", "line_4"),
      start="started_on", period=("", "last_file"), entity=("companies", "entity_key"), role="kind",
      statement="{entity}: {role} at {title}",
      note="a company's registered office; no residential address is held in any published table"),
    # ── societies ───────────────────────────────────────────────────────────
    V("societies", "societies", "organisation", ("name",), names=("name",),
      start="registered_on", end="removed_on", statement="{title}: incorporated society, {status}"),
    V("society_officers", "societies", "person", ("full_name",), names=("full_name",), suppressed="suppressed",
      start="started_on", end="ended_on", period=("first_read_on", "last_read_on"), entity=("societies", "society_key"),
      role="role_type", statement="{title}: {role} of {entity} ({role_status})",
      note="a role the register stopped listing keeps its last day read; it is never given an end the register did not state"),
    # ── party returns ───────────────────────────────────────────────────────
    V("party_return_totals", "party_returns", "figure", ("party", "year"), year="year", amount="declared_total",
      statement="{party} return for {year}: declared total {amount}",
      note="an amendment the Commission lists replaces a return; the two are never summed"),
    V("party_return_donors", "party_returns", "figure", ("donor", "amount"), names=("donor",), year="year", amount="amount",
      entity=("party_return_totals", "return_key"), statement="{title} to {party}, in the party's return for {year} (Part A)"),
    V("party_return_loans", "party_returns", "figure", ("lender", "amount"), names=("lender",), year="year", amount="amount",
      entity=("party_return_totals", "return_key"), statement="{title} lent to {party}, in the party's return for {year}"),
    # ── large-donation disclosures ──────────────────────────────────────────
    V("disclosures", "disclosures", "figure", ("donor_name", "party"), names=("donor_name",), on="received_on", amount="amount",
      statement="{title}: large-donation disclosure, {amount}, received by the Commission {on}",
      note="an amended declaration is one row with the amended figures; never summed with its original, and never added to a return that covers the same gift"),
    V("disclosure_items", "disclosures", "figure", ("contributor", "amount"), names=("contributor",), on="first_date", amount="amount",
      entity=("disclosures", "declaration"), statement="{title}: a contribution itemised in a disclosure"),
    # ── candidate returns ───────────────────────────────────────────────────
    V("candidate_return_totals", "candidate_returns", "figure", ("surname", "given_names", "electorate", "year"),
      names=("surname", "given_names"), year="year", amount="donations",
      statement="{title}: candidate return, donations {amount}",
      note="a replaced return shows the amendment the Commission links in its place and is never summed"),
    V("candidate_return_donors", "candidate_returns", "figure", ("donor", "amount"), names=("donor",), year="year", amount="amount",
      entity=("candidate_return_totals", "return_key"), statement="{title} to the candidate {surname} ({electorate}, {party}), return for {year}"),
    # ── gazette ─────────────────────────────────────────────────────────────
    V("gazette_liquidations", "gazette", "organisation", ("company",), names=("company",), on="appointed_on",
      entity=("companies", "register_key"), statement="{title}: {shape}, appointed by {appointed_by}",
      note="no address, telephone or email is shown or held"),
    V("gazette_company_notices", "gazette", "organisation", ("company", "kind"), names=("company",), on="event_on",
      entity=("companies", "register_key"), statement="{title}: {action}", note="an applicant is named only"),
    V("gazette_liquidators", "gazette", "person", ("name", "role"), names=("name",), on="published_on",
      role="role", statement="{title} named in a Gazette notice"),
    V("gazette_practitioners", "gazette", "person", ("name", "role"), names=("name",), on="published_on",
      role="role", statement="{title} named in a Gazette notice"),
    V("gazette_prohibitions", "gazette", "person", ("name", "action"), names=("name", "also_known_as"),
      hide_names=("superseded_how", "^revoked"), start="starts_on", end="ends_on", role="action",
      statement="{title} ({statute})", note="a person a later notice revoked is not shown"),
    V("gazette_bankruptcies", "gazette", "person", ("surname", "given_names"), names=("surname", "given_names", "also_known_as"),
      hide_names=("withheld_by", "."), on="event_on", role="kind", statement="{title}: {kind} ({shape})",
      note="a person a later annulment names is withheld on every earlier row"),
    V("gazette_appointments", "gazette", "person", ("name", "role"), names=("name",), start="starts_on", end="ends_on",
      role="role", statement="{title}, {body}", note="where an appointee lives is never kept"),
    # ── the House ───────────────────────────────────────────────────────────
    V("candidates", "house", "person", ("display_name", "election"), names=("display_name", "name"), year="election",
      statement="{title}: stood for {party} in {electorate}"),
    V("members", "house", "person", ("display_name", "route"), names=("display_name", "name"), start="from_on", end="ended_on",
      statement="{title}: sat for {party} ({electorate})", note="the day a seat actually ended is in no file this lane holds"),
    # ── MPs' interests ──────────────────────────────────────────────────────
    V("mp_interest_returns", "mp_interests", "person", ("name", "as_at"), names=("name",), on="as_at",
      statement="{title}: return of pecuniary interests, {declarations} declarations"),
    V("mp_interests", "mp_interests", "figure", ("heading", "name"), names=("name",), withheld="withheld", on="as_at",
      entity=("mp_interest_returns", "member_return"), statement="{heading}: {text}",
      note="the category is the heading, never the number: the register renumbered in 2018"),
    # ── parties and promoters ───────────────────────────────────────────────
    V("parties", "parties", "organisation", ("name",), names=("name",), start="registered_on", end="cancelled_on",
      statement="{title}: registered political party, {status}", note="never the secretary's contact lines"),
    V("promoters", "party_finance", "organisation", ("promoter", "year"), names=("promoter",), on="registered_on",
      statement="{title}: registered promoter", note="never an email or an address"),
    V("promoter_people", "party_finance", "person", ("name", "role"), names=("name",), year="year",
      entity=("promoters", "promoter_key"), role="role", statement="{title} of {entity}"),
)
BY_NAME = {v.name: v for v in VIEWS}

#: the registers, in the order the memo lists them, with a plain name each
REGISTERS = (
    ("party_returns", "Party donation and loan returns"),
    ("disclosures", "Large-donation disclosures"),
    ("candidate_returns", "Candidate donation and expense returns"),
    ("companies", "Companies, directors and shareholders"),
    ("societies", "Incorporated societies and their officers"),
    ("gazette", "Gazette notices"),
    ("house", "Candidates and the House"),
    ("mp_interests", "MPs' declared interests"),
    ("parties", "Registered political parties"),
    ("party_finance", "Registered promoters"),
)
REGISTER_NAME = dict(REGISTERS)

#: registers the plan names that no lane has published yet (step 4.1 and step 5.3)
NOT_HELD = (
    ("charities", "Charities register and officers"),
    ("courts", "Court judgments"),
    ("insolvency", "The Insolvency Register"),
    ("securities", "The Personal Property Securities Register"),
    ("fsp", "Financial service providers"),
    ("linz", "LINZ titles"),
    ("tenders", "Tenders and awards"),
    ("sanctions", "Sanctions lists"),
    ("limited_partnerships", "Limited partnerships register"),
    ("building_practitioners", "Licensed building practitioners"),
)
NOT_HELD_NAME = dict(NOT_HELD)

#: what links/ publishes; read through walk, never as a register view
LINKS_VIEWS = frozenset({"links", "groups", "decisions", "names", "old_decisions"})


def views_of(register: str) -> list:
    return [v for v in VIEWS if v.register == register]


def columns_read(v: View) -> set:
    """Every column the report reads from this view; the citation's columns
    are read when present and not demanded (a child may cite through its parent)."""
    out = set(v.title) | set(v.names)
    for c in (v.suppressed, v.withheld, v.start, v.end, v.on, v.year, v.role, v.amount, v.key_col):
        if c:
            out.add(c)
    out |= {c for c in v.period if c}
    if v.hide_names:
        out.add(v.hide_names[0])
    if v.entity:
        out.add(v.entity[1])
    return out


def fold(term: str) -> str:
    out = (term or "").strip().lower().translate(str.maketrans(MACRONS[0], MACRONS[1]))
    return " ".join(out.split())
