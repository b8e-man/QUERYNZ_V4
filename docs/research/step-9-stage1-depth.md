# Step 9, stage 1: how deep the confirmed links go

Measured 9 November 2026, on `querynz_v4` through the session reader, by
stream B of the step 9 integrator session. Subjects are named by row ref
only. Nothing here is a ruling.

## The question for Arthur (answered: ruling 158, option B)

**How far should the first report follow confirmed links, and where should
it stop at a hub?** Stage 1 is built with the safest measured option behind
two named constants in `products/report/stage1.py`:

- `HOPS = 3` (ruling 158, Arthur, 10 November: option B): from a person,
  their companies, the people on those companies, and those people's other
  companies; from a company, its people, their other companies, and the
  people on those. Every
  organisation and person at the next hop is counted and said, never listed.
- `HUB_PEOPLE = HUB_ENTITIES = 50`: an organisation with more than 50
  people on it, or a person on more than 50 organisations, is listed and
  flagged but not followed further. The subject's own record is always
  followed.

The options, with what they cost on the ten subjects below, are at the end
(**Options**). Changing either constant is a one-line change; nothing else
moves.

## What the report does today

The diagnostic template (`products/report/templates/diagnostic/`, depth 2,
chain depth 2, every walk bucket) runs `walk.walk`:

1. **The group.** A person row's group (`pub.groups`, built from confirmed
   identity links). A filed row (a donation, a loan) takes the group of the
   person row a confirmed link names. An organisation needs no group.
2. **The links.** Every link touching a member of the group
   (`pub.links`, up to 400): confirmed links are listed confirmed, near links
   listed near with their reason, and each `name-only@1` star is read through
   its centre so every namesake is reached once.
3. **The entities.** The organisations the group's rows sit on (a director
   row's company, an officer row's charity or society), the organisations a
   link reaches, and a company's charity or partnership by business number.
   Up to 40 are listed and 12 expanded.
