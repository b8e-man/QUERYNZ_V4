# Model pass 2: a second reading to enrich and correct (3 November 2026)

Arthur, 3 November 2026: "wait on 2 and make a document called 'model pass 2'". The courts lane's tranche 2 (the
text reader re-reading every court document for identifying information) waits for this plan. Nothing in this plan
runs until Arthur says which profiles go first.

Pass 1 is what each lane's reader does today. Pass 2 is a second model reading of a document that pass 1 has already
read. It reads the same text, along with pass 1's stored reading, and returns two things:

- **Enrichments:** fields pass 1 was never asked for. First among them is every identifying detail the document
  prints (Arthur, 3 November: "any identifying information").
- **Corrections:** for each pass 1 value the text contradicts or leaves out, a proposed change, with the place in
  the text that shows it.

## The rules every pass 2 reader follows

1. **The model.** The local text reader (profile `text-reader`, the standing server on node2) through the model
   client. No text leaves the boxes. Temperature 0. Pieces are cut by the profile's own split rule (ruling 130),
   never as excerpts.
2. **One reading, stored.** One pass 2 reading per document hash and settings, stamped with the reader, the model
   and the prompt's hash, then replayed by every load (ruling 50). Pass 1's reading is never overwritten; both
   stay.
3. **Corrections are proposals.** A correction is applied only by a versioned rule for its profile, after it has
   been measured. The measuring follows the links-rules method: count the corrections by kind, read 20 against
   the document, then version the rule. Until then a correction is counted, not applied.
4. **Identifiers are private.** Every identifier goes to the lane's `*_private` schema, beside the name it
   belongs to. It never appears in a `pub.` view, a landed document, a log, a card or a session's output. A
   register's removals clear a record's identifiers, and a suppression keeps them private, as it already does for
   names. The lane's check fails if any published column carries one.
5. **Cost before running.** Each profile is measured on 20 documents first: extra tokens and seconds per call,
   corrections and enrichments per document, and how many answers were unusable. The full run is costed in reader
   nights and goes to Arthur before it is queued.
6. **Small tranches.** One profile family at a time, each with tests that fail against the old reader and a load
   on real data that can fail.

## What pass 2 asks for, in every profile

**Identifiers**, per person or body named. Each is given as a kind from the list below, the value as printed and
its place in the text:

| Group | Kinds |
| --- | --- |
| Address and place | address, place of residence |
| Age and birth | age, date of birth, year of birth |
| Work | occupation, employer, firm |
| Contact | email, phone |
| Relationship | relationship to another named person (for example "the defendant's brother") |
| Numbers | company number, NZBN, licence or registration number, file or case number naming a person, vehicle registration |
| Anything else | other, with the text's own label |

