# construction-1: template 07, subcontractor vetting and phoenix detection (step 5.2, use case 7)
branch: session/construction-1 (pushed; 6ad1f44)
session: construction-1
raised: 2026-10-21
claims: products/templates/07-construction/ (template.toml, rules.py, limits.md, checkpoint.list, README.md, tests/); docs/status/construction.md; lessons/an-event-can-rewrite-the-value-you-compare-across-it.md; seven cards (below)

The sixth use-case template on the subject-report shape: a head
contractor's procurement lead asks "is this the failed firm again under a
new name". It reads 12 pub views (companies, directors, shareholders,
company_addresses, the Gazette's liquidations, liquidators, company
notices, appointments, prohibitions and bankruptcies, societies and their
officers), each with its licence, attribution and refresh, and nothing
else; depth 2. `company_states` and `gazette_possessions` are published but
unknown to the catalogue, so not named (the open
`the-catalogue-does-not-know-gazette-possessions`). Eight sections in a
procurement lead's order: the entity and its namesakes apart; officers and
holders of record, dated; the phoenix section (every company reached, with
its status and start); registered offices; prohibitions and bankruptcies;
the people beside them and their society roles; the Gazette on the entity
and the companies above; not held (the building practitioners register,
the Official Assignee's Insolvency Register, court judgments, employment
determinations, the change history before 16 August 2026, named).

`rules.py` takes `flag`, `items`, `section` and `all_items` from the bound
`contract`; no import of `products.report`; the builder's common rules run
and no copy is carried. 26 flags. `phoenix-signature` sets each failure,
dated from its Gazette notice (an appointment where stated, else the day
published), beside each going company's start with the window stated (365
days either side, `WINDOW_DAYS`); raised only on a shared person (from a
person) or a shared registered office from before the failure (from a
company, with a same-name company), never on a name alone; a hub, a near
link or a removal is never red. `same-name-failed` shows the name case,
info or amber. Each rule branches on the start; from a company the people
checks block. `HISTORY = False`.

Checked on querynz_v4: 32 fast tests (fixtures; a mutant check of fourteen
deliberate breaks of `rules.py`, each caught by the property written for
it) and 4 slow (real tables through the CLI, subjects taken at run time,
12.6 s); `bin/fast products/templates` green in 28.3 s; the one-way and
reading-limit tests green. `python -m products.report check` reports one
problem that is not this branch's (no file in `products/report/` changed):
a member's report lists confirmed expense category lines since the 09:25
links reload (carded). Checkpoint: twelve real subjects
(`checkpoint.list`); 11 print, 1 refused by the shape (a company named like
an address, carded), none broke a rule, 0.3 to 6.0 s; three phoenix cases
in construction trades raised red; three facts read against the Gazette
source file, fields only (`limits.md`).

Cards: report lane
`a-company-named-like-a-street-address-refuses-every-report-that-meets-it`,
`the-walk-counts-the-companies-at-an-office-and-does-not-list-them`,
`a-section-cannot-set-the-starts-own-rows-apart-from-its-peoples`,
`the-not-held-list-lacks-employment-determinations-and-the-change-history`,
`confirmed-expense-links-put-every-category-line-in-a-members-report`;
companies lane `a-liquidated-companys-office-before-its-liquidation-is-not-published`;
templates 2, 3, 4, 13 `four-templates-still-say-no-link-reaches-a-bankruptcy`.

Default taken: the window, 365 days either side of the failure (the old
MC-C1 used 90 after); one setting. Nothing to install: `qv4-report` serves
every template on disk. The branch is based on 5339394; main has since
taken gazette-6, which touches no file here.

## Result (integrator, 2026-10-21 10:58 NZDT)

Merged into main as 987782e (merged main first). Done at the merge:
`qv4-report` restarted (the template is served from disk); board, lessons
index and queue regenerated; the lesson
`an-event-can-rewrite-the-value-you-compare-across-it` indexed (216
characters). No profile, catalogue or job change. The seven cards stand
open for their lanes: six for the report shape (the office count, a
section's own rows, two not-held labels, the expense links, the
street-named company) and go to the shape's third tranche (`report-3`,
launched 21 October 11:00); one for the companies lane (a liquidated
company's office before its liquidation); `four-templates-still-say-no-
link-reaches-a-bankruptcy` for templates 2, 3, 4 and 13. The default
window of 365 days either side of the failure stands unless Arthur rules.
