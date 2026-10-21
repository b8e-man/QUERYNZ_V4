# fix-products-templates-1: healthcare, property and ownership read the new reaches (an officer's near links, the companies above) and name their not-held keys
branch: fix/products-templates-1 (pushed; 4c71029)
session: fix-products-templates-1 (fix, scope products/templates/)
raised: 2026-10-22
claims: products/templates/ (11-healthcare, 12-property, 13-ownership: template.toml, rules.py, limits.md, README.md, tests/ fixture and real); docs/status/templates-fix.md; lessons/a-rule-keyed-on-through-adds-a-namesakes-rows-once-the-officers-reach-follows-near-links.md; cards: three closed (the-healthcare-, the-property-, the-ownership-template-can-now-read-the-charities-register-and-the-reaches)

One commit per template, each with a fixture test that fails on HEAD's
rules.py and template.toml (checked) and new mutants:

1. **Healthcare** (f61dbbb). The five health keys in the not-held section
   (`retirement_villages` on standing too); the five blocked flags name each
   register as the catalogue does. A row an officer's near link reaches is
   counted apart in `officer-overlap` and `officer-company-notices` (info
   alone, never amber, no clear while one stands); a prohibition reached by
   one is never red. `chain` in the Gazette section; `insolvency-notices`
   sets a notice above beside the entity's own.
2. **Property** (511263b). `oio`, `building_consents`, `rea` named; the
   three flags point at them. A director's near-linked companies are their
   own principal, a namesake's, amber at most: serial-pattern,
   earlier-failure, insolvency-notices, possession and the people checks
   count them apart; history-reach fires on them. `directors` in the chain
   section, `chain` in the Gazette and possessions sections; holding-chain
   counts what is listed above.
3. **Ownership** (a6b31cc). `chain_depth = 2` and a chain section (companies,
   shareholders, directors, the Gazette company views); holding-chain names
   the companies reached, how, the holders not followed and the cut;
   insolvency-notices sets a notice above beside the company's own; the
   holder-name checks read the holders up the chain.

No word of cause in any new text (the CAUSE properties run on them).
Licence, attribution and refresh unchanged: no new view is read.

Checkpoints re-rendered before (a clean copy of 2748790) and after, all
36 subjects; none refused; each limits.md records it. Flags that moved:
property's serial-pattern on GORING and KERVIL fired amber -> blocked (it
had added the director's namesake PJO liquidation to the entity's own
failure: the bug the lesson names); ownership's overseas-holders on Foley
Wines blocked -> fired amber (an LLC and a Pty one up), custodial-holders
and holder-hubs on Seasonal Solutions to fired info (trustee holders one
up). Healthcare: no flag moved.

Checked: `bin/fast products/templates` green (42.3 s); the three templates'
slow tests green; `python -m products.report check` green (64 s);
`tests/test_imports_one_way.py`, `tests/test_reading_limits.py` green.

For the integrator:
1. Three slow assertions were amended in this branch, within scope:
   healthcare's and property's not-held lines (now leading with the new
   keys) and ownership's chain text.
2. No `qv4-report` restart needed: no form change, and templates load per
   render.
3. tests/test_generators.py will fail in the working copy until the gate's
   rebuild indexes the lesson and the cards, as before.
Lesson: filed.

## Result (integrator, 2026-10-22 02:56 NZDT)

Merged into main as 1e98db0 (`merge integrate/fix-products-templates-1: gate green`). Branch `integrate/fix-products-templates-1` from `fix/products-templates-1` (4c71029), main merged. Healthcare, property and ownership read the new reaches (an officer's near links; for ownership the companies above) and name their not-held keys, one commit per template with a fixture test that fails without it, the checkpoints re-rendered and the changes in each `limits.md`; the three cards from fix-report-2 closed by the session; the lesson filed. Fast tier green in 534.1 s. Gate green, nothing to load. `qv4-report` restarted. Branches and the working copy retired.
