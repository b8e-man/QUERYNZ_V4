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
