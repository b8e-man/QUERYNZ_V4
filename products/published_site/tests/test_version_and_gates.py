"""A version is written once with a manifest the snapshot gate holds it to; the record never says publish."""
import json
import os

import pytest

from products.published_site import gates, version


def test_a_version_is_written_once_and_counted(tmp_path):
    out = str(tmp_path)
    d = version.write(out, "2026-10-20T0700", {"data/home.json": {"a": 1}, "data/donor/x-1.json": {"b": 2}, "data/donor/y-2.json": {}}, {"template": "t"})
    m = version.manifest_of(d)
    assert m["written"] == {"home": 1, "donor": 2} and m["files"] == 3 and m["deploy"].startswith("none")
    with pytest.raises(FileExistsError):
        version.write(out, "2026-10-20T0700", {}, {})
    with pytest.raises(ValueError):
        version.write(out, "t2b", {}, {})
    assert version.latest(out) == d
    version.record(out, "2026-10-20T0700", True, "n", [("snapshot", True)])
    rows = [json.loads(l) for l in open(os.path.join(out, "RELEASES.jsonl"))]
    assert rows[-1]["action"] == "built" and "publish" not in json.dumps(rows)


def test_the_snapshot_gate_holds_the_folder_to_the_manifest(tmp_path):
    out = str(tmp_path)
    d = version.write(out, "2026-10-20T0701", {"data/home.json": {"a": 1}, "data/subject/party/act-1.json": {}}, {})
    ok, line = gates.snapshot(d)
    assert ok, line
    with open(os.path.join(d, "data", "subject", "party", "stray-2.json"), "w") as f:
        f.write("{}")
    ok, line = gates.snapshot(d)
    assert not ok and "manifest counts 1 subject" in line
    os.makedirs(os.path.join(d, "data", "review"))
    with open(os.path.join(d, "data", "review", "x.json"), "w") as f:
        f.write("{}")
    ok, line = gates.snapshot(d)
    assert not ok and "factory surface" in line
    results = gates.run_all(d)
    assert results[0][0] == "snapshot" and results[0][1] is False


def test_a_file_that_does_not_parse_or_is_not_a_kind_fails(tmp_path):
    out = str(tmp_path)
    d = version.write(out, "2026-10-20T0702", {"data/home.json": {}}, {})
    with open(os.path.join(d, "data", "home.json"), "w") as f:
        f.write("{not json")
    ok, line = gates.snapshot(d)
    assert not ok and "does not parse" in line
    with open(os.path.join(d, "notes.txt"), "w") as f:
        f.write("x")
    ok, line = gates.snapshot(d)
    assert "not one of the ten kinds: notes.txt" in line
