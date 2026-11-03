"""Scanned minutes (profile council-minutes-scanned v1): recognised by shape, never by a phrase, both ways; every page
through the page reader once, stored and replayed; the page reader's text tidied and then read by the same rules, the
two skips first; the load waits for a scan's unread pages and reads it once they are stored; the text reader's pieces
of a scan never share a key with a text layer's. The invented half needs no PDF; the real half rasterises real landed
minutes (sample.list) into image-only PDFs, so the shape test and the skips can fail on real documents. No model is
called: the page reader's answer is stood in by the original's own text with its columns collapsed, as the page reader
prints them."""
import os
import re
import shutil
import subprocess
import tempfile

import pytest

from support import reader as rd
from support.docread import pages, pagereader
from registers.council_minutes import load, minutes as M, model_read as MR, scans as SC

SHA = "c4" * 32

#: the invented minutes as the page reader prints them: one space where the text layer kept a column, markdown marks,
#: an HTML table, a public forum item and a public-excluded item in title case
OCR = {1: """## INVENTED DISTRICT COUNCIL
**Minutes** of a meeting of the Invented District Council held on 22 October 2026

PRESENT: Cr A Example (Chairperson), Cr B Sample, Cr D Notreal

1. KARAKIA

2. Public Forum
Hemi Speaker spoke about the Invented Road footpath.

3. REPORTS
<table><tr><td>RESOLUTION 2026/3</td></tr></table>
Moved: Cr Notreal
Seconded: Cr Example
That the report be received.
CARRIED
""", 2: """4. Resolution to exclude the public
RESOLUTION 2026/4
Moved: Cr Example
Seconded: Cr Sample
That the public be excluded.
CARRIED
4.1 SECRET PERSON EMPLOYMENT
That Secret Person be paid.
The public were re-admitted at 11.05 am.

5. CLOSING
RESOLUTION 2026/5
Moved: Cr Sample
Seconded: Cr Example
That the meeting be closed.
CARRIED
"""}


def test_the_scanned_profile_is_proposed_and_recognises_by_shape_alone():
    from support import profiles
    p = profiles.profile(M.SCANNED, path=SC.PROPOSED)
    assert p and p["version"] >= 1 and p["role"] == "read" and p["config"]["dpi"] == SC.DPI
    assert "shape" in p["recognise"]["by"] and "never a phrase" in p["recognise"]["by"]
    assert SC.profile_version() >= 1


def test_scan_shape_both_ways():
    assert M.scan_shape(b"%PDF-1.7", "pixels", 3, {1, 2, 3}) == (M.SCANNED, "")
    assert M.scan_shape(b"%PDF-1.7", "pixels", 4, {1, 2}) == (M.SCANNED, ""), "half the pages a picture is a scan"
    assert M.scan_shape(b"%PDF-1.7", "pixels", 5, {1, 2}) == ("", M.NOT_A_SCAN)
    assert M.scan_shape(b"%PDF-1.7", "pixels", 2, set()) == ("", M.NOT_A_SCAN), "no text and no image: not a scan"
    assert M.scan_shape(b"%PDF-1.7", "text", 3, {1, 2, 3})[0] == "", "a text layer is never a scan, pictures or not"
    assert M.scan_shape(b"%PDF-1.7", "mixed", 3, {1, 2, 3})[0] == ""
    assert M.scan_shape(b"<html>", "pixels", 1, {1}) == ("", "not a PDF")


def test_the_page_reader_s_text_is_tidied_into_the_shape_the_rules_read():
    t = {p: M.from_pages(x) for p, x in OCR.items()}
    lines = [l for _p, l in M.lines_of(t)]
    assert "2  PUBLIC FORUM" in lines and "4  RESOLUTION TO EXCLUDE THE PUBLIC" in lines and "1  KARAKIA" in lines
    assert "RESOLUTION 2026/3" in lines and not any("<" in l or "**" in l or l.startswith("#") for l in lines)
    kept, skipped = M.sections(t)
    text = "\n".join(l for _p, l in kept)
    assert "Hemi Speaker" not in text and "Secret Person" not in text and "That the meeting be closed." in text
    assert skipped["public forum items"] == 1 and skipped["public excluded parts"] == 1
    assert M.recognise(t, "text") == (M.STANDARD, "")
    res = M.read_standard(t)["resolutions"]
    assert [r["number"] for r in res if r["part"] == M.OPEN] == ["2026/3", "2026/5"]
    assert [r["part"] for r in res if r["part"] != M.OPEN] == [M.EXCLUDED], "the excluded part read, flagged (ruling 142)"
    # without the tidy the page reader's single-spaced headings are no items, and the forum would be read
    raw_kept, raw_skipped = M.sections(OCR)
    assert raw_skipped.get("public forum items", 0) == 0 and "Hemi Speaker" in "\n".join(l for _p, l in raw_kept)


