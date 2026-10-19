# charities: where the capture stands

Session charities-capture (Opus), 20 October 2026, node2. Capture half only.

## The four questions (full page: `registers/charities/position/charities-register.md`)

1. Open: yes. OData feed `www.odata.charities.govt.nz`, no login, read only;
   no challenge met; robots.txt 404 on both hosts, so no crawl delay is stated.
2. Lawful copying: the data is licensed CC BY 3.0 NZ (Crown copyright), so
   attribution is owed. The site's general copyright page is narrower; the
   lawyer confirms which one governs.
3. Terms: none clicked. Developer use is intended; a 1,000-row cap per query
   (honoured); emails must not be harvested for marketing (we don't, and don't show them).
4. Privacy / Act: ss 24-25 make officers and returns public, restricted data
   is left out of the feed, and officers' home addresses and birth dates are
   not published (no such field). Shown with care: disqualification flags, a small
   charity's address for service, emails and phones.

## Done

- `capture.py`: pages of 1,000 by key through the gate, landed verbatim by
  hash, listing `charities.capture_pages`, catch log `capture_set_aside`,
  resumable passes, changes by `ModifiedOn`, full copy every 28 days,
  off-peak, 5 s rest. `--measure`. `read.py`: listing and reconciliation
  (reconciles). 21 tests green.
- Register's own counts, 20 Oct ~07:30: 46,132 organisations, 29,265
  registered; 589,015 officer rows; 430,434 annual returns; 357 groups;
  0 related-party transactions.
- Proof landed (by day, 24 requests): 7 documents, 10 code lists, Groups
  whole (357), Organisations 2,000 of 46,132. 4 lines set aside (free-text
  lists over the cap, now paged by key).

## Half-done

- Organisations pass 20 at key 34584; every other keyed set not started.
  The job resumes it.

## Next

- Integrator: the job into the catalogue, the position into `docs/legal/`
  (cards). First full night (about 1,170 requests), then `--measure`.
- The two builds read through `read.pages(conn, set)`.
