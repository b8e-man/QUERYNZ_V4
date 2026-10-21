-- registers/building_practitioners: every table this lane owns, in `building_practitioners` and its private twin, in
-- two parts. The capture's record (capture.py makes it; never wiped): no capture table holds a row of the source; the
-- list pages stay in the document store verbatim by sha256. The reading's tables (load.py drops and makes them again
-- at every load). No address of any kind is read: the decisions list publishes a region at most (hard limit 15). The
-- register of practitioners is held (Building Act 2004, s 307): its table exists so the view can say "not held", and
-- nothing fills it.

-- ── the capture ──────────────────────────────────────────────────────────────

-- one row per pass over the Board's decisions list: its stated total (the list's own "of N results") and progress
CREATE TABLE IF NOT EXISTS building_practitioners.capture_passes (
    pass_id      bigserial PRIMARY KEY,
    stated       integer,                           -- "Displaying 20 of N results" on the pass's first page
    next_start   integer NOT NULL DEFAULT 0,        -- the next page's `start`; the pass resumes from it
    pages        integer NOT NULL DEFAULT 0,
    items        integer NOT NULL DEFAULT 0,
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz
);

-- the listing: one row per list page landed, with its hash
CREATE TABLE IF NOT EXISTS building_practitioners.capture_pages (
    pass_id   bigint NOT NULL REFERENCES building_practitioners.capture_passes (pass_id),
    page_no   integer NOT NULL,
    start     integer NOT NULL,
    url       text NOT NULL,
    sha256    text NOT NULL,
    items     integer NOT NULL,
    new       boolean NOT NULL,
    PRIMARY KEY (pass_id, page_no)
);

-- the documents about the source (the copyright grant, the privacy statement, the register's statement of s 307)
CREATE TABLE IF NOT EXISTS building_practitioners.capture_docs (
    name      text NOT NULL,
    url       text NOT NULL,
    sha256    text NOT NULL,
    new       boolean NOT NULL,
    at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS building_practitioners.capture_set_aside (
    pass_id  bigint,
    item     text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
-- load.py drops these and makes them again at every load. Each row cites the page's sha256, page 1, its place
-- (`complaint=CB26816`), the reader and the profile.

-- the ledger: one row per list page read; items in = decisions typed + read again on a later page + set aside
CREATE TABLE IF NOT EXISTS building_practitioners.read_pages (
    document     text PRIMARY KEY,
    pass_id      bigint,
    stated       integer,
    items        integer NOT NULL,
    typed        integer NOT NULL,
    superseded   integer NOT NULL,
    set_aside    integer NOT NULL
);

-- one row per published complaint decision of the Building Practitioners Board
CREATE TABLE IF NOT EXISTS building_practitioners.decisions (
    key               text PRIMARY KEY,             -- building_practitioners/decision/<complaint number>/<kind>
    complaint_number  text NOT NULL,                -- the Board's own (CB26816)
    citation          text,                         -- [2025] BPB 26816
    decision_kind     text NOT NULL,                -- as the title states it: final decision, penalty decision, …
    name              text,                         -- the practitioner as the title publishes it; NULL when suppressed
    lbp_number        text,                         -- NULL when suppressed
    suppressed        boolean NOT NULL,             -- the Board withholds the name, or the item records a suppression
    region            text,                         -- the area the list publishes and nothing finer; NULL when "Omitted"
    licence_classes   text[] NOT NULL,
    decided_on        date,
    penalties         text[] NOT NULL,              -- s 318 orders as listed
    grounds           text[] NOT NULL,              -- s 317 grounds as listed, each with "- not upheld" where so
    upheld            boolean,                      -- any ground upheld; NULL when the list gives no ground
    decision_url      text,                         -- carries the name: withheld on the view when suppressed
    pdf_url           text,
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL, reader text NOT NULL,
    profile text NOT NULL, profile_version integer NOT NULL, loaded_at timestamptz NOT NULL DEFAULT now()
);

-- the register of licensed building practitioners: HELD (Building Act 2004, s 307). Nothing fills this table until
-- Arthur's decision and a profile built from the first authorised page; the view over it says "not held" by being
-- empty, and its columns are the brief's (no address: hard limit 15).
CREATE TABLE IF NOT EXISTS building_practitioners.practitioners (
    key               text PRIMARY KEY,             -- building_practitioners/lbp/<licence number>
    licence_number    text NOT NULL,
    name              text,
    suppressed        boolean NOT NULL,
    licence_classes   jsonb,                        -- [{class, area of practice, licensed on, status, ended on}]
    status            text,
    area              text,                         -- the town or region the register publishes, nothing finer
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL, reader text NOT NULL,
    profile text NOT NULL, profile_version integer NOT NULL, loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS building_practitioners.read_set_aside (
    document  text NOT NULL,
    place     text NOT NULL,
    stage     text NOT NULL,
    reason    text NOT NULL
);

-- the private twin holds nothing: a decision's summary is never kept (it can name a property or a complainant), and
-- the register's addresses are never read.
