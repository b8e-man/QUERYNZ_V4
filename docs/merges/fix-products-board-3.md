# fix-products-board-3: the collapse section folds rows pub.names holds none of ("lloyd budd")
branch: fix/products-board-1 (pushed, 9a01ff6; one commit on e6fac4c)
session: fix-products-board-1 (Opus, fix weight, scope products/board/)
raised: 2026-10-28
claims: products/board/ (collapse.py, spec.md, tests/test_collapse.py, tests/test_real.py); one lesson, lessons/INDEX.md; docs/status/board.md

## The fault (Arthur, live board, 19:20)

"lloyd budd" with "a shared first and last name" ticked folded the links lane's entities but left six single-row
entities apart: one charity officer and five Gazette celebrants, the same name. collapse.keys read name keys from
pub.names by ref, and pub.names holds 0 rows of charity_officers and gazette_celebrants (the links lane reads only
the views links/spec.md names), so those rows had no key.

## The fix

`collapse.row_name_keys(v, r)`: where pub.names has no entry for a lone row's ref, the row is keyed for "name" and
"full" from its own first declared Name (catalogue Fields.names, read in its ruling-85 order: parts, given-family,
family-given), as links/rows.py `read_name` reads a name, folded by `people.key_fold` (links' fold), so the key has
pub.names' fl_key/full_key shape. A row pub.names does hold is never re-read. A suppressed row, a "name suppressed"
value, or a name with an organisation word gets no key (abstain: the lane's weak-surname exception is not copied).
Only the first Name keys a row: a second is an alias or another party. A fold says nothing new (ruling 112).

## Verified

- `tests/test_collapse.py` (17): a charity officer and gazette celebrants fold with a named entity by name and by
  full name; a celebrant filed surname "Jane", given "Hart" does not; suppressed and organisation-word rows abstain;
  a row pub.names holds keeps its pub.names key. Mutations go red: swapping given and family; re-reading held rows.
- `tests/test_real.py` (26, alone): new live tests: "lloyd budd" by name in both states is one fold holding the
  entity, the charity officer and the five celebrants (each celebrant keyed "lloyd budd": family-given read right);
  board-made keys equal pub.names' keys on live directors (parts) and candidates ("SURNAME, Given") rows.
  The two-second floor holds. It failed once while the check ran beside it on the same database; alone it was
  green four times out of four (search.search does not call the collapse code).
- Live: "lloyd budd" 17 entries → 3 by name (the fold, the same fold under its tab, one minister diary entry),
  13 by full name; page time unchanged (~2.9 s, no new query).
- `python -m products.board check`: green. `QV4_INTEGRATOR=1 bin/fast products/board`: green in 52.3 s.

## The integrator must

1. Merge `fix/products-board-1`.
2. **Restart `qv4-board` at the release.** No table, unit or setting changes.
3. Regenerate `lessons/INDEX.md` if the merge conflicts on it (one new lesson).

## Result (integrator, 28 October 20:03 NZDT)
Merged c4a8f4f as `integrate/fix-products-board-3`, gate green at the first run (the board's slow tests only: 15 minutes). Released; `qv4-board` restarted and answering. "lloyd budd" by a shared name now folds the entity, the charity officer and the five celebrants. Branch and working copy retired. Why the rows had no key: the links lane reads neither `pub.gazette_celebrants` nor `pub.charity_officers` (the charities lane published a day after the lane's reads were written); a links fix to read both is the lasting repair, this fallback stays for any view the lane leaves out.
