# credit-1: template 05, business credit and monitoring (step 5.2, use case 5)
branch: session/credit-1 (pushed; a678bac)
session: credit-1
raised: 2026-10-21
claims: products/templates/05-credit/ (template.toml, rules.py, limits.md, checkpoint.list, README.md, tests/); docs/status/credit.md; lessons/a-reports-own-rows-cannot-say-which-files-exist.md; six cards (below)

The seventh use-case template on the subject-report shape: a trade credit
team asks "has anything changed for the companies I am exposed to, and what
stands against this one today". It reads 12 pub views (companies,
directors, shareholders, company_addresses, the Gazette's liquidations,
company notices, liquidators, appointments, prohibitions and bankruptcies,
societies and their officers), each with its licence, attribution and
refresh, and nothing else; depth 2. `company_states` and
`gazette_possessions` are published but unknown to the catalogue, so not
named (carded; a template naming them is refused at load). Seven sections
in a credit analyst's order: the entity and its namesakes apart; its
standing today; what changed (each director, holder and registered office
with the monthly files that show it, the grain stated); the Gazette on the
entity; its people; prohibitions and bankruptcies among them; not held
(PPSR, the Insolvency Register, court judgments, credit-bureau defaults,
the change history before 16 August 2026, the interface until 5.5, and
more, named).

`rules.py` takes `flag`, `items`, `section` and `all_items` from the bound
`contract`; no import of `products.report`; no copy of the common rules. 25
flags. `monthly-changes` lists every change between the monthly files on
the entity (from a person, the person's companies), newest first, dated by
the file that first shows it, "a month and not a day": arrivals and
departures of directors and holders, a holding whose shares changed
(paired), an office move (never the address), the entity first shown or
gone. `recent-adverse-change` (a Gazette insolvency in the last 90 days
red, a removal amber, a director leaving or an office moving to a busy
address in the latest file amber), `officer-churn` (founders not counted),
`insolvency-notices`, `register-events`, `young-entity`,
`people-failed-companies`, `prohibition` and `bankruptcy` (ended or old:
amber). A since-date is not in the shape: carded, the full list shown
dated. Status and name changes unreachable, so no change check clears
(`STATES = False`); `HISTORY = False`.

Checked on querynz_v4: 32 fast tests (fixtures; a mutant check of twelve
deliberate breaks of `rules.py`, each caught; two survived until their
properties were tightened) and 3 slow (real tables through the CLI,
subjects taken at run time); `bin/fast products/templates` green in 28.1 s;
the one-way and reading-limit tests green. The checkpoint: twelve real
subjects, all print as text and HTML, none refused, 0.2 to 4.9 s; six
faults found and fixed (in `limits.md`); two Gazette notices read against
the source file, six fields, no text printed.

Not this branch's: the whole fast tier is red on
`tests/test_generators.py::test_the_committed_records_generate_cleanly`
only because the board and the lessons index are stale with this branch's
six cards and lesson; they are the integrator's to regenerate (the test's
own run rewrote them in this working copy; left unstaged, not committed).
`python -m products.report check` reports one problem not of this branch
(an expense row on a member's report; construction-1's
`confirmed-expense-links-put-every-category-line-in-a-members-report`).

Cards: report lane `the-catalogue-does-not-know-company-states`,
`a-report-takes-no-since-date`, `the-report-keeps-no-watched-list`,
`a-section-cannot-select-the-rows-that-changed-between-files`,
`the-not-held-list-lacks-credit-bureau-and-the-business-number-interface`;
companies lane `the-companies-lane-publishes-no-list-of-its-monthly-files`.

To merge: nothing to install (`qv4-report` serves every template on disk).

## Result (integrator, 2026-10-21 12:37 NZDT)

Merged into main as c9444d8 (merged main first; the folder's README
add/add resolved to the session's). Done at the merge: `qv4-report`
restarted (the template is served from disk); board, lessons index and
queue regenerated; the lesson
`a-reports-own-rows-cannot-say-which-files-exist` indexed (172
characters). No profile, catalogue or job change. Of its six cards, four
are closed by `report-3` (merged next in order: the catalogue knows
`company_states`, a since date, a section's changed-rows filter, the
not-held keys for the credit bureau and the business-number interface);
`the-report-keeps-no-watched-list` goes to step 5.5 (`companies-2` builds
the watch table in the companies lane) and
`the-companies-lane-publishes-no-list-of-its-monthly-files` stands open for
the companies lane.
