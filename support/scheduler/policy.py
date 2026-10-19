"""THE NINE RULES FOR SHARING THE GRAPHICS CARDS (carried from
ops/fleet/schedule.py, rules 1-5, Arthur's ruling of 22 September; rules 6-9
are step 2's).

This module is PURE. `plan()` takes the clock, what each card holds, what
each job type has waiting, and the catalogue, and returns one decision per
card. It starts nothing, stops nothing and asks nothing — which is why the
policy can be tested exhaustively without a card, and why a scheduling bug
is findable at all. The worker acts on the decisions (`cards.py`).

1. YIELD ON EMPTY. A job type whose queue has drained releases its card at
   once. "An hour" is a ceiling, not an entitlement.
2. UNINTERRUPTED WITHIN THE SLICE. While a job type's slice runs and its
   queue is not empty, nothing takes its card.
3. DRAIN, NEVER KILL. A slice expiring means take no new work and let what
   is in flight finish. A half-finished reading is how a wrong figure gets
   stored.
4. PRIORITY-ORDERED ROUND ROBIN. Priority orders the job types waiting; a
   job type that has had a turn goes to the back, so waiting is bounded.
5. A SWAP MUST PAY FOR ITSELF. Discarding a resident profile needs enough
   queued work to be worth the load. A card already holding the right
   profile is taken at no cost (a handover).
6. A SMALL JOB NEVER WAITS FOR EVER. A queue too short to justify a swap
   gets one anyway after `max_wait_seconds` (30 minutes to start).
7. PIECES. Long jobs are cut into pieces of a few minutes, each recording
   its own progress. That is the queue's rule (`queue.py`); the planner
   sees only depth.
8. THREE CLASSES: someone is waiting; due by a time; whenever. A waiting
   person goes first, a due job next as its time nears, bulk work fills
   the rest.
9. A BULK JOB TAKES EVERY FREE CARD but gives cards back when others queue.
   The swap cost in rule 5 is the measured load time of each profile (from
   the swap ledger), not a fixed number; the queue floor is the fallback
   until a profile's load time has been measured.

A reserved card (step 2.9) is accounted for every tick and never planned.
"""
from __future__ import annotations

import dataclasses

from support.scheduler import registry as reg

# Actions, in increasing cost. `cards.py` maps these to operations.
KEEP, RELEASE, DRAIN = "keep", "release", "drain"
HANDOVER, LOAD = "handover", "load"
RESTART = LOAD   # the old name: a restart is a load of the same weights; the measured load time tells them apart

CLASS_RANK = {"waiting": 0, "due": 1, "whenever": 2}


@dataclasses.dataclass(frozen=True)
class Held:
    """What a card holds right now.

    TWO DIFFERENT THINGS: `job_type` is who holds the LEASE, and `loaded` is
    which PROFILE is physically resident. Releasing a lease does not unload
    21 GB of weights, so a card just released by one job type is still set
    up for every job type naming that profile, and handing it over costs
    nothing. Pricing that as a cold load would idle a correctly configured
    card for no reason.
    """
    card: str                    # "node2:1"
    job_type: str | None         # the LEASE holder; None = free
    since: float = 0.0           # epoch seconds the slice began
    draining: bool = False
    in_flight: int = 0
    loaded: str | None = None    # the resident PROFILE; None = cold card
    reserved: bool = False       # step 2.9: never planned


@dataclasses.dataclass(frozen=True)
class Demand:
    """What one job type has waiting (rule 8 and rule 9 need more than a
    count)."""
    depth: int
    cls: str = "whenever"                 # waiting | due | whenever
    waiting_since: float | None = None    # when it first had work and no card (rule 6)
    due_at: float | None = None           # the nearest due time among its queued work (rule 8)
    item_seconds: float | None = None     # measured seconds per item (rule 9)


@dataclasses.dataclass(frozen=True)
class Decision:
    card: str
    action: str
    job_type: str | None         # what the card should hold after this
    why: str                     # the RULE, in words, for the ledger
    profile: str | None = None   # the profile the card should hold after this

    @property
    def costly(self) -> bool:
        return self.action == LOAD


def _demand(v) -> Demand:
    return v if isinstance(v, Demand) else Demand(int(v))


def _age(held: Held, now: float) -> float:
    return max(0.0, now - held.since)


def pays_for_itself(depth: int, item_seconds: float | None, load_seconds: float | None, floor: int) -> bool:
    """Rule 5 with rule 9's measure: the queued work is worth the load when
    its measured time exceeds the measured load time; until both are
    measured, the queue floor decides."""
    if item_seconds is not None and load_seconds is not None:
        return depth * item_seconds >= load_seconds
    return depth >= floor


