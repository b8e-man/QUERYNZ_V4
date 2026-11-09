# Step 9: the connections pane and its base configuration

Built 10 November 2026 by stream G of the step 9 integrator session, on
Arthur's word of the same day (rulings 158 and 159). Measured on
`querynz_v4` through the session reader. Subjects are named by row ref
only. Nothing here is a ruling.

## What was built

- `products/report/connections.toml`: the connection types in plain words,
  their variables, and the base configuration by kind of subject. One
  declared table; `products/report/connections.py` reads it.
- `products/report/connections.py`: the settings (from the page's address,
  on top of the subject's base), what they tell the first stage's web, the
  pruning of the walk after it, a party's own donations, and the hub line
  the base configuration asks for.
- `products/report/stage1.py`: `closure` takes the settings (a role kept by
  `when` and `since`, a type not walked on from, a type off), and
  `hub_lines` says every hub the web met and did not follow on the result,
  the subject's own first when its first hop passes a limit (ruling 158).
- `products/report/build.py`, `memo.py`: the report carries `hub_lines`;
  the memo prints them in a box headed "Hubs not followed", after the
  subject and before the flags, in HTML and text.
- The board's report tab (`products/board/subject_report.py`,
  `static/connections.js`): the pane opens to the left of the report. It
  holds only types, counts and controls. A tick or a dropdown change sends
  the pane's form and the report is rebuilt. The settings are in the
  address (`c=1&c.<type>=on&c.<type>.<variable>=…`), so a filtered report
  reopens as it was. "base configuration" clears them.

## The connection types

Taken from what the walk lists on eleven subjects (the stage-1 depth
subjects, docs/research/step-9-stage1-depth.md), counted by the view each
row comes from: directors 1,253; companies 515; shareholders 485; Hansard
speeches 400; charity officers 108; registered offices 33; charity returns
29; Gazette company notices 22; society officers 21; expenses 18; court
judgment parties 16; MPs' interests 11; charities 10; insolvency
appointments 9; the business-number register's holdings 7 and roles 4;
Gazette appointments 6 and liquidations 4; societies 2; court judgments 2;
a bankruptcy notice 1; a party return 1. By the reach or link rule that
brought them: the first stage's web 870; an officer's other roles 332; a
director beside an officer 263; `member-on-the-day@1` 163; `full-name@1`
102; `organisation-sole-company@3` 23; the register's own keys 1,204.

The reach and the link rule decide how a row is graded (confirmed or near)
and are printed on each row; they are not types. The types are the kinds
of row, declared in `connections.toml`:

| Type | Views | Variables |
| --- | --- | --- |
| director | directors, the business-number register's roles (all are directors bar 7) | roles, ended, from it |
| shareholder | shareholders, the business-number register's holdings | roles, ended, from it |
| society officer, charity officer, general partner | their views | roles, ended, from it |
| party board role | party board roles | roles, ended |
| company | companies and their states, lookups, changes, retirement villages | tick only |
| registered office | company addresses | tick only |
| society, charity or partnership | their views | tick only |
| donation | party and candidate return donors, disclosures and their items | by, top, over |
| loan to a party | party return loans | tick only |
| return or annual return | party and candidate return totals, charity returns, MPs' interests returns | tick only |
| liquidator or receiver appointment | the companies file's appointments, Gazette liquidators and practitioners | from it |
| Gazette notice | the other Gazette views | tick only |
| land title | LINZ titles and owners of record | tick only |
| candidate or member of the House | candidates, members | tick only |
| any other register | each register no type names, by its own name | tick only |

The variables: **roles** (current only; past too, listed (the walk as it
was); past too, followed); **ended** (any time, or within the past 1, 3, 5
or 10 years); **from it** (followed further, or not); **by** (size or
recency); **top** (10, 25, 50, 100, all); **over** (the past 1, 3, 6 or 10
years, or every year held).

A type that is off is neither listed nor followed, and every row reached
through one of its rows leaves with it, counted as set aside in the pane.
The subject's own row and its group's rows always stay.

## The base configuration, measured

Before is the one template as it stood; after is the same template with
the base configuration (no settings in the address). Rows are the rows
listed in the report's sections.

