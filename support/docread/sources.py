"""Where a stored document's bytes are — in whatever format it was captured.

C308 (2026-10-09). THREE COPIES OF ONE LINE EXCLUDED THE CLASS THAT MOST NEEDS
READING. `find_pdf(stem)` globbed `STAGING.rglob(f"{stem}.pdf")` and its callers
kept only what it found, in `docread.corpus`, `docread.review` and
`ops/donor_pairing_audit.py` — the same restriction stated three times and argued
nowhere. Measured over the whole staging tree: of 3,597 documents with a stored
read, **11 have no PDF at all and are held only as `.jpg`** — every one of them a
DISCLOSURE, and photographed forms are exactly the readings in dispute (C308's
no-address rows and C544's sub-threshold rows name 12 and 10 documents, 7 shared).
A finder named for one format cannot report what it excluded, so nothing did.

THE NAME IS THE FIX. `find_document` says what it finds; a caller that wants a
PDF specifically has to say so, and none of the three did.
"""
from __future__ import annotations

import pathlib

import os
# the old estate's captured returns, read-only (plan 1.10, case 1); the new
# document store takes over as lanes land their copies by hash
OLD_LIVE = pathlib.Path(os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3")
STAGING = OLD_LIVE / "var/staging/ec-donations"

#: The formats a stored document can be, in the order a reader prefers them.
#: A PDF first because it carries page structure and crops at render
#: resolution; a raster after, because for a photographed form it is not a
#: lesser copy — it is the document. Order is preference, never permission:
#: every one of these is readable, and `.json` (the stored READ) is not a
#: document and is deliberately absent.
READABLE: tuple[str, ...] = (".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")

#: The rasters among them: no page structure, exactly one page, and nothing
#: for `pdfinfo` or `pdftoppm` to open.
RASTER: frozenset[str] = frozenset(READABLE[1:])


def find_document(stem: str) -> pathlib.Path | None:
    """The stored document for `stem`, preferring a PDF — or None.

    One walk of the tree per call, as the three `rglob` copies did, and the
    PREFERENCE is applied over everything found rather than by globbing the
    extensions in order: globbing `.pdf` first and returning early is how the
    raster class became invisible, and a loop that can only find what it was
    told to look for cannot say what else was there.
    """
    hits = [p for p in STAGING.rglob(f"{stem}.*")
            if p.is_file() and p.suffix.lower() in READABLE]
    if not hits:
        return None
    return min(hits, key=lambda p: (READABLE.index(p.suffix.lower()), str(p)))


def is_raster(path: pathlib.Path | str) -> bool:
    """A document with no page structure — one page, and PDF tools cannot open it."""
    return pathlib.Path(path).suffix.lower() in RASTER
