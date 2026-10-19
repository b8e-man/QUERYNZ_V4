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
