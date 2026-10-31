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

A PIECED ROW RUNS ITS PIECES SEVERAL AT ONCE (31 October). Measured on live
that day: three reader rows each running pieces one after another gave the
standing server 3 to 4 requests at a time and 7 a minute; eight hand streams
of the same pieces read 155 a minute, sixteen 145. So the row's runner
(`_run_pieces`) keeps N pieces in flight, each a `--piece KEY` child with its
own run record, where N = min(the job's `concurrency`, (the profile's
`streams` less every other row's pieces in flight on the same server) //
the job's `threads`), never under 1, worked out again before every piece
starts and written to the row (`in_flight`, shown by `status`). The lease
and the piece records are kept by the runner thread on the one connection;
the children only run. A row claimed with no pieces runs its type's
`pieces_command` first and its lines are the pieces; none means the row is
done at once ("nothing waiting"). A finished row queues its type's `then`
jobs, one in flight each (`queue.then_rows`).

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
        self.in_flight = 0                        # pieces (children) running now; 1 for a job not cut into pieces
        self.pieced = False                       # its pieces are counted on their cards (Worker.card_pieces)
        self.cap: int | None = None               # the runner's N, as last worked out and written to the row
        self.lost = False                         # the lease was lost: every child's tick says stop


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
        self.retry_pause_s = 5.0                   # after one failed piece, before the next is started
        self.card_pieces: dict = {}                 # card index → pieces in flight on it, every row (pick_card)

    # ── pieces in flight (31 October) ────────────────────────────────────────

    def streams_of(self, profile: str) -> int | None:
        """The pieces worth keeping in flight on `profile` across every row
        on its server (the profile's measured `streams`, else its slots)."""
        return reg.streams_of(self.profiles, profile) if profile in self.profiles else None

    def in_flight_cap(self, r: Running) -> int:
        """N for this row now: the job's concurrency, cut to what the
        profile's streams leave after every other row's pieces in flight on
        the same server (each counted times its job's threads), divided by
        this job's own threads; never under 1, so a row always moves."""
        cap = r.jt.concurrency
        if r.jt.profile:
            streams = self.streams_of(r.jt.profile)
            if streams:
                on = self.serving(r.jt.profile)
                # a server the worker starts runs on ONE card, so its streams are per card: two cards holding the
                # profile take twice the pieces (1 November 2026, Qwen 3.6 one copy a card); a standing server
                # across several cards is one server and its streams are its own
                srv = self.profiles.get(on)
                if srv is not None and not srv.standing:
                    streams *= max(1, len(self.cards_holding(r.jt.profile)))
                with self.lock:
                    others = sum(o.in_flight * o.jt.threads for o in self.running.values()
                                 if o is not r and o.jt.profile and self.serving(o.jt.profile) == on)
                cap = min(cap, (streams - others) // max(1, r.jt.threads))
        return max(1, cap)

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
            # pieces in flight on each card (1 November 2026: a row's own pieces were all sent to the lowest card,
            # since only OTHER rows were counted), and each other row that is not cut into pieces
            load = dict(self.card_pieces)
            for other in self.running.values():
                if other is not r and other.card is not None and not other.pieced:
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

    def _argv(self, command, extra: list[str]) -> list[str]:
        argv = list(command) + list(extra)
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

    def _begin_run(self, conn, r: Running, piece: dict | None, card: dict | None) -> tuple[str, int]:
        """The run's two records (the journal and the table) before the child
        starts. Returns (run_id, working_mb)."""
        jt, claim = r.jt, r.claim
        raise_id = r.rerun["id"] if r.rerun else None
        working_mb = int(r.memory_gb * 1024)
        run_id = runs.begin(jt.name, box=self.box, queue_id=claim["id"], card=f"{self.box}:{card['card']}" if card else None,
                            requested_model=self.profiles[jt.profile].model if jt.profile else None,
                            args={"piece": piece["key"] if piece else None, "worker": self.name, "rerun_of_raise": raise_id})
        q.run_begin(conn, self.schema, run_id, job=jt.name, worker=self.name, box=self.box, qid=claim["id"],
                    piece=piece["piece"] if piece else None, declared_mb=int(jt.memory_gb * 1024), working_mb=working_mb,
                    raise_id=raise_id)
        return run_id, working_mb

    def _end_run(self, conn, r: Running, res: runner.Result, run_id: str, working_mb: int) -> None:
        jt = r.jt
        raise_id = r.rerun["id"] if r.rerun else None
        res.run_id = run_id
        runs.finish(run_id, outcome=res.outcome, error=res.error, peak_mb=res.peak_mb, declared_mb=int(jt.memory_gb * 1024),
                    note=res.stopped_for, working_mb=working_mb, rerun_of_raise=raise_id)
        q.run_end(conn, self.schema, run_id, outcome=res.outcome, exit_code=res.code, error=res.error, detail=res.stopped_for,
                  peak_mb=res.peak_mb)
        if res.peak_mb > jt.memory_gb * 1024:
            self.log(f"{jt.name} run {run_id}: peak {res.peak_mb} MB passed its declared {int(jt.memory_gb * 1024)} MB: "
                     f"flagged, correct the figure")

    def _renew_if_due(self, conn, r: Running) -> bool:
        """Renew the row's lease when a third of it has passed. The clock is
        the claim's, not a piece's (card the-worker-s-lease-lapses-under-a-
        run-of-short-pieces). False, and `r.lost`, when the lease is gone."""
        if r.lost:
            return False
        if time.monotonic() - r.last_renew >= self.rules.lease_seconds / 3:
            r.last_renew = time.monotonic()
            if not q.renew(conn, self.schema, r.claim["id"], r.claim["token"], lease_s=self.rules.lease_seconds):
                self.log(f"row {r.claim['id']}: lease lost; stopping the child(ren)")
                r.lost = True
                return False
        return True

    def _run_one(self, conn, r: Running, piece: dict | None) -> runner.Result:
        """One child on the job thread (a job not cut into pieces): the lease
        is renewed from the child's tick."""
        jt = r.jt
        card = self.pick_card(r) if jt.profile else None
        if jt.profile and card is None:
            # the card that held the profile when the job was claimed no longer does: do not run a
            # doomed child; the job goes back and is claimed again when a card holds it
            return runner.Result(None, 0.0, 0, "failed", f"no card on {self.box} holds profile {jt.profile} now", "lease")
        run_id, working_mb = self._begin_run(conn, r, piece, card)

        def tick() -> bool:
            if self.stopping:
                return False
            return self._renew_if_due(conn, r)

        res = runner.run(self._argv(jt.command, [piece["key"]] if piece else []), deadline_s=jt.needs.deadline_s,
                         ceiling_mb=runner.ceiling_for(r.memory_gb), query_timeout_s=jt.needs.query_timeout_s,
                         env=self._env(r, run_id, piece, card), cwd=REPO, tick=tick, log=self.log, nice=jt.nice)
        self._end_run(conn, r, res, run_id, working_mb)
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

    # ── the pieces command and the concurrent runner (31 October) ────────────

    def _pieces_command(self, conn, r: Running) -> tuple[list[str], str | None]:
        """Run the job's `pieces_command` in the job's environment and read
        the piece keys from its output, one a line, blank lines and repeats
        dropped (its stderr flows to the journal). Recorded as a run with
        piece 0. Returns (keys, error): an error means the row fails."""
        jt = r.jt
        card = self.pick_card(r) if jt.profile else None
        run_id, working_mb = self._begin_run(conn, r, {"piece": 0, "key": "pieces_command"}, card)
        env = dict(os.environ)
        env.update(self._env(r, run_id, None, card))
        env.pop("QV4_PIECE", None)
        if jt.needs.query_timeout_s:
            env["PGOPTIONS"] = f"-c statement_timeout={int(jt.needs.query_timeout_s) * 1000}"
        t0 = time.monotonic()
        keys, error, code = [], None, None
        try:
            p = subprocess.run(self._argv(jt.pieces_command, []), cwd=REPO, env=env, stdout=subprocess.PIPE, text=True,
                               timeout=jt.needs.deadline_s)
            code = p.returncode
            if code:
                error = f"pieces_command exit {code} (its stderr is in the journal)"
            else:
                seen = set()
                for line in p.stdout.splitlines():
                    k = line.strip()
                    if k and k not in seen:
                        seen.add(k)
                        keys.append(k)
        except subprocess.TimeoutExpired:
            error = f"pieces_command stopped at its deadline of {jt.needs.deadline_s:.0f}s"
        except (OSError, ValueError) as e:
            error = f"pieces_command {type(e).__name__}: {str(e)[:300]}"
        res = runner.Result(code, round(time.monotonic() - t0, 1), 0, "failed" if error else "ok", error)
        self._end_run(conn, r, res, run_id, working_mb)
        return keys, error

    def _start_piece(self, conn, r: Running, piece: dict, card: dict | None, results) -> None:
        """One piece as a child in its own thread; its result goes on
        `results` for the runner thread, which keeps every record."""
        jt = r.jt
        run_id, working_mb = self._begin_run(conn, r, piece, card)
        argv = self._argv(jt.command, [piece["key"]])
        env = self._env(r, run_id, piece, card)
        c = card["card"] if card else None
        with self.lock:
            r.in_flight += 1
            r.pieced = True
            if c is not None:
                self.card_pieces[c] = self.card_pieces.get(c, 0) + 1

        def go():
            res = runner.run(argv, deadline_s=jt.needs.deadline_s, ceiling_mb=runner.ceiling_for(r.memory_gb),
                             query_timeout_s=jt.needs.query_timeout_s, env=env, cwd=REPO,
                             tick=lambda: not (self.stopping or r.lost), log=self.log, nice=jt.nice)
            if c is not None:
                with self.lock:
                    self.card_pieces[c] = max(0, self.card_pieces.get(c, 0) - 1)
            results.put((piece, res, run_id, working_mb))

        threading.Thread(target=go, name=f"piece-{r.claim['id']}-{piece['piece']}", daemon=True).start()

    def _run_pieces(self, conn, r: Running) -> None:
        """The row's pieces, N at a time (`in_flight_cap`, worked out again
        before each start). The runner stops STARTING pieces, lets the ones
        in flight finish, and gives the row back when: the worker is
        stopping; the lease is lost; no card on this box holds the profile
        any more (a draining card finishes its pieces and takes no more); a
        piece was stopped at its memory ceiling and the raise re-runs the row
        (ruling 115); two pieces failed in a row (the environment, not two bad
        pieces: retried in two minutes). One failed piece pauses the starts
        for `retry_pause_s`. Otherwise the row completes, done when no piece
        failed, and its `then` jobs are queued either way."""
        import queue as pyqueue
        jt, claim = r.jt, r.claim
        qid, token = claim["id"], claim["token"]
        results: pyqueue.Queue = pyqueue.Queue()
        stop: str | None = None
        detail, not_before = "", None
        hold_until, in_a_row = 0.0, 0
        while True:
            if stop is None and self.stopping:
                stop, detail = "stopping", "worker stopping"
            if stop is None and r.lost:
                stop, detail = "lease", "worker stopping or lease lost"
            while stop is None and time.monotonic() >= hold_until:
                cap = self.in_flight_cap(r)
                if cap != r.cap:
                    r.cap = cap
                    q.set_in_flight(conn, self.schema, qid, cap)
                if r.in_flight >= cap:
                    break
                card = self.pick_card(r) if jt.profile else None
                if jt.profile and card is None:
                    stop, detail = "no card", f"no card on {self.box} holds profile {jt.profile} now; given back with its progress"
                    break
                piece = q.next_piece(conn, self.schema, qid, token, self.name)
                if piece is None:
                    break
                self._start_piece(conn, r, piece, card, results)
            if r.in_flight == 0:
                if stop is None and time.monotonic() < hold_until:
                    time.sleep(max(0.0, hold_until - time.monotonic()))
                    self._renew_if_due(conn, r)
                    continue
                break
            due = self.rules.lease_seconds / 3 - (time.monotonic() - r.last_renew)
            try:
                piece, res, run_id, working_mb = results.get(timeout=max(0.05, min(due, 1.0)))
            except pyqueue.Empty:
                self._renew_if_due(conn, r)
                continue
            with self.lock:
                r.in_flight -= 1
            self._end_run(conn, r, res, run_id, working_mb)
            q.finish_piece(conn, self.schema, qid, token, piece["piece"], ok=res.outcome == "ok", seconds=res.seconds,
                           detail=res.error or "")
            if res.stopped_for == "lease" and stop is None:
                stop, detail = "lease", "worker stopping" if self.stopping else "worker stopping or lease lost"
            if res.stopped_for == "memory":
                rz = self._raise_memory(conn, r, res, pieced=True)
                if rz["requeued_id"] and stop is None:
                    stop, detail = "memory", f"memory raise {rz['id']}: {rz['note']}"
            if res.outcome != "ok":
                in_a_row += 1
                if in_a_row >= 2 and stop is None:
                    stop = "failures"
                    detail = f"{in_a_row} pieces failed in a row ({res.error}); retried in 2 minutes"
                    not_before = q.utcnow() + dt.timedelta(seconds=120)
                    self.log(f"row {qid} ({jt.name}): {in_a_row} pieces failed in a row; given back for 2 minutes")
                else:
                    hold_until = time.monotonic() + self.retry_pause_s
            else:
                in_a_row = 0
            self._renew_if_due(conn, r)
        q.set_in_flight(conn, self.schema, qid, None)
        if stop is not None:
            q.requeue(conn, self.schema, qid, token, detail=detail, not_before=not_before)
            r.outcome = f"given back: {detail}"
            return
        left = q.pieces_left(conn, self.schema, qid)
        ok = left["failed"] == 0 and left["todo"] == 0
        r.outcome = "ok" if ok else "failed"
        q.complete(conn, self.schema, qid, token, outcome=r.outcome, detail=f"pieces done {left['done']}, failed {left['failed']}")
        if not ok:
            self.alarm(f"qv4 {self.box}: {jt.name} failed", f"row {qid}: {left['failed']} piece(s) failed")
        self._then(conn, r)

    def _then(self, conn, r: Running) -> None:
        """A row has finished: queue its type's `then` jobs (one in flight each)."""
        for line in q.then_rows(conn, self.schema, r.claim["id"], r.jt, registry=self.registry):
            self.log(f"row {r.claim['id']} ({r.jt.name}) {line}")

    def _run_job(self, r: Running) -> None:
        conn = None
        try:
            conn = self._connect()
            jt, claim = r.jt, r.claim
            r.rerun = q.raise_for_row(conn, self.schema, claim["id"])
            if jt.pieces:
                if not claim.get("pieces_total") and jt.pieces_command:
                    keys, error = self._pieces_command(conn, r)
                    if error:
                        r.outcome = "failed"
                        q.complete(conn, self.schema, claim["id"], claim["token"], outcome="failed", detail=error)
                        self.alarm(f"qv4 {self.box}: {jt.name} failed", f"row {claim['id']}: {error}")
                        return
                    if not keys:
                        r.outcome = "ok"
                        q.complete(conn, self.schema, claim["id"], claim["token"], outcome="ok", detail="nothing waiting")
                        self._then(conn, r)
                        return
                    n = q.add_pieces(conn, self.schema, claim["id"], claim["token"], keys)
                    if n < 0:
                        self.log(f"row {claim['id']}: lease lost before its pieces were set")
                        return
                    self.log(f"row {claim['id']} ({jt.name}): {n} piece(s) from its pieces_command")
                self._run_pieces(conn, r)
            else:
                with self.lock:
                    r.in_flight = 1
                res = self._run_one(conn, r, None)
                with self.lock:
                    r.in_flight = 0
                if res.stopped_for == "lease":
                    q.requeue(conn, self.schema, claim["id"], claim["token"], detail="worker stopping or lease lost")
                    r.outcome = "given back"
                    return
                rz = self._raise_memory(conn, r, res, pieced=False) if res.stopped_for == "memory" else None
                detail = res.error or ""
                if rz:
                    detail += f"; memory raise {rz['id']}: {rz['note']}"
                r.outcome = res.outcome
                q.complete(conn, self.schema, claim["id"], claim["token"], outcome=res.outcome, detail=detail)
                if res.outcome != "ok" and not (rz and rz["requeued_id"]):
                    self.alarm(f"qv4 {self.box}: {jt.name} failed", f"row {claim['id']}: {detail}")
                if res.outcome == "ok":
                    self._then(conn, r)
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
