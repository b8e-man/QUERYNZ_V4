"""A build is pinned to a frozen release's listing: hashes in, folders counted, a bad file refused."""
import json

import pytest

from products.published_site import pin


def write(tmp_path, version, rows, files=None):
    p = tmp_path / f"{version}.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps({"version": version, "listed_at": "2026-10-20T07:30:00+13:00", "root": "/x/staging",
                            "files": len(rows) if files is None else files, "bytes": 3}) + "\n")
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return str(p)


def test_a_listing_loads_its_hashes_and_folders(tmp_path):
    p = write(tmp_path, "2026-10-20T0620", [
        {"path": "ec-donations/a.pdf", "bytes": 1, "mtime": "x", "sha256": "a" * 64},
        {"path": "ec-donations/b.pdf", "bytes": 1, "mtime": "x", "sha256": "b" * 64},
        {"path": "linz/c.csv", "bytes": 1, "mtime": "x", "sha256": "c" * 64}])
    L = pin.load(p)
    assert L.version == "2026-10-20T0620" and L.files == 3
    assert L.holds("a" * 64) and not L.holds("d" * 64) and not L.holds(None)
    assert L.folders == {"ec-donations": 2, "linz": 1}
    assert pin.versions(str(tmp_path)) == ["2026-10-20T0620"] and pin.latest(str(tmp_path)) == "2026-10-20T0620"


def test_a_short_or_headerless_listing_is_refused(tmp_path):
    p = write(tmp_path, "v1", [{"path": "a/b", "bytes": 1, "mtime": "x", "sha256": "a" * 64}], files=2)
    with pytest.raises(ValueError, match="header says 2"):
        pin.load(p)
    q = tmp_path / "v2.jsonl"
    q.write_text(json.dumps({"path": "a/b", "sha256": "a" * 64}) + "\n")
    with pytest.raises(ValueError, match="not a release listing"):
        pin.load(str(q))
    assert pin.latest(str(tmp_path / "nowhere")) is None
