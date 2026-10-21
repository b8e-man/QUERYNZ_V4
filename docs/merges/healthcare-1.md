# healthcare-1: template 11, healthcare operator governance (step 5.2, use case 11)
branch: session/healthcare-1 (pushed; 73da5f3)
session: healthcare-1
raised: 2026-10-21
depends on: report-3 (merge it first: this template names report-3's `officers` and `chain` reaches, the `own` filter, `company_states`, `chain_depth` and the not-held keys `tribunals`, `disciplinary`, `employment`, `regulators`, `worksafe`, `company_history`; main's report-2 loader refuses it, and `python -m products.report templates` then fails for every template's load test)
claims: products/templates/11-healthcare/ (template.toml, rules.py, limits.md, checkpoint.list, README.md, tests/); docs/status/healthcare.md; lessons/a-row-that-lists-no-officer-is-not-a-board-with-nobody-on-it.md; four cards (below). docs/board.md was rewritten in the working copy by tests/test_generators.py and is not committed: regenerate it at the merge.

The ninth use-case template on the subject-report shape: an aged-care
investor or a regulator's analyst asks who governs this operator, what its
charity arm files, and where its officers overlap. It reads 13 pub views
(companies, company_states, directors, shareholders, company_addresses,
societies, society_officers, the Gazette's liquidations, liquidators,
company notices, appointments, prohibitions and bankruptcies), each with its
licence, attribution and refresh, and nothing else; depth 2, chain_depth 2.
The charities lane's pub.charities, pub.charity_officers and
pub.charity_returns are named in the brief but not on the database
(charities-3 unmerged) and unknown to the catalogue, so not named; carded.
Seven sections: the entity and its namesakes apart (`own = false`); its
standing and age; its governance (directors, holders of record, the chain;
the charities register named as not held); the charity's returns (not held);
officer overlap (the `officers` reach and the people beside); the Gazette on
the entity, its people and its people's companies; what is not held (the
retirement villages file and its statutory supervisors, HDC decisions,
certification audits, the Ministry's provider registers, the Aged Care
Commissioner, court judgments and the rest).

`rules.py` takes `flag`, `items`, `section` and `all_items` from the bound
`contract`; no import of `products.report`; no copy of the common rules. 21
flags: `officer-overlap` (each officer's other current roles beside the
officer's role on the entity, dated; care-named organisations counted apart,
the entity's own leading name word apart again; hubs never amber; from a
person, a contested group's rows counted near), `disqualified-officer` and
`officer-bankruptcy` (the Gazette on the person or each officer's record,
red only on a current, uncontested, non-hub officer with the notice in
force), `insolvency-notice`, `officer-company-notices` (amber, never red;
never clear while past roles are not held), `entity-status`,
`young-entity`, four charity flags (`charity-arm`, `charity-returns`,
`charity-audit-opinion`, `charity-return-filed`) written against the
charity views by name and blocked while the template does not read them,
six not-held flags and `past-roles` blocked, never clear. A start that lists
no officer (a charitable trust board, a society's companies row, a village
row) blocks every officer check.

Checked on querynz_v4 through a scratch copy of session/report-3 with this
folder: 31 fast tests (fixtures; a mutant check of eighteen deliberate
breaks of `rules.py`, each caught) and 3 slow (real tables through the CLI,
subjects at run time), green; `products/templates` and `products/report`
fast tiers green on that shape (249 tests); the one-way, reading-limit and
generator tests green on this branch.

Checkpoint: twelve real subjects (seven operators, two charitable trust
boards, a society, a village developer in receivership, a director on two
operators' boards), all printed, none refused, no rule broke, 0.1 to 6.7 s.
Three faults found and fixed before the close (officer checks cleared on
zero officers; a contested group dropped the overlap; an operator's own
subsidiaries counted as other operators). One fact read against its source
record (Gazette notice 2026-aa1210).

Cards: `the-report-cannot-reach-the-charities-register` (report lane and
links lane, after charities-3); `the-not-held-list-has-no-key-for-the-health-registers`
(report lane); `the-officers-reach-counts-past-officers-against-its-limit`
(report lane); `the-retirement-villages-file-holds-no-operator-or-supervisor`
(a lane, plan 5.3).

## Result (integrator, 2026-10-21 15:52 NZDT)

Merged into main as 2dddc4f (`merge integrate/healthcare-1: gate green`). Branch `integrate/healthcare-1` from `session/healthcare-1` (73da5f3), main merged; reconcile-1's merge record carried with it; board and lessons index regenerated. Template 11 (healthcare operator governance): 13 views, seven sections, 21 flags; four cards for the report lane (the charities register unreachable from the shape, no not-held key for the health registers, the officers reach's limit, the retirement villages file) go to `fix-report-2`; lesson `a-row-that-lists-no-officer-is-not-a-board-with-nobody-on-it`. Fast tier green in 354.9 s (target 300 missed under load, recorded). Gate green, nothing to load. `qv4-report` restarted 15:53. Branches and the working copy retired.
