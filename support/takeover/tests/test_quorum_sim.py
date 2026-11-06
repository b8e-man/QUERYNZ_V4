"""The quorum lease under faults (support/takeover/voter.md). A discrete-event simulation of the three
machines: each has its own clock running at its own rate, every link drops, delays (with stalls of seconds,
as node2's Wi-Fi does), duplicates and partitions, actions take random time and sometimes fail, boxes and
the voter crash and come back. After every event: never two boxes in a role whose database may accept a
write. Then the scenarios that must make progress: a dead primary is replaced, a pulled cable and a dead
voter change nothing, a planned switchover is fast, a returning box rejoins and never resumes a role
someone else has held since."""
import heapq
import itertools
import random

import pytest

from support.takeover import quorum as q

A, B, V = "node1", "node2", "voter"


class Sim:
    def __init__(self, seed=0, *, loss=0.0, dup=0.0, stall=0.0, drift=1e-4, primary=A):
        self.r = random.Random(seed)
        self.t = 0.0
        self.ev, self.seq = [], itertools.count()
        self.loss, self.dup, self.stall = loss, dup, stall
        self.rate = {m: 1.0 + self.r.uniform(-drift, drift) for m in (A, B, V)}
        self.off = {m: self.r.uniform(0, 1000) for m in (A, B, V)}
        self.down = set()                 # crashed machines
        self.cut = set()                  # frozenset pairs with no path at all
        self.voter_state = {"holder": primary, "epoch": 1}
        self.voter = q.Voter(self.clock(V), self.voter_state)
        self.voter.quiet_until = self.clock(V)          # a running estate, not a restart
        self.agents = {}
        for m in (A, B):
            role = "primary" if m == primary else "standby"
            self.agents[m] = q.Agent(m, B if m == A else A, role, self.clock(m), held_epoch=1 if m == primary else None)
        self.held = {A: 1 if primary == A else None, B: 1 if primary == B else None}   # what each box persists
        self.dbrole = {A: "primary" if primary == A else "standby", B: "standby" if primary == A else "primary"}
        self.checked = 0
        self.max_writable = 0
        for m in (A, B):
            self.at(self.r.uniform(0, q.RENEW), ("tick", m))
            self.at(self.r.uniform(0, q.CHECK), ("check", m))

    def clock(self, m):
        return self.t * self.rate[m] + self.off[m]

    def at(self, dt, what):
        heapq.heappush(self.ev, (self.t + dt, next(self.seq), what))

    def send(self, frm, to, msg, reply=False):
        if frm in self.down or to in self.down or frozenset((frm, to)) in self.cut:
            return
        copies = 2 if self.r.random() < self.dup else 1
        for _ in range(copies):
            if self.r.random() < self.loss:
                continue
            d = self.r.uniform(0.002, 0.1)
            if self.r.random() < self.stall:
                d += self.r.uniform(1, 5)
            self.at(d, ("deliver", frm, to, dict(msg), reply))

    def run_actions(self, m, acts):
        for a in acts:
            dur = {"PROMOTE": (1, 8), "START_PRIMARY": (2, 10), "FENCE": (0, 3), "REJOIN": (5, 60)}[a]
            fail = 1.0 if (a == "FENCE" and getattr(self, "fence_hangs", False)) else getattr(self, "fail", 0.0)
            self.at(self.r.uniform(*dur), ("done", m, a, self.r.random() > fail))

    def emit(self, m, out, acts):
        for to, msg in out:
            self.send(m, to, msg)
        self.run_actions(m, acts)

    def step(self):
        self.t, _, what = heapq.heappop(self.ev)
        kind = what[0]
        if kind == "tick":
            m = what[1]
            if m not in self.down:
                ag = self.agents[m]
                self.emit(m, *ag.tick(self.clock(m)))
                self.at(q.RENEW / self.rate[m], ("tick", m))
        elif kind == "check":
            m = what[1]
            if m not in self.down:
                ag = self.agents[m]
                self.run_actions(m, ag.check(self.clock(m)))
                if not ag.watchdog_ok(self.clock(m)):           # the hardware watchdog restarts the box
                    self.down.add(m); self.dbrole[m] = "stopped"
                    self.at(self.r.uniform(40, 90), ("restart", m))
                self.at(q.CHECK / self.rate[m], ("check", m))
        elif kind == "deliver":
            _, frm, to, msg, is_reply = what
            if to in self.down:
                pass
            elif to == V:
                self.send(V, frm, self.voter.handle(msg, self.clock(V)), reply=True)
                self.voter_state = self.voter.state()
            elif is_reply:
                self.emit(to, *self.agents[to].reply(msg, self.clock(to)))
            else:
                self.send(to, frm, self.agents[to].request(msg, self.clock(to)), reply=True)
        elif kind == "done":
            _, m, a, ok = what
            if m not in self.down:
                ag = self.agents[m]
                if a == "FENCE" and ok:
                    self.dbrole[m] = "stopped"
                elif a in ("PROMOTE", "START_PRIMARY") and ok:
                    self.dbrole[m] = "primary"
                elif a == "REJOIN":
                    other = B if m == A else A           # a rewind needs a live primary to copy from
                    ok = ok and other not in self.down and self.dbrole[other] == "primary"
                    if ok:
                        self.dbrole[m] = "standby"
                self.emit(m, *ag.done(a, ok, self.clock(m)))
                self.held[m] = ag.held_epoch
        elif kind == "crash":
            m = what[1]
            self.down.add(m)
            if m != V:
                self.dbrole[m] = "stopped"
        elif kind == "restart":
            m = what[1]
            self.down.discard(m)
            if m == V:
                self.voter = q.Voter(self.clock(V), self.voter_state)
            else:
                # the daemon at boot: a box whose database was a standby comes back as one; any other is down
                role = "standby" if self.dbrole[m] == "standby" else "down"
                self.agents[m] = q.Agent(m, B if m == A else A, role, self.clock(m), held_epoch=self.held[m])
                self.at(self.r.uniform(0, q.RENEW), ("tick", m))
                self.at(self.r.uniform(0, q.CHECK), ("check", m))
        self.check()

    def writable(self):
        return [m for m in (A, B) if m not in self.down and self.agents[m].writable()]

    def check(self):
        w = self.writable()
        self.checked += 1
        self.max_writable = max(self.max_writable, len(w))
        assert len(w) <= 1, f"two writable at t={self.t:.1f}: {w}\n" + "\n".join(
            self.agents[A].log[-8:] + self.agents[B].log[-8:])

    def run(self, until):
        while self.ev and self.ev[0][0] <= until:
            self.step()
        self.t = until

    def primary(self):
        p = [m for m in (A, B) if m not in self.down and self.agents[m].role == "primary"]
        return p[0] if len(p) == 1 else None


