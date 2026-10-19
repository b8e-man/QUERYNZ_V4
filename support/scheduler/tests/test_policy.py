"""The nine rules must be provably starvation-free (carried from
ops/fleet/tests/test_schedule.py; rules 6, 8 and 9 added).

`plan()` is pure, so the policy can be exercised exhaustively — which
matters more here than anywhere else, because a scheduling bug does not
announce itself. It shows up weeks later as one job that never seems to
run, and the old estate had form for that: the gateway sent every call to
one card for weeks while the other sat idle, and nothing said so."""
from __future__ import annotations

import pytest

from support.scheduler import policy, registry as reg
from support.scheduler.policy import DRAIN, HANDOVER, KEEP, LOAD, RELEASE, Demand, Held
from support.scheduler.tests import fixtures as fx


@pytest.fixture
def cat(tmp_path):
    return fx.catalogue(tmp_path)


def plan(cat, **kw):
    registry, profiles, rules = cat
    return policy.plan(registry=registry, profiles=profiles, rules=rules, **kw)


def one(decisions, card="n:0"):
    return next(d for d in decisions if d.card == card)


# ── rule 1: yield on empty ───────────────────────────────────────────────────

def test_a_job_whose_queue_drained_gives_the_card_back(cat):
    """"Or until its queue is empty" — an hour is a ceiling, not an
    entitlement. A card held idle by a finished job is the waste this whole
    service exists to end."""
    ds, _ = plan(cat, now=100, held=[Held("n:0", "doc", since=90)], queues={"doc": 0})
    assert one(ds).action == RELEASE


def test_an_empty_queue_with_work_in_flight_drains_first(cat):
    ds, _ = plan(cat, now=100, held=[Held("n:0", "doc", since=90, in_flight=2)], queues={"doc": 0})
    assert one(ds).action == DRAIN


# ── rule 2: uninterrupted within the slice ───────────────────────────────────

def test_nothing_takes_a_card_mid_slice(cat):
    """The rule that buys reliable per-task performance. A higher-priority job
    type with a deep queue still waits."""
    ds, _ = plan(cat, now=1000, held=[Held("n:0", "rev", since=500)], queues={"rev": 40, "doc": 500})
    assert one(ds).action == KEEP and "uninterrupted" in one(ds).why


def test_the_slice_is_measured_from_when_it_began(cat):
    for age, expected in ((3599, KEEP), (3600, DRAIN), (7200, DRAIN)):
        ds, _ = plan(cat, now=10_000, held=[Held("n:0", "rev", since=10_000 - age)], queues={"rev": 40, "doc": 500})
        assert one(ds).action == expected, (age, one(ds).why)


# ── rule 3: drain, never kill ────────────────────────────────────────────────

def test_slice_expiry_drains_rather_than_killing(cat):
    ds, _ = plan(cat, now=5000, held=[Held("n:0", "rev", since=0, in_flight=3)], queues={"rev": 40, "doc": 20})
    d = one(ds)
    assert d.action == DRAIN and d.job_type == "rev" and "not killing" in d.why


def test_a_draining_card_is_released_once_nothing_is_in_flight(cat):
    ds, _ = plan(cat, now=5000, held=[Held("n:0", "rev", since=0, draining=True, in_flight=0)], queues={"rev": 40})
    assert one(ds).action == RELEASE


def test_an_expired_slice_is_kept_when_nobody_else_wants_the_card(cat):
    """Handing a card back to nobody is pure loss — a reload for no reason."""
    ds, _ = plan(cat, now=5000, held=[Held("n:0", "rev", since=0)], queues={"rev": 40})
    assert one(ds).action == KEEP and "nobody" in one(ds).why


def test_a_draining_card_with_work_in_flight_is_not_taken_away(cat):
    """Rule 3's real case: a draining card keeps draining until its in-flight
    count reaches zero — releasing it early IS the kill the rule forbids."""
    ds, _ = plan(cat, now=9999, held=[Held("n:0", "rev", since=0, draining=True, in_flight=2)],
                 queues={"rev": 40, "doc": 500})
    d = one(ds)
    assert d.action == DRAIN and d.job_type == "rev" and "2 in flight" in d.why
    assert not any(x.card == "n:0" and x.job_type == "doc" for x in ds)


# ── rule 4: priority-ordered round robin ─────────────────────────────────────

def test_the_highest_priority_waiting_job_takes_a_free_card(cat):
    ds, _ = plan(cat, now=0, held=[Held("n:0", None)], queues={"reason": 50, "doc": 50, "rev": 50})
    assert one(ds).job_type == "doc"


