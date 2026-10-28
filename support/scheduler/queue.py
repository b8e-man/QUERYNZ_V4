"""THE ONE JOB QUEUE, in the database (plan step 2.1, 2.8, 2.12, 2.13).

Taken from the lease-and-token pattern of the old `ops/extract_queue.py`,
applied to jobs in general:

  1. LEASE. A claim carries `lease_until`; the worker renews it while the
     job runs. If its box dies the lease lapses and `reap()` re-offers the
     row, so the other worker takes the job (2.8). A worker that stops on
     purpose releases its leases first; a deliberate stop never alarms.
  2. FENCING TOKEN. Every claim carries a uuid. A renewal, a piece or a
     completion names it (`… WHERE id = %s AND lease_token = %s`); if a
     reclaimed zombie wakes and finishes, its rowcount is 0 and it knows it
     no longer owns the work. Duplicate completion is impossible, not merely
     unlikely.
  3. The claim is `FOR UPDATE SKIP LOCKED`: two workers never pick one row.

PIECES (rule 7). A long job is enqueued with a list of piece keys; a worker
takes the pieces one at a time under the job's lease, each recording its
own progress, so a worker stopped mid-job loses at most the piece it was
on and the other worker finishes the rest.

THE CLOCK BELONGS TO THE SCHEDULER (2.12). A timetabled job's next slot is
enqueued by whichever worker notices first; a unique index on (job, slot)
keeps two workers from enqueueing the same slot. A job new to the clock, or
whose timetable changed, takes its NEXT slot: the slot due when it appears
is marked served, so nothing runs the moment a catalogue is read. STANDING SERVICES (2.13)
carry a wanted count; a worker enqueues what is missing.

Every time here is UTC (`timestamptz`); both boxes' clocks hold local time
(trap: 13 hours ahead in summer). `now` is passed in so the policy can be
tested at any clock. Every function takes the connection and the schema,
so the fast tier runs it in a scratch schema of the sample database.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import uuid

from support.scheduler import SCHEMA
from support.scheduler import registry as reg
from support.scheduler.policy import Demand

HERE = os.path.dirname(os.path.abspath(__file__))
TABLES = os.path.join(HERE, "tables.sql")
QUEUED, LEASED, DONE, FAILED, CANCELLED = "queued", "leased", "done", "failed", "cancelled"
CLASS_RANK = {"waiting": 0, "due": 1, "whenever": 2}


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _now(now) -> dt.datetime:
    return now or utcnow()


def tables_sql(schema: str = SCHEMA) -> str:
    with open(TABLES, encoding="utf-8") as f:
        return f.read().replace("{s}", schema)


def tables(conn, schema: str = SCHEMA) -> None:
    """Create the tables under `schema` (idempotent). The schema itself is
    created here too, owned by the connection's role, and the session
    reader may read it: nothing here holds an address or a document's
    text, and a question session answers "what is queued" from it."""
    import support.db as db
    read = db.ROLES["read"]
    with conn.transaction():
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        conn.execute(tables_sql(schema))
        conn.execute(f"GRANT USAGE ON SCHEMA {schema} TO {read}")
        conn.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {read}")
        conn.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {read}")


# ── workers ──────────────────────────────────────────────────────────────────

def register(conn, schema: str, name: str, box: str, profile: dict, now=None) -> None:
    with conn.transaction():
        conn.execute(
            f"INSERT INTO {schema}.workers (name, box, started_at, last_seen, probed_at, profile, state) "
            f"VALUES (%s, %s, %s, %s, %s, %s::jsonb, 'up') "
            f"ON CONFLICT (name) DO UPDATE SET box = EXCLUDED.box, started_at = EXCLUDED.started_at, "
            f"last_seen = EXCLUDED.last_seen, probed_at = EXCLUDED.probed_at, profile = EXCLUDED.profile, "
            f"state = 'up', alarmed_at = NULL",
            (name, box, _now(now), _now(now), _now(now), json.dumps(profile)))


def heartbeat(conn, schema: str, name: str, now=None, profile: dict = None) -> None:
    with conn.transaction():
        if profile is not None:
            conn.execute(f"UPDATE {schema}.workers SET last_seen = %s, probed_at = %s, profile = %s::jsonb, "
                         f"state = 'up', alarmed_at = NULL WHERE name = %s",
                         (_now(now), _now(now), json.dumps(profile), name))
        else:
            conn.execute(f"UPDATE {schema}.workers SET last_seen = %s, state = 'up', alarmed_at = NULL WHERE name = %s",
                         (_now(now), name))


def stop_worker(conn, schema: str, name: str, now=None) -> int:
    """A deliberate stop: the worker's leases go back to the queue at once
    and its state says `stopped`, so the other worker's silence check never
    alarms for it. Returns the rows released."""
    with conn.transaction():
        cur = conn.execute(
            f"UPDATE {schema}.queue SET state = 'queued', lease_token = NULL, lease_owner = NULL, lease_until = NULL, "
            f"detail = concat_ws(' ', detail, 'released by a deliberate stop of ' || %s) "
            f"WHERE state = 'leased' AND lease_owner = %s", (name, name))
        n = cur.rowcount
        conn.execute(f"UPDATE {schema}.pieces SET state = 'todo', worker = NULL WHERE state = 'running' AND worker = %s", (name,))
        conn.execute(f"UPDATE {schema}.workers SET state = 'stopped', last_seen = %s WHERE name = %s", (_now(now), name))
    return n


def workers(conn, schema: str) -> list[dict]:
    rows = conn.execute(f"SELECT name, box, started_at, last_seen, probed_at, profile, state, alarmed_at, note "
                        f"FROM {schema}.workers ORDER BY name").fetchall()
    keys = ("name", "box", "started_at", "last_seen", "probed_at", "profile", "state", "alarmed_at", "note")
    return [dict(zip(keys, r)) for r in rows]


def silent_workers(conn, schema: str, *, after_s: int, me: str, now=None) -> list[dict]:
    """Workers that were up and have not been heard from for `after_s`
    seconds, not yet alarmed for (step 2.10). Marks them `silent` and
    `alarmed_at`, so the alarm is raised once; a heartbeat clears it."""
    cutoff = _now(now) - dt.timedelta(seconds=after_s)
    with conn.transaction():
        rows = conn.execute(
            f"UPDATE {schema}.workers SET state = 'silent', alarmed_at = %s "
            f"WHERE state = 'up' AND name <> %s AND last_seen < %s RETURNING name, box, last_seen",
            (_now(now), me, cutoff)).fetchall()
    return [{"name": r[0], "box": r[1], "last_seen": r[2]} for r in rows]


# ── enqueue, claim, renew, complete, reap ────────────────────────────────────

def enqueue(conn, schema: str, job: str, *, args: dict = None, cls: str = None, priority: int = None,
            due_at=None, not_before=None, pieces: list = None, created_by: str = "", standing: bool = False,
            timetable_slot=None, registry: dict = None, now=None) -> int | None:
    """Queue one instance of `job`. `pieces` is a list of piece keys (rule
    7). A timetabled instance names its `timetable_slot`; a second enqueue of
    the same slot returns None (the unique index: two workers, one slot)."""
    registry = registry if registry is not None else reg.load()
    jt = registry.get(job)
    cls = cls or (jt.cls if jt else "whenever")
    priority = priority if priority is not None else (jt.priority if jt else 99)
    pieces = list(pieces or [])
    with conn.transaction():
        row = conn.execute(
            f"INSERT INTO {schema}.queue (job, args, cls, priority, state, due_at, not_before, created_at, created_by, "
            f"pieces_total, standing, timetable_slot) VALUES (%s, %s::jsonb, %s, %s, 'queued', %s, %s, %s, %s, %s, %s, %s) "
            f"ON CONFLICT (job, timetable_slot) WHERE timetable_slot IS NOT NULL DO NOTHING RETURNING id",
            (job, json.dumps(args or {}), cls, priority, due_at, not_before, _now(now), created_by, len(pieces),
             standing, timetable_slot)).fetchone()
        if row is None:
            return None
        qid = row[0]
        for i, key in enumerate(pieces, 1):
            conn.execute(f"INSERT INTO {schema}.pieces (queue_id, piece, key) VALUES (%s, %s, %s)", (qid, i, str(key)))
    return qid


def claim(conn, schema: str, worker: str, eligible: list, *, lease_s: int, now=None, exclude_ids: list = None) -> dict | None:
    """The most urgent queued row this worker can run, leased to it. Order:
    class (someone waiting first), due time, priority, age. `eligible` is
    the job types the worker can run right now (programs present, memory
    fits, a card holding the profile); nothing else is offered."""
    if not eligible:
        return None
    t = _now(now)
    token = uuid.uuid4()
    with conn.transaction():
        row = conn.execute(
            f"WITH pick AS ("
            f"  SELECT id FROM {schema}.queue"
            f"  WHERE state = 'queued' AND job = ANY(%s) AND (not_before IS NULL OR not_before <= %s)"
            f"    AND NOT (id = ANY(%s))"
            f"  ORDER BY CASE cls WHEN 'waiting' THEN 0 WHEN 'due' THEN 1 ELSE 2 END, due_at NULLS LAST, priority, created_at"
            f"  FOR UPDATE SKIP LOCKED LIMIT 1)"
            f"UPDATE {schema}.queue q SET state = 'leased', lease_token = %s, lease_owner = %s, lease_until = %s,"
            f"  started_at = COALESCE(q.started_at, %s), attempts = attempts + 1"
            f" FROM pick WHERE q.id = pick.id"
            f" RETURNING q.id, q.job, q.args, q.cls, q.priority, q.due_at, q.attempts, q.pieces_total, q.pieces_done, "
            f" q.standing, q.timetable_slot",
            (list(eligible), t, list(exclude_ids or []), token, worker, t + dt.timedelta(seconds=lease_s), t)).fetchone()
    if row is None:
        return None
    keys = ("id", "job", "args", "cls", "priority", "due_at", "attempts", "pieces_total", "pieces_done", "standing", "timetable_slot")
    out = dict(zip(keys, row))
    out["token"] = token
    return out


def renew(conn, schema: str, qid: int, token, *, lease_s: int, now=None) -> bool:
    """Extend the lease. False means the lease was lost: the worker must stop
    the work, because another worker may already hold it."""
    with conn.transaction():
        cur = conn.execute(f"UPDATE {schema}.queue SET lease_until = %s WHERE id = %s AND lease_token = %s AND state = 'leased'",
                           (_now(now) + dt.timedelta(seconds=lease_s), qid, token))
    return cur.rowcount == 1


def complete(conn, schema: str, qid: int, token, *, outcome: str, detail: str = "", now=None) -> bool:
    """Finish a leased row. `outcome` ok → done, else failed. False means
    the lease was lost first (the fence)."""
    state = DONE if outcome == "ok" else FAILED
    with conn.transaction():
        cur = conn.execute(
            f"UPDATE {schema}.queue SET state = %s, outcome = %s, detail = concat_ws(' | ', NULLIF(detail, ''), NULLIF(%s, '')), "
            f"finished_at = %s, lease_token = NULL, lease_until = NULL WHERE id = %s AND lease_token = %s AND state = 'leased'",
            (state, outcome, detail[:2000], _now(now), qid, token))
        if cur.rowcount == 1:
            conn.execute(f"UPDATE {schema}.timetable SET last_done = %s WHERE job = (SELECT job FROM {schema}.queue WHERE id = %s)",
                         (_now(now), qid))
    return cur.rowcount == 1


def requeue(conn, schema: str, qid: int, token, *, detail: str = "", not_before=None, now=None) -> bool:
    """Give a leased row back unfinished (a piece failed and will be retried,
    the worker is stopping). Pieces keep their progress."""
    with conn.transaction():
        cur = conn.execute(
            f"UPDATE {schema}.queue SET state = 'queued', lease_token = NULL, lease_owner = NULL, lease_until = NULL, "
            f"not_before = %s, detail = concat_ws(' | ', NULLIF(detail, ''), NULLIF(%s, '')) "
            f"WHERE id = %s AND lease_token = %s AND state = 'leased'",
            (not_before, detail[:2000], qid, token))
        conn.execute(f"UPDATE {schema}.pieces SET state = 'todo' WHERE queue_id = %s AND state = 'running'", (qid,))
    return cur.rowcount == 1


def cancel(conn, schema: str, qid: int, why: str, now=None) -> bool:
    with conn.transaction():
        cur = conn.execute(f"UPDATE {schema}.queue SET state = 'cancelled', outcome = 'cancelled', detail = %s, finished_at = %s "
                           f"WHERE id = %s AND state IN ('queued', 'leased')", (why, _now(now), qid))
    return cur.rowcount == 1


def reap(conn, schema: str, now=None) -> list[dict]:
    """Rows whose lease lapsed: the worker's box died, or the worker hung.
    They go back to the queue with their pieces' progress kept; a piece that
    was running is the one piece lost. Returns what was reaped so the
    worker records it."""
    t = _now(now)
    with conn.transaction():
        rows = conn.execute(
            f"UPDATE {schema}.queue SET state = 'queued', lease_token = NULL, lease_owner = NULL, lease_until = NULL, "
            f"detail = 'lease lapsed from ' || COALESCE(lease_owner, '?') || ' at ' || %s "
            f"WHERE state = 'leased' AND lease_until < %s RETURNING id, job, pieces_done, pieces_total",
            (t.isoformat(timespec="seconds"), t)).fetchall()
        out = []
        for qid, job, done, total in rows:
            lost = conn.execute(f"UPDATE {schema}.pieces SET state = 'todo', worker = NULL, attempts = attempts "
                                f"WHERE queue_id = %s AND state = 'running' RETURNING piece", (qid,)).fetchall()
            out.append({"id": qid, "job": job, "pieces_done": done, "pieces_total": total, "pieces_lost": [r[0] for r in lost]})
    return out


# ── pieces (rule 7) ──────────────────────────────────────────────────────────

def next_piece(conn, schema: str, qid: int, token, worker: str, now=None) -> dict | None:
    """The next piece of a leased job, marked running. None when no piece is
    left, or when the lease is no longer this worker's (the fence)."""
    with conn.transaction():
        owns = conn.execute(f"SELECT 1 FROM {schema}.queue WHERE id = %s AND lease_token = %s AND state = 'leased'",
                            (qid, token)).fetchone()
        if not owns:
            return None
        row = conn.execute(
            f"WITH pick AS (SELECT piece FROM {schema}.pieces WHERE queue_id = %s AND state = 'todo' "
            f"ORDER BY piece FOR UPDATE SKIP LOCKED LIMIT 1) "
            f"UPDATE {schema}.pieces p SET state = 'running', worker = %s, started_at = %s, attempts = attempts + 1 "
            f"FROM pick WHERE p.queue_id = %s AND p.piece = pick.piece RETURNING p.piece, p.key, p.attempts",
            (qid, worker, _now(now), qid)).fetchone()
    return {"piece": row[0], "key": row[1], "attempts": row[2]} if row else None


