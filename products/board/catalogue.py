"""What the board knows about each published view: which register it
belongs to, how a row is titled, which columns are searched, which are
shown, which are dates, which cite the document, and which other rows of
the same register it points at. Written from each lane's `pane.md`; the
board reads only `pub.*` (the one-way test). Pure data and pure functions:
no database here.

A register the plan names but no lane has published yet is listed under
NOT_HELD so the first pane can say "not held" rather than nothing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MACRONS = ("āēīōūĀĒĪŌŪ", "aeiouAEIOU")   # the fold the SQL applies before matching


@dataclass(frozen=True)
class Join:
    """Rows of another view, in the same register, that belong under this
    one: `view.column = this row's <key_column>`; a tuple of columns on both
    sides matches each pair (a Hansard turn's section is its day and index)."""
    label: str
    view: str
    column: str | tuple
    key_column: str | tuple = "key"
    order: str = "key"

    def pairs(self) -> tuple:
        """((far column, this row's column), ...)."""
        far = (self.column,) if isinstance(self.column, str) else tuple(self.column)
        own = (self.key_column,) if isinstance(self.key_column, str) else tuple(self.key_column)
        return tuple(zip(far, own))


@dataclass(frozen=True)
class Relation:
    """A connection the register itself asserts between this view's row and a
    row of another view: `pub.<view>.<to_column> = this row's <column>`. The
    graph tab draws one edge per match (ruling 80), typed by `kind`; a new
    lane adds a line here and no code. Never an address, and never a name
    the board matches by looking (plan 4.9: no link is made by looking)."""
    kind: str                       # one of EDGE_KINDS
    column: str                     # this row's column naming the far end
    view: str                       # the far end's pub view
    to_column: str = "key"          # the far end's column it is matched to
    label: str = ""                 # what the edge says, read from this row to the far end


#: the edge types the graph draws, in the key's order, with their colour and stroke (ruling 86 (1): night mode):
#: the categorical palette's dark blue, orange and aqua, with yellow, magenta and violet stepped lighter so that
#: every pair, not only neighbours in the key, is 15 or more apart in OKLab (x100) and each is 3:1 or more on the
#: picture's surface (tests/test_night.py); same person shares one hue, solid or dashed; lineage, a lime 19 apart from every other. Every edge also carries its words, its tooltip and its line in the list.
EDGE_KINDS = (
    ("money", "#3987e5", ""),
    ("role", "#d95926", ""),
    ("candidacy", "#199e70", ""),
    ("declaration", "#e3b23c", ""),
    ("dealing", "#e87ba4", ""),
    ("same person, confirmed", "#d4ccff", ""),
    ("same person, near", "#d4ccff", "6 4"),
    ("lineage", "#80f040", ""),          # pub.links' related grade (ruling 106 (2)): earlier company to later, inside its frame
)
RELATION_KINDS = ("money", "role", "candidacy", "declaration", "dealing")   # what a catalogue line may declare; the two same-person kinds come from pub.links


@dataclass(frozen=True)
class Gift:
    """A donor's rows the graph draws as one money edge per recipient (ruling
    86 (3)): every row filed under one donor name, as filed (case, macrons
    and spacing folded, nothing else), to one party or one candidate, is one
    edge to one node, labelled with the total of the register's own amounts
    and its count; every addend is listed under it. One name as filed is
    never a finding that its rows are one person. `added`: whether this
    view's amounts are summed into the total, or listed apart (a disclosure's
    gift is also in that year's return: never summed with it, rulings 190 to
    193 of the old estate, carried in the disclosures and scan templates).
    `one_recipient`: columns of the recipient row that make one recipient
    across its rows (a candidate files one return per election); empty, the
    recipient row is itself the node (a party)."""
    view: str                       # the donor's view
    name: str                       # the donor's name, as filed
    amount: str
    years: tuple                    # a year column, or date columns whose year counts, first present wins
    to_view: str                    # the recipient's view
    column: str                     # this row's column naming the recipient, or the record that names it
    to_column: str = "key"          # matched to
    record: str = ""                # this row's column naming the record it sits in (its return), listed beside it
    record_view: str = ""
    what: str = ""                  # what one addend is, in words
    added: bool = True
    one_recipient: tuple = ()
    replaced: str = "replaced_by"   # a row an amendment replaces is listed, never added


GIFTS = (
    Gift("party_return_donors", "donor", "amount", ("year",), "parties", "party_key", record="return_key",
         record_view="party_return_totals", what="party return"),
    Gift("disclosures", "donor_name", "amount", ("given_on", "received_on"), "parties", "party", to_column="name",
         what="large-donation disclosure", added=False, replaced=""),
    Gift("candidate_return_donors", "donor", "amount", ("year",), "candidate_return_totals", "return_key",
         record="return_key", record_view="candidate_return_totals", what="candidate return",
         one_recipient=("surname", "given_names")),
)
GIFT_OF = {g.view: g for g in GIFTS}

#: the links lane's rules in plain words (ruling 84), keyed by the rule id `pub.links` carries
#: without its version; the words follow each rule's own description in links/ (rules.py, build.py).
#: The id and version are shown only in a tooltip or a list, as `rule_ref` writes them, never as a label.
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
    "organisation-sole-company": "a row's organisation name and the one body of the name on the companies, societies, partnerships and charities registers, live on the row's own date",   # rulings 106 (1), 114, 125
    "successor-name": "a company succeeded by another of its name with a year in brackets, a person on both",        # ruling 106 (2), related
    "candidate-same-party": "one candidate name standing for one party in two elections",                            # ruling 106 (3)
    "organisation-one-live-company": "a row's organisation name and the one of several bodies of the name live on the row's own date",   # rulings 107, 114, 125
    "refiled-name": "a company removed and another of its name registered within twelve months, a person on both",   # ruling 109, related
    "member-on-the-day": "a member's printed name, titles off, and the one member of that name sitting in the House on the row's day",   # ruling 116
}


def _rule_parts(rule) -> tuple:
    rid, _, version = str(rule or "").partition("@")
    return rid, version


def rule_words(rule) -> str:
    """`name-only@1` reads "same name, nothing else"; an id the table lacks
    reads "links rule <id>", so nothing is hidden."""
    rid, _ = _rule_parts(rule)
    return RULE_WORDS.get(rid) or f"links rule {rid}"


def rule_ref(rule) -> str:
    """"(links rule name-only, version 1)": for a tooltip or a list only."""
    rid, version = _rule_parts(rule)
    return f"(links rule {rid}" + (f", version {version})" if version else ")")


@dataclass(frozen=True)
class Name:
    """Where one person's name sits in a view's row, for the field search
    (ruling 82): `whole`, a column holding the whole name as one string; or
    the parts, `first`, `middle` and `last`, with `given` for a column
    holding the first and middle names together. `order` (ruling 85) says
    how the name fields read it: PARTS for the parts; for a whole name
    GIVEN_FAMILY or FAMILY_GIVEN where the register's form or the lane's own
    rule fixes the order, AMBIGUOUS where nothing does. A comma reads family
    then given whatever the order."""
    whole: str = ""
    first: str = ""
    middle: str = ""
    given: str = ""
    last: str = ""
    order: str = ""

    def columns(self) -> tuple:
        return tuple(c for c in (self.whole, self.first, self.middle, self.given, self.last) if c)


#: a Name's orders (ruling 85)
PARTS, GIVEN_FAMILY, FAMILY_GIVEN, AMBIGUOUS = "parts", "given-family", "family-given", "ambiguous"
ORDERS = (PARTS, GIVEN_FAMILY, FAMILY_GIVEN, AMBIGUOUS)
#: the orders that fix where a name's words go: the near matches' reversed class reads only these
STATED = (PARTS, GIVEN_FAMILY, FAMILY_GIVEN)


@dataclass(frozen=True)
class Fields:
    """Which columns of a view hold each field of the expanded search
    (ruling 82). A lane adds a line to FIELDS_OF and no code."""
    names: tuple = ()               # Name: the people a row names; a name field matches any one of them
    organisation: tuple = ()        # columns holding a company, party, charity or society name
    named: tuple = ()               # a name that may be a person's or an organisation's: the organisation field matches it only where it carries an organisation word
    address: tuple = ()             # registered-address columns an organisation publishes (ADDRESS_COLUMNS), never a person's
    year: tuple = ()                # integer year columns
    dates: tuple = None             # date columns whose year counts; None: the View's dates


@dataclass(frozen=True)
class Say:
    """A line a row's pane and its results hit carry where `column` holds one
    of `values` (empty: any value), or, with `above`, a number above it; the
    words may name the row's columns in braces ("read from the newest of
    {versions} versions"). A lane's pane.md line said as data."""
    words: str
    column: str
    values: tuple = ()
    above: int | None = None

    def holds(self, r: dict) -> bool:
        x = r.get(self.column)
        if x is None or x == "":
            return False
        if self.above is not None:
            return isinstance(x, (int, float)) and x > self.above
        return not self.values or x in self.values


@dataclass(frozen=True)
class View:
    name: str                       # the pub view
    register: str                   # the lane it belongs to (its folder name under registers/)
    kind: str                       # what a row is: person, organisation, document, event, place, figure
    title: tuple                    # columns joined with ' · ' for the pane's title
    search: tuple                   # text columns a search term is matched against
    numbers: tuple = ()             # columns an official number is matched against exactly
    fields: tuple = ()              # (label, column) shown in the pane, in order
    dates: tuple = ()               # columns shown as dates, with their names
    urls: tuple = ()                # columns that hold the source's own address
    names: tuple = ()               # the name columns a person pane and "same name elsewhere" use
    suppressed: str = ""            # a column that, when true, hides every name column
    hide_names: tuple = ()          # (column, regex): name columns hidden, and never matched, when the column's value matches
    withheld: str = ""              # a column that, when true, hides `text`
    joins: tuple = ()               # Join
    parent: tuple = ()              # (label, view, this row's column holding the parent's key)
    note: str = ""                  # a line every pane of this view carries
    default_order: str = "key"
    key_col: str = "key"             # the stable key (one view, expense_release_totals, has none and uses its release)
    relations: tuple = ()           # Relation: the connections to other rows this view's rows assert
    text: tuple = ()                # (label, column, words when empty): a long text shown whole in the row pane alone, never in a results hit or the table
    title_format: str = ""          # the title as words around its columns ("{sitting_on} · Parliament {parliament}"); where a column it names is empty, the plain title
    says: tuple = ()                # Say: a line the row carries where a column holds a value
    flags: tuple = ()               # (column, flag column, words): where the flag is true the column's cell, a field or a text, carries the words small beside it
    served: str = ""                # a column that, when false, strikes the row's title through: "withdrawn by the source"
    cite: tuple = ()                # (label, column): the source's own id for the row, shown in the citation beside the hash
    no_url: str = ""                # what the citation says where every one of `urls` is empty ("file name only: no address served")


#: every Hansard row's line (registers/hansard/pane.md, ruling 96)
HANSARD_NOTE = "taken from the old estate's tables; original not held; held at 23 September 2026"

#: every Beehive row's line (registers/beehive/pane.md, ruling 78)
BEEHIVE_NOTE = ("the estate did not fetch this page: the query-nz provider captured it off-estate (ruling 78), "
                "or the old estate's scraper did before ruling 78")
#: the heading pane.md insists on for the provider's topics and quotes (ruling 96)
ANNOTATION = "The source's annotation (made by its model, not ours)"

#: every ministers' diary row's line (registers/ministers_diaries/pane.md, ruling 78)
DIARY_NOTE = ("the estate did not fetch the PDF: the query-nz provider read it from the Beehive off-estate (ruling 78). "
              "Names are as the release prints them and are links to nobody")
#: every Parliament row's line (registers/parliament/pane.md, rulings 78, hard limit 6)
PARLIAMENT_NOTE = ("the estate did not fetch parliament.nz: the query-nz provider captured it off-estate (ruling 78), "
                   "through a challenge the estate may not pass (hard limit 6)")
#: the flag note beside a text a lane's shapes say names an address (ruling 102): the board shows it whole
NAMES_ADDRESS = "names an address by its shape: a product keeps it off its own surface (hard limit 15); the board shows it whole"
#: a row served in more than one version (registers/parliament/pane.md)
VERSIONS = Say("read from the version taken last, of {versions}", "versions", above=1)

DOC = (("document", "document"), ("page", "page"), ("place", "place"), ("read from", "read_from"),
       ("reader", "reader"), ("profile", "profile"))

