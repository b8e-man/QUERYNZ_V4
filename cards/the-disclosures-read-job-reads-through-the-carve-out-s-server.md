# The disclosures read job reads through the carve-out's server
kind: finding
state: open
use-case: 1
session: founding
opened: 2026-10-20

`qv4-disclosures-read` (queue row 97, 246 pieces, 19 October 21:18 to
21:20) held the page-reader profile on card 1, but its pieces sent every
page to the page reader's default address, port 8032: the carve-out's own
GLM-OCR server on card 0 (`support/docread/pagereader.py`, `URL`), the one
the old `ec-disclosures` job needs at 03:30. The readings are good (same
weights, same prompt, same dots) and are stored under the right stamp;
nothing on card 0 was stopped or changed. But the reservation on card 0
is fixed and the scheduler's card sat idle while the carve-out did the
work (hard limit 25; step 2.9).

Cause: `registers.disclosures.read.read_scan` calls `read_document`
without the worker's `QV4_MODEL_URL` and `QV4_MODEL`, and until today
`read_document` could not pass them on.

Fix: `read_document` now takes `url` and `model` (founding, 20 October);
`qv4-read-pages` passes the worker's. The disclosures lane's `read_scan`
and `main` should do the same (session 2's brief). Until then the job is
not queued again.