def finish_piece(conn, schema: str, qid: int, token, piece: int, *, ok: bool, seconds: float, detail: str = "",
                 now=None) -> bool:
    """Record a piece's end under the job's lease. A failed piece goes back
    to `todo` for one more try; after three it stays failed."""
    with conn.transaction():
        owns = conn.execute(f"SELECT 1 FROM {schema}.queue WHERE id = %s AND lease_token = %s AND state = 'leased'",
                            (qid, token)).fetchone()
        if not owns:
            return False
        if ok:
            conn.execute(f"UPDATE {schema}.pieces SET state = 'done', done_at = %s, seconds = %s, detail = %s "
                         f"WHERE queue_id = %s AND piece = %s", (_now(now), seconds, detail[:500], qid, piece))
            conn.execute(f"UPDATE {schema}.queue SET pieces_done = pieces_done + 1 WHERE id = %s", (qid,))
        else:
            conn.execute(f"UPDATE {schema}.pieces SET state = CASE WHEN attempts >= 3 THEN 'failed' ELSE 'todo' END, "
                         f"done_at = %s, seconds = %s, detail = %s WHERE queue_id = %s AND piece = %s",
                         (_now(now), seconds, detail[:500], qid, piece))
    return True


def pieces_left(conn, schema: str, qid: int) -> dict:
    row = conn.execute(f"SELECT count(*) FILTER (WHERE state = 'todo'), count(*) FILTER (WHERE state = 'running'), "
                       f"count(*) FILTER (WHERE state = 'done'), count(*) FILTER (WHERE state = 'failed') "
                       f"FROM {schema}.pieces WHERE queue_id = %s", (qid,)).fetchone()
    return {"todo": row[0], "running": row[1], "done": row[2], "failed": row[3]}