VIEWS: tuple[View, ...] = (
    # ── companies (copied; pane.md: companies) ──────────────────────────────
    View("companies", "companies", "organisation", ("name",),
         search=("name",), numbers=("nzbn", "number"),
         fields=(("type", "entity_type"), ("status", "status"), ("NZBN", "nzbn"), ("number", "number"),
                 ("register", "register"), ("in the latest file", "in_latest"), ("first file", "first_file"),
                 ("last file", "last_file"), ("more", "extra")),
         dates=(("registered on", "registered_on"), ("removed on", "removed_on")),
         names=("name",),
         joins=(Join("Directors", "directors", "entity_key", order="appointed_on"),
                Join("Shareholders", "shareholders", "entity_key", order="name"),
                Join("Registered office", "company_addresses", "entity_key", order="started_on"),
                Join("Earlier states", "company_states", "entity_key", order="file")),
         note="taken from the old estate's tables; original not held"),
    View("directors", "companies", "person", ("full_name",),
         search=("full_name", "last_name"),
         fields=(("role", "role_type"), ("company", "entity_key"), ("NZBN", "nzbn"), ("company number", "company_number"),
                 ("in the latest file", "in_latest"), ("in the files from", "first_file"), ("to", "last_file")),
         dates=(("appointed on", "appointed_on"), ("ended on", "ended_on")),
         names=("full_name",), suppressed="suppressed",
         parent=("Company", "companies", "entity_key"),
         note="a role that has left the latest file carries no end date: the file states none",
         relations=(Relation("role", "entity_key", "companies", label="director of"),)),
    View("shareholders", "companies", "person", ("name",),
         search=("name",), numbers=("holder_nzbn",),
         fields=(("holder type", "shareholder_type"), ("shares", "shares"), ("allocation", "allocation_status"),
                 ("holder's NZBN", "holder_nzbn"), ("company", "entity_key"), ("in the latest file", "in_latest"),
                 ("in the files from", "first_file"), ("to", "last_file")),
         names=("name",), suppressed="suppressed",
         parent=("Company", "companies", "entity_key"),
         relations=(Relation("role", "entity_key", "companies", label="shareholder of"),)),
    View("company_addresses", "companies", "place", ("line_1", "line_2", "line_3", "line_4"),
         search=("line_1", "line_2", "line_3", "line_4", "postcode"),
         fields=(("kind", "kind"), ("care of", "care_of"), ("postcode", "postcode"), ("country", "country"),
                 ("in the latest file", "in_latest"), ("last file", "last_file")),
         dates=(("from", "started_on"),),
         parent=("Company", "companies", "entity_key"),
         note="a company's registered office; no residential address is held in any published table"),
    View("company_states", "companies", "event", ("file", "status"),
         search=("name",),
         fields=(("name in that file", "name"), ("type", "entity_type"), ("status", "status")),
         dates=(("registered on", "registered_on"), ("removed on", "removed_on")),
         parent=("Company", "companies", "entity_key")),
    # ── companies, step 5.5: the interface's answers (companies-2; pane.md: companies; added at the charities-3 merge) ──
    View("company_lookups", "companies", "organisation", ("name",),
         search=("name",), numbers=("nzbn",),
         fields=(("kind", "kind"), ("type", "entity_type"), ("status", "status"), ("NZBN", "nzbn"),
                 ("in the monthly file", "in_monthly"), ("asked at", "asked_at"), ("source", "source_note")),
         dates=(("registered on", "registered_on"), ("register updated on", "register_updated_on")),
         names=("name",),
         joins=(Join("Roles (the interface)", "company_lookup_roles", "entity_key", order="started_on"),
                Join("Holdings (the interface)", "company_lookup_holdings", "entity_key", order="started_on"),
                Join("Changes", "company_changes", "entity_key", order="seen_on")),
         parent=("Company", "companies", "entity_key"),
         note="the register's last answer for an entity a product looked up or watches; a sole trader's withheld name reads as the register gives it; no address of a person is shown"),
    View("company_lookup_roles", "companies", "person", ("full_name",),
         search=("full_name", "last_name"),
         fields=(("role", "role_type"), ("status", "role_status"), ("a body", "is_body"), ("body NZBN", "body_nzbn"),
                 ("entity", "entity_key"), ("held row", "held_key"), ("source", "source_note")),
         dates=(("started on", "started_on"), ("ended on", "ended_on")),
         names=("full_name", "first_name", "middle_names", "last_name"), suppressed="suppressed",
         parent=("Entity", "company_lookups", "entity_key"),
         note="the register's own start and end dates; a role the monthly file stopped listing shows the end the interface gives it",
         relations=(Relation("role", "entity_key", "company_lookups", label="role in"),)),
    View("company_lookup_holdings", "companies", "person", ("name",),
         search=("name",), numbers=("holder_nzbn",),
         fields=(("holder type", "holder_type"), ("shares", "shares"), ("allocation", "allocation"),
                 ("current", "current"), ("entity", "entity_key"), ("source", "source_note")),
         dates=(("started on", "started_on"), ("ended on", "ended_on")),
         names=("name",), suppressed="suppressed",
         parent=("Entity", "company_lookups", "entity_key"),
         relations=(Relation("role", "entity_key", "company_lookups", label="holds shares in"),)),
    View("company_changes", "companies", "event", ("kind", "subject"),
         search=("subject",),
         fields=(("kind", "kind"), ("before", "before"), ("after", "after"), ("date basis", "date_basis"),
                 ("compared with", "compared_with"), ("entity", "entity_key"), ("source", "source_note")),
         dates=(("effective on", "effective_on"), ("seen on", "seen_on"), ("register updated on", "register_updated_on")),
         suppressed="suppressed",
         parent=("Entity", "company_lookups", "entity_key"),
         note="a difference between two answers of the interface, or between its answer and the monthly file; dated by the register's own date where it states one, else the day seen"),
    # ── societies (copied through the per-entity interface; pane.md: societies; added at societies-1) ──
    View("societies", "societies", "organisation", ("name",),
         search=("name",), numbers=("nzbn", "number"),
         fields=(("status", "status"), ("NZBN", "nzbn"), ("number", "number"), ("Act", "act"),
                 ("charity number", "charity_number"), ("party society", "party_society"),
                 ("in the latest file", "in_latest"), ("last file", "last_file"), ("source", "source_note")),
         dates=(("registered on", "registered_on"), ("re-registered on", "reregistered_on"), ("removed on", "removed_on")),
         names=("name",),
         joins=(Join("Officers", "society_officers", "society_key", order="started_on"),
                Join("Earlier states", "society_states", "society_key", order="file")),
         note="taken from the old estate's tables or one ask's answer; no address is shown"),
    View("society_officers", "societies", "person", ("full_name",),
         search=("full_name", "last_name"),
         fields=(("role", "role_type"), ("status", "role_status"), ("society", "society_key"), ("NZBN", "nzbn"),
                 ("source", "source_note")),
         dates=(("started on", "started_on"), ("ended on", "ended_on"), ("first read on", "first_read_on"),
                ("last read on", "last_read_on")),
         names=("full_name",), suppressed="suppressed",
         parent=("Society", "societies", "society_key"),
         note="a role the register stopped listing keeps its last day read; it is never given an end the register did not state",
         relations=(Relation("role", "society_key", "societies", label="officer of"),)),
    View("society_states", "societies", "event", ("file", "status"),
         search=("name",),
         fields=(("name in that file", "name"), ("status", "status")),
         dates=(("registered on", "registered_on"), ("removed on", "removed_on")),
         parent=("Society", "societies", "society_key")),
    # ── charities (the register's own OData feed; pane.md: charities; added at charities-3) ──
    View("charities", "charities", "organisation", ("name",),
         search=("name", "other_names"), numbers=("number", "nzbn", "incorporation_number"),
         fields=(("status", "status"), ("number", "number"), ("legal structure", "legal_structure"),
                 ("charitable purpose", "charitable_purpose"), ("main sector", "main_sector"),
                 ("main activity", "main_activity"), ("main beneficiary", "main_beneficiary"),
                 ("address for service", "address_for_service"), ("group", "group_name"), ("NZBN", "nzbn"),
                 ("deregistration reason", "deregistration_reason")),
         dates=(("registered on", "registered_on"), ("deregistered on", "deregistered_on"),
                ("annual return due on", "annual_return_due_on")),
         names=("name",),
         joins=(Join("Officers", "charity_officers", "charity_key", order="started_on"),
                Join("Annual returns", "charity_returns", "charity_key", order="period_end")),
         note="the address for service is shown only where the charity is a body corporate (ruling 64); a trust's or an unincorporated group's is withheld because it may be a trustee's home"),
    View("charity_officers", "charities", "person", ("full_name",),
         search=("full_name", "last_name"),
         fields=(("role", "role"), ("status", "status"), ("kind", "kind"), ("disqualified", "disqualified"),
                 ("charity", "charity_key"), ("name note", "name_note")),
         dates=(("started on", "started_on"), ("ended on", "ended_on")),
         names=("full_name", "first_name", "middle_name", "last_name"), suppressed="suppressed",
         parent=("Charity", "charities", "charity_key"),
         note="as the register's feed states the officer; a suppressed name is suppressed here, the row and its dates stay",
         relations=(Relation("role", "charity_key", "charities", label="officer of"),)),
    View("charity_returns", "charities", "figure", ("period_end", "tier"),
         search=("charity_key",),
         fields=(("tier", "tier"), ("months covered", "months_covered"), ("audited", "audited"),
                 ("opinion", "opinion"), ("total gross income", "total_gross_income"),
                 ("total expenditure", "total_expenditure"), ("net surplus", "net_surplus"),
                 ("total assets", "total_assets"), ("total liabilities", "total_liabilities"),
                 ("total equity", "total_equity"), ("group", "group_key")),
         dates=(("period end", "period_end"), ("began on", "began_on")),
         parent=("Charity", "charities", "charity_key")),
    # ── party finance, session 2 (added at party-finance-2) ─────────────────
    View("promoter_expense_returns", "party_finance", "figure", ("promoter", "year", "part"),
         search=("promoter",),
         fields=(("part", "part"), ("spending", "spending"), ("figure", "figure"), ("figure check", "figure_check"),
                 ("declared", "declared"), ("schedule", "schedule"), ("listing row", "listing_row")),
         names=("promoter",),
         note="each part from the declaration's box and the schedule's own total, checked against each other, never added across parts",
         default_order="year"),
    View("party_statement_figures", "party_finance", "figure", ("party_label", "filed_year", "figure"),
         search=("party_label",),
         fields=(("figure", "figure"), ("amount", "amount"), ("prior year", "prior_amount"), ("scale", "scale"),
                 ("figure check", "figure_check"), ("as printed", "printed"), ("current statement", "current"),
                 ("party basis", "party_basis")),
         dates=(("balance date", "balance_date"),),
         parent=("Party", "parties", "party"),
         note="a pair publishes only where the statement's own arithmetic holds",
         default_order="filed_year"),
    # ── candidate returns (built; pane.md: candidate_returns; added at candidate-returns-1) ──
    View("candidate_return_totals", "candidate_returns", "figure", ("surname", "given_names", "electorate", "year"),
         search=("surname", "given_names", "electorate", "party"),
         fields=(("party", "party"), ("status", "status"), ("replaced by", "replaced_by"), ("placed by", "placed_by"),
                 ("donations", "donations"), ("Part A", "part_a"), ("Part C", "part_c"), ("Part D", "part_d"),
                 ("donations check", "donations_check"), ("expenses", "expenses"), ("Part F", "part_f"), ("Part G", "part_g"),
                 ("expenses check", "expenses_check"), ("loans", "loans"), ("loans check", "loans_check"), ("signed", "signed")),
         names=("surname", "given_names"),
         joins=(Join("Donors", "candidate_return_donors", "return_key", order="ordinal"),),
         note="a replaced return shows the amendment the Commission links in its place and is never summed",
         default_order="year"),
    View("candidate_return_donors", "candidate_returns", "figure", ("donor", "amount"),
         search=("donor", "surname", "electorate"),
         fields=(("amount", "amount"), ("dates", "dates"), ("contributions", "contributions"), ("candidate", "surname"),
                 ("electorate", "electorate"), ("party", "party"), ("year", "year")),
         names=("donor",),
         parent=("Return", "candidate_return_totals", "return_key"),
         note="no donor's address is held in any published table", default_order="ordinal",
         relations=(Relation("money", "return_key", "candidate_return_totals", label="donated, in the return"),)),
    # ── disclosures (built; pane.md: disclosures) ──────────────────────────
    View("disclosures", "disclosures", "figure", ("donor_name", "party"),
         search=("donor_name", "party", "party_label"),
         fields=(("amount", "amount"), ("amount before amendment", "amount_original"), ("party", "party"),
                 ("party as printed", "party_label"), ("regime", "regime"), ("floor", "threshold"), ("section", "section"),
                 ("amendment", "amendment"), ("Commission's note", "commission_note"), ("amount note", "amount_note"),
                 ("items sum", "items_sum"), ("items check", "items_check"), ("at or under threshold", "at_or_under_threshold"),
                 ("form total", "form_total"), ("form check", "form_check"), ("declaration document", "declaration_document")),
         dates=(("received by the party", "given_on"), ("received by the Commission", "received_on"),
                ("amended on", "amended_on"), ("withdrawn on", "withdrawn_on"), ("returned on", "returned_on")),
         urls=("href",), names=("donor_name",),
         joins=(Join("Itemised gifts", "disclosure_items", "declaration", order="ordinal"),),
         note="an amended declaration is one row with the amended figures; never summed with its original",
         default_order="received_on",
         relations=(Relation("money", "party", "parties", to_column="name", label="disclosed by"),)),
    View("disclosure_items", "disclosures", "figure", ("contributor", "amount"),
         search=("contributor", "text"),
         fields=(("amount", "amount"), ("contributor", "contributor"), ("as printed", "text"), ("ordinal", "ordinal")),
         dates=(("first date", "first_date"),), names=("contributor",),
         parent=("Declaration", "disclosures", "declaration"),
         relations=(Relation("money", "declaration", "disclosures", label="itemised in"),)),
    # ── expenses (copied from published files; pane.md: expenses) ─────────
    View("mp_expenses", "expenses", "figure", ("name", "category"),
         search=("name", "member", "party", "party_label"),
         fields=(("member", "member"), ("party", "party"), ("party as printed", "party_label"), ("category", "category"),
                 ("role", "role"), ("figure", "figure"), ("as printed", "printed"), ("line check", "line_check"),
                 ("line", "line"), ("marks", "marks"), ("release", "release"), ("period basis", "period_basis")),
         dates=(("period from", "period_start"), ("period to", "period_end")),
         urls=("url",), names=("name",),
         note="money outside the total is shown beside it and never added in",
         default_order="period_start"),
    View("minister_expenses", "expenses", "figure", ("name", "category"),
         search=("name", "member", "party", "party_label"),
         fields=(("member", "member"), ("party", "party"), ("party as printed", "party_label"), ("category", "category"),
                 ("role", "role"), ("figure", "figure"), ("as printed", "printed"), ("line check", "line_check"),
                 ("line", "line"), ("marks", "marks"), ("release", "release"), ("period basis", "period_basis")),
         dates=(("period from", "period_start"), ("period to", "period_end")),
         urls=("url",), names=("name",), default_order="period_start"),
    View("expense_release_totals", "expenses", "figure", ("release", "label"),
         search=("release", "label", "heading", "publisher"),
         fields=(("publisher", "publisher"), ("heading", "heading"), ("total role", "total_role"),
                 ("printed", "printed"), ("sum of the lane's rows", "rows_sum"), ("equal", "equal")),
         dates=(("period from", "period_start"), ("period to", "period_end")),
         note="the publisher's own grand total beside the sum of the lane's lines", default_order="release", key_col="release"),
    # ── gazette (built; pane.md: gazette) ──────────────────────────────────
    View("gazette_notices", "gazette", "document", ("notice", "title"),
         search=("title", "notice"),
         fields=(("section", "section"), ("family", "family"), ("format", "format"), ("status", "status"),
                 ("records", "records"), ("year", "year"), ("number", "number")),
         dates=(("published on", "published_on"),),
         urls=("url",),
         joins=(Join("Celebrants named", "gazette_celebrants", "notice", key_column="notice", order="ordinal"),
                Join("Prohibitions", "gazette_prohibitions", "notice", key_column="notice", order="ordinal"),
                Join("Liquidations", "gazette_liquidations", "notice", key_column="notice", order="ordinal"),
                Join("Company notices", "gazette_company_notices", "notice", key_column="notice", order="ordinal"),
                Join("Bankruptcies", "gazette_bankruptcies", "notice", key_column="notice", order="ordinal"),
                Join("Appointments", "gazette_appointments", "notice", key_column="notice", order="ordinal"),
                Join("Mortgagee possession", "gazette_possessions", "notice", key_column="notice")),
         note="the notice text is never shown: some notices print home addresses", default_order="published_on"),
    View("gazette_celebrants", "gazette", "person", ("surname", "given_names"),
         search=("surname", "given_names", "organisation"),
         fields=(("organisation", "organisation"), ("action", "action"), ("statute", "statute"), ("list shape", "list_shape"),
                 ("how the name was cut", "split"), ("marks", "marks"), ("ordinal", "ordinal")),
         dates=(("published on", "published_on"), ("period from", "period_from"), ("period to", "period_to")),
         names=("surname", "given_names"),
         parent=("Notice", "gazette_notices", "notice"),
         note="a row from an address list says only that its address is held privately", default_order="published_on"),
    View("gazette_prohibitions", "gazette", "person", ("name", "action"),
         search=("name", "also_known_as"),
         fields=(("also known as", "also_known_as"), ("action", "action"), ("Act and section", "statute"), ("months", "months"),
                 ("permanent", "permanent"), ("start basis", "starts_basis"), ("supersedes", "supersedes"),
                 ("superseded by", "superseded_by"), ("how", "superseded_how"), ("named twice", "named_twice"), ("ordinal", "ordinal")),
         dates=(("published on", "published_on"), ("starts on", "starts_on"), ("ends on", "ends_on"), ("dated", "dated_on")),
         names=("name", "also_known_as"), hide_names=("superseded_how", "^revoked"),
         parent=("Notice", "gazette_notices", "notice"),
         note="the address the notice prints is never shown; a person a later notice revoked is not shown either", default_order="published_on"),
    View("gazette_liquidations", "gazette", "organisation", ("company",),
         search=("company",), numbers=("company_number",),
         fields=(("company number", "company_number"), ("shape", "shape"), ("appointed by", "appointed_by"), ("section", "statute"),
                 ("appointed at", "appointed_at"), ("date basis", "date_basis"), ("corrigendum", "corrigendum"),
                 ("liquidators named", "liquidators"), ("companies register row", "register_key"),
                 ("how the register was matched", "register_match"), ("ordinal", "ordinal")),
         dates=(("published on", "published_on"), ("appointed on", "appointed_on"), ("dated", "dated_on")),
         names=("company",),
         joins=(Join("Liquidators named in the notice", "gazette_liquidators", "notice", key_column="notice", order="ordinal"),),
         parent=("Notice", "gazette_notices", "notice"),
         note="no address, telephone or email is shown or held", default_order="published_on"),
    View("gazette_liquidators", "gazette", "person", ("name", "role"),
         search=("name",),
         fields=(("role", "role"), ("how the name was read", "named_in_body"), ("companies in the notice", "companies"), ("ordinal", "ordinal")),
         dates=(("published on", "published_on"),),
         names=("name",),
         joins=(Join("Companies in the notice", "gazette_liquidations", "notice", key_column="notice", order="ordinal"),),
         parent=("Notice", "gazette_notices", "notice"), default_order="published_on"),
    View("gazette_company_notices", "gazette", "organisation", ("company", "kind"),
         search=("company", "party"), numbers=("company_number",),
         fields=(("kind", "kind"), ("action", "action"), ("company number", "company_number"), ("shape", "shape"),
                 ("section", "statute"), ("ground", "ground"), ("by whom", "by_whom"), ("applicant or plaintiff", "party"),
                 ("event at", "event_at"), ("date basis", "event_basis"), ("court", "court"), ("reference", "reference"),
                 ("corrigendum", "corrigendum"), ("people named", "people"), ("people a correction names", "people_named"),
                 ("role in an amalgamation", "role"), ("companies register row", "register_key"),
                 ("how the register was matched", "register_match"), ("ordinal", "ordinal")),
         dates=(("published on", "published_on"), ("event on", "event_on"), ("filed on", "filed_on"), ("dated", "dated_on")),
         names=("company",),
         joins=(Join("Receivers and administrators named", "gazette_practitioners", "notice", key_column="notice", order="ordinal"),),
         parent=("Notice", "gazette_notices", "notice"),
         note="an applicant is named only; no address for service is held or shown", default_order="published_on"),
    View("gazette_practitioners", "gazette", "person", ("name", "role"),
         search=("name",),
         fields=(("role", "role"), ("how the name was read", "named_in_body"), ("companies in the notice", "companies"), ("ordinal", "ordinal")),
         dates=(("published on", "published_on"),),
         names=("name",),
         joins=(Join("Companies in the notice", "gazette_company_notices", "notice", key_column="notice", order="ordinal"),),
         parent=("Notice", "gazette_notices", "notice"), default_order="published_on"),
    View("gazette_bankruptcies", "gazette", "person", ("surname", "given_names"),
         search=("surname", "given_names", "also_known_as"),
         fields=(("kind", "kind"), ("shape", "shape"), ("also known as", "also_known_as"), ("occupation", "occupation"),
                 ("event at", "event_at"), ("court", "court"), ("section", "statute"), ("withheld by", "withheld_by"),
                 ("ordinal", "ordinal")),
         dates=(("published on", "published_on"), ("event on", "event_on"), ("dated", "dated_on")),
         names=("surname", "given_names", "also_known_as"), hide_names=("withheld_by", "."),
         parent=("Notice", "gazette_notices", "notice"),
         note="the address the notice prints is never shown; a person a later annulment names is withheld on every earlier row",
         default_order="published_on"),
    View("gazette_appointments", "gazette", "person", ("name", "role"),
         search=("name", "body", "role"),
         fields=(("body", "body"), ("role", "role"), ("section", "statute"), ("by whom", "by_whom"),
                 ("corrigendum", "corrigendum"), ("ordinal", "ordinal")),
         dates=(("published on", "published_on"), ("starts on", "starts_on"), ("ends on", "ends_on"), ("dated", "dated_on")),
         names=("name",),
         parent=("Notice", "gazette_notices", "notice"),
         note="where an appointee lives is never kept", default_order="published_on"),
    View("party_labels", "parties", "figure", ("label", "on"),
         search=("label", "party_name"),
         fields=(("resolves to", "party_name"), ("basis", "basis"), ("why", "why"), ("grain", "grain"),
                 ("same name", "same_name"), ("sources", "sources"), ("rows", "rows"), ("resolver", "resolver")),
         parent=("Party", "parties", "party"),
         note="every party label the other registers print, and the registration each resolves to; unresolved stays unresolved",
         default_order="label"),
    View("gazette_possessions", "gazette", "event", ("mortgagee", "asset"),
         search=("mortgagee", "mortgagor"), numbers=("mortgagee_number", "mortgagor_number"),
         fields=(("lender", "mortgagee"), ("lender kind", "mortgagee_kind"), ("lender's company number", "mortgagee_number"),
                 ("lender's register row", "mortgagee_register_key"), ("how the lender was matched", "mortgagee_register_match"),
                 ("borrower (a company only)", "mortgagor"), ("borrower kind", "mortgagor_kind"),
                 ("borrower's company number", "mortgagor_number"), ("borrower's register row", "mortgagor_register_key"),
                 ("how the borrower was matched", "mortgagor_register_match"), ("land or goods", "asset"),
                 ("action", "action"), ("section", "statute"), ("day basis", "entered_basis"),
                 ("a description is held", "property_held"), ("corrigendum", "corrigendum")),
         dates=(("published on", "published_on"), ("entered on", "entered_on"), ("dated", "dated_on")),
         names=("mortgagee", "mortgagor"),
         parent=("Notice", "gazette_notices", "notice"),
         note="the property's address, the goods' numbers and every person's name are never shown; a title is cut before the property it names",
         default_order="published_on"),
    # ── house (built; pane.md: house) ──────────────────────────────────────
    View("candidates", "house", "person", ("display_name", "election"),
         search=("name", "display_name", "party", "party_registered", "electorate"),
         fields=(("as printed", "name"), ("party as printed", "party"), ("party as registered", "party_registered"),
                 ("party basis", "party_basis"), ("electorate", "electorate"), ("list place", "list_place"),
                 ("list place cited at", "list_place_cite"), ("votes at the official count", "votes"),
                 ("poll cancelled", "poll_cancelled"), ("how the 2026 row was joined", "joined_basis")),
         names=("display_name", "name"),
         parent=("Electorate", "electorates", "electorate"),
         note="the party as printed on the page, and as registered where the label resolves", default_order="election",
         relations=(Relation("candidacy", "party_registered", "parties", to_column="name", label="candidate for"),
                    Relation("candidacy", "electorate", "electorates", label="stood in"))),
    View("members", "house", "person", ("display_name", "route"),
         search=("name", "display_name", "party", "party_registered", "electorate"),
         fields=(("as printed", "name"), ("party", "party"), ("party as registered", "party_registered"), ("route", "route"),
                 ("electorate", "electorate"), ("candidacy", "candidate"), ("from basis", "from_basis"), ("to basis", "to_basis")),
         dates=(("seat from", "from_on"), ("to, at the latest", "to_by"), ("ended on", "ended_on")),
         names=("display_name", "name"),
         parent=("Candidacy", "candidates", "candidate"),
         note="the day a seat actually ended is in no file this lane holds", default_order="from_on",
         relations=(Relation("candidacy", "candidate", "candidates", label="seat from"),)),
    View("electorates", "house", "place", ("name", "election"),
         search=("name", "statsnz_name"),
         fields=(("number", "number"), ("Stats NZ name", "statsnz_name"), ("Stats NZ code", "statsnz_code"), ("layer", "layer"),
                 ("join basis", "join_basis"), ("votes counted", "votes_counted"), ("candidate votes", "candidate_total"),
                 ("candidate informals", "candidate_informals"), ("party votes", "party_total"), ("party informals", "party_informals"),
                 ("poll cancelled", "poll_cancelled"), ("result held", "result_held")),
         joins=(Join("Candidates", "candidates", "electorate", order="votes"),),
         parent=("Election", "elections", "election"), default_order="election"),
    View("elections", "house", "event", ("name",),
         search=("name", "electorate"),
         fields=(("kind", "kind"), ("electorate", "electorate"), ("polling day basis", "polled_basis")),
         dates=(("polling day", "polled_on"),), urls=("results_href",),
         joins=(Join("Electorates", "electorates", "election", order="name"),
                Join("Seats", "members", "election", order="display_name")), default_order="polled_on"),
    # ── hansard (taken from the old estate's tables, ruling 96; pane.md: hansard) ──
    View("hansard_sittings", "hansard", "event", ("sitting_on", "parliament", "volume"),
         search=("url", "progress"),
         fields=(("Parliament", "parliament"), ("volume", "volume"), ("transcript when the old estate read it", "progress"),
                 ("sections", "sections"), ("speech turns", "turns"), ("member turns", "attributed"),
                 ("role-only turns", "unattributed"), ("members who spoke", "speakers"),
                 ("page last modified, by the index", "index_lastmod"), ("index fetched", "index_fetched"),
                 ("source", "source_note")),
         dates=(("sitting day", "sitting_on"),), urls=("url",),
         joins=(Join("Sections", "hansard_sections", "sitting_on", key_column="sitting_on", order="section_index"),
                Join("The daily PDF (the MCP)", "hansard_days", "sitting_on", key_column="sitting_on", order="sitting_on")),
         title_format="{sitting_on} · Parliament {parliament}, volume {volume}",
         note=HANSARD_NOTE, default_order="sitting_on"),
    View("hansard_sections", "hansard", "document", ("subject", "sitting_on"),
         search=("subject", "proceeding", "bill_title"),
         numbers=("bill_id",),
         fields=(("proceeding", "proceeding"), ("subject", "subject"), ("bill", "bill_title"), ("bill id", "bill_id"),
                 ("transcript when the old estate read it", "progress"), ("section", "section_index"),
                 ("speech turns", "turns"), ("characters", "chars"), ("Parliament", "parliament"), ("volume", "volume"),
                 ("source", "source_note")),
         dates=(("sitting day", "sitting_on"),), urls=("url",),
         text=(("Text as captured", "text", "no text held"),),
         joins=(Join("Sitting day", "hansard_sittings", "sitting_on", key_column="sitting_on", order="sitting_on"),
                Join("Speech turns, in order", "hansard_speeches", ("sitting_on", "section_index"),
                     key_column=("sitting_on", "section_index"), order="ordinal")),
         note=HANSARD_NOTE + "; the text is shown on the board only (hard limit 13)", default_order="sitting_on"),
    View("hansard_speeches", "hansard", "event", ("member_name", "role", "sitting_on"),
         search=("member_name", "label_as_read", "role", "subject", "bill_title"),
         numbers=("member_id",),
         fields=(("member, the old roster's name", "member_name"), ("label, as read by the old estate", "label_as_read"),
                 ("role", "role"), ("Parliament's member id", "member_id"), ("proceeding", "proceeding"),
                 ("subject", "subject"), ("bill", "bill_title"), ("section", "section_index"), ("turn", "ordinal"),
                 ("source", "source_note")),
         dates=(("sitting day", "sitting_on"),), urls=("url",),
         names=("member_name",),
         joins=(Join("Section", "hansard_sections", ("sitting_on", "section_index"),
                     key_column=("sitting_on", "section_index"), order="section_index"),
                Join("This member's turns", "hansard_speeches", "member_id", key_column="member_id", order="sitting_on")),
         title_format='{member_name} · "{label_as_read}" as read by the old estate · {sitting_on}',
         note=HANSARD_NOTE + "; a turn is presence on the record, not advocacy: the chair speaks often. A role-only turn "
              "(the Speaker, the chair, the Clerk, an unnamed interjection) shows the role and never a person. The House "
              "publishes no member id, so a turn names no House member row: matching them by name would be a link made by looking",
         default_order="sitting_on"),
    View("hansard_days", "hansard", "document", ("sitting_on", "title"),
         search=("title", "pdf_url"),
         fields=(("the provider's title", "title"), ("pages", "page_count"), ("words", "word_count"),
                 ("captured by the provider", "captured_at"), ("the provider's hash of the PDF", "pdf_sha256"),
                 ("versions served", "versions"), ("the old transcript", "old_note"),
                 ("the old transcript's sections", "old_sections"), ("its subjects", "old_subjects"),
                 ("of them in the PDF's text", "subjects_in_text"), ("source", "source_note")),
         dates=(("sitting day", "sitting_on"),), urls=("citation_url",),
         joins=(Join("The sitting's pane (the old transcript's sections)", "hansard_sittings", "sitting_on",
                     key_column="sitting_on", order="sitting_on"),),
         title_format="{sitting_on} · daily PDF",
         note="captured and read off-estate by the query-nz provider (ruling 78); pdftotext's text, no section or "
              "speaker split. The text is in no view: \"source\" opens the landed record whole (ruling 88, the board only)",
         default_order="sitting_on"),
    # ── parliament (the ingest MCP's parliament corpora, rulings 96, 101, 102; pane.md: parliament) ──
    View("parliament_written_questions", "parliament", "document", ("title",),
         search=("title", "minister_name", "ministerial_display_name", "document_id"),
         fields=(("number", "question_number"), ("year", "question_year"), ("Parliament", "parliament_number"),
                 ("minister", "minister_name"), ("the minister's title", "ministerial_display_name"),
                 ("released, as served", "question_released_at"), ("reply held", "reply_present"),
                 ("Parliament's member id, the asking member", "member_id"), ("document type", "document_type"),
                 ("dated", "dated"), ("last modified", "last_modified"), ("attachment", "attachment_name"),
                 ("captured by the provider", "provider_fetched_at"), ("versions served", "versions"),
                 ("served by the source", "served"), ("source", "source_note")),
         dates=(("released", "question_released_on"),), urls=("citation_url",),
         text=(("The question, as the API gives it", "question_text", "no question text held"),
               ("The reply, as the API gives it", "reply_text", "no reply held")),
         flags=(("question_text", "question_text_names_address", NAMES_ADDRESS),
                ("reply_text", "reply_text_names_address", NAMES_ADDRESS)),
         relations=(Relation("role", "member_id", "hansard_speeches", to_column="member_id",
                             label="asked by the member of these turns (Parliament's member id)"),),
         says=(VERSIONS,), served="served",
         cite=(("Parliament's document id", "document_id"),),
         no_url="no page address: the API gives none, and none is made up",
         note=PARLIAMENT_NOTE + ". The asking member is joined to Hansard by Parliament's own member id, never by a name; "
              "the House publishes no such id",
         default_order="parliament_number, question_year, question_number"),
    View("parliament_api_items", "parliament", "document", ("title", "document_type"),
         search=("title", "short_title", "bill_title", "select_committee", "member_name", "party_name", "author"),
         numbers=("bill_number",),
         fields=(("corpus", "corpus"), ("documentType, as the API gives it", "document_type"), ("type", "item_type"),
                 ("short title", "short_title"), ("bill", "bill_title"), ("bill number", "bill_number"),
                 ("current stage", "bill_current_stage_name"), ("stages", "bill_stages"),
                 ("committee", "select_committee"), ("member, as served", "member_name"),
                 ("party, as served", "party_name"), ("author", "author"), ("people", "people"),
                 ("published, as served", "publication_date"), ("last stage", "last_stage_date"),
                 ("last modified", "last_modified"), ("submissions close", "iob_closing_date"),
                 ("reference", "reference"), ("order", "order_number"), ("Parliament", "parliament_number"),
                 ("SOP", "sop"), ("status", "status"), ("attachment", "attachment_name"), ("updated", "updated_at"),
                 ("captured by the provider", "provider_fetched_at"), ("collected by the provider", "provider_collected_at"),
                 ("the provider's capture", "capture"), ("versions served", "versions"),
                 ("served by the source", "served"), ("source", "source_note")),
         dates=(("published", "publication_on"),), urls=("citation_url",),
         text=(("Text, the provider's run of the record's fields", "text", "no text held"),),
         flags=(("text", "text_names_address", NAMES_ADDRESS),),
         says=(VERSIONS,), served="served",
         cite=(("Parliament's record id", "record_id"),),
         no_url="no page address in the record: cited by its hash and Parliament's record id",
         title_format="{title} · {document_type}",
         note=PARLIAMENT_NOTE + ". A current bill is in both bill corpora: two rows, one per corpus. The member is a "
              "name as served, a link to nobody",
         default_order="publication_on"),
    View("parliament_wayback_pages", "parliament", "document", ("html_title", "dated"),
         search=("html_title", "citation_url"),
         fields=(("the page's address", "citation_url"), ("the Internet Archive's copy", "snapshot_url"),
                 ("archived, the copy's stamp", "archived_at"), ("day, the copy's", "dated"), ("type", "doc_type"),
                 ("kind", "kind"), ("words", "text_words"), ("captured by the provider", "captured_at"),
                 ("the provider's hash of the copy", "captured_sha256"), ("capture status", "capture_status"),
                 ("the provider's capture", "capture"), ("versions served", "versions"),
                 ("served by the source", "served"), ("source", "source_note")),
         urls=("citation_url", "snapshot_url"),
         text=(("Text as captured", "text", "no text held"),),
         flags=(("text", "text_names_address", NAMES_ADDRESS),),
         says=(VERSIONS,), served="served",
         title_format="{html_title} · archived {dated}",
         note=PARLIAMENT_NOTE + "; read from the Internet Archive's copy, not the live page",
         default_order="dated"),
    # ── beehive (the ingest MCP's beehive corpus and the old estate's export, ruling 96; pane.md: beehive) ──
    View("beehive_releases", "beehive", "document", ("title", "type"),
         search=("title", "type"),
         fields=(("type, as the site gives it", "type"), ("kind, as the provider captured it", "kind"),
                 ("words", "word_count"), ("ministers the site tags", "ministers"), ("portfolios", "portfolios"),
                 ("the source's annotation: topics (made by its model)", "topics"),
                 ("the source's annotation: quotes (made by its model)", "quotes"),
                 ("versions served", "versions"), ("read from", "origin"), ("the provider's reading", "mcp_state"),
                 ("captured", "captured_at"), ("source", "source_note")),
         dates=(("day, the record's own", "published_on"),), urls=("citation_url",),
         joins=(Join("Ministers the site tags it with, in order", "beehive_release_ministers", "release", order="ordinal"),
                Join(ANNOTATION, "beehive_release_annotations", "release", order="annotation, ordinal")),
         title_format="{title} · {type}",
         says=(Say("read from the newest of {versions} versions", "versions", above=1),
               Say("the title, day and words are the old estate's: its scraper's reading, original not held",
                   "origin", ("old estate",)),
               Say("captured by the provider on {captured_at}, not yet read: the old estate's reading is shown until "
                   "the provider reads the page", "mcp_state", ("captured only",))),
         note=BEEHIVE_NOTE + ". The body is in no view: \"source\" opens the record whole (ruling 88, the board only)",
         default_order="published_on"),
    View("beehive_release_ministers", "beehive", "event", ("name", "published_on"),
         search=("name", "slug"),
         fields=(("minister, as the site tags the release", "name"), ("the site's slug", "slug"),
                 ("order on the release", "ordinal"), ("release", "release"), ("type", "type")),
         dates=(("the release's day", "published_on"),), urls=("citation_url",),
         names=("name",),
         parent=("Release", "beehive_releases", "release"),
         title_format='{name} · tagged on "{title}" · {published_on}',
         note=BEEHIVE_NOTE + ". A tag is the site's, on the release; the name is not a link to any person: the House "
              "publishes no id the site's slug matches, and matching by name would be a link made by looking",
         default_order="published_on"),
    View("beehive_release_annotations", "beehive", "document", ("annotation", "value"),
         search=("value",),
         fields=(("annotation", "annotation"), ("order", "ordinal"), ("value", "value"),
                 ("speaker, as the source's model attributed the quote", "speaker"), ("made by a model", "model_made"),
                 ("made by", "made_by"), ("release", "release")),
         dates=(("the release's day", "published_on"),), urls=("citation_url",),
         parent=("Release", "beehive_releases", "release"),
         title_format=ANNOTATION + " · {annotation}: {value}",
         note=ANNOTATION + ": the query-nz provider's model made it off-estate. Shown as the provider's, never a finding "
              "of the estate, never a link and never read into the graph (ruling 96)",
         default_order="published_on"),
    # ── ministers_diaries (the ingest MCP's parliament-diaries corpus, rulings 96, 102; pane.md: ministers_diaries) ──
    View("minister_diary_releases", "ministers_diaries", "document", ("minister", "file_name"),
         search=("minister", "file_name"),
         fields=(("minister, as the release prints them", "minister"), ("ministers its entries name", "ministers_named"),
                 ("portfolios, as released", "portfolios"), ("month", "month"),
                 ("month, as the file name gives it", "month_named"), ("month of every entry", "entries_month"),
                 ("calendar months its entries fall in", "months"), ("file name", "file_name"),
                 ("the site's folder", "upload_folder"), ("entries", "entries"),
                 ("entries with a withholding", "withheld_entries"), ("locations flagged", "locations_flagged"),
                 ("source", "source_note")),
         dates=(("first entry", "first_on"), ("last entry", "last_on")), urls=("citation_url",),
         joins=(Join("Its meetings, in date and time order", "minister_diary_entries", "release", order="entry_on, rowid"),),
         title_format="{minister} · {month}",
         no_url="file name only: no address served",
         note=DIARY_NOTE, default_order="first_on"),
    View("minister_diary_entries", "ministers_diaries", "event", ("entry_on", "time", "meeting"),
         search=("meeting", "attendees", "portfolio", "minister"),
         fields=(("minister, as released", "minister"), ("portfolio, as released", "portfolio"),
                 ("time, as released", "time"), ("meeting, as released", "meeting"),
                 ("attendees, as released", "attendees"), ("location, as released", "location"),
                 ("the fields the release withholds", "withheld"), ("date, as released", "date_as_released"),
                 ("release", "release"), ("the provider's row", "rowid"), ("versions served", "versions"),
                 ("collected by the provider", "collected_at"), ("updated", "updated_at"), ("source", "source_note")),
         dates=(("day", "entry_on"),), urls=("citation_url",),
         parent=("Release", "minister_diary_releases", "release"),
         flags=(("location", "location_names_home", "names a home"),
                ("location", "location_street_only", "street address, no place of business named"),
                ("meeting", "meeting_names_address", "street address in the meeting"),
                ("attendees", "attendees_names_address", "street address in the attendees")),
         says=(VERSIONS,),
         no_url="file name only: no address served",
         note=DIARY_NOTE + ". A withheld field shows the release's own words. The board shows the meeting, attendees and "
              "location whole (ruling 102); a product keeps a flagged one off its own surface (hard limit 15)",
         default_order="entry_on"),
    # ── mp_interests (copied from published files; pane.md: mp_interests) ──
    View("mp_interest_returns", "mp_interests", "person", ("name", "as_at"),
         search=("name", "member", "party", "party_label", "electorate"),
         fields=(("member as printed", "member"), ("party", "party"), ("party as printed", "party_label"),
                 ("electorate", "electorate"), ("statement", "statement"), ("declarations", "declarations"),
                 ("as at, printed", "printed")),
         dates=(("as at", "as_at"),), names=("name",),
         joins=(Join("Declarations", "mp_interests", "member_return", order="key"),),
         parent=("Edition", "mp_interest_editions", "document"), default_order="as_at"),
    View("mp_interests", "mp_interests", "figure", ("heading", "name"),
         search=("text", "name", "heading"),
         fields=(("member", "member"), ("party", "party"), ("electorate", "electorate"), ("category (the heading)", "heading"),
                 ("number as printed", "number_printed"), ("declared", "text")),
         dates=(("as at", "as_at"),), names=("name",), withheld="withheld",
         parent=("Member's return", "mp_interest_returns", "member_return"),
         note="the category is the heading, never the number: the register renumbered in 2018",
         relations=(Relation("declaration", "member_return", "mp_interest_returns", label="declared by"),)),
    View("mp_interest_editions", "mp_interests", "document", ("as_at_printed",),
         search=("as_at_printed", "categories"),
         fields=(("categories", "categories"), ("members", "members"), ("declarations", "declarations"),
                 ("numbering agrees", "numbering_agrees")),
         dates=(("as at", "as_at"),),
         joins=(Join("Members' returns", "mp_interest_returns", "document", order="name"),), default_order="as_at"),
    # ── parties (copied and built; pane.md: parties) ───────────────────────
    View("parties", "parties", "organisation", ("name",),
         search=("name", "first_name", "abbreviation", "secretary"),
         fields=(("status", "status"), ("on the register", "on_register"), ("first name", "first_name"),
                 ("registered basis", "registered_basis"), ("page basis", "page_basis"), ("window", "window"),
                 ("abbreviation", "abbreviation"), ("abbreviation on the ballot", "abbreviation_on_ballot"),
                 ("component parties", "components"), ("statement deadline", "statement_deadline"), ("audit", "audit"),
                 ("website", "website"), ("party rules", "rules_title"), ("secretary", "secretary"),
                 ("register document", "register_document"), ("cancellation document", "cancelled_document")),
         dates=(("registered on", "registered_on"), ("notice's day", "notice_registered_on"), ("registered by", "registered_by"),
                ("cancelled on", "cancelled_on"), ("register seen on", "register_seen_on"), ("off the register by", "off_register_by"),
                ("logo registered on", "logo_registered_on")),
         urls=("rules_href", "website"), names=("name",),
         joins=(Join("Names carried", "party_names", "party", order="from_on"),
                Join("Gazette events", "party_events", "party", order="published_on"),
                Join("Donation returns", "party_return_totals", "party", key_column="name", order="year"),
                Join("Large-donation disclosures", "disclosures", "party", key_column="name", order="received_on"),
                Join("Election expenses", "party_expenses", "party", order="year"),
                Join("Expense returns", "party_expense_returns", "party", order="year"),
                Join("Financial statements", "party_financial_statements", "party", order="filed_year"),
                Join("Broadcasting allocations", "broadcasting_allocations", "party", order="year"),
                Join("Candidates standing for it", "candidates", "party_registered", key_column="name", order="election"),
                Join("Members sitting for it", "members", "party_registered", key_column="name", order="from_on")),
         note="never the secretary's contact lines"),
    View("party_names", "parties", "event", ("name", "kind"),
         search=("name",),
         fields=(("kind", "kind"), ("basis", "basis")),
         dates=(("from", "from_on"), ("to", "to_on")),
         parent=("Registration", "parties", "party")),
    View("party_events", "parties", "event", ("kind", "party_label"),
         search=("party_label", "new_name", "title"),
         fields=(("party as printed", "party_label"), ("new name", "new_name"), ("abbreviation", "abbreviation"),
                 ("old abbreviation", "old_abbreviation"), ("reference", "ref"), ("notice", "notice"), ("title", "title")),
         dates=(("published on", "published_on"), ("decided on", "decided_on")),
         urls=("url",), parent=("Registration", "parties", "party"), default_order="published_on"),
    # ── party_finance (built; pane.md: party_finance) ──────────────────────
    View("party_expenses", "party_finance", "figure", ("party", "year"),
         search=("party", "party_label"),
         fields=(("party as printed", "party_label"), ("Commission's figure for election expenses", "total_expenses"),
                 ("limit", "expense_limit"), ("broadcasting allocation", "allocation"), ("allocation spent", "allocation_spent"),
                 ("audited", "audited"), ("as printed", "printed"), ("the return's own total", "return_total"),
                 ("return check", "return_check"), ("return read from", "return_read_from"), ("the two agree", "agrees"),
                 ("return document", "return_document"), ("return page", "return_page"), ("note", "note")),
         note="where the return was not read the pane says not read, never agrees", default_order="year"),
    View("party_expense_returns", "party_finance", "figure", ("party", "year"),
         search=("party", "party_label"),
         fields=(("party as printed", "party_label"), ("current", "current"), ("total", "total"), ("total check", "total_check"),
                 ("Part A", "part_a"), ("Part B", "part_b"), ("Part C", "part_c"), ("limit", "expense_limit"),
                 ("listing row", "listing_row")), default_order="year"),
    View("party_financial_statements", "party_finance", "document", ("party", "filed_year"),
         search=("party", "party_label"),
         fields=(("party as printed", "party_label"), ("audit requirement", "audit_requirement"), ("balance date as printed", "balance_printed"),
                 ("deadline as printed", "deadline_printed"), ("filed as printed", "filed_printed"), ("statements", "statements"),
                 ("mark", "mark"), ("note", "note")),
         dates=(("balance date", "balance_date"), ("deadline", "deadline"), ("date filed", "date_filed")),
         note="no figure from inside a statement yet", default_order="filed_year"),
    View("broadcasting_allocations", "party_finance", "figure", ("party", "year"),
         search=("party", "party_label"),
         fields=(("party as printed", "party_label"), ("round", "round_label"), ("final", "final"), ("eligible", "eligible"),
                 ("amount", "amount"), ("as printed", "printed"), ("mark", "mark")), default_order="year"),
    View("promoters", "party_finance", "organisation", ("promoter", "year"),
         search=("promoter",),
         fields=(("registered for", "registered_for"), ("statement", "statement")),
         dates=(("registered on", "registered_on"),), names=("promoter",),
         joins=(Join("People named in public roles", "promoter_people", "promoter_key", order="role"),
                Join("Expenses", "promoter_expenses", "promoter", key_column="promoter", order="year")),
         note="never an email or an address", default_order="year"),
    View("promoter_people", "party_finance", "person", ("name", "role"),
         search=("name", "promoter"),
         fields=(("promoter", "promoter"), ("role", "role"), ("year", "year")),
         names=("name",), parent=("Promoter", "promoters", "promoter_key"),
         relations=(Relation("role", "promoter_key", "promoters", label="named for"),)),
    View("promoter_expenses", "party_finance", "figure", ("promoter", "year"),
         search=("promoter",),
         fields=(("election expenses", "election_expenses"), ("cannabis referendum expenses", "cannabis_referendum_expenses"),
                 ("end of life referendum expenses", "end_of_life_referendum_expenses"), ("as printed", "printed"),
                 ("return document", "return_document"), ("note", "note")),
         note="election and referendum spending side by side and never added", default_order="year"),
    # ── party_returns (built; pane.md: party_returns) ──────────────────────
    View("party_return_totals", "party_returns", "figure", ("party", "year"),
         search=("party", "party_label"),
         fields=(("party as printed", "party_label"), ("declared total", "declared_total"), ("parts declared", "declared_parts"),
                 ("total check", "total_check"), ("Part A", "part_a"), ("Part C", "part_c"), ("Part D", "part_d"),
                 ("Part F", "part_f"), ("Part G", "part_g"), ("loans H", "loans_h"), ("loans I", "loans_i"),
                 ("loans total", "loans_total"), ("donors check", "donors_check"), ("loans check", "loans_check"),
                 ("year from", "year_from"), ("replaced by", "replaced_by")),
         joins=(Join("Donors (Part A)", "party_return_donors", "return_key", order="ordinal"),
                Join("Lenders", "party_return_loans", "return_key", order="ordinal")),
         note="an amendment the Commission lists replaces a return; the two are never summed", default_order="year",
         relations=(Relation("money", "party_key", "parties", label="return of"),)),
    View("party_return_donors", "party_returns", "figure", ("donor", "amount"),
         search=("donor",),
         fields=(("party", "party"), ("year", "year"), ("amount", "amount"), ("dates as printed", "dates"),
                 ("contributions", "contributions"), ("how the row was paired", "paired_by"), ("ordinal", "ordinal"),
                 ("replaced by", "replaced_by")),
         names=("donor",), parent=("Return", "party_return_totals", "return_key"), default_order="ordinal",
         relations=(Relation("money", "return_key", "party_return_totals", label="donated, in the return"),)),
    View("party_return_loans", "party_returns", "figure", ("lender", "amount"),
         search=("lender",),
         fields=(("party", "party"), ("year", "year"), ("amount", "amount"), ("dates as printed", "dates"),
                 ("interest", "interest"), ("ordinal", "ordinal"), ("replaced by", "replaced_by")),
         names=("lender",), parent=("Return", "party_return_totals", "return_key"), default_order="ordinal",
         relations=(Relation("money", "return_key", "party_return_totals", label="lent, in the return"),)),
    # ── party boards, the declared tier (ruling 72; pane.md: party_boards; catalogued in the merge after party-boards-1) ──
    View("party_board_roles", "party_boards", "person", ("name", "role"),
         search=("name", "name_as_declared"),
         fields=(("party", "party"), ("role", "role"), ("role basis", "role_basis"), ("section", "section"),
                 ("name as declared", "name_as_declared"), ("qualifier", "qualifier"), ("tier", "tier"),
                 ("captures", "captures"), ("page shape", "shape")),
         dates=(("first captured on", "captured_on"), ("last captured on", "last_captured_on")),
         urls=("url", "archive_url"),
         names=("name", "name_as_declared"),
         parent=("Page", "party_board_pages", "document"),
         note="the board a party declares on its own website, as captured; built and not deployed to the Follow the Money site (ruling 72)",
         relations=(Relation("role", "party", "parties", to_column="name", label="on the board of"),)),
    View("party_board_pages", "party_boards", "document", ("party", "url"), key_col="document", default_order="document",
         search=("url",),
         fields=(("party", "party"), ("status", "status"), ("page shape", "shape"), ("reason", "reason"),
                 ("rows", "rows"), ("set aside", "set_aside"), ("capture kind", "capture_kind")),
         dates=(("captured on", "captured_on"),),
         urls=("url", "archive_url"),
         joins=(Join("Declared roles", "party_board_roles", "document", key_column="document", order="name"),)),
    # ── step 5.4, the senior courts' judgments (courts-1; catalogued in the merge after) ──
    View("court_judgments", "courts", "document", ("citation", "court_name"),
         search=("citation", "heading", "case_numbers"),
         fields=(("court", "court_name"), ("registry", "registry"), ("case numbers", "case_numbers"),
                 ("judges", "judges"), ("heading", "heading"), ("outcome", "outcome"),
                 ("paragraphs", "paragraphs"), ("parties", "parties"), ("suppression", "suppression"),
                 ("suppression kinds", "suppression_kinds"), ("names withheld", "names_withheld"),
                 ("status", "status"), ("missing", "missing"), ("source", "source")),
         dates=(("judgment date", "judgment_date"),),
         urls=("source_url",),
         withheld="names_withheld",
         joins=(Join("Parties", "court_judgment_parties", "judgment", key_column="judgment", order="position"),),
         note="a court's suppression order binds every surface: a withheld name is withheld here and in every product"),
    View("court_judgment_parties", "courts", "person", ("name", "role"),
         search=("name",),
         fields=(("citation", "citation"), ("court", "court"), ("position", "position"), ("role", "role"),
                 ("capacity", "capacity"), ("the Crown", "crown"), ("anonymised", "anonymised"),
                 ("confidence", "confidence")),
         dates=(("judgment date", "judgment_date"),),
         names=("name",), suppressed="withheld",
         parent=("Judgment", "court_judgments", "judgment")),
    # ── courts-2 (30 October): the four views the lane published beside the judgments, catalogued in the merge after (ruling 123) ──
    View("court_documents", "courts", "document", ("kind", "citation"),
         search=("citation", "case_numbers", "url"),
         fields=(("kind", "kind"), ("case", "case_slug"), ("state", "state"), ("profile", "profile"),
                 ("outcome", "outcome"), ("pages", "pages"), ("read from", "read_from"), ("characters of text", "text_chars"),
                 ("citation", "citation"), ("case numbers", "case_numbers"), ("model", "model")),
         dates=(("dated", "dated"), ("fetched", "fetched_at")), urls=("url",),
         joins=(Join("People the text reader named", "court_people", "document", key_column="document", order="key"),),
         note="one row per captured file of the MCP's courts corpus; the text reader's summary is in no view: \"url\" opens the record whole (ruling 88, the board only)",
         default_order="dated"),
    View("court_cases", "courts", "document", ("case_name", "citation"),
         search=("case_name", "citation", "case_numbers"),
         fields=(("court", "court"), ("citation", "citation"), ("case numbers", "case_numbers"), ("judges", "judges"),
                 ("result", "result"), ("suppression", "suppression"), ("links", "links")),
         dates=(("judgment", "date_of_judgment"), ("hearing", "date_of_hearing")), urls=("url",),
         withheld="suppression",
         joins=(Join("Links on the case page", "court_case_links", "case", order="position"),),
         note="the Supreme Court's case page as the site serves it; under a suppression the case name is withheld at the load",
         default_order="date_of_judgment"),
    View("court_case_links", "courts", "document", ("label", "section"),
         search=("label",),
         fields=(("section", "section"), ("position", "position"), ("linked document, where held", "linked_document")),
         urls=("href",),
         parent=("Case", "court_cases", "case")),
    View("court_people", "courts", "person", ("name", "role"),
         search=("name",),
         fields=(("kind", "kind"), ("role", "role"), ("role, as the text says", "role_text"), ("for", "for_party"),
                 ("citation", "citation"), ("case", "case_slug"), ("document kind", "document_kind"), ("model", "model")),
         dates=(("dated", "dated"),),
         names=("name",), suppressed="suppressed",
         note="a name the text reader found in the document, as the document prints it; not a link to any person: the links lane reads this view (ruling 123)",
         default_order="dated"),
    # ── step 5.3 (sanctions-1; catalogued in the merge after): limited partnerships, the Board's decisions, the held lists' views follow when published ──
    View("limited_partnerships", "limited_partnerships", "organisation", ("name", "number"),
         search=("name",), numbers=("number", "nzbn"),
         fields=(("number", "number"), ("NZBN", "nzbn"), ("kind", "kind"), ("type", "type_description"),
                 ("status", "status"), ("country of origin", "country_of_origin"),
                 ("registered office", "registered_office"), ("name withheld", "name_withheld")),
         dates=(("registered on", "registered_on"), ("office since", "office_since"), ("asked on", "asked_on")),
         joins=(Join("General partners", "limited_partnership_partners", "partnership_key", key_column="partnership_key", order="full_name"),),
         note="a partnership's registered office is shown (hard limit 15: a company's registered address is shown); limited partners are confidential by statute and not sought"),
    View("limited_partnership_partners", "limited_partnerships", "person", ("full_name", "kind"),
         search=("full_name", "first_name", "last_name"), numbers=("body_nzbn",),
         fields=(("kind", "kind"), ("body NZBN", "body_nzbn"), ("current", "current"), ("status", "status"),
                 ("dates stated", "dates_stated")),
         dates=(("started on", "started_on"), ("ended on", "ended_on"), ("asked on", "asked_on")),
         names=("full_name", "first_name", "middle_names", "last_name"), suppressed="suppressed",
         parent=("Partnership", "limited_partnerships", "partnership_key"),
         relations=(Relation("role", "partnership_key", "limited_partnerships", label="general partner of"),)),
    View("building_practitioner_decisions", "building_practitioners", "document", ("citation", "decision_kind"),
         search=("name", "citation", "complaint_number"), numbers=("lbp_number",),
         fields=(("complaint", "complaint_number"), ("kind", "decision_kind"), ("LBP number", "lbp_number"),
                 ("region", "region"), ("licence classes", "licence_classes"), ("penalties", "penalties"),
                 ("grounds", "grounds"), ("upheld", "upheld")),
         dates=(("decided on", "decided_on"),),
         urls=("decision_url", "pdf_url"),
         names=("name",), suppressed="suppressed",
         note="the Board's published decisions, shown for three years as the register itself shows them; the practitioner register is held (Building Act s 307)"),
    View("building_practitioners", "building_practitioners", "person", ("name", "licence_number"),
         search=("name",), numbers=("licence_number",),
         fields=(("licence number", "licence_number"), ("licence classes", "licence_classes"), ("status", "status"),
                 ("area", "area")),
         names=("name",), suppressed="suppressed",
         note="held: nothing is asked of the practitioner register (Building Act 2004 s 307, s 308); this view is empty until Arthur rules"),
    # ── step 5.3, the held sanctions lists (sanctions-1; catalogued in the merge after their views were published) ──
    View("sanctions_lists", "sanctions", "document", ("name", "version"), key_col="list_id", default_order="list_id",
         search=("name", "publisher"),
         fields=(("publisher", "publisher"), ("law", "law"), ("version", "version"), ("stated count", "stated"),
                 ("stated where", "stated_where"), ("listings", "listings"), ("ended", "ended"), ("set aside", "set_aside")),
         joins=(Join("Listings", "sanctions_listings", "list_id", key_column="list_id", order="name"),),
         note="held on the publishers' terms (sanctions-1): empty until a list is landed by hand under its licence or the publisher authorises a copy"),
    View("sanctions_listings", "sanctions", "person", ("name", "kind"),
         search=("name", "aliases"),
         fields=(("list", "list_id"), ("list reference", "list_ref"), ("other reference", "other_ref"), ("kind", "kind"),
                 ("status", "status"), ("aliases", "aliases"), ("original script", "original_script"), ("titles", "titles"),
                 ("positions", "positions"), ("nationalities", "nationalities"), ("countries", "countries"),
                 ("regime", "regime"), ("basis", "basis"), ("list version", "list_version")),
         dates=(("designated on", "designated_on"), ("renewed on", "renewed_on"), ("expires on", "expires_on"),
                ("ended on", "ended_on"), ("updated on", "updated_on")),
         names=("name",),
         parent=("List", "sanctions_lists", "list_id"),
         note="names and aliases as the list publishes them; countries and nothing finer (hard limit 15)"),
    # ── step 6.2, the GETS award notices (tenders-1; catalogued in the merge after; pane.md) ──
    View("award_notices", "tenders", "event", ("title", "posting_agency"),
         search=("title", "posting_agency", "department", "reference_number"), numbers=("rfx_id",),
         fields=(("GETS identifier", "rfx_id"), ("era", "era"), ("department", "department"), ("RFx type", "rfx_type"),
                 ("competition", "competition_type"), ("coverage", "tender_coverage"),
                 ("prequalification required", "prequalification_required"), ("reference", "reference_number"),
                 ("award type", "award_type"), ("value NZD", "value_nzd"), ("value note", "value_note"),
                 ("regions", "regions"), ("categories", "categories"), ("suppliers named", "suppliers_named"),
                 ("file report date", "report_date"), ("licence", "licence"), ("attribution", "attribution")),
         dates=(("opened on", "opened_on"), ("closed on", "closed_on"), ("awarded on", "awarded_on")),
         joins=(Join("Suppliers", "award_suppliers", "notice_key", key_column="notice_key", order="business_name"),),
         note="a notice lists who won what and when; it never says why. 'Not Awarded' is also how an agency marks a tender awarded off the system"),
    View("award_suppliers", "tenders", "organisation", ("business_name", "posting_agency"),
         search=("business_name",), numbers=("nzbn", "rfx_id"),
         fields=(("NZBN", "nzbn"), ("NZBN as published", "nzbn_as_published"), ("NZBN form", "nzbn_form"),
                 ("country", "country"), ("agency", "posting_agency"), ("notice", "title"), ("award type", "award_type"),
                 ("notice value NZD", "notice_value_nzd"), ("licence", "licence"), ("attribution", "attribution")),
         dates=(("awarded on", "awarded_on"),),
         names=("business_name",),
         parent=("Notice", "award_notices", "notice_key"),
         note="the supplier as published; no address and no website is held (a supplier may be a sole trader)",
         relations=(Relation("dealing", "notice_key", "award_notices", label="awarded in"),)),
    # ── step 5.3, the regulator actions (regulators-1; catalogued in the merge after) ──
    View("commerce_commission_cases", "commerce_commission", "event", ("case_number", "title"),
         search=("title", "case_number", "acts", "industry"),
         fields=(("kind", "kind"), ("sub-category", "sub_category"), ("Act and section", "act_section"), ("Acts", "acts"),
                 ("sections", "sections"), ("industry", "industry"), ("status", "status"), ("outcome", "outcome"),
                 ("title withheld", "title_withheld")),
         dates=(("opened on", "opened_on"), ("closed on", "closed_on"), ("action on", "action_on")),
         urls=("url",), withheld="title_withheld",
         joins=(Join("Parties", "commerce_commission_parties", "case_key", key_column="case_key", order="ordinal"),),
         note="the Commission's case register as it lists it today (CC BY 4.0); a name the Commission withholds is withheld here"),
    View("commerce_commission_parties", "commerce_commission", "organisation", ("name", "trading_as"),
         search=("name", "trading_as"), numbers=("company_number",),
         fields=(("trading as", "trading_as"), ("organisation", "organisation"), ("company number", "company_number"),
                 ("withheld by", "withheld_by"), ("split from", "split_from"), ("ordinal", "ordinal")),
         names=("name",), suppressed="withheld",
         parent=("Case", "commerce_commission_cases", "case_key"), default_order="ordinal"),
    View("fma_actions", "fma", "event", ("kind", "title"),
         search=("title", "summary", "acts"),
         fields=(("kind", "kind"), ("summary", "summary"), ("Acts", "acts"), ("sections", "sections"), ("outcome", "outcome"),
                 ("outcome when", "outcome_when"), ("names nobody", "names_nobody"), ("title withheld", "title_withheld")),
         dates=(("action on", "action_on"), ("outcome on", "outcome_on")),
         urls=("url",), withheld="title_withheld",
         joins=(Join("Parties", "fma_parties", "action_key", key_column="action_key", order="ordinal"),),
         note="the Financial Markets Authority's warnings, alerts and enforcement cases as listed today (CC BY 4.0); a topic alert names nobody"),
    View("fma_parties", "fma", "organisation", ("name", "named_in"),
         search=("name",), numbers=("company_number",),
         fields=(("organisation", "organisation"), ("company number", "company_number"), ("named in", "named_in"),
                 ("withheld by", "withheld_by"), ("split from", "split_from"), ("ordinal", "ordinal")),
         names=("name",), suppressed="withheld",
         parent=("Action", "fma_actions", "action_key"), default_order="ordinal"),
    View("worksafe_actions", "worksafe", "event", ("kind", "title"),
         search=("title", "industry", "court", "section_charged"),
         fields=(("kind", "kind"), ("industry", "industry"), ("offence when", "offence_when"), ("section charged", "section_charged"),
                 ("Acts", "acts"), ("sections", "sections"), ("charged when", "charged_when"), ("court", "court"), ("plea", "plea"),
                 ("decision", "decision"), ("fine", "fine_text"), ("fine amount", "fine_amount"), ("reparation", "reparation_text"),
                 ("status", "status"), ("title withheld", "title_withheld")),
         dates=(("offence on", "offence_on"), ("charged on", "charged_on"), ("decided on", "decided_on"),
                ("published on", "published_on"), ("accepted on", "accepted_on"), ("action on", "action_on")),
         urls=("url",), withheld="title_withheld",
         joins=(Join("Parties", "worksafe_parties", "action_key", key_column="action_key", order="ordinal"),),
         note="WorkSafe's court summaries and enforceable undertakings, the facts as stated and nothing inferred; an unnamed defendant's code is withheld"),
    View("worksafe_parties", "worksafe", "organisation", ("name", "named_in"),
         search=("name",), numbers=("company_number",),
         fields=(("organisation", "organisation"), ("company number", "company_number"), ("named in", "named_in"),
                 ("withheld by", "withheld_by"), ("split from", "split_from"), ("ordinal", "ordinal")),
         names=("name",), suppressed="withheld",
         parent=("Action", "worksafe_actions", "action_key"), default_order="ordinal"),
    # ── step 5.3, the overseas investment decisions (oio-1; catalogued in the merge after) ──
    View("overseas_investment_decisions", "overseas_investment", "event", ("case_number", "kind"),
         search=("case_number", "case_numbers", "investment", "rationale", "pathway"),
         fields=(("case numbers", "case_numbers"), ("kind", "kind"), ("outcome", "outcome"), ("granted", "granted"),
                 ("section", "section"), ("decision maker", "decision_maker"), ("pathway", "pathway"),
                 ("investment class", "investment_class"), ("investment", "investment"), ("areas as stated", "areas_stated"),
                 ("area (ha)", "area_ha"), ("consideration", "consideration_heading"), ("consideration as stated", "consideration_stated"),
                 ("consideration NZD", "consideration_nzd"), ("consideration withheld", "consideration_withheld"),
                 ("penalty", "penalty_stated"), ("notification", "notification_number"), ("parent case", "parent_case"),
                 ("applicant as listed", "applicant_listed"), ("rationale", "rationale"), ("attribution", "attribution")),
         dates=(("decided on", "decided_on"),),
         urls=("url",),
         joins=(Join("Parties", "overseas_investment_parties", "decision_key", key_column="decision_key", order="ordinal"),),
         note="the office's summary as published (Crown copyright, CC BY 4.0); the land's legal descriptions and street addresses are withheld on every row (hard limit 15, queue)"),
    View("overseas_investment_parties", "overseas_investment", "organisation", ("name", "role"),
         search=("name",), numbers=("company_number",),
         fields=(("role", "role"), ("role as stated", "role_stated"), ("status", "status"), ("trust", "trust"),
                 ("organisation", "organisation"), ("company number", "company_number"), ("ownership lines", "ownership_lines"),
                 ("origins", "origins"), ("shares", "shares"), ("ownership scope", "ownership_scope"),
                 ("withheld by", "withheld_by"), ("ordinal", "ordinal")),
         names=("name",), suppressed="withheld",
         parent=("Decision", "overseas_investment_decisions", "decision_key"), default_order="ordinal",
         relations=(Relation("dealing", "decision_key", "overseas_investment_decisions", label="party to"),)),
    # ── step 6.3, the grants (grants-1; catalogued in the merge after) ──
    View("grant_publishers", "grants", "organisation", ("name", "kind"),
         search=("name",),
         fields=(("kind", "kind"), ("role", "role"), ("website", "website"), ("on the Department's list", "on_departments_list"),
                 ("grants", "grants"), ("licence", "licence"), ("attribution", "attribution")),
         urls=("website",),
         joins=(Join("Grants", "grants", "grantor_key", key_column="key", order="decided_on"),
                Join("Recipients", "grant_recipients", "grantor_key", key_column="key", order="name_as_published")),
         note="the Department of Internal Affairs, the Lottery Grants Board and each class 4 society as the Department lists it"),
    View("grants", "grants", "event", ("recipient_as_published", "grantor"),
         search=("recipient_as_published", "recipient_final_as_published", "grantor", "grantor_as_published", "purpose_as_published"),
         numbers=("nzbn", "charity_number"),
         fields=(("grantor", "grantor"), ("grantor as published", "grantor_as_published"), ("committee", "committee"),
                 ("recipient as published", "recipient_as_published"), ("recipient kind", "recipient_kind"),
                 ("NZBN", "nzbn"), ("charity number", "charity_number"), ("status", "status"),
                 ("requested as published", "amount_requested_as_published"), ("granted as published", "amount_granted_as_published"),
                 ("amount NZD", "amount_nzd"), ("multi-year", "multi_year"), ("purpose as published", "purpose_as_published"),
                 ("category 1", "category_1"), ("category 2", "category_2"), ("period", "period"), ("round", "round"),
                 ("refund", "is_refund"), ("benefits", "benefits"), ("territorial authority", "territorial_authority"),
                 ("region", "region"), ("licence", "licence"), ("attribution", "attribution")),
         dates=(("decided on", "decided_on"), ("refunded on", "refunded_on")),
         names=("recipient_as_published",),
         parent=("Grantor", "grant_publishers", "grantor_key"), default_order="decided_on",
         note="every grant as the Department's national file or a Lottery record of grants prints it (CC BY 4.0); a recipient is kept as printed and never looked up; declined applications as the Department shows them (queue)",
         relations=(Relation("dealing", "recipient_key", "grant_recipients", label="granted to"),)),
    View("grant_recipients", "grants", "organisation", ("name_as_published", "grantor"),
         search=("name_as_published",), numbers=("nzbn", "charity_number"),
         fields=(("grantor", "grantor"), ("kind", "kind"), ("NZBN", "nzbn"), ("charity number", "charity_number"),
                 ("grants", "grants"), ("accepted", "accepted"), ("declined", "declined"), ("amount NZD", "amount_nzd"),
                 ("first period", "first_period"), ("last period", "last_period"), ("licence", "licence"), ("attribution", "attribution")),
         names=("name_as_published",),
         parent=("Grantor", "grant_publishers", "grantor_key"), default_order="name_as_published",
         note="one row per grantor and recipient name as published"),
    # ── step 6.2 template 3, the iwi and hapū directory (settlements-1; catalogued in the merge after; pane.md) ──
    View("iwi_directory_entities", "iwi_directory", "organisation", ("name", "kind"),
         search=("name", "listed_as", "region", "legal_entity", "hapu_represented", "area_of_interest", "local_authorities", "wharenui"),
         numbers=("charity_number", "nzbn"),
         fields=(("kind", "kind"), ("listed as", "listed_as"), ("region", "region"), ("legal entity", "legal_entity"),
                 ("governance structure", "governance_structure"), ("hapū represented", "hapu_represented"),
                 ("area of interest", "area_of_interest"), ("local authorities", "local_authorities"),
                 ("primary purpose", "primary_purpose"), ("website", "website"), ("wharenui", "wharenui"),
                 ("location", "location"), ("roles as printed", "flags"), ("charity number", "charity_number"), ("NZBN", "nzbn"),
                 ("last updated as printed", "last_updated"), ("pages", "pages"), ("source", "source")),
         urls=("website", "url"),
         joins=(Join("Relations", "iwi_directory_relations", "from_key", key_column="key", order="relation"),
                Join("Settlements", "iwi_directory_settlements", "entity_key", key_column="key", order="act_year")),
         default_order="name",
         note="as supplied to Te Puni Kōkiri by the organisations; not advice on whom to consult. No person, phone, email or postal address is held; a marae's location is the marae's own"),
    View("iwi_directory_relations", "iwi_directory", "event", ("relation", "to_name"),
         search=("to_name", "relation", "section"),
         fields=(("relation", "relation"), ("to", "to_name"), ("section of the page", "section")),
         urls=("url",),
         parent=("Entity", "iwi_directory_entities", "from_key"), default_order="relation",
         note="hapū of iwi, marae of hapū or iwi, organisation of iwi, iwi in region, rohe in local authority, as the directory lists them"),
    View("iwi_directory_settlements", "iwi_directory", "event", ("name", "act"),
         search=("name", "act", "as_printed"),
         fields=(("Act", "act"), ("year", "act_year"), ("stage", "stage"), ("signed on", "signed_on"), ("as printed", "as_printed"),
                 ("settlement", "settlement_key")),   # one row per body since fix-registers-iwi-directory-1's second sitting; the settlement's own key beside it
         urls=("url",),
         parent=("Entity", "iwi_directory_entities", "entity_key"), default_order="act_year",
         note="the Act or deed a governance entity's own entry names; a mandate is a stage, never a settlement"),
    # ── step 6.3, agency contract disclosures (procurement-1; pane.md) ──
    View("agency_contract_costs", "contract_disclosures", "figure", ("contract_class", "financial_year"),
         search=("agency", "contract_class", "region", "territorial_authority"),
         fields=(("agency", "agency"), ("level", "level"), ("region", "region"), ("territorial authority", "territorial_authority"),
                 ("contract class", "contract_class"), ("financial year", "financial_year"), ("year ended", "year_ended"),
                 ("active claims as published", "active_claims_as_published"), ("total costs as published", "total_costs_as_published"),
                 ("active claims", "active_claims"), ("total costs NZD", "total_costs_nzd"), ("suppressed", "suppressed"),
                 ("licence", "licence"), ("attribution", "attribution")),
         default_order="financial_year",
         note="ACC's own Official Information Act answer: claims and costs through each class of its health contracts, by year and place; no supplier is named; a suppressed cell is shown as ACC printed it"),
    # ── step 6.3, the councils lanes (councils-1; catalogued in the merge after; each lane's views.md) ──
    View("council_meetings", "council_minutes", "event", ("council", "body"),
         search=("council", "body", "kind", "code", "minutes_file"),
         fields=(("council", "council"), ("body", "body"), ("time", "meeting_time"), ("kind", "kind"), ("code", "code"),
                 ("documents listed", "documents"), ("minutes file", "minutes_file"), ("minutes held", "minutes_held"),
                 ("minutes sha256", "minutes_sha256"), ("source", "source")),
         dates=(("meeting date", "meeting_date"),),
         urls=("minutes_url", "listing_url"),
         default_order="meeting_date",
         note="one row per meeting on the council's own InfoCouncil listing; the minutes are held by hash and never read (plan 6.3): no attendance, no resolution, no venue"),
    View("councillor_interest_registers", "councillor_interests", "document", ("council", "form"),
         search=("council", "host", "form", "why"),
         fields=(("host", "host"), ("form", "form"), ("documents held", "documents_held"), ("members read", "members_read"), ("why", "why")),
         urls=("landing_url",),
         joins=(Join("Interests", "councillor_interests", "council", key_column="council", order="member"),),
         default_order="council", key_col="council",
         note="the 78 councils' registers of members' interests: where each is, in what form, what is held, and why nothing is read where it is not"),
    View("councillor_interests", "councillor_interests", "person", ("member", "council"),
         search=("member", "council", "role", "category"),
         fields=(("council", "council"), ("role", "role"), ("category", "category"), ("entries", "entries"),
                 ("as at", "as_at"), ("source", "source")),
         urls=("url",),
         names=("member",),
         parent=("Register", "councillor_interest_registers", "council"), default_order="member",
         note="an elected member's declared interests as the council's own structured register publishes them; never real property, a home, an address, a contact, or a spouse's or partner's interests. Off the public site unless Arthur says (hard limit 14)"),
    # ── step 6.3, local election candidate returns (local-elections-1; catalogued in the merge after; views-note.md) ──
    View("local_election_returns", "local_elections", "document", ("candidate_as_listed", "council", "election_year"),
         search=("candidate_as_listed", "council", "position"),
         fields=(("council", "council"), ("election", "election_year"), ("by-election", "by_election"),
                 ("covers", "covers"), ("seat", "position"), ("kind", "return_kind"), ("file held", "file_state"),
                 ("file", "file_document"), ("source", "source")),
         urls=("file_url", "listing_url"),
         names=("candidate_as_listed",),
         joins=(Join("Coverage", "local_election_returns_coverage", "council", key_column="council", order="election_year"),),
         default_order="election_year",
         note="a return the council's electoral officer lists under s 112F, held and not read: no amount and no donor until the returns' reading (ruling 79); the candidate's name as the listing prints it, matched to no one by this lane"),
    View("local_election_returns_coverage", "local_elections", "figure", ("council", "election_year"),
         search=("council",),
         fields=(("by-election", "by_election"), ("returns listed", "returns_listed"), ("combined files", "combined_files"),
                 ("files held", "files_held"), ("files failed", "files_failed")),
         default_order="council", key_col="council",
         note="a council's election: what its electoral officer lists and what the estate holds"),
)

