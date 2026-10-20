# gazette-4: the pane for gazette-3's four views; three more sections read; the unread sections by use case

Branch `session/gazette-4` (7 commits on 15ba016). Scope `registers/gazette/`,
plus this session's own card, lesson, status and queue files.

## What it claims

**1. Pane (card `the-gazette-pane-spec-omits-the-four-tables-of-gazette-3`, closed).**
`registers/gazette/pane.md` has a paragraph each for `pub.gazette_company_notices`,
`gazette_practitioners`, `gazette_bankruptcies` and `gazette_appointments`, written
from the views and measured on every row (kinds and actions, `event_basis`, the
48,393 rows with no event day, the 72 with a day and no basis, practitioners'
roles and `named_in_body`, bankruptcy kinds and withheld rows, who appointed).

`products/board/catalogue.py` read against them (not edited; it is yours):

- `gazette_notices` joins only `gazette_celebrants`. A notice's pane does not
  list its prohibitions, liquidations, company notices, bankruptcies or
  appointments, though each of those rows links up to its notice.
- `gazette_company_notices` shows `event_on` as a bare "event on" with "date
  basis" as a separate field. The pane (and the report, since report-2) says
  what the date is ("to be heard 13 July 2018"). The board does not.
- `gazette_liquidations` has no field for `register_key` or `register_match`,
  though the view publishes both and `gazette_company_notices` shows them.
- `register_key` is shown as text on both views, not as a link to the
  companies pane. `Join` reaches only the same register, so this may need a
  cross-register link in the board.
- The company-notice `note` says nothing of restorations. Add "a
  restoration's applicant is never held or shown" if you want the note to
  match the pane.
- `gazette_practitioners`, `gazette_bankruptcies` and `gazette_appointments`
  match their paragraphs.

**2. The parties lane reads this lane's `au` notices** (parties-2, merged 20
October, 137 from `pub.gazette_notices`). Recorded in `docs/status/gazette.md`.

**3. Three new kinds in `gazette.company_notices`.** Each has its own profile
in `registers/gazette/profile-proposed.jsonl` (version 1; please append all
three to the ledger). Each was measured on every notice: by the reader over
the export, then by a full load of all 207,133 notices through this branch
into `scratch_gazette_4_full` in `querynz_v4_sample` (92 s). The register
rows came from `querynz_v4`'s `pub.companies` through the read-only login,
because the sample database has none. `python -m registers.gazette.check`
exits 0 on it.

| Kind | Section | Profile | Notices read | Rows | Joined | Floor |
| --- | --- | --- | --- | --- | --- | --- |
| overseas company | `cb` | `gazette-overseas-company-ceasing` | 2,601 of 2,607 | 2,885 | 95.4% | 92% |
| restoration | `ot`, titled so | `gazette-restoration-notice` | 868 of 888 | 31,515 | 93.1% | 90% |
| dissolution | `is`, `ct`, titled so | `gazette-society-dissolution` | 1,697 of 1,813 | 33,749 | 98.7% (90.2% of numbers agree by name) | 95%, name 85% |

- A restoration list prints each applicant's name and address, often a
  home. The reader takes only the company before each "Applicant:" and never
  reads past it. A unit test asserts that no part of the applicant reaches
  the reading.
- `register.py`: `Index.match` takes the registers a printed number may
  belong to. A society's number is looked up among societies and trust
  boards, never companies. Existing kinds behave as before: every
  pre-existing format count and join figure on the full load equals the
  published one.
- `check.py`: one kind may span several sections (`codes`). A section that
  holds other notices too asks the profile only for its titled notices
  (`TITLED`). There is also a name-agreement floor for dissolutions
  (`COMPANY_NUMBER_FLOOR`).
- `tables.sql`: the `kind` check allows the three new kinds. `publish.sql`
  is unchanged; no new view and no new column.
- Unread notices fell from 86,173 to 80,865.

