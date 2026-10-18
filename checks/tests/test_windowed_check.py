"""The windowed lanes' board check reads each lane's own check by exit code."""
from checks import windowed as w


def fake(answers):
    return lambda lane: answers[lane]


def items(r):
    return {i["name"]: i for i in r["items"]}


def test_both_lanes_green_when_nothing_is_short():
    r = w.check(run=fake({"tenancy_tribunal": (0, "equal: 12 months, source 400, held 400\nshort: 0 months, source 0, held 0\npast_window: 0 months, source 0, held 0"),
                          "real_estate_authority": (0, "equal: 3 years, source 84, held 84")}))
    assert r["ok"] and r["check"] == "windowed"
    assert items(r)["tenancy_tribunal"]["detail"].startswith("equal: 12 months")


def test_a_short_month_is_red_with_the_short_lines():
    out = "equal: 11 months, source 380, held 380\nshort: 1 months, source 20, held 7\n  short 2026-09: source 20, held 7"
    r = w.check(run=fake({"tenancy_tribunal": (1, out), "real_estate_authority": (0, "equal: 3 years, source 84, held 84")}))
    assert not r["ok"]
    assert not items(r)["tenancy_tribunal"]["ok"] and "2026-09" in items(r)["tenancy_tribunal"]["detail"]
    assert items(r)["real_estate_authority"]["ok"]


def test_a_check_that_fails_to_run_is_red_and_says_so():
    r = w.check(run=fake({"tenancy_tribunal": (3, "no answer in 120 s"), "real_estate_authority": (2, "Traceback\nKeyError: 'x'")}))
    assert not r["ok"]
    assert "exit 3" in items(r)["tenancy_tribunal"]["detail"] and "KeyError" in items(r)["real_estate_authority"]["detail"]


def test_the_live_lane_checks_are_runnable_commands():
    """The real runner reaches each lane's check module (it may be red on data; it must not be missing)."""
    for lane in w.LANES:
        rc, out = w.run_lane(lane)
        assert rc in (0, 1), (lane, rc, out[-300:])
