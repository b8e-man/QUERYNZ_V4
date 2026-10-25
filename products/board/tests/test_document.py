"""The originating document (ruling 86 (4)), pure: /doc/<sha256> serves a
served source's bytes whole with their content type, refuses anything but
64 hex characters, reads nothing outside the store root, never lists it,
refuses a held document whose source may print a home address (hard limit
15), and every row's citation begins with its "source"."""
import hashlib
import os
import threading
import urllib.error
import urllib.request

import pytest

from products.board import catalogue as cat
from support.docstore import landing
from products.board import db, document, panes, server

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
SECRET = b"a home address, never to be served\n"


class Conn:
    """The store's records as support.docstore's reader answers them."""
    def __init__(self, documents, names=()):
        self.documents, self.names = documents, names

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_documents_of(shas, conn):
    want = set(shas)
    return {d[0]: {"kind": d[1], "source": d[2], "withdrawn": d[3]} for d in conn.documents if d[0] in want}


def fake_names_of(sha, conn):
    return [n for s, n in conn.names if s == sha]


@pytest.fixture(autouse=True)
def reader(monkeypatch):
    """landing.documents_of arrives with the patch board-4-docstore-read; faked here either way."""
    monkeypatch.setattr(landing, "documents_of", fake_documents_of, raising=False)
    monkeypatch.setattr(landing, "names_of", fake_names_of)


def sha(b):
    return hashlib.sha256(b).hexdigest()


@pytest.fixture
def store(tmp_path, monkeypatch):
    root = tmp_path / "store"
    for data in (PDF, SECRET):
        (root / sha(data)[:2]).mkdir(parents=True, exist_ok=True)
        (root / sha(data)[:2] / sha(data)).write_bytes(data)
    monkeypatch.setenv("QV4_DOCS", str(root))
    return root


def conn():
    return Conn([(sha(PDF), "pdf", "house", None), (sha(SECRET), "pdf", "party_returns", None),
                 ("e" * 64, "pdf", "house", "withdrawn: a test"), ("b" * 64, "pdf", "house", None)],
                [(sha(PDF), "list.pdf")])


def test_a_served_source_answers_its_bytes_whole_with_its_content_type(store):
    assert "party_returns" not in cat.SERVED_SOURCES and "house" in cat.SERVED_SOURCES
    status, ctype, body = document.fetch(conn(), sha(PDF))
    assert (status, ctype, body) == (200, "application/pdf", PDF)


def test_a_wrong_or_malformed_sha_a_withdrawn_or_absent_document_answers_404(store):
    c = conn()
    for bad in ("", "abc", sha(PDF).upper(), sha(PDF)[:63], sha(PDF) + "0", "../" + sha(PDF)[3:], "0" * 64, "e" * 64):
        assert document.fetch(c, bad)[0] == 404, bad
    assert document.fetch(c, "b" * 64)[0] == 404                      # in the table, not on the disk


def test_a_source_that_may_print_a_home_address_is_refused_and_its_bytes_never_read(store):
    status, ctype, body = document.fetch(conn(), sha(SECRET))
    assert status == 403 and SECRET.decode() not in body and "hard limit 15" in body


