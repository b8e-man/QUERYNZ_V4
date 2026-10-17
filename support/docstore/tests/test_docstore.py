"""A document is its bytes: keyed by hash, names are attributes; a web page
also has a sameness hash that ignores what changes on every fetch."""
import pytest

import support.docstore as ds


def test_a_document_is_its_bytes_and_names_are_attributes():
    data = b"%PDF-1.4 the same return"
    a = ds.describe(data, "Act-Party-Annual-Return-2021.pdf", source="ec-donations")
    b = ds.describe(data, "dup-of-residue/ACT_2021.pdf", source="ec-donations")
    assert a.sha256 == b.sha256 == ds.sha256_bytes(data)
    assert a.names != b.names and a.kind == "pdf" and a.size == len(data)
    assert a.content_sha256 == ""       # not a web page


def test_a_web_page_has_a_sameness_hash_that_ignores_the_volatile_parts():
    page1 = b"<html><head><script nonce='a1'>x()</script><style>p{}</style></head><body><!-- 12:01 --><p>Hello &amp; welcome</p>  <div>Rows: 3</div></body></html>"
    page2 = b"<html><head><script nonce='b2'>y()</script></head><body><!-- 12:02 --><p>Hello &amp;   welcome</p><div>Rows: 3</div></body></html>"
    page3 = page2.replace(b"Rows: 3", b"Rows: 4")
    a, b, c = (ds.describe(p, "x.html") for p in (page1, page2, page3))
    assert a.kind == "web-page"
    assert a.sha256 != b.sha256                 # the bytes differ
    assert a.content_sha256 == b.content_sha256  # the page is the same
    assert a.content_sha256 != c.content_sha256  # a changed figure is a different page
    assert ds.canonical_text(page1.decode()) == "Hello & welcome Rows: 3"


def test_kinds_and_refusals():
    assert ds.kind_of("a.XLSX") == "spreadsheet" and ds.kind_of("a.jpg") == "image"
    assert ds.kind_of("x", "text/html; charset=utf-8") == "web-page" and ds.kind_of("x") == "other"
    with pytest.raises(ValueError):
        ds.DocumentRef("abc", 1, "pdf")
    with pytest.raises(ValueError):
        ds.DocumentRef("0" * 64, 1, "scroll")


def test_sha256_file_matches_bytes(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"bytes")
    assert ds.sha256_file(str(p)) == ds.sha256_bytes(b"bytes")
