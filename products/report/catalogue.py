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
    register: str               # the lane folder, as pub.names and pub.links name it: a row's ref is `register:key`, so a
                                #   label of the catalogue's own finds no link (councils, rea and building_board did, to 9 November 2026)
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
    undated: str = ""           # why the register states no date for the connection: the item is undated, and says why


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
      role="role", published="published_on", statement="{title}, {body} ({action})",
      note="where an appointee lives is never kept; a Justice of the Peace's town is the list's, never an address"),
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
    # ── the regulators' listings (step 5.3 lanes; into the report 1 November 2026, the overnight's approval 4) ──────────
    V("worksafe_actions", "worksafe", "event", ("title",), names=("title",), suppressed="title_withheld", on="action_on",
      on_label="listed", amount="fine_amount",
      statement="{title}: WorkSafe {kind}, {court}, {decision}; fine {fine_text}, reparation {reparation_text}",
      note="a court summary or an enforceable undertaking as WorkSafe lists it today; the offence as stated, never a cause"),
    V("worksafe_parties", "worksafe", "organisation", ("name",), names=("name",), suppressed="withheld",
      entity=("worksafe_actions", "action_key"), on="action_on", on_label="listed",
      statement="{title}: named in WorkSafe's listing \"{entity}\"", note="a party as the listing names it; a name WorkSafe withheld is not shown"),
    V("commerce_commission_cases", "commerce_commission", "event", ("title",), names=("title",), suppressed="title_withheld",
      start="opened_on", end="closed_on", statement="{title}: Commerce Commission {kind} ({status}); {outcome}",
      note="a case as the Commission lists it today"),
    V("commerce_commission_parties", "commerce_commission", "organisation", ("name",), names=("name", "trading_as"),
      suppressed="withheld", entity=("commerce_commission_cases", "case_key"), on="action_on", on_label="listed",
      statement="{title}: named in the Commerce Commission's case \"{entity}\""),
    V("fma_actions", "fma", "event", ("title",), names=("title",), suppressed="title_withheld", on="action_on", on_label="listed",
      statement="{title}: Financial Markets Authority {kind}; {outcome}", note="a warning or a case as the FMA lists it today"),
    V("fma_parties", "fma", "organisation", ("name",), names=("name",), suppressed="withheld", entity=("fma_actions", "action_key"),
      on="action_on", on_label="listed", statement="{title}: named in the Financial Markets Authority's listing \"{entity}\""),
    V("building_practitioner_decisions", "building_practitioners", "person", ("name", "decision_kind"), names=("name",),
      suppressed="suppressed", on="decided_on", on_label="decided",
      statement="{title}: Building Practitioners Board decision {complaint_number}, upheld {upheld}; penalties {penalties}",
      note="a Board decision as published, shown for three years from the decision; a name the Board withholds is not shown"),
    # ── the Real Estate Authority's decisions database (registers/real_estate_authority, published 2 November 2026): a decision and
    # each licensee, agency or defendant it names; a suppressed decision's names withheld; the penalty never shown (it can name a
    # street, `penalty_names_address`), nor the reasoning, nor the complainant ──
    V("rea_decisions", "real_estate_authority", "event", ("citation",), names=("citation",), suppressed="suppressed", on="decided_on", on_label="decided",
      statement="{title}: {decided_by}, {decision}",
      note="a decision as the Authority's database lists it: the deciding body and its finding; the penalty and the reasoning are in the "
           "decision cited, never here"),
    V("rea_parties", "real_estate_authority", "person", ("name",), names=("name",), suppressed="suppressed", entity=("rea_decisions", "decision_key"),
      role="role", on="decided_on", on_label="decided",
      statement="{title}: {role} ({kind}; licence {licence_number}) named in {entity}, {decided_by}: {decision}",
      note="a licensee, agency or defendant as the decision names it; being named is not a finding against anyone unless the decision "
           "says so; a name the Authority suppressed is not shown"),
    # ── grants (registers/grants): a grant as its publisher lists it, joined to a company by its business number or to a charity by
    # its registration number, both as published ──
    V("grants", "grants", "figure", ("recipient_as_published", "decided_on"), names=("recipient_as_published",), on="decided_on",
      on_label="decided", amount="amount_nzd",
      statement="{title}: a grant of {amount} from {grantor} ({status}); {purpose_as_published}",
      note="a grant as the funder publishes it, joined by the business or charity number the funder printed; a request declined is "
           "listed with its status, and no amount is added across funders"),
    # ── the societies register's earlier states (registers/societies) ──
    V("society_states", "societies", "organisation", ("name",), names=("name",), as_in="file", start="registered_on", end="removed_on",
      entity=("societies", "society_key"), role="status",
      statement="{title}: an earlier state of {entity}, {status}, as the file {file} carried it; a later file changed it",
      note="the state a monthly file carried before a later file changed it; the day of the change is between the two files' cuts"),
    # ── councillors' declared interests (registers/councillor_interests): a member's register entry, by category; the entries' text
    # is never shown (it can name property), only that the register holds an entry under the category ──
    V("councillor_interests", "councillor_interests", "person", ("member",), names=("member",), role="category", on="as_at", on_label="as at",
      statement="{title}: {role} of {council}; the register of interests holds entries under {category}",
      note="a councillor's own published summary of the register of members' interests; the entries are in the document cited, never "
           "here; a name only: a namesake's until a rule confirms it"),
    V("limited_partnerships", "limited_partnerships", "organisation", ("name",), names=("name",), suppressed="name_withheld",
      start="registered_on", statement="{title}: {status} limited partnership, number {number}"),
    V("limited_partnership_partners", "limited_partnerships", "person", ("full_name",), names=("full_name", "first_name", "middle_names",
      "last_name"), suppressed="suppressed", start="started_on", end="ended_on", entity=("limited_partnerships", "partnership_key"),
      role="kind", statement="{title}: general partner of {entity} ({status})",
      note="a general partner, a person or a body, current or past, as the business-number register states it; the limited partners are not public"),
    V("overseas_investment_decisions", "overseas_investment", "event", ("case_number", "investment_class"), on="decided_on",
      on_label="decided", statement="Overseas Investment Office {kind} {title}: {outcome} ({pathway})",
      note="a decision summary as the Office lists it; street addresses are not in the view"),
    V("overseas_investment_parties", "overseas_investment", "organisation", ("name", "role_stated"), names=("name",),
      suppressed="withheld", entity=("overseas_investment_decisions", "decision_key"), role="role_stated", on="decided_on",
      on_label="decided", statement="{title}, in Overseas Investment Office decision {entity}",
      note="an applicant, vendor or consent holder as the decision summary names it; a name the Office withheld is not shown"),
    V("company_lookup_roles", "companies", "person", ("full_name", "role_type"), names=("full_name", "last_name"), suppressed="suppressed",
      start="started_on", end="ended_on", entity=("companies", "entity_key"), role="role_type",
      statement="{title}: {role} of {entity} ({role_status}), as the business-number register states it",
      note="a role the business-number register states and no monthly file held: a past director with the register's own dates, "
           "back to the company's registration; read company by company by the history backfill, so most companies are not yet asked"),
    # ── the October 2026 package's two files the lane reads beside the four (published 2 November 2026) ──
    V("company_insolvencies", "companies", "organisation", ("entity_name", "insolvency_type"), names=("entity_name",),
      on="appointed_on", on_label="appointed", end="vacated_on", entity=("companies", "entity_key"), role="appointment_type",
      statement="{title}: {appointee} appointed, as the companies file lists it",   # the appointment type ("239L - Court") reads as an address
      note="an insolvency practitioner's appointment as the Companies Office's file lists it, with the day of appointment and the "
           "day vacated where filed; a liquidation that follows a resolution of solvency is a solvent winding-up, never a failure"),
    V("retirement_villages", "companies", "organisation", ("name",), names=("name",), entity=("companies", "operator_key"), on="supervisor_appointed_on",
      on_label="supervisor appointed",
      statement="{title}: a retirement village operated by {operator_name}; statutory supervisor {supervisor_name}",
      note="the retirement villages file as the Companies Office publishes it: the operator and the statutory supervisor in office "
           "and the day appointed; an earlier supervisor is not in the file"),
    V("company_lookup_holdings", "companies", "person", ("name",), names=("name",), suppressed="suppressed",
      start="started_on", end="ended_on", entity=("companies", "entity_key"), role="holder_type",
      statement="{title}: a past holder of record of {entity} ({role}), as the business-number register states it",
      note="a holding the business-number register states and the monthly file no longer lists: a past holder of record with the "
           "register's own dates; a holder of record is not an owner; read company by company by the history backfill, so most "
           "companies are not yet asked"),
    # ── the courts corpus held (registers/courts; into the report 2 November 2026) ─────────────────────────────────
    V("court_judgments", "courts", "event", ("citation",), names=(), on="judgment_date", on_label="judgment",
      statement="{title}: a judgment or decision",
      note="a judgment as the courts corpus holds it; a name under a suppression order or withheld is never shown"),
    V("court_judgment_parties", "courts", "person", ("name",), names=("name",), suppressed="withheld",
      entity=("court_judgments", "judgment"), role="role", on="judgment_date", on_label="judgment",
      statement="{title}: {role} in {entity}",
      note="a party as the judgment's heading names it; being a party is not a finding against anyone"),
    V("court_people", "courts", "person", ("name",), names=("name",), suppressed="suppressed", role="role_text", on="dated",
      on_label="dated", statement="{title}: {role_text} in {citation} ({role})",
      note="a person or body a court document names, read by the text reader: a party, a judge, counsel, a witness or another"),
    # ── government contract awards, as GETS publishes its award notices (registers/tenders; into the report 2 November 2026) ──
    V("award_notices", "tenders", "event", ("title",), names=(), on="awarded_on", on_label="awarded", amount="value_nzd",
      statement="{title}: awarded by {posting_agency}, {amount}",
      note="a contract award notice as GETS publishes it; the value is the notice's, as published, and can be the whole panel's"),
    V("award_suppliers", "tenders", "organisation", ("business_name",), names=("business_name",), entity=("award_notices", "notice_key"),
      on="awarded_on", on_label="awarded", amount="notice_value_nzd",
      statement="{title}: a supplier awarded {entity}, by {posting_agency}",
      note="a supplier a GETS award notice names; the notice's value is the whole award's, not this supplier's share"),
    # ── the tables the diagnostic report reads (9 November 2026): every published table that names a person or a body ─
    # one kind per table, though several mix people and bodies (sanctions, title owners, the Hansard, Beehive and
    # Parliament mentions, diary attendees): such a table is walked as its larger part is, and the findings say so
    V("insolvency_people", "insolvency", "person", ("name",), names=("name",), suppressed="suppressed",
      start="adjudicated_on", end="discharged_on", role="insolvency_type",
      statement="{title}: {role} in the Insolvency Register, {status}; estate {estate_number}",
      note="a person's bankruptcy or no-asset procedure as the Insolvency Register lists it; an annulled one says so; no address is held in the view"),
    V("insolvency_companies", "insolvency", "organisation", ("name",), names=("name", "organisation_name"), suppressed="suppressed",
      start="liquidated_on", end="completed_on", entity=("companies", "entity_key"), role="insolvency_type",
      statement="{title}: {role} in the Insolvency Register, {status}; estate {estate_number}",
      note="a company or partnership estate the Official Assignee administers, as the Insolvency Register lists it"),
    V("linz_titles", "linz", "place", ("type", "land_district"), on="issued_on", on_label="issued",
      statement="a {type} land title in {land_district}, {status}; {number_owners} registered proprietor(s)",
      note="a title as LINZ publishes it; its registered proprietors are in pub.linz_title_owners"),
    V("linz_title_owners", "linz", "person", ("name",), names=("name", "prime_surname", "prime_other_names", "corporate_name"),
      entity=("linz_titles", "title_key"), role="owner_type",
      undated="LINZ publishes no date for a proprietor's registration on a title; the title's own issue date is on the title",
      statement="{title}: a registered proprietor ({role}) on {entity}, share {estate_share}",
      note="a registered proprietor as the title states it (the title's own term); a title is land, and no address is shown"),
    V("sanctions_listings", "sanctions", "person", ("name",), names=("name", "original_script"),
      start="designated_on", end="ended_on", role="kind",
      statement="{title}: {role} on a sanctions list ({regime}), {status}",
      note="a listing as its list publishes it; a revoked or expired listing says so"),
    V("building_practitioners", "building_practitioners", "person", ("name",), names=("name", "first_name", "middle_names", "last_name"),
      suppressed="suppressed", start="first_granted_on", role="licence_classes",
      statement="{title}: licensed building practitioner {licence_number}, {status}; classes {role}",
      note="the licence register as it stands today; the area named is the practitioner's stated working area, never an address"),
    V("company_lookups", "companies", "organisation", ("name",), names=("name",), on="asked_at", on_label="asked",
      start="registered_on", entity=("companies", "entity_key"),
      statement="{title}: {status} {type_description}, as the business-number register answered when asked",
      note="the business-number register's own answer for one company, read company by company"),
    V("company_changes", "companies", "event", ("kind", "subject"), names=("subject",), suppressed="suppressed",
      on="effective_on", on_basis="date_basis", entity=("companies", "entity_key"), role="kind",
      statement="{entity}: {role} changed: {subject}",
      note="a change between two files or answers of the register; the day is the register's where it states one"),
    V("grant_recipients", "grants", "organisation", ("name_as_published",), names=("name_as_published",),
      period=("first_period", "last_period"), amount="amount_nzd",
      statement="{title}: {grants} grant(s) from {grantor}, {amount} accepted",
      note="a recipient as its funder publishes it, gathered by the number printed where there is one; no amount is added across funders"),
    V("council_meetings", "council_minutes", "event", ("council", "body", "meeting_date"), on="meeting_date", on_label="met",
      statement="{council}, {body}: a {kind} meeting"),
    V("council_meeting_attendance", "council_minutes", "person", ("name",), names=("name",), on="meeting_date", on_label="met",
      entity=("council_meetings", "meeting_key"), role="role",
      statement="{title} ({role}), {attendance} at {entity}",
      note="as the minutes record it; a name in the minutes only, so a namesake's until a rule confirms it"),
    V("council_meeting_declarations", "council_minutes", "person", ("member",), names=("member",), on="meeting_date", on_label="met",
      entity=("council_meetings", "meeting_key"), role="role",
      statement="{title}: a declaration of interest recorded at {entity}, item {item}",
      note="the declaration's words are in the minutes cited, never here"),
    V("council_resolutions", "council_minutes", "event", ("item_title",), names=("mover", "seconder"), on="meeting_date", on_label="met",
      entity=("council_meetings", "meeting_key"),
      statement="{entity}: resolution {number} on {title}, moved by {mover}, seconded by {seconder}: {outcome}",
      note="a resolution as the minutes record it"),
    V("court_cases", "courts", "event", ("case_name",), names=("case_name",), on="date_of_judgment", on_label="judgment",
      statement="{title}: {court}, {citation}; {result}",
      note="a case as the courts' site lists it; a suppressed name is withheld in the view"),
    V("gazette_celebrants", "gazette", "person", ("surname", "given_names"), names=("surname", "given_names"),
      start="period_from", end="period_to", published="published_on", role="action",
      statement="{title}: {role} as a marriage or civil union celebrant ({organisation})"),
    V("gazette_board_interventions", "gazette", "organisation", ("board",), names=("board",), on="dated_on", published="published_on",
      role="action", statement="{title}: {role} under {statute}, directed by {directed_by}"),
    V("hansard_speeches", "hansard", "person", ("member_name",), names=("member_name",), on="sitting_on", on_label="sitting",
      role="role", statement="{title} ({party}) spoke in the House on {subject}",
      note="a speech as Hansard prints it; the words are in the day's record cited"),
    V("hansard_people", "hansard", "person", ("name",), names=("name",), on="sitting_on", on_label="sitting", role="role",
      statement="{title}: named in the House ({kind}) on {subject}",
      note="a person or body Hansard's text names, read by a model; a name only, so a namesake's until a rule confirms it"),
    V("beehive_people", "beehive", "person", ("name",), names=("name",), on="published_on", on_label="released", role="role",
      statement="{title}: named ({kind}) in the release \"{release}\"",
      note="a person or body a ministerial release names, read by a model; a name only, so a namesake's until a rule confirms it"),
    V("beehive_release_ministers", "beehive", "person", ("name",), names=("name",), on="published_on", on_label="released",
      statement="{title}: the minister of a {type} release"),
    V("parliament_people", "parliament", "person", ("name",), names=("name",), on="dated", role="role",
      statement="{title}: named ({kind}) in a Parliament {source_table} item",
      note="a person or body a Parliament page names, read by a model; a name only, so a namesake's until a rule confirms it"),
    V("parliament_written_questions", "parliament", "event", ("title",), names=("minister_name",), on="question_released_on",
      on_label="released", statement="written question {question_number}/{question_year} to {minister_name}: {title} ({status_id})",
      note="the question and reply are in the item cited"),
    V("minister_diary_attendees", "ministers_diaries", "person", ("attendee",), names=("attendee", "organisation"),
      on="entry_on", on_label="met", entity=("minister_diary_entries", "entry"), role="kind",
      statement="{title} ({role}): at a meeting in the diary of {minister}, {portfolio}",
      note="an attendee as the released diary prints them; a meeting's place is never shown"),
    V("minister_diary_entries", "ministers_diaries", "event", ("minister", "entry_on"), names=("minister",), on="entry_on",
      on_label="met", statement="{minister} ({portfolio}): a diary entry",
      note="the meeting's words are in the release cited; its place is never shown"),
    V("iwi_directory_entities", "iwi_directory", "organisation", ("name",), names=("name",), role="kind", on="last_updated",
      on_label="directory updated",
      statement="{title}: {role} in Te Kāhui Māngai ({region}); {legal_entity}",
      note="as the directory lists it; a business or charity number joins it to that register"),
    V("iwi_directory_settlements", "iwi_directory", "event", ("name",), names=("name",), on="signed_on", on_label="signed",
      statement="{title}: a Treaty settlement, {stage} ({act})"),
    V("local_election_returns", "local_elections", "person", ("candidate_as_listed",), names=("candidate_as_listed",),
      year="election_year", role="return_kind",
      statement="{title}: a local election return ({role}) to {council}, {election_year}",
      note="a candidate as the council lists the return; the figures are in the file cited"),
    V("party_board_roles", "party_boards", "person", ("name",), names=("name", "name_as_declared"), on="captured_on",
      on_label="seen", role="role", statement="{title}: {role} of {party}, as the party's own site states it",
      note="read from the party's whole site; a role a later capture no longer shows keeps its last day seen"),
    V("party_names", "parties", "organisation", ("name",), names=("name",), start="from_on", end="to_on",
      statement="{title}: a name of {party} ({kind})"),
    V("party_events", "parties", "event", ("kind", "party"), on="decided_on", published="published_on",
      statement="{party}: {kind} ({new_name})"),
    V("party_expenses", "party_finance", "figure", ("party", "year"), year="year", amount="total_expenses",
      statement="{party}: election expenses for {year}, {amount}"),
    V("party_financial_statements", "party_finance", "figure", ("party", "filed_year"), year="filed_year",
      statement="{party}: annual financial statements for the year to {balance_date}, filed {date_filed}"),
    V("broadcasting_allocations", "party_finance", "figure", ("party", "year"), year="year", amount="amount",
      statement="{party}: broadcasting allocation for {year}, {amount}"),
    V("promoter_expenses", "party_finance", "figure", ("promoter", "year"), names=("promoter",), year="year",
      amount="election_expenses", statement="{title}: a promoter's expenses for {year}, {amount}"),
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
    ("worksafe", "WorkSafe prosecutions and enforceable undertakings"),
    ("commerce_commission", "Commerce Commission cases"),
    ("fma", "Financial Markets Authority warnings and cases"),
    ("building_practitioners", "Building practitioners: the licence register and the Board's decisions"),
    ("limited_partnerships", "Limited partnerships and their general partners"),
    ("overseas_investment", "Overseas Investment Office decision summaries"),
    ("courts", "Court judgments (the courts corpus held)"),
    ("tenders", "Government contract award notices (GETS)"),
    ("real_estate_authority", "Real Estate Authority decisions (the Authority's decisions database)"),
    ("grants", "Grants as their funders publish them"),
    ("councillor_interests", "Councillors' registers of interests"),
    ("insolvency", "The Insolvency Register: personal bankruptcies, no-asset procedures and company estates"),
    ("linz", "LINZ land titles and their registered owners"),
    ("sanctions", "Sanctions lists"),
    ("council_minutes", "Council meetings: attendance, declarations of interest and resolutions"),
    ("hansard", "Hansard: speeches and the people the House names"),
    ("beehive", "Ministerial releases (Beehive): the people and bodies they name"),
    ("parliament", "Parliament's pages and written questions: the people and bodies they name"),
    ("ministers_diaries", "Ministers' diaries: meetings and attendees"),
    ("iwi_directory", "Te Kāhui Māngai: iwi, hapū, marae and their settlements"),
    ("local_elections", "Local election candidate returns"),
    ("party_boards", "Party boards as each party's site states them"),
)
REGISTER_NAME = dict(REGISTERS)

