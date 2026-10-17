"""The reader contract, implemented (plan 1.10; docs/contracts/reader.md).

    from support.docread.read import read_document
    readings = read_document(data, sha256, profile="ec-party-return-text", profile_version=3, store=store)

Per page: the text layer first (`pages.page_text`); for a page with no
usable layer, the page reader (`pagereader.ocr_pages`), when one is
allowed (`page_reader=True`); each page's reading stamped with the reader,
the model and its settings, the profile and version, and whether it read
text or pixels; stored by the document's hash in the reader store and
replayed from there, so the fast tier never calls a model. A page that
cannot be read is reported as unread, never returned empty: `unread` on
the result names its pages.
"""
import datetime as dt
from dataclasses import dataclass, field

from support import reader as rd
from support.docread import pagereader, pages

READER = "support.docread 1"
TEXT_MODEL = "text-layer"


@dataclass
class DocumentReading:
    document: str
    read_from: str                     # text | pixels | mixed
    readings: list = field(default_factory=list)
    unread: list = field(default_factory=list)
    replayed: int = 0

    @property
    def texts(self) -> dict:
        return {r.page: r.text for r in self.readings}


def read_document(data: bytes, sha256: str, *, profile: str, profile_version: int, store: rd.Store,
                  page_reader: bool = False, post=None, max_pages: int = None, dpi: int = None,
                  texts: dict = None) -> DocumentReading:
    """`texts` is the page → text-layer map when the caller has already
    measured it (a lane recognises a document by shape before it reads it);
    left out, it is extracted here."""
    texts = texts if texts is not None else pages.text_pages(data, max_pages)
    how = pages.read_from(data, texts)
    out = DocumentReading(sha256, how)
    thin = set(pages.thin_pages(texts))
    text_settings = {"tool": "pdftotext -layout"}
    pixel_settings = {"dpi": dpi or pagereader.DPI, "prompt": pagereader.PROMPT}
    want_pixels = []
    for p in sorted(texts):
        if p in thin:
            want_pixels.append(p)
            continue
        key = rd.reading_key(sha256, p, TEXT_MODEL, text_settings, profile, profile_version)
        if store.has(key):
            out.readings.append(store.get(key))
            out.replayed += 1
            continue
        r = rd.Reading(sha256, p, READER, TEXT_MODEL, text_settings, profile, profile_version, "text", texts[p],
                       made_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
        store.put(r)
        out.readings.append(r)
    need = []
    for p in want_pixels:
        key = rd.reading_key(sha256, p, pagereader.MODEL, pixel_settings, profile, profile_version)
        if store.has(key):
            out.readings.append(store.get(key))
            out.replayed += 1
        else:
            need.append(p)
    if need and page_reader:
        got = pagereader.ocr_pages(data, need, dpi=dpi, post=post)
        for p in need:
            if p in got:
                r = rd.Reading(sha256, p, READER, pagereader.MODEL, pixel_settings, profile, profile_version, "pixels",
                               got[p], made_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
                store.put(r)
                out.readings.append(r)
            else:
                out.unread.append(p)
    else:
        out.unread.extend(need)
    out.readings.sort(key=lambda r: r.page)
    return out
