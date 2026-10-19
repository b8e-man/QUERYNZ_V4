"""`qv4-read-pages`: every image page of one document through the page
reader on the card the worker holds, stored under the stamp the lane
replays. `qv4-reread-pages` reads one page per document and left the
party-returns lane 645 image pages short (card
`forty-one-party-returns-have-image-pages-with-no-stored-page-reading`)."""
import json

from support import reader as rd
from support.docread import pagereader, read as docread
from support.scheduler import registry as reg
from support.scheduler import reread

SHA = "ab" * 32
URL = "http://127.0.0.1:8140/v1/chat/completions"


def _fake_reader(monkeypatch, tmp_path, calls):
    monkeypatch.setattr(reread.landing, "read_bytes", lambda sha: b"%PDF-1.4 fake")
    monkeypatch.setattr(docread.pages, "text_pages", lambda data, max_pages=None: {1: "typed " * 400, 2: "", 3: ""})
    monkeypatch.setattr(docread.pages, "read_from", lambda data, texts=None: "mixed")
    monkeypatch.setattr(reread.doc_profiles, "profile", lambda slug: {"slug": slug, "version": 3})

    def render(data, page, tmpdir, dpi=None):
        png = tmp_path / f"p{page}.png"
        png.write_bytes(b"\x89PNG fake")
        return str(png)

    def post(url, body, timeout):
        calls.append((url, body["model"]))
        return {"model": body["model"], "choices": [{"message": {"content": "Part A  A Donor  $5,000"}}]}
    monkeypatch.setattr(pagereader, "render", render)
    return post


def test_every_image_page_is_read_on_the_workers_card_and_stored_under_the_lanes_stamp(tmp_path, monkeypatch):
    # the party-returns lane's second stamp, model and profile (`registers/party_returns/read.py`, PAGE_SETTINGS[1]);
    # a lane test holds that end, this one holds this end: support never imports a lane
    PROFILE, PAGE_MODEL, STAMP = "ec-party-return-text", "glm-ocr", {"dpi": 300, "prompt": "OCR"}
    store, calls = rd.Store(str(tmp_path / "store")), []
    post = _fake_reader(monkeypatch, tmp_path, calls)
    line = reread.read_pages(SHA, profile=PROFILE, url=URL, model="glm-ocr", store=store, post=post,
                             ledger=str(tmp_path / "rereads.jsonl"), run_id="r1")
    assert line["pages"] == 3 and line["images"] == 2 and line["read_now"] == 3 and line["replayed"] == 0 and line["unread"] == []
    assert calls == [(URL, "glm-ocr")] * 2, "the reader on the worker's card, never the page reader's default server"
    for page in (2, 3):
        key = rd.reading_key(SHA, page, PAGE_MODEL, STAMP, PROFILE, 3)
        assert store.has(key), "stored under the stamp the party-returns lane replays"
        assert store.get(key).read_from == "pixels"
    again = reread.read_pages(SHA, profile=PROFILE, url=URL, model="glm-ocr", store=store, post=post,
                              ledger=str(tmp_path / "rereads.jsonl"))
    assert again["read_now"] == 0 and again["replayed"] == 3 and len(calls) == 2, "a stored page is never read twice"
    ledger = open(tmp_path / "rereads.jsonl", encoding="utf-8").read()
    rec = json.loads(ledger.splitlines()[0])
    assert rec["document"] == SHA and rec["run_id"] == "r1" and rec["read_from"] == "pages"
    assert "Donor" not in ledger and "typed" not in ledger, "no page text in the ledger"
    assert reread.summary(str(tmp_path / "rereads.jsonl"))["glm-ocr"]["pages"] == 3


def test_the_catalogue_entry_names_a_profile_the_ledger_knows():
    from support import profiles
    jt = reg.load()["qv4-read-pages"]
    assert jt.profile == "page-reader" and jt.pieces and jt.command[3] == "read-pages"
    assert profiles.profile(jt.command[-1]) is not None, "the stamp's document profile must exist"
