-- registers/hansard: every table this lane owns, in `hansard`. Every row is read from the once-only export of the old
-- estate's Hansard tables (capture.py, ruling 96), "taken from the old estate's tables; original not held", and cites
-- the export's hash, the sitting day and section, and the page's own address. Rebuilt whole on every load.
-- `hansard_private` holds nothing: no row of this source is a home address.

CREATE SCHEMA IF NOT EXISTS hansard;
CREATE SCHEMA IF NOT EXISTS hansard_private;

-- one per sitting day: the sitting row's own counts as the old estate derived them, and the same counts made again
-- from the sections (check.py compares the two)
CREATE TABLE IF NOT EXISTS hansard.sittings (
    key              text PRIMARY KEY,               -- the sitting day, YYYY-MM-DD
    sitting_on       date NOT NULL,
    parliament       integer,
    volume           integer,
    progress         text,                           -- 'Draft' or 'Corrected', as the page said when captured
    url              text,                           -- the day's transcript page
    sections         integer NOT NULL,               -- counted from the sections held
    turns            integer NOT NULL,               -- every speech turn in the day's speaker lists
    attributed       integer NOT NULL,               -- turns that carry Parliament's member id
    unattributed     integer NOT NULL,               -- turns that carry only a role
    speakers         integer NOT NULL,               -- distinct member ids
    old_sections     integer,                        -- the old sitting row's own figures
    old_speeches     integer,
    old_unattributed integer,
    old_speakers     integer,
    old_derived_at   timestamptz,
    source_note      text NOT NULL,
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- one per section of a sitting day's transcript, with its text
CREATE TABLE IF NOT EXISTS hansard.sections (
    key              text PRIMARY KEY,               -- <sitting day>/<section index>
    sitting_on       date NOT NULL,
    section_index    integer NOT NULL,
    parliament       integer,
    volume           integer,
    proceeding       text,
    subject          text,
    bill_title       text,
    bill_id          text,
    progress         text,
    old_status       text,                           -- the old pipeline's own state (captured, processed, failed)
    text             text NOT NULL,                  -- as captured; '' where the old estate held none
    chars            integer NOT NULL,
    text_sha1        text NOT NULL,                  -- the old body_hash, checked against the text at the read
    turns            integer NOT NULL,
    url              text NOT NULL,
    captured_at      timestamptz,                    -- when the old estate fetched the page
    old_id           text,
    source_note      text NOT NULL,
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- one per entry of a section's speaker list, in its printed order: the label as the old capture read it off the page,
-- and the member id and roster name it carried. No name is matched here; check.py measures the match to pub.members
CREATE TABLE IF NOT EXISTS hansard.turns (
    key              text PRIMARY KEY,               -- <sitting day>/<section index>/<ordinal>
    section          text NOT NULL,                  -- hansard.sections.key
    sitting_on       date NOT NULL,
    section_index    integer NOT NULL,
    ordinal          integer NOT NULL,               -- from 1
    label            text,                           -- as the old capture read it ('Hon BARBARA EDMONDS', 'SPEAKER')
    member_id        text,                           -- Parliament's id for the member, as captured; null for a role
    roster_name      text,                           -- the old roster's name for that id ('Edmonds, Hon Barbara')
    role             text,                           -- the old capture's role where no member is named
    in_roster        boolean NOT NULL,               -- the member id is in hansard.members
    source_note      text NOT NULL,
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- the old estate's roster of members, by Parliament's id
CREATE TABLE IF NOT EXISTS hansard.members (
    key              text PRIMARY KEY,               -- Parliament's member id
    display_name     text,
    sort_name        text,
    parliaments      integer[],
    source_note      text NOT NULL,
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- the old estate's own derivation, one per sitting, section and member: never published, kept so the check can count
-- the turns again against it. A retired row is one the old derive no longer made
CREATE TABLE IF NOT EXISTS hansard.old_speeches (
    key              text PRIMARY KEY,               -- the old row's id
    sitting_on       date NOT NULL,
    section_index    integer NOT NULL,
    member_id        text,
    speaker_label    text,
    speaker_name     text,
    speech_count     integer,
    retired_at       timestamptz,
    document         text NOT NULL
);

-- room for the MCP's `parliament-hansard-index` (session hansard-2, after mcp-1): one row per index record, which
-- Hansard page changed and when; it carries no text. Joined to the sittings by url. Empty until hansard-2 fills it
CREATE TABLE IF NOT EXISTS hansard.index_pages (
    url              text NOT NULL,
    lastmod          timestamptz,                    -- the sitemap's own last-modified
    fetched          timestamptz,                    -- when the MCP fetched the sitemap
    index_on         date,                           -- the index record's date
    record           text,                           -- the MCP's record id
    document         text NOT NULL,                  -- the record landed by sha256
    loaded_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (url, document)
);

CREATE TABLE IF NOT EXISTS hansard.files (
    sha256           text PRIMARY KEY,
    name             text NOT NULL,
    kind             text NOT NULL,
    status           text NOT NULL
);

-- the catch log: one line per item not read, with the stage and the reason
CREATE TABLE IF NOT EXISTS hansard.set_aside (
    item             text NOT NULL,
    stage            text NOT NULL,
    reason           text NOT NULL
);
