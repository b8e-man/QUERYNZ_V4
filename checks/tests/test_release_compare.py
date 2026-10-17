"""The release comparison groups files by kind, tells same from changed from
added and removed, and names the JSON keys that changed."""
import json
import os

from checks import release_compare as rc


def make(root, files):
    for rel, content in files.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content if isinstance(content, str) else json.dumps(content))


def test_kinds_counts_and_changed_keys(tmp_path):
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    make(a, {"SNAPSHOT.json": {"stamp": "a", "files": 3},
             "data/donor/x.json": {"name": "X", "generated_at": "1", "total": 5},
             "data/donor/y.json": {"name": "Y", "generated_at": "1", "total": 7},
             "data/cite/c-1.json": {"id": 1},
             "data/electorate/e.json": {"e": 1},
             "assets/pi-aaa.js": "console.log(1)"})
    make(b, {"SNAPSHOT.json": {"stamp": "b", "files": 3},
             "data/donor/x.json": {"name": "X", "generated_at": "2", "total": 5},
             "data/donor/y.json": {"name": "Y", "generated_at": "2", "total": 9},
             "data/cite/c-2.json": {"id": 2},
             "data/electorate/e.json": {"e": 1},
             "assets/pi-bbb.js": "console.log(1)"})
    r = rc.compare(a, b)
    k = r["kinds"]
    assert k["(root)"] == dict(k["(root)"], changed=1, same=0) and k["(root)"]["changed_keys"] == {"stamp": 1}
    assert k["data/donor"]["changed"] == 2 and k["data/donor"]["changed_keys"] == {"generated_at": 2, "total": 1}
    assert k["data/cite"]["added"] == 1 and k["data/cite"]["removed"] == 1
    assert k["data/electorate"]["same"] == 1 and k["data/electorate"]["changed"] == 0
    assert k["assets"]["added"] == 1 and k["assets"]["removed"] == 1
    text = rc.render(r)
    assert "data/donor" in text and "generated_at:2" in text


def test_kind_of():
    assert rc.kind_of("data/donor/x.json") == "data/donor"
    assert rc.kind_of("data/home.json") == "data/home.json"
    assert rc.kind_of("SNAPSHOT.json") == "(root)"
    assert rc.kind_of("fonts/a.woff2") == "fonts"