def next_in_round(waiting: list[str], round_done: frozenset[str], registry: dict[str, reg.JobType],
                  demands: dict[str, Demand] | None = None, now: float = 0.0,
                  due_horizon: float = 7200.0) -> tuple[str | None, frozenset[str]]:
    """Rules 4 and 8. The next job type to get a card, and the round after it.

    A `waiting`-class job type goes first, round or no round: a person is
    waiting. A `due` job type whose time is within the horizon goes next,
    nearest first. The rest take turns in priority order; a job type that
    has had a slice this round stands aside until every other waiting job
    type has had one, so waiting is bounded by (waiting - 1) slices
    however low its priority.
    """
    if not waiting:
        return None, round_done
    demands = demands or {}

    def d(n: str) -> Demand:
        return demands.get(n) or Demand(1)

    urgent = [n for n in waiting if d(n).cls == "waiting"]
    if urgent:
        urgent.sort(key=lambda n: (registry[n].priority, n))
        return urgent[0], round_done | {urgent[0]}
    due = [n for n in waiting if d(n).cls == "due" and d(n).due_at is not None and d(n).due_at - now <= due_horizon]
    if due:
        due.sort(key=lambda n: (d(n).due_at, registry[n].priority, n))
        return due[0], round_done | {due[0]}
    fresh = [n for n in waiting if n not in round_done]
    if not fresh:                       # everybody has had a turn: new round
        round_done, fresh = frozenset(), list(waiting)
    fresh.sort(key=lambda n: (registry[n].priority, n))
    pick = fresh[0]
    return pick, round_done | {pick}


