# party-returns: where it stands

**Date:** 2026-10-19. **Step:** 4.1, the party donation and loan returns
lane, `registers/party_returns/`. **Merge request:** `party-returns-1`.

## Done

- Tranche 1, the declaration from pixels. Image pages are replayed from
  the page reader's stored readings (GLM-OCR Q8_0, 300 dots, `OCR`); no
  model is called. `pixels.py` reads the page reader's one-line figures
  and takes the year from the loans page's balance date. Over the 152
  landed returns: 99 rows (32 before; 34 text, 65 pixels), 49 party-years
  equal to the frozen site (23 before), none differing. Column
  `year_from` added (live table gains it by `ADD COLUMN IF NOT EXISTS`;
  the view takes it last).

## Set aside, carded

- 41 returns at stage `read`: image pages with no stored reading, 18 in
  the window (`cards/forty-one-party-returns-…`). Needs a page-reader job.
- 7 pixel returns at the declaration page (`cards/seven-pixel-read-…`).
- 27 unresolved party labels (`cards/twenty-seven-party-labels-…`).

## Next

1. Tranche 2: Part A donor rows from the stored readings
   (`support.docread.parse`, `invariants`), each row reconciled to its
   part's printed total; the donor's address into `party_returns_private`
   only (hard limit 15). Then loans (Part H), then amendments (which
   return a later filing replaces, as the Commission states it).
2. The outside check against the Commission's own by-year table once a
   lane captures it (trial keys hold 89 of its figures; not a capture).