# ── the timetable (2.12) and the standing services (2.13) ────────────────────

def slot_for(jt: reg.JobType, now: dt.datetime) -> dt.datetime | None:
    """The timetable slot that is due at `now`, in UTC: the latest multiple
    of `every_s` since the epoch, or today's `at_utc` once the clock has
    passed it. None for a job with no timetable."""
    if jt.every_s:
        epoch = int(now.timestamp()) // jt.every_s * jt.every_s
        return dt.datetime.fromtimestamp(epoch, dt.timezone.utc)
    if jt.at_utc:
        # the latest of the day's times the clock has passed; before the first, yesterday's last
        times = sorted(tuple(int(x) for x in t.split(":")) for t in jt.at_utc)
        passed = [now.replace(hour=h, minute=m, second=0, microsecond=0) for h, m in times
                  if now >= now.replace(hour=h, minute=m, second=0, microsecond=0)]
        if passed:
            return passed[-1]
        h, m = times[-1]
        return now.replace(hour=h, minute=m, second=0, microsecond=0) - dt.timedelta(days=1)
    return None


def clock_of(jt: reg.JobType) -> str | None:
    """The timetable as one comparable string ("every 600s", "at 03:30,15:00");
    None for a job with no timetable. Stored on the job's timetable row, so a
    change to it is seen whichever worker, or whichever start, reads it."""
    if jt.every_s:
        return f"every {jt.every_s}s"
    if jt.at_utc:
        return "at " + ",".join(sorted(jt.at_utc))
    return None


