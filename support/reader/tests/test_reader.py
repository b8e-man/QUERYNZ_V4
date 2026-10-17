"""A reading is stamped with its model, settings, profile and version, keyed
by the document's hash, stored once and replayed without the model; a
missing reading names the document."""
import pytest

import support.reader as rd

DOC = "c" * 64


def reading(page=1, model="text-layer", settings=None, text="Part A total $5,000"):
    return rd.Reading(document=DOC, page=page, reader="docread 1", model=model, settings=settings or {"dpi": 200},
                      profile="ec-party-return-text", profile_version=3, read_from="text" if model == "text-layer" else "pixels",
                      text=text, rows=[{"donor": "A", "amount": 5000}], checks={"total": True}, made_at="2026-10-18T02:00:00+13:00")


def test_key_carries_document_page_profile_model_and_settings():
    r = reading()
    assert r.key.startswith(f"{DOC}/p1/ec-party-return-text@3/text-layer/")
    assert reading(settings={"dpi": 300}).key != r.key
    assert reading(model="glm-ocr", settings={"dpi": 200}).key != r.key
    assert rd.settings_hash({"b": 1, "a": 2}) == rd.settings_hash({"a": 2, "b": 1})


def test_store_put_get_and_replay_without_a_model(tmp_path):
    store = rd.Store(str(tmp_path))
    r = reading()
    store.put(r)
    assert store.has(r.key)
    assert store.get(r.key) == r
    calls = []
    got = rd.replay_or_read(store, r.key, read=lambda: calls.append(1) or reading())
    assert got == r and calls == []           # replayed, the reader never ran


def test_a_missing_reading_names_the_document(tmp_path):
    store = rd.Store(str(tmp_path))
    with pytest.raises(rd.MissingReading) as e:
        rd.replay_or_read(store, reading().key)
    assert DOC in str(e.value)


def test_reading_once_then_stored(tmp_path):
    store = rd.Store(str(tmp_path))
    r = reading(model="glm-ocr")
    got = rd.replay_or_read(store, r.key, read=lambda: r)
    assert got.read_from == "pixels" and store.has(r.key)
    with pytest.raises(ValueError):
        rd.replay_or_read(store, reading(page=2).key, read=lambda: reading(page=3))


def test_refusals():
    with pytest.raises(ValueError):
        rd.Reading(DOC, 1, "r", "m", {}, "p", 1, "guess", "t")
    with pytest.raises(ValueError):
        rd.Reading(DOC, 0, "r", "m", {}, "p", 1, "text", "t")