BY_NAME = {v.name: v for v in VIEWS}


#: the field search (ruling 82): for each view, which column holds which field.
#: A view not listed has only the year of its dates. Every column is checked
#: against its view (check.py, tests/test_catalogue.py). Every Name says its
#: order (ruling 85), with the reason beside it: the lane's pane.md or spec,
#: its reader, or the register's printed form; where none states it, AMBIGUOUS.
_P3 = Name(first="first_name", middle="middle_names", last="last_name", order=PARTS)
FIELDS_OF = {
    "companies": Fields(organisation=("name",)),
    "directors": Fields(names=(_P3,)),
    "shareholders": Fields(names=(Name("name", order=GIVEN_FAMILY),), named=("name",)),   # the Companies Office's full_name, given names then SURNAME
    "company_addresses": Fields(address=("line_1", "line_2", "line_3", "line_4", "postcode")),
    "company_states": Fields(organisation=("name",)),
    "company_lookups": Fields(organisation=("name",)),
    "company_lookup_roles": Fields(names=(_P3,)),
    "company_lookup_holdings": Fields(names=(Name("name", order=AMBIGUOUS),), named=("name",)),   # no row published yet; the lane states no order
    "societies": Fields(organisation=("name",)),
    "society_officers": Fields(names=(_P3,)),
    "society_states": Fields(organisation=("name",)),
    "charities": Fields(organisation=("name", "other_names"), address=("address_for_service",)),
    "charity_officers": Fields(names=(Name(first="first_name", middle="middle_name", last="last_name", order=PARTS),)),
    "promoter_expense_returns": Fields(names=(Name("promoter", order=AMBIGUOUS),),   # a promoter as the return is filed: the form fixes no order
                                         named=("promoter",), year=("year",)),
    "party_statement_figures": Fields(organisation=("party", "party_label"), year=("filed_year",)),
    "candidate_return_totals": Fields(names=(Name(given="given_names", last="surname", order=PARTS),), organisation=("party",), year=("year",)),
    "candidate_return_donors": Fields(names=(Name("donor", order=AMBIGUOUS),          # the donor as the candidate wrote it: the form fixes no order
                                                Name(given="given_names", last="surname", order=PARTS)), named=("donor",),
                                      organisation=("party",), year=("year",)),
    "disclosures": Fields(names=(Name("donor_name", order=AMBIGUOUS),),   # the donor as the party declared it: no order
                           named=("donor_name",), organisation=("party", "party_label")),
    "disclosure_items": Fields(names=(Name("contributor", order=AMBIGUOUS),),   # as the declaration itemises it: no order
                                named=("contributor",)),
    "mp_expenses": Fields(names=(Name("name", order=AMBIGUOUS),     # the lane turns "Surname, Given" round but leaves the workbook's "Logie Jan" as printed
                                 Name("member", order=FAMILY_GIVEN)),   # the workbook prints the surname first, with or without a comma
                          organisation=("party", "party_label")),
    "minister_expenses": Fields(names=(Name("name", order=GIVEN_FAMILY),     # expenses/read.py person(): given-first, honorifics off
                                       Name("member", order=GIVEN_FAMILY)),  # the listings print "Hon Given Surname"
                                organisation=("party", "party_label")),
    "gazette_notices": Fields(year=("year",)),
    "gazette_celebrants": Fields(names=(Name(given="given_names", last="surname", order=PARTS),), organisation=("organisation",)),
    "gazette_prohibitions": Fields(names=(Name("name", order=GIVEN_FAMILY),          # the notice's prose names the person given-first
                                          Name("also_known_as", order=AMBIGUOUS))),   # an alias in brackets: no order stated
    "gazette_liquidations": Fields(organisation=("company",)),
    "gazette_liquidators": Fields(names=(Name("name", order=GIVEN_FAMILY),)),     # the notice's signature, given-first
    "gazette_company_notices": Fields(organisation=("company",), named=("party",)),
    "gazette_practitioners": Fields(names=(Name("name", order=GIVEN_FAMILY),)),   # as the notice signs them, given-first
    "gazette_bankruptcies": Fields(names=(Name(given="given_names", last="surname", order=PARTS),
                                          Name("also_known_as", order=FAMILY_GIVEN))),   # printed as the subject is, "SURNAME, Given"
    "gazette_appointments": Fields(names=(Name("name", order=GIVEN_FAMILY),)),    # the appointee in the notice's prose, honorific first
    "party_labels": Fields(organisation=("label", "party_name")),
    "gazette_possessions": Fields(names=(Name("mortgagee", order=AMBIGUOUS), Name("mortgagor", order=AMBIGUOUS)),   # the lane states no order
                                 named=("mortgagee", "mortgagor")),
    "candidates": Fields(names=(Name("name", order=FAMILY_GIVEN),              # the Commission's "SURNAME, Given"
                                Name("display_name", order=GIVEN_FAMILY)),   # house/read.py: keys.names' given-first display
                         organisation=("party", "party_registered")),
    "members": Fields(names=(Name("name", order=FAMILY_GIVEN),              # the Commission's "SURNAME, Given"
                             Name("display_name", order=GIVEN_FAMILY)),   # house/read.py: keys.names' given-first display
                      organisation=("party", "party_registered")),
    "hansard_speeches": Fields(names=(Name("member_name", order=FAMILY_GIVEN),)),   # the old roster's "Kuriger, Barbara": the comma fixes it
    "parliament_written_questions": Fields(names=(Name("minister_name", order=GIVEN_FAMILY),)),   # "Hon Tama Potaka": 673,651 of 683,524 with the honorific, none with a comma
    "parliament_api_items": Fields(names=(Name("member_name", order=GIVEN_FAMILY),),   # the SOPs' member as served, "Lan Pham", "Dr ...": no comma in 783
                                   organisation=("party_name", "select_committee")),
    "minister_diary_releases": Fields(names=(Name("minister", order=GIVEN_FAMILY),)),   # as the release prints them, "Hon Chris Penk": no comma in 2,560
    "minister_diary_entries": Fields(names=(Name("minister", order=GIVEN_FAMILY),)),   # as the release prints them, "Hon Chris Penk"
    "beehive_release_ministers": Fields(names=(Name("name", order=GIVEN_FAMILY),)),   # the site's tag "Hon Chris Bishop": given then family, the honorific off the front
    "mp_interest_returns": Fields(names=(Name("name", order=GIVEN_FAMILY),      # mp_interests/read.py: keys.names' given-first display
                                         Name("member", order=GIVEN_FAMILY)),   # the register's header "Name (Party, Electorate)", given-first
                                  organisation=("party", "party_label")),
    "mp_interests": Fields(names=(Name("name", order=GIVEN_FAMILY), Name("member", order=GIVEN_FAMILY)),   # as mp_interest_returns
                           organisation=("party",)),
    "parties": Fields(names=(Name("secretary", order=AMBIGUOUS),),   # the lane states no order
                      organisation=("name", "first_name")),
    "party_names": Fields(organisation=("name",)),
    "party_events": Fields(organisation=("party_label", "new_name")),
    "party_expenses": Fields(organisation=("party", "party_label"), year=("year",)),
    "party_expense_returns": Fields(organisation=("party", "party_label"), year=("year",)),
    "party_financial_statements": Fields(organisation=("party", "party_label"), year=("filed_year",)),
    "broadcasting_allocations": Fields(organisation=("party", "party_label"), year=("year",)),
    "promoters": Fields(names=(Name("promoter", order=AMBIGUOUS),),   # as the promoter filed it: no order
                        named=("promoter",), year=("year",)),
    "promoter_people": Fields(names=(Name("name", order=AMBIGUOUS),),   # as the return names them: no order
                              named=("promoter",), year=("year",)),
    "promoter_expenses": Fields(names=(Name("promoter", order=AMBIGUOUS),),   # as filed: no order
                                named=("promoter",), year=("year",)),
    "party_return_totals": Fields(organisation=("party", "party_label"), year=("year",)),
    "party_return_donors": Fields(names=(Name("donor", order=AMBIGUOUS),),   # the donor as the party's return prints it: MILLS PHILLIP and Phillip Mills both (ruling 85)
                                  named=("donor",), organisation=("party", "party_label"), year=("year",)),
    "party_return_loans": Fields(names=(Name("lender", order=AMBIGUOUS),),   # as the return prints it: no order
                                 named=("lender",), organisation=("party", "party_label"), year=("year",)),
    "party_board_roles": Fields(names=(Name("name", order=GIVEN_FAMILY), Name("name_as_declared", order=GIVEN_FAMILY)),   # a party's page, ordinary text
                                organisation=("party",)),
    "party_board_pages": Fields(organisation=("party",)),
    "court_people": Fields(names=(Name("name", order=AMBIGUOUS),)),   # as the text reader found it in the document: the lane states no order
    "court_judgment_parties": Fields(names=(Name("name", order=AMBIGUOUS),),   # an intitulement in capitals: the lane states no order
                                     named=("name",)),
    "limited_partnerships": Fields(organisation=("name",), address=("registered_office",)),
    "limited_partnership_partners": Fields(names=(_P3,), named=("full_name",)),
    "building_practitioner_decisions": Fields(names=(Name("name", order=AMBIGUOUS),)),   # the lane states no order
    "building_practitioners": Fields(names=(Name("name", order=AMBIGUOUS),)),   # the lane states no order
    "sanctions_listings": Fields(names=(Name("name", order=AMBIGUOUS),),   # the lists' own orders differ; the lane states none
                                 named=("name",),
                                 dates=("designated_on", "expires_on", "ended_on", "updated_on")),   # renewed_on is a list of dates
    "award_suppliers": Fields(organisation=("business_name",)),
    "commerce_commission_parties": Fields(names=(Name("name", order=AMBIGUOUS),),   # "as published": no order stated
                                          organisation=("name", "trading_as")),
    "fma_parties": Fields(names=(Name("name", order=AMBIGUOUS),),   # "as published": no order stated
                          organisation=("name",)),
    "worksafe_parties": Fields(names=(Name("name", order=AMBIGUOUS),),   # the lane states no order
                               organisation=("name",)),
    "overseas_investment_parties": Fields(names=(Name("name", order=AMBIGUOUS),),   # "as published": no order stated
                                          organisation=("name",)),
    "grant_publishers": Fields(organisation=("name",)),
    "grants": Fields(names=(Name("recipient_as_published", order=AMBIGUOUS),),   # "exactly as printed": no order stated
                     organisation=("grantor",),
                     named=("recipient_as_published", "recipient_final_as_published")),
    "grant_recipients": Fields(organisation=("name_as_published", "grantor")),
    "iwi_directory_entities": Fields(organisation=("name", "legal_entity")),
    "iwi_directory_settlements": Fields(year=("act_year",)),
    "agency_contract_costs": Fields(dates=("year_ended",)),
    "councillor_interests": Fields(names=(Name("member", order=AMBIGUOUS),)),   # the lane states no order
    "local_election_returns": Fields(names=(Name("candidate_as_listed", order=AMBIGUOUS),),   # each council lists its own way
                                     year=("election_year",)),
    "local_election_returns_coverage": Fields(year=("election_year",)),
}