#: registers the plan names that no lane has published yet (step 4.1 and step 5.3), and the registers the
#: templates must say they cannot see: one list, each with the key a template's section cites in `not_held`
NOT_HELD = (
    ("court_coverage", "Court judgments the corpus held does not carry: most of the High Court's, the Court of Appeal's and the District Court's, and most tribunals'"),
    ("tribunals", "Tribunal decisions (employment, tenancy, environment, coroners)"),
    ("disciplinary", "Disciplinary tribunals' findings (lawyers, conveyancers, the other professional bodies)"),
    ("disputes", "Disputes Tribunal decisions"),
    ("employment", "Employment Relations Authority determinations"),
    ("securities", "The Personal Property Securities Register"),
    ("fsp", "Financial service providers"),
    ("tender_coverage", "Contracts awarded without a GETS award notice: under the thresholds, direct awards, and most councils' and private clients' contracts"),
    ("overseas", "Overseas company registers"),
    ("trusts", "Trusts: no New Zealand register exists"),
    ("unincorporated", "Sole traders, general partnerships and other business-number entities outside the companies file"),
    ("company_history", "The companies change history before 16 August 2026"),
    ("nzbn_interface", "The business-number interface, between monthly files (step 5.5)"),
    ("credit_bureau", "Credit-bureau defaults and payment records"),
    ("mpi", "Ministry for Primary Industries prosecutions and animal-tracing enforcement"),
    ("fire", "Fire and Emergency New Zealand notices"),
    # the registers a health regulator keeps (healthcare-1)
    ("hdc", "Health and Disability Commissioner decisions"),
    ("certification", "Certification audits of rest homes and hospitals"),
    ("health_providers", "The Ministry of Health's provider registers"),
    ("aged_care_commissioner", "The Aged Care Commissioner's reports"),
    # the registers a property developer check names (property-1); the Real Estate Authority lane captures and publishes no view yet
    ("building_consents", "Building consents, code compliance certificates and council minutes"),
)
NOT_HELD_NAME = dict(NOT_HELD)
#: not-held keys a template may still cite for a register a lane has since published: {old key: the register}. A template naming one
#: loads, the key is dropped from its section's blank, and the report says the register is published and the template does not read it
SUPERSEDED_NOT_HELD = {"charities": "charities", "rea": "real_estate_authority",   # rea: published 2 November 2026
                       "retirement_villages": "companies",
                       "building_practitioners": "building_practitioners",
                       "insolvency": "insolvency", "linz": "linz", "sanctions": "sanctions"}   # published; read by the catalogue from 9 November 2026   # the licensed practitioners' register, published (9 November 2026)   # the October 2026 package's villages file (2 November 2026)