def next_slot(jt: reg.JobType, now: dt.datetime) -> dt.datetime | None:
    """The first slot after `now`: when a job new to the clock first runs."""
    if jt.every_s:
        return slot_for(jt, now) + dt.timedelta(seconds=jt.every_s)
    if jt.at_utc:
        times = sorted(tuple(int(x) for x in t.split(":")) for t in jt.at_utc)
        for day in (0, 1):
            for h, m in times:
                t = now.replace(hour=h, minute=m, second=0, microsecond=0) + dt.timedelta(days=day)
                if t > now:
                    return t
    return None


def handover(conn, schema: str, job: str, *, registry: dict = None, now=None, by: str = "handover") -> dt.datetime | None:
    """A job moving from a timer on one box onto the queue's clock (2.12):
    the slot due at `now` is marked served, because the timer served it, so
    the queue's first instance is the NEXT slot and nothing runs twice at
    the handover. Returns the slot marked, None for a job with no timetable."""
    registry = registry if registry is not None else reg.load()
    jt = registry.get(job)
    if jt is None:
        return None
    slot = slot_for(jt, _now(now))
    if slot is None:
        return None
    _mark_served(conn, schema, job, slot, clock_of(jt), by)
    return slot


def _mark_served(conn, schema: str, job: str, slot: dt.datetime, clock: str | None, by: str) -> None:
    """Mark `slot` served under `clock`, never moving an existing clock back."""
    conn.execute(f"INSERT INTO {schema}.timetable (job, last_slot, last_by, clock) VALUES (%s, %s, %s, %s) "
                 f"ON CONFLICT (job) DO UPDATE SET last_slot = GREATEST({schema}.timetable.last_slot, EXCLUDED.last_slot), "
                 f"last_by = EXCLUDED.last_by, clock = EXCLUDED.clock", (job, slot, by, clock))