#: the only columns the address field may search: the registered addresses
#: organisations publish. No published table holds a person's home address
#: (hard limit 15) and the board never searches for one; societies publish
#: no address. A test holds every `address` declaration inside this set.
ADDRESS_COLUMNS = frozenset({
    ("company_addresses", "line_1"), ("company_addresses", "line_2"), ("company_addresses", "line_3"),
    ("company_addresses", "line_4"), ("company_addresses", "postcode"),
    ("charities", "address_for_service"), ("limited_partnerships", "registered_office"),
})


def fields_of(v: View) -> Fields:
    """The view's field declaration, its dates defaulting to the View's own."""
    f = FIELDS_OF.get(v.name, Fields())
    if f.dates is None:
        f = Fields(f.names, f.organisation, f.named, f.address, f.year, tuple(c for _, c in v.dates))
    return f


def field_columns(v: View) -> set:
    """Every column the field search reads in this view."""
    f = fields_of(v)
    return ({c for n in f.names for c in n.columns()} | set(f.organisation) | set(f.named) | set(f.address)
            | set(f.year) | set(f.dates))

#: the register folders in the order the first pane lists them, with a plain name each
REGISTERS = (
    ("party_returns", "Party donation and loan returns"),
    ("disclosures", "Large-donation disclosures"),
    ("parties", "Registered political parties"),
    ("party_finance", "Party finance: expenses, statements, promoters, broadcasting"),
    ("house", "Candidates, electorates and the House"),
    ("mp_interests", "MPs' declared interests"),
    ("parliament", "Parliament: written questions, bills, papers and archived pages"),
    ("hansard", "Hansard: who spoke in Parliament"),
    ("beehive", "Beehive: releases, speeches and features"),
    ("ministers_diaries", "Ministers' diaries: who met the minister"),
    ("expenses", "MPs' and ministers' expenses"),
    ("companies", "Companies, directors and shareholders"),
    ("societies", "Incorporated societies and their officers"),
    ("charities", "Charities register and officers"),
    ("candidate_returns", "Candidate donation and expense returns"),
    ("gazette", "Gazette notices"),
    ("party_boards", "Party boards as declared on party websites (ruling 72: not on the site)"),
    ("overseas_investment", "Overseas investment decisions"),
    ("grants", "Grants from gaming-machine societies and the Lottery Grants Board"),
    ("commerce_commission", "Commerce Commission cases"),
    ("fma", "Financial Markets Authority warnings and enforcement"),
    ("worksafe", "WorkSafe prosecutions and enforceable undertakings"),
    ("tenders", "Government procurement award notices (GETS open data, CC BY 3.0 NZ)"),
    ("sanctions", "Sanctions lists (held on the publishers' terms)"),
    ("limited_partnerships", "Limited partnerships and their general partners"),
    ("building_practitioners", "Licensed building practitioners: the Board's decisions (the register held)"),
    ("courts", "Court judgments of the senior courts, by caption"),
    ("iwi_directory", "Iwi, hapū, marae and post-settlement governance entities (Te Kāhui Māngai, CC BY 3.0 NZ as catalogued)"),
    ("contract_disclosures", "Agency contract disclosures: ACC's health contract costs (an OIA answer on the data catalogue, CC BY 3.0 NZ)"),
    ("council_minutes", "Council meetings on InfoCouncil (minutes held by hash, never read)"),
    ("councillor_interests", "Councillors' registers of interests, council by council (off the public site: hard limit 14)"),
    ("local_elections", "Local election candidate returns (listed; held unread until ruling 79 lifts)"),
)

