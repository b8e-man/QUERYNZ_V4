# recruitment: where it stands

**Date:** 2026-10-20. **Step:** 5.2, template 1 (use case 8, recruitment
board screen), `products/templates/08-recruitment/`. **Merge requests:**
`recruitment-1` (merged), `recruitment-2` (raised: the common rules from the builder).

## Done

- `template.toml`: 23 pub views with licence, attribution and refresh; seven
  sections in the consultant's order (namesakes apart first, then
  directorships and holdings of record, Gazette insolvency/bankruptcy/
  prohibition, charity and society roles, political money, seats and
  declared interests, what is not held); depth 1 (co-directors are not the
  subject's record); limits.
- `rules.py`: 11 flags for the old seven person rules (liquidation history,
  prohibition, young entity, namesake exposure, charity officer roles,
  charity integrity marks, ComCom) plus subject hub, register removals,
  bankruptcy, public life; the builder adds group-standing, hubs-met and
  replaced-return. `flag` and the helpers are the bound `contract`. Red only on confirmed
  rows, amber on a namesake's; a clear only where the walk could have seen
  it (bankruptcy, charity marks and ComCom blocked). Imports nothing of the
  shape (the one-way test).
- Checkpoint on 12 real subjects (keys in `checkpoint.list`): re-measured
  by `recruitment-2`, all 12 print, none refused, 0.1 to 5.1 s through
  the CLI; three facts read against their Gazette notices. `limits.md`.
- Tests: 21 fast (fixtures, with `contract` bound as the loader binds it;
  the shape's CLI), 3 slow (real tables through the CLI, each memo holding
  the three common flags once); `python -m products.report check` green;
  one-way test green.

## Carded

Open: `bankruptcies-and-appointments-are-not-in-pub-names` (links). The
report lane's eight cards are closed; `limits.md` still describes two of
them (`a-donation-row-start-has-no-group`, the Gazette notice date) as
limits, not re-checked here.

## Next

1. The integrator merges `recruitment-2`; nothing to install (the shape's
   `qv4-report` serves every template on disk).
2. When the charities lane publishes, add its views and the integrity-marks
   rule; when links carry bankruptcies, the bankruptcy rule clears.
3. Step 5.2, template 2: use case 4, agriculture.