def test_nothing_outside_the_store_root_is_read(store, tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(PDF)
    fake = "c" * 64
    (store / "cc").mkdir()
    os.symlink(outside, store / "cc" / fake)                         # a name in the store that leads out of it
    assert document.path_in_store(fake) == ""
    assert document.path_in_store(sha(PDF)) == str((store / sha(PDF)[:2] / sha(PDF)).resolve())
    assert document.path_in_store("..") == "" and document.path_in_store(sha(PDF)[:2]) == ""


def test_bytes_that_do_not_hash_to_their_name_are_not_served(store):
    (store / sha(PDF)[:2] / sha(PDF)).write_bytes(PDF + b"x")
    assert document.fetch(conn(), sha(PDF))[0] == 404


def test_the_content_type_is_the_stored_kind_then_the_name_then_the_bytes():
    assert document.content_type("web-page") == "text/html; charset=utf-8"
    assert document.content_type("spreadsheet", ["q3.xlsx"]) == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert document.content_type("other", ["https://x/select?q=a&wt=json"]) == "application/json"
    assert document.content_type("other", [], b'  {"a": 1}') == "application/json"
    assert document.content_type("image", ["scan.PNG"]) == "image/png"
    assert document.content_type("other", [], b"\x00\x01") == "application/octet-stream"


def test_the_handler_serves_refuses_and_never_lists(store, monkeypatch):
    monkeypatch.setattr(db, "read_connect", conn)
    srv = server.Server(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def get(path):
        try:
            r = urllib.request.urlopen(base + path)
            return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read()
    try:
        status, headers, body = get(f"/doc/{sha(PDF)}")
        assert status == 200 and headers["Content-Type"] == "application/pdf" and body == PDF
        assert "sandbox" in headers["Content-Security-Policy"] and headers["X-Content-Type-Options"] == "nosniff"
        assert get("/doc/" + "1" * 64)[0] == 404
        assert get(f"/doc/{sha(SECRET)}")[0] == 403 and SECRET not in get(f"/doc/{sha(SECRET)}")[2]
        for listing in ("/doc", "/doc/", f"/doc/{sha(PDF)[:2]}", f"/doc/{sha(PDF)[:2]}/"):
            status, _, body = get(listing)
            assert status == 404 and sha(PDF).encode() not in body, listing
    finally:
        srv.shutdown()


def row(**kw):
    return {"key": "k1", "document": sha(PDF), **kw}


def test_every_citation_begins_with_its_source_at_its_page():
    v = cat.BY_NAME["candidates"]
    docs = {sha(PDF): {"state": document.SERVED, "kind": "pdf", "source": "house", "why": ""}}
    line = panes.citation_line(v, row(page=3), docs)
    assert line.startswith(f'<div class="cite"><a class="source" href="/doc/{sha(PDF)}#page=3">source</a>')
    pane = panes.citation(v, row(page=3), [], docs)
    assert pane.index(">source</a>") < pane.index("<th>document</th>")
    web = {sha(PDF): {"state": document.SERVED, "kind": "web-page", "source": "house", "why": ""}}
    assert f'href="/doc/{sha(PDF)}"' in panes.citation_line(v, row(page=3), web)       # no page on a web page


def test_a_document_not_held_or_not_opened_says_so_and_a_suppressed_row_offers_none():
    v = cat.BY_NAME["candidates"]
    assert "document not held here" in panes.citation_line(v, row(), {})
    assert "document not held here" in panes.citation_line(v, {"key": "k1"}, {})
    held = {sha(PDF): {"state": document.WITHHELD, "kind": "pdf", "source": "party_returns", "why": cat.WITHHELD_WHY}}
    line = panes.citation_line(v, row(), held)
    assert "/doc/" not in line and "not opened here" in line
    d = cat.BY_NAME["directors"]
    served = {sha(PDF): {"state": document.SERVED, "kind": "pdf", "source": "house", "why": ""}}
    hidden = panes.citation_line(d, row(full_name="X", suppressed=True), served)
    assert "/doc/" not in hidden and "source not opened" in hidden
    assert 'href="https://example.org/a"' in panes.citation_line(cat.BY_NAME["disclosures"], row(href="https://example.org/a"), held)


def test_without_the_store_s_reader_nothing_opens(store, monkeypatch):
    monkeypatch.delattr(landing, "documents_of")
    st = document.statuses(conn(), [sha(PDF)])[sha(PDF)]
    assert st["state"] == document.ABSENT and "documents_of" in st["why"]
    assert document.fetch(conn(), sha(PDF))[0] == 404


def test_the_board_never_queries_the_store_s_tables_itself():
    import inspect
    for mod in (document, server):
        assert "docs.documents" not in inspect.getsource(mod).replace("`docs.documents`", "")
