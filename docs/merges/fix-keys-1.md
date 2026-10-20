# fix-keys-1 (second): four named spelling rules in keys.parties
branch: fix/keys-1 (pushed; d323de2, on main 8706017)
session: fix-keys-1 (fix, keys; Opus)
raised: 2026-10-20
claims: keys/parties.py, keys/tests/test_parties.py; cards `three-party-labels-resolve-to-no-registration` (two of its three labels) and `short-party-labels-in-the-expense-and-interests-registers-do-not-resolve` (its "Act"/"ACT" line)

Four rules, each named in the module and each with a test that fails
without it (shown: every new test fails against main's `parties.py`):

- `SPELLINGS`: "nz is new zealand", "and is &", "a trailing incorporated
  is off". Applied to the label and to every registered name alike, and
  tried only after the core as filed misses, so nothing that resolved by
  exact, variant or core can move.
- `THE_X_PARTY`: an abbreviation "The X Party" also answers to X. The
  lane's ACT abbreviation is "The Act Party"; "ACT" and "Act" now reach
  ACT New Zealand. Abbreviations only: a *name* of that shape sheds
  nothing (tested).

Basis stays `core` (the contract's set unchanged); two live registrations
stay unresolved; the fuzzy arm's floor, length window and rival rule are
untouched (tested). Both paths, the snapshot and the lane's rows.

Measured: the label set parties-2 publishes as `pub.party_labels` (its
17 source tables, its `on` expressions, its Independent and bracket
rules), rebuilt from the published tables of `querynz_v4` and resolved
against `pub.party_names` joined to `pub.parties` (parties-2 is not merged
and its scratch schema is closed to the session reader): 1,154 labels.

- Unresolved before 119, after 27: **92 labels resolve** (3,369 rows):
  90 `ACT`/`Act` (expenses, interests), `New Zealand Outdoors and Freedom
  Party` 2023, `Animal Justice Party Aotearoa NZ Incorporated` 2023.
- **0 labels that resolved before resolve to a different registration.**
  One changes basis only: `NZ Outdoors and Freedom Party` 2022, fuzzy:0.94
  to core, same registration.
- Left, not this fix: `The Maori Party (Te Pati Maori)` already resolves
  through the lane's bracket rule; "United Future", "Progressive …",
  "Internet Party" and 22 more need lineage or are not registered names.

For the merge: contract `docs/contracts/keys.md` item 7 (outside this
fence) may add "the core arm also compares after named spelling rules
(NZ/New Zealand, and/&, a trailing Incorporated; an abbreviation 'The X
Party' answers to X)". The two cards are the lanes' to re-measure on
replay; neither lane needs a code change.

Fast tier: whole repository green (289 s), keys green (27 s). Lesson:
nothing new.

---

# fix-keys-1: keys.parties resolves labels against pub.party_names, by date
branch: fix/keys-1 (pushed; 2932596)
session: fix-keys-1 (fix, keys)
raised: 2026-10-20
claims: keys/parties.py, keys/tests/test_parties.py; card `keys-parties-should-read-the-party-names-the-lane-publishes`

`party_name(label, rows, on=date)`: given the parties lane's name rows
(`pub.party_names` joined to `pub.parties` for `registered_on` /
`cancelled_on`; without those, the names' own windows set the
registration's window), it resolves against the registrations live on the
day (a year: live at any point in it) and returns the registration's key
with the basis. Same arms as before: exact, variant, core, fuzzy. Every
rule kept: the amendment marker comes off first; a label two live
registrations answer to is unresolved, whatever the arm; the fuzzy arm
needs one clear winner, no other registration close behind, and the
party's distinctive word readable. "New Labour", "NZNP" and persons stay
None. Called with the snapshot (the default), it behaves as before.
`keys.parties.name_key` is the lane's comparison key, equal to
`pub.party_names.name_key` on all 149 published rows.

Measured on the published tables (the real database, 20 October), on the
rows that are unresolved today:
- party returns (`pub.party_return_totals`, by the return's year): 38 of
  42 resolve (31 of 35 from 2019; the card's 34 is a day older). 32 exact,
  4 core, 2 fuzzy. Left: `The Maori Party (Te Pati Maori)` (2 rows),
  `Animal Justice Party Aotearoa NZ Incorporated`, `New Zealand Outdoors
  and Freedom Party`.
- disclosures (`pub.disclosures`, by `received_on`): 53 of 53. 42 exact,
  4 core, 7 fuzzy (`The Greens, Green Party of Aotearoa New Zealand`,
  0.96).
- No label in this set changes with the window; the window decides
  between registrations of one name (New Zealand Loyal 2023 and 2026,
  held by the tests; United Future likewise).

For the merge, please:
- Contract `docs/contracts/keys.md` item 7 (outside this fence): add "or,
  given the lane's name rows and `on`, (registration key or None, basis)
  among the registrations live that day; two live registrations is
  unresolved". Its last sentence ("defaults to the snapshot … until the
  parties lane serves the live one") now has the live path beside it.
- Close the card; the callers (party-returns, disclosures, and the parties
  lane's `lifecycle.name_key`, which can now import `keys.parties.name_key`)
  are their lanes' work.

Fast tier: whole repository green (44.7 s, --no-fill). Lesson: nothing new.

## Result (integrator, 2026-10-20 06:20)

Merged into main as c102ffd. Done at the merge: contract item 7 in
`docs/contracts/keys.md` carries the live path (the lane's rows and `on`;
two live registrations unresolved); the card is closed. Fast tier and
gate green. The session ran headless from the integrator (the first):
eight minutes from launch to request. Left to the lanes, each in its own
session: party-returns, disclosures and parties switch to
`party_name(label, rows, on=date)` and the parties lane's `lifecycle`
takes `keys.parties.name_key`.

## Result (integrator, 2026-10-20 18:59 NZDT; the second fix)

Merged to main at 1f6fa2a, gate green. The contract's item 7 now names the
four spelling rules (`docs/contracts/keys.md`). The two label cards stay
open for the expenses, interests and party-returns lanes to re-measure on
replay through `pub.party_labels`. Worktree and branch retired.