def enqueue_due(conn, schema: str, registry: dict = None, *, now=None, created_by: str = "timetable",
                log=None) -> list[int]:
    """Queue every timetabled job whose slot is due and not yet served. Any
    worker may do this; the unique index keeps the slot single. A slot is
    not queued while an earlier instance of the job is still queued or
    leased: a stuck job does not pile up behind itself.

    A job the clock has never served (no timetable row: new to the
    catalogue, or enabled for the first time), or whose timetable differs
    from the one its row records, is not queued: the slot due now is marked
    served, as `handover` does, and its first run is the next slot. Before
    this a new daily job was owed yesterday's last slot and ran the moment
    a worker read the catalogue (procurement-1 and settlements-1, 22
    October). A row from before the clock was recorded (`clock` NULL) adopts
    the current timetable and is served as before."""
    registry = registry if registry is not None else reg.load()
    t = _now(now)
    out = []
    for jt in registry.values():
        if not jt.enabled or not (jt.every_s or jt.at_utc):
            continue
        slot = slot_for(jt, t)
        if slot is None:
            continue
        clock = clock_of(jt)
        with conn.transaction():
            last = conn.execute(f"SELECT last_slot, clock FROM {schema}.timetable WHERE job = %s", (jt.name,)).fetchone()
            if last is None or (last[1] is not None and last[1] != clock):
                why = "new to the clock" if last is None else f"timetable changed from {last[1]!r}"
                _mark_served(conn, schema, jt.name, slot, clock, f"{created_by}: {why}")
                if log:
                    log(f"timetable: {jt.name} {why} ({clock}); slot {slot:%Y-%m-%d %H:%M} UTC marked served, "
                        f"first run {next_slot(jt, t):%Y-%m-%d %H:%M} UTC")
                continue
            if last[1] is None:
                conn.execute(f"UPDATE {schema}.timetable SET clock = %s WHERE job = %s", (clock, jt.name))
            if last[0] is not None and last[0] >= slot:
                continue
            busy = conn.execute(f"SELECT 1 FROM {schema}.queue WHERE job = %s AND state IN ('queued', 'leased') LIMIT 1",
                                (jt.name,)).fetchone()
            if busy:
                continue
            qid = enqueue(conn, schema, jt.name, cls=jt.cls, priority=jt.priority, due_at=slot, created_by=created_by,
                          timetable_slot=slot, registry=registry, now=t)
            if qid is not None:
                conn.execute(f"INSERT INTO {schema}.timetable (job, last_slot, last_by, clock) VALUES (%s, %s, %s, %s) "
                             f"ON CONFLICT (job) DO UPDATE SET last_slot = EXCLUDED.last_slot, last_by = EXCLUDED.last_by, "
                             f"clock = EXCLUDED.clock", (jt.name, slot, created_by, clock))
                out.append(qid)
    return out