def test_a_job_that_has_had_its_turn_stands_aside(cat):
    ds, _ = plan(cat, now=0, held=[Held("n:0", None)], queues={"reason": 50, "doc": 50, "rev": 50},
                 round_done=frozenset({"doc"}))
    assert one(ds).job_type == "rev"


def test_the_round_restarts_once_everyone_has_had_a_turn(cat):
    ds, done = plan(cat, now=0, held=[Held("n:0", None)], queues={"doc": 50, "rev": 50},
                    round_done=frozenset({"doc", "rev"}))
    assert one(ds).job_type == "doc"
    assert done == frozenset({"doc"}), "a new round, not the old one continued"


def test_waiting_is_bounded_by_the_number_of_job_types(cat):
    """THE PROPERTY THAT MATTERS. Drive one card through many rounds with
    every queue permanently non-empty — the lowest-priority job type must
    still get a turn, and within (job types - 1) slices of any other."""
    queues = {"doc": 999, "rev": 999, "reason": 999, "emb": 999}
    done, turns = frozenset(), []
    for _ in range(24):
        ds, done = plan(cat, now=0, held=[Held("n:0", None)], queues=queues, round_done=done)
        turns.append(one(ds).job_type)
    assert set(turns) == set(queues), f"a job type starved: {turns}"
    for name in queues:
        gaps = [i for i, t in enumerate(turns) if t == name]
        assert max(b - a for a, b in zip(gaps, gaps[1:])) <= len(queues), f"{name} waited longer than one full round: {turns}"


def test_priority_still_decides_the_order_inside_a_round(cat):
    done, turns = frozenset(), []
    for _ in range(4):
        ds, done = plan(cat, now=0, held=[Held("n:0", None)], queues={"doc": 9, "rev": 9, "reason": 9, "emb": 9},
                        round_done=done)
        turns.append(one(ds).job_type)
    assert turns == ["doc", "rev", "reason", "emb"]


def test_a_job_with_an_empty_queue_is_not_offered_a_card(cat):
    ds, _ = plan(cat, now=0, held=[Held("n:0", None)], queues={"doc": 0, "rev": 5})
    assert one(ds).job_type == "rev"


def test_a_free_card_with_nothing_queued_is_left_alone(cat):
    ds, _ = plan(cat, now=0, held=[Held("n:0", None)], queues={"doc": 0})
    assert one(ds).action == KEEP and one(ds).job_type is None


def test_a_processor_job_is_never_planned_onto_a_card(cat):
    ds, _ = plan(cat, now=0, held=[Held("n:0", None)], queues={"cpu": 50})
    assert one(ds).action == KEEP and one(ds).job_type is None


# ── rule 5: a swap must pay for itself ───────────────────────────────────────

def test_a_costly_switch_needs_enough_queued_work(cat):
    """Unloading 21 GB for three items of work spends more card time than it
    buys. The floor is why min_queue_to_evict exists."""
    ds, _ = plan(cat, now=0, held=[Held("n:0", "rev", since=0)], queues={"rev": 0, "emb": 3})
    acts = [(d.action, d.job_type, d.why) for d in ds]
    assert any(a == RELEASE for a, _, _ in acts), acts
    assert any("would discard a working" in w for _, _, w in acts), acts
    assert not any(a == LOAD for a, _, _ in acts), acts


def test_a_cold_card_takes_work_however_little_there_is(cat):
    """The floor guards DISCARDING a resident profile. A cold card has none
    to discard, so waiting saves nothing and only leaves it idle."""
    ds, _ = plan(cat, now=0, held=[Held("n:0", None, loaded=None)], queues={"emb": 1})
    assert one(ds).action == LOAD and one(ds).job_type == "emb" and one(ds).profile == "bge"


def test_a_released_card_is_still_configured_for_its_last_profile(cat):
    """Releasing a LEASE does not unload 21 GB of weights. A card `reason`
    has just let go still holds the 50k profile, so `doc` takes it free."""
    ds, _ = plan(cat, now=0, held=[Held("n:0", None, loaded="qwen-50k")], queues={"doc": 1})
    assert one(ds).action == HANDOVER and one(ds).job_type == "doc"


def test_a_costly_switch_proceeds_once_the_work_justifies_it(cat):
    ds, _ = plan(cat, now=0, held=[Held("n:0", "rev", since=0)], queues={"rev": 0, "emb": 40})
    assert any(d.action == LOAD and d.job_type == "emb" for d in ds), [(d.action, d.job_type) for d in ds]


