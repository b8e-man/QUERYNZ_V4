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
"""
from __future__ import annotations

import os
import signal
import subprocess
import time

from support.scheduler import LIVE
from support.scheduler import policy
from support.scheduler import probe as pb
from support.scheduler import queue as q
from support.scheduler import registry as reg
from support.scheduler import runs

PORT_BASE = 8110
LOAD_TIMEOUT_S = 900          # a 21 GB load from a cold page cache takes minutes
STOP_GRACE_S = 20             # the server hangs ~45 s after TERM; 20 s then KILL (old lesson)
LOGS = os.path.join(LIVE, "scheduler", "servers")


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


class Server:
    def __init__(self, proc: subprocess.Popen, prof: reg.Profile, card: int, port: int, started: float):
        self.proc, self.prof, self.card, self.port, self.started = proc, prof, card, port, started


class Manager:
    """One per worker. Pure decisions come from `policy.plan`; this performs
    them on this box's cards and keeps the `cards` table true."""

    def __init__(self, *, popen=None, ask=None, models_dir: str = None, log=None, reservations: list = None):
        self.popen = popen or subprocess.Popen
        self.ask = ask or pb.ask_server
        self.models_dir = models_dir
        self.reservations = reservations if reservations is not None else reg.reservations()
        self.servers: dict[int, Server] = {}
        self.round_done: frozenset = frozenset()
        self.holder_since: dict[int, float] = {}
        self.failed_loads: dict[str, tuple] = {}     # profile → the box's programs when its load failed here
        self.log = log
        self.worker = None

    # ── registration ─────────────────────────────────────────────────────────

    def start(self, worker) -> None:
        self.worker = worker
        self.log = self.log or worker.log
        self.register_cards(worker)

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

    # ── the tick ─────────────────────────────────────────────────────────────

    def held(self, worker, now_s: float) -> list[policy.Held]:
        out = []
        for c in q.cards(worker.conn, worker.schema, worker.box):
            if c["worker"] != worker.name and not c["reserved"]:
                continue                      # another worker's card on this box
            if c["reserved"]:
                out.append(policy.Held(f"{worker.box}:{c['card']}", None, reserved=True, loaded=None))
                continue
            in_flight = 0
            if c["card"] in self.servers:
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
            prof = worker.profiles.get(jt.profile) if jt.profile else None
            if prof is not None and prof.binary and not progs.get(prof.binary):
                continue                  # its profile's own server is not on this box
            out.add(jt.name)
        return out

    def tick(self, worker, now) -> None:
        now_s = now.timestamp()
        self._reap_dead_servers(worker)
        demands = q.demands(worker.conn, worker.schema, worker.registry, now=now)
        measured = q.measured_load_seconds(worker.conn, worker.schema)
        profiles = {n: (p if p.load_seconds is not None or n not in measured else
                        reg.Profile(**{**p.__dict__, "load_seconds": measured[n]})) for n, p in worker.profiles.items()}
        held = self.held(worker, now_s)
        if not held:
            return
        decisions, self.round_done = policy.plan(now=now_s, held=held, queues=demands, registry=worker.registry,
                                                 profiles=profiles, rules=worker.rules, round_done=self.round_done,
                                                 eligible=self.claimable(worker))
        for d in decisions:
            self.apply(worker, d, now_s)

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

    # ── acting ───────────────────────────────────────────────────────────────

    def apply(self, worker, d: policy.Decision, now_s: float) -> None:
        card = int(d.card.rsplit(":", 1)[1])
        if d.action == policy.KEEP:
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
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            if proc.poll() is not None:
                return None, time.monotonic() - t0
            a = self.ask(port)
            if a["healthy"] and a["served"]:
                return a["served"], time.monotonic() - t0
            time.sleep(2)
        return None, time.monotonic() - t0

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
