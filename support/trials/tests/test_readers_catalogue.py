"""Every reader has its own documented prompt, a profile that serves it and a
job that runs it; the merged catalogue passes the registry's rules; a
piece stores readings keyed by hash, page, model, settings and profile."""
import json
import os

from support import reader as rd
from support.trials import catalogue, piece, readers, rows


def test_every_reader_is_documented_and_served():
    for r in readers.READERS.values():
        assert r.prompt and r.prompt_from and r.profile and r.model and len(r.weights) == 2
        assert r.family in ("zhipu", "qwen")
        if r.variant_of:
            assert readers.by_profile(r.profile, r.name) is r and readers.READERS[r.variant_of].profile == r.profile
            assert readers.by_profile(r.profile) is readers.READERS[r.variant_of]
        else:
            assert readers.by_profile(r.profile) is r
    assert readers.by_profile("page-reader", "ovisocr2") is None       # a variant must be served by the same profile
    assert readers.READERS["glm-ocr"].prompt == "OCR"
    assert set(readers.CHALLENGERS) <= set(readers.READERS)
    fams = {readers.READERS[c].family for c in readers.CHALLENGERS}
    assert fams == {"qwen"} and readers.READERS[readers.INCUMBENT].family == "zhipu"


def test_settings_tell_readers_apart_and_carry_no_long_prompt():
    a = readers.settings(readers.READERS["glm-ocr"], 200)
    b = readers.settings(readers.READERS["glm-ocr"], 300)
    c = readers.settings(readers.READERS["chandra-ocr-2"], 300)
    assert rd.settings_hash(a) != rd.settings_hash(b) != rd.settings_hash(c)
    assert a["prompt"] == "OCR" and c["prompt"] is None and c["prompt_sha"]


def test_messages_follow_each_models_own_example():
    r = readers.READERS["teleocr"]
    m = readers.messages(r, "AAAA", "image/png")
    assert m[0]["role"] == "system" and m[1]["content"][0]["type"] == "image_url"
    g = readers.messages(readers.READERS["glm-ocr"], "AAAA", "image/png")
    assert g[0]["role"] == "user" and g[0]["content"][0] == {"type": "text", "text": "OCR"}
    assert readers.extra(readers.READERS["ovisocr2"])["chat_template_kwargs"] == {"enable_thinking": False}
    assert "chat_template_kwargs" not in readers.extra(readers.READERS["glm-ocr"])


def test_the_merged_catalogue_passes():
    assert catalogue.problems() == []
    jp, pp = catalogue.merged()
    j, p = open(jp, encoding="utf-8").read(), open(pp, encoding="utf-8").read()
    assert "[profiles.trial-ovisocr2]" in p and "[jobs.qv4-trial-read-glm-ocr]" in j
    assert "qv4-trial-urgent-page" in j and 'class = "waiting"' in j
    # Before the integrator applies the additions the patch carries them; once
    # the shipped catalogue holds them (18 October) the patch is empty.
    patch = catalogue.patch()
    assert patch == "" or "+[profiles.trial-ovisocr2]" in patch


def test_a_piece_stores_a_reading_by_hash_page_model_settings_and_profile(tmp_path, monkeypatch):
    from support.trials import pageset
    doc = next(d for d in pageset.load() if d["shape"] == "scan" and d["kind"] == "party-return")
    store = rd.Store(str(tmp_path / "readings"))
    calls = []

    def post(url, body, timeout):
        calls.append(body)
        return {"model": body["model"], "choices": [{"message": {"content": "TOTAL FOR PART A $1,000.00"}}], "usage": {}}
    monkeypatch.setattr(pageset, "read_bytes", lambda sha: b"%PDF-not-really")
    monkeypatch.setattr(piece.pagereader, "render", lambda data, p, td, dpi: _png(tmp_path, p))
    monkeypatch.setattr(piece.modelclient, "LEDGER", str(tmp_path / "calls.jsonl"))
    r = readers.READERS["glm-ocr"]
    t = piece.run(doc["sha256"], reader=r, url="http://127.0.0.1:8111/v1/chat/completions", args={"pages": [1, 2], "dpi": 200, "pass": "one"},
                  store=store, post=post, ledger=str(tmp_path / "pages.jsonl"), log=lambda *_: None, doc=doc)
    assert t["read"] == 2 and t["failed"] == 0 and len(calls) == 2
    assert calls[0]["temperature"] == 0.0 and calls[0]["model"] == "glm-ocr"
    from support import profiles as doc_profiles
    scan_version = int(doc_profiles.profile("ec-party-return-scan")["version"])
    key = rd.reading_key(doc["sha256"], 1, "glm-ocr", readers.settings(r, 200), "ec-party-return-scan", scan_version)
    got = store.get(key)
    assert got.read_from == "pixels" and got.profile_version == scan_version and got.checks["trial_pass"] == "one"
    # a second run replays and asks nothing
    t2 = piece.run(doc["sha256"], reader=r, url="http://127.0.0.1:8111/v1/chat/completions", args={"pages": [1, 2], "dpi": 200},
                   store=store, post=post, ledger=str(tmp_path / "pages.jsonl"), log=lambda *_: None, doc=doc)
    assert t2["replayed"] == 2 and len(calls) == 2
    lines = [json.loads(l) for l in open(tmp_path / "pages.jsonl")]
    assert all("text" not in l for l in lines) and lines[0]["old_cache"] == "miss"


def _png(tmp_path, p):
    q = tmp_path / f"pg{p}.png"
    q.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([p]))
    return str(q)


def test_rows_parse_takes_only_what_is_printed():
    body = rows.parse('here {"rows": [{"part": "a", "n": 1, "amount": "25,000.00", "date": "1/2/2023", "donor": "X", "is_total": false},'
                      ' {"part": "A", "amount": 41500.5, "is_total": true}], "parts_named": ["A"], "declared_total": "41,500.50"} there')
    assert body["rows"][0]["amount"] == 25000.0 and body["rows"][0]["part"] == "A"
    assert body["rows"][1]["is_total"] and body["declared_total"] == 41500.5 and not body["unparsed"]
    assert rows.parse("no json")["unparsed"]


def test_doc_profile_follows_kind_and_shape():
    assert piece.doc_profile({"kind": "party-return", "shape": "scan"})[0] == "ec-party-return-scan"
    assert piece.doc_profile({"kind": "party-return", "shape": "image-first-page"})[0] == "ec-party-return-image-declaration"
    assert piece.doc_profile({"kind": "disclosure-20k", "shape": "raster"})[0] == "ec-donation-disclosure-20k"
    slug, version, dpi = piece.doc_profile({"kind": "party-return", "shape": "scan", "named_case": "vision-nz-2020-handwritten"})
    assert slug == "ec-party-return-handwritten" and version == 2 and dpi == 300
