# legal-1: template 02, legal counterparty and conflict check (step 5.2, use case 2)
branch: session/legal-1 (pushed; 3f4e6e2)
session: legal-1
raised: 2026-10-21
claims: products/templates/02-legal/ (template.toml, rules.py, limits.md, checkpoint.list, README.md, tests/); docs/status/legal.md; lessons/probe-every-field-of-a-source-record-before-calling-a-join-wrong.md; six cards (below)

The fourth use-case template on the subject-report shape: a law firm asks,
before acting, "who is this counterparty, who stands on its register, and
does anyone here already act for or against them". It reads 20 pub views,
each with its licence, attribution and refresh, and nothing else; depth 2,
so the people on the person's companies are listed, near. Six sections in
a conflicts clerk's order: the party and its namesakes apart; officers and
holders of record with dates; the conflict web (each company the person
sits on, with its status and dates, and the other directors and holders on
it, near); the Gazette on the company and its people (liquidations,
receiverships, administrations, winding-up applications, creditors'
notices, deeds of company arrangement, removals, dissolutions,
restorations, amalgamations, the Registrar's rectifications, transfers out;
prohibitions; a practitioner's own liquidator appointments); charity,
society and political money; what is not held, court judgments and
disciplinary findings named.

`rules.py` takes `flag`, `items`, `section` and `all_items` from the bound
`contract`; no import of `products.report`; the builder's three common rules
run and no copy is carried. 27 flags standing for the old legal checks
MC-L1 to MC-L5 and the person and company rules, each branching on the
start; from a company the people checks block; a donation that takes a
person's group is read as that person. `client-overlap` is always blocked:
the shape takes one row, so the firm's client list is not an input, and no
flag ever says there is no conflict (a property and a mutant hold this).
`HISTORY = False` as in banking: no check over a person's companies clears.

Checked on querynz_v4: 36 fast tests (fixtures; a mutant check of twelve
deliberate breaks of `rules.py`, each caught) and 3 slow (real tables
through the CLI, subjects taken at run time, 3.8 s); `bin/fast
products/templates` green in 28.2 s; `python -m products.report check`
green; the one-way test and the root suite green. Checkpoint: twelve real
subjects (`checkpoint.list`), all print, none refused, 0.3 to 6.1 s; three
facts read against the Gazette source file, fields only (`limits.md`).

Cards: report lane `a-template-cannot-take-the-firms-client-list`,
`the-catalogue-does-not-know-gazette-possessions`,
`the-not-held-list-lacks-disciplinary-findings-and-tribunals`,
`an-amalgamation-notices-other-companies-are-not-reached`,
`a-liquidator-row-does-not-name-its-company`; gazette lane
`an-amalgamation-row-carries-no-effective-date`.

Note for the gate: running the root suite in the working copy rewrites
`docs/board.md` and `lessons/INDEX.md` (generated; the hook refuses this
session touching them), so they are left unstaged and not in the branch.
Regenerate at the merge for the new lesson and the six cards. Nothing to
install: `qv4-report` serves every template on disk.

## Result (integrator, 2026-10-21 09:45 NZDT)

Merged into main as a4843c8 (merged main first). Done at the merge: ruling
63's text corrected in `docs/decisions/rulings.md` (step 7 held to the end,
step 6 in its place); the carrier card for the twin cable
(`the-primary-loses-its-own-database-address-when-the-twin-cable-is-out`)
with the node2 drop-in recorded; board, lessons index and queue
regenerated; `qv4-report` restarted. Template 02: 20 views, 27 flags, 36
fast and 3 slow tests, 12 checkpoint subjects; the report-lane cards
(possessions table unknown to the report, no not-held entry for
disciplinary findings, amalgamation companies unreachable, liquidator row
without its company) and the gazette card (amalgamation effective date
unread) stand open for their lanes. The gate ran three times: the first
during the links reload (statement timeouts in the real-data renders), the
second collided with a stray copy of itself; the third was green with
nothing else running. Next in step 5.2's order: use case 7
(`construction-1`), launched after this merge.
