# templates-fix (session fix-products-templates-1, 2026-10-22)

Where it stands: done; branch `fix/products-templates-1` pushed, merge
request `fix-products-templates-1` raised. Nothing half-done. The three
template cards fix-templates-1 left open are closed.

- **Healthcare.** The five health keys (`retirement_villages`, `hdc`,
  `certification`, `health_providers`, `aged_care_commissioner`) in the
  not-held section, the villages file on standing too; each blocked flag
  names its register as the catalogue does. An officer's near links counted
  apart in the overlap and the officers' notices (info alone, never amber,
  never red on a prohibition). `chain` in the Gazette section; a notice up
  the chain beside the entity's own.
- **Property.** `oio`, `building_consents`, `rea` named. A director's
  near-linked companies are a namesake's principal of their own, amber at
  most, counted apart in every principal check; history-reach fires on
  them. The chain section lists the directors above; the Gazette and
  possessions sections name `chain`.
- **Ownership.** `chain_depth = 2` and a chain section; holding-chain
  names what was read above (every hop near at the checkpoint: no holder
  row carries a business number); a notice above beside the company's own;
  the holder-name checks read the holders up the chain.

Each change has a fixture test that fails on HEAD and new mutants; each
checkpoint was re-rendered before and after, recorded in its `limits.md`.
Notable: property's serial pattern on GORING and KERVIL went from fired to
blocked (it had added a namesake's liquidation to the entity's own).

Checks: `bin/fast products/templates` green (42 s); the three templates'
slow tests green (two real assertions on the not-held line and one on the
chain amended); `python -m products.report check` green (64 s);
`tests/test_imports_one_way.py`, `tests/test_reading_limits.py` green.

Next: the integrator merges; `qv4-report` needs no restart (no form change).