#: what links/ publishes; read through walk, never as a register view
LINKS_VIEWS = frozenset({"links", "groups", "decisions", "names", "old_decisions"})

#: every other table a lane's publish.sql defines, and why the report reads no row of it (the diagnostic report's
#: inventory, 9 November 2026). A table neither here nor in VIEWS fails tests/test_catalogue.py: a new table is placed
#: before it is published, so a register that names people is never silently left out of every report
NOT_READ = {
    "agency_contract_costs": "an agency's contract totals by year: a figure on an agency, no person or body is a party",
    "beehive_release_annotations": "a model's notes on a release; the people it names are in beehive_people",
    "beehive_releases": "the release itself, a document; its people are in beehive_people and its ministers in beehive_release_ministers",
    "councillor_interest_registers": "which councils' registers were found and read: coverage, not rows",
    "court_case_citations": "the OpenLaw lane's, dropped on 3 November 2026 (ruling 137): defined, never loaded",
    "court_case_documents": "the links lane's join of a case to its documents, read through court_cases",
    "court_case_links": "the links a judgment's page carries: addresses, not people",
    "court_case_parties": "the OpenLaw lane's, dropped on 3 November 2026 (ruling 137): defined, never loaded",
    "court_case_statutes": "the OpenLaw lane's, dropped on 3 November 2026 (ruling 137): defined, never loaded",
    "court_company_numbers": "a company number a judgment prints: read by the links lane, which joins the company",
    "court_documents": "the judgment documents themselves; their parties are in court_judgment_parties",
    "elections": "an election: an event with no party to it",
    "electorates": "an electorate: a place",
    "entities": "the links lane's entities, read through the walk's groups",
    "expense_release_totals": "a release's printed totals: a check on the release, not a person's figure",
    "gazette_notices": "every notice's heading; the people and bodies are in the Gazette's own tables",
    "grant_publishers": "the funders that publish grants; each grant names its funder",
    "hansard_day_sections": "the shape of a sitting day: no person",
    "hansard_days": "a sitting day's record, a document",
    "hansard_sections": "a debate's section, a document; its speakers are in hansard_speeches",
    "hansard_sittings": "a sitting: an event with no party to it",
    "hdc_decision_providers": "the HDC lane's: defined, not published yet",
    "hdc_decisions": "the HDC lane's: defined, not published yet",
    "iwi_directory_relations": "how two directory entries relate (a marae of a hapū): read through iwi_directory_entities",
    "linz_place_names": "a place name: a place, no person",
    "local_election_returns_coverage": "how many returns each council listed and we hold: coverage, not rows",
    "minister_diary_releases": "a diary release, a document; its entries and attendees are read",
    "mp_interest_editions": "an edition of the register, a document; its returns are read",
    "papers_past_items": "Papers Past is searched, never mined (hard limit 17): no person is built from it",
    "parliament_api_items": "an item as Parliament's interface lists it, a document; its people are in parliament_people",
    "parliament_wayback_pages": "an archived page, a document; its people are in parliament_people",
    "party_board_pages": "a party site's page as captured, a document; its roles are in party_board_roles",
    "party_expense_returns": "a return's parts as read; the party's figure is in party_expenses",
    "party_labels": "how a printed party name was resolved: the parties lane's working, not a party",
    "party_statement_figures": "each line of a party's statements; the statement is in party_financial_statements",
    "promoter_expense_returns": "a return's parts as read; the promoter's figure is in promoter_expenses",
    "sanctions_lists": "a list itself; its listings are read",
}


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
    "organisation-sole-company": "a row's organisation name and the one body of the name on the companies, societies, partnerships and charities registers, live on the row's own date",   # rulings 106 (1), 114, 125
    "successor-name": "a company succeeded by another of its name with a year in brackets, a person on both",        # ruling 106 (2), related
    "candidate-same-party": "one candidate name standing for one party in two elections",                            # ruling 106 (3)
    "organisation-one-live-company": "a row's organisation name and the one of several bodies of the name live on the row's own date",   # rulings 107, 114, 125
    "refiled-name": "a company removed and another of its name registered within twelve months, a person on both",   # ruling 109, related
    "member-on-the-day": "a member's printed name, titles off, and the one member of that name sitting in the House on the row's day",   # ruling 116
    "judgment-number": "a court document prints the NZBN or company number of the company named as its party",         # ruling 1 (3 Nov)
    "shared-contact": "one email or phone number printed in two court documents, beside the same name",               # ruling 2 (4 Nov)
    "judgment-address-office": "a street address a court document prints and a company's registered office",          # ruling 3 (4 Nov)
    "judgment-address-judgment": "one street address printed in two court documents",                                 # ruling 142
    "judgment-address-insolvency": "a street address a court document prints and a bankrupt's address at adjudication",   # ruling 142
    "judgment-address-title": "a street address a court document prints and a land title's address, a registered proprietor of the title",   # ruling 142
    "owner-full-name": "a land title's registered proprietor and another row of the same first, middle and last name",   # 4 Nov
    "licence-number": "two rows of the Real Estate Authority's decisions printing one licence number",                 # 3 Nov
}


def rule_text(rule) -> str:
    """A links rule as the memo names it: "a company succeeded by … (links rule
    successor-name, version 1)"; a rule that is not a links rule (the walk's
    own: same-name, official-number, chain, …, which carry no version) as it is."""
    rid, at, version = str(rule or "").partition("@")
    if not at or rid not in RULE_WORDS:
        return str(rule or "")
    return f"{RULE_WORDS[rid]} (links rule {rid}, version {version})"
