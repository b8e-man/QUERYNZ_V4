-- The scheduler's tables (plan step 2.1: one job queue, kept in the database,
-- so it moves with the database when a box is lost). Schema `scheduler` in
-- querynz_v4; the fast tier's copy goes in a session's scratch schema of
-- querynz_v4_sample, so `{s}` is the schema. Idempotent. No table here ever
-- holds a person's home address or a document's text: keys, counts, times,
-- reasons and figures only.

CREATE TABLE IF NOT EXISTS {s}.workers (
    name          text PRIMARY KEY,                    -- node2, node2-b (the rehearsal's second worker)
    box           text NOT NULL,
    started_at    timestamptz NOT NULL DEFAULT now(),
    last_seen     timestamptz NOT NULL DEFAULT now(),  -- the heartbeat (step 2.10)
    probed_at     timestamptz,
    profile       jsonb NOT NULL DEFAULT '{}'::jsonb,  -- the hardware profile, probed never typed (2.3)
    state         text NOT NULL DEFAULT 'up' CHECK (state IN ('up', 'stopped', 'silent')),
    alarmed_at    timestamptz,                         -- when the other worker raised the alarm for this one
    note          text
);

CREATE TABLE IF NOT EXISTS {s}.queue (
    id              bigserial PRIMARY KEY,
    job             text NOT NULL,                     -- the job type, qv4-…
    args            jsonb NOT NULL DEFAULT '{}'::jsonb,
    cls             text NOT NULL DEFAULT 'whenever' CHECK (cls IN ('waiting', 'due', 'whenever')),
    priority        int NOT NULL DEFAULT 99,
    state           text NOT NULL DEFAULT 'queued'
                    CHECK (state IN ('queued', 'leased', 'done', 'failed', 'cancelled')),
    due_at          timestamptz,                       -- rule 8; a timetabled instance's slot
    not_before      timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    created_by      text,
    lease_token     uuid,                              -- the fencing token (2.8): a completion names it
    lease_owner     text,                              -- the worker holding the lease
    lease_until     timestamptz,                       -- lapsed = the box died; the other worker takes it
    started_at      timestamptz,
    finished_at     timestamptz,
    attempts        int NOT NULL DEFAULT 0,
    pieces_total    int NOT NULL DEFAULT 0,            -- rule 7
    pieces_done     int NOT NULL DEFAULT 0,
    standing        boolean NOT NULL DEFAULT false,    -- a standing service's instance (2.13)
    timetable_slot  timestamptz,                       -- the timetable slot this instance serves (2.12)
    outcome         text,
    detail          text
);
CREATE UNIQUE INDEX IF NOT EXISTS queue_one_instance_per_slot ON {s}.queue (job, timetable_slot)
    WHERE timetable_slot IS NOT NULL;
CREATE INDEX IF NOT EXISTS queue_queued ON {s}.queue (priority, created_at) WHERE state = 'queued';
CREATE INDEX IF NOT EXISTS queue_leased ON {s}.queue (lease_until) WHERE state = 'leased';

CREATE TABLE IF NOT EXISTS {s}.pieces (
    queue_id    bigint NOT NULL REFERENCES {s}.queue (id),
    piece       int NOT NULL,
    key         text NOT NULL,                         -- what the piece is: a document hash, a source key
    state       text NOT NULL DEFAULT 'todo' CHECK (state IN ('todo', 'running', 'done', 'failed')),
    attempts    int NOT NULL DEFAULT 0,
    worker      text,
    started_at  timestamptz,
    done_at     timestamptz,
    seconds     real,
    detail      text,
    PRIMARY KEY (queue_id, piece)
);
CREATE INDEX IF NOT EXISTS pieces_todo ON {s}.pieces (queue_id, piece) WHERE state = 'todo';

CREATE TABLE IF NOT EXISTS {s}.cards (
    box               text NOT NULL,
    card              int NOT NULL,
    reserved          boolean NOT NULL DEFAULT false,   -- step 2.9: never planned
    reserved_why      text,
    memory_total_gb   real,                             -- probed
    memory_used_gb    real,
    product           text,
    profile           text,                             -- the resident model profile; NULL = cold
    port              int,
    pid               int,
    server_started_at timestamptz,
    holder            text,                             -- the job type holding the lease (the slice)
    holder_since      timestamptz,
    draining          boolean NOT NULL DEFAULT false,
    slots             int,
    slots_busy        int,
    worker            text,
    updated_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (box, card)
);

-- hard limit 25: every swap is recorded, with its reason
CREATE TABLE IF NOT EXISTS {s}.swaps (
    id            bigserial PRIMARY KEY,
    at            timestamptz NOT NULL DEFAULT now(),
    box           text NOT NULL,
    card          int NOT NULL,
    action        text NOT NULL,                       -- load | handover | release | drain | unload | failed | died | stray | stop | start (the night window, ruling 129)
    from_profile  text,
    to_profile    text,
    job           text,
    why           text NOT NULL,                       -- the planner's reason, verbatim
    by_worker     text,
    load_seconds  real,                                -- measured: from the start of the server to its first healthy answer
    served_model  text,                                -- what the card actually answered with, read back
    ok            boolean,
    detail        text
);

CREATE TABLE IF NOT EXISTS {s}.runs (
    run_id        text PRIMARY KEY,
    queue_id      bigint,
    piece         int,
    job           text NOT NULL,
    worker        text,
    box           text,
    card          int,
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz,
    seconds       real,
    outcome       text,                                -- ok | failed | refused | partial | lapsed
    exit_code     int,
    error         text,
    detail        text,
    peak_mb       int,                                 -- step 2.6: measured peak memory
    declared_mb   int,                                 -- what the job declared per worker
    served_model  text
);
CREATE INDEX IF NOT EXISTS runs_job_started ON {s}.runs (job, started_at);

CREATE TABLE IF NOT EXISTS {s}.timetable (
    job        text PRIMARY KEY,
    last_slot  timestamptz,
    last_done  timestamptz,
    last_by    text
);
-- the timetable the clock last served the job under (`queue.clock_of`): a job with no row, or
-- whose timetable differs, takes its NEXT slot (card the-scheduler-s-worker-runs-the-main-checkout-…)
ALTER TABLE {s}.timetable ADD COLUMN IF NOT EXISTS clock text;

-- Ruling 115: a job stopped at its memory ceiling has its working figure raised here, never in
-- jobs.toml (the repository's declared figure); the working figure is the larger of the declared
-- figure and the job's latest applied raise. A raise over the box's budget is recorded, not applied.
CREATE TABLE IF NOT EXISTS {s}.memory_raises (
    id               bigserial PRIMARY KEY,
    at               timestamptz NOT NULL DEFAULT now(),
    job              text NOT NULL,
    run_id           text NOT NULL,                    -- the run stopped at its ceiling
    queue_id         bigint NOT NULL,                  -- the row that run served
    origin_queue_id  bigint NOT NULL,                  -- the first row of the chain: at most two raises re-run per origin
    peak_mb          int NOT NULL,                     -- measured at the stop: a floor on the need, not the need
    ceiling_mb       int NOT NULL,                     -- the ceiling it crossed
    held_gb          real NOT NULL,                    -- the working figure it ran under
    raised_gb        real NOT NULL,                    -- twice the ceiling, rounded up to the next 0.5 GB
    budget_gb        real,                             -- the box's memory less the reserve, at the raise
    applied          boolean NOT NULL,                 -- false: over the budget, the working figure unchanged
    requeued_id      bigint,                           -- the row queued again (a pieced job's own row); NULL = stays failed
    note             text NOT NULL                     -- what was done, in words
);
CREATE INDEX IF NOT EXISTS memory_raises_job ON {s}.memory_raises (job, id);
CREATE INDEX IF NOT EXISTS memory_raises_requeued ON {s}.memory_raises (requeued_id);
ALTER TABLE {s}.runs ADD COLUMN IF NOT EXISTS working_mb int;     -- the working figure the run was placed and capped under
ALTER TABLE {s}.runs ADD COLUMN IF NOT EXISTS raise_id bigint;    -- a re-run: the raise that queued it

-- 31 October: the chain runs itself. `pieces_source` says where a pieced row's pieces came from ('listed' at the
-- enqueue, 'command' from the job's pieces_command run at the claim); `then_of` names the finished row whose `then`
-- queued this one; `in_flight` is the pieces the runner keeps running at once on a leased row (its figure, not a count).
ALTER TABLE {s}.queue ADD COLUMN IF NOT EXISTS pieces_source text;
ALTER TABLE {s}.queue ADD COLUMN IF NOT EXISTS then_of bigint;
ALTER TABLE {s}.queue ADD COLUMN IF NOT EXISTS in_flight int;