#: the graph canvas's node colours (ruling 100), by family of register: 32 registers cannot take 32 colours each 3:1
#: on the picture's surface and 15 apart in OKLab (the best found is 13.5 apart), so registers of one family share a
#: colour, as the two same-person kinds share one hue in the key; the 14 colours are 17.5 or more apart and 3:1 or more
#: on the surface (tests/test_night.py, panes.contrast_problems). A node's register is named in its hover and the
#: canvas's legend. Queue item `graph-node-colours-by-family` asks whether to keep this or take 28 colours closer together.
FAMILIES = (
    ("party donations", "#60c0f8", ("party_returns", "disclosures")),
    ("candidate returns", "#8048e0", ("candidate_returns", "local_elections")),
    ("parties", "#f04020", ("parties", "party_boards")),
    ("party finance", "#f8c0c8", ("party_finance",)),
    ("the House", "#00d070", ("house", "parliament", "hansard", "beehive", "ministers_diaries")),
    ("declared interests", "#d0a008", ("mp_interests", "councillor_interests")),
    ("expenses", "#986800", ("expenses",)),
    ("companies", "#0088b0", ("companies", "limited_partnerships")),
    ("societies and charities", "#009000", ("societies", "charities")),
    ("iwi", "#90f8d0", ("iwi_directory",)),
    ("public money", "#f8e000", ("grants", "tenders", "contract_disclosures")),
    ("regulators", "#c02090", ("commerce_commission", "fma", "worksafe", "building_practitioners", "overseas_investment")),
    ("courts and sanctions", "#b888a0", ("courts", "sanctions")),
    ("notices and minutes", "#f878f8", ("gazette", "council_minutes")),
)
#: (register, colour) for every register, in the catalogue's order
REGISTER_COLOURS = tuple((r, c) for reg, _ in REGISTERS for _, c, regs in FAMILIES for r in regs if r == reg)
REGISTER_COLOUR = dict(REGISTER_COLOURS)
FAMILY_OF = {r: name for name, _, regs in FAMILIES for r in regs}

