"""WHAT EACH CARD HOLDS, and the model server beside the old one (plan steps
2.7, 2.9, 2.15; hard limits 23 and 25).

The worker's card manager registers this box's cards from the probe, marks
the reserved ones (the carve-out's, step 2.9: never touched), and acts on
the planner's decisions for the rest: a `load` starts the new estate's own
model server on the card with the profile's weights and settings, waits
for it to answer, READS BACK the model it says it serves (a wrong model
answering was the old estate's 13.8%), measures the load time (rule 9) and
writes the swap to the ledger with the planner's reason; a `release` or a
`drain` changes the card's lease; an `unload` stops the server.

THE SERVER IS A CHILD OF THE WORKER, not a systemd unit: the card's state
lives in the scheduler's tables and the swap ledger, the worker supervises
the process, and a worker that dies takes its servers with it (the other
box's worker then loads what the queue needs there). The binary is the
estate's own copy (`support.installer` puts it beside the old build, never
over it); until it is installed the old build's path is used read-only,
which is allowed: it is a program, not the frozen product's servers.

Ports: 8110 + card index, far from the carve-out's 8020/8032/8090 and the
product's 8300/8301.

A STANDING SERVER IS NOT A CHILD (ruling 121). Radiance serves Flash-Next on
both of node2's cards from its own unit, `qv4-radiance`, so a boot brings it
back without a worker. Its profile names the unit, the port and the number
of cards; the manager asks that port every tick, reads the model back, and
marks the cards as holding the profile when it answers with the profile's
model, or as held and reserved when it does not (starting, stopped, wrong
model). The planner sees those cards as reserved and never plans them; a
load of a standing profile, or of a view on one, is never acted on. The
standing load is recorded in the swap ledger when this worker first sees
the server answer, with the time since the unit started when it saw the
server down before (a measured load), and a `died` line when it stops.

THE NIGHT WINDOW (ruling 129) is the one time the manager touches that unit.
Inside the hours of jobs.toml `[night_window]` (22:00 to 05:45 NZDT), when
page-reader work is queued and no piece of a view on the standing profile is
running or leased, the manager stops the unit, waits until the port is down
and the cards have released the model (measured with rocm-smi), holds the
standing server's other card reserved for the frozen product's OCR server,
and leaves the window's card cold; the planner then loads the page reader
there and runs the pieces. When the page queue is empty, or a text-reader or
review piece is due, or the window closes, the page reader drains (never
killed), is unloaded, the unit is started again, the model is read back on
its port, and the cards are marked standing as today. Each stop and start is
a `stop` or `start` line in the swap ledger with its reason and the measured
seconds; a start that fails is a `failed` line, an alarm and a note in the
inbox for the integrator, and the manager tries again each tick. Outside the
window the unit is never stopped or planned. A marker file under <live>
records a stop until the start, so a worker restarted in between starts the
unit again rather than leaving it down. The clock half is `night.py`.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import signal
import subprocess
import time

from support.scheduler import LIVE
from support.scheduler import night
from support.scheduler import policy
from support.scheduler import probe as pb
from support.scheduler import queue as q
from support.scheduler import registry as reg
from support.scheduler import runs

PORT_BASE = 8110
LOAD_TIMEOUT_S = 900          # a 21 GB load from a cold page cache takes minutes
STOP_GRACE_S = 20             # the server hangs ~45 s after TERM; 20 s then KILL (old lesson)
LOGS = os.path.join(LIVE, "scheduler", "servers")
# the night window (ruling 129)
STOP_TIMEOUT_S = 150          # the unit's TimeoutStopSec (60) and podman's own 30, then the cards' release
START_TIMEOUT_S = 330         # the unit's TimeoutStartSec (300); Radiance answered in 21.6 s on 29 October
RELEASE_SLACK_GB = 2.0        # a card has released the model when its used memory is within this of (total - the model)
NIGHT_REST_S = 900            # after a start, no new stop for this long: a page row given back for two minutes is not a new night
NIGHT_MARK = os.path.join(LIVE, "scheduler", "night-window.json")
INBOX_CARDS = os.environ.get("QV4_INBOX_CARDS") or "/home/user/querynzv4-work/inbox/cards"
_CATALOGUE = object()


def server_binary(profile_programs: dict, prefer: str = None, profile: reg.Profile = None) -> str | None:
    """The estate's own program, as profiles.toml `[server] binary` says:
    the build from source ("built"), or the copy of the old build ("copy").
    One that is missing falls back to the other; the old build itself,
    read-only, only until the installer has put either beside it. A profile
    that names its own `binary` gets that program or nothing: TeleOCR's
    conversion loads only on the patched server, and the unpatched one
    standing in for it was the 19 October failure."""
    if profile is not None and profile.binary:
        return profile_programs.get(profile.binary)
    prefer = prefer or reg.server_binary_setting()
    order = ("qv4-llama-server-built", "qv4-llama-server") if prefer == "built" else ("qv4-llama-server", "qv4-llama-server-built")
    for name in order:
        if profile_programs.get(name):
            return profile_programs[name]
    return profile_programs.get("llama-server")


def server_argv(binary: str, prof: reg.Profile, card: int, port: int, models_dir: str = None) -> list[str]:
    """The llama-server command for a profile on a card. Geometry is
    DERIVED from the profile; the alias is the model name every call will
    demand."""
    weights = prof.weight_paths(models_dir)
    argv = [binary, "-m", weights[0], "-ngl", "999", *prof.serve_flags(), "--host", "127.0.0.1", "--port", str(port),
            "--alias", prof.model, "--metrics"]
    if len(weights) > 1:
        argv += ["--mmproj", weights[1]]
    argv += list(prof.flags)
    return argv


def unit_active_seconds(unit: str) -> float | None:
    """Seconds since a user unit last became active, from systemd's own
    monotonic clock; None when it cannot say."""
    try:
        r = subprocess.run(["systemctl", "--user", "show", "-p", "ActiveEnterTimestampMonotonic", "--value", unit],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.match(r"\s*(\d+)", r.stdout or "")
    if r.returncode or not m or int(m.group(1)) == 0:
        return None
    return round(time.clock_gettime(time.CLOCK_MONOTONIC) - int(m.group(1)) / 1e6, 1)


def systemctl_user(verb: str, unit: str, timeout: float = START_TIMEOUT_S + 30) -> int:
    """`systemctl --user <verb> <unit>`: the return code, non-zero on any
    failure. `start` and `stop` block until the unit is up or gone (the unit
    is Type=notify), so the measured seconds around a call are real."""
    try:
        r = subprocess.run(["systemctl", "--user", verb, unit], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return -1
    return r.returncode


class Server:
    def __init__(self, proc: subprocess.Popen, prof: reg.Profile, card: int, port: int, started: float):
        self.proc, self.prof, self.card, self.port, self.started = proc, prof, card, port, started


class Manager:
    """One per worker. Pure decisions come from `policy.plan`; this performs
    them on this box's cards and keeps the `cards` table true."""

    def __init__(self, *, popen=None, ask=None, models_dir: str = None, log=None, reservations: list = None,
                 active_seconds=None, window=_CATALOGUE, systemctl=None, read_cards=None, clock=None, sleep=None,
                 mark: str = None, inbox: str = None):
        self.popen = popen or subprocess.Popen
        self.ask = ask or pb.ask_server
        self.models_dir = models_dir
        self.reservations = reservations if reservations is not None else reg.reservations()
        # the night window (ruling 129): the window from the catalogue, and what acting on it needs, all injectable
        self.window: night.Window | None = reg.night_window() if window is _CATALOGUE else window
        self.systemctl = systemctl or systemctl_user
        self.read_cards = read_cards or pb.cards
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.mark = mark or NIGHT_MARK
        self.inbox = inbox or INBOX_CARDS
        self.night_state = "standing"                # standing | page | closing | restarting
        self.night_reason: str | None = None
        self.night_page_card: int | None = None
        self.night_hold_cards: list[int] = []
        self.night_rest_until = 0.0                  # epoch seconds before which no new stop is attempted
        self.night_alarmed = False                   # one alarm and one note per failed-start episode
        self.night_logged: set[str] = set()          # lines said once per state
        self.servers: dict[int, Server] = {}
        self.round_done: frozenset = frozenset()
        self.holder_since: dict[int, float] = {}
        self.failed_loads: dict[str, tuple] = {}     # profile → the box's programs when its load failed here
        self.active_seconds = active_seconds or unit_active_seconds
        self.standing_seen: dict[str, bool] = {}     # standing profile → answering at the last look (absent: not yet looked)
        self.skipped_loads: set[str] = set()         # standing profiles a planned load was refused for, logged once
        self.log = log
        self.worker = None

    # ── registration ─────────────────────────────────────────────────────────

    def start(self, worker) -> None:
        self.worker = worker
        self.log = self.log or worker.log
        self.register_cards(worker)
        self.night_recover(worker)

    def register_cards(self, worker) -> None:
        """This box's cards, from the probe. A card this worker did not load
        is cold to it: a server left by an earlier worker is a stray (it
        answers on the card's port) and is reported, never adopted."""
        reserved = {r.key: r for r in self.reservations}
        live_others = {w["name"] for w in q.workers(worker.conn, worker.schema)
                       if w["name"] != worker.name and w["state"] == "up"
                       and (q.utcnow() - w["last_seen"]).total_seconds() < worker.alarm_after_s}
        owned_by_other = {c["card"]: c["worker"] for c in q.cards(worker.conn, worker.schema, worker.box)
                          if c["worker"] in live_others and not c["reserved"]}
        for c in worker.profile.get("cards") or []:
            key = f"{worker.box}:{c['index']}"
            if c["index"] in owned_by_other:
                # two workers on one box (the rehearsal): the first to register manages the card; the
                # other runs jobs on its profile but never loads or unloads there
                self.log(f"card {c['index']}: managed by {owned_by_other[c['index']]}; this worker runs jobs on it but does not place")
                continue
            fields = dict(memory_total_gb=c["memory_total_gb"], memory_used_gb=c["memory_used_gb"], product=c.get("product"),
                          worker=worker.name, profile=None, port=None, pid=None, holder=None, holder_since=None, draining=False,
                          slots=None, slots_busy=None)
            if key in reserved:
                fields.update(reserved=True, reserved_why=reserved[key].why)
            elif c["index"] not in self.servers:
                stray = self.ask(PORT_BASE + c["index"])
                if stray["healthy"]:
                    self.log(f"card {c['index']}: a stray server answers on :{PORT_BASE + c['index']} ({stray['served']!r}); "
                             f"not adopted, this worker will not use that port until it is gone")
                    q.record_swap(worker.conn, worker.schema, worker.box, c["index"], "stray", "a server this worker did not start "
                                  "answers on the card's port", served_model=stray["served"], by_worker=worker.name, ok=False)
            q.upsert_card(worker.conn, worker.schema, worker.box, c["index"], **fields)
        self.mark_standing(worker)

    # ── standing servers (ruling 121) ────────────────────────────────────────

    def standing_profiles(self, worker) -> list[reg.Profile]:
        """The standing servers this box runs: the profile's program is here."""
        progs = worker.profile.get("programs") or {}
        return [p for p in worker.profiles.values() if p.standing and progs.get(p.binary)]

    def standing_cards(self, worker, prof: reg.Profile) -> list[int]:
        reserved = {r.key for r in self.reservations}
        idx = sorted(c["index"] for c in worker.profile.get("cards") or [] if f"{worker.box}:{c['index']}" not in reserved)
        return [i for i in idx if i not in self.servers][:prof.cards]

    def mark_standing(self, worker) -> None:
        """Read each standing server's model back and mark its cards."""
        for prof in self.standing_profiles(worker):
            if self.night_holds(prof.name):
                continue              # the night window holds its cards; night_tick marks them (ruling 129)
            a = self.ask(prof.port)
            up = bool(a["healthy"]) and a["served"] == prof.model
            was = self.standing_seen.get(prof.name)
            idx = self.standing_cards(worker, prof)
            for card in idx:
                if up:
                    q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=prof.name, port=prof.port, pid=None,
                                  holder=None, draining=False, slots=prof.slots, slots_busy=None, reserved=False,
                                  reserved_why=None, worker=worker.name)
                else:
                    why = (f"{prof.unit} holds this card for {prof.name}; it answers on :{prof.port} with {a['served']!r}, "
                           f"not {prof.model!r}" if a["served"] else f"{prof.unit} holds this card for {prof.name}; "
                           f"not answering on :{prof.port}")
                    if self.night_state == "restarting" and self.window and prof.name == self.window.standing:
                        why += "; it did not start again after the night window (ruling 129); the worker tries again each tick"
                    q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=None, port=None, pid=None, holder=None,
                                  draining=False, slots=None, slots_busy=None, reserved=True, reserved_why=why,
                                  worker=worker.name)
            if up and was is not True:
                seconds = self.active_seconds(prof.unit) if was is False else None
                for card in idx:
                    q.record_swap(worker.conn, worker.schema, worker.box, card, "load",
                                  f"standing: {prof.unit} serves {prof.model} on :{prof.port} across {len(idx)} card(s)",
                                  to_profile=prof.name, by_worker=worker.name, load_seconds=seconds, served_model=a["served"],
                                  ok=True, detail="seen answering after it was down" if was is False else "seen answering")
                runs.placement(",".join(f"{worker.box}:{c}" for c in idx), "standing", None, f"{prof.unit} answering", prof.name)
                self.log(f"cards {idx}: {prof.name} answering on :{prof.port} ({prof.unit})"
                         + (f", {seconds:.0f}s after the unit started" if seconds is not None else ""))
            elif not up and was is True:
                for card in idx:
                    q.record_swap(worker.conn, worker.schema, worker.box, card, "died",
                                  f"standing: {prof.unit} stopped answering with {prof.model}", from_profile=prof.name,
                                  by_worker=worker.name, served_model=a["served"], ok=False)
                self.log(f"cards {idx}: {prof.name} not answering on :{prof.port}; held for {prof.unit}")
            self.standing_seen[prof.name] = up

    # ── the tick ─────────────────────────────────────────────────────────────

    def held(self, worker, now_s: float) -> list[policy.Held]:
        out = []
        for c in q.cards(worker.conn, worker.schema, worker.box):
            if c["worker"] != worker.name and not c["reserved"]:
                continue                      # another worker's card on this box
            if c["reserved"] or (c["profile"] in worker.profiles and worker.profiles[c["profile"]].standing):
                # a fixed reservation, or a standing server's card: never planned
                out.append(policy.Held(f"{worker.box}:{c['card']}", None, reserved=True, loaded=c["profile"]))
                continue
            in_flight = 0
            if c["card"] in self.servers and c["port"]:
                a = self.ask(c["port"])
                if a["total"]:
                    in_flight = a["total"] - max(a["free"], 0)
            # a job this worker is running against the card's profile is in flight whether or not
            # it has a request open at this instant: the card is not swapped under it
            with worker.lock:
                busy_jobs = sum(1 for r in worker.running.values() if r.jt.profile and r.jt.profile == c["profile"])
            in_flight = max(in_flight, busy_jobs)
            out.append(policy.Held(f"{worker.box}:{c['card']}", c["holder"], since=self.holder_since.get(c["card"], now_s),
                                   draining=bool(c["draining"]), in_flight=in_flight, loaded=c["profile"]))
        return out

    @staticmethod
    def _programs_key(worker) -> tuple:
        return tuple(sorted((k, v or None) for k, v in (worker.profile.get("programs") or {}).items()))

    def claimable(self, worker) -> set[str]:
        """The job types this box could ever claim: enabled, every required
        program present (the probe's eligibility, the same test the worker's
        claim applies), and not on a profile whose load failed here while the
        box's programs have been as they are now. The planner sees no other
        demand, so rule 6 never discards a working profile for a row nobody
        here may take (19 October: three swaps for TeleOCR's row 74)."""
        key = self._programs_key(worker)
        progs = worker.profile.get("programs") or {}
        out = set()
        for jt in worker.registry.values():
            if not jt.enabled or pb.missing_programs(worker.profile, jt.requires):
                continue
            if jt.profile and self.failed_loads.get(jt.profile) == key:
                continue
            prof = reg.server_of(worker.profiles, jt.profile) if jt.profile in worker.profiles else None
            if prof is not None and prof.binary and not progs.get(prof.binary):
                continue                  # its profile's own server is not on this box
            out.add(jt.name)
        return out

    def tick(self, worker, now) -> None:
        now_s = now.timestamp()
        self._reap_dead_servers(worker)
        demands = q.demands(worker.conn, worker.schema, worker.registry, now=now)
        self.night_tick(worker, now, demands)
        self.mark_standing(worker)
        measured = q.measured_load_seconds(worker.conn, worker.schema)
        profiles = {n: (p if p.load_seconds is not None or n not in measured else
                        reg.Profile(**{**p.__dict__, "load_seconds": measured[n]})) for n, p in worker.profiles.items()}
        held = self.held(worker, now_s)
        if not held:
            return
        eligible = self.claimable(worker)
        if self.night_state == "page":
            eligible &= self._jobs_on(worker, {self.window.profile})     # the window's card is for the page reader
        elif self.night_state == "closing":
            eligible -= self._jobs_on(worker, {self.window.profile})     # nothing new is placed while it drains
        decisions, self.round_done = policy.plan(now=now_s, held=held, queues=demands, registry=worker.registry,
                                                 profiles=profiles, rules=worker.rules, round_done=self.round_done,
                                                 eligible=eligible)
        for d in decisions:
            self.apply(worker, d, now_s)
        if self.night_state == "closing" and self.night_page_card is not None:
            # a release above clears the flag, and the worker claims after this tick: the page card stays draining
            # until the page reader is unloaded, so a piece given back is not claimed again on it
            q.upsert_card(worker.conn, worker.schema, worker.box, self.night_page_card, draining=True)

    def _reap_dead_servers(self, worker) -> None:
        for card, s in list(self.servers.items()):
            if s.proc.poll() is not None:
                self.log(f"card {card}: the server for {s.prof.name} exited ({s.proc.returncode}); card is cold")
                runs.placement(f"{worker.box}:{card}", "died", None, f"server exited {s.proc.returncode}", s.prof.name)
                q.record_swap(worker.conn, worker.schema, worker.box, card, "died", f"server exited {s.proc.returncode}",
                              from_profile=s.prof.name, by_worker=worker.name, ok=False)
                q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=None, port=None, pid=None, holder=None,
                              draining=False, slots=None, slots_busy=None)
                del self.servers[card]

    # ── the night window (ruling 129) ────────────────────────────────────────

    def night_profile(self, worker) -> reg.Profile | None:
        """The standing profile the window may stop, when this box runs it."""
        w = self.window
        if w is None:
            return None
        prof = worker.profiles.get(w.standing)
        if prof is None or not prof.standing or not (worker.profile.get("programs") or {}).get(prof.binary):
            return None
        return prof

    def night_holds(self, name: str) -> bool:
        """Whether the window holds this standing profile's cards right now."""
        return self.window is not None and name == self.window.standing and self.night_state in ("page", "closing")

    def _jobs_on(self, worker, profiles: set[str]) -> set[str]:
        return {n for n, jt in worker.registry.items() if jt.profile in profiles}

    def _views(self, worker, standing: str) -> set[str]:
        return {n for n, p in worker.profiles.items() if p.on == standing}

    def _page_depth(self, worker, demands: dict) -> int:
        """Pieces waiting for the window's profile, among the job types this box may claim."""
        jobs = self._jobs_on(worker, {self.window.profile}) & self.claimable(worker)
        return sum(demands[n].depth for n in jobs if n in demands)

    def _page_running(self, worker) -> int:
        with worker.lock:
            return sum(1 for r in worker.running.values() if r.jt.profile == self.window.profile)

    def _views_busy(self, worker, demands: dict, standing: str) -> str | None:
        """A piece of a view on the standing server running here or leased anywhere: the stop waits."""
        views = self._views(worker, standing)
        with worker.lock:
            running = sorted(r.jt.name for r in worker.running.values() if r.jt.profile in views)
        if running:
            return f"{running[0]} is running here"
        leased = sorted(n for n in self._jobs_on(worker, views) if n in demands and demands[n].leased > 0)
        if leased:
            return f"{leased[0]} has {demands[leased[0]].leased} row(s) leased"
        return None

    def _views_due(self, worker, demands: dict, standing: str, now_s: float) -> str | None:
        """A view piece that is due (rule 8: someone waiting, or due within the horizon): the window closes early."""
        views = self._views(worker, standing)
        for n in sorted(self._jobs_on(worker, views)):
            d = demands.get(n)
            if d is None or d.depth <= 0:
                continue
            if d.cls == "waiting":
                return f"{n} has {d.depth} waiting-class piece(s) queued"
            if d.cls == "due" and d.due_at is not None and d.due_at - now_s <= worker.rules.due_horizon_seconds:
                return f"{n} is due in {max(0.0, d.due_at - now_s):.0f}s"
        return None

    def _once(self, key: str, msg: str) -> None:
        if key not in self.night_logged:
            self.night_logged.add(key)
            self.log(msg)

    def night_tick(self, worker, now: dt.datetime, demands: dict) -> None:
        """One look at the clock and the queue: open the window, close it, or keep trying to start the unit."""
        w, prof = self.window, self.night_profile(worker)
        if w is None or prof is None:
            return
        now_s = now.timestamp()
        inside = night.in_window(now, w)
        if self.night_state == "standing":
            if not inside or now_s < self.night_rest_until:
                return
            depth = self._page_depth(worker, demands)
            if depth <= 0:
                return
            busy = self._views_busy(worker, demands, prof.name)
            if busy:
                self._once("busy", f"night window: {depth} page piece(s) wait but {busy}; {prof.unit} stays up")
                return
            if not self.standing_seen.get(prof.name):
                self._once("down", f"night window: {prof.unit} is not answering on :{prof.port}, so there is nothing to "
                                   f"stop; the page reader waits for it (ruling 121: the worker does not start it)")
                return
            self._night_stop(worker, prof, now, depth)
        elif self.night_state == "page":
            reason = None
            if not inside:
                reason = f"the window closed at {w.end} {w.timezone}"
            elif self._page_depth(worker, demands) <= 0:
                reason = "the page queue is empty"
            else:
                reason = self._views_due(worker, demands, prof.name, now_s)
            if reason is None:
                return
            self.night_state, self.night_reason = "closing", reason
            self.night_logged.clear()
            self.log(f"night window: closing ({reason}); {w.profile} drains and {prof.unit} starts again")
            self._night_close(worker, prof, now)
        elif self.night_state == "closing":
            self._night_close(worker, prof, now)
        elif self.night_state == "restarting":
            if self.standing_seen.get(prof.name):
                self.log(f"night window: {prof.unit} is answering again; cards standing as today")
                self._night_done(now)
                return
            self._night_start(worker, prof, now)

    def _wait_released(self, prof: reg.Profile, idx: list[int], timeout: float = STOP_TIMEOUT_S) -> bool:
        """True once the port is down and each card has released the model
        (its used memory is within RELEASE_SLACK_GB of total less the
        model's measured share). A card read that fails is not data: then
        the port alone decides, as `systemctl stop` blocks until the
        container is gone."""
        t0 = self.clock()
        need = (prof.memory_gb or 0.0)
        while True:
            a = self.ask(prof.port)
            cards = self.read_cards()
            freed = cards is None or all(
                c.get("memory_used_gb") is None or c.get("memory_total_gb") is None
                or c["memory_used_gb"] <= c["memory_total_gb"] - need + RELEASE_SLACK_GB
                for c in cards if c.get("index") in idx)
            if not a["healthy"] and freed:
                return True
            if self.clock() - t0 >= timeout:
                return False
            self.sleep(2)

    def _wait_standing(self, prof: reg.Profile, timeout: float = START_TIMEOUT_S) -> str | None:
        """The model the port answers with once it is the profile's, or the
        last thing it answered with when the timeout passes."""
        t0 = self.clock()
        last = None
        while True:
            a = self.ask(prof.port)
            if a["healthy"] and a["served"] == prof.model:
                return a["served"]
            last = a["served"] or last
            if self.clock() - t0 >= timeout:
                return last
            self.sleep(2)

    def _night_stop(self, worker, prof: reg.Profile, now: dt.datetime, depth: int) -> None:
        w = self.window
        idx = self.standing_cards(worker, prof)
        if w.card not in idx:
            self._once("card", f"night window: card {w.card} is not one of {prof.name}'s cards {idx}; the window cannot open")
            return
        why = (f"night window (ruling 129): {depth} page piece(s) queued for {w.profile}, no text-reader or review piece "
               f"running or leased; {prof.unit} stopped for the page reader on card {w.card}")
        self.log(f"night window: stopping {prof.unit}: {depth} page piece(s) queued for {w.profile}")
        t0 = self.clock()
        rc = self.systemctl("stop", prof.unit)
        released = self._wait_released(prof, idx) if rc == 0 else False
        seconds = round(self.clock() - t0, 1)
        if not released:
            detail = f"systemctl stop returned {rc}" if rc else f"the cards still hold the model after {seconds:.0f}s"
            for card in idx:
                q.record_swap(worker.conn, worker.schema, worker.box, card, "failed", why, from_profile=prof.name,
                              by_worker=worker.name, load_seconds=seconds, ok=False, detail=detail)
            self.log(f"night window: stop of {prof.unit} FAILED: {detail}; starting it again, no new stop for {NIGHT_REST_S}s")
            self.systemctl("reset-failed", prof.unit)
            self.systemctl("start", prof.unit)
            self.standing_seen[prof.name] = False          # mark_standing records its return as a measured load
            self.night_rest_until = now.timestamp() + NIGHT_REST_S
            return
        for card in idx:
            q.record_swap(worker.conn, worker.schema, worker.box, card, "stop", why, from_profile=prof.name,
                          by_worker=worker.name, load_seconds=seconds, ok=True,
                          detail=f"{prof.unit} stopped; the cards released {prof.model} in {seconds:.1f}s")
        runs.placement(",".join(f"{worker.box}:{c}" for c in idx), "stop", None, why, prof.name)
        hold = [c for c in idx if c != w.card]
        cold = dict(profile=None, port=None, pid=None, holder=None, holder_since=None, draining=False, slots=None,
                    slots_busy=None, worker=worker.name)
        for card in hold:
            q.upsert_card(worker.conn, worker.schema, worker.box, card, reserved=True,
                          reserved_why=f"night window: held for the frozen product's OCR server (:8032, hard limit 23) while "
                                       f"{prof.unit} is stopped; the page reader takes card {w.card}", **cold)
        q.upsert_card(worker.conn, worker.schema, worker.box, w.card, reserved=False, reserved_why=None, **cold)
        self.night_page_card, self.night_hold_cards = w.card, hold
        self.standing_seen[prof.name] = False
        self.night_state, self.night_reason, self.night_alarmed = "page", None, False
        self.night_logged.clear()
        self._write_mark(worker, prof, now, why)
        self.log(f"night window: {prof.unit} stopped in {seconds:.1f}s; card {w.card} free for {w.profile}, "
                 f"card(s) {hold} held for the OCR server")

    def _night_close(self, worker, prof: reg.Profile, now: dt.datetime) -> None:
        w, card = self.window, self.night_page_card
        if card is not None and self._page_running(worker):
            q.upsert_card(worker.conn, worker.schema, worker.box, card, draining=True)
            self._once("drain", f"night window: a {w.profile} piece is in flight on card {card}; draining, not killing, "
                                f"before {prof.unit} starts")
            return
        if card is not None:
            self.unload(worker, card, f"night window: {self.night_reason}; {prof.unit} starts again")
        self._night_start(worker, prof, now)

    def _night_start(self, worker, prof: reg.Profile, now: dt.datetime) -> None:
        idx = self.standing_cards(worker, prof)
        why = f"night window (ruling 129): {self.night_reason}; {prof.unit} started again"
        self.log(f"night window: starting {prof.unit}: {self.night_reason}")
        t0 = self.clock()
        self.systemctl("reset-failed", prof.unit)          # three failed starts in ten minutes would otherwise refuse a fourth
        rc = self.systemctl("start", prof.unit)
        served = self._wait_standing(prof) if rc == 0 else None
        seconds = round(self.clock() - t0, 1)
        if served == prof.model:
            for card in idx:
                q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=prof.name, port=prof.port, pid=None,
                              holder=None, holder_since=None, draining=False, slots=prof.slots, slots_busy=None,
                              reserved=False, reserved_why=None, worker=worker.name)
                q.record_swap(worker.conn, worker.schema, worker.box, card, "start", why, to_profile=prof.name,
                              by_worker=worker.name, load_seconds=seconds, served_model=served, ok=True,
                              detail=f"{prof.unit} answering with {served!r} on :{prof.port} after {seconds:.1f}s")
            runs.placement(",".join(f"{worker.box}:{c}" for c in idx), "start", None, why, prof.name)
            self.standing_seen[prof.name] = True
            self.log(f"night window: {prof.unit} answering again in {seconds:.1f}s; cards {idx} standing as today")
            self._night_done(now)
            return
        if rc:
            detail = f"systemctl start returned {rc}"
        elif served:
            detail = f"after {seconds:.0f}s :{prof.port} answers with {served!r}, not {prof.model!r}"
        else:
            detail = f"not answering on :{prof.port} after {seconds:.0f}s"
        for card in idx:
            q.record_swap(worker.conn, worker.schema, worker.box, card, "failed", why, to_profile=prof.name,
                          by_worker=worker.name, load_seconds=seconds, served_model=served, ok=False, detail=detail)
            q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=None, port=None, pid=None, holder=None,
                          holder_since=None, draining=False, slots=None, slots_busy=None, reserved=True,
                          reserved_why=f"{prof.unit} holds this card for {prof.name}; it did not start again after the "
                                       f"night window ({detail}); the worker tries again each tick", worker=worker.name)
        self.standing_seen[prof.name] = False
        self.night_state = "restarting"
        self.log(f"night window: {prof.unit} did NOT start again: {detail}; trying again each tick")
        if not self.night_alarmed:
            self.night_alarmed = True
            note = self._night_note(worker, prof, now, detail)
            worker.alarm(f"qv4 {worker.box}: {prof.unit} did not start after the night window",
                         f"{detail}; the text reader and review have no card until it answers; the worker tries again "
                         f"each tick; the integrator's note is {note}")

    def _night_done(self, now: dt.datetime) -> None:
        self.night_state, self.night_reason = "standing", None
        self.night_page_card, self.night_hold_cards = None, []
        self.night_logged.clear()
        self.night_alarmed = False
        self.night_rest_until = now.timestamp() + NIGHT_REST_S
        try:
            os.remove(self.mark)
        except OSError:
            pass

    def _write_mark(self, worker, prof: reg.Profile, now: dt.datetime, why: str) -> None:
        """The stop, on disk until the start: a worker restarted in between
        finds it and starts the unit again instead of leaving it down."""
        try:
            os.makedirs(os.path.dirname(self.mark), exist_ok=True)
            with open(self.mark, "w", encoding="utf-8") as f:
                json.dump({"unit": prof.unit, "standing": prof.name, "page_card": self.night_page_card,
                           "hold_cards": self.night_hold_cards, "since": now.isoformat(timespec="seconds"),
                           "worker": worker.name, "why": why}, f, indent=1)
        except OSError as e:
            self.log(f"night window: could not write {self.mark}: {e}")

    def night_recover(self, worker) -> None:
        """At start: a marker left by a stop with no start means the window
        held the cards when the last worker died. The unit is started again
        on the first tick, whatever the clock says."""
        if not os.path.exists(self.mark):
            return
        try:
            with open(self.mark, encoding="utf-8") as f:
                m = json.load(f)
        except (OSError, ValueError):
            m = {}
        prof = self.night_profile(worker)
        if prof is None:
            self.log(f"night window: {self.mark} says {m.get('unit', '?')} was stopped by {m.get('worker', '?')} and not "
                     f"started again, but this catalogue has no window for it; the integrator starts it")
            worker.alarm(f"qv4 {worker.box}: {m.get('unit', 'a standing unit')} may be down",
                         f"the night window's marker is on disk with no window in the catalogue to act on it; check the unit")
            return
        self.night_page_card = m.get("page_card", self.window.card)
        self.night_hold_cards = list(m.get("hold_cards") or [])
        self.night_state = "closing"
        self.night_reason = f"the worker restarted while the window held the cards (stopped {m.get('since', '?')})"
        self.log(f"night window: {self.mark} found; {prof.unit} starts again on the first tick")

    def _night_note(self, worker, prof: reg.Profile, now: dt.datetime, detail: str) -> str:
        """A note for the integrator in the inbox (outside git), the way a
        question session leaves a fault: the integrator files the card. It
        names the unit, the failure and the commands to look with, and
        nothing about any person."""
        local = now.astimezone(self.window.zone) if self.window else now
        path = os.path.join(self.inbox, f"{local:%Y-%m-%d}-{prof.unit.replace('.service', '')}-did-not-start-after-the-night-window.md")
        lines = [
            f"# {prof.unit} did not start again after the night window (ruling 129)",
            "kind: blocker",
            f"raised: {local:%Y-%m-%d %H:%M %Z} by the worker {worker.name} on {worker.box} (support.scheduler.cards)",
            f"blocks: every text-reader and review job (no card holds {prof.name}); the board's chat pane says the model "
            f"is not running (ruling 122)",
            "",
            f"The card manager stopped {prof.unit} inside the night window for the page reader and could not start it "
            f"again: {detail}. It keeps trying each tick (reset-failed, then start, then the model read back on "
            f":{prof.port} for up to {START_TIMEOUT_S} s), holds the standing cards reserved meanwhile, and records "
            f"each try as a failed swap. This note is written once per episode.",
            "",
            "On node2, in /home/user/querynzv4:",
            "",
            f"    systemctl --user status {prof.unit}",
            f"    journalctl --user -u {prof.unit} -n 80 --no-pager",
            "    rocm-smi --showpids",
            "    .venv/bin/python -m support.scheduler status | head -60",
            "",
            "A stray server on a card (rocm-smi lists it) would leave Radiance short of its pool; the frozen "
            "product's OCR server (querynz-vision-ocr, :8032) is never the thing to stop.",
            "",
        ]
        text = "\n".join(lines)
        try:
            os.makedirs(self.inbox, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(text)
        except OSError as e:
            self.log(f"night window: could not write the integrator's note {path}: {e}")
        return path

    # ── acting ───────────────────────────────────────────────────────────────

    def apply(self, worker, d: policy.Decision, now_s: float) -> None:
        card = int(d.card.rsplit(":", 1)[1])
        if d.action == policy.KEEP:
            return
        prof = worker.profiles.get(d.profile)
        if d.action == policy.LOAD and prof is not None and (prof.standing or prof.on):
            # its own unit serves it; the worker starts no server for it, on any card
            if d.profile not in self.skipped_loads:
                self.log(f"card {card}: a load of {d.profile} is not acted on: "
                         f"{reg.server_of(worker.profiles, d.profile).unit} serves it")
                self.skipped_loads.add(d.profile)
            return
        runs.placement(d.card, d.action, d.job_type, d.why, d.profile)
        if d.action == policy.DRAIN:
            q.upsert_card(worker.conn, worker.schema, worker.box, card, draining=True)
            q.record_swap(worker.conn, worker.schema, worker.box, card, "drain", d.why, from_profile=d.profile, job=d.job_type,
                          by_worker=worker.name, ok=True)
            return
        if d.action == policy.RELEASE:
            q.upsert_card(worker.conn, worker.schema, worker.box, card, holder=None, holder_since=None, draining=False)
            self.holder_since.pop(card, None)
            q.record_swap(worker.conn, worker.schema, worker.box, card, "release", d.why, from_profile=d.profile,
                          by_worker=worker.name, ok=True)
            return
        if d.action == policy.HANDOVER:
            q.upsert_card(worker.conn, worker.schema, worker.box, card, holder=d.job_type, draining=False)
            self.holder_since[card] = now_s
            q.record_swap(worker.conn, worker.schema, worker.box, card, "handover", d.why, from_profile=d.profile,
                          to_profile=d.profile, job=d.job_type, by_worker=worker.name, ok=True)
            return
        if d.action == policy.LOAD:
            self.load(worker, card, d, now_s)

    def _failed(self, worker, card: int, prof: reg.Profile, d: policy.Decision, detail: str, remember: bool = True, **more) -> bool:
        """A load that did not happen or did not come up: ledgered, logged,
        and (unless the fault is a stray on the port, which goes away on its
        own) remembered so the profile is not tried again on this box until
        the probe's programs change."""
        self.log(f"card {card}: load of {prof.name} FAILED: {detail}")
        q.record_swap(worker.conn, worker.schema, worker.box, card, "failed", d.why, to_profile=prof.name, job=d.job_type,
                      by_worker=worker.name, ok=False, detail=detail, **more)
        if remember:
            self.failed_loads[prof.name] = self._programs_key(worker)
        return False

    def load(self, worker, card: int, d: policy.Decision, now_s: float) -> bool:
        prof = worker.profiles[d.profile]
        was = self.servers.get(card)
        # what can be known without touching the card is checked BEFORE the resident profile is
        # discarded (19 October: a working page-reader was unloaded three times for a load that failed)
        binary = server_binary(worker.profile.get("programs") or {}, profile=prof)
        if not binary:
            return self._failed(worker, card, prof, d, f"no model server program {prof.binary!r} on this box" if prof.binary
                                else "no model server program on this box")
        missing = [w for w in prof.weight_paths(self.models_dir) if not os.path.exists(w)]
        if missing:
            return self._failed(worker, card, prof, d, f"weights missing: {missing}")
        if was is not None:
            self.unload(worker, card, f"making room for {prof.name}: {d.why}")
        port = PORT_BASE + card
        busy = self.ask(port)
        if busy["healthy"]:
            # a server this worker did not start answers on the card's port: starting another would fail to
            # bind, and reading the stray's answer as our own would call the wrong model ready
            return self._failed(worker, card, prof, d, f"port {port} is busy: a stray server answers with {busy['served']!r}; "
                                f"not started", remember=False, served_model=busy["served"])
        argv = server_argv(binary, prof, card, port, self.models_dir)
        os.makedirs(LOGS, exist_ok=True)
        logf = open(os.path.join(LOGS, f"{worker.box}-card{card}.log"), "ab")
        # the copied binary's RUNPATH still names the old build's folder; LD_LIBRARY_PATH
        # is searched first, so the estate's own libraries beside the binary are the ones loaded
        # (the build from source carries $ORIGIN and needs no such help; `[server] binary` chooses)
        # ONE device filter only: HIP_VISIBLE_DEVICES and ROCR_VISIBLE_DEVICES set together filter
        # twice (index 1 of a one-card list is nothing) and the server falls back to the processor
        env = dict(os.environ, HIP_VISIBLE_DEVICES=str(card),
                   LD_LIBRARY_PATH=os.path.dirname(binary) + (":" + os.environ["LD_LIBRARY_PATH"] if os.environ.get("LD_LIBRARY_PATH") else ""))
        t0 = time.monotonic()
        self.log(f"card {card}: loading {prof.name} ({prof.model}, {prof.geometry}) on :{port}: {d.why}")
        try:
            proc = self.popen(argv, env=env, stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        except OSError as e:
            return self._failed(worker, card, prof, d, f"{type(e).__name__}: {e}")
        served, seconds = self._wait_ready(proc, port, prof)
        if served != prof.model:
            detail = f"after {seconds:.0f}s the card answered with {served!r}, not {prof.model!r}" if served else \
                     f"not healthy after {seconds:.0f}s"
            self._stop(proc)
            q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=None, port=None, pid=None, holder=None)
            return self._failed(worker, card, prof, d, detail, load_seconds=seconds, served_model=served)
        self.servers[card] = Server(proc, prof, card, port, t0)
        self.holder_since[card] = now_s
        q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=prof.name, port=port, pid=proc.pid,
                      server_started_at=q.utcnow(), holder=d.job_type, draining=False, slots=prof.slots, slots_busy=0,
                      worker=worker.name)
        q.record_swap(worker.conn, worker.schema, worker.box, card, "load", d.why, from_profile=was.prof.name if was else None,
                      to_profile=prof.name, job=d.job_type, by_worker=worker.name, load_seconds=seconds, served_model=served,
                      ok=True, detail=f"server {binary}")
        self.log(f"card {card}: {prof.name} ready in {seconds:.0f}s, serving {served!r} from {binary}")
        return True

    def _wait_ready(self, proc, port: int, prof: reg.Profile, timeout: float = LOAD_TIMEOUT_S) -> tuple[str | None, float]:
        t0 = self.clock()
        while self.clock() - t0 < timeout:
            if proc.poll() is not None:
                return None, self.clock() - t0
            a = self.ask(port)
            if a["healthy"] and a["served"]:
                return a["served"], self.clock() - t0
            self.sleep(2)
        return None, self.clock() - t0

    def _stop(self, proc) -> None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                proc.send_signal(sig)
                proc.wait(timeout=STOP_GRACE_S)
                return
            except subprocess.TimeoutExpired:
                continue
            except Exception:  # noqa: BLE001
                return

    def unload(self, worker, card: int, why: str) -> None:
        s = self.servers.pop(card, None)
        if s is None:
            return
        self.log(f"card {card}: unloading {s.prof.name}: {why}")
        runs.placement(f"{worker.box}:{card}", "unload", None, why, s.prof.name)
        self._stop(s.proc)
        q.record_swap(worker.conn, worker.schema, worker.box, card, "unload", why, from_profile=s.prof.name, by_worker=worker.name,
                      ok=True)
        q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=None, port=None, pid=None, holder=None,
                      draining=False, slots=None, slots_busy=None)
        self.holder_since.pop(card, None)

    def stop_all(self, worker, why: str = "worker stopping") -> None:
        for card in list(self.servers):
            self.unload(worker, card, why)
