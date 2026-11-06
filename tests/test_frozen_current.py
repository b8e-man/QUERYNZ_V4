"""The frozen site's `current` link is node2's absolute path; node1 reads the folder over NFS where that path does not
exist (7 November 2026: qv4-disclosures-load failed on node1). The version is found from the link's last part."""
import os

from support import frozen


def tree(tmp_path, target):
    snap = tmp_path / "old" / "var" / "pi-snapshot"
    (snap / "v" / "2026-11-07T0727" / "data").mkdir(parents=True)
    (snap / "v" / "2026-11-07T0727" / "data" / "home.json").write_text("{}")
    os.symlink(target, snap / "current")
    return str(tmp_path / "old")


def test_a_link_to_another_box_s_absolute_path_is_read_by_its_last_part(tmp_path):
    old = tree(tmp_path, "/no-such-box/Git Repos/QueryNZ_V3/var/pi-snapshot/v/2026-11-07T0727")
    assert not os.path.exists(os.path.join(old, "var", "pi-snapshot", "current"))   # as node1 sees it
    assert frozen.current_version(old) == "2026-11-07T0727"
    assert frozen.home_json(old) == os.path.join(old, "var", "pi-snapshot", "v", "2026-11-07T0727", "data", "home.json")
    assert os.path.isfile(frozen.home_json(old))


def test_a_version_not_held_or_no_link_is_none(tmp_path):
    old = tree(tmp_path, "/elsewhere/v/2026-01-01T0000")
    assert frozen.current_dir(old) is None and not os.path.exists(frozen.home_json(old))
    assert frozen.current_version(str(tmp_path / "nothing")) is None


def test_the_frozen_check_reads_the_version_the_same_way(tmp_path):
    from checks import frozen_product
    old = tree(tmp_path, "/no-such-box/Git Repos/QueryNZ_V3/var/pi-snapshot/v/2026-11-07T0727/")
    assert frozen_product.current_version(old) == "2026-11-07T0727"