def plan(*, now: float, held: list[Held], queues: dict,
         registry: dict[str, reg.JobType] | None = None,
         profiles: dict[str, reg.Profile] | None = None,
         rules: reg.Queueing | None = None,
         round_done: frozenset[str] = frozenset(),
         eligible: set[str] | None = None,
         ) -> tuple[list[Decision], frozenset[str]]:
    """What should happen to each card, and the round state after it.

    One decision per card, a `keep` with its reason included, so the
    ledger records why every card did what it did at every tick.
    `queues` maps a job type to its depth (an int) or a `Demand`.
    `eligible` is the job types this box can claim at all (the probe's
    programs, step 2.3); demand from any other is invisible here, so rule 6
    never loads a profile for a row no worker on this box may take (card
    the-card-manager-loads-a-profile-for-a-job-no-box-can-claim). None
    means every job type.
    """
    registry = registry if registry is not None else reg.load()
    profiles = profiles if profiles is not None else reg.profiles()
    rules = rules or reg.queueing()
    demands = {n: _demand(v) for n, v in queues.items() if eligible is None or n in eligible}
    out: list[Decision] = []

    def prof_of(jt: str | None) -> str | None:
        return registry[jt].profile if jt and jt in registry else None

    # a card holding a lease is, by construction, loaded for its holder's profile
    held = [dataclasses.replace(h, loaded=prof_of(h.job_type)) if h.job_type and h.loaded is None else h for h in held]

    resident = {h.job_type for h in held if h.job_type and not h.draining and not h.reserved}
    free_cards: list[Held] = []
    kept: dict[str, list[tuple[int, Held]]] = {}      # job type → its KEEP decisions (index, card), for rule 9

    # ── rules 1-3: what happens to cards that are already held ──────────────
    for h in held:
        if h.reserved:
            out.append(Decision(h.card, KEEP, h.job_type, "reserved: a fixed reservation the planner never touches (step 2.9)", h.loaded))
            continue
        if h.job_type is None:
            free_cards.append(h)
            continue
        depth = demands.get(h.job_type, Demand(0)).depth

        if h.draining:
            if h.in_flight > 0:
                out.append(Decision(h.card, DRAIN, h.job_type, f"draining: {h.in_flight} in flight, taking no new work", h.loaded))
            else:
                out.append(Decision(h.card, RELEASE, None, "drained: in flight is 0, card released", h.loaded))
                free_cards.append(dataclasses.replace(h, job_type=None))  # loaded survives
            continue

        if depth == 0:
            # rule 1 — a finished job does not sit on a card
            if h.in_flight > 0:
                out.append(Decision(h.card, DRAIN, h.job_type, "queue empty: draining the last requests", h.loaded))
            else:
                out.append(Decision(h.card, RELEASE, None, "queue empty and nothing in flight: released", h.loaded))
                free_cards.append(dataclasses.replace(h, job_type=None))
            continue

        age = _age(h, now)
        if age >= rules.slice_seconds:
            others = [n for n, d in demands.items() if d.depth > 0 and n != h.job_type and n not in resident
                      and n in registry and registry[n].profile]
            if others:
                # rule 3 — expiry drains, it never kills
                out.append(Decision(h.card, DRAIN, h.job_type,
                                    f"slice of {rules.slice_seconds}s spent ({age:.0f}s) and {len(others)} job "
                                    f"type(s) waiting: draining, not killing", h.loaded))
            else:
                out.append(Decision(h.card, KEEP, h.job_type,
                                    f"slice spent ({age:.0f}s) but nothing else is waiting: a handback to nobody is waste",
                                    h.loaded))
                kept.setdefault(h.job_type, []).append((len(out) - 1, h))
            continue

        # rule 2 — uninterrupted
        out.append(Decision(h.card, KEEP, h.job_type,
                            f"slice running ({age:.0f}s of {rules.slice_seconds}s), {depth} queued: uninterrupted",
                            h.loaded))
        kept.setdefault(h.job_type, []).append((len(out) - 1, h))

    # ── rules 4-6, 8: fill the free cards ───────────────────────────────────
    placed = set(resident)
    shared_by: dict[str, str] = {}          # job type served by sharing → the card
    for h in held:
        if h.job_type and not h.draining and not h.reserved:
            for n, d in demands.items():
                if d.depth > 0 and n in registry and n != h.job_type and registry[n].profile == h.loaded \
                        and registry[n].needs.can_share and registry[h.job_type].needs.can_share:
                    shared_by.setdefault(n, h.card)

    def waiting_now() -> list[str]:
        return [n for n, d in demands.items()
                if d.depth > 0 and n in registry and registry[n].profile and n not in placed and n not in shared_by]

    taken_this_tick: list[str] = []
    for card in free_cards:
        waiting = waiting_now()
        pick, round_done = next_in_round(waiting, round_done, registry, demands, now, rules.due_horizon_seconds)
        if pick is None:
            out.append(Decision(card.card, KEEP, None, "no job type has queued work", card.loaded))
            continue

        want = registry[pick]
        to = profiles.get(want.profile or "")
        was = profiles.get(card.loaded) if card.loaded else None
        cost = reg.switch_cost(was, to)
        d = demands[pick]

        # rule 5 — a swap must pay for itself. The floor guards DISCARDING a
        # resident profile; it does not apply to a COLD card, where waiting
        # saves nothing and only leaves the card idle.
        if was is not None and cost == "load":
            load_s = to.load_seconds if to else None
            if not pays_for_itself(d.depth, d.item_seconds, load_s, rules.min_queue_to_evict):
                waited = (now - d.waiting_since) if d.waiting_since is not None else 0.0
                if d.waiting_since is not None and waited >= rules.max_wait_seconds:
                    out.append(Decision(card.card, LOAD, pick,
                                        f"{pick} has waited {waited:.0f}s (rule 6: a small job never waits for ever, "
                                        f"ceiling {rules.max_wait_seconds}s): load, discarding {was.name}", to.name))
                    placed.add(pick)
                    taken_this_tick.append(pick)
                    continue
                basis = (f"{d.depth} item(s) x {d.item_seconds:.0f}s < load {load_s:.0f}s"
                         if d.item_seconds is not None and load_s is not None
                         else f"{d.depth} item(s) (floor {rules.min_queue_to_evict})")
                out.append(Decision(card.card, KEEP, None,
                                    f"{pick} wants this card but a load would discard a working {was.name} "
                                    f"profile for {basis}", card.loaded))
                round_done = round_done - {pick}      # it did not get a turn
                continue

        action = {"none": KEEP, "handover": HANDOVER, "load": LOAD}[cost]
        out.append(Decision(card.card, action, pick,
                            f"{pick} (priority {want.priority}, {d.cls}) takes this card, {d.depth} queued, {cost}: "
                            f"profile {to.name if to else want.profile}", to.name if to else want.profile))
        placed.add(pick)
        taken_this_tick.append(pick)

    # ── rule 9: a bulk job takes every free card, and gives cards back ───────
    idle = [i for i, dcs in enumerate(out) if dcs.action == KEEP and dcs.job_type is None and dcs.why == "no job type has queued work"]
    if idle and taken_this_tick:
        bulk = [n for n in taken_this_tick if demands[n].depth > 1]
        for i in idle:
            if not bulk:
                break
            n = bulk.pop(0)
            card = next(h for h in free_cards if h.card == out[i].card)
            to = profiles.get(registry[n].profile or "")
            cost = reg.switch_cost(profiles.get(card.loaded) if card.loaded else None, to)
            out[i] = Decision(card.card, {"none": KEEP, "handover": HANDOVER, "load": LOAD}[cost], n,
                              f"rule 9: {n} has {demands[n].depth} queued and nobody else waits: takes this card too ({cost})",
                              to.name if to else None)
            bulk.append(n)
    elif not free_cards and waiting_now():
        # somebody waits with no free card: a job type holding more than one card gives one back
        for n, keeps in kept.items():
            if len(keeps) >= 2:
                i, h = max(keeps, key=lambda ih: ih[1].since)
                out[i] = Decision(h.card, DRAIN, n,
                                  f"rule 9: {n} holds {len(keeps)} cards and {len(waiting_now())} job type(s) wait: "
                                  f"giving this one back (draining, not killing)", h.loaded)
                break

    return out, round_done
