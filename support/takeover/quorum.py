"""THE QUORUM LEASE (support/takeover/voter.md). A box holds the primary role only while two of the three
machines agree, the box itself one: the primary keeps the role on an unexpired lease from the voter OR the
standby; the standby takes the role only on the voter's grant, once its own promises to the primary have run
out.

Pure state machines. Nothing here reads a clock, opens a socket or touches a database: every method is
given `now` (a monotonic reading of THIS machine's clock; no two machines' clocks are ever compared) and
returns the messages to send and the actions to run. The live daemons (`voterd`, `roled`) and the fault
simulation (`tests/test_quorum_sim.py`) drive the same code.

Messages are plain dicts. A request carries `id`, `op`, `box`; its reply carries the same `id`, `re` (the op
answered) and `from` (who answered).

The epoch counts holders: every new grant raises it. A box that held the role and went down may take it
back only if nobody has held it since (its epoch is still the voter's): otherwise it would start a primary
on a history the other box has moved past and discard what was written there.
"""
from __future__ import annotations

TTL = 30.0          # a lease, counted by its grantor from when it answered
MARGIN = 8.0        # the grantee counts from when it SENT, and gives up this much sooner: covers CHECK + FENCE_LIMIT and drift
RENEW = 2.0         # how often a holder renews
CHECK = 0.25        # how often a primary looks at its lease (a fence starts at most this late)
FENCE_LIMIT = 4.0   # a fence not finished in this long: the daemon stops feeding the watchdog and the box restarts
REJOIN_EVERY = 120.0   # a down box starts a rejoin at most this often

WRITABLE = ("primary", "promoting", "fencing")   # the roles in which the database may accept a write


class Voter:
    """The third machine. Holds {holder, epoch, until}; grants the role to one box at a time.

    `state()` is what must survive a restart (the daemon writes it with fsync before it answers). After a
    restart the voter cannot know whether a lease it gave is still running: it counts the stored holder's
    lease as live for TTL, so no new holder is granted before then."""

    def __init__(self, now: float, state: dict | None = None):
        state = state or {}
        self.holder = state.get("holder")
        self.epoch = int(state.get("epoch", 0))
        self.held = bool(state.get("held", False))        # maintenance: renewals go on, no new holder
        # a restart cannot know whether the stored holder's lease still runs: count it as live for TTL
        self.until = now + TTL if self.holder else now

    def state(self) -> dict:
        return {"holder": self.holder, "epoch": self.epoch, "held": self.held}

    def live(self, now: float) -> bool:
        return self.holder is not None and now < self.until

    def handle(self, msg: dict, now: float) -> dict:
        op, box = msg.get("op"), msg.get("box")
        reply = {"id": msg.get("id"), "re": op, "from": "voter", "ok": False}
        if op == "renew":
            if self.holder == box and self.live(now):
                self.until, reply["ok"] = now + TTL, True
        elif op == "acquire":
            resume = bool(msg.get("resume"))
            same = int(msg.get("held_epoch", -1)) == self.epoch
            if self.holder == box and self.live(now):
                self.until, reply["ok"] = now + TTL, True
            elif not self.live(now) and resume and self.holder == box and same:
                # the last holder taking back the role nobody has held since; allowed during maintenance
                self.until, reply["ok"] = now + TTL, True
            elif not self.live(now) and not resume and not self.held:
                self.holder, self.epoch, self.until, reply["ok"] = box, self.epoch + 1, now + TTL, True
        elif op == "release":
            if self.holder == box:
                self.until, reply["ok"] = now, True       # the epoch stays: the next grant raises it
        elif op == "hold":
            self.held, reply["ok"] = bool(msg.get("on", True)), True
        reply.update(holder=self.holder if self.live(now) else None, epoch=self.epoch, ttl=TTL, held=self.held)
        return reply


