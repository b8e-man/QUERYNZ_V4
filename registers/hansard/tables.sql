-- registers/hansard: every table this lane owns, in `hansard`. Every row is read from the once-only export of the old
-- estate's Hansard tables (capture.py, ruling 96), "taken from the old estate's tables; original not held", and cites
-- the export's hash, the sitting day and section, and the page's own address. Rebuilt whole on every load.
-- The MCP's rows (hansard-2) read the records support/mcpsource landed and cite the record's hash and the page's or
-- PDF's address. `hansard_private` holds each day's text as the provider's pdftotext gave it: shown on the board only.
-- hansard-3: the split of each day's text into sections and turns (day_sections, day_turns), and the text reader's
-- names (readings, people), by profile hansard-day.

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
    captured_at      timestamptz,                    -- the latest the old estate fetched any of the day's sections
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

-- one per page of the MCP's `parliament-hansard-index` (a sitemap entry: which page changed and when; no text), read
-- from the version the pull saw last. Joined to the sittings by url in pub.hansard_sittings
CREATE TABLE IF NOT EXISTS hansard.index_pages (
    url              text NOT NULL,
    lastmod          timestamptz,                    -- the sitemap's own last-modified
    fetched          timestamptz,                    -- when the provider fetched the sitemap entry
    index_on         date,                           -- the record's `date`
    record           text,                           -- the MCP's record id
    raw_file         text,                           -- the provider's file name on its box
    versions         integer NOT NULL,               -- documents the MCP has served for this record
    fields_unread    text[] NOT NULL DEFAULT '{}',   -- any field of the record this lane has no column for
    source_note      text NOT NULL,
    document         text NOT NULL,                  -- the record landed by sha256
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (url, document)
);

