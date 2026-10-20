# Legal counterparty and conflict check: known limits

Template `legal` 0.1, use case 2. What the report cannot see, stated to the
reader. Checked on 2026-10-21 against twelve real subjects on `querynz_v4`
(the checkpoint, below). Each line is a limit accepted for now; the card
that would lift it is named.

## What it cannot see

- **The firm's own clients.** The report takes one row; the firm's client
  and matter list, and its opposing parties, are not an input. So the
  conflict check itself is the firm's: the flag `client-overlap` is always
  **blocked, never clear**, and counts the names to compare (the party,
  its officers and holders of record, the conflict web). No line in the
  report says there is no conflict.
  (`a-template-cannot-take-the-firms-client-list`)
- **The conflict web, from a company.** Started from a company, the report
  lists its directors, holders of record, registered office and the
  Gazette notices on it, and does not follow the people: the companies
  they share, their prohibitions, their insolvency appointments and their
  society roles are not read. The web section then prints "none found",
  which is not a clear; the flags block and say to start a report from
  each person listed. Started from a person (or a donation that takes a
  person's group) the web is read.
  (`a-company-start-does-not-follow-its-officers`)
- **Court judgments, tribunal decisions and disciplinary findings.** None
  is held (step 5.4); the flags `court-judgments` and
  `disciplinary-findings` are blocked. The catalogue has no not-held key
  for disciplinary findings or tribunals, so the section's not-held line
  names courts only and the text names the rest.
  (`the-not-held-list-lacks-disciplinary-findings-and-tribunals`)
- **Past roles.** The companies file lists current roles only: a company
  the person left, or one struck off with them on it, is not seen. A firm
  that acted for or against such a company cannot see the link here. The
  checks over a person's companies fire on what they see and are otherwise
  blocked; `past-roles` says so on every report.
  (`the-companies-file-holds-no-past-directorships`)
- **The companies an amalgamation joins.** A proposal naming the company
  is flagged, but the other companies in it, and the company it continues
  as, are other rows of the same notice and are not reached; nor is the
  date it takes effect. (`an-amalgamation-notices-other-companies-are-not-reached`,
  `an-amalgamation-row-carries-no-effective-date`)
- **A lender's entry into possession.** Published (`pub.gazette_possessions`)
  but unknown to the report's catalogue; `mortgagee-possession` is blocked.
  (`the-catalogue-does-not-know-gazette-possessions`)
- **A bankruptcy.** No link rule joins a Gazette bankruptcy notice to a
  person; `bankruptcy` is always blocked: a blank there is not a clear.
  (`bankruptcies-and-appointments-are-not-in-pub-names`)
- **Which company a liquidator was appointed to.** A practitioner's own
  appointments are listed, each citing its notice, but the row does not
  name the company. Receivers and administrators named in notices are not
  reached at all. (`a-liquidator-row-does-not-name-its-company`)
- **Every company of a busy director.** The walk lists 40 companies and
  reads the notices and officers of 12; past those, `walk-coverage` fires
  and the clears that need them block.
  (`the-walk-reads-twelve-companies-and-lists-forty`)
- **Who holds a company holder.** A holder of record that is a company is
  flagged and not followed: the register carries no business number for
  it. A nominee or trustee holds for others the register does not name.
  (`a-company-holder-carries-no-business-number`)
- **Smaller shared offices.** A registered office shared by fifty or more
  companies is flagged as a hub; which companies share a smaller one is
  not listed.
- **The Insolvency Register, the Personal Property Securities Register,
  the Charities Register, a limited partnership's partners, financial
  service providers, sanctions lists, land titles, the Commerce
  Commission's cases.** Not held; named in the last section and in the
  flags that would read them.

## How to read it

- **The party** is the row the report starts from and the rows a rule
  confirms are the same person. Every other row under the name is a
  **namesake**, listed first and apart with the reason it is only near; a
  conflict search on the name alone meets every one. Past fifty namesakes
  the report says it is partial.
- **Officers and holders of record** are as the companies file lists them,
  with its dates. A holding is a holding of record, never ownership.
- **The conflict web** is each company the person sits on, with its
  status and dates, and the other directors and holders on it, always
  near: a connection through another person is never confirmed. A name on
  two companies is two rows that share a name (`shared-boards`).
- **The Gazette** lists, under each company's name with its own date,
  liquidations, receiverships, administrations, winding-up applications
  (the day to be heard), creditors' notices, deeds of company arrangement,
  removals (the last day for objections), dissolutions, restorations,
  amalgamations, the Registrar's rectifications and transfers out; then
  prohibitions with their term and a practitioner's own appointments. A
  removal, an amalgamation or a rectification is not an insolvency; a deed
  of company arrangement is. A person a rectification names is never
  printed.
- **Two facts with dates sit side by side.** The report never says one
  followed from the other.
- **Hubs:** a professional director (50 or more directorships), a nominee,
  the Crown, a registered office shared by 50 or 1,000 companies.
- **Absence is not a finding.** "None found in …" is the most it says.
- Companies register rows come from the old estate's tables; the original
  monthly file is not held, so they cite the row.

## The checkpoint, 2026-10-21

Twelve real subjects (`checkpoint.list`), chosen from the tables to cover
the cases: a director of two companies both in liquidation (CRANELAB); a
company in receivership and liquidation with a winding-up application
(SACRED HILL VINEYARDS); a company an amalgamation names as the continuing
company (RED CIRCLE WHOLESALE); one the Registrar gave notice to rectify
(Nobilo Wine Group); one under a deed of company arrangement and later
administration (WAIKATO ICE SUPPLIES); one transferring out of New Zealand
(FEDMER HOLDING); a company with a nominee holder; a director in a
contested group whose name the link rules join to sixteen liquidator
appointments (near); a director confirmed to a prohibition that ended in
2023; a professional director of 60 companies (walk short); the most shared
name among directors (61 namesakes, a contested group of 337 rows, 380
names to compare, declared partial); a party donor row that takes a
director's group. All twelve printed; none was refused by the shape's
presentation rules; built in 0.3 to 6.1 seconds each.

Read against the Gazette source file (fields only, never the text): RED
CIRCLE WHOLESALE's amalgamation notice 2011-ot1330 published 3 March 2011,
names the company and the word amalgamation, and prints two dates the row
does not carry (carded); FEDMER HOLDING's transfer out 2019-ot3298
published 12 July 2019 and prints 26 July 2019, the row's "applies after"
day; WAIKATO ICE SUPPLIES's deed 2019-ot4535 published 30 September 2019,
prints 11 September 2019, the row's day the deed was executed, and names
the company in its title (the text names only the first of three).

Against the old legal checks (MC-L1 to MC-L5 in the old estate's
`data-layer/docs/USE_CASE_PROGRAMME.md`; the requirements file has no legal
section): the web two hops with each edge's basis (L1: from a person; from
a company blocked, carded); a shared registered office (L2: a hub at 50,
smaller sharing not listed); Gazette insolvency per web company (L3); the
conflict overlap with a client list (L4: not an input, carded, always
blocked); courts stated as not held in every report (L5).

What the checkpoint changed: a donation row that takes a person's group is
now read as that person (it blocked every check before); `shared-boards`
says how many of the companies reached are the person's confirmed (a
contested group's companies are near). Failures carded: five on the report
lane and one on the gazette lane (above).
