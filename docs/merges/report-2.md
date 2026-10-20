# report-2: the subject-report shape, second tranche (step 5.1)
branch: session/report-2 (pushed; 3e58d4d)
session: report-2
raised: 2026-10-20
claims: products/report/ (contract.py new; rules, walk, catalogue, rows, build, memo, server, template, check, templates/subject/, tests, spec.md); docs/status/report.md; lessons/a-presentation-rule-reads-the-reports-own-words-never-a-registers-values.md; cards: eight closed (a-surname-lane-trips-the-home-address-check, a-company-name-with-control-trips-the-cause-check, a-template-cannot-reach-the-flag-contract-or-the-shapes-rules, an-mps-declared-interests-are-not-walked-from-a-person-start, expenses-views-are-not-in-the-report-catalogue, a-gazette-company-notice-date-does-not-say-what-it-dates, the-report-header-repeats-group-rows-a-section-lists, a-donation-row-start-has-no-group), one amended (a-pane-on-the-board-offers-a-report-from-here: the shape's side done, the board half open), one new for links (a-member-row-and-its-interests-return-join-only-by-name)

The eight cards the recruitment session opened for the report lane, each
closed with its check measured on the real published tables through
`python -m products.report check` (green, about 10 s; every checked row is
taken from the tables at run time, never fixed):

1. Rules 3, 4 and 7 read the report's own words. A register's values (a
   company named PEST CONTROL, a donor surnamed Lane, an owners' trust held
   of record) are masked before the search for cause or ownership; an
   address is recognised by its shape (a street number standing alone, or a
   comma, locality and postcode), values included, title and statement read
   apart. The planted faults still refuse (fixtures).
2. `products/report/contract.py`: the flag, the helpers over a built
   report, the common rules (group-standing, hubs-met, replaced-return), the
   presentation rules, the report's address. The loader binds it as the
   name `contract` in every template's rules.py before the file runs, so
   a template under products/templates/ reaches it with no import and
   tests/test_imports_one_way.py is unchanged and green. The builder runs
   the common rules for every template (`common_rules = false` opts out;
   a template flag with the same rule name replaces the common one).
3. The walk: a row of the subject's own group with child rows (an interests
   return) is expanded as the subject's own filing; `mp_expenses` and
   `minister_expenses` are catalogued and reached from a seat or an
   interests return by printed name, near with the reason, totals and
   money outside the total only; a filed row (a donation, a loan, a
   disclosure, an interest) takes the group of the person row a confirmed
   link names and says so in the group line and the group-standing flag.
4. A Gazette notice's date says what it dates ("to be heard 13 July 2018;
   filed 25 May 2018; published 5 July 2018"); a notice with only a
   publication day is dated by it. The header lists no group row a section
   lists. The stable address of a report on a row is
   `/report/<register>:<key>` (`contract.report_url`; the memo's own
   links use it; `/report?ref=` still answers).

Checked on querynz_v4 through the product reader: `python -m
products.report check` green; fast tier `products/report` 26 passed in
25 s with the fill; slow 4 passed; tests/test_imports_one_way.py,
test_reading_limits.py green. The card rows themselves print:
party_returns:d87ba315…/A/10, companies:companies/9429000001458/director/8944b48ae1b8,
mp_interests:036fa950…/p10/l12, companies:companies/9429031200745(/director/9826f5895450).

For the integrator:
1. Restart `qv4-report` after the merge (the running unit serves main's code).
2. The eight closed cards are the recruitment session's files, copied from
   session/recruitment with the closing paragraph added. If recruitment-1
   merges first the merge meets add/add conflicts on those eight: take this
   branch's copies. If this merges first, recruitment-1's copies are the
   open originals: keep this branch's.
3. The new links card and the pane card's board half are for other sessions.
   For the recruitment template (a fix in its folder): drop its own flag,
   subject_hub and replaced_rows copies and its figure-start block, and
   write `flag = contract.flag`.
4. tests/test_generators.py will fail in this working copy until the gate's
   rebuild indexes the lesson and cards, as with report-1.
Lesson: filed (a presentation rule reads the report's own words, never a
register's values; a hard-limit rule reads values and recognises by shape).

## Result (integrator, 2026-10-20 15:53 NZDT)

Merged into main as 8706017 (merged main first; the eight card files
collided with recruitment-1's open copies and this branch's closings were
taken, as asked). Done at the merge: the lesson's rule cut from 265 to
210 characters; records regenerated; the house-2 record rode along;
status. Fast tier and gate green after two slips of the integrator's own
(the rule's length, the status file fourteen bytes over). After the merge
`qv4-report` was restarted on this code so `/report/<register>:<key>`
answers and the recruitment template's views are in its running
catalogue. The two fix sessions asked for: the board's link is built
(`fix/products-board-1`, pushed, integrating next); the recruitment
template's rule copies wait for a slot. The links card
(`a-member-row-and-its-interests-return-join-only-by-name`) is the links
lane's next. The session ran headless from the integrator as Fable, about
45 minutes.
