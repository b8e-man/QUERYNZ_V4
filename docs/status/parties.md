# parties: where it stands

**Date:** 2026-10-20. **Step:** 4.1, the Register of Political Parties and
party lifecycle, `registers/parties/`. **Merge requests:** `parties-1`
(merged), `parties-2` (raised).

## Done

- Tranche 1: the register page (17 parties; contact lines private), the
  lifecycle (renames one registration, re-registration a new one), the
  outside check against the notices.
- Tranche 2: the Commission's notices taken from the Gazette lane
  (`pub.gazette_notices`, section `au`, register titles: 137), text from
  its export by hash where equal to the parties export (136 of 136), cited
  to that document and the notice's row (`gazette_key`); the old export
  kept landed, "read, compared, not cited". New: 2023-au2700 cancels
  Heartland New Zealand (20 June 2023). A section 70A logo cancellation no
  longer mints a second One New Zealand Party: 77 registrations.
- `same_name_as`/`same_name_note` on `pub.parties`: New Zealand Loyal,
  United Future New Zealand, the Alliance kept apart and said so.
- `pub.party_labels`: 1,154 (label, day or year) rows from 17 tables of
  six lanes, 1,009 joined, 0 disagreeing with any lane's own join.
- Full build in the sample database (`scratch_parties_2_full`, labels read
  from the real `pub`): catch log empty, outside check green. Fast tier
  green (whole repository, 290 s).

## Carded

- Closed: renamed-party money (confirmed), New Zealand Loyal (two),
  labels the frozen site left unfolded (measured).
- Open with what each needs: three labels and short labels (`bin/fix
  keys`: `NZ`, `and`, `Incorporated`, `ACT`); unregistered candidacy label
  (site); five parties with no cancellation held (a capture, after the
  switch); new: the lanes and the site do not yet join the party labels.

## Next

1. Integrator: append `gazette-party-register-notices` version 2 from
   `profile-proposed.jsonl`; load the lane after the label lanes so
   `pub.party_labels` sees their latest rows.
2. A fix session on `keys`; then each consuming lane joins the view.
