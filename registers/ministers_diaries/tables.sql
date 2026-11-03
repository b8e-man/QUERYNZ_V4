-- registers/ministers_diaries: the tables this lane owns, in `ministers_diaries` and `ministers_diaries_private`.
-- Loaded into a staging or scratch schema by replacing `ministers_diaries.` (and `ministers_diaries_private.`) with
-- that schema's name (load.sql). Every entry is read from one document: a record of the ingest MCP's
-- `parliament-diaries` corpus, landed whole by support/mcpsource (rulings 78, 94, 96): one meeting of a minister's
-- monthly diary release, which Arthur's provider read from the Beehive's PDF off-estate. The estate never fetched
-- the PDF. A record served changed is a second document; an entry is read from the version the pull saw last
-- (mcpsource.arrivals by landed_at, never the highest seq), and every version is in `files`.

-- one row per release: the PDF, as the entries' `source_url` names it
CREATE TABLE IF NOT EXISTS ministers_diaries.releases (
    key              text PRIMARY KEY,                      -- the `source_url` as served
    source_url       text NOT NULL,
    pdf_url          text,                                  -- the PDF's address on www.beehive.govt.nz; NULL where the
                                                            -- provider served a file name only (none is made up)
    file_name        text NOT NULL,                         -- the PDF's file name, decoded
    upload_folder    text,                                  -- the site's own folder, YYYY-MM (when the file went up)
    minister         text,                                  -- as the entries name the minister
    ministers_named  integer NOT NULL,                      -- distinct ministers its entries name (one, or a fault)
    portfolios       text[] NOT NULL DEFAULT '{}',          -- as released, in order of first appearance
    month            text,                                  -- YYYY-MM: the file name's month, else the entries' one month
    month_named      text,                                  -- YYYY-MM as the file name gives it
    entries_month    text,                                  -- YYYY-MM when every entry falls in one calendar month
    months           integer NOT NULL,                      -- calendar months its entries fall in
    first_on         date,
    last_on          date,
    entries          integer NOT NULL,                      -- rows in entries
    withheld_entries integer NOT NULL,                      -- entries in which the release prints a withholding
    locations_flagged integer NOT NULL,                     -- entries whose location is flagged (names a home, street only)
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),   -- its first entry's document
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per record: one meeting or event of a release, as released
CREATE TABLE IF NOT EXISTS ministers_diaries.entries (
    key              text PRIMARY KEY,                      -- the record's `id`
    release          text NOT NULL,                         -- releases.key
    rowid            bigint,                                -- the provider's `rowid`
    minister         text,                                  -- as released
    portfolio        text,                                  -- as released
    entry_on         date,                                  -- the record's `date`
    date_as_released text,
    year             text,
    time             text,                                  -- as released ("9:00 AM - 9:20 AM", "Withheld under OIA")
    meeting          text,                                  -- as released, whole
    attendees        text,                                  -- as released, whole, names as printed
    location         text,                                  -- as released, whole (ruling 102)
    -- the flags a product applies hard limit 15 by, at its own surface (ruling 102), set by the value's shape
    location_names_home     boolean NOT NULL DEFAULT false, -- the release's words name a home or residence
    location_street_only    boolean NOT NULL DEFAULT false, -- a street address with no place of business named
    meeting_names_address   boolean NOT NULL DEFAULT false, -- a street address in the meeting
    attendees_names_address boolean NOT NULL DEFAULT false, -- a street address in the attendees
    withheld         text[] NOT NULL DEFAULT '{}',          -- the fields in which the release prints a withholding
    collected_at     text,                                  -- the provider's `_collected`, as served
    updated_at       text,                                  -- the MCP's
    provider_file    text,                                  -- the provider's `file`: the release PDF as its box holds it (4 November 2026)
    provider_path    text,                                  -- the provider's `path`: the same, relative to its store
    capture_path     text,                                  -- the capture block's `path`, as served
    text_words       integer NOT NULL DEFAULT 0,            -- words in the record's `text` (what the MCP's `measure` counts)
    fields_unread    text[] NOT NULL DEFAULT '{}',          -- any field of the record this lane has no column for
    versions         integer NOT NULL DEFAULT 1,            -- documents held for this record
    seq              bigint,                                -- the MCP's place for the version read
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                         -- `record`: the whole JSON document
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS ministers_diaries_entries_release ON ministers_diaries.entries (release);

-- one row per attendee of an entry, in the order the release prints them (attendees.py: by rules, no model). The
-- separators and the attendees joined in order are the entry's attendees text exactly; an entry whose text is not
-- split (an unbalanced bracket) is in attendees_set_aside with the reason, and has no row here. The entry's flags are
-- not copied: the published view joins them down from the entry.
CREATE TABLE IF NOT EXISTS ministers_diaries.attendees (
    key              text PRIMARY KEY,                      -- the entry's key, '/', the position
    entry            text NOT NULL,                         -- entries.key
    position         integer NOT NULL CHECK (position >= 1),
    attendee         text NOT NULL,                         -- as written, whole (titles kept)
    sep_before       text NOT NULL DEFAULT '',              -- the separator text before it ('' for the first)
    sep_after        text NOT NULL DEFAULT '',              -- a separator left at the end (the last row only)
    kind             text NOT NULL CHECK (kind IN ('person', 'organisation', 'crown', 'group', 'role', 'withheld')),
    folded           text NOT NULL,                         -- titles off, folded as the scans fold a name
    organisation     text,                                  -- the organisation part: "Name (Org)", "Name, Org", a
                                                            -- group's body ("Fonterra staff"), a body's own name
    crown            boolean NOT NULL DEFAULT false,        -- the organisation part is the Crown's own (a ministry,
                                                            -- a department, a Crown agency, a Cabinet committee)
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL,
    UNIQUE (entry, position)
);

-- an entry whose attendees text was not split, and why
CREATE TABLE IF NOT EXISTS ministers_diaries.attendees_set_aside (
    entry   text PRIMARY KEY,
    reason  text NOT NULL
);

-- every document read: each version of each record, and which one the entry is read from
CREATE TABLE IF NOT EXISTS ministers_diaries.files (
    sha256      text PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    record_id   text,
    seq         bigint,
    status      text NOT NULL                               -- read | older version | set aside
);

-- the catch log: one line per item not read (stage, reason)
CREATE TABLE IF NOT EXISTS ministers_diaries.set_aside (
    item    text NOT NULL,
    stage   text NOT NULL,
    reason  text NOT NULL
);

-- the provider's `text` (its own join of every field), as served: never published
CREATE TABLE IF NOT EXISTS ministers_diaries_private.entries (
    key        text PRIMARY KEY,
    text       text
);
