"""THE WORKER: one per box (plan step 2.2; two on node2 under their own
names while node1 is out, ruling 55 and the queue's default).

Each tick it: sends its heartbeat; probes its box at start and on a clock
and reports what it has (2.3); reaps leases that lapsed (2.8); raises the
alarm if the other worker has gone silent (2.10); queues the timetable's
due slots and the standing services' missing copies (2.12, 2.13); lets the
card manager act on the planner (2.7, `cards.py`); and pulls the most
urgent job it can run, which it runs under the runner's limits with the
lease renewed as it goes. Losing a box means one worker stops pulling and
its leases lapse; the other finishes the work.

WHAT A WORKER MAY RUN (2.3, 2.5). A job whose required programs this box
lacks is never claimed. Parallelism is worked out, not fixed: a job gets
as many parallel workers as fit in the box's available memory after the
reserve for the database and the standing services, up to its declared
cap. A job needing a model profile is claimed only while a card on this
box holds that profile.

A DELIBERATE STOP (SIGTERM) tells each running child to stop, gives the
leased rows back with their progress, marks the worker `stopped`, and
raises no alarm.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import signal
import sys
import threading
import time
import traceback

from support.alarm import send as send_alarm
from support.scheduler import LIVE, SCHEMA
from support.scheduler import probe as pb
from support.scheduler import queue as q
from support.scheduler import registry as reg
from support.scheduler import runner, runs

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _connect(database: str):
    import support.db as db
    conn = db.connect(db.OWNER_KEY, database, autocommit=True)
    conn.execute("SET statement_timeout = 30000")
    conn.execute("SET application_name = 'qv4-worker'")
    return conn


class Running:
    def __init__(self, claim: dict, jt: reg.JobType):
        self.claim, self.jt = claim, jt
        self.started = time.monotonic()
        self.thread: threading.Thread | None = None
        self.outcome: str | None = None


class Worker:
    def __init__(self, name: str, box: str = None, *, database: str = "querynz_v4", schema: str = SCHEMA,
                 registry: dict = None, profiles: dict = None, rules: reg.Queueing = None, tick_s: float = 5.0,
                 probe_every_s: int = 600, alarm_after_s: int = 300, hide_programs=(), max_parallel: int = 4,
                 log=None, connect=None, alarm=None, cards_manager=None):
        self.name, self.box = name, box or pb.profile().get("host")
        self.database, self.schema = database, schema
        self._reload = registry is None and profiles is None     # a test's own catalogue is never replaced
        self.registry = registry if registry is not None else reg.load()
        self.profiles = profiles if profiles is not None else reg.profiles()
        self.rules = rules or reg.queueing()
        self.tick_s, self.probe_every_s, self.alarm_after_s = tick_s, probe_every_s, alarm_after_s
        self.hide_programs = tuple(hide_programs)
        self.max_parallel = max_parallel
        self.log = log or (lambda m: print(f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')} {name}: {m}", flush=True))
        self._connect = connect or (lambda: _connect(self.database))
        self.alarm = alarm or send_alarm
        self.cards_manager = cards_manager
        self.conn = None
        self.profile: dict = {}
        self.probed_at = 0.0
        self.running: dict[int, Running] = {}
        self.lock = threading.Lock()
        self.stopping = False
        self.ticks = 0

    # ── the box ──────────────────────────────────────────────────────────────

    def probe(self) -> dict:
        p = pb.profile(self.box)
        for h in self.hide_programs:          # the rehearsal: a box that lacks a program
            if h in p.get("programs", {}):
                p["programs"][h] = None
        p["worker"] = self.name
        self.profile, self.probed_at = p, time.monotonic()
        return p

    def reload_catalogue(self) -> None:
        """The catalogue and the profiles are re-read on the probe's clock,
        so a change lands within that interval without a restart. A file
        that no longer parses is logged and the last good one kept."""
        if not self._reload:
            return
        try:
            registry, profiles, rules = reg.load(), reg.profiles(), reg.queueing()
            probs = reg.problems()
        except Exception as exc:  # noqa: BLE001
            self.log(f"catalogue not reloaded: {type(exc).__name__}: {exc}")
            return
        if probs:
            self.log(f"catalogue not reloaded: {len(probs)} problem(s), first: {probs[0]}")
            return
        if set(registry) != set(self.registry) or any(registry[n] != self.registry.get(n) for n in registry):
            self.log(f"catalogue reloaded: {len(registry)} job types, {len(profiles)} profiles")
        self.registry, self.profiles, self.rules = registry, profiles, rules

    def available_gb(self) -> float:
        m = pb.meminfo()
        avail = m.get("memory_available_gb", 0.0)
        with self.lock:
            committed = sum(r.jt.memory_gb for r in self.running.values())
        return avail - self.rules.memory_reserve_gb - committed

    def cards_here(self) -> list[dict]:
        return q.cards(self.conn, self.schema, self.box)

    def eligible(self) -> list[str]:
        """The job types this worker may claim right now."""
        free = self.available_gb()
        cards = self.cards_here()
        with self.lock:
            counts = {}
            for r in self.running.values():
                counts[r.jt.name] = counts.get(r.jt.name, 0) + 1
            total = len(self.running)
        if total >= self.max_parallel:
            return []
        out = []
        for jt in self.registry.values():
            if not jt.enabled or pb.missing_programs(self.profile, jt.requires):
                continue
            fits = int(free // jt.memory_gb) if jt.memory_gb > 0 else jt.concurrency
            if counts.get(jt.name, 0) >= min(jt.concurrency, max(fits, 0)):
                continue
            if jt.profile:
                if not any(c["profile"] == jt.profile and not c["draining"] and c["port"] and not c["reserved"] for c in cards):
                    continue
            out.append(jt.name)
        return out

    # ── the loop ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        self.conn = self._connect()
        q.tables(self.conn, self.schema)
        self.probe()
        q.register(self.conn, self.schema, self.name, self.box, self.profile)
        self.log(f"registered on {self.box}: {self.profile.get('cores')} cores, {self.profile.get('memory_total_gb')} GB, "
                 f"{len(self.profile.get('cards') or [])} card(s), programs missing: "
                 f"{[k for k, v in (self.profile.get('programs') or {}).items() if not v]}")
        if self.cards_manager:
            self.cards_manager.start(self)

    def tick(self) -> None:
        self.ticks += 1
        now = q.utcnow()
        if time.monotonic() - self.probed_at >= self.probe_every_s:
            self.probe()
            self.reload_catalogue()
            q.heartbeat(self.conn, self.schema, self.name, now, profile=self.profile)
        else:
            q.heartbeat(self.conn, self.schema, self.name, now)
        for r in q.reap(self.conn, self.schema, now):
            self.log(f"reaped queue row {r['id']} ({r['job']}): lease lapsed, {r['pieces_done']}/{r['pieces_total']} pieces kept, "
                     f"lost {r['pieces_lost']}")
        for w in q.silent_workers(self.conn, self.schema, after_s=self.alarm_after_s, me=self.name, now=now):
            self.log(f"ALARM: worker {w['name']} on {w['box']} silent since {w['last_seen']}")
            seen = w["last_seen"].astimezone(dt.timezone.utc) if w["last_seen"].tzinfo else w["last_seen"]
            self.alarm(f"qv4 {self.box}: worker {w['name']} silent",
                       f"no heartbeat from {w['name']} ({w['box']}) since {seen:%Y-%m-%d %H:%M} UTC; "
                       f"its leases lapse and {self.name} takes them over")
        for qid in q.enqueue_due(self.conn, self.schema, self.registry, now=now, created_by=self.name):
            self.log(f"timetable: queued row {qid}")
        for qid in q.enqueue_standing(self.conn, self.schema, self.registry, now=now, created_by=self.name):
            self.log(f"standing: queued row {qid}")
        if self.cards_manager:
            self.cards_manager.tick(self, now)
        self._reap_threads()
        if not self.stopping:
            elig = self.eligible()
            claim = q.claim(self.conn, self.schema, self.name, elig, lease_s=self.rules.lease_seconds, now=now)
            if claim:
                self._launch(claim)

    def run_forever(self) -> None:
        self.start()
        signal.signal(signal.SIGTERM, lambda *_: self.stop())
        signal.signal(signal.SIGINT, lambda *_: self.stop())
        while not self.stopping:
            try:
                self.tick()
            except Exception:  # noqa: BLE001 — a tick that fails is logged; the worker lives
                self.log("tick failed:\n" + traceback.format_exc())
                try:
                    self.conn.close()
                except Exception:  # noqa: BLE001
                    pass
                self.conn = self._connect()
            time.sleep(self.tick_s)
        self._finish_stop()

    def stop(self) -> None:
        if not self.stopping:
            self.log("stopping on request: children told to stop, leases given back, no alarm")
        self.stopping = True

    def _finish_stop(self) -> None:
        with self.lock:
            threads = [r.thread for r in self.running.values() if r.thread]
        for t in threads:
            t.join(timeout=runner.KILL_GRACE_S + 10)
        if self.cards_manager:
            self.cards_manager.stop_all(self, "worker stopping")
        released = q.stop_worker(self.conn, self.schema, self.name)
        self.log(f"stopped; {released} lease(s) given back")

    # ── running a job ────────────────────────────────────────────────────────

    def _launch(self, claim: dict) -> None:
        jt = self.registry[claim["job"]]
        r = Running(claim, jt)
        with self.lock:
            self.running[claim["id"]] = r
        r.thread = threading.Thread(target=self._run_job, args=(r,), name=f"job-{claim['id']}", daemon=True)
        r.thread.start()
        self.log(f"claimed row {claim['id']} ({jt.name}, {claim['cls']}, pieces {claim['pieces_done']}/{claim['pieces_total']})")

    def _reap_threads(self) -> None:
        with self.lock:
            done = [qid for qid, r in self.running.items() if r.thread and not r.thread.is_alive()]
            for qid in done:
                del self.running[qid]

    def _argv(self, jt: reg.JobType, extra: list[str]) -> list[str]:
        argv = list(jt.command) + list(extra)
        if argv and argv[0] == "python":
            argv[0] = sys.executable
        return argv

    def _env(self, r: Running, run_id: str, piece: dict | None) -> dict:
        env = {"QV4_RUN_ID": run_id, "QV4_JOB": r.jt.name, "QV4_QUEUE_ID": str(r.claim["id"]), "QV4_WORKER": self.name,
               "QV4_BOX": self.box, "QV4_ARGS": json.dumps(r.claim.get("args") or {}), "PYTHONUNBUFFERED": "1"}
        if piece:
            env["QV4_PIECE"] = str(piece["piece"])
            env["QV4_PIECE_KEY"] = piece["key"]
        if r.jt.profile:
            card = next((c for c in self.cards_here() if c["profile"] == r.jt.profile and c["port"] and not c["draining"]), None)
            if card:
                env["QV4_MODEL_URL"] = f"http://127.0.0.1:{card['port']}/v1/chat/completions"
                env["QV4_MODEL_PORT"] = str(card["port"])
                env["QV4_CARD"] = str(card["card"])
            env["QV4_MODEL"] = self.profiles[r.jt.profile].model
            env["QV4_PROFILE"] = r.jt.profile
        return env

    def _run_one(self, conn, r: Running, piece: dict | None) -> runner.Result:
        jt, claim = r.jt, r.claim
        if jt.profile and not self._env(r, "", piece).get("QV4_MODEL_URL"):
            # the card that held the profile when the job was claimed no longer does: do not run a
            # doomed child; the job goes back and is claimed again when a card holds it
            return runner.Result(None, 0.0, 0, "failed", f"no card on {self.box} holds profile {jt.profile} now", "lease")
        run_id = runs.begin(jt.name, box=self.box, queue_id=claim["id"], card=None,
                            requested_model=self.profiles[jt.profile].model if jt.profile else None,
                            args={"piece": piece["key"] if piece else None, "worker": self.name})
        q.run_begin(conn, self.schema, run_id, job=jt.name, worker=self.name, box=self.box, qid=claim["id"],
                    piece=piece["piece"] if piece else None, declared_mb=int(jt.memory_gb * 1024))
        last_renew = [time.monotonic()]

        def tick() -> bool:
            if self.stopping:
                return False
            if time.monotonic() - last_renew[0] >= self.rules.lease_seconds / 3:
                last_renew[0] = time.monotonic()
                if not q.renew(conn, self.schema, claim["id"], claim["token"], lease_s=self.rules.lease_seconds):
                    self.log(f"row {claim['id']}: lease lost; stopping the child")
                    return False
            return True

        res = runner.run(self._argv(jt, [piece["key"]] if piece else []), deadline_s=jt.needs.deadline_s,
                         ceiling_mb=runner.ceiling_for(jt.memory_gb), query_timeout_s=jt.needs.query_timeout_s,
                         env=self._env(r, run_id, piece), cwd=REPO, tick=tick, log=self.log, nice=jt.nice)
        runs.finish(run_id, outcome=res.outcome, error=res.error, peak_mb=res.peak_mb, declared_mb=int(jt.memory_gb * 1024),
                    note=res.stopped_for)
        q.run_end(conn, self.schema, run_id, outcome=res.outcome, exit_code=res.code, error=res.error, detail=res.stopped_for,
                  peak_mb=res.peak_mb)
        if res.peak_mb > jt.memory_gb * 1024:
            self.log(f"{jt.name} run {run_id}: peak {res.peak_mb} MB passed its declared {int(jt.memory_gb * 1024)} MB: "
                     f"flagged, correct the figure")
        return res

    def _run_job(self, r: Running) -> None:
        conn = None
        try:
            conn = self._connect()
            jt, claim = r.jt, r.claim
            if jt.pieces:
                failed, in_a_row = 0, 0
                while True:
                    if self.stopping:
                        q.requeue(conn, self.schema, claim["id"], claim["token"], detail="worker stopping")
                        return
                    piece = q.next_piece(conn, self.schema, claim["id"], claim["token"], self.name)
                    if piece is None:
                        break
                    res = self._run_one(conn, r, piece)
                    if res.stopped_for in ("lease",):
                        q.requeue(conn, self.schema, claim["id"], claim["token"], detail="worker stopping or lease lost")
                        return
                    q.finish_piece(conn, self.schema, claim["id"], claim["token"], piece["piece"], ok=res.outcome == "ok",
                                   seconds=res.seconds, detail=res.error or "")
                    if res.outcome != "ok":
                        failed += 1
                        in_a_row += 1
                        if in_a_row >= 2:
                            # two pieces failing back to back is the environment (a server gone, a disk full),
                            # not two bad pieces: give the job back for later rather than burn every piece's attempts
                            q.requeue(conn, self.schema, claim["id"], claim["token"],
                                      detail=f"{in_a_row} pieces failed in a row ({res.error}); retried in 2 minutes",
                                      not_before=q.utcnow() + dt.timedelta(seconds=120))
                            self.log(f"row {claim['id']} ({jt.name}): {in_a_row} pieces failed in a row; given back for 2 minutes")
                            return
                        time.sleep(5)
                    else:
                        in_a_row = 0
                left = q.pieces_left(conn, self.schema, claim["id"])
                ok = left["failed"] == 0 and left["todo"] == 0
                q.complete(conn, self.schema, claim["id"], claim["token"], outcome="ok" if ok else "failed",
                           detail=f"pieces done {left['done']}, failed {left['failed']}")
                if not ok:
                    self.alarm(f"qv4 {self.box}: {jt.name} failed", f"row {claim['id']}: {left['failed']} piece(s) failed")
            else:
                res = self._run_one(conn, r, None)
                if res.stopped_for == "lease":
                    q.requeue(conn, self.schema, claim["id"], claim["token"], detail="worker stopping or lease lost")
                    return
                q.complete(conn, self.schema, claim["id"], claim["token"], outcome=res.outcome, detail=res.error or "")
                if res.outcome != "ok":
                    self.alarm(f"qv4 {self.box}: {jt.name} failed", f"row {claim['id']}: {res.error}")
            self.log(f"row {claim['id']} ({jt.name}) finished: {r.outcome or 'see record'}")
        except Exception:  # noqa: BLE001
            self.log(f"row {r.claim['id']} failed inside the worker:\n" + traceback.format_exc())
            try:
                if conn:
                    q.complete(conn, self.schema, r.claim["id"], r.claim["token"], outcome="failed", detail="worker error")
            except Exception:  # noqa: BLE001
                pass
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:  # noqa: BLE001
                pass


def report(conn, schema: str = SCHEMA, path: str = None) -> str:
    """The `qv4-scheduler-report` job: the scheduler's state for the checks
    board, as JSON under <live>/checks/."""
    path = path or os.path.join(LIVE, "checks", "scheduler.json")
    st = q.status(conn, schema)
    st["written"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(st, f, default=str, indent=1)
    return path
