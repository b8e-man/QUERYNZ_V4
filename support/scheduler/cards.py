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


def server_binary(profile_programs: dict) -> str | None:
    """The estate's own build first; the old build read-only until the
    installer has put one beside it."""
    return profile_programs.get("qv4-llama-server") or profile_programs.get("llama-server")


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

    def __init__(self, *, popen=None, ask=None, models_dir: str = None, log=None):
        self.popen = popen or subprocess.Popen
        self.ask = ask or pb.ask_server
        self.models_dir = models_dir
        self.servers: dict[int, Server] = {}
        self.round_done: frozenset = frozenset()
        self.holder_since: dict[int, float] = {}
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
        reserved = {r.key: r for r in reg.reservations()}
        for c in worker.profile.get("cards") or []:
            key = f"{worker.box}:{c['index']}"
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
                                                 profiles=profiles, rules=worker.rules, round_done=self.round_done)
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

    def load(self, worker, card: int, d: policy.Decision, now_s: float) -> bool:
        prof = worker.profiles[d.profile]
        was = self.servers.get(card)
        if was is not None:
            self.unload(worker, card, f"making room for {prof.name}: {d.why}")
        binary = server_binary(worker.profile.get("programs") or {})
        if not binary:
            q.record_swap(worker.conn, worker.schema, worker.box, card, "failed", d.why, to_profile=prof.name, job=d.job_type,
                          by_worker=worker.name, ok=False, detail="no model server program on this box")
            self.log(f"card {card}: cannot load {prof.name}: no model server program")
            return False
        missing = [w for w in prof.weight_paths(self.models_dir) if not os.path.exists(w)]
        if missing:
            q.record_swap(worker.conn, worker.schema, worker.box, card, "failed", d.why, to_profile=prof.name, job=d.job_type,
                          by_worker=worker.name, ok=False, detail=f"weights missing: {missing}")
            self.log(f"card {card}: cannot load {prof.name}: weights missing {missing}")
            return False
        port = PORT_BASE + card
        busy = self.ask(port)
        if busy["healthy"]:
            # a server this worker did not start answers on the card's port: starting another would fail to
            # bind, and reading the stray's answer as our own would call the wrong model ready
            detail = f"port {port} is busy: a stray server answers with {busy['served']!r}; not started"
            self.log(f"card {card}: cannot load {prof.name}: {detail}")
            q.record_swap(worker.conn, worker.schema, worker.box, card, "failed", d.why, to_profile=prof.name, job=d.job_type,
                          by_worker=worker.name, served_model=busy["served"], ok=False, detail=detail)
            return False
        argv = server_argv(binary, prof, card, port, self.models_dir)
        os.makedirs(LOGS, exist_ok=True)
        logf = open(os.path.join(LOGS, f"{worker.box}-card{card}.log"), "ab")
        # the copied binary's RUNPATH still names the old build's folder; LD_LIBRARY_PATH
        # is searched first, so the estate's own libraries beside the binary are the ones loaded
        # ONE device filter only: HIP_VISIBLE_DEVICES and ROCR_VISIBLE_DEVICES set together filter
        # twice (index 1 of a one-card list is nothing) and the server falls back to the processor
        env = dict(os.environ, HIP_VISIBLE_DEVICES=str(card),
                   LD_LIBRARY_PATH=os.path.dirname(binary) + (":" + os.environ["LD_LIBRARY_PATH"] if os.environ.get("LD_LIBRARY_PATH") else ""))
        t0 = time.monotonic()
        self.log(f"card {card}: loading {prof.name} ({prof.model}, {prof.geometry}) on :{port}: {d.why}")
        try:
            proc = self.popen(argv, env=env, stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        except OSError as e:
            q.record_swap(worker.conn, worker.schema, worker.box, card, "failed", d.why, to_profile=prof.name, job=d.job_type,
                          by_worker=worker.name, ok=False, detail=f"{type(e).__name__}: {e}")
            return False
        served, seconds = self._wait_ready(proc, port, prof)
        if served != prof.model:
            detail = f"after {seconds:.0f}s the card answered with {served!r}, not {prof.model!r}" if served else \
                     f"not healthy after {seconds:.0f}s"
            self.log(f"card {card}: load of {prof.name} FAILED: {detail}")
            self._stop(proc)
            q.record_swap(worker.conn, worker.schema, worker.box, card, "failed", d.why, to_profile=prof.name, job=d.job_type,
                          by_worker=worker.name, load_seconds=seconds, served_model=served, ok=False, detail=detail)
            q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=None, port=None, pid=None, holder=None)
            return False
        self.servers[card] = Server(proc, prof, card, port, t0)
        self.holder_since[card] = now_s
        q.upsert_card(worker.conn, worker.schema, worker.box, card, profile=prof.name, port=port, pid=proc.pid,
                      server_started_at=q.utcnow(), holder=d.job_type, draining=False, slots=prof.slots, slots_busy=0,
                      worker=worker.name)
        q.record_swap(worker.conn, worker.schema, worker.box, card, "load", d.why, from_profile=was.prof.name if was else None,
                      to_profile=prof.name, job=d.job_type, by_worker=worker.name, load_seconds=seconds, served_model=served,
                      ok=True)
        self.log(f"card {card}: {prof.name} ready in {seconds:.0f}s, serving {served!r}")
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