Emails, phones, company numbers and NZBNs have a fixed format. A pattern match finds them without a model (the
courts lane's tranche 1, now being built), so pass 2 asks for them only where the pattern match finds none.

**Corrections**, checked against the text in every profile:
- a name spelt differently from the printed one;
- an initial expanded, or a macron dropped or added;
- a name the text does not contain (invented);
- a name the text contains that pass 1 missed;
- a person filed as a body or a body as a person;
- a role or organisation the text contradicts;
- a counsel's party wrong;
- a date read wrong;
- a summary that states something the text does not.

## The profiles

The ✱ column marks which pass this is for the profile:
- **2**: pass 1 is a model reading, so pass 2 is a true second pass.
- **P**: pass 1 is the page reader (OCR) only, so pass 2 is the first model reading of the OCR text.
- **R**: pass 1 is rules only. These profiles carry free text worth a model reading.

### Courts (16 profiles)

| Profile | ✱ | Enrich | Correct |
| --- | --- | --- | --- |
| `courts-nzsc-judgment` v3, `courts-nzca-judgment` v3, `courts-nzhc-civil-judgment` v3, `courts-nzhc-criminal-judgment` v3, `courts-nzdc-judgment` v1, `courts-judgment` v2 | 2 | Identifiers for every party, witness and victim named. Charges and the statutes they fall under; sentence, damages, costs and orders, with amounts; the result for each party; the cases cited (held for citation links, ruling 140); the scope of each suppression order (whom it covers, kept privately) | Caption parties against the model's people; counsel's party; the judgment's own date; judges; outcome |
| `courts-maori-court-judgment` v1 | 2 | As for judgments, plus the block, the land, the trust, whānau, hapū and iwi named, and succession lines | As for judgments; macrons |
| `courts-era-determination` v1, `courts-hrrt-decision` v1, `courts-tribunal-decision` v1 | 2 | Identifiers; the employer and the employee or claimant; remedies and their amounts; the body that decided (the nine tribunal codes) | The body against the citation; a decision filed as a submission (Weathertight decisions were) |
| `courts-hearing-transcript` v2 | 2 | Identifiers for each witness; who examined whom | Speaker labels against the people named |
| `courts-counsel-submission` v2 | 2 | Counsel, firms, emails and phones; the party filing | Party and role |
| `courts-case-page` v2, `courts-case-synopsis` v2, `courts-media-release` v2 | 2 | Hearing dates; the result; the court's contact person | Case name and citation against the judgment they link |
| `courts-scanned-document` v1 | P | Everything the judgment rows ask for, from the OCR text | OCR misreadings of names, checked against the caption |

### Electoral Commission returns (14 profiles)

| Profile | ✱ | Enrich | Correct |
| --- | --- | --- | --- |
| `ec-party-donations-return` v4, `ec-party-return-text` v3, `ec-party-return-scan` v5, `ec-party-return-handwritten` v2, `ec-party-return-image-declaration` v4, `ec-party-return-two-column-donor` v1, `ec-donations-protected-return` v1, `ec-candidate-return-scan` v1 | 2 | Each donor's street address (privately); the date of each donation; the party secretary and auditor named | The four hazards in the profiles' notes: a continuation page, a date breakdown read as a schedule, an auditor's stamp over a figure, the two-column donor cell. Re-read any return whose Part A does not reconcile to its printed total |
| `ec-party-expenses-return` v4, `ec-party-loan-return` v2, `ec-party-financial-statements` v2 | 2 | Lenders' and payees' identifiers; loan terms; the auditor | Totals against the printed totals |
| `ec-candidate-expenses-return` v6, `ec-donation-disclosure-20k` v3, `ec-promoter-expenses-return` v2 | P | Candidates', donors' and promoters' identifiers; each line's item, date and amount | Totals against the printed totals |

### Parliament and the executive (4 profiles)

| Profile | ✱ | Enrich | Correct |
| --- | --- | --- | --- |
| `hansard-day` v2 | 2 | Identifiers for people the speakers name (constituents, officials, witnesses); bills and documents referred to; amounts quoted | Names against the MP alias roster (`registers.mp_aliases`); "the Minister" is never turned into a name |
| `mcp-parliament-written-question` v2, `mcp-parliament-wayback-page` v2 | 2 | The agencies asked; dates and amounts; officials named, with their identifiers | The asking member and the answering minister against the record's own fields |
| `beehive-release-body` v1 | 2 | Appointments (person, body, term dates); the press secretary's contact details; programmes and amounts; places | Role and organisation against the text; ministers tagged against ministers named |

### Councils (5 profiles)

| Profile | ✱ | Enrich | Correct |
| --- | --- | --- | --- |
| `council-minutes-text` v1, `council-minutes-scanned` v1 | 2 | Identifiers for attendees and for people a resolution names (applicants, submitters, property addresses), all privately; the mover and seconder; the vote, member by member; amounts; public forum speakers (pass 1 skips them; the public-excluded skip stays) | Attendance against the apologies; declared conflicts against the members present |
| `council-minutes-standard` v1 | P | As above, from the OCR text | As above |
| `interests-register-pdf-text` v1, `interests-register-html-text` v1 (councillors' registers of interests) | 2 | What pass 1 never keeps: real property, addresses, a spouse's or partner's interests, emails and phones. Pass 1 counts these by heading only; pass 2 gathers them privately, with identifiers for each member and each entity they declare | The category typing |

### Organisations' own pages (2 profiles)

| Profile | ✱ | Enrich | Correct |
| --- | --- | --- | --- |
| `captured-web-page` v3, `default` v3 | 2 | Staff and board members, their roles, emails, phones and addresses; the organisation's own numbers | Role and organisation |

### Profiles read by rules today (R): the first model reading

These are free-text documents that pass 1 reads with fixed rules for their structured fields. A model reading gives
them the same identifiers and corrections as everything above.

| Family | Profiles | What the text holds |
| --- | --- | --- |
| Gazette | the 27 `gazette-*` notices: bankruptcy, no asset procedure, creditors, liquidator, receivership, removal, restoration, director prohibition, appointments, celebrants, JPs, mortgagee possession and the rest | Names with addresses and occupations (bankruptcy and creditors' notices print both); liquidators and receivers with their firms and contacts; the companies named |
| Disciplinary and regulatory decisions | `hdc-decision-page`, `hdc-case-study-page`, `lbp-board-decisions-list-page`, `lbp-register-practitioner-page`, `rea-decision-abstract`, `fma-enforcement-case-page`, `fma-warning-page`, `worksafe-court-summary`, `worksafe-enforceable-undertaking`, `oio-decision-summary`, `oio-standing-consent-notification`, `comcom-case-register-entry` | The practitioner, provider, company or person, their identifiers, the finding and the penalty |
| Waitangi Tribunal | `waitangi-tribunal-report` (page reader today) | Claimants, the Wai numbers, hapū and iwi, places, the Crown's witnesses |
| Grants and distributions | the 11 `society-*` PDFs, `lottery-record-of-grants-page`, `dia-class4-grants-csv` | Recipients, their places and amounts |
| Parties | `party-constitution`, `party-website-document`, `party-website-board-page` | Officers, board members and their roles and contacts |
| Te Kāhui Māngai | `tkm-iwi-page`, `tkm-authority-page`, `tkm-other-organisations-page`, `tkm-non-tribal-marae-page` | Contacts, trustees, addresses |

These are not a second pass: their rows come from registers or spreadsheets with fixed columns. Companies, NZBN,
charities, societies, the insolvency register (identifiers already kept, c0540f9), sanctions lists, expenses
workbooks, ICIJ, election results.

## The order proposed

1. The courts judgments (the largest gap; the courts are complete only when this is done).
2. The Gazette's insolvency and creditors' notices.
3. The EC returns' re-reads where Part A does not reconcile.
4. Council minutes and councillor interests.
5. Everything else.

Each step starts with its 20-document measurement and its cost in reader nights.
