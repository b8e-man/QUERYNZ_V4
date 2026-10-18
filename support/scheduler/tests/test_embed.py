"""The embed piece: chunks that fit the request, one reading per page
keyed by document, model and settings, replayed when stored, thin pages
skipped, the ledger without the text."""
from __future__ import annotations

import json

import pytest

from support import reader as rd
from support.scheduler import embed


def test_chunks_cover_the_text_with_an_overlap_and_know_their_offsets():
    text = "a" * 100 + "b" * 100 + "c" * 50
    cs = embed.chunks(text, size=100, overlap=20)
    assert [c["offset"] for c in cs] == [0, 80, 160]
    assert cs[0]["text"] == "a" * 100 and cs[1]["text"] == "a" * 20 + "b" * 80 and cs[-1]["text"] == "b" * 40 + "c" * 50
    assert "".join(c["text"][20 if i else 0:] for i, c in enumerate(cs)) == text, "nothing lost between windows"
    assert embed.chunks("   ") == [] and len(embed.chunks("short")) == 1


def test_a_piece_stores_one_reading_per_page_and_replays_it_next_time(tmp_path, monkeypatch):
    store = rd.Store(str(tmp_path / "store"))
    calls = []

    def fake_embed(url, *, lane, model, texts):
        calls.append((url, lane, model, len(texts)))
        return [[0.5, float(i)] for i, _ in enumerate(texts)]
    monkeypatch.setattr(embed.pages, "text_pages", lambda data, max_pages=None: {1: "the first page " * 200, 2: "", 3: "third " * 50})
    line = embed.piece("ab" * 32, url="http://127.0.0.1:8111/v1/embeddings", model="bge-m3-q8", store=store, embed=fake_embed,
                       ledger=str(tmp_path / "embeds.jsonl"), data=b"%PDF", run_id="r1")
    assert line["embedded"] == 2 and line["thin"] == 1 and line["replayed"] == 0 and line["dims"] == 2
    assert [c[1:] for c in calls] == [("search", "bge-m3-q8", 3), ("search", "bge-m3-q8", 1)]
    key = rd.reading_key("ab" * 32, 1, "bge-m3-q8", {"chunk_chars": 1500, "overlap_chars": 200, "reader": embed.READER}, "embedding", 0)
    r = store.get(key)
    assert r.model == "bge-m3-q8" and r.read_from == "text" and len(r.rows) == 3 and r.rows[1]["offset"] == 1300
    assert r.rows[0]["vector"] == [0.5, 0.0] and r.checks == {"chunks": 3, "dims": 2}
    again = embed.piece("ab" * 32, url="u", model="bge-m3-q8", store=store, embed=fake_embed, ledger=str(tmp_path / "e.jsonl"), data=b"%PDF")
    assert again["embedded"] == 0 and again["replayed"] == 2 and len(calls) == 2, "a stored reading is never made twice"
    rec = json.loads(open(tmp_path / "embeds.jsonl").read().splitlines()[-1])
    assert rec["document"] == "ab" * 32 and rec["run_id"] == "r1" and "first page" not in open(tmp_path / "embeds.jsonl").read()


def test_without_the_clients_embed_the_piece_says_so(monkeypatch):
    import support.modelclient as mc
    monkeypatch.delattr(mc, "embed", raising=False)
    with pytest.raises(RuntimeError, match="no embed"):
        embed.embed_fn()