**For the template sessions:** agriculture's `register-removals` flag reads
every non-insolvency company notice as "a removal or restoration notice".
The three new kinds now reach it: an overseas company leaving New Zealand
and a society's dissolution will be described that way. The words may want
a case per kind.

## The unread sections, by use case (recruitment 08, agriculture 04, banking 03, legal 02)

Counts are notices still "not read" on the full load.

| Section | What it is | Unread | Wanted by | Done |
| --- | --- | --- | --- | --- |
| `go` | Vehicle confiscation orders (Sentencing Act; each names a convicted person) | 6,213 | 02 at most | Queue: `may-the-gazette-lane-read-notices-that-name-people-for-conduct` |
| `go` | Education licence cancellations, medicine consents, school integration agreements, marriage approvals, JPs (home addresses), other | ~23,900 | none of the four | Left |
| `ln` | Land taken, roads, reserves | 25,679 | 12 property | Left |
| `lt` | Land Transfer Act lost titles (owners, properties) | 2,637 | 12 property | Left |
| `au` | Aviation, electricity, transport determinations and exemptions | 7,165 | none; the parties lane reads its 137 party-register notices | Left |
| `gn` | Mortgagee entries into possession of land and goods | 2,953 | 03, 04 | Card `mortgagee-entries-into-possession-in-the-gazette-are-unread` |
| `gn` | Disciplinary tribunals | 96 | 08, 02 | Queue (above) |
| `gn` | Unclaimed property, claims, other | ~650 | none | Left |
| `ot` | Rectifications ~487, amalgamations ~250, transfers out ~70, deeds of arrangement 19 | 1,258 | 03, 02 | Card `amalgamations-and-the-registrar-s-rectifications-under-ot-are-unread` |
| `ct`, `is` | Charitable schemes, surplus-asset directions, financial statements | 384 | none | Left |
| `pn` | Special partnerships; law and accounting firms' partners | 555 | 02 at a stretch | Left |
| `vr`, `ps` | Ministers' resignations, the "Honourable" title, vacancies | 659 | the house lane | Left |
| `fs` | Friendly societies and credit unions | 109 | 03 at a stretch | Left |
| `gs`, `sl`, `cu`, `rs`, `dl`, `vw`, `pb` | Standards, secondary legislation, tariffs, regulation lists, fisheries bylaws, warrants, private bills | 8,628 | none | Left |

Two cards are left alone, as briefed:
`appointment-notices-whose-appointees-run-together-are-unread` and
`annulled-bankrupts-the-reader-cannot-name-stay-published-on-earlier-rows`.

## Notes for the gate

- The fast tier is green for `registers/gazette` (51 s). The whole repository
  is red on one test only: `lessons/INDEX.md` is stale. It is generated and
  yours to rebuild (new lesson
  `a-join-by-number-hides-a-broken-name-read-the-agreement-share`).
  `docs/board.md` will need the new cards.
- The gate's load needs `pub.companies` and `pub.members` published first, as
  before. Nothing here fetches, and no job is added.
- There are two new scratch schemas in `querynz_v4_sample`,
  `scratch_gazette_4_full` and `scratch_gazette_4_full_private` (the second
  holds bankruptcy, prohibition and celebrant addresses, owner-only). Drop
  them when you like.
- No address, and no applicant of a restoration, was printed into the
  session or written to any file. Samples were looked at through a
  vocabulary mask.

## Result (integrator, 2026-10-20 19:48 NZDT)

Merged to main at fa0c50d, gate green (207,133 notices loaded in 168 s).
The three profiles are in the ledger (64 to 67), the proposal retired. No
new view, so the board catalogue is unchanged by this merge; the five
catalogue mismatches the pane paragraphs found (the notice pane's joins to
its five tables, the company notice's date basis in words, the
liquidation view's register fields, the register match as a link, the
restoration note) are the integrator's next board commit. The queue item on
notices that name people for their conduct waits on Arthur (default no).
gazette-5 launched 19:05 on the two cards. Worktree and branch retired.
