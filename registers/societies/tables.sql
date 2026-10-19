-- registers/societies: the tables this lane owns, in `societies` and `societies_private`.
-- Loaded into a staging or scratch schema by replacing `societies.` (and `societies_private.`) with that schema's
-- name (load.sql). Rows come from two kinds of document: the once-only export of the old estate's tables
-- (capture.py: taken from the old estate's tables, original not held; `place` is the export line), and the NZBN
-- register's entity detail as it answered one ask (`place` is the role's position in its `roles` list).

-- every incorporated society the register names
CREATE TABLE IF NOT EXISTS societies.societies (
    key              text PRIMARY KEY,                      -- societies/<nzbn>, or societies/number/<incorporation number>
    nzbn             text,                                  -- the NZBN as filed
    number           text,                                  -- the society's incorporation number
    name             text NOT NULL,
    status           text,                                  -- as filed: registered, dissolved, removed, liquidation
    registered_on    date,                                  -- as filed
    removed_on       date,                                  -- as filed: the deregistration date
    act              text,                                  -- as filed: the Act it is registered under
    reregistered_on  date,                                  -- as filed: re-registered under the 2022 Act
    charity_number   text,                                  -- as filed: its Charities Register number
    in_latest        boolean NOT NULL,                      -- in the latest monthly file read
    last_file        text NOT NULL,
    party_society    boolean NOT NULL DEFAULT false,        -- asked first every night (capture.is_party_society)
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- a society's earlier state, where the monthly file changed it
CREATE TABLE IF NOT EXISTS societies.society_states (
    key              text PRIMARY KEY,                      -- <society key>/in/<file>[/<n>]
    society_key      text NOT NULL,
    file             text NOT NULL,
    name             text NOT NULL,
    status           text,
    registered_on    date,
    removed_on       date,
    vanished_at      text,                                  -- when the old loader saw it go, as it recorded
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per officer role the register lists. The register gives no role number: the key is the society and the
-- role's filed content (names and start); roles that share it take /2, /3 in a fixed order of their content.
-- The window is the register's own: started_on and ended_on as it states them, never a load day. read_on is the
-- day of the ask that listed it, as evidence of when, not as a date of the role
CREATE TABLE IF NOT EXISTS societies.officers (
    key              text PRIMARY KEY,                      -- societies/<nzbn>/officer/<12 hex of names and start>[/n]
    society_key      text NOT NULL,
    nzbn             text NOT NULL,
    first_name       text,
    middle_names     text,
    last_name        text,
    full_name        text NOT NULL,
    role_type        text NOT NULL,                         -- as filed: Officer
    role_status      text,                                  -- as filed: Active | Inactive
    started_on       date,                                  -- as filed
    ended_on         date,                                  -- as filed; the register states it
    first_read_on    date NOT NULL,                         -- the first ask that listed this role
    last_read_on     date NOT NULL,                         -- the last ask that listed it
    suppressed       boolean NOT NULL DEFAULT false,
    unique_identifier text,                                 -- as filed (one per society in every answer read so far)
    old_id           text,                                  -- the old estate's row id, for mapping old decisions by content only
    private_ref      text,                                  -- the key into societies_private.officer_addresses, when the answer gave one
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- every ask of the register: when, whether it answered, how many officers it gave. An ask is a fact apart from
-- what it found (old C531): the clock the nightly slice runs on
CREATE TABLE IF NOT EXISTS societies.asks (
    key              text PRIMARY KEY,                      -- societies/<nzbn>/ask/<asked at, to the second>
    society_key      text NOT NULL,
    nzbn             text NOT NULL,
    asked_at         timestamptz NOT NULL,
    answered         boolean NOT NULL,                      -- the register answered at all
    officers         integer NOT NULL,
    note             text,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- every document the lane took, and what it did with it
CREATE TABLE IF NOT EXISTS societies.files (
    document   text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    name       text NOT NULL,
    kind       text NOT NULL,                               -- societies | officers | asks | entity
    status     text NOT NULL,                               -- read
    PRIMARY KEY (document, name)
);

-- the catch log: one line for every item the lane could not take to a row
CREATE TABLE IF NOT EXISTS societies.set_aside (
    item       text NOT NULL,                               -- <document sha>/line <n>, or <document sha>/roles <n>
    stage      text NOT NULL,                               -- capture | societies | officers | asks | entity
    reason     text NOT NULL,
    count      integer NOT NULL DEFAULT 1,
    at         timestamptz NOT NULL DEFAULT now()
);

-- an officer's address where an answer carries one, keyed by the role's key: never published, never read into a
-- session (hard limits 11 and 15). The old tables hold none
CREATE TABLE IF NOT EXISTS societies_private.officer_addresses (
    key        text PRIMARY KEY,
    address    jsonb NOT NULL,
    document   text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$')
);
