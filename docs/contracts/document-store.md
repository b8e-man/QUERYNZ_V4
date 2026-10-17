# Contract: the document store

**Fixes:** what a document is and how it is keyed. **Test:**
`support/docstore/tests/`. **Taken from:** the old `ingestion/landing.py`
(rebuilt, not moved: it stored an article's text, this stores bytes) and
the old estate's 424 returns held under two names each.

1. **A document is its bytes.** It is keyed by the sha256 of those bytes.
   Its names (file name, URL, the folder it was found in) are attributes; a
   document may have several, and a renamed file is the same document.
2. **One landing wrapper** (built in 1.10) writes the bytes to the store
   and one row to the `docs` schema; nothing else writes either. A failed
   landing is retried; a document is never registered before it lands.
3. **A web page has two hashes:** the bytes as fetched, and
   `content_sha256` of its canonical text (scripts, styles, comments, tags
   and whitespace runs removed). The second says "the same page again", so
   nothing is fetched or stored twice for a nonce or a timestamp. The
   reader reads the bytes, never the canonical text.
4. **Every reading and every row cites the document's hash**, with a page
   and a place. A citation never carries a file name or a row number that
   can change.
5. **Captured documents are never deleted** (hard limits, "what may be
   deleted"). Withdrawn or quarantined, they keep their hash and a note.
6. **Where a lane's documents come from** is one of three cases (plan
   1.10): copied by hash from the old `var/staging/` folders; exported
   once from old tables where no file was kept; or captured once, politely,
   through the fetch gate. The lane's spec says which.
