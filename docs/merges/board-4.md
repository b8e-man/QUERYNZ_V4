# board-4: night mode, no edge numbers, donations summed, the originating document (ruling 86); the use cases tab (ruling 87)
branch: session/board-4 (pushed; nine commits on 78701e0)
session: board-4 (Opus, build, scope products/board/)
raised: 2026-10-26
claims: products/board/ (catalogue.py, panes.py, graph.py, search-tab rendering in server.py, check.py, spec.md; new
document.py, uses.py; tests: new test_night.py, test_document.py, test_uses.py; test_graph.py, test_panes.py,
test_real.py extended); the patch `board-4-docstore-read.patch` beside this file for support/docstore (NOT on the
branch: outside the fence); lessons/a-captured-document-served-whole-carries-every-address-it-prints.md;
docs/decisions/queue/which-captured-documents-the-board-may-open-whole.md (no default); docs/status/board.md.
No card opened or closed.

## What it does

1. **Night mode (86 (1)).** One dark stylesheet in `panes.CSS`, with no toggle. The SVG takes its colours from it
   too: no inline fills, only the edge strokes. Every text colour reads at 4.5:1 or more on every background the
   sheet sets. `panes.contrast_problems` reads those pairs from the stylesheet string. The key's edge colours are
   re-chosen: blue, orange and aqua from the validated palette's dark steps, with yellow, magenta and violet
   stepped lighter. Each is 3:1 or more on the picture, and every pair is 15 or more apart in OKLab (×100), all
   pairs and not only neighbours.
2. **No edge numbers (86 (2)).** An edge's words are its first cause's words, with "(+n)" when there are more.
   They are drawn on the line only where their box touches no other text box, node label or circle. Placement
   is deterministic, with a 2-pixel gap. Every line keeps its hover title. `graph.text_boxes` reads each `<text>`
   back from the rendered SVG (x, y, anchor, class, characters), and `touching_text` finds pairs that touch. The
   list under the key has one heading per connected row, its edges beneath, ordered by kind in the key's order,
   then by title.
3. **Donations summed (86 (3)).** `catalogue.GIFTS` covers party return donors, disclosures and candidate return
   donors.
   - A donor's rows filed under one name are one node. The match is on the name as filed, with case, macrons and
     spacing folded.
   - There is one money edge per party, found in pub.parties by key or by name as the relations match it, or per
     candidate, where one node stands for that candidate's returns. It joins any party node a candidacy or role
     edge already drew.
   - The label reads "donated $T (n returns, first–last)". The total is the sum of the return rows' own amounts.
   - Every addend is listed with its amount, its year and hrefs to its row and its return.
   - A row an amendment replaced, or one with no amount, is listed and not added. A disclosure is listed and
     never added, because its gift is also in that year's return (the old rulings 190 to 193, as the scan
     templates state). Its own sum is named apart.
   - The page says that one filed name is not a finding of one person.