def test_a_free_handover_has_no_minimum(cat):
    """`doc` and `reason` name the same profile, so passing the card between
    them costs nothing — and a floor that applied here would idle a
    correctly configured card for no reason."""
    ds, _ = plan(cat, now=0, held=[Held("n:0", "reason", since=0, draining=True)], queues={"reason": 0, "doc": 1})
    assert any(d.action == HANDOVER and d.job_type == "doc" for d in ds), [(d.action, d.job_type, d.why) for d in ds]


def test_a_costly_switch_refused_does_not_consume_the_jobs_turn(cat):
    _, done = plan(cat, now=0, held=[Held("n:0", "rev", since=0)], queues={"rev": 0, "emb": 3})
    assert "emb" not in done


def test_the_swap_cost_is_the_measured_load_time_when_there_is_one(tmp_path):
    """Rule 9's second half: with the profile's load time and the job's
    seconds per item measured, the floor gives way to arithmetic. Three
    items at 100 s each do not pay for a 400 s load; five do."""
    j, p = fx.write(tmp_path, profiles=fx.PROFILES.replace('model = "B"', 'model = "B"\nload_seconds = 400'))
    registry, profiles, rules = reg.load(j), reg.profiles(p), reg.queueing(j)
    ds, _ = policy.plan(now=0, held=[Held("n:0", "rev", since=0)],
                        queues={"rev": 0, "emb": Demand(3, item_seconds=100)},
                        registry=registry, profiles=profiles, rules=rules)
    assert not any(d.action == LOAD for d in ds) and any("3 item(s) x 100s < load 400s" in d.why for d in ds)
    ds, _ = policy.plan(now=0, held=[Held("n:0", "rev", since=0)],
                        queues={"rev": 0, "emb": Demand(5, item_seconds=100)},
                        registry=registry, profiles=profiles, rules=rules)
    assert any(d.action == LOAD and d.job_type == "emb" for d in ds)


# ── rule 6: a small job never waits for ever ─────────────────────────────────

def test_a_small_queue_gets_its_card_after_the_maximum_wait(cat):
    """Three items never justify a load under rule 5, so without rule 6
    `emb` would wait behind a busy `rev` for as long as `rev` has work.
    After 30 minutes it gets the card anyway."""
    held = [Held("n:0", "rev", since=0)]
    ds, _ = plan(cat, now=10_000, held=held, queues={"rev": 0, "emb": Demand(3, waiting_since=10_000 - 1799)})
    assert not any(d.action == LOAD for d in ds)
    ds, _ = plan(cat, now=10_000, held=held, queues={"rev": 0, "emb": Demand(3, waiting_since=10_000 - 1800)})
    d = next(d for d in ds if d.job_type == "emb")
    assert d.action == LOAD and "rule 6" in d.why


def test_a_starved_job_this_box_cannot_claim_is_never_the_pick(cat):
    """Card the-card-manager-loads-a-profile-for-a-job-no-box-can-claim: row 74
    required a program the probe did not list, so the worker never claimed it;
    rule 6 still picked it as the starved small job three times on 19 October
    and discarded a working profile for a load that failed. The planner sees
    only the demand of job types this box can claim."""
    held = [Held("n:0", "rev", since=0)]
    queues = {"rev": 0, "emb": Demand(3, waiting_since=10_000 - 1800)}
    ds, done = plan(cat, now=10_000, held=held, queues=queues, eligible={"rev", "doc", "reason"})
    assert not any(d.action == LOAD for d in ds), [(d.action, d.why) for d in ds]
    assert not any(d.job_type == "emb" for d in ds) and "emb" not in done
    assert one(ds).action == RELEASE, "rev's queue is empty: the card is released, and no ineligible demand holds it"
    ds, _ = plan(cat, now=10_000, held=held, queues=queues, eligible={"rev", "emb"})
    assert any(d.action == LOAD and d.job_type == "emb" for d in ds), "eligible here: rule 6 stands"


def test_an_ineligible_job_type_does_not_make_a_slice_expire_either(cat):
    """The same invisibility under rule 3: a job type this box cannot run is
    not 'another job type waiting', so the resident slice is kept."""
    ds, _ = plan(cat, now=5000, held=[Held("n:0", "rev", since=0)], queues={"rev": 40, "doc": 20}, eligible={"rev"})
    assert one(ds).action == KEEP and "nobody" in one(ds).why


# ── rule 8: three classes ────────────────────────────────────────────────────

