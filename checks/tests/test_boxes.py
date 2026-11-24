"""The two boxes' check (checks/boxes.py): the judging, on readings made by hand."""
from checks import boxes

AT = 1_800_000_000.0


def _r(box, **kw):
    r = {"box": box, "free_gb": 600.0, "oom_kills": 1, "pressure": 0.0, "boot_id": f"{box}-boot",
         "previous_boot_clean": True, "holds_vip": box == "node1", "release": "abc", "release_time": AT - 7200,
         "db_primary": box == "node1", "settings": {k: "x" for k in boxes.SAME}}
    r.update(kw)
    return r


def _items(now, before=None, voter=None):
    before = before if before is not None else {b: _r(b) for b in boxes.BOXES}
    voter = voter if voter is not None else {"holder": "node1", "epoch": 4, "held": False}
    return {i["name"]: i for i in boxes.judge(now, before, voter, AT)}


def test_two_healthy_boxes_are_green():
    got = _items({b: _r(b) for b in boxes.BOXES})
    assert all(i["ok"] for i in got.values()), [i for i in got.values() if not i["ok"]]
    assert {"node1/disk", "node2/memory", "address", "voter", "settings", "release"} <= set(got)


def test_the_lost_settings_of_november_are_red():
    n1 = _r("node1", settings={**{k: "x" for k in boxes.SAME}, "max_wal_size": "1024"})
    got = _items({"node1": n1, "node2": _r("node2")})
    assert not got["settings"]["ok"] and "max_wal_size 1024 on node1" in got["settings"]["detail"]


def test_disk_memory_and_an_unclean_reboot_are_red():
    n2 = _r("node2", free_gb=90.0, oom_kills=3, boot_id="new", previous_boot_clean=False)
    got = _items({"node1": _r("node1"), "node2": n2}, before={"node1": _r("node1"), "node2": _r("node2")})
    assert not got["node2/disk"]["ok"]
    assert got["node2/memory"]["ok"]          # a new boot resets the kill counter: no kill counted across it
    assert not got["node2/reboot"]["ok"]
    got = _items({"node1": _r("node1"), "node2": _r("node2", oom_kills=2)})
    assert not got["node2/memory"]["ok"]


def test_two_holders_no_holder_and_a_voter_that_disagrees_are_red():
    assert not _items({"node1": _r("node1"), "node2": _r("node2", holds_vip=True)})["address"]["ok"]
    assert not _items({"node1": _r("node1", holds_vip=False), "node2": _r("node2")})["address"]["ok"]
    assert not _items({b: _r(b) for b in boxes.BOXES}, voter={"holder": "node2", "epoch": 5})["voter"]["ok"]
    got = boxes.judge({b: _r(b) for b in boxes.BOXES}, {}, None, AT)
    assert not next(i for i in got if i["name"] == "voter")["ok"]


def test_a_box_that_does_not_answer_is_red():
    assert not _items({"node1": _r("node1"), "node2": None})["node2/answers"]["ok"]


def test_release_copies_apart_are_red_after_an_hour():
    old = _items({"node1": _r("node1"), "node2": _r("node2", release="def")})
    assert not old["release"]["ok"]
    young = _items({"node1": _r("node1"), "node2": _r("node2", release="def", release_time=AT - 600)})
    assert young["release"]["ok"]
