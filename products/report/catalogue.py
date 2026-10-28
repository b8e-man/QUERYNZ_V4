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
MONEY_COLUMNS = {"figure"}   # money columns the statement formats that rows.MONEY does not list by name
#: what a Gazette notice's date is, by the lane's event_basis, as the memo words it
ON_BASIS_WORD = {"hearing": "to be heard", "objections by": "objections by", "appointment": "appointed", "ceased to act": "ceased to act",
                 "meeting": "meeting", "claims by": "claims by", "dividend": "dividend", "published": "published"}


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
    on_basis: str = ""          # a column whose value says what `on` dates (a hearing, objections by, an appointment)
    on_label: str = ""          # a fixed word saying what `on` dates, when the view has one meaning
    filed: str = ""             # the day the notice was filed, printed beside
    published: str = ""         # the day the notice was published, printed beside; dates the row when nothing else does
    year: str = ""              # a year column, when that is all the dating a row has
    period: tuple = ()          # (first_file, last_file): the files the row was seen in, when nothing else dates it
    as_in: str = ""             # a column naming the monthly file whose state the row is: dated "as in the file …"
    entity: tuple = ()          # (view, column): the row of another view this row sits on
    entity_col: str = ""        # the parent's column that `entity` joins, when not its key (a notice number)
    role: str = ""              # the column naming the role
    amount: str = ""            # the money column
    statement: str = ""         # the sentence, with {title} {role} {entity} {amount} {year} {party}
    note: str = ""              # a line every item of this view carries
    row_note: str = ""          # a column whose value, when filled, is the item's note (a name field the lane withheld, and why)
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
    V("company_states", "companies", "organisation", ("name",), names=("name",), as_in="file",
      start="registered_on", end="removed_on", entity=("companies", "entity_key"), role="status",
      statement="{title}: an earlier state of {entity}, {status} {entity_type}, as the file {file} carried it; a later file changed it",
      note="the state a monthly file carried before a later file changed it; the day of the change is between the two files' cuts, which the lane does not publish"),
    # ── societies ───────────────────────────────────────────────────────────
    V("societies", "societies", "organisation", ("name",), names=("name",),
      start="registered_on", end="removed_on", statement="{title}: incorporated society, {status}"),
    V("society_officers", "societies", "person", ("full_name",), names=("full_name",), suppressed="suppressed",
      start="started_on", end="ended_on", period=("first_read_on", "last_read_on"), entity=("societies", "society_key"),
      role="role_type", statement="{title}: {role} of {entity} ({role_status})",
      note="a role the register stopped listing keeps its last day read; it is never given an end the register did not state"),
    # ── charities (the register's own open data; its officers and returns sit on the charity) ──
    V("charities", "charities", "organisation", ("name",), names=("name",),
      start="registered_on", end="deregistered_on", statement="{title}: registered charity {number}, {status}; {legal_structure}",
      note="as the Charities Register's feed states it; the address for service is never read here; the charity's business number joins it to its "
           "companies-register row"),
    V("charity_officers", "charities", "person", ("full_name",), names=("full_name", "first_name", "middle_name", "last_name"), suppressed="suppressed",
      start="started_on", end="ended_on", entity=("charities", "charity_key"), role="role", row_note="name_note",
      statement="{title}: {role} of {entity} ({status}; disqualified as the register states it: {disqualified})",
      note="an officer as the register's feed names them, a role and its dates; no address, birth date or contact is held in the view"),
    V("charity_returns", "charities", "figure", ("period_end", "tier"), on="period_end", on_label="period to", amount="total_gross_income",
      entity=("charities", "charity_key"),
      statement="{entity}: annual return, {tier}: gross income {amount}, expenditure {total_expenditure}, net surplus {net_surplus}, "
                "total assets {total_assets}, total liabilities {total_liabilities}, total equity {total_equity}; audited {audited}; opinion {opinion}",
      note="the figures as filed in the return, under the ruling of 14 August 2026; a blank is a field the return did not fill"),
    # ── party returns ───────────────────────────────────────────────────────
    V("party_return_totals", "party_returns", "figure", ("party", "year"), year="year", amount="declared_total",
      statement="{party} return for {year}: declared total {amount}",
      note="an amendment the Commission lists replaces a return; the two are never summed"),
    V("party_return_donors", "party_returns", "figure", ("donor", "amount"), names=("donor",), year="year", amount="amount",
      entity=("party_return_totals", "return_key"), statement="{title} to {party}, in the party's return for {year} (Part A); dates as printed: {dates}"),
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
      entity=("candidate_return_totals", "return_key"), statement="{title} to the candidate {surname} ({electorate}, {party}), return for {year}; dates as printed: {dates}"),
    # ── gazette ─────────────────────────────────────────────────────────────
    V("gazette_liquidations", "gazette", "organisation", ("company",), names=("company",), on="appointed_on", on_label="appointed",
      published="published_on", entity=("companies", "register_key"), statement="{title}: {shape}, appointed by {appointed_by}",
      note="no address, telephone or email is shown or held"),
    V("gazette_company_notices", "gazette", "organisation", ("company", "kind"), names=("company",), on="event_on", on_basis="event_basis",
      filed="filed_on", published="published_on", entity=("companies", "register_key"), statement="{title}: {action}",
      note="an applicant is named only; the date says what it dates: a winding-up application's is the day it is to be heard, a removal's the last day for objections"),
    V("gazette_possessions", "gazette", "event", ("mortgagee", "action"), names=("mortgagee", "mortgagor"), on="entered_on", on_label="entered",
      published="published_on", entity=("companies", "mortgagor_register_key"), role="action",
      statement="{title}, {asset}; mortgagor {mortgagor} ({mortgagor_kind}); {statute}",
      note="a mortgagee's entry into possession as the Gazette states it; a person's name and the property stay in the lane's private tables, "
           "and a company mortgagee or mortgagor is named with its register key"),
    V("gazette_liquidators", "gazette", "person", ("name", "role"), names=("name",), on="published_on",
      entity=("gazette_liquidations", "notice"), entity_col="notice",
      role="role", statement="{title} named in the Gazette notice on {entity}",
      note="a practitioner is named as the notice names them, a business name and a role; never an address"),
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
    # ── MPs' and ministers' expenses (the releases print a name only: reached by name, as near) ──
    V("mp_expenses", "expenses", "figure", ("name", "category"), names=("name",), start="period_start", end="period_end", amount="figure",
      role="role", statement="{title}: {amount}, a member's expenses as released for the period",
      note="the member's period total as the release prints it, and money the release prints outside its total beside it, never added in; "
           "the per-category lines are in pub.mp_expenses and not listed"),
    V("minister_expenses", "expenses", "figure", ("name", "category"), names=("name",), start="period_start", end="period_end", amount="figure",
      role="role", statement="{title}: {amount}, a minister's expenses as released for the period",
      note="the minister's period total as the release prints it, and money the release prints outside its total beside it, never added in; "
           "the per-category lines are in pub.minister_expenses and not listed"),
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
    ("charities", "Charities register, officers and annual returns"),
    ("gazette", "Gazette notices"),
    ("house", "Candidates and the House"),
    ("mp_interests", "MPs' declared interests"),
    ("expenses", "MPs' and ministers' expenses"),
    ("parties", "Registered political parties"),
    ("party_finance", "Registered promoters"),
)
REGISTER_NAME = dict(REGISTERS)

