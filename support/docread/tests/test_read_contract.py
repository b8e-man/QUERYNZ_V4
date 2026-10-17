"""The reader contract on a hand-built PDF: a page with a text layer is read
from text and stored; a blank page is thin and goes to the page reader
(faked), read from pixels; both replay from the store without a reader;
a page the reader cannot read is reported unread."""
import shutil

import pytest

from support import reader as rd
from support.docread import pagereader, pages
from support.docread.read import read_document

needs_poppler = pytest.mark.skipif(not shutil.which("pdftotext") or not shutil.which("pdfinfo"), reason="poppler absent")


def minimal_pdf(page_texts):
    """A valid PDF with one page per entry; an empty string is a blank page."""
    objs = []
    font = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    page_ids = []
    kids_index = 2
    n = 3
    contents = []
    for t in page_texts:
        stream = ""
        if t:
            lines = t.split("\n")
            stream = "BT /F1 12 Tf 50 750 Td " + " ".join(f"({l}) Tj 0 -16 Td" for l in lines) + " ET"
        contents.append(stream)
    # objects: 1 catalog, 2 pages, then per page: page obj, content obj; last: font
    font_id = 3 + 2 * len(page_texts)
    body = []
    for i, stream in enumerate(contents):
        pid, cid = 3 + 2 * i, 4 + 2 * i
        page_ids.append(pid)
        body.append((pid, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {cid} 0 R >>"))
        body.append((cid, f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream"))
    objs = [(1, "<< /Type /Catalog /Pages 2 0 R >>"),
            (2, f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in page_ids)}] /Count {len(page_ids)} >>")] + body + [(font_id, font)]
    out = b"%PDF-1.4\n"
    offsets = {}
    for oid, text in objs:
        offsets[oid] = len(out)
        out += f"{oid} 0 obj\n{text}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for oid in range(1, len(objs) + 1):
        out += f"{offsets[oid]:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


LONG = "Part A Donations exceeding five thousand dollars received by the party in the year\n" * 4


@needs_poppler
def test_a_text_page_is_read_from_text_and_stored(tmp_path):
    data = minimal_pdf([LONG])
    store = rd.Store(str(tmp_path / "store"))
    got = read_document(data, "a" * 64, profile="ec-party-return-text", profile_version=3, store=store)
    assert got.read_from == "text" and got.unread == [] and len(got.readings) == 1
    r = got.readings[0]
    assert r.read_from == "text" and "Part A Donations" in r.text and r.model == "text-layer" and r.profile_version == 3
    assert store.has(r.key)
    again = read_document(data, "a" * 64, profile="ec-party-return-text", profile_version=3, store=store)
    assert again.replayed == 1


@needs_poppler
def test_a_thin_page_goes_to_the_page_reader_and_is_read_from_pixels(tmp_path):
    data = minimal_pdf([LONG, ""])
    assert pages.read_from(data) == "mixed"
    store = rd.Store(str(tmp_path / "store"))
    calls = []

    def post(url, body, timeout):
        calls.append(url)
        return {"model": pagereader.MODEL, "choices": [{"message": {"content": "Schedule: 1  A Donor  $5,000"}}]}
    got = read_document(data, "b" * 64, profile="ec-party-return-scan", profile_version=4, store=store, page_reader=True, post=post)
    assert [r.read_from for r in got.readings] == ["text", "pixels"] and got.unread == []
    assert got.readings[1].model == "glm-ocr" and "A Donor" in got.readings[1].text and len(calls) == 1
    again = read_document(data, "b" * 64, profile="ec-party-return-scan", profile_version=4, store=store, page_reader=True, post=post)
    assert again.replayed == 2 and len(calls) == 1          # replayed, the reader was not called


@needs_poppler
def test_without_a_page_reader_the_thin_page_is_reported_unread(tmp_path):
    data = minimal_pdf(["", ""])
    assert pages.read_from(data) == "pixels"
    store = rd.Store(str(tmp_path / "store"))
    got = read_document(data, "c" * 64, profile="ec-party-return-scan", profile_version=4, store=store)
    assert got.readings == [] and got.unread == [1, 2]


def test_a_raster_is_one_page_read_from_pixels(tmp_path):
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 64
    assert pagereader.page_total(jpeg) == 1 and pages.text_pages(jpeg) == {1: ""} and pages.read_from(jpeg) == "pixels"