@pytest.fixture
def scan(monkeypatch):
    """A two-page scan without a PDF: no text layer, both pages pictures."""
    monkeypatch.setattr(pages, "text_pages", lambda data, *a, **k: {1: "", 2: " "})
    monkeypatch.setattr(M, "picture_pages", lambda data: {1, 2})
    return rd.Store(tempfile.mkdtemp())


def _store_pages(store, sha, texts):
    for p, t in texts.items():
        store.put(rd.Reading(sha, p, "test", pagereader.MODEL, {"dpi": SC.DPI, "prompt": pagereader.PROMPT}, SC.PROFILE,
                             SC.profile_version(), "pixels", t))


def test_every_page_goes_through_the_page_reader_once(scan, monkeypatch):
    calls = []

    def ocr(data, want, dpi=None, **k):
        calls.append((tuple(want), dpi))
        return {p: OCR[p] for p in want}
    monkeypatch.setattr(pagereader, "ocr_pages", ocr)
    got = SC.read_pages(SHA, data=b"%PDF-1.7 scan", store=scan)
    assert got["state"] == "read" and got["read_now"] == 2 and calls == [((1, 2), SC.DPI)]
    again = SC.read_pages(SHA, data=b"%PDF-1.7 scan", store=scan)
    assert again["replayed"] == 2 and again["read_now"] == 0 and len(calls) == 1, "a stored page is never read again"
    texts, unread = SC.texts(SHA, b"%PDF-1.7 scan", scan)
    assert unread == [] and "2  PUBLIC FORUM" in texts[1]
    monkeypatch.setattr(M, "picture_pages", lambda data: set())
    assert SC.read_pages("d5" * 32, data=b"%PDF-1.7 blank", store=scan)["state"] == M.NOT_A_SCAN


def test_the_load_waits_for_a_scan_s_pages_then_reads_it_with_the_skips(scan, monkeypatch):
    monkeypatch.setattr(load, "standard_version", lambda: 1)
    meetings = {"k": {"key": "k", "council": "Invented District Council", "body": "Council", "meeting_date": "2026-10-22",
                      "minutes_sha256": SHA, "minutes_held": "landed"}}
    captured = {"https://invented/1.PDF": ("landed", SHA)}
    read = lambda: load.read_minutes(meetings, captured, read_bytes=lambda s: b"%PDF-1.7 scan", store=scan)
    _store_pages(scan, SHA, {1: OCR[1]})
    first = read()["minutes_read"][0]
    assert first["state"] == M.WAIT_PAGES and first["unread_pages"] == "2" and first["read_from"] == "pixels"
    assert first["profile"] == M.SCANNED
    _store_pages(scan, SHA, {2: OCR[2]})
    out = read()
    line = out["minutes_read"][0]
    assert line["state"] == "read" and line["profile"] == M.STANDARD and line["read_from"] == "pixels"
    assert line["excluded_parts"] == 1 and line["forum_items"] == 1 and line["resolutions"] == 3
    assert {r["read_from"] for t in ("attendance", "resolutions") for r in out[t]} == {"pixels"}
    assert not any("Secret Person" in (r["text"] or "") for r in out["resolutions"] if r["part"] == M.OPEN)
    assert any("Secret Person" in x["text"] for x in out["part_lines"] if x["part"] == M.EXCLUDED)