#: registers the plan names that no lane has published yet (step 4.1 and step 5.3), and the registers the
#: templates must say they cannot see: one list, each with the key a template's section cites in `not_held`
NOT_HELD = (
    ("courts", "Court judgments"),
    ("tribunals", "Tribunal decisions (employment, tenancy, environment, coroners)"),
    ("disciplinary", "Disciplinary tribunals' findings (lawyers, conveyancers, the other professional bodies)"),
    ("disputes", "Disputes Tribunal decisions"),
    ("employment", "Employment Relations Authority determinations"),
    ("insolvency", "The Insolvency Register"),
    ("securities", "The Personal Property Securities Register"),
    ("fsp", "Financial service providers"),
    ("linz", "LINZ titles"),
    ("tenders", "Tenders and awards"),
    ("sanctions", "Sanctions lists"),
    ("limited_partnerships", "Limited partnerships' partners (the partnerships themselves are rows of the companies register)"),
    ("building_practitioners", "Licensed building practitioners"),
    ("overseas", "Overseas company registers"),
    ("trusts", "Trusts: no New Zealand register exists"),
    ("unincorporated", "Sole traders, general partnerships and other business-number entities outside the companies file"),
    ("company_history", "The companies change history before 16 August 2026"),
    ("nzbn_interface", "The business-number interface, between monthly files (step 5.5)"),
    ("credit_bureau", "Credit-bureau defaults and payment records"),
    ("worksafe", "WorkSafe prosecutions and enforceable undertakings"),
    ("regulators", "Commerce Commission and Financial Markets Authority actions"),
    ("mpi", "Ministry for Primary Industries prosecutions and animal-tracing enforcement"),
    ("fire", "Fire and Emergency New Zealand notices"),
    # the registers a health regulator keeps (healthcare-1)
    ("retirement_villages", "The retirement villages file: each village's operator and statutory supervisor"),
    ("hdc", "Health and Disability Commissioner decisions"),
    ("certification", "Certification audits of rest homes and hospitals"),
    ("health_providers", "The Ministry of Health's provider registers"),
    ("aged_care_commissioner", "The Aged Care Commissioner's reports"),
    # the registers a property developer check names (property-1); the Real Estate Authority lane captures and publishes no view yet
    ("oio", "Overseas Investment Office decisions"),
    ("building_consents", "Building consents, code compliance certificates and council minutes"),
    ("rea", "Real Estate Authority decisions"),
)
NOT_HELD_NAME = dict(NOT_HELD)
#: not-held keys a template may still cite for a register a lane has since published: {old key: the register}. A template naming one
#: loads, the key is dropped from its section's blank, and the report says the register is published and the template does not read it
SUPERSEDED_NOT_HELD = {"charities": "charities"}

