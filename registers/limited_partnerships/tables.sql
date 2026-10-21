-- registers/limited_partnerships: every table this lane owns, in `limited_partnerships` and its private twin, in two
-- parts. The capture's record (capture.py makes it; never wiped): no capture table holds a row of the register; the
-- answers stay in the document store verbatim by sha256. The reading's tables (load.py drops and makes them again at
-- every load, from the answers the listing names). Every address a general partner's role carries goes to
-- `limited_partnerships_private.addresses` and nowhere else (hard limit 15); a partnership's registered office is
-- shown, as a company's is.

-- ── the capture ──────────────────────────────────────────────────────────────

-- one row per night (or proof): the frame's size, the Companies Office file's own count of registered partnerships
CREATE TABLE IF NOT EXISTS limited_partnerships.capture_passes (
    pass_id      bigserial PRIMARY KEY,
    frame_size   integer NOT NULL,                  -- registered limited partnerships in pub.companies at the start
    frame_note   text,
    asked        integer NOT NULL DEFAULT 0,
    set_aside    integer NOT NULL DEFAULT 0,
    stopped      text,                              -- why the night stopped early, if it did
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz
);

-- the listing: one row per call, with the answer's hash (NULL for a 404); the answers are the lane's documents
CREATE TABLE IF NOT EXISTS limited_partnerships.capture_asks (
    pass_id    bigint NOT NULL REFERENCES limited_partnerships.capture_passes (pass_id),
    nzbn       text NOT NULL,
    asked_at   timestamptz NOT NULL,
    status     integer NOT NULL,                    -- 200, or 404 (the register holds no such entity)
    sha256     text,
    new        boolean NOT NULL DEFAULT false       -- the bytes were not held before this call
);
CREATE INDEX IF NOT EXISTS capture_asks_nzbn ON limited_partnerships.capture_asks (nzbn, asked_at);

-- the capture's catch log: one line per call that did not give an answer, with the stage and the reason
CREATE TABLE IF NOT EXISTS limited_partnerships.capture_set_aside (
    pass_id  bigint,
    item     text NOT NULL,                         -- the NZBN asked
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
-- load.py drops these and makes them again at every load. Each row cites the answer's sha256, page 1, its place in
-- the answer (`entity`, `roles[2]`), the reader and the profile.

-- the ledger: one row per answer read; roles in = partners typed + other roles + set aside
CREATE TABLE IF NOT EXISTS limited_partnerships.read_answers (
    document     text PRIMARY KEY,
    nzbn         text,
    asked_at     timestamptz,
    superseded   boolean NOT NULL,                  -- a later answer for the same partnership was read instead
    recognised   boolean NOT NULL,                  -- the answer is the profile's shape (else set aside whole)
    roles        integer NOT NULL,
    partners     integer NOT NULL,                  -- general partners typed
    other_roles  integer NOT NULL,                  -- roles that are not a general partner (a person authorised for service)
    set_aside    integer NOT NULL                   -- roles set aside
);

-- one row per limited partnership, from its newest answer
CREATE TABLE IF NOT EXISTS limited_partnerships.partnerships (
    key                text PRIMARY KEY,            -- limited_partnerships/<nzbn>
    nzbn               text NOT NULL,
    number             text,                        -- the register's own number (sourceRegisterUniqueIdentifier)
    name               text,                        -- NULL where the register withholds it
    name_withheld      boolean NOT NULL,
    kind               text NOT NULL CHECK (kind IN ('nz', 'overseas')),
    entity_type        text,                        -- as answered: Y (NZ) or Z (overseas)
    type_description   text,
    status             text,
    status_code        text,
    registered_on      date,
    country_of_origin  text,
    registered_office  text,                        -- the current registered address: a partnership's office is shown
    office_since       date,                        -- the interface's own start date for that address
    asked_on           date NOT NULL,               -- the New Zealand day the answer was given; a date of the answer only
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL, reader text NOT NULL,
    profile text NOT NULL, profile_version integer NOT NULL, loaded_at timestamptz NOT NULL DEFAULT now()
);

-- one row per general partner (a person or a body, as the register states it). The interface states no start or end
-- date for a partner; `started_on`/`ended_on` stay NULL unless an answer states one, and `current` is the register's
-- own Active/Inactive. Limited partners are not public and are never read.
CREATE TABLE IF NOT EXISTS limited_partnerships.partners (
    key                text PRIMARY KEY,            -- limited_partnerships/<nzbn>/partner/<the role's own identifier>
    partnership_key    text NOT NULL,
    nzbn               text NOT NULL,               -- the partnership's
    role_id            text,                        -- the interface's own identifier for the role
    kind               text NOT NULL CHECK (kind IN ('person', 'body')),
    full_name          text,
    first_name         text,
    middle_names       text,
    last_name          text,
    body_nzbn          text,                        -- a body's NZBN, where the register gives one
    suppressed         boolean NOT NULL,            -- the register withholds the name: blanked on every view
    current            boolean NOT NULL,
    status             text,                        -- as answered: Active, Inactive
    started_on         date,
    ended_on           date,
    dates_stated       boolean NOT NULL,            -- false: the answer states no date for this partner
    asked_on           date NOT NULL,
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL, reader text NOT NULL,
    profile text NOT NULL, profile_version integer NOT NULL, loaded_at timestamptz NOT NULL DEFAULT now()
);

-- the reading's catch log
CREATE TABLE IF NOT EXISTS limited_partnerships.read_set_aside (
    document  text NOT NULL,
    place     text NOT NULL,
    stage     text NOT NULL,
    reason    text NOT NULL
);

-- every address a general partner's role carries (a person's may be a home): never published
CREATE TABLE IF NOT EXISTS limited_partnerships_private.addresses (
    key           text NOT NULL,                    -- the partner's key
    address_type  text,
    address       text NOT NULL,
    document      text NOT NULL,
    place         text NOT NULL
);
