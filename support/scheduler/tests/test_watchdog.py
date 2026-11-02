"""The model server's watchdog decides from the server's own counters: it restarts a server that is up,
warm, has work in flight and makes no token for ten minutes; it never starts a stopped unit, never touches
an idle or warming one, and stops restarting after three in six hours."""
from support.scheduler import watchdog as w

METRICS = """# HELP vllm:num_requests_running x
vllm:num_requests_running{model_name="qwen4exp",engine="0"} 11
vllm:num_requests_waiting{model_name="qwen4exp",engine="0"} 1
vllm:generation_tokens_total{model_name="qwen4exp",engine="0"} 6798891
"""


def m(tokens, running=2, waiting=0):
    return {"generation_tokens_total": float(tokens), "num_requests_running": float(running),
            "num_requests_waiting": float(waiting)}


def run(steps, active_s=5000, state=None):
    """steps: (seconds from 0, metrics); returns the actions."""
    state, out = state or {}, []
    for t, mm in steps:
        state, action, _ = w.decide(state, 1_000_000 + t, active_s, mm)
        out.append(action)
    return out, state


def test_the_live_metrics_text_parses():
    assert w.parse(METRICS) == {"num_requests_running": 11.0, "num_requests_waiting": 1.0, "generation_tokens_total": 6798891.0}
    assert w.parse("nothing here") == {}


def test_a_stuck_server_is_restarted_after_ten_minutes_and_not_before():
    acts, _ = run([(0, m(100)), (120, m(100)), (480, m(100)), (599, m(100)), (600, m(100))])
    assert acts == ["none", "none", "none", "none", "restart"]


def test_a_moving_server_and_an_idle_one_are_left_alone():
    acts, _ = run([(t, m(100 + t)) for t in range(0, 3600, 120)])
    assert set(acts) == {"none"}
    acts, _ = run([(t, m(100, running=0, waiting=0)) for t in range(0, 3600, 120)])
    assert set(acts) == {"none"}


def test_a_stopped_unit_is_never_started_and_a_warming_one_never_judged():
    acts, _ = run([(t, {}) for t in range(0, 3600, 120)], active_s=None)
    assert set(acts) == {"none"}
    acts, _ = run([(t, m(100)) for t in range(0, 3600, 120)], active_s=300)
    assert set(acts) == {"none"}


def test_a_silent_metrics_endpoint_on_an_active_unit_counts_as_stuck():
    acts, _ = run([(0, m(100)), (300, {}), (700, {})])
    assert acts == ["none", "none", "restart"]


def test_after_three_restarts_in_six_hours_it_alarms_and_leaves_the_server():
    state, acts = {}, []
    for i in range(5):
        base = i * 1300
        a, state = run([(base, m(100)), (base + 1200, m(100))], state=state)
        acts += a
    assert acts.count("restart") == 3 and acts[-1] == "alarm"
    # the window clears: seven hours on, a stall is restarted again
    a, _ = run([(30_000, m(5)), (31_000, m(5))], state=state)
    assert a == ["none", "restart"]
