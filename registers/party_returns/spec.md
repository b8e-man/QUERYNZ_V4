owns: schema `party_returns` (`returns`, `set_aside`); `party_returns_private` holds nothing yet (the lane reads declaration pages, which carry no home address)
reads: the document store (`docs`); the old folder's `var/staging/ec-donations/archive/` and `residue/party_returns/`, read-only, copied by hash (case 1 of 1.10); the profiles `ec-party-return-text`, `-scan` and `-image-declaration`; the page reader's stored readings in the reader store (GLM-OCR, replayed, never called); `keys.parties`
publishes: `pub.party_return_totals`, one row per return read: party, year, the declared total and its parts as printed, the document and page, text or pixels, and where the year was read
outside check: each party-year's declared total against the figure the frozen site shows (`check.py`, from the current release's home.json); the Commission's own listing when a fetch lane exists
jobs: none yet; loaded by the merge gate's staging step. A `qv4-party-returns-load` job comes with step 2's scheduler