def enqueue_standing(conn, schema: str, registry: dict = None, *, now=None, created_by: str = "standing") -> list[int]:
    """A standing service carries a wanted count: queue what is missing, in
    priority order. A surviving box starts whatever is missing in order of
    importance, within what it can carry (the worker's eligibility)."""
    registry = registry if registry is not None else reg.load()
    out = []
    for jt in sorted(registry.values(), key=lambda j: j.priority):
        if not jt.enabled or not jt.wanted:
            continue
        with conn.transaction():
            have = conn.execute(f"SELECT count(*) FROM {schema}.queue WHERE job = %s AND standing AND state IN ('queued', 'leased')",
                                (jt.name,)).fetchone()[0]
            for _ in range(max(0, jt.wanted - have)):
                qid = enqueue(conn, schema, jt.name, cls=jt.cls, priority=jt.priority, created_by=created_by, standing=True,
                              registry=registry, now=now)
                out.append(qid)
    return out


# ── what the planner needs ───────────────────────────────────────────────────

def demands(conn, schema: str, registry: dict = None, *, now=None) -> dict[str, Demand]:
    """Per job type: how much work waits (queued instances, plus the pieces
    left on leased ones), its most urgent class, when it first waited, its
    nearest due time, and its measured seconds per item from the last runs."""
    registry = registry if registry is not None else reg.load()
    t = _now(now)
    rows = conn.execute(
        f"SELECT job, state, cls, created_at, due_at, GREATEST(1, pieces_total - pieces_done) FROM {schema}.queue "
        f"WHERE state IN ('queued', 'leased') AND (not_before IS NULL OR not_before <= %s)", (t,)).fetchall()
    acc: dict[str, dict] = {}
    for job, state, cls, created, due, left in rows:
        a = acc.setdefault(job, {"depth": 0, "cls": "whenever", "since": None, "due": None})
        a["depth"] += int(left)
        if CLASS_RANK.get(cls, 2) < CLASS_RANK[a["cls"]]:
            a["cls"] = cls
        if state == QUEUED and (a["since"] is None or created < a["since"]):
            a["since"] = created
        if due is not None and (a["due"] is None or due < a["due"]):
            a["due"] = due
    secs = dict(conn.execute(
        f"SELECT job, avg(seconds) FROM (SELECT job, seconds, row_number() OVER (PARTITION BY job ORDER BY finished_at DESC) rn "
        f"FROM {schema}.runs WHERE outcome = 'ok' AND seconds IS NOT NULL) x WHERE rn <= 20 GROUP BY job").fetchall())
    out = {}
    for job, a in acc.items():
        jt = registry.get(job)
        item = secs.get(job)
        item = float(item) if item is not None else (jt.item_seconds if jt else None)
        out[job] = Demand(a["depth"], a["cls"], a["since"].timestamp() if a["since"] else None,
                          a["due"].timestamp() if a["due"] else None, item)
    return out


# ── runs in the database (the record that moves with it) ─────────────────────

def run_begin(conn, schema: str, run_id: str, *, job: str, worker: str, box: str, qid: int = None, piece: int = None,
              card: int = None, declared_mb: int = None, working_mb: int = None, raise_id: int = None, now=None) -> None:
    with conn.transaction():
        conn.execute(f"INSERT INTO {schema}.runs (run_id, queue_id, piece, job, worker, box, card, started_at, declared_mb, "
                     f"working_mb, raise_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (run_id) DO NOTHING",
                     (run_id, qid, piece, job, worker, box, card, _now(now), declared_mb, working_mb, raise_id))


def run_end(conn, schema: str, run_id: str, *, outcome: str, exit_code: int = None, error: str = None, detail: str = None,
            peak_mb: int = None, served_model: str = None, now=None) -> None:
    with conn.transaction():
        conn.execute(f"UPDATE {schema}.runs SET finished_at = %s, seconds = EXTRACT(EPOCH FROM (%s - started_at)), outcome = %s, "
                     f"exit_code = %s, error = %s, detail = %s, peak_mb = %s, served_model = %s WHERE run_id = %s",
                     (_now(now), _now(now), outcome, exit_code, error, detail, peak_mb, served_model, run_id))


def over_declared(conn, schema: str) -> list[dict]:
    rows = conn.execute(f"SELECT run_id, job, peak_mb, declared_mb FROM {schema}.runs WHERE peak_mb > declared_mb "
                        f"ORDER BY finished_at DESC LIMIT 50").fetchall()
    return [{"run_id": r[0], "job": r[1], "peak_mb": r[2], "declared_mb": r[3]} for r in rows]


# ── memory raises (ruling 115) ───────────────────────────────────────────────
# A job stopped at its memory ceiling failed by a figure the scheduler holds,
# not by its own error, so the worker raises the figure and queues it again.
# The working figure lives here, never in jobs.toml: it is the larger of the
# declared figure and the job's latest applied raise, read from the table at
# every tick, so a restarted worker (or the other box's) places by it too.

RAISES_PER_ORIGIN = 2


def raised_figure_gb(ceiling_mb: int) -> float:
    """Twice the ceiling crossed, rounded up to the next 0.5 GB: the peak at a
    kill is a floor on the need, not the need."""
    return math.ceil(2 * ceiling_mb / 512) * 0.5