| Subject | Ref | Before | After | Set aside | Hub line on the result |
| --- | --- | ---: | ---: | --- | --- |
| a party (the largest by donations) | `parties:ec-party/1994-12-02/af3607addd1b` | 0 | 10 | 511 donations | 521 donations filed in its returns, 330 over the past 3 years; the top 10 by size listed, no donor followed further |
| a liquidator | `companies:companies/9429031765398/insolvency/3583d4928da8#appointee` | 402 (401 appointments, 1 company) | 1 (its own appointment) | 439 appointments, 1 company | 4,750 appointments held in the companies file; the companies appointed to are not listed and not followed further |
| a trustee company | `companies:companies/9429030020948` | 231 (166 directors, 41 companies, 16 Gazette notices, …) | 6 (its 4 directors, its office, its holder) | 234 directors, 41 companies, 16 Gazette notices, 6 charity officers, 2 appointments, 2 holders, 1 charity | its directors hold 1,986 directorships; not followed further; the measure is a named gap (below) |
| an ordinary director | `companies:companies/9429046000149/director/a3cf284a0720` | 8 | 8 | none | none |
| a director of forty companies | `companies:companies/9429041163580/director/57d947d7f918` | 268 | 268 | none | one director met on 53 organisations |
| a professional director | `companies:companies/9429041091357/director/3ffe2546fd6d` | 933 | 933 | none | the subject itself: 434 organisations; one director met on 422 |
| a company with 47 holders | `companies:companies/9429038055164` | 547 | 547 | none | an organisation of 76 current people; two people on 61 and 200 organisations |

The build times did not move (the party 0.1 s; the trustee company 10 to
11 s; the liquidator 1.6 to 0.9 s).

**The party.** The walk alone lists nothing from a party's register row:
no view's rows sit on a `parties` row by its key in the walk. The base
reads the party's own donations, the rows its returns file under its
party key, a return replaced by an amendment left out (never summed). The
top 10 are donations, one row each, not donors summed: a donor's rows
across returns are joined only by a name, which the first stage never
follows. Large-donation disclosures carry the party's name, not its key,
and are not read for a party subject; nor are its loans.

**The liquidator.** A liquidator's appointment row is walked as an
organisation (the companies file's appointee); its group is every
appointment of the practitioner, 4,750 here. The base lists the subject's
own appointment and counts the rest. Ticking the type again lists them
(402, to the walk's links limit).

**The trustee company.** Recognised by its registered name (trustee,
nominee or custodian, whole words) **and** a current director whose group
holds more than 50 directorships. Without the second test the base would
take in 62,042 registered companies so named, most of them a family
trust's trustee company with its two directors, whose other companies are
the point of a report on it. A family trust's trustee company is followed
as before (checked at run time in the tests).

**Every other subject** builds the same rows as before
(`test_an_ordinary_director_s_report_is_as_before`).

## The variables, measured on the director of forty companies

| Setting | Rows | Set aside | First stage, hop 3 organisations |
| --- | ---: | --- | ---: |
| base | 268 | none | 56 |
| director: not followed further | 227 | 5 companies, 1 charity | 21 |
| director: current only | 256 | 12 directors | 56 |
| director: past too, followed | 299 | none | 59 |
| director: ended in the past year | 268 | none | 56 |
| only director, shareholder and office ticked | 39 | 94 companies, 97 directors, 18 holders, 12 offices, 6 court rows | 54 |

"Ended in the past year" takes nothing out here: the ended roles on this
subject's companies are directors no longer in the latest file, and the
file states no end for them, so no date says they ended before the cut.
A role with no end filed is kept by the date test and taken out only by
"current only".

## A named gap: the significance of a trustee company's directorships

Arthur: "trustee companies we need another tool for measuring the
significance of their directorships. if we had data on the value of their
companies or the deeper connections they have." Not built. Until it is, a
trustee company that is a hub has its people listed and their other
directorships and holdings counted, not followed, and its hub line says
so. What it would need: a figure per company that is not a prior on a
person (a company's own filed accounts or its holdings, where a register
states them), or the count of the subject's own connections that a
directorship reaches. Neither is held for most companies.

## How to see it

The board, report tab: search a name, choose a row; the pane is at the
left of the report. A party: search "national party", the
`parties` row. The address carries the settings, e.g.
`/subject-report?ref=parties%3Aec-party%2F1994-12-02%2Faf3607addd1b&template=one&c=1&c.donation=on&c.donation.top=25&c.donation.order=recency&c.donation.years=6`.
