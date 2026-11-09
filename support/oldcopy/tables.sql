-- The old-estate copy's ledgers (support/oldcopy; ruling 160). Idempotent. Schema `{ledger}`, private by its suffix:
-- a key bound or an old file path can carry a name. NEVER WIPED: no code here drops or deletes a row of these tables;
-- the copied tables themselves (old_<database>_private.*) can be regenerated and may be dropped and copied again.

CREATE SCHEMA IF NOT EXISTS {ledger};

-- one line per batch tried, good or bad: the source's rows and md5, the landed rows and md5
CREATE TABLE IF NOT EXISTS {ledger}.batches (
    batch_id     bigserial PRIMARY KEY,
    piece        text NOT NULL,                  -- database:schema.table
    range_no     int NOT NULL DEFAULT 0,         -- 0 for a NEW table; the inventory's missing range for a PARTLY one
    after_key    text,                           -- JSON list of the key's text, exclusive; NULL = from the start
    through_key  text,                           -- JSON list of the key's text, inclusive
    rows_source  bigint,
    rows_copied  bigint,
    rows_landed  bigint,
    md5_source   text,
    md5_landed   text,
    ok           boolean NOT NULL,
    why          text,
    seconds      numeric,
    at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS batches_piece ON {ledger}.batches (piece, range_no, batch_id);

-- where each table (and each missing range of a PARTLY one) has got to
CREATE TABLE IF NOT EXISTS {ledger}.cursors (
    piece        text NOT NULL,
    range_no     int NOT NULL DEFAULT 0,
    after_key    text,                           -- JSON list; the last key landed
    caught_up    boolean NOT NULL DEFAULT false, -- the last run found nothing more
    batches      int NOT NULL DEFAULT 0,
    rows         bigint NOT NULL DEFAULT 0,
    updated_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (piece, range_no)
);

-- a table the copier would not copy, and why (no usable key, a type the new database lacks, a shape that differs)
CREATE TABLE IF NOT EXISTS {ledger}.refusals (
    refusal_id   bigserial PRIMARY KEY,
    piece        text NOT NULL,
    why          text NOT NULL,
    at           timestamptz NOT NULL DEFAULT now()
);

-- one line per old file tried: landed (new or already held), skipped as held by its old path, or failed
CREATE TABLE IF NOT EXISTS {ledger}.files (
    file_id      bigserial PRIMARY KEY,
    store        text NOT NULL,
    old_path     text NOT NULL,
    size         bigint,
    mtime        double precision,
    sha256       text,
    outcome      text NOT NULL,                  -- landed-new, landed-held, held-by-path, failed, too-big
    why          text,
    at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS files_path ON {ledger}.files (store, old_path);

CREATE TABLE IF NOT EXISTS {ledger}.file_cursors (
    store        text PRIMARY KEY,
    after_path   text,                           -- the last path walked, relative to the store's root
    caught_up    boolean NOT NULL DEFAULT false,
    files        bigint NOT NULL DEFAULT 0,
    updated_at   timestamptz NOT NULL DEFAULT now()
);
