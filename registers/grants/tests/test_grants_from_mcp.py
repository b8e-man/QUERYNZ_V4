"""The capture answered from the ingest MCP's copy (`--from-mcp`): the crawl is the MCP provider's (the 5 November
2026 split), so the walk asks the web, the gate and its holds for nothing, runs at any hour, and an address the copy
lacks is set aside without stopping the host. Every page here is invented; nothing is fetched."""
import datetime as dt
import hashlib
import types
import urllib.request

import pytest

from registers.grants import capture
from registers.grants.tests import fixtures
from registers.grants.tests.test_grants_capture import CM, FILE_PAGE_BODY, FILE_URL, INTERSTITIAL, FakeTables

DAY = dt.datetime(2026, 11, 14, 14, 0, tzinfo=capture.NZ)       # mid-afternoon: the web walk would not run
NH = "https://www.newhorizoncommunitytrust.co.nz"
NH_FILE = f"{NH}/wp-content/uploads/Grants-Approved-June-2024-May-2025.pdf"


def site():
    home = f'<html><a href="/lottery-fund/lottery-fund-grants-made">made</a><a href="/missing">m</a></html>'.encode()
    return {
        capture.FILE_PAGE: FILE_PAGE_BODY,
        FILE_URL: fixtures.dia_csv(),
        f"{CM}/": home,
        f"{CM}/lottery-fund/lottery-fund-grants-made": fixtures.lottery_page(),
        f"{NH}/approved-grants": f'<html><a href="{NH_FILE}">Grants approved 2024</a></html>'.encode(),
        NH_FILE: b"%PDF-1.4 invented",
    }


class Files:
    """mcpsource.files as the replay asks it: each address the copy holds answers with itself as its hash."""

    def __init__(self, pages, corpus="estate-grants"):
        self.pages, self.corpus, self.asked = pages, corpus, []

    def execute(self, sql, params):
        url, corpora = params
        self.asked.append(url)
        held = self.corpus in corpora and url in self.pages
        return types.SimpleNamespace(fetchone=lambda: (url,) if held else None)


@pytest.fixture(autouse=True)
def _no_web(monkeypatch, tmp_path):
    """Any ask of the web, of the gate's decision or of its holds fails the test."""
    def web(*a, **k):
        raise AssertionError("asked the web or the gate")
    monkeypatch.setattr(capture, "fetch_once", web)
    monkeypatch.setattr(urllib.request, "urlopen", web)
    monkeypatch.setattr(urllib.request, "build_opener", web)
    monkeypatch.setattr(capture.fg, "check", web)
    monkeypatch.setattr(capture.fg, "refused_by", web)
    monkeypatch.setattr(capture.fg, "hold", web)


def _land(data, *, name, source, name_kind):
    return types.SimpleNamespace(sha256=hashlib.sha256(data).hexdigest()), True


def _run(files, pages, lists=capture.LISTS, societies=("new-horizon-community-trust",)):
    t = FakeTables()
    kw = capture.from_mcp(files, read_bytes=lambda sha: pages[sha])
    run = capture.Run(t, land_fn=_land, now=lambda: DAY, lists=lists, societies=societies, log=lambda *a: None, **kw)
    return t, run.run()


def test_every_list_is_answered_from_the_copy_by_day_and_never_asks_the_web():
    pages = site()
    files = Files(pages)
    t, out = _run(files, pages)
    landed = {(d["list"], d["url"]) for d in t.docs}
    assert ("dia-file", FILE_URL) in landed and ("society-file", NH_FILE) in landed
    assert ("lottery-page", f"{CM}/lottery-fund/lottery-fund-grants-made") in landed
    assert out["records_of_grants"] == 1 and not out["blocked_hosts"]
    assert set(files.asked) >= set(pages)          # every address was asked of the copy, none of the web


def test_addresses_the_copy_lacks_are_set_aside_and_never_stop_the_host():
    pages = site()
    home = "".join(f'<a href="/gap-{i}">g</a>' for i in range(6)) + '<a href="/lottery-fund/lottery-fund-grants-made">m</a>'
    pages[f"{CM}/"] = f"<html>{home}</html>".encode()
    t, out = _run(Files(pages), pages, lists=("lottery-page",))
    assert not out["blocked_hosts"] and out["records_of_grants"] == 1
    assert sum("not in the MCP's copy" in r for _, _, r in t.asides) == 6
    assert capture.outcome(out)[0]


def test_a_copy_that_is_a_challenge_page_stops_the_host_for_the_run_and_holds_nothing():
    pages = site()
    pages[f"{CM}/"] = INTERSTITIAL
    t, out = _run(Files(pages), pages, lists=("lottery-page",))     # fg.hold would fail the test
    assert out["blocked_hosts"] == [capture.CM_HOST] and not t.docs
    assert t.asides and "challenge" in t.asides[0][2]


def test_another_corpus_s_copy_does_not_answer():
    pages = site()
    t, out = _run(Files(pages, corpus="estate-fma"), pages)
    assert not t.docs



def test_a_page_the_copy_keeps_with_a_trailing_slash_answers_its_canonical_address():
    # the provider keeps Air Rescue's, Trust Aoraki's and New Horizon's grants pages at the address with a slash; the
    # walk asks the canonical one, without (a dry run on the copy of 14 November 2026 missed their 76 files)
    pages = site()
    pages[f"{NH}/approved-grants/"] = pages.pop(f"{NH}/approved-grants")
    t, out = _run(Files(pages), pages, lists=("society-file",))
    assert [d["url"] for d in t.docs if d["list"] == "society-file"] == [NH_FILE] and not t.asides
