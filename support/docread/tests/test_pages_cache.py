"""The text-layer cache (support.docread.pages.text_pages_cached, 11 November 2026): a file is extracted once and
replayed by its hash; another tool's entry, a corrupt entry and a hash that is not the bytes' are never trusted."""
import gzip
import hashlib
import json

from support.docread import pages
from support.docread.tests.test_read_contract import minimal_pdf, needs_poppler


def _counting(monkeypatch):
    calls = []
    real = pages.page_text
    monkeypatch.setattr(pages, "page_text", lambda d, p: calls.append(p) or real(d, p))
    return calls


@needs_poppler
def test_a_file_is_extracted_once_and_replayed_by_its_hash(tmp_path, monkeypatch):
    data = minimal_pdf(["The first page of a judgment, long enough to be a text layer and not a scan at all here.", ""])
    sha = hashlib.sha256(data).hexdigest()
    calls = _counting(monkeypatch)
    first = pages.text_pages_cached(data, sha, cache=str(tmp_path), workers=1)
    assert first == pages.text_pages(data, workers=1) and "first page" in first[1] and first[2].strip() == ""
    n = len(calls)
    assert pages.text_pages_cached(data, sha, cache=str(tmp_path), workers=1) == first
    assert len(calls) == n                                            # replayed: pdftotext not run again


@needs_poppler
def test_an_entry_of_another_tool_or_corrupt_is_read_again(tmp_path, monkeypatch):
    data = minimal_pdf(["A page with a text layer that is long enough to count as text and not as an image page."])
    sha = hashlib.sha256(data).hexdigest()
    path = pages._cache_path(sha, str(tmp_path))
    pages.text_pages_cached(data, sha, cache=str(tmp_path), workers=1)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump({"sha256": sha, "tool": "pdftotext 0.1", "pages": {"1": "stale words"}}, f)
    assert "stale" not in pages.text_pages_cached(data, sha, cache=str(tmp_path), workers=1)[1]
    with open(path, "wb") as f:
        f.write(b"not gzip")
    assert "long enough" in pages.text_pages_cached(data, sha, cache=str(tmp_path), workers=1)[1]


@needs_poppler
def test_bytes_that_are_not_the_named_file_are_read_but_never_filed(tmp_path):
    data = minimal_pdf(["Another page with a text layer long enough to be counted as a text page in this test."])
    wrong = "0" * 64
    assert "Another page" in pages.text_pages_cached(data, wrong, cache=str(tmp_path), workers=1)[1]
    assert not list(tmp_path.rglob("*.json.gz"))