4. **The originating document (86 (4)).** Every citation, in the results pane and in the row's own pane, begins
   with "source": `/doc/<sha256>`, with `#page=n` for a PDF. The publisher's address stays beside it.
   - **Hard limit 15 governs this.** Party and candidate returns and disclosures print donors' home addresses.
     The Gazette, the tribunals and the companies files print other people's. A document is served whole, so
     only a source in `catalogue.SERVED_SOURCES` opens: house (167 documents; one address-shaped line, the
     Commission's own) and expenses (103 documents; none). Lines were counted, never printed.
   - Every other held document reads "source held, not opened here (hard limit 15)". `/doc/` answers 403 for it
     without reading its bytes. A document not in the store reads "document not held here". A suppressed row or
     withheld text offers no link.
   - Arthur's decision is queued with no default: `which-captured-documents-the-board-may-open-whole`.
   - The handler: 64 hex characters only. It reads `<root>/<aa>/<sha>`, resolved inside the root and hashed
     before sending, and serves it with its stored content type under `Content-Security-Policy: sandbox`. A
     malformed, absent, withdrawn or mismatched document answers 404, and nothing under `/doc` lists the store.
5. **The use cases tab (87), `/uses`.** It reads `docs/plan/reference/registers-and-use-cases/the-sixteen-use-cases.md`
   at render time, found relative to the module, so the release copy shows its own plan. It shows 17 rows in the
   plan's order, with 17 after 15 as printed: number, name, who, question, shape, step. If the file is missing,
   the tab says so.
   - **Templates:** `products/scan/templates/*/template.toml` is read as data files from disk (tomllib), never
     imported. The one-way test binds imports and queries of another module's inside. The scan publishes nothing
     in pub, so the pub route had nothing to read. No template has a `use_case` field, so the tab reads the
     owner line's "(use case N)", and reads a `use_case` field once a template carries one. Templates are built
     for use cases 9, 10 and 14 today.
   - **Registers:** the reference names registers by use case only in `not-held.md`. Each of its sources maps to
     the board's registers (`catalogue.REFERENCE_REGISTERS`), and each is shown as held or not held from the pub
     views present.
6. **The check** gains:
   - no two text boxes touching on the three rendered graphs, and no edge number;
   - the known donor's party edge total equal to the addends listed under it and to the register's own sum;
   - `/doc/` answering 200 with the stored content type and the document's own bytes for a known cited document,
     404 for a wrong or malformed sha, and 403 for a party return; the citation beginning with "source";
   - the contrast floor;
   - the use cases tab's 17 rows in the plan's order.

## The fence: the patch for support/docstore

The whole-repository fast tier refused the first version: `test_no_query_crosses_a_lane` says `docs.*` belongs to
`support.docstore`. So the board now reads the store only through `support.docstore`: `landing.names_of`, and a new
read-only `landing.documents_of(shas, conn)` returning `{sha: {kind, source, withdrawn}}` in one query. That
function and its test are in **`board-4-docstore-read.patch`**, beside this file. Until the patch is applied,
`document.records` returns None, nothing opens, every link says why, and the live check reports exactly one
problem.

## Checked

- `QV4_INTEGRATOR=1 bin/fast products/board`: green (41.9 s).
- Whole-repository fast tier (`QV4_INTEGRATOR=1 bin/fast`): one red, the generated records (below).
- `python -m products.board check` against live pub:
  - on the branch alone: one problem (nothing opens without the patch);
  - with the patched support/ first on the path: green;
  - the first version, before the fence fix: green in 25.6 s.
- Slow tests (`-m slow`): 10 passed with the patch, including the two new ones (the summed edge, the source link).
- The patch's own tests: support/docstore's fast tests on a patched copy, 9 passed.
- Mutants, each shown to fail its test or the check:
  - nothing avoided in placement: the pure test, and the live crowded graph with 310 touching pairs;
  - the planner's own overlap reading blinded: the SVG reading still fails;
  - the day scheme's highlight colour put back (1.62:1);
  - a total one cent off its addends;
  - party_returns put into SERVED_SOURCES (the check: 200 where 403 is wanted).
- Rendered pages looked at in scratch screenshots: graph, search and use cases.
- Live examples: the known donor has 11 rows over 6 years, drawn as one party edge with 10 rows added and 1
  disclosure listed apart.

## For the integrator

1. Apply the patch:
   `git apply /home/user/querynzv4-work/inbox/merge-requests/board-4-docstore-read.patch`
   It adds `support/docstore/landing.py` `documents_of` and a test in `support/docstore/tests/test_landing.py`.
   Merge it with or before the branch.
2. Merge, then **restart `qv4-board`** at the release. New modules: `document.py`, `uses.py`. No table or
   other module changes, and no `state` run.
3. **The store path.** The unit needs no new setting: the board defaults to `/mnt/hdd2/qv4-docs`, which is
   `drwxr-xr-x user:user`, and the unit runs as `user`. Add `QV4_DOCS=` to the unit only if the store moves. The
   release copy must carry `docs/plan/reference/registers-and-use-cases/` and `products/scan/templates/` (it does
   today).
4. **Rebuild `lessons/INDEX.md` and `docs/decisions/queue.md`** at the merge (`bin/lessons-index`,
   `bin/decisions`). One new lesson and one queue file; the fence refuses generated files to a build session, so
   `test_generators` is red on the branch until then.
5. Optional, for the scan's owner: a `use_case` field on each template would replace the board's reading of the
   owner line.

## Whole-repository fast tier

Second run, after the fence fix: one red, `tests/test_generators.py::test_the_committed_records_generate_cleanly`.
It fails because `lessons/INDEX.md` (and, in the first run, `docs/decisions/queue.md`) lag this branch's new lesson
and queue file, which is item 4 above. Everything else is green, including `test_imports_one_way` (red in the first
run, and the reason for the patch). It took 614.8 s against the 300 s target (missed, recorded by the tier).

## Result (integrator, 26 October 07:50 NZDT)

Merged as 27062d6: fast tier green (620 s), gate green, nothing to load.
The docstore patch applied by hand on the integrate branch (the hooks
refuse `git apply`): `landing.documents_of` and its test, 1 passed.
Indexes regenerated at the merge. Ruling 88 (26 October, about 07:20)
answers the queue item: the board opens every held document whole,
addresses included, built by `fix-products-board-1e` from this main.
Working copy and branches retired; release copy moved; `qv4-board`
restarted; the use-cases tab, the dark scheme and a House document's
source link answer on the local network.
