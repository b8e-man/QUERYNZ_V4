# fix-products-board-1e: the board opens every captured document whole, ruling 88
branch: fix/products-board-1 (pushed, 07f1280; one commit on f1871b5)
session: fix-products-board-1 (Opus, fix, scope products/board/; fifth use of the name)
raised: 2026-10-26
claims: products/board/ (document.py, catalogue.py, panes.py, server.py, check.py, spec.md; tests test_document.py,
test_panes.py, test_real.py); lessons/a-captured-document-served-whole-carries-every-address-it-prints.md and
lessons/INDEX.md; docs/status/board.md; docs/decisions/queue/which-captured-documents-the-board-may-open-whole.md.
No card opened or closed.

## What it does

1. **No source is refused.** `catalogue.SERVED_SOURCES`, `catalogue.WITHHELD_WHY`, `document.WITHHELD`, the 403 and
   the words "source held, not opened here (hard limit 15)" are gone. Every other rule of `/doc/<sha256>` stands:
   64 hex characters only, resolved inside the store root, hashed before sending, the stored content type,
   `Content-Security-Policy: sandbox`, 404 for absent, malformed, mismatched or withdrawn, and nothing lists the
   store. A withdrawn document's row still says "document withdrawn from the store". A suppressed row or withheld
   text still offers no link (hard limit 16, `panes.source_link`, unchanged).
2. **Spec and status.** `spec.md` says the board opens captured documents whole under ruling 88 because it listens on
   the local network only (hard limit 13), and publishes no table and no export. The owns line loses the setting.
   `docs/status/board.md` says the same.
3. **Check and tests.**
   - Check case 12: a party return answers 200 with its stored content type and bytes that hash to its name. Before,
     it had to answer 403.
   - New `check.cited_by_source`: one held document of each source a published view's `document` column cites,
     read through `support.docstore` only. Each must answer 200 with its own bytes (`check.opened_problems`).
   - Pure test `test_no_source_is_refused`: eight sources, including party returns, the Gazette, tenancy and an
     unknown name, each fetch 200. The handler test now gets 200 for a party return and 404 for a withdrawn one.
   - The citation test checks that a withdrawn document says "withdrawn" and offers no link.
   - Slow test `test_a_cited_document_of_every_cited_source_opens`.
   - Test counts did not change: test_document.py has 11, test_panes.py 17. test_real.py went from 10 to 11.

## Live figures

- The store holds 54,875 documents from 31 sources. None is withdrawn, so all 54,875 now open. Under board-4, 270
  opened.
- 27 sources are cited by a published row, and one document of each answered 200 with its stored type. That
  includes party_returns, candidate_returns, disclosures, gazette, companies and courts.
- Four sources hold documents that no published row cites: tenancy_tribunal, real_estate_authority,
  settlement_commitments and council_procurement. `/doc/` opens their documents too, but no link on the board
  reaches them.

## Checked

- `QV4_INTEGRATOR=1 bin/fast products/board`: green (41.5 s).
- `python -m products.board check`: green against the live data (28 s).
- Slow `test_real.py -k "document or source"`: 2 passed.
- Negative test: I patched `document.fetch` in memory to refuse party returns. `check.doc_problems` then went red on
  two counts: the party return case and the per-source case.

## For the integrator

1. Merge, then **restart `qv4-board`** at the release. Expected: document.py, catalogue.py, panes.py, server.py and
   check.py changed. No table or unit changes. No `state` run.
2. **The queue item.** I added a `ruled:` line naming ruling 88 to
   `docs/decisions/queue/which-captured-documents-the-board-may-open-whole.md` and left the file where it is. There is
   no `docs/decisions/closed/` folder. The convention (`bin/decisions`' docstring) is that the integrator removes a
   ruled question's file. So: remove it, then run `bin/decisions` to rewrite `queue.md`. I did not edit `queue.md`
   because it is outside this session's fence.
3. `lessons/INDEX.md` is already regenerated. The lesson's first line now says "outside the board (ruling 88)" and
   is 231 characters.
4. Not touched, and outside the board: `products/report/memo.py` still says "The document is cited, not opened".
   Ruling 88 covers the board only, so that is right as it stands.

## Result (integrator, 26 October 09:10 NZDT)

Merged as 8c9d8b8: fast tier green (630 s), gate green, nothing to load.
The ruled queue item removed at the merge and the queue regenerated.
Release copy moved; `qv4-board` restarted; a party return's source link
answers 200 on the live board. The working copy and branch stay: the
session for rulings 89 and 90 runs in them, branched from this fix.