def working_figures(conn, schema: str) -> dict[str, float]:
    """Per job, the figure of its latest applied raise."""
    rows = conn.execute(f"SELECT DISTINCT ON (job) job, raised_gb FROM {schema}.memory_raises WHERE applied "
                        f"ORDER BY job, id DESC").fetchall()
    return {r[0]: float(r[1]) for r in rows}


def raise_for_row(conn, schema: str, qid: int) -> dict | None:
    """The raise that queued row `qid` again (a re-run), or None."""
    r = conn.execute(f"SELECT id, origin_queue_id, raised_gb FROM {schema}.memory_raises WHERE requeued_id = %s "
                     f"ORDER BY id DESC LIMIT 1", (qid,)).fetchone()
    return {"id": r[0], "origin_queue_id": r[1], "raised_gb": float(r[2])} if r else None


def raise_memory(conn, schema: str, *, job: str, run_id: str, qid: int, peak_mb: int, ceiling_mb: int, held_gb: float,
                 budget_gb: float | None, pieced: bool = False, registry: dict = None, now=None) -> dict:
    """Record the raise for a run stopped at `ceiling_mb` on row `qid`, and
    queue the job again unless the raised figure is over `budget_gb` or the
    row's origin has had RAISES_PER_ORIGIN raises already. A pieced job's row
    is its own re-run (the worker gives it back with its progress); a
    standing service's next copy is queued by `enqueue_standing`. Returns
    the raise: id, raised_gb, applied, requeued_id, note."""
    raised = raised_figure_gb(ceiling_mb)
    prior = raise_for_row(conn, schema, qid)
    origin = prior["origin_queue_id"] if prior else qid
    with conn.transaction():
        row = conn.execute(f"SELECT args, cls, priority, standing FROM {schema}.queue WHERE id = %s", (qid,)).fetchone()
        done = conn.execute(f"SELECT count(*) FROM {schema}.memory_raises WHERE origin_queue_id = %s", (origin,)).fetchone()[0]
        applied = budget_gb is None or raised <= budget_gb
        requeued = None
        if not applied:
            note = (f"stays failed: {raised:g} GB is over the box's budget of {budget_gb:g} GB (its memory less the reserve); "
                    f"the working figure stays {held_gb:g} GB")
        elif done >= RAISES_PER_ORIGIN:
            note = (f"stays failed: raised {done} times already for row {origin}; the next run takes {raised:g} GB")
        elif row is None:
            note = f"stays failed: row {qid} is gone; the next run takes {raised:g} GB"
        elif row[3]:
            note = f"standing service: its next copy runs at {raised:g} GB"
        elif pieced:
            requeued = qid
            note = f"row {qid} given back with its pieces' progress, to run at {raised:g} GB"
        else:
            requeued = enqueue(conn, schema, job, args=row[0], cls=row[1], priority=row[2],
                               created_by=f"memory raise of row {qid}", registry=registry, now=now)
            note = f"queued again as row {requeued} at {raised:g} GB"
        rid = conn.execute(
            f"INSERT INTO {schema}.memory_raises (at, job, run_id, queue_id, origin_queue_id, peak_mb, ceiling_mb, held_gb, "
            f"raised_gb, budget_gb, applied, requeued_id, note) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            f"RETURNING id", (_now(now), job, run_id, qid, origin, peak_mb, ceiling_mb, held_gb, raised, budget_gb, applied,
                              requeued, note)).fetchone()[0]
    return {"id": rid, "raised_gb": raised, "applied": applied, "requeued_id": requeued, "origin_queue_id": origin,
            "note": note}


def unfolded_raises(conn, schema: str, registry: dict = None) -> list[dict]:
    """Every raise jobs.toml has not caught up with: its declared figure is
    below the raised one. The integrator folds them at a merge; a raise is
    folded when the declared figure is at least the raised figure."""
    registry = registry if registry is not None else reg.load()
    if conn.execute("SELECT to_regclass(%s)", (f"{schema}.memory_raises",)).fetchone()[0] is None:
        return []                                  # the table is not made yet (the worker makes it at start)
    rows = conn.execute(f"SELECT id, at, job, run_id, queue_id, peak_mb, ceiling_mb, held_gb, raised_gb, budget_gb, applied, "
                        f"requeued_id, note FROM {schema}.memory_raises ORDER BY job, id").fetchall()
    keys = ("id", "at", "job", "run_id", "queue_id", "peak_mb", "ceiling_mb", "held_gb", "raised_gb", "budget_gb", "applied",
            "requeued_id", "note")
    out = []
    for r in rows:
        d = dict(zip(keys, r))
        jt = registry.get(d["job"])
        d["declared_gb"] = jt.memory_gb if jt else None
        if d["declared_gb"] is None or d["declared_gb"] < float(d["raised_gb"]):
            out.append(d)
    return out


