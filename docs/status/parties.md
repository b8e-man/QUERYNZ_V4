# parties: where it stands

**Date:** 2026-10-19, 21:30. **Step:** 4.1, the Register of Political
Parties and party lifecycle, `registers/parties/`. **Merge request:**
`parties-1`.

## Done

- Capture: the register page and applications page copied by hash (case
  1; 21 earlier captures in the old manifest were overwritten, catch-log
  lines at load); the Commission's 136 Gazette notices on the register
  exported once to `gazette-party-register-notices-2026-10-19.jsonl`
  (sha256 dc19fb7f…, case 2), landed in the store.
- Readers: `register.py` (17 of 17 parties; contact lines private),
  `notices.py` (every resolution read, none set aside; 15 stated renames,
  one corrigendum applied), `lifecycle.py` (78 registrations, 17 on the register, 55 cancelled;
  renames kept in one registration, re-registration a new one).
- Outside check green on the sample: 14 page parties joined to the notices
  by name, 3 before the notices' reach, 0 differing; the four known renames
  one registration each, the window agreeing.
- Label measurement: by name and window alone, 31 of 34 unresolved
  party-return rows and 46 of 53 unresolved disclosure rows resolve.

## Carded

- `keys-parties-should-read-the-party-names-the-lane-publishes` (blocker
  for the two lanes' labels; `keys/` is outside this fence).
- `six-parties-are-off-the-register-with-no-cancellation-held`.

## Next

1. A fix session on `keys` to read `pub.party_names` by date (card above).
2. When the Gazette lane exists, take its notices instead of the export.
