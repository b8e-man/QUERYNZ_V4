"""A reading made by an earlier model stands for one by the model that replaced it (1 November 2026)."""
from support import reader as rd


def _r(model, text="x"):
    return rd.Reading("a" * 64, 1, "t 1", model, {"k": 1}, "beehive-release", 2, "text", text)


def test_the_new_model_finds_the_earlier_reading_and_its_own_wins(tmp_path):
    s = rd.Store(str(tmp_path))
    new_key = rd.reading_key("a" * 64, 1, "qwen3.6-35b-a3b-q4km", {"k": 1}, "beehive-release", 2)
    assert not s.has(new_key)
    s.put(_r("qwen4exp", "old"))
    assert s.has(new_key) and s.get(new_key).model == "qwen4exp" and s.get(new_key).text == "old"
    s.put(_r("qwen3.6-35b-a3b-q4km", "new"))
    assert s.get(new_key).text == "new"


def test_the_old_model_never_borrows_the_new_one(tmp_path):
    s = rd.Store(str(tmp_path))
    s.put(_r("qwen3.6-35b-a3b-q4km"))
    assert not s.has(rd.reading_key("a" * 64, 1, "qwen4exp", {"k": 1}, "beehive-release", 2))


def test_other_settings_or_versions_are_not_borrowed(tmp_path):
    s = rd.Store(str(tmp_path))
    s.put(_r("qwen4exp"))
    assert not s.has(rd.reading_key("a" * 64, 1, "qwen3.6-35b-a3b-q4km", {"k": 2}, "beehive-release", 2))
    assert not s.has(rd.reading_key("a" * 64, 1, "qwen3.6-35b-a3b-q4km", {"k": 1}, "beehive-release", 3))
