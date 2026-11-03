# Contract: the document profile

**Fixes:** what a profile carries and how a version is added. **Test:**
`support/profiles/tests/`. **Taken from:** `data-layer/docreview` and its
`profiles.jsonl`, which moved to `support/profiles/` in 1.7.

1. **A profile describes one kind of document:** how to recognise it, which
   pages need the page reader, how its tables are laid out, the prompt and
   the checks. Fields: `title`, `recognise`, `signals`, `ocr`, `tables`,
   `prompt`, `notes`, `role`, `applies_to`, `tooling`, `config`, `process`,
   `gates`, `on_fail`.
2. **Recognition is by shape, measured without reading:** page count, a
   text layer or not, image pages, landmarks (`recognise`, `signals`). A
   profile that matches on a phrase can never find a document with no text.
3. **Profiles come before readers.** A reading is made from a profile and
   is stamped with its slug and version.
4. **Added to, never rewritten.** A new version is a new line in
   `profiles.jsonl`, one higher than the highest held, read at write time;
   it says who made it and when. No line is ever edited, so a reading made
   under version 2 stays explicable after version 3.
5. **The current profile is the highest version,** by version and not by
   position in the file.
6. **A profile never carries a person's address or a suppressed name** as
   an example; the copy brought across had one such example replaced.

7. **A profile lists what it extracts** (Arthur, 3 November 2026). `extract` is
   a list of items: `field`, `iteration`, `by` (rules, pattern or model),
   `ask` (the instruction), `private` (an identifier, held in a `_private`
   schema and never published) and `kinds`. The profile's `iteration` is
   its highest item's. A new field, or a changed instruction for a field,
   is an item at the next iteration in a new version; no field is dropped
   and none goes back an iteration.
8. **A document records what it has had extracted.** `docs.extractions`
   holds one row per document, profile and field, with the iteration it
   was extracted at. A reader asks only for the items above that
   iteration (`support.profiles.wanted`), so an added field is read
   without reading the document again from the start.
