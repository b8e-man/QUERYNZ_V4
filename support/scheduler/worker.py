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
box holds that profile; its cap (`concurrency`) is per card holding the
profile, and each piece runs against the card with the fewest of this
worker's jobs on it (`pick_card`), so two page readers are both fed (card
one-page-reader-at-a-time-while-card-0-holds-the-ocr-server, 30 October:
every piece went to the first card holding the profile).

A JOB STOPPED AT ITS MEMORY CEILING (ruling 115) failed by a figure the
scheduler holds, so the worker records a raise (`queue.raise_memory`): the
working figure goes to twice the ceiling crossed, rounded up to the next
0.5 GB, and the job is queued again at once, unless the raised figure is
over the box's budget (its memory less the reserve) or its first row has
been raised twice already; then it stays failed and alarmed, with the note.
The working figure is the larger of the declared one and the latest applied
raise, read from the table every tick, and placement and the ceiling use
it. No other failure is re-run by this.

A DELIBERATE STOP (SIGTERM) tells each running child to stop, gives the
leased rows back with their progress, marks the worker `stopped`, and
raises no alarm.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import signal
import subprocess
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

# The copy this worker runs in, and so every job it starts: the release copy
# (/home/user/querynzv4-release, moved only by `python -m support.installer
# release` after a push), never the main checkout the integrator works in.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORIGIN_MAIN = "refs/remotes/origin/main"