#: registers the plan names that no lane has published yet (plan step 4.1 and later steps)
NOT_HELD = (
    ("openlaw", "OpenLaw case law (held on its terms: queue, no default)"),
    ("hdc_decisions", "Health and Disability Commissioner decisions (held on the Commissioner's copyright terms: queue, no default)"),
    ("linz", "LINZ titles"),
    ("papers_past", "Papers Past"),
    ("tenancy_tribunal", "Tenancy Tribunal orders (held, nothing published: ruling 58)"),
    ("real_estate_authority", "Real Estate Authority decisions (held, nothing published: ruling 59)"),
    ("settlement_commitments", "Treaty settlement commitments (Te Haeata: behind a login, hard limit 6; watched)"),
    ("council_procurement", "Council procurement off GETS (barred by the councils' terms or behind a login; watched)"),
)

#: the plan's reference names registers by use case in one table only, "Not held" (docs/plan/reference/
#: registers-and-use-cases/not-held.md, its "Serves use cases" column); each of its sources, by the words it
#: begins with, and the board's registers that hold it, if any lane has built one (ruling 87). A source with
#: none reads "no lane". Held or not is read from `pub` at render time.
REFERENCE_REGISTERS = {
    "Securities register": (),
    "Parsed case law": ("openlaw",),
    "Tribunals, employment and environment courts": ("tenancy_tribunal", "real_estate_authority"),
    "Sole traders, partnerships, trusts": (),
    "Company filings": (),
    "Sanctions lists; limited partnership partners": ("sanctions", "limited_partnerships"),
    "Overseas ownership data": ("overseas_investment",),
    "Licensed building practitioners": ("building_practitioners",),
    "Health and Disability Commissioner decisions": ("hdc_decisions",),
    "Live tenders, agency contract disclosures, council procurement": ("tenders", "contract_disclosures", "council_procurement"),
    "Grants": ("grants",),
    "Local election returns, councillors' interests, council pay": ("local_elections", "councillor_interests"),
    "Iwi and hapū directory, settlement commitments, Māori Land Court": ("iwi_directory", "settlement_commitments"),
    "Stock exchange announcements": (),
    "Building consents; primary-industry prosecutions": (),
}