-- one per record of the MCP's `parliament-hansard-debates`: a sitting day's daily PDF, read by the provider with
-- pdftotext -layout. No section or speech split (the provider made none). The text is in hansard_private.day_texts
CREATE TABLE IF NOT EXISTS hansard.days (
    key              text PRIMARY KEY,               -- the sitting day, YYYY-MM-DD
    sitting_on       date NOT NULL,
    title            text,
    pdf_url          text NOT NULL,                  -- the daily PDF's address: the citation
    pdf_sha256       text,                           -- the provider's hash of the PDF as it received it
    pdf_bytes        bigint,
    http_status      integer,
    captured_at      timestamptz,                    -- when the provider fetched the PDF
    raw_file         text,                           -- the provider's file name on its box
    updated_at       text,                           -- the MCP's: moves when the record changes
    page_count       integer,
    word_count       integer,                        -- as served
    text_words       integer NOT NULL,               -- whitespace words of the text (what the MCP's `measure` counts)
    chars            integer NOT NULL,
    versions         integer NOT NULL,
    fields_unread    text[] NOT NULL DEFAULT '{}',
    old_sections     integer,                        -- the old transcript's sections for the day; NULL: not held there
    old_subjects     integer,                        -- of those, with a subject that is not a continuation note
    subjects_in_text integer,                        -- of those, the subject found in this day's text
    layout           text,                           -- the split's layout: final | draft; NULL where it could not split
    parliament       integer,                        -- from the cover, else by the election before the day
    sections         integer,                        -- the split's counts (hansard-3): sections, speaker turns, turns
    turns            integer,                        --   with a member id, turns with none, distinct member ids
    attributed       integer,
    unattributed     integer,
    speakers         integer,
    split_rule       text,                           -- split.RULE
    reading          text NOT NULL DEFAULT 'waiting: text reader',   -- read | waiting: text reader | set aside: <why>
    pieces           integer,                        -- the joined reading's pieces, names, unusable pieces
    names            integer,
    unusable_pieces  integer,
    source_note      text NOT NULL,
    document         text NOT NULL,                  -- the record landed by sha256
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- one per old section on a day both sources hold: where its subject is found. No text; check.py reads it under
-- the reader login (the texts are private)
CREATE TABLE IF NOT EXISTS hansard.day_subjects (
    key              text PRIMARY KEY,               -- hansard.sections.key
    sitting_on       date NOT NULL,
    found            text NOT NULL CHECK (found IN ('own day', 'neighbouring day', 'continuation note',
                                                     'no subject', 'not found')),
    neighbour        date,                           -- the held day whose text has it, for 'neighbouring day'
    document         text NOT NULL                   -- the day's record
);

-- one per section of a day's text as the split rule of profile hansard-day cut it (split.py): the heading run, the
-- proceeding, subject and bill it names, and its counts. No text: the reader re-splits the landed record
CREATE TABLE IF NOT EXISTS hansard.day_sections (
    key              text PRIMARY KEY,               -- <sitting day>/<section index>
    sitting_on       date NOT NULL,
    section_index    integer NOT NULL,               -- from 0
    layout           text NOT NULL,
    heading          text,                           -- the heading lines as printed, ' / ' between
    proceeding       text,
    subject          text,
    bill_title       text,
    chars            integer NOT NULL,
    turns            integer NOT NULL,
    attributed       integer NOT NULL,
    unattributed     integer NOT NULL,
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

-- one per speaker turn the split found: the speaker line as printed, its brackets read, the member matched to the
-- old roster within the day's Parliament, or only a role. Published for the days the old transcript does not hold
CREATE TABLE IF NOT EXISTS hansard.day_turns (
    key              text PRIMARY KEY,               -- <sitting day>/<section index>/<ordinal>
    section          text NOT NULL,                  -- hansard.day_sections.key
    sitting_on       date NOT NULL,
    section_index    integer NOT NULL,
    ordinal          integer NOT NULL,               -- from 1
    label            text NOT NULL,                  -- the speaker as printed: 'Hon CHRIS BISHOP', 'CHAIRPERSON'
    name             text,                           -- the person named: the label, or the chair's name in brackets
    role_text        text,                           -- the brackets: 'Leader of the House', 'Labour—Mana'
    party            text,
    electorate       text,
    role             text,                           -- Speaker, Deputy Speaker, Assistant Speaker, Chairperson, Clerk, Member (unattributed)
    first_speech     boolean NOT NULL,               -- the name was printed in capitals
    member_id        text,                           -- Parliament's id, from the old roster
    roster_name      text,
    match_basis      text,                           -- full | given | surname; NULL when not matched
    in_roster        boolean NOT NULL,
    chars            integer NOT NULL,
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
CREATE INDEX IF NOT EXISTS day_turns_member ON hansard.day_turns (member_id);
CREATE INDEX IF NOT EXISTS day_turns_day ON hansard.day_turns (sitting_on);

-- one per piece of a day's joined text-reader reading (model_read.py): its summary and counts
CREATE TABLE IF NOT EXISTS hansard.readings (
    key              text PRIMARY KEY,               -- <document sha256>/piece/<p>
    day              text NOT NULL,                  -- hansard.days.key
    sitting_on       date NOT NULL,
    piece            integer NOT NULL,
    section          text,                           -- hansard.day_sections.key
    part             integer,
    parts            integer,
    chars            integer,
    turns            integer,
    names            integer NOT NULL,
    summary          text,
    truncated        boolean NOT NULL,
    unusable         text,
    model            text NOT NULL,
    reader           text NOT NULL,
    made_at          text,
    document         text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- one per person or body a speech names, as the text reader read it (the common rules of 31 October 2026): the
-- rows the links lane reads through pub.hansard_people. Never a link, never a claim; from stored readings only
CREATE TABLE IF NOT EXISTS hansard.people (
    key              text PRIMARY KEY,               -- <document sha256>/person/<n>
    name             text NOT NULL,                  -- as printed
    kind             text NOT NULL,                  -- person | company | agency | body | other
    role             text,                           -- the role as the text says it
    role_text        text,
    "of"             text,                           -- the organisation a person is of, where the text says
    day              text NOT NULL,                  -- the document's own key: hansard.days.key
    sitting_on       date NOT NULL,
    section          text,                           -- the piece's section: hansard.day_sections.key
    piece            integer NOT NULL,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL,
    place            text NOT NULL,                  -- 'text reader, piece p, name n'
    read_from        text NOT NULL,
    reader           text NOT NULL,
    model            text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS people_day ON hansard.people (day);
CREATE INDEX IF NOT EXISTS people_name ON hansard.people (upper(name));

CREATE TABLE IF NOT EXISTS hansard_private.day_texts (
    key              text PRIMARY KEY,               -- hansard.days.key
    text             text NOT NULL
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