def test_someone_waiting_goes_first_whatever_the_round_says(cat):
    """A live question (class waiting) outranks a bulk job that would be
    next in the round, even one that has not had its turn."""
    ds, _ = plan(cat, now=0, held=[Held("n:0", None)],
                 queues={"doc": 500, "reason": Demand(1, cls="waiting")}, round_done=frozenset({"reason"}))
    assert one(ds).job_type == "reason" and "waiting" in one(ds).why


def test_a_due_job_goes_ahead_of_bulk_work_as_its_time_nears(cat):
    """`emb` is due in an hour: it goes before `doc`'s bulk work. Due in a
    day, it waits its turn like anyone else."""
    ds, _ = plan(cat, now=0, held=[Held("n:0", None)], queues={"doc": 500, "emb": Demand(5, cls="due", due_at=3600)})
    assert one(ds).job_type == "emb"
    ds, _ = plan(cat, now=0, held=[Held("n:0", None)], queues={"doc": 500, "emb": Demand(5, cls="due", due_at=86400)})
    assert one(ds).job_type == "doc"


# ── rule 9: a bulk job takes every free card, and gives cards back ───────────

def test_a_bulk_job_alone_takes_every_free_card(cat):
    ds, _ = plan(cat, now=0, held=[Held("n:0", None), Held("n:1", None)], queues={"doc": 999})
    assert [d.job_type for d in ds] == ["doc", "doc"]
    assert any("rule 9" in d.why for d in ds)


def test_two_cards_are_not_given_to_the_same_job_type_while_another_waits(cat):
    """One card, one job type per tick when somebody else is waiting (the
    old rule); rule 9 only hands out cards nobody else wants."""
    ds, _ = plan(cat, now=0, held=[Held("n:0", None), Held("n:1", None)], queues={"doc": 999, "rev": 5})
    assert sorted(d.job_type for d in ds) == ["doc", "rev"]


def test_a_job_with_one_item_left_does_not_take_a_second_card(cat):
    ds, _ = plan(cat, now=0, held=[Held("n:0", None), Held("n:1", None)], queues={"doc": 1})
    assert [d.job_type for d in ds] == ["doc", None]


def test_a_job_holding_two_cards_gives_one_back_when_another_queues(cat):
    """Mid-slice, with its queue deep: the extra card drains (not the last
    one, and nothing is killed) so the waiting job type gets a turn."""
    held = [Held("n:0", "doc", since=100), Held("n:1", "doc", since=200)]
    ds, _ = plan(cat, now=300, held=held, queues={"doc": 999, "rev": 5})
    assert one(ds, "n:0").action == KEEP
    assert one(ds, "n:1").action == DRAIN and "rule 9" in one(ds, "n:1").why


def test_a_job_holding_two_cards_keeps_both_while_nobody_waits(cat):
    held = [Held("n:0", "doc", since=100), Held("n:1", "doc", since=200)]
    ds, _ = plan(cat, now=300, held=held, queues={"doc": 999})
    assert [d.action for d in ds] == [KEEP, KEEP]


# ── sharing a profile, and reserved cards ────────────────────────────────────

def test_a_job_whose_profile_is_already_loaded_shares_it_rather_than_waiting(cat):
    """`reason` and `doc` both name the 50k profile and may share: with
    `doc` holding card 0 on that profile, `reason` is served there and does
    not take the free card with a load of its own."""
    ds, _ = plan(cat, now=0, held=[Held("n:0", "doc", since=0), Held("n:1", None)], queues={"doc": 5, "reason": 5})
    assert one(ds, "n:1").job_type is None


def test_a_reserved_card_is_accounted_for_and_never_planned(cat):
    """Step 2.9: the carve-out's card. Every tick records it; nothing is
    ever placed on it, however deep the queues."""
    ds, _ = plan(cat, now=0, held=[Held("n:9", None, reserved=True)], queues={"doc": 999, "rev": 999})
    d = one(ds, "n:9")
    assert d.action == KEEP and d.job_type is None and "reserved" in d.why


# ── every card gets a reason, every tick ─────────────────────────────────────

def test_every_card_is_accounted_for_in_every_plan(cat):
    held = [Held("n:0", "rev", since=0), Held("n:1", None), Held("n:2", "doc", since=0, draining=True, in_flight=1),
            Held("n:9", None, reserved=True)]
    ds, _ = plan(cat, now=10, held=held, queues={"rev": 5})
    assert {d.card for d in ds} == {"n:0", "n:1", "n:2", "n:9"}
    assert all(d.why for d in ds)
