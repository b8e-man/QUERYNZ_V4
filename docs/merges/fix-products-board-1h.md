# fix-products-board-1h: the board catalogues the three Hansard views (carries board-7)
branch: fix/products-board-1 (pushed, 7ea37b9; carries board-7, ruling 100's Cytoscape canvas, merged in from integrate/board-7 and not yet on main)
session: fix-products-board-1 (Opus, fix, scope products/board/)
raised: 2026-10-27
claims: products/board/ (catalogue.py, panes.py, search.py, spec.md; tests: new test_hansard.py, test_catalogue.py's published list);
cards/the-board-has-no-entry-for-the-hansard-views.md (closed); lessons/a-published-view-with-no-shared-id-gets-no-pointer.md;
docs/status/board.md.

## What it does

1. **The register.** "Hansard: who spoke in Parliament" in `catalogue.REGISTERS` straight after MPs' interests; in the
   House's family (`FAMILIES`, the same colour as `house`: the contrast tests are green, no colour added); `hansard`
   leaves `NOT_HELD`; `MAIN_VIEW["hansard"] = "hansard_sittings"`.
2. **The sitting day** (`hansard_sittings`, main view): titled "20 November 2024 · Parliament 54, volume 780" through a
   new `View.title_format` (falls back to the plain title when a column it names is empty); Parliament, volume, Draft or
   Corrected, sections, turns, member and role-only turns, members, the index's last-modified and fetched (empty until
   hansard-2); the transcript's address as the source address; its sections joined in order.
3. **The section** (`hansard_sections`): titled subject and day; the text whole in its own pane under "Text as
   captured" through a new `View.text` (label, column, words when empty), "no text held" for the 262 empty; never in a
   results hit or the table (it is not in `fields`), and not searched (a search finds a section by subject, proceeding
   or bill; searching the text is a line in `search` if Arthur wants it). Its day and its turns in order.
4. **The speech turn** (`hansard_speeches`): titled `Smith, Stuart · "Stuart Smith" as read by the old estate · <day>`;
   a role-only turn (no member id) is titled its role and day and is kind `event`, so no person pane is offered and no
   person is shown. Each turn's section, and the member's other turns by Parliament's member id. The field search's Name
   is `member_name`, **family-given**, not given-family as the brief said: the old roster prints "Kuriger, Barbara" on
   all 40,098 member turns, and a comma reads family then given (ruling 85).
5. **Every row** carries "taken from the old estate's tables; original not held; held at 23 September 2026"
   (`HANSARD_NOTE`), and the source note as a field.
6. **A `Join` may match on two columns** (`Join.pairs`, `search.children`): a turn's section is its day and section index;
   the views publish no section key on a turn.

## No pointer and no edge to the House's member row

`pub.members` publishes no Parliament member id (its key is election and seat; `name_key` is a folded name); no column
of it holds any turn's `member_id` (measured: 0 rows). A pointer would read "(row not held)" on every member turn, a false
absence, and the only join left is a name match, which plan 4.9 forbids (no link is made by looking). So no `POINTERS`
line and no `Relation`. The shared id is the house or hansard lane's to publish; then it is one catalogue line here.

## Suppression

As `panes.shown()`. The lane's pane.md says a name the estate holds as suppressed is suppressed in a section's text; no
published view carries a suppressed-name list or a flag on these rows, so the board has nothing to apply and shows the
text as published. Said in docs/status/board.md's known limits.

## Checks

- `python -m products.board check` against the live tables: green (was red on the three views).
- `pytest -m slow products/board/tests/test_real.py`: green. `products/board/tests`: green, test_night and test_canvas
  (the contrast floor with the House's colour on hansard) included.
- `QV4_INTEGRATOR=1 bin/fast products/board`: green in 43.3 s.
- A rendered walk on live rows (sitting day, section, a Speaker's turn, a member's turn): titles as above, the text pane
  present, "no text held" on an empty section, no person pane on the role-only turn. A search for "Edmonds" 1.3 s.

## At the merge

The integrator restarts `qv4-board` at the release. No table, unit or job changes. Lessons: one filed (above).

## Result (integrator, 27 October 07:10 NZDT)
Merged ae6120a, gate green at 07:06, carrying board-7 (ruling 100). The lesson's rule line shortened under 240 characters at the merge. Released; `qv4-board` restarted; a search for "edmonds" lists "Hansard: who spoke in Parliament". The card closed. No pointer from a speech to the House's member row until a lane publishes the shared id (the lesson filed). Branches and the working copy retired.
