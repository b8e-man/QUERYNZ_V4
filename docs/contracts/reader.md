# Contract: the reader

**Fixes:** the one way a document becomes text and rows. **Test:**
`support/reader/tests/`. **Taken from:** `data-layer/docread`, moved behind
this contract in 1.10; the old estate had 11 text-extraction calls in 4
shapes across 9 files.

1. **Per page.** A document is read page by page, and each reading knows
   its page.
2. **Text layer first.** The page reader (a model that turns a page image
   into text) runs only for pages the profile marks as image pages or that
   the surface signals show have no usable text layer. Text is extracted
   with layout kept, or tables break apart.
3. **Run from the document profile,** by slug and version. Profiles come
   before readers: a reading without a profile is refused.
4. **Every reading is stamped** with the reader, the model and its
   settings, the profile and version, whether it read text or pixels, and
   when. The stamp is part of the key.
5. **Stored by the document's hash and replayed.** The fast tier replays
   stored readings and never calls a model (ruling 50). A missing reading
   fails the test and names the document; the session asks for it as a
   re-read job.
6. **A reading that fails its own check publishes nothing,** not a number.
   Every return prints its own total, so every reading is scored against it.
7. **A reading never carries a home address into a published row;** the
   row contract keeps that in the private schema.