#: what links/ publishes; read through walk, never as a register view
LINKS_VIEWS = frozenset({"links", "groups", "decisions", "names", "old_decisions"})


def views_of(register: str) -> list:
    return [v for v in VIEWS if v.register == register]


def columns_read(v: View) -> set:
    """Every column the report reads from this view; the citation's columns
    are read when present and not demanded (a child may cite through its parent)."""
    out = set(v.title) | set(v.names)
    for c in (v.suppressed, v.withheld, v.start, v.end, v.on, v.on_basis, v.filed, v.published, v.year, v.role, v.amount, v.key_col):
        if c:
            out.add(c)
    out |= {c for c in v.period if c}
    if v.as_in:
        out.add(v.as_in)
    if v.hide_names:
        out.add(v.hide_names[0])
    if v.entity:
        out.add(v.entity[1])
    if v.row_note:
        out.add(v.row_note)
    return out


def fold(term: str) -> str:
    out = (term or "").strip().lower().translate(str.maketrans(MACRONS[0], MACRONS[1]))
    return " ".join(out.split())


#: the board's name for the fold; search.words_of, copied from the board, calls it so
fold_term = fold


#: the links lane's rules in plain words, keyed by the rule id `pub.links` carries without its version: the
#: board's words (products/board/catalogue.py RULE_WORDS, ruling 84), held equal to them by tests/test_related.py
#: for every id both carry; the walk's own rules (same-name, official-number, chain, ...) are not links rules.
RULE_WORDS = {
    "full-name": "same first, middle and last name",
    "name-and-address": "same first and last name, and their companies filed the same registered office",
    "name-only": "same name, nothing else",
    "company-name": "two companies under one name",
    "seat-and-window": "a row the House published and the seat whose term covers it",
    "official-number": "the same official number (NZBN or company number)",
    "organisation-name": "a donation's organisation name is a company's name",
    "declared-directorship": "a member's declared company has a director of the member's name",
    "candidate-name-form": "one name for one party's candidate across elections",
    "filed-name": "two donations filed under one organisation name",
    "source-identifier": "the register's own identifier joins the two rows",
    "member-and-party-donor": "a member's name on a donation to the member's own party, in the term",
    "own-return": "a donor in the candidate's own name, on the candidate's own return",
    "coupled-name": "one of the people a donation filed as two names",
    "organisation-sole-company": "a donation's organisation name and the one company of the name live in its year",   # ruling 106 (1)
    "successor-name": "a company succeeded by another of its name with a year in brackets, a person on both",        # ruling 106 (2), related
    "candidate-same-party": "one candidate name standing for one party in two elections",                            # ruling 106 (3)
    "organisation-one-live-company": "a donation's organisation name and the one of several companies of the name live in its year",   # ruling 107
    "refiled-name": "a company removed and another of its name registered within twelve months, a person on both",   # ruling 109, related
}


def rule_text(rule) -> str:
    """A links rule as the memo names it: "a company succeeded by … (links rule
    successor-name, version 1)"; a rule that is not a links rule (the walk's
    own: same-name, official-number, chain, …, which carry no version) as it is."""
    rid, at, version = str(rule or "").partition("@")
    if not at or rid not in RULE_WORDS:
        return str(rule or "")
    return f"{RULE_WORDS[rid]} (links rule {rid}, version {version})"
