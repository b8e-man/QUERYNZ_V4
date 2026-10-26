-- support/mcpsource: the ingest MCP's pull record (ruling 96). Schema `mcpsource`; idempotent.
-- The documents themselves are in `docs` (the landing wrapper); these say how far each corpus has been taken.

-- one row per corpus: how many of its records (in the MCP's arrival order) have been landed
CREATE TABLE IF NOT EXISTS mcpsource.cursors (
    corpus       text PRIMARY KEY,
    cursor       bigint NOT NULL DEFAULT 0 CHECK (cursor >= 0),   -- the MCP's `cursor`: records already taken
    source_total bigint,                                          -- the MCP's `total` on the last page asked
    updated_at   timestamptz NOT NULL DEFAULT now()
);
-- the newest `updated_at` the change feed (`changes`) has been followed to: records the MCP changed in place
ALTER TABLE mcpsource.cursors ADD COLUMN IF NOT EXISTS changes_since text;
-- how far a re-walk (`--rewalk`) has come, so one longer than its deadline resumes; NULL when none is under way
ALTER TABLE mcpsource.cursors ADD COLUMN IF NOT EXISTS rewalk_at bigint;

-- one row per record taken: its place in the arrival order and the document it landed as. A record the MCP
-- changed in place and a re-walk found again is a second row at the same `seq` with its new hash
CREATE TABLE IF NOT EXISTS mcpsource.arrivals (
    corpus     text NOT NULL,
    seq        bigint NOT NULL,                  -- the record's `seq`, its place in the arrival order
    record_id  text NOT NULL,                    -- the record's `id`
    url        text,                             -- the record's `url`, where it has one
    sha256     text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    new        boolean NOT NULL,                 -- false: the same bytes were already held (an unchanged re-arrival)
    landed_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (corpus, seq, sha256)
);
CREATE INDEX IF NOT EXISTS mcpsource_arrivals_record ON mcpsource.arrivals (corpus, record_id);
CREATE INDEX IF NOT EXISTS mcpsource_arrivals_sha ON mcpsource.arrivals (sha256);

-- the catch log: one line per record that could not be landed (stage: shape, land); `resolved_at` once a later
-- run landed it. Items in (the cursor's advance) = arrivals + unresolved lines
CREATE TABLE IF NOT EXISTS mcpsource.catch (
    corpus      text NOT NULL,
    seq         bigint NOT NULL,
    record_id   text,
    stage       text NOT NULL,
    reason      text NOT NULL,
    at          timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz,
    PRIMARY KEY (corpus, seq, stage)
);

-- a field, or a type of a field, the recorded shapes (shapes.json) do not hold: the record still lands whole,
-- and the run goes red until a lane's register has the field (ruling 96: their fields in our registers)
CREATE TABLE IF NOT EXISTS mcpsource.drift (
    corpus     text NOT NULL,
    field      text NOT NULL,                    -- `name`, or `list.name` for a field of a list's items
    type       text NOT NULL,
    first_seq  bigint NOT NULL,
    records    bigint NOT NULL DEFAULT 1,
    seen_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (corpus, field, type)
);