def test_a_quiet_estate_keeps_its_primary():
    s = Sim(1, loss=0.04, stall=0.01)
    s.run(600)
    assert s.primary() == A and s.agents[B].role == "standby"


def test_a_dead_primary_is_replaced_within_a_minute_and_rejoins_when_it_returns():
    s = Sim(2, loss=0.04, stall=0.01)
    s.run(60)
    s.at(0, ("crash", A)); s.run(61)
    s.run(61 + 60)
    assert s.primary() == B
    s.at(0, ("restart", A)); s.run(300)
    assert s.agents[A].role == "standby" and s.primary() == B


def test_a_pulled_cable_changes_nothing():
    s = Sim(3, loss=0.04, stall=0.01)
    s.run(60)
    s.cut.add(frozenset((A, B)))
    s.run(600)
    assert s.primary() == A and s.agents[B].role in ("standby", "acquiring")


def test_a_dead_voter_changes_nothing():
    s = Sim(4, loss=0.04, stall=0.01)
    s.run(60)
    s.at(0, ("crash", V)); s.run(600)
    assert s.primary() == A


def test_a_primary_cut_off_from_both_fences_itself_and_the_standby_takes_over():
    s = Sim(5)
    s.run(60)
    s.cut |= {frozenset((A, B)), frozenset((A, V))}
    s.run(150)
    assert s.agents[A].role == "down" and s.primary() == B


def test_a_fence_that_never_finishes_restarts_the_box_before_the_standby_takes_over():
    s = Sim(15)
    s.fence_hangs = True
    s.run(60)
    s.cut |= {frozenset((A, B)), frozenset((A, V))}
    s.run(200)
    assert s.primary() == B


def test_a_voter_restart_grants_no_new_holder_until_a_lease_has_run_out():
    s = Sim(6)
    s.run(60)
    s.at(0, ("crash", V)); s.at(5, ("restart", V)); s.at(5, ("crash", A))
    s.run(66)
    assert s.primary() is None or s.primary() == B
    s.run(200)
    assert s.primary() == B


def test_a_planned_switchover_takes_seconds_not_a_lease():
    s = Sim(7)
    s.run(60)
    s.emit(A, *s.agents[A].switchover(s.clock(A)))
    s.run(60 + 20)
    assert s.primary() == B


def test_a_box_that_returns_after_the_other_has_held_the_role_never_resumes_it():
    s = Sim(8)
    s.run(30)
    s.at(0, ("crash", A)); s.run(31)
    s.run(120)
    assert s.primary() == B
    s.at(0, ("crash", B)); s.at(1, ("restart", A))      # B dies too; A returns holding epoch 1
    s.run(400)
    assert s.agents[A].role != "primary", "A resumed on a history B had moved past"


def test_a_box_that_returns_after_the_other_held_and_died_never_resumes_either():
    s = Sim(18)
    s.run(30)
    s.at(0, ("crash", A)); s.run(31)
    s.run(120)
    assert s.primary() == B
    s.at(0, ("crash", B)); s.run(121 + 90)               # B's lease long gone when A returns
    s.at(0, ("restart", A))
    s.run(600)
    assert s.agents[A].role != "primary", "A resumed on a history B had moved past"


def test_a_primary_that_restarts_with_nobody_holding_since_takes_its_role_back():
    s = Sim(9)
    s.agents[B].caught_up = False           # the standby is behind, so it never asks
    s.run(30)
    s.at(0, ("crash", A)); s.at(40, ("restart", A))
    s.run(300)
    assert s.primary() == A


def test_a_standby_that_is_behind_never_asks_for_the_role():
    s = Sim(10)
    s.agents[B].caught_up = False
    s.run(30)
    s.at(0, ("crash", A)); s.run(300)
    assert s.primary() is None


@pytest.mark.parametrize("seed", range(40))
def test_chaos_never_two_writable(seed):
    s = Sim(100 + seed, loss=0.15, dup=0.05, stall=0.05, drift=1e-3)
    s.fail = 0.1
    r = random.Random(seed)
    t = 0.0
    while t < 3000:
        t += r.uniform(20, 200)
        what = r.choice(["crash", "restart", "cut", "heal", "switch"])
        m = r.choice([A, B, V])
        if what == "crash":
            s.at(t - s.t, ("crash", m))
        elif what == "restart":
            s.at(t - s.t, ("restart", m))
        elif what == "cut":
            s.cut.add(frozenset(r.sample([A, B, V], 2)))
        elif what == "heal":
            s.cut.clear()
        s.run(t)
        if what == "switch" and s.primary():
            p = s.primary()
            s.emit(p, *s.agents[p].switchover(s.clock(p)))
    assert s.checked > 200 and s.max_writable <= 1
