"""A lane folder has its eight pieces and its tests; the spec has five
lines; the sample is hashes and keys only; its tables live in its own
schema or its private twin."""
import os

import support.lane as lane

SPEC = "owns: gazette, gazette_private\nreads: docs\npublishes: pub.gazette_notices\noutside check: the Gazette's own notice count by week\njobs: qv4-gazette-capture daily 03:10\n"


def make_lane(root, name="gazette", spec=SPEC, sample="# the sample\n" + "a" * 64 + " party return 2021\nkey: notice-2024-1234\n",
              tables="CREATE TABLE IF NOT EXISTS gazette.notices (id text);\nCREATE TABLE IF NOT EXISTS gazette_private.addresses (k text);\n"):
    d = os.path.join(root, name)
    os.makedirs(os.path.join(d, "tests"))
    for p in lane.PIECES:
        with open(os.path.join(d, p), "w") as f:
            f.write({"spec.md": spec, "sample.list": sample, "tables.sql": tables}.get(p, "# " + p + "\n"))
    return d


def test_a_complete_lane_passes(tmp_path):
    assert lane.check_folder(make_lane(str(tmp_path))) == []


def test_missing_pieces_are_named(tmp_path):
    d = make_lane(str(tmp_path))
    os.remove(os.path.join(d, "check.py"))
    os.rmdir(os.path.join(d, "tests"))
    probs = lane.check_folder(d)
    assert "gazette: missing check.py" in probs and "gazette: missing tests/" in probs


def test_the_spec_has_five_lines():
    assert lane.check_spec(SPEC) == []
    assert lane.check_spec("owns: x\nreads: y\n") == ["spec.md has no `publishes:` line", "spec.md has no `outside check:` line",
                                                      "spec.md has no `jobs:` line"]
    assert any("12 lines" in p or "lines;" in p for p in lane.check_spec("\n".join(f"owns: {i}" for i in range(20)) + "\nreads: a\npublishes: b\noutside check: c\njobs: d"))


def test_the_sample_is_hashes_and_keys_only(tmp_path):
    d = make_lane(str(tmp_path), sample="b" * 64 + "\nkey: x1\n12 Example Street, Karori\n")
    assert lane.check_folder(d) == ["gazette: sample.list:3: not a sha256 or a `key:` line"]


def test_tables_stay_in_the_lanes_own_schema(tmp_path):
    d = make_lane(str(tmp_path), tables="CREATE TABLE IF NOT EXISTS companies.entities (id text);\n")
    assert lane.check_folder(d) == ["gazette: tables.sql creates a table in `companies`, not its own schema"]


def test_a_lane_folder_is_a_schema_name(tmp_path):
    d = make_lane(str(tmp_path), name="Gazette-Lane")
    assert any("not a schema name" in p for p in lane.check_folder(d))