def test_a_scan_s_text_reader_pieces_wait_for_its_pages_and_never_share_a_layer_s_key(scan):
    other = {1: OCR[1].replace("RESOLUTION 2026/3", "Resolved"), 2: "Closed.\n"}
    texts, source, why = MR.texts_for(SHA, b"%PDF-1.7 scan", scan)
    assert texts is None and why == M.WAIT_PAGES
    _store_pages(scan, SHA, other)
    texts, source, why = MR.texts_for(SHA, b"%PDF-1.7 scan", scan)
    assert why == "" and source == SC.SOURCE and set(texts) == {1, 2}
    assert MR.key_for(SHA, 1, 1, source=source) != MR.key_for(SHA, 1, 1)
    assert MR.settings() == MR.settings(source=None), "a text layer's keys are as they were"
    assert MR.replay(SHA, b"%PDF-1.7 scan", version=1, store=scan, texts=texts, source=source)["state"] == MR.WAIT_TEXT


# ── real landed minutes, rasterised ─────────────────────────────────────────────────────────────────────────────
#: from sample.list: Western Bay of Plenty (standard, a public forum item and two public-excluded parts), Central
#: Otago (standard, one public-excluded part), Carterton (another shape, one public-excluded part)
REAL = ("147a9e274699ebc1dc1123684a950a4cff165e49be8c98df928e7e21371eeed5",
        "3b2235a2968ec014e7abd632f54d9f3f2401d895f7b1b26b9ca32e9894c8901f",
        "adaa699eb6013b13701567a0a22c86dbe12c4a21df6ae38f1b7a2dcb02bcb68c")


def _real_or_skip(sha):
    from support.docstore.landing import path_for, read_bytes
    if not os.path.exists(path_for(sha)) or not (shutil.which("pdftoppm") and shutil.which("magick")):
        pytest.skip("the document store or pdftoppm/magick is not on this box")
    return read_bytes(sha)


def _rasterise(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.pdf")
        open(src, "wb").write(data)
        subprocess.run(["pdftoppm", "-r", "40", "-gray", "-png", src, os.path.join(td, "p")], check=True, timeout=60)
        pngs = sorted(f for f in os.listdir(td) if f.endswith(".png"))
        subprocess.run(["magick", *[os.path.join(td, f) for f in pngs], os.path.join(td, "out.pdf")], check=True, timeout=60)
        return open(os.path.join(td, "out.pdf"), "rb").read()


def _as_the_page_reader_prints(text: str) -> str:
    """The original's text as the page reader gives it: no column gaps, no indent."""
    return "\n".join(re.sub(r"\s{2,}", " ", l).strip() for l in (text or "").splitlines())


@pytest.mark.slow
@pytest.mark.parametrize("sha", REAL)
def test_real_minutes_rasterised_are_a_scan_by_shape_and_read_by_the_same_rules(sha):
    data = _real_or_skip(sha)
    layer = pages.text_pages(data)
    assert SC.recognise(data, layer)[0] == "", "a real text layer is never a scan"
    prof_text, _ = M.recognise(layer, pages.read_from(data, layer))
    assert prof_text in (M.STANDARD, M.TEXT)
    scan = _rasterise(data)
    scan_sha = __import__("hashlib").sha256(scan).hexdigest()
    scan_layer = pages.text_pages(scan)
    assert pages.read_from(scan, scan_layer) == "pixels" and len(scan_layer) == len(layer)
    assert SC.recognise(scan, scan_layer) == (M.SCANNED, ""), "an image-only copy is a scan by its shape"
    assert M.recognise(scan_layer, "pixels") == ("", M.WAIT_PAGES), "a scan is never read from its own layer"
    store = rd.Store(tempfile.mkdtemp())
    _store_pages(store, scan_sha, {p: _as_the_page_reader_prints(t) for p, t in layer.items()})
    texts, unread = SC.texts(scan_sha, scan, store, layer=scan_layer)
    assert unread == []
    k0, want = M.sections(layer)
    k1, got = M.sections(texts)
    for k in ("public excluded parts", "public forum items"):
        assert got.get(k, 0) == want.get(k, 0), f"{k}: {got.get(k, 0)} on the page reader's text, {want.get(k, 0)} on the layer"
    norm = lambda l: " ".join(l.split())
    leaked = {norm(l) for _p, l in k1} - {norm(l) for _p, l in k0}
    assert not leaked, f"{len(leaked)} line(s) the layer's skips drop are kept from the page reader's text"
    assert M.recognise(texts, "text")[0] == prof_text
    if prof_text == M.STANDARD:
        assert [r["number"] for r in M.read_standard(texts)["resolutions"]] == \
            [r["number"] for r in M.read_standard(layer)["resolutions"]]
