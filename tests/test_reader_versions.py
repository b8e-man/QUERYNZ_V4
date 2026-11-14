"""Which version of a reader made which reading (Arthur, 15 November 2026): every READER string held to its code,
and every stored reading stamped with its commit."""
import json
import os

from support import reader as rd
from support.reader import versions as V


def test_every_reader_s_version_string_matches_its_code():
    d = V.drift(V.current(), V.load())
    assert not d["bump"], f"code changed under the same READER (bump it, then run support.reader.versions --update): {d['bump']}"
    assert not d["record"], f"not recorded (run python -m support.reader.versions --update): {d['record']}"
    assert not d["gone"], f"in the manifest but defining no READER now (run --update): {d['gone']}"


def _lane(tmp_path, reader="registers.x.read 1", helper="A = 1\n"):
    lane = tmp_path / "registers" / "x"
    lane.mkdir(parents=True, exist_ok=True)
    (lane / "__init__.py").write_text("")
    (lane / "helper.py").write_text(helper)
    (lane / "other.py").write_text("B = 2\n")
    (lane / "read.py").write_text(f'from registers.x import helper\nREADER = "{reader}"\n')
    return str(tmp_path)


def test_a_change_to_a_reader_or_a_module_it_imports_wants_a_bump_and_a_bump_is_recorded(tmp_path):
    repo = _lane(tmp_path)
    rec = V.current(repo)
    assert rec["registers/x/read.py"]["files"] == ["registers/x/helper.py", "registers/x/read.py"]
    assert V.drift(V.current(repo), rec) == {"bump": [], "record": [], "gone": []}
    _lane(tmp_path, helper="A = 3\n")                              # an imported module changed, the string did not
    assert V.drift(V.current(repo), rec)["bump"] == ["registers/x/read.py"]
    (tmp_path / "registers" / "x" / "other.py").write_text("B = 9\n")   # a module it does not import: no bump wanted
    assert V.drift(V.current(repo), rec)["bump"] == ["registers/x/read.py"]
    _lane(tmp_path, reader="registers.x.read 2", helper="A = 3\n")   # bumped: to be recorded, not a bump
    assert V.drift(V.current(repo), rec) == {"bump": [], "record": ["registers/x/read.py"], "gone": []}


def test_a_stored_reading_carries_the_commit_it_was_made_at_and_an_old_one_replays(tmp_path, monkeypatch):
    monkeypatch.setenv("QV4_COMMIT", "abc123")
    monkeypatch.setattr(rd, "_COMMIT", {})
    store = rd.Store(str(tmp_path))
    r = rd.Reading(document="d" * 64, page=1, reader="registers.x.read 1", model="text-layer", settings={},
                   profile="p", profile_version=1, read_from="text", text="t")
    path = store.put(r)
    assert json.load(open(path))["commit"] == "abc123" and store.get(r.key).commit == "abc123"
    old = json.load(open(path))
    del old["commit"]                                              # a reading stored before 15 November
    json.dump(old, open(path, "w"))
    assert store.get(r.key).commit == "" and store.get(r.key).key == r.key


def test_the_commit_is_the_checkout_s_head():
    rd._COMMIT.clear()
    if os.environ.get("QV4_COMMIT") is None:
        got = rd.code_commit()
        assert len(got.split("+")[0]) == 40
