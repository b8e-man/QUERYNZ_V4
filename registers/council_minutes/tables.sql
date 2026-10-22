-- registers/council_minutes: every table this lane owns, in `council_minutes`, in two parts. The capture's record
-- (capture.py makes it; never wiped): no capture table holds a row of the source; every listing page and every
-- minutes document stays in the document store verbatim by sha256. The reading's tables (load.py drops and makes
-- them again at every load) come from the listing pages only: the minutes are held and never read (plan 6.3; ruling
-- 79). No private twin: a meeting's venue is never read, and nothing else in a listing names a person's place.

-- ── the capture ──────────────────────────────────────────────────────────────

-- one row per ask of an instance's listing (its default page: the year's meetings)
CREATE TABLE IF NOT EXISTS council_minutes.capture_listings (
    listing_id  bigserial PRIMARY KEY,
    host        text NOT NULL,
    url         text NOT NULL,
    asked_at    timestamptz NOT NULL DEFAULT now(),
    status      integer,
    sha256      text,                                -- the page landed; NULL when the read failed
    rows        integer,                             -- the grid's own row count, counted at capture
    why         text                                 -- a failed read's reason
);

-- one row per minutes document the listings name, and what became of it; a document is asked at most once
CREATE TABLE IF NOT EXISTS council_minutes.capture_documents (
    url         text PRIMARY KEY,
    host        text NOT NULL,
    file        text NOT NULL,
    state       text NOT NULL CHECK (state IN ('landed', 'held by the old estate', 'failed', 'set aside')),
    sha256      text,                                -- landed: the bytes' hash; held by the old estate: its listed hash
    listed_in   text,                                -- the listing page's sha256 that named it first
    asked_at    timestamptz,
    why         text
);

-- an instance not asked again until a session reads why: a challenged, blocked or refused read (hard limit 6), or a
-- listing that answered 404 (the instance moved)
CREATE TABLE IF NOT EXISTS council_minutes.capture_held_hosts (
    host   text PRIMARY KEY,
    since  timestamptz NOT NULL DEFAULT now(),
    why    text NOT NULL
);

CREATE TABLE IF NOT EXISTS council_minutes.capture_set_aside (
    item    text NOT NULL,
    stage   text NOT NULL,
    reason  text NOT NULL,
    at      timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
-- load.py drops these and makes them again at every load, from every listing page held: a row met on several
-- listings is the newest listing's. Each row cites the listing page's sha256, page 1, its row, the reader and the
-- profile.

-- the ledger: one row per listing page read; rows in = meetings out (check.py)
CREATE TABLE IF NOT EXISTS council_minutes.read_listings (
    document    text PRIMARY KEY,
    host        text NOT NULL,
    asked_at    timestamptz,                         -- NULL for a sample listing (no capture record)
    state       text NOT NULL CHECK (state IN ('read', 'set aside')),
    year        integer,
    grid_rows   integer NOT NULL DEFAULT 0,          -- the grid's rows, counted apart from the reader
    meetings    integer NOT NULL DEFAULT 0,
    documents   integer NOT NULL DEFAULT 0
);

-- one row per meeting row of a listing (a supplementary agenda is its own row, as the council lists it)
CREATE TABLE IF NOT EXISTS council_minutes.meetings (
    key              text PRIMARY KEY,                -- <host>/<first document's stem>
    council          text NOT NULL,
    host             text NOT NULL,
    body             text NOT NULL,                   -- the committee, board or council as listed; never the venue
    meeting_date     date NOT NULL,
    meeting_time     text,
    kind             text NOT NULL,                   -- from the listed name: meeting, extraordinary, supplementary, workshop, hearing
    code             text,                            -- the council's own code for the body, from the file name
    documents        integer NOT NULL,
    minutes_file     text,
    minutes_url      text,
    minutes_sha256   text,                            -- the minutes PDF's hash where held (landed, or the old estate's)
    minutes_held     text NOT NULL,                   -- landed | held by the old estate | not yet captured | failed | no minutes listed | html only
    document         text NOT NULL,                   -- the listing page's sha256
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                   -- 'row n' of the grid
    listing_url      text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- every document a meeting row links (agenda, attachments, minutes; HTML and PDF), listed, not read
CREATE TABLE IF NOT EXISTS council_minutes.documents (
    key              text PRIMARY KEY,                -- <host>/<file>
    meeting_key      text NOT NULL,
    kind             text NOT NULL CHECK (kind IN ('agenda', 'agenda attachments', 'minutes', 'minutes attachments')),
    format           text NOT NULL CHECK (format IN ('pdf', 'html')),
    file             text NOT NULL,
    url              text NOT NULL,
    size_as_printed  text,
    sha256           text,                            -- held: the bytes' hash
    held             text NOT NULL,
    document         text NOT NULL,
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS council_minutes.read_set_aside (
    document  text NOT NULL,
    place     text,
    stage     text NOT NULL,
    reason    text NOT NULL
);