# ── cards and swaps ──────────────────────────────────────────────────────────

def upsert_card(conn, schema: str, box: str, card: int, **fields) -> None:
    cols = ["box", "card"] + list(fields)
    vals = [box, card] + list(fields.values())
    sets = ", ".join(f"{k} = EXCLUDED.{k}" for k in fields) + ", updated_at = now()"
    with conn.transaction():
        conn.execute(f"INSERT INTO {schema}.cards ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(vals))}) "
                     f"ON CONFLICT (box, card) DO UPDATE SET {sets}", vals)


def cards(conn, schema: str, box: str = None) -> list[dict]:
    where = "WHERE box = %s" if box else ""
    rows = conn.execute(f"SELECT box, card, reserved, reserved_why, memory_total_gb, memory_used_gb, product, profile, port, "
                        f"pid, server_started_at, holder, holder_since, draining, slots, slots_busy, worker, updated_at "
                        f"FROM {schema}.cards {where} ORDER BY box, card", (box,) if box else ()).fetchall()
    keys = ("box", "card", "reserved", "reserved_why", "memory_total_gb", "memory_used_gb", "product", "profile", "port",
            "pid", "server_started_at", "holder", "holder_since", "draining", "slots", "slots_busy", "worker", "updated_at")
    return [dict(zip(keys, r)) for r in rows]


def record_swap(conn, schema: str, box: str, card: int, action: str, why: str, *, from_profile: str = None,
                to_profile: str = None, job: str = None, by_worker: str = None, load_seconds: float = None,
                served_model: str = None, ok: bool = None, detail: str = None, now=None) -> int:
    with conn.transaction():
        row = conn.execute(
            f"INSERT INTO {schema}.swaps (at, box, card, action, from_profile, to_profile, job, why, by_worker, load_seconds, "
            f"served_model, ok, detail) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (_now(now), box, card, action, from_profile, to_profile, job, why, by_worker, load_seconds, served_model, ok,
             detail)).fetchone()
    return row[0]


def measured_load_seconds(conn, schema: str) -> dict[str, float]:
    """Per profile, the average of its last five measured loads (rule 9)."""
    rows = conn.execute(f"SELECT to_profile, avg(load_seconds) FROM (SELECT to_profile, load_seconds, "
                        f"row_number() OVER (PARTITION BY to_profile ORDER BY at DESC) rn FROM {schema}.swaps "
                        f"WHERE action = 'load' AND ok AND load_seconds IS NOT NULL) x WHERE rn <= 5 GROUP BY to_profile").fetchall()
    return {r[0]: float(r[1]) for r in rows}


# ── reading it back ──────────────────────────────────────────────────────────

def status(conn, schema: str, limit: int = 20) -> dict:
    counts = dict(conn.execute(f"SELECT state, count(*) FROM {schema}.queue GROUP BY state").fetchall())
    by_job = conn.execute(f"SELECT job, state, count(*) FROM {schema}.queue WHERE state IN ('queued', 'leased') "
                          f"GROUP BY job, state ORDER BY job").fetchall()
    recent = conn.execute(f"SELECT id, job, state, lease_owner, pieces_done, pieces_total, outcome, created_at, finished_at "
                          f"FROM {schema}.queue ORDER BY id DESC LIMIT %s", (limit,)).fetchall()
    swaps = conn.execute(f"SELECT at, box, card, action, from_profile, to_profile, job, load_seconds, served_model, ok, why "
                         f"FROM {schema}.swaps ORDER BY id DESC LIMIT %s", (limit,)).fetchall()
    runs_ = conn.execute(f"SELECT run_id, job, worker, started_at, finished_at, outcome, peak_mb, declared_mb, error "
                         f"FROM {schema}.runs ORDER BY started_at DESC LIMIT %s", (limit,)).fetchall()
    return {"queue": {k: int(v) for k, v in counts.items()},
            "waiting": [{"job": j, "state": s, "n": int(n)} for j, s, n in by_job],
            "recent": [dict(zip(("id", "job", "state", "lease_owner", "pieces_done", "pieces_total", "outcome", "created_at",
                                 "finished_at"), r)) for r in recent],
            "workers": workers(conn, schema), "cards": cards(conn, schema),
            "swaps": [dict(zip(("at", "box", "card", "action", "from_profile", "to_profile", "job", "load_seconds",
                                "served_model", "ok", "why"), r)) for r in swaps],
            "runs": [dict(zip(("run_id", "job", "worker", "started_at", "finished_at", "outcome", "peak_mb", "declared_mb",
                               "error"), r)) for r in runs_]}
