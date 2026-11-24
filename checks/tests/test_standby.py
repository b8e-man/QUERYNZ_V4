from checks import standby


def test_no_connected_standby_is_red():
    items = standby.judge({"connected": 0, "slots": [{"name": "node2_standby", "active": False, "behind_gb": None,
                                                       "wal_status": None}]})
    assert not items[0]["ok"] and "INACTIVE" in items[0]["detail"] and "rebuild" in items[0]["detail"]


def test_a_streaming_standby_within_the_lag_is_green_and_past_it_red():
    ok = standby.judge({"connected": 1, "slots": [{"name": "node2_standby", "active": True, "behind_gb": 0.2,
                                                    "wal_status": "reserved"}]})
    assert all(i["ok"] for i in ok)
    far = standby.judge({"connected": 1, "slots": [{"name": "node2_standby", "active": True, "behind_gb": 60.0,
                                                     "wal_status": "extended"}]})
    assert far[0]["ok"] and not far[1]["ok"]


def test_a_standby_agent_not_caught_up_is_red_and_a_primary_is_not():
    assert not standby.judge_agent({"box": "node2", "role": "standby", "caught_up": False})["ok"]
    assert standby.judge_agent({"box": "node2", "role": "standby", "caught_up": True})["ok"]
    assert standby.judge_agent({"box": "node1", "role": "primary"})["ok"]
    assert not standby.judge_agent(None)["ok"]


def test_the_wal_budget_is_red_past_64_gb_a_day_and_measuring_before_a_day():
    import datetime as dt
    t = dt.datetime(2026, 11, 25, 17, 0, tzinfo=dt.timezone.utc)
    day = dt.timedelta(hours=24)
    assert standby.judge_wal([(t - dt.timedelta(hours=2), 0), (t, 10**9)], t)["detail"].startswith("measuring")
    assert standby.judge_wal([(t - day, 0), (t, 3 * 10**9)], t)["ok"]
    assert not standby.judge_wal([(t - day, 0), (t, 600 * 10**9)], t)["ok"]
