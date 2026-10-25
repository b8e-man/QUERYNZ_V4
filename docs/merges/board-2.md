# board-2: the board's two tabs, search and graph (ruling 80; step 4.9 second version)
branch: session/board-2 (pushed, 96f67cd; one commit on 6be51db)
session: board-2 (scope products/board/)
raised: 2026-10-25
claims: products/board/ (catalogue.py, search.py, panes.py, server.py, check.py, spec.md, new graph.py, tests/test_graph.py, tests updated); lessons/a-script-free-check-box-form-needs-a-hidden-mark-of-the-state-it-was-showing.md; docs/status/board.md. No card opened or closed.

## What it does

- **Search tab**, same address `/?q=&p=` so saved paths still open; `r=<register>` repeated carries the boxes checked.
  Left pane: check box per register in `REGISTERS` order, not-held registers greyed and disabled, "search all" at the
  top, the search box. Nothing checked = all (`search.selection`, with a hidden `was_all` mark; lesson filed). Results
  pane beside it (46rem): every matching row of the checked registers, up to 50 per view (`RESULTS_LIMIT`) with the
  view's whole count, every field, date, url and citation its View shows, the term marked with the search's own fold,
  character for character. Suppressed and withheld handling is `panes.shown()` as before. Row, person and link panes
  still open to the right; pins and paths unchanged (no table change).
- **Graph tab** `/graph?q=&r=&c=<view:key>`: `graph.py`. Up to 16 matched rows as nodes; one hop of edges from
  `Relation` lines in the catalogue (22 lines: money, role, candidacy, declaration, dealing) and `pub.links`
  (confirmed solid, near dashed), at most 10 per relation per row, with drawn and not-drawn counts in the key. SVG
  written by the server, no script, no library; deterministic sector layout; a node's href re-centres on it; each edge
  label is an href to the row that asserts it. No address edge (tested); a suppressed row draws no same-person edges.
  Reads on the product reader.
- **Outside check** adds: known donor found with only `party_returns` checked and not with it unchecked; the graph of
  a donor row draws a money edge, every node a real row, no address edge type; every relation column present in its
  view and in the view it matches to. Green live; shown to fail on a broken relation column.

## Verified

- `python -m products.board check`: green (about 10 s). Board tests: 40 pass (5 slow, against live pub).
- `bin/fast products/board`: green in 45 s. Root `tests/` fast: green.
- Server on loopback: `/health`, the search tab, the graph tab, a bad centre and a missing row all return 200.
- Screenshots looked at (scratch): macron marks both ways; a centred company graph reads cleanly; a 16-row name search
  is busy but readable.

## For the integrator

1. Merge, then **restart `qv4-board`** at the release (the server now imports `graph.py`). No table change; no
   `state` run needed.
2. Lanes, mirror these relation lines in your `pane.md` at your next session (the board already holds them):
   companies (directors, shareholders -> companies; company_lookup_roles, company_lookup_holdings -> company_lookups),
   societies (society_officers -> societies), charities (charity_officers -> charities), party_returns (donors and
   loans -> party_return_totals; totals `party_key` -> parties), candidate_returns (donors -> candidate_return_totals),
   disclosures (`party` -> parties.name; items -> disclosures), house (candidates -> parties.name by
   `party_registered`, -> electorates; members -> candidates), mp_interests (interests -> mp_interest_returns),
   party_boards (roles -> parties.name), party_finance (promoter_people -> promoters), limited_partnerships (partners
   -> partnerships), tenders (suppliers -> award_notices), overseas_investment (parties -> decisions), grants
   (`recipient_key` -> grant_recipients).
3. Not drawn, by choice (not among the ruling's types): regulator and court parties, gazette `register_key` matches,
   grants -> publishers. Each is one catalogue line if Arthur wants it.

Nothing new beyond the one lesson filed.

## Result (integrator, 25 October 14:05 NZDT)

Merged as bd2faca after `fix-registers-companies-1` (the one fast-tier
red, a date-dependent companies test the branch never touched): fast tier
green twice (692 s red on that test, then 632 s green on the combined
branch), gate green, nothing to load. Working copy and branches retired;
release copy moved; `qv4-board` restarted on the new code and both tabs
answer on the local network. The relation lines for each lane's `pane.md`
stand in this request for the lanes' next sessions. Not drawn, Arthur's
if wanted: regulator and court parties, gazette matches, grants to their
publishers.