#: the links views the board reads once links/ publishes them (plan step 4.9: a search table published by links)
LINKS_VIEWS = {"links": "pub.links", "groups": "pub.groups", "decisions": "pub.decisions"}
#: every view the links module publishes: read through LINKS_VIEWS and the search table, never catalogued as a register view
LINKS_PUBLISHED = frozenset({"links", "groups", "decisions", "names", "old_decisions", "entities"})   # entities: ruling 123 (links-4); the board reads it in the fix that follows


#: ruling 92 (2): shown columns holding another view's key that no parent tuple or Relation names, as data:
#: view -> ((column, far view, far column), ...). The far column is the far view's key, or an official number
#: (an NZBN) the far view carries; the pane shows the far row's title in the column's place
POINTERS = {
    "shareholders": (("holder_nzbn", "companies", "nzbn"),),
    "company_lookup_roles": (("body_nzbn", "companies", "nzbn"), ("held_key", "directors", "key")),
    "limited_partnership_partners": (("body_nzbn", "companies", "nzbn"),),
    "charity_returns": (("group_key", "charities", "key"),),
    "gazette_liquidations": (("register_key", "companies", "key"),),
    "gazette_company_notices": (("register_key", "companies", "key"),),
    "gazette_possessions": (("mortgagee_register_key", "companies", "key"), ("mortgagor_register_key", "companies", "key")),
}