4. **On each entity.** Its register rows (directors, shareholders, offices,
   states, the business-number register's roles), the notices pointing at it
   (Gazette liquidations and company notices, the companies file's insolvency
   appointments, possessions), and its own links one step. A person on the
   subject's company is listed **near by the design's default** (a connection
   through more than one person), not because a name was matched.
5. **The reaches.** From an organisation start, each current officer is
   followed one step to the officer's other current roles and their
   companies (12 officers, 40 rows each), with the directors beside them on
   those companies (12 a company); the companies at a non-hub registered
   office (near); the holding chain up to two companies (by business number
   confirmed, by a name one company carries near).
6. **By name.** Views no link reaches yet (charity officers, regulators'
   party lists, the business-number register's past roles, the expense
   releases) are searched by the person's name and listed near.

So the diagnostic already mixes the two stages: steps 1 to 5 are reached by
confirmed links and register keys, and steps 2 (near links), 5 (the office,
a holder by name, an officer's near links) and 6 are name matches.

## Which links are confirmed and which near

`pub.links` on 9 November 2026, by grade and rule:

| Rule | Confirmed | Near | What confirms it |
| --- | ---: | ---: | --- |
| `full-name@1` | 1,650,915 | 572,669 | the whole name and a second fact (a middle name, a shared company) |
| `name-and-address@1` | 990,116 | | the name and a registered office both agree |
| `member-on-the-day@1` | 703,171 | 21,533 | a member of the House sitting on the row's day, the only one of the name |
| `owner-full-name@1` | 645,057 | 2,217,361 | a title owner's whole name and a second fact |
| `organisation-sole-company@3` | 285,082 | 157,997 | the one body of the name live on the row's date |
| `official-number@1` | 137,880 | | a business, company or charity number printed on the row |
| `seat-and-window@1` | 23,042 | | a seat and its term |
| `organisation-one-live-company@3` | 20,807 | 29,094 | the one live body of several of the name |
| judgment rules (`judgment-*`) | 1,271 | 11,038 | a judgment's address, title or number |
| `declared-directorship@1`, `source-identifier@1`, `candidate-same-party@1`, `licence-number@1`, `shared-contact@1` | 1,448 | 562 | the fact the rule names |
| `name-only@1` | | 5,948,066 | none: a namesake |
| `organisation-name@1` | | 1,000,316 | none: a body's name only |
| `company-name@1` | | 88,509 | none: a company's name only |
| `filed-name@1`, `candidate-name-form@1`, `member-and-party-donor@1`, `coupled-name@1`, `own-return@1` | | 727 | none |
| `successor-name@1`, `refiled-name@1` | | | grade `related` (965 and 9): two companies, never one |

Stage 1 follows the confirmed grade only, plus the register's own keys
(a director row's company, a company's rows, a notice's register key, a
charity by business number). It never follows a near link, a `related`
link, or a name search; those wait for stage 2.

## How the closure was measured

A script (kept in the session's scratch folder, not in the repository)
walked the confirmed closure breadth first from each subject, one hop at a
time, counting and never printing:

- a row's **group** (all rows confirmed the same person) and its confirmed
  links;
- a row's **entity** (`pub.names.entity_ref`: the company, society, charity
  or partnership it sits on);
- an entity's **people**: every row on it (`entity_ref`).

Three policies were measured:

- **all**: every view's rows, every entity kind;
- **stage-1 policy** (`s_nocap`): only the people views a company or body
  lists as its officers and holders (directors, shareholders, society and
  charity officers, general partners, the business-number register's roles
  and holdings), current roles only, and only companies, societies,
  charities and partnerships as entities. Insolvency practitioners
  (the companies file's appointees) and political parties (a donor row's
  entity) are listed on their entity but never followed: a liquidator's
  other liquidations, or a party's other donors, are not the subject's;
- the stage-1 policy with **hub caps** at 50 and at 20.

A **hop** is one step from a person to an organisation or back. From a
person: hop 1 is their organisations, hop 2 the people on them, hop 3 those
people's other organisations, hop 4 the people on those. From an
organisation: hop 1 its people, hop 2 their other organisations, and so on.

## The subjects

| # | Ref | Shape |
| --- | --- | --- |
| 1 | `companies:companies/9429046000149/director/a3cf284a0720` | a person with one company |
| 2 | `companies:companies/9429041163580/director/57d947d7f918` | a director of forty companies |
| 3 | `companies:companies/9429041091357/director/3ffe2546fd6d` | a professional director, 436 companies |
| 4 | `companies:companies/9429037065836` | a large listed company |
| 5 | `companies:companies/9429030488595` | a public body (a State enterprise) |
| 6 | `charities:charities/CC50271` | a charity with 48 officers |
| 7 | `societies:societies/9429000014458` | an incorporated society |
| 8 | `gazette:gazette/2000-ba1151/person/1` | a Gazette bankruptcy notice |
| 9 | `party_returns:a7e03e19e71030eb088d72b30f8ede131d20c89d2eb31a75148b2c933de2fa45/A/21` | a donor row on a party return |
| 10 | `house:ge-2023/seat/list/green-party/abel-steve` | a member of the House |
| 11 | `companies:companies/9429038055164` | a company with 47 holders of record |

## Hop by hop

New organisations (O) and new people (P) at each hop; "stop" is the size of
the frontier where the measure stopped (past 20,000 organisations).

**Stage-1 policy, no cap**

| # | hop 1 | hop 2 | hop 3 | hop 4 | hop 5 | hop 6 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | O 1 | P 2 | O 3 | P 6 | O 50 | P 851 |
| 2 | O 40 | P 6 | O 63 | P 151 | O 916 | P 4,731 |
| 3 | O 436 | P 41 | O 71 | P 332 | O 533 | P 4,655 |
| 4 | P 7 | O 23 | P 292 | O 866 | P 6,124 | O 16,420 (stop 83,284) |
| 5 | P 8 | O 42 | P 202 | O 1,193 | P 8,382 | O 18,814 (stop 87,106) |
| 6 | P 48 | O 4 | P 5 | O 5 | P 291 | O 811 |
| 7 | P 14 | O 29 | P 173 | O 276 | P 2,046 | O 3,903 (stop 38,333) |
| 8 | (none: the notice's group is two rows and no organisation) | | | | | |
| 9 | O 1 | P 1 | O 81 | P 64 | O 247 | P 1,634 |
| 10 | (none: 1,280 rows in the member's group, no organisation) | | | | | |
| 11 | P 37 | O 93 | P 394 | O 1,161 | P 7,038 | O 16,796 (stop 84,020) |

**With every view and entity (no policy)** the same subjects grow faster
from hop 2: subject 9 reaches 1,970 people at hop 2 (every other donor to
the party), and subjects 2 to 5 reach 50,000 or more organisations by
hop 5, through the insolvency practitioners.

**Stage-1 policy, hubs capped at 50 people / 50 organisations**

| # | hop 1 | hop 2 | hop 3 | hop 4 | hop 5 | hop 6 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | O 1 | P 2 | O 3 | P 6 | O 50 | P 262 |
| 2 | O 40 | P 6 | O 59 | P 148 | O 484 | P 2,728 |
| 3 | O 436 | P 41 | O 64 | P 322 | O 534 | P 3,594 |
| 4 | P 7 | O 23 | P 136 | O 653 | P 2,707 | O 7,354 |
| 5 | P 8 | O 42 | P 202 | O 947 | P 5,376 | O 11,024 |
| 6 | P 48 | O 4 | P 5 | O 5 | P 22 | O 7 |
| 7 | P 14 | O 29 | P 173 | O 217 | P 1,418 | O 2,322 |
| 9 | O 1 | P 1 | (the company has 95 holders: a hub, stopped) | | | |
| 11 | P 37 | O 93 | P 258 | O 607 | P 3,042 | O 6,620 |

**Stage-1 policy, hubs capped at 20**

| # | hop 1 | hop 2 | hop 3 | hop 4 | hop 5 | hop 6 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | O 1 | P 2 | O 3 | P 6 | O 27 | P 67 |
| 2 | O 40 | P 6 | O 11 | P 2 | | |
| 3 | O 436 | P 41 | O 64 | P 159 | O 252 | P 687 |
| 4 | P 7 | O 23 | P 85 | O 297 | P 739 | O 1,965 |
| 5 | P 8 | O 21 | P 71 | O 233 | P 709 | O 1,365 |
| 6 | P 48 | O 4 | P 5 | O 5 | P 2 | O 2 |
| 7 | P 14 | O 29 | P 49 | O 17 | P 72 | O 134 |
| 11 | P 37 | O 93 | P 130 | O 284 | P 647 | O 1,337 |

Time to measure: hops 1 and 2 under a second each; hops 3 and 4 up to
7 seconds; hops 5 and 6 up to 46 seconds and 400,000 rows read. A report
would add the cost of reading each listed row whole.

## Where the hubs are

The closure is small to hop 2 and then swells at a few kinds of hub. The
largest met (people on an organisation, or organisations of one person),
by ref:

- **Insolvency practitioners.** A liquidator's group sits on up to 4,674
  companies (`companies:companies/9429031765398/insolvency/3583d4928da8#appointee`,
  `companies:companies/9429030007352/insolvency/d3ecd9c35bdf#appointee`). With
  every view followed, these carry subjects 2 to 5 past 50,000
  organisations. The stage-1 policy lists an appointment on its company and
  never follows the practitioner.
- **Political parties.** A donor row's entity is its party: 2,229 rows on
  one party (`parties:The New Zealand National Party`), 745 and 603 on two
  others. Never followed: another donor to the same party is not the
  subject's connection.
- **Trustee and nominee companies' directors.** Two directors of one
  trustee company (`companies:companies/9429030020948/director/5709e6db4fbc`,
  `…/0e785911f0cd`) sit on 647 and 643 organisations; another
  (`companies:companies/9429030030480/director/a27c384cae02`) on 422; subject
  3 is a professional director of 436.
- **Charity officers on hundreds of charities.** Groups of charity officer
  rows on 250 to 641 charities (`charities:charities/officers/1739743`,
  `…/1360539`, `…/1281138`): a trust corporation or an umbrella's officer
  registered on each member charity.
- **Investment schemes and wide holdings.** Forestry and investment
  schemes' general-partner companies with 286 to 369 holders of record
  (`companies:companies/9429039407955`, `…/9429030823693`,
  `…/9429030824027`).
- **Removed companies keep their rows.** Removed companies with 214 to 351
  rows left on them (`companies:companies/9429037944087`,
  `…/9429036192809`, `…/9429037877729`).
- **A building practitioner** whose group holds 258 organisations
  (`building_practitioners:building_practitioners/lbp/BP102923`).

The State enterprise (subject 5) is itself no hub at hop 1 (8 people), but
its directors are public figures on many boards, and by hop 4 it reaches
more organisations than any other subject.

## Options

| Option | What is listed | Largest measured (organisations / people listed) | Cost |
| --- | --- | --- | --- |
| **A. Two hops, hubs at 50** (built) | the subject's organisations and the people on them; or a company's people and their other organisations | 436 organisations (subject 3's own) and 48 people (subject 6's officers); every other subject under 100 organisations | under a second to measure; the next hop counted, not listed; a report lists at most 400 of the web's rows (`LIST_ROWS`), the rest counted |
| **B. Three hops, hubs at 50** | A, and the people on those organisations (from a company), or their other organisations (from a person) | 436 organisations and 202 people at hop 3 (subjects 3 and 5); subject 11, 258 people | about a second to measure; a report of several hundred rows |
| **C. Four hops, hubs at 20** | B, and one more step | 297 organisations and 739 people at hop 4 (subject 4); 233 and 709 (subject 5) | a few seconds; a report of a thousand rows or more for a company |
| D. Four or more hops, hubs at 50 | | 947 to 1,193 organisations at hop 4 and 5,000 to 8,000 people at hop 5 | not listable in one report |

Under every option the counts beyond the last hop are carried on the
report, and the walk-coverage check fires when anything was counted and not
listed, so a cut is never silent.

A's cost is low enough that B is the natural next step if Arthur wants the
co-officers' other companies in the first report; C and D are where the
hubs, not the subject, decide what the report holds.

## What the built first stage gives

`products/report/stage1.py`, run through the `one` template on the same
subjects (9 November 2026, after the build). The built stage is stricter
than the measure in one way: a role is current in **every** view (a society
or charity officer with an end filed, a business-number register role that
ended), where the measure checked directors and holders only. So some hops
are smaller (subject 7's officers 7, not 14; subject 3's people 16, not 41).

| # | hop 1 | hop 2 | next hop, counted | hubs not followed | rows added | near links set aside | build |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | O 1 | P 2 | O 3 | 0 | 0 | 1 | under 1 s |
| 2 | O 40 | P 6 | O 56 | 1 | 66 | 42 | 6 s |
| 3 | O 434 | P 16 | O 30 | 1 | 400 (419 counted past the limit) | 49 | 6 s |
| 4 | P 7 | O 20 | P 120 | 1 | 0 | 35 | 4 s |
| 5 | P 8 | O 38 | P 146 | 0 | 0 | 140 | 6 s |
| 6 | P 7 | O 0 | none | 0 | 0 | 523 | 1 s |
| 7 | P 7 | O 24 | P 84 | 0 | 8 | 45 | 2 s |
| 8 | none | | | 0 | 0 | 13 | under 1 s |
| 9 | O 1 | P 1 | none | 1 (the party) | 0 | 0 | 1 s |
| 10 | none | | | 0 | 0 | 0 | 1 s |
| 11 | P 37 | O 87 | P 344 | 1 | 62 | 48 | 4 s |

"Rows added" are the web's rows the diagnostic walk had not already listed.
The charity (subject 6) reaches no organisation at hop 2 in the built
stage: no link joins the Charities Register's officers to any other row
yet, so its officers are followed only where a confirmed group holds them.
None of the reports built breaks a presentation rule, and none lists a row
reached by a name or a near link (checked in `tests/test_stage1.py`).
