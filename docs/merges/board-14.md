# board-14: ruling 119, a fold by hand of organisation entities, for this view
branch: session/board-14 (pushed, 2fe2499; three commits on e58a404, one per tranche)
session: board-14 (Opus, build, scope products/board/)
raised: 2026-10-29
claims: products/board/ (collapse.py, search.py, panes.py, graph.py, server.py, state.py, tables.sql, static/graph.js,
spec.md; tests/test_hand_fold.py new, test_collapse.py, test_real.py);
lessons/a-fold-the-reader-makes-in-the-results-brings-its-own-members-into-the-graph.md; docs/status/board.md.
publish: nothing. units: unchanged.
**tables.sql: one column added**, `board.paths.boxes text NOT NULL DEFAULT ''` (`ALTER TABLE … ADD COLUMN IF NOT EXISTS`;
nothing dropped or updated). **After the merge: run `python -m products.board state`** on node2 in the main checkout, then
**restart `qv4-board`** at the release (`graph.js` changed: a tick box opens nothing).

## What it does (ruling 119)

1. **Tick boxes.** Every organisation entity in the results carries one (`panes.tick_box`, `hk=`, tied by `form=` to the
   collapse section's form `handfold`). An organisation entity is: a group whose shown rows pub.names reads as organisations,
   or, with no kinds, whose rows in hand are all an organisation's (`collapse.organisation_group`); a lone row of an
   organisation view, a shareholder of holder type `company` (`collapse.ORG_ROWS`), or a row pub.names reads as an
   organisation (one query per page, by key) (`collapse.organisation_row`). A person entity, a document or an event has none.
2. **"collapse the ticked into one"** (`collapse.hand_fold`): the ticked become one entry at the first one's place, named by
   `collapse.label`, saying "collapsed here by hand; not a link" (`collapse.words`), with an unfold link. Its dossier is
   `fold:hand:<ids>` (`dossier.gather_fold`, unchanged): the members as the entities they are. The criteria's folds leave
   a fold by hand as made. A person named in a crafted address is never folded, in the results or the graph.
3. **The graph** (`collapse.fold_graph`, `graph.fold_rows`): the fold is one node with the same words. Its members are drawn
   whatever the search's 16-row cut, on the search's graph and on a graph centred on a member, so the entry's click opens it.
4. **The address and the saved path.** `hf=` per fold (ids quoted, comma-joined; at most 20 folds of 100), `search.Boxes.hand`;
   the ticked `hk=` join as one fold and are not written back. A saved path stores its address's boxes (`boxes`); a path
   saved before opens as it did. Nothing else is written; no link, no decision.

## Tests: fail on main, pass on the branch

`tests/test_hand_fold.py`, 10 fast tests on a Rank Group fixture: all 10 fail on main (the archive of `main` with the file
copied in), all pass here. `test_real.py` (slow, the real tables): Rank Group offers 21 organisations; the group, the five
RANK GROUP LIMITED holder rows and the Commerce Commission party fold into one entry and one node, the 14 others stay
apart and can still be ticked; the entry's click graph holds the fold, a graph centred elsewhere does not; a path saved
with the fold (scratch_board_14 in the sample) reopens folded. `bin/fast products/board`: green in 42.5 s. Root tests:
green. The whole board suite with slow: green after two test fixes (a monkeypatched `lone_hit` signature; a comment read
as SQL).

## Measured, live (read-only), main on 8496 against this branch on 8497

| Page | main | branch |
| --- | --- | --- |
| "Rank Group" searched, two runs | 1.84 / 1.74 s, 69 KB | 1.86 / 1.74 s, 78 KB |
| The same with the seven folded by hand | | 1.74 / 1.73 s, 153 KB (every href carries the fold) |
| The folded entry's click graph | | 0.12 s, 13 nodes, one fold node |
| The fold's dossier | | 0.21 s, 44 KB, 7 members |

## Read on a default

The brief names "a lone row whose view the catalogue marks organisation", but the five holder rows sit in `shareholders`,
a person view. They are offered because their own column says `company`, and a donor row (a figure view) because
pub.names says organisation. The brief's "twenty other Rank Group companies" measured 14 distinct entities offered.

Lesson: filed (above).

## Result (integrator, 29 October 16:45 NZDT)

Merged: `b9c06a5 merge integrate/board-14: gate green`. The session could not write the inbox (the auto-mode
sandbox refused `querynzv4-work/inbox/`), so it left this request in its scratch folder and the integrator filed
it. The branch alone was refused by the first gate (16:17 to 16:27) on `tests/test_generators.py`: the lesson was
filed but `lessons/INDEX.md` not regenerated. Merged into `integrate/board-14` off main, index regenerated
(5b3276d), second gate green 16:42 (whole-repository fast tier, the board's slow tests; nothing staged).
After the merge: `python -m products.board state` run on node2 in the main checkout (`board.paths.boxes` added,
nothing dropped); released; `qv4-board` restarted. Working copy and local branches retired; the remote
`session/board-14` is Arthur's to delete. The next board work is pinned to 30 October (an entities view from the
links lane; the donor name rule on organisation rows; same-name bodies).