def checkout_branch(path) -> str | None:
    """The branch the checkout holding `path` is on, asked of git by path:
    "HEAD" for a detached head, None when git cannot say."""
    try:
        p = subprocess.run(["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode:
        return None
    return p.stdout.strip() or None


def _git(path, *args) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return -1, ""
    return p.returncode, p.stdout.strip()


def release_state(path) -> str | None:
    """None when the checkout holding `path` stands, unedited, at a commit
    of origin/main (as that checkout last fetched it); otherwise why not.
    The release copy always does; the main checkout does only once main is
    pushed, never on an integrate branch or a merge not yet pushed."""
    rc, head = _git(path, "rev-parse", "HEAD")
    if rc or not head:
        return "git cannot say which commit the checkout stands at"
    rc, _ = _git(path, "merge-base", "--is-ancestor", head, ORIGIN_MAIN)
    if rc == 1:
        branch = checkout_branch(path)
        at = f"on {branch}" if branch and branch != "HEAD" else "detached"
        return f"the checkout stands at {head[:12]} ({at}), not a commit of origin/main"
    if rc:
        return "git cannot say whether the checkout's commit is on origin/main"
    rc, edits = _git(path, "status", "--porcelain", "--untracked-files=no")
    if rc:
        return "git cannot say whether the checkout is edited"
    if edits:
        return f"the checkout's tracked files are edited ({len(edits.splitlines())} path(s))"
    return None


def _connect(database: str):
    import support.db as db
    conn = db.connect(db.OWNER_KEY, database, autocommit=True)
    conn.execute("SET statement_timeout = 30000")
    conn.execute("SET application_name = 'qv4-worker'")
    return conn


class Running:
    def __init__(self, claim: dict, jt: reg.JobType):
        self.claim, self.jt = claim, jt
        self.memory_gb = jt.memory_gb             # the working figure at the claim (ruling 115)
        self.rerun: dict | None = None            # the memory raise that queued this row, if any
        self.card: int | None = None              # the card the current piece runs against (pick_card)
        self.started = time.monotonic()
        self.last_renew = time.monotonic()    # across every piece of the claim, so short pieces still renew
        self.thread: threading.Thread | None = None
        self.outcome: str | None = None


class Worker:
    def __init__(self, name: str, box: str = None, *, database: str = "querynz_v4", schema: str = SCHEMA,
                 registry: dict = None, profiles: dict = None, rules: reg.Queueing = None, tick_s: float = 5.0,
                 probe_every_s: int = 600, alarm_after_s: int = 300, hide_programs=(), max_parallel: int = 8,
                 log=None, connect=None, alarm=None, cards_manager=None):
        self.name, self.box = name, box or pb.profile().get("host")
        self.database, self.schema = database, schema
        self._reload = registry is None and profiles is None     # a test's own catalogue is never replaced
        self.log = log or (lambda m: print(f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')} {name}: {m}", flush=True))
        self._held: str | None = None                              # why the catalogue is held, as last logged
        if self._reload and not self._on_release():
            registry = {}    # no good catalogue yet: run nothing until the checkout stands at a commit of origin/main
        self.registry = registry if registry is not None else reg.load()
        self.profiles = profiles if profiles is not None else reg.profiles()
        self.rules = rules or reg.queueing()
        self.tick_s, self.probe_every_s, self.alarm_after_s = tick_s, probe_every_s, alarm_after_s
        self.hide_programs = tuple(hide_programs)
        self.max_parallel = max_parallel
        self._connect = connect or (lambda: _connect(self.database))
        self.alarm = alarm or send_alarm
        self.cards_manager = cards_manager
        self.conn = None
        self.profile: dict = {}
        self.probed_at = 0.0
        self.running: dict[int, Running] = {}
        self.raised: dict[str, float] = {}         # per job, its latest applied memory raise (ruling 115)
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
        dropped = p.get("devices_dropped") or []
        if dropped and dropped != (self.profile.get("devices_dropped") or []):
            # the probe's log line: what rocm-smi listed that is not a card (said when it changes, not every probe)
            self.log("probe: not a card, dropped: " + "; ".join(
                f"index {d['index']} {d.get('product')!r} {d.get('memory_total_gb')} GB" for d in dropped))
        self.profile, self.probed_at = p, time.monotonic()
        return p

    def _on_release(self) -> bool:
        """Whether the checkout the catalogue is read from stands, unedited,
        at a pushed commit of main. An integrator checks an integrate branch
        out in the main checkout for about twenty-five minutes before the
        gate; a catalogue read there ran the branch's new jobs live (card
        the-scheduler-s-worker-runs-the-main-checkout-…, finding 2). The
        worker runs from the release copy, which always passes; anywhere
        else the last good catalogue is kept and one line says why, once
        per change."""
        why = release_state(reg.JOBS.parent)
        if why is None:
            if self._held is not None:
                self.log("catalogue: the checkout stands at a commit of origin/main again; reloading")
                self._held = None
            return True
        if why != self._held:
            self.log(f"catalogue not reloaded: {why}; the last good catalogue is kept")
            self._held = why
        return False

    def reload_catalogue(self) -> None:
        """The catalogue and the profiles are re-read on the probe's clock,
        so a change lands within that interval without a restart. A file
        that no longer parses is logged and the last good one kept; so is
        every file while the checkout is not at a commit of origin/main."""
        if not self._reload or not self._on_release():
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

    def read_raises(self) -> None:
        """The working figures, from the table: a restart, or the other
        worker, places by the same raises."""
        raised = q.working_figures(self.conn, self.schema)
        with self.lock:
            self.raised = raised

    def working_gb(self, jt: reg.JobType) -> float:
        """The larger of the declared figure and the job's latest applied raise."""
        with self.lock:
            return max(jt.memory_gb, self.raised.get(jt.name, 0.0))

    def memory_budget_gb(self) -> float | None:
        """The most one job may hold on this box: its memory less the reserve
        for the database and the standing services. None before a probe."""
        total = (self.profile or {}).get("memory_total_gb")
        return None if not total else float(total) - self.rules.memory_reserve_gb

    def available_gb(self) -> float:
        m = pb.meminfo()
        avail = m.get("memory_available_gb", 0.0)
        with self.lock:
            committed = sum(r.memory_gb for r in self.running.values())
        return avail - self.rules.memory_reserve_gb - committed

    def serving(self, profile: str) -> str:
        """The profile a card must hold for a job on `profile`: a view's
        standing server, otherwise the profile itself."""
        return reg.server_of(self.profiles, profile).name if profile in self.profiles else profile

    def cards_here(self) -> list[dict]:
        return q.cards(self.conn, self.schema, self.box)

    def cards_holding(self, profile: str, cards: list[dict] = None) -> list[dict]:
        """The cards on this box a job on `profile` may run against now:
        holding its serving profile, answering on a port, not draining, not
        reserved."""
        on = self.serving(profile)
        return [c for c in (cards if cards is not None else self.cards_here())
                if c["profile"] == on and c["port"] and not c["draining"] and not c.get("reserved")]

    def pick_card(self, r: Running) -> dict | None:
        """The card this run's next piece goes to: of the cards holding the
        profile, the one with the fewest of this worker's other jobs on it,
        the lowest index on a tie; None when no card holds it. Recorded on
        the run, so the pieces of one job and its concurrent rows are spread
        over every card holding the profile, not sent to the first."""
        cards = self.cards_holding(r.jt.profile)
        if not cards:
            r.card = None
            return None
        with self.lock:
            load = {}
            for other in self.running.values():
                if other is not r and other.card is not None:
                    load[other.card] = load.get(other.card, 0) + 1
        card = min(cards, key=lambda c: (load.get(c["card"], 0), c["card"]))
        r.card = card["card"]
        return card

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
            mem = self.working_gb(jt)
            fits = int(free // mem) if mem > 0 else jt.concurrency
            cap = jt.concurrency
            if jt.profile:
                holding = self.cards_holding(jt.profile, cards)
                if not holding:
                    continue
                # the cap is per card holding the profile: three rows on each of two page readers, not three in all
                cap = jt.concurrency * len(holding)
            if counts.get(jt.name, 0) >= min(cap, max(fits, 0)):
                continue
            out.append(jt.name)
        return out

    # ── the loop ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        self.conn = self._connect()
        q.tables(self.conn, self.schema)
        self.probe()
        q.register(self.conn, self.schema, self.name, self.box, self.profile)
        self.read_raises()
        self.log(f"running from {REPO} at {_git(REPO, 'rev-parse', '--short=12', 'HEAD')[1] or '?'}")
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
        for qid in q.enqueue_due(self.conn, self.schema, self.registry, now=now, created_by=self.name, log=self.log):
            self.log(f"timetable: queued row {qid}")
        for qid in q.enqueue_standing(self.conn, self.schema, self.registry, now=now, created_by=self.name):
            self.log(f"standing: queued row {qid}")
        if self.cards_manager:
            self.cards_manager.tick(self, now)
        self._reap_threads()
        self.read_raises()
        if not self.stopping:
            elig = self.eligible()
            # The clock is read again here, not reused from the top of the tick: the card manager
            # may have spent minutes loading a profile in between, and a lease stamped from the
            # tick's start had already lapsed when the 35B model took 124 s (card
            # the-lease-lapses-while-a-large-model-loads: the row was reaped by its own worker).
            claim = q.claim(self.conn, self.schema, self.name, elig, lease_s=self.rules.lease_seconds, now=q.utcnow())
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
        r.memory_gb = self.working_gb(jt)
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

    def _env(self, r: Running, run_id: str, piece: dict | None, card: dict | None = None) -> dict:
        env = {"QV4_RUN_ID": run_id, "QV4_JOB": r.jt.name, "QV4_QUEUE_ID": str(r.claim["id"]), "QV4_WORKER": self.name,
               "QV4_BOX": self.box, "QV4_ARGS": json.dumps(r.claim.get("args") or {}), "PYTHONUNBUFFERED": "1"}
        if piece:
            env["QV4_PIECE"] = str(piece["piece"])
            env["QV4_PIECE_KEY"] = piece["key"]
        if r.jt.profile:
            card = card or self.pick_card(r)
            if card:
                env["QV4_MODEL_URL"] = f"http://127.0.0.1:{card['port']}/v1/chat/completions"
                env["QV4_MODEL_PORT"] = str(card["port"])
                env["QV4_CARD"] = str(card["card"])
            prof = self.profiles[r.jt.profile]
            env["QV4_MODEL"] = prof.model
            env["QV4_PROFILE"] = r.jt.profile
            # what every request on this profile says (ruling 121: the reader's thinking off, review's on with a
            # budget); a job merges it into its call
            env["QV4_MODEL_REQUEST"] = json.dumps({"temperature": prof.temperature, "max_tokens": prof.max_tokens,
                                                   **prof.request_fields}, sort_keys=True)
        return env

    def _run_one(self, conn, r: Running, piece: dict | None) -> runner.Result:
        jt, claim = r.jt, r.claim
        card = self.pick_card(r) if jt.profile else None
        if jt.profile and card is None:
            # the card that held the profile when the job was claimed no longer does: do not run a
            # doomed child; the job goes back and is claimed again when a card holds it
            return runner.Result(None, 0.0, 0, "failed", f"no card on {self.box} holds profile {jt.profile} now", "lease")
        raise_id = r.rerun["id"] if r.rerun else None
        working_mb = int(r.memory_gb * 1024)
        run_id = runs.begin(jt.name, box=self.box, queue_id=claim["id"], card=f"{self.box}:{card['card']}" if card else None,
                            requested_model=self.profiles[jt.profile].model if jt.profile else None,
                            args={"piece": piece["key"] if piece else None, "worker": self.name, "rerun_of_raise": raise_id})
        q.run_begin(conn, self.schema, run_id, job=jt.name, worker=self.name, box=self.box, qid=claim["id"],
                    piece=piece["piece"] if piece else None, declared_mb=int(jt.memory_gb * 1024), working_mb=working_mb,
                    raise_id=raise_id)
        # The renewal clock lives on the claim (`r.last_renew`), not on the piece: a run of
        # pieces each shorter than lease_seconds / 3 used to never renew, and the 90 s lease
        # lapsed under pass one of the trial (card the-worker-s-lease-lapses-under-a-run-of-short-pieces).
        def tick() -> bool:
            if self.stopping:
                return False
            if time.monotonic() - r.last_renew >= self.rules.lease_seconds / 3:
                r.last_renew = time.monotonic()
                if not q.renew(conn, self.schema, claim["id"], claim["token"], lease_s=self.rules.lease_seconds):
                    self.log(f"row {claim['id']}: lease lost; stopping the child")
                    return False
            return True

        res = runner.run(self._argv(jt, [piece["key"]] if piece else []), deadline_s=jt.needs.deadline_s,
                         ceiling_mb=runner.ceiling_for(r.memory_gb), query_timeout_s=jt.needs.query_timeout_s,
                         env=self._env(r, run_id, piece, card), cwd=REPO, tick=tick, log=self.log, nice=jt.nice)
        res.run_id = run_id
        runs.finish(run_id, outcome=res.outcome, error=res.error, peak_mb=res.peak_mb, declared_mb=int(jt.memory_gb * 1024),
                    note=res.stopped_for, working_mb=working_mb, rerun_of_raise=raise_id)
        q.run_end(conn, self.schema, run_id, outcome=res.outcome, exit_code=res.code, error=res.error, detail=res.stopped_for,
                  peak_mb=res.peak_mb)
        if res.peak_mb > jt.memory_gb * 1024:
            self.log(f"{jt.name} run {run_id}: peak {res.peak_mb} MB passed its declared {int(jt.memory_gb * 1024)} MB: "
                     f"flagged, correct the figure")
        return res

    def _raise_memory(self, conn, r: Running, res: runner.Result, pieced: bool) -> dict:
        """A run stopped at its ceiling: record the raise and, within the
        budget and the two raises, queue the job again (ruling 115)."""
        rz = q.raise_memory(conn, self.schema, job=r.jt.name, run_id=res.run_id, qid=r.claim["id"], peak_mb=res.peak_mb,
                            ceiling_mb=runner.ceiling_for(r.memory_gb), held_gb=r.memory_gb,
                            budget_gb=self.memory_budget_gb(), pieced=pieced, registry=self.registry)
        if rz["applied"]:
            with self.lock:
                self.raised[r.jt.name] = max(self.raised.get(r.jt.name, 0.0), rz["raised_gb"])
        self.log(f"row {r.claim['id']} ({r.jt.name}): stopped at {res.peak_mb} MB over its ceiling of "
                 f"{runner.ceiling_for(r.memory_gb)} MB; memory raise {rz['id']}: {rz['note']}")
        return rz

    def _run_job(self, r: Running) -> None:
        conn = None
        try:
            conn = self._connect()
            jt, claim = r.jt, r.claim
            r.rerun = q.raise_for_row(conn, self.schema, claim["id"])
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
                    if res.stopped_for == "memory":
                        rz = self._raise_memory(conn, r, res, pieced=True)
                        if rz["requeued_id"]:
                            q.requeue(conn, self.schema, claim["id"], claim["token"],
                                      detail=f"memory raise {rz['id']}: {rz['note']}")
                            return
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
                rz = self._raise_memory(conn, r, res, pieced=False) if res.stopped_for == "memory" else None
                detail = res.error or ""
                if rz:
                    detail += f"; memory raise {rz['id']}: {rz['note']}"
                q.complete(conn, self.schema, claim["id"], claim["token"], outcome=res.outcome, detail=detail)
                if res.outcome != "ok" and not (rz and rz["requeued_id"]):
                    self.alarm(f"qv4 {self.box}: {jt.name} failed", f"row {claim['id']}: {detail}")
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


def report(conn, schema: str = SCHEMA, path: str = None, registry: dict = None) -> str:
    """The `qv4-scheduler-report` job: the scheduler's state for the checks
    board, as JSON under <live>/checks/."""
    path = path or os.path.join(LIVE, "checks", "scheduler.json")
    st = q.status(conn, schema)
    st["memory_raises"] = q.unfolded_raises(conn, schema, registry)
    st["written"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(st, f, default=str, indent=1)
    return path


def memory_lines(raises: list[dict]) -> list[str]:
    """The raises not yet folded into jobs.toml, one line each, then what to
    fold per job: the largest applied raise (ruling 115)."""
    if not raises:
        return ["memory: no raise waits to be folded into jobs.toml"]
    out = [f"memory: {len(raises)} raise(s) not yet folded into jobs.toml"]
    fold: dict[str, float] = {}
    for x in raises:
        declared = "not in the catalogue" if x["declared_gb"] is None else f"declared {x['declared_gb']:g} GB"
        out.append(f"  raise {x['id']} {x['job']}: {declared}, held {x['held_gb']:g} GB, peak {x['peak_mb']} MB over its "
                   f"ceiling of {x['ceiling_mb']} MB, raised to {x['raised_gb']:g} GB"
                   f"{'' if x['applied'] else ' (NOT applied)'}, run {x['run_id']}, row {x['queue_id']}, "
                   f"{x['at'].astimezone(dt.timezone.utc):%Y-%m-%d %H:%M} UTC: {x['note']}")
        if x["applied"] and x["declared_gb"] is not None:
            fold[x["job"]] = max(fold.get(x["job"], 0.0), float(x["raised_gb"]))
    for job, gb in sorted(fold.items()):
        out.append(f"  fold: [jobs.{job}] memory_gb = {gb:g}")
    return out
