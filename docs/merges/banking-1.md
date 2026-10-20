# banking-1: template 03, banking director history (step 5.2, use case 3)
branch: session/banking-1 (pushed; 8d76d6b)
session: banking-1
raised: 2026-10-20
claims: products/templates/03-banking/ (template.toml, rules.py, limits.md, checkpoint.list, README.md, tests/); docs/status/banking.md; lessons/a-register-snapshot-of-current-roles-cannot-clear-a-history.md, lessons/read-a-source-notice-for-its-fields-never-print-its-text.md; six cards (below)

The third use-case template on the subject-report shape: a credit analyst
asks "every company this person has touched, and how each ended". It reads
19 pub views, each with its licence, attribution and refresh, and nothing
else; depth 2, so the people beside the person are listed, near. Seven
sections in the analyst's order: namesakes apart; every directorship and
shareholding the file lists, with dates; how each company ended (its
register status, and beneath it the Gazette's liquidations, receiverships,
administrations, winding-up applications, creditors' notices, removals,
restorations, overseas-company cessations under s 341, society
dissolutions and partnership deregistrations, each dated); prohibitions and
bankruptcies on the person; the people they sat beside and the companies
those people share; charity, society and political money; what is not
held, the Personal Property Securities Register named.

`rules.py` takes `flag`, `items`, `section` and `all_items` from the bound
`contract` as recruitment-2 does; no import of `products.report`; the
builder's three common rules run and no copy is carried. 20 flags, each
branching on the start (person, company, other); from a company the people
checks block and tell the reader to start from each person. Dates side by
side, hubs flagged, a nominee or company holder shown as a holder of
record.

**The finding that shapes it:** the companies file holds current roles
only. None of 1,185,805 director rows carries an end date, and the
1,066,680 removed companies keep 4,888 directors between them. A director
history from it cannot clear, so `HISTORY = False` turns every clear over a
person's companies into "blocked" with the reason, and the flag `past-roles`
says it on every report. One setting flips it when a view publishes past
roles; the tests cover both settings.

Checked on querynz_v4: the template's tests 32 fast (fixtures; a mutant
check of ten deliberate breaks of `rules.py`, each caught by the property
aimed at it) and 3 slow (real tables through the CLI, subjects taken at run
time); `bin/fast products/templates` green in 27.5 s; `python -m
products.report check` green; tests/test_imports_one_way.py green.
Checkpoint: 12 real subjects (`checkpoint.list`), all print, none refused,
0.3 to 8.4 s; three facts read against the Gazette source file.

Whole-repository `bin/fast --no-fill`: RED only on tests/test_generators.py
(the six new cards and two lessons are not yet in the generated
docs/board.md and lessons index; the run rewrote docs/board.md in this
working copy, uncommitted, which the fence will not let me restore), and
302.7 s against the 300 s target. The gate's rebuild makes them current.

**Cards.** Companies lane: `the-companies-file-holds-no-past-directorships`.
Report lane: `the-walk-reads-twelve-companies-and-lists-forty`,
`a-contested-groups-near-row-can-make-the-start-rows-own-company-near`,
`a-crown-entity-holder-is-not-flagged-as-the-crown`,
`group-standing-calls-a-filed-row-with-no-group-an-organisation`,
`a-section-cannot-put-current-roles-first`. The existing
`a-company-start-does-not-follow-its-officers` covers use case 3 too.

Nothing to install: `qv4-report` serves every template on disk.

## Result (integrator, 2026-10-21 07:12 NZDT)

Merged to main at 895e08b, gate green on the third run. The first two runs
failed on the disclosures lane's frozen-site test, not on this branch: the
frozen site's 06:19 release carries a new ACT New Zealand declaration
($22,374.74, received by the Commission 19 October) that the lane's one-off
capture predates; carded for disclosures
(`act-new-zealand-2026-a-declaration-filed-after-the-lane-s-capture`), and
the equal-years floor lowered 15 to 14 with the card named. That release
is also step 1.4's positive half observed. A lesson's rule was cut to the
limit. `qv4-report` restarted so it serves template 03. The session's
hard-limit 11 slip (a notice's text with a home address printed into its
own transcript once) is reported to Arthur. Worktree and branch retired.