class Agent:
    """One box's role.

    primary    the database here accepts writes; renews with the voter and the peer every RENEW s; with
               neither lease live it FENCES (the address off, the database stopped)
    promoting  the voter granted: PROMOTE (a standby) or START_PRIMARY (a box resuming the role it held)
               is running; the grant is renewed meanwhile, and if it runs out first the box fences
    fencing    FENCE is running
    standby    following the primary; on each renewal promises the primary not to take over for TTL
    acquiring  the primary silent for TTL, every promise run out, and this standby caught up: asking the voter
    rejoining  REJOIN is running (rewind onto the holder's history, start as its standby)
    down       no role (fenced, stopped, or just booted): finds who holds the role and rejoins it, or, if it
               held the role last and nobody has held it since (`held_epoch`), asks for it back

    Actions the daemon runs and reports with `done(name, ok, now)`: PROMOTE, START_PRIMARY, FENCE, REJOIN.
    `caught_up` is the daemon's word that this standby was streaming when the primary went silent."""

    def __init__(self, box: str, peer: str, role: str, now: float, *, held_epoch: int | None = None):
        self.box, self.peer, self.role = box, peer, role
        self.held_epoch = held_epoch           # the epoch this box last held the role in (persisted by the daemon)
        self.epoch = held_epoch or 0
        self.voter_ok = now + TTL - MARGIN if role == "primary" else 0.0   # restarted on a running primary
        self.peer_ok = 0.0
        self.heard = now
        self.caught_up = True
        self.next_rejoin = now
        self.sent: dict[str, tuple[str, float]] = {}
        self.n = 0
        self.log: list[str] = []

    def _req(self, to: str, op: str, now: float, **extra) -> tuple[str, dict]:
        self.n += 1
        rid = f"{self.box}-{self.n}"
        self.sent[rid] = (op, now)
        while len(self.sent) > 64:
            del self.sent[next(iter(self.sent))]
        return to, dict(id=rid, op=op, box=self.box, epoch=self.epoch, **extra)

    def _renew_voter(self, now: float):
        # a holder renews as a resume of its own epoch, so an agent restarted while the voter's lease lapsed
        # (maintenance) gets the role back, and never one someone else has held since
        if self.held_epoch is None:      # a primary activated with no epoch of its own yet: claim one
            return self._req("voter", "acquire", now)
        return self._req("voter", "acquire", now, resume=True, held_epoch=self.held_epoch)

    def _say(self, now: float, text: str) -> None:
        self.log.append(f"{now:.1f} {self.box} {text}")

    def _fence(self, now: float, why: str) -> list:
        self.role, self.fence_started = "fencing", now
        self._say(now, f"fence: {why}")
        return ["FENCE"]

    # ── the clock ───────────────────────────────────────────────────────────
    def check(self, now: float) -> list:
        """Called every CHECK s: a primary (or promoting box) whose lease has run out fences at once."""
        if self.role == "primary" and now >= max(self.voter_ok, self.peer_ok):
            return self._fence(now, f"no lease from the voter or {self.peer}")
        if self.role == "promoting" and now >= self.voter_ok:
            return self._fence(now, "the grant ran out before the promotion finished")
        return []

    def watchdog_ok(self, now: float) -> bool:
        """False once a fence has run FENCE_LIMIT without finishing: the daemon stops feeding the hardware
        watchdog and the box restarts, which stops its database for certain."""
        return not (self.role == "fencing" and now - getattr(self, "fence_started", now) >= FENCE_LIMIT)

    def tick(self, now: float) -> tuple[list, list]:
        out, acts = [], []
        if self.role == "primary":
            if now >= max(self.voter_ok, self.peer_ok):
                acts += self._fence(now, f"no lease from the voter or {self.peer}")
            else:
                out += [self._renew_voter(now), self._req(self.peer, "renew", now)]
        elif self.role == "promoting":
            if now >= self.voter_ok:
                acts += self._fence(now, "the grant ran out before the promotion finished")
            else:
                out.append(self._renew_voter(now))
        elif self.role == "standby":
            if now - self.heard >= TTL and self.caught_up:
                self.role = "acquiring"
                self._say(now, f"{self.peer} silent {now - self.heard:.0f} s: asking the voter")
        if self.role == "acquiring":
            out.append(self._req("voter", "acquire", now))
        elif self.role == "down":
            if self.held_epoch is not None:
                out.append(self._req("voter", "acquire", now, resume=True, held_epoch=self.held_epoch))
            else:
                out.append(self._req("voter", "query", now))
            out.append(self._req(self.peer, "status", now))
        return out, acts

    # ── replies to our requests ─────────────────────────────────────────────
    def reply(self, msg: dict, now: float) -> tuple[list, list]:
        out, acts = [], []
        op, sent_at = self.sent.pop(msg.get("id"), (None, None))
        if op is None:
            return out, acts                                 # unknown, duplicated or forgotten
        frm = msg.get("from")
        until = sent_at + float(msg.get("ttl", TTL)) - MARGIN
        holder = msg.get("holder")
        if frm == "voter":
            self.epoch = max(self.epoch, int(msg.get("epoch", 0)))
            if op in ("renew", "acquire") and msg.get("ok") and now < until:
                if self.role in ("primary", "promoting"):
                    self.voter_ok = max(self.voter_ok, until)
                    if self.role == "primary" and self.held_epoch is None:
                        self.held_epoch = self.epoch
                elif self.role == "acquiring":
                    self.voter_ok, self.role, self.held_epoch = until, "promoting", self.epoch
                    self._say(now, f"granted, epoch {self.epoch}: promoting")
                    acts.append("PROMOTE")
                elif self.role == "down" and self.held_epoch is not None and op == "acquire":
                    self.voter_ok, self.role = until, "promoting"
                    self._say(now, f"granted back the role it held, epoch {self.epoch}: starting as primary")
                    acts.append("START_PRIMARY")
            elif not msg.get("ok") or op == "query":
                if (self.role == "acquiring" and holder and holder != self.box
                        and now >= getattr(self, "handover_until", 0.0)):
                    self.role, self.heard = "standby", now           # the voter says the primary lives
                elif self.role == "down" and holder and holder != self.box:
                    if self.held_epoch is not None and int(msg.get("epoch", 0)) != self.held_epoch:
                        self.held_epoch = None                       # someone has held it since: never resume
                    acts += self._rejoin(now)
                elif self.role == "down" and op == "acquire" and int(msg.get("epoch", 0)) != self.held_epoch:
                    self.held_epoch = None
        elif frm == self.peer:
            if op == "renew" and msg.get("ok") and self.role == "primary" and now < until:
                self.peer_ok = max(self.peer_ok, until)
            elif op == "status" and self.role == "down" and msg.get("role") == "primary" and self.held_epoch is None:
                acts += self._rejoin(now)
        return out, acts

    def _rejoin(self, now: float) -> list:
        if now < self.next_rejoin:
            return []
        self.next_rejoin, self.role = now + REJOIN_EVERY, "rejoining"
        self._say(now, "rejoining as the standby")
        return ["REJOIN"]

    # ── requests from the peer ──────────────────────────────────────────────
    def request(self, msg: dict, now: float) -> dict:
        op = msg.get("op")
        reply = {"id": msg.get("id"), "re": op, "ok": False, "from": self.box, "ttl": TTL}
        if msg.get("box") != self.peer:
            return reply
        if op == "renew" and self.role == "standby":
            self.heard, reply["ok"] = now, True       # the promise: no takeover before heard + TTL
        elif op == "status":
            reply.update(ok=True, role=self.role)
        elif op == "handover" and self.role == "standby":
            # a planned switchover: the primary has stopped and released at the voter; take over now
            self.heard, reply["ok"] = now - TTL, True
            self.handover_until = now + 10.0      # the release may reach the voter after our first ask
        return reply

    # ── actions finished ────────────────────────────────────────────────────
    def switchover(self, now: float) -> tuple[list, list]:
        """A planned move of the role to the peer: stop cleanly here, then release at the voter and tell the
        peer to take over at once (no 30 s wait). Only from a primary."""
        if self.role != "primary":
            return [], []
        self.handing_over = True
        return [], self._fence(now, "planned switchover")

    def done(self, action: str, ok: bool, now: float) -> tuple[list, list]:
        out, acts = [], []
        if action in ("PROMOTE", "START_PRIMARY"):
            if self.role != "promoting":
                return out, acts
            if ok and now < self.voter_ok:
                self.role, self.peer_ok, self.held_epoch = "primary", 0.0, self.epoch
                self._say(now, f"primary, epoch {self.epoch}")
            else:
                acts += self._fence(now, f"{action} {'failed' if not ok else 'finished after the grant ran out'}")
        elif action == "FENCE" and self.role == "fencing":
            if not ok:
                self._say(now, "fence failed: trying again")      # the daemon's watchdog restarts the box if it never succeeds
                acts.append("FENCE")
                return out, acts
            self.role, self.voter_ok, self.peer_ok = "down", 0.0, 0.0
            self._say(now, "fenced")
            if getattr(self, "handing_over", False):
                self.handing_over, self.held_epoch = False, None
                out += [self._req("voter", "release", now), self._req(self.peer, "handover", now)]
        elif action == "REJOIN" and self.role == "rejoining":
            if ok:
                self.role, self.heard, self.held_epoch = "standby", now, None
                self._say(now, "standby again")
            else:
                self.role = "down"
                self._say(now, "rejoin failed: stays down (a full copy is a person's call)")
        return out, acts

    def writable(self) -> bool:
        return self.role in WRITABLE
