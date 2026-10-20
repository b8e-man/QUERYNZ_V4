# agriculture-1: template 04, the agriculture counterparty (step 5.2, use case 4)
branch: session/agriculture (pushed; 670c2ac)
session: agriculture
raised: 2026-10-20
claims: products/templates/04-agriculture/ (template.toml, rules.py, limits.md, README.md, tests/); docs/status/agriculture.md; lessons/a-company-start-lists-people-the-walk-never-follows.md; five cards (below)

The second use-case template on the subject-report shape. It reads 19 pub
views, each with its licence, attribution and refresh, and nothing else. Its
seven sections run in the order a credit manager reads them: namesakes set
apart; officers and holders of record with their dates; Gazette
receiverships, liquidations, winding-up applications, administrations,
creditors' notices and removals, plus bankruptcies and prohibitions; the
people's other companies and what became of them; charity and society
roles; political money; what is not held. It has 19 flags standing for the
old estate's four company rules where the held registers support them:
register-status for partnership-dissolved; entity- and
officer-group-insolvency for group-receivership; practitioner-repeat and
mpi-coverage blocked. Every rule branches on what kind of row the report
starts from. From a company, the five checks that read its people are
blocked, never clear, and the reader is told to start a report from each
person listed. A removal is not an insolvency. A nominee, trustee or company
holder is flagged and never called an owner. Dates sit side by side.

Like recruitment, `rules.py` carries its own flag contract, because the
report lane's contract (report-2) is not on main yet. It imports nothing of
`products.report`.

Checked on querynz_v4: `bin/fast products/templates` green in 25.3 s (21
tests of this template, plus a mutant check: letting the prohibition rule
clear from a company start is caught); slow 4 passed (real tables through
the command line, subjects taken at run time); `python -m products.report
check` green; tests/test_imports_one_way.py green. Checkpoint: 12 real
subjects, all print, none refused, 0.1 to 1.3 s each. Three facts were read
against the Gazette source file. `limits.md` is the known-limits page.

Whole-repository `bin/fast`: RED only on tests/test_generators.py, because
the new cards and lesson are not yet in the generated docs/board.md and
lessons/INDEX.md (its run rewrote docs/board.md in this working copy,
uncommitted). The gate's rebuild makes them current.

Cards. For the report lane: a-company-start-does-not-follow-its-officers
(the main one: use case 4's question is the people behind the company),
insolvency-practitioners-are-not-reached-from-a-notice,
not-held-lacks-unincorporated-entities-and-mpi. For links:
a-companys-same-name-companies-are-not-set-apart. For companies:
a-company-holder-carries-no-business-number.

For the integrator: nothing to install; `qv4-report` serves every template
on disk. The memos were read in samples only; no home address or
suppressed name was printed.

## Result (integrator, 2026-10-20 18:32 NZDT)

Merged to main at b4d74bc, gate green. The lesson's rule was cut to the
limit (236 characters). `qv4-report` restarted so it serves template 04.
Follow-ups for the template's next session: take the flag and common rules
from the bound `contract` as recruitment-2 does; gazette-4's three new
notice kinds (overseas company ceasing, restoration, society dissolution)
now reach its "removal or restoration" wording. Worktree and branch retired.