#: ruling 93: the status words, case folded and trimmed, of a company no longer on the register. pub.companies'
#: status values, 26 October 2026: Removed 1,066,680, removed 1,931, dissolved 28,534, deregistered 2,550, closed 65,
#: "Removed & In Liquidation" 2. Left out: liquidation, receivership and administration (still on the register),
#: CANCELLED 5, SUSPENDED 1, inactive 1 (not stated as off the register)
REMOVED_STATUS = frozenset({"removed", "deregistered", "dissolved", "closed", "removed & in liquidation"})
#: the views whose rows are hidden by status unless "show removed companies" is ticked: view -> its status column
REMOVED_OF = {"companies": "status"}


def pointers(v: View) -> dict:
    """{column: (far view, far column)} for every column a pane of `v` shows
    (its fields) that names another view's row (ruling 92 (2)): the parent
    tuple and each Relation matched to the far view's key, then POINTERS. A
    Relation matched to a name (a party by its name) is not one: the value
    is already the name."""
    shown = {c for _, c in v.fields}
    out = {}
    if v.parent and v.parent[2] in shown:
        out[v.parent[2]] = (v.parent[1], BY_NAME[v.parent[1]].key_col)
    for r in v.relations:
        if r.column in shown and r.to_column == BY_NAME[r.view].key_col:
            out.setdefault(r.column, (r.view, r.to_column))
    for column, view, to_column in POINTERS.get(v.name, ()):
        if column in shown:
            out.setdefault(column, (view, to_column))
    return out


def views_of(register: str) -> list:
    return [v for v in VIEWS if v.register == register]


#: a register's main view, the one its table opens first (ruling 92 (5)), where it is not the first catalogued
MAIN_VIEW = {"parties": "parties", "grants": "grants", "sanctions": "sanctions_listings", "hansard": "hansard_sittings",
             "beehive": "beehive_releases", "parliament": "parliament_written_questions",
             "ministers_diaries": "minister_diary_releases"}


def main_view_of(register: str) -> str:
    """The view a register's table opens on: MAIN_VIEW, else its first catalogued view."""
    return MAIN_VIEW.get(register) or views_of(register)[0].name


def columns_shown(v: View) -> set:
    """Every column a pane of this view reads; the citation's document, page
    and place are read when present and are not demanded here (a child row
    may cite through its parent)."""
    return (set(v.title) | {c for _, c in v.fields} | {c for _, c in v.dates} | set(v.urls) | set(v.names)
            | {c for _, c, _ in v.text} | set(re.findall(r"\{(\w+)\}", v.title_format))
            | {c for say in v.says for c in (say.column, *re.findall(r"\{(\w+)\}", say.words))}
            | {c for f in v.flags for c in f[:2]} | {c for _, c in v.cite} | ({v.served} if v.served else set()))


def fold_term(term: str) -> str:
    """The same fold the SQL applies: lower case, macrons dropped, runs of
    space collapsed."""
    out = term.strip().lower().translate(str.maketrans(MACRONS[0], MACRONS[1]))
    return " ".join(out.split())
