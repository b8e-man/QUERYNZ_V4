# property-1: template 12, property developer due diligence (step 5.2)
branch: session/property-1 (pushed; edaa35a)
session: property-1
raised: 2026-10-21
claims: products/templates/12-property/ (template.toml, rules.py, limits.md, checkpoint.list, README.md, tests/test_property_template.py, tests/test_property_real.py); docs/status/property.md; lessons/an-intention-to-remove-is-not-a-removal.md; cards opened: the-not-held-list-has-no-key-for-the-property-registers, the-officers-reach-does-not-list-an-officers-near-links, the-chain-reach-reads-nothing-on-the-companies-above, the-construction-template-counts-a-lapsed-intention-to-remove-as-a-failure

The template for use case 12 on the shape's third tranche: 14 published
views with licences; 11 sections in a buyer's order (namesakes apart,
standing, principals, the holding chain, the principals' other companies
newest first, the serial pattern's notices, offices, mortgagee
possessions, people's prohibitions and bankruptcies, the Gazette on the
entity, not held); the reaches officers, office and chain (depth 2).
23 flags: serial-pattern (MC-P1, the SPV-serial rule) and earlier-failure
set each dated failure of a principal's companies beside a start with the
gap in days, the window read as report["window_days"] (ruling 65; no cut
until the shape carries it, card on construction-2); entity-status (a
Gazette liquidation newer than the monthly file is red), young-entity,
sole-vehicle, professional-office and shared-office (an accountant's, a
lawyer's, a care-of or a fifty-company office is a hub, never compared),
possession, prohibition, bankruptcy, insolvency-notices, holding-chain,
history-reach, namesake-exposure; nine not-held registers blocked (LINZ,
OIO, consents and council minutes, courts, PPSR, Insolvency Register, REA,
building practitioners, past roles). Nothing over a principal's companies
clears while the file lists current roles only.

Checked: 37 fixture tests (26 mutants, each caught); 3 real-table tests
(slow) green; bin/fast products/templates green in 30.1 s;
tests/test_imports_one_way.py and test_reading_limits.py green;
python -m products.report check green. Checkpoint: twelve real subjects
(checkpoint.list), none refused, no rule broken; four faults fixed on the
way (a lapsed intention to remove counted as a failure; a stale count; a
one-company group read as a full history; care-of offices named apart).

For the integrator:
1. Nothing outside the folder changes; no unit to restart (qv4-report reads
   templates from disk per render).
2. tests/test_generators.py will fail in this working copy until the
   gate's rebuild indexes the lesson and the four cards, as before.
3. The template references two cards on unmerged branches
   (the-report-carries-no-template-parameters, construction-2;
   the-report-cannot-reach-the-charities-register, healthcare-1).
Lesson: filed (an intention to remove is not a removal).

## Result (integrator, 2026-10-21 16:35 NZDT)

Merged into main as 9f98d83 (`merge integrate/property-1: gate green`). Branch `integrate/property-1` from `session/property-1` (edaa35a), main merged. Carried with it: the board's two party-boards views (Party board roles, Party board pages) and the register entry, held from party-boards-1 under the gate-order lesson, `products.board check` green against the live tables; party-boards-1's merge record; board, lessons index and queue regenerated. Template 12 (property development due diligence): 14 views, 11 sections, 23 flags; four cards (two for the report lane, to `fix-report-2`; one on the chain reach; one for construction); lesson `an-intention-to-remove-is-not-a-removal`. Fast tier green in 399.2 s (target 300 missed under load, recorded). Gate green, nothing to load. Step 5.2 closes with this merge: ten templates. `qv4-board` and `qv4-report` restarted 16:36. Branches and the working copy retired.
