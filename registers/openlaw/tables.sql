-- registers/openlaw: every table the lane owns. Two parts: the capture's record (never wiped; capture.py makes it)
-- and, below the marker, the reading's tables (dropped and rebuilt by load.py at every load). A party's name sits in
-- `openlaw_private.party_names` and a case's title in `openlaw_private.case_titles`, so the session reader never sees
-- a suppressed one; the views show a name only where the party is not withheld, a title only where the case carries no
-- suppression marker (hard limit 16). No table holds an address.

CREATE SCHEMA IF NOT EXISTS openlaw;
CREATE SCHEMA IF NOT EXISTS openlaw_private;

-- one walk of the interface's cases, newest first, paged by offset
CREATE TABLE IF NOT EXISTS openlaw.capture_passes (
    pass_id      bigserial PRIMARY KEY,
    mode         text NOT NULL,                 -- 'sample' (the first night's) or 'full'
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz,
    next_offset  integer NOT NULL DEFAULT 0,    -- where the pass resumes
    pages        integer NOT NULL DEFAULT 0,
    cases_landed integer NOT NULL DEFAULT 0,
    target       integer,                       -- the cases the pass stops at (the sample's 2,000), or NULL
    probed_total integer,                       -- the interface's own figure, probed by offset at the pass's start
    set_aside    integer NOT NULL DEFAULT 0
);

-- the listing: one row per page landed, by hash
CREATE TABLE IF NOT EXISTS openlaw.capture_pages (
    pass_id    bigint NOT NULL REFERENCES openlaw.capture_passes,
    page_no    integer NOT NULL,
    page_offset integer NOT NULL,
    url        text NOT NULL,
    sha256     text NOT NULL,
    cases      integer NOT NULL,
    ids        text[] NOT NULL,         -- the interface's ids of the page's cases, in its order
    new        boolean NOT NULL,
    landed_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (pass_id, page_no)
);

-- the catch log of the capture: one line per item it could not process
CREATE TABLE IF NOT EXISTS openlaw.capture_set_aside (
    pass_id  bigint,
    item     text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
CREATE TABLE openlaw.read_pages (
    document   text PRIMARY KEY,
    cases      integer NOT NULL,       -- records on the page
    typed      integer NOT NULL,       -- read into a case row
    set_aside  integer NOT NULL,       -- in the catch log
    superseded integer NOT NULL,       -- read again from a later page
    skipped    integer NOT NULL        -- cases - typed - set_aside - superseded: 0 on a full load
);

CREATE TABLE openlaw.cases (
    key               text PRIMARY KEY,   -- the interface's own id (a stable string)
    openlaw_id        text NOT NULL,
    citation          text,               -- the neutral citation, [YYYY] NZXX N, where the record carries one
    citations         text[] NOT NULL,    -- every citation the record carries, as written
    court             text,               -- the court's acronym as the interface names it
    court_name        text,
    registry          text,               -- the registry as the record names it (the interface's `location`, else the caption)
    filing_number     text,
    decided_on        date,               -- caseDate as filed
    pdf_url           text,
    suppressed        boolean NOT NULL,   -- a suppression or anonymisation marker in the text or the title
    suppression_marks text[] NOT NULL,    -- which markers fired (their names, never the text around them)
    parties_from      text NOT NULL,      -- 'interface', 'caption' or 'none'
    is_valid          boolean,
    source_modified_at date,
    parsers_version   text,
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL,
    reader text NOT NULL, profile text NOT NULL, profile_version integer NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE openlaw.parties (
    key          text PRIMARY KEY,        -- case key | role | position
    case_key     text NOT NULL,
    role         text NOT NULL,           -- APPLICANT, PLAINTIFF, APPELLANT, RESPONDENT, DEFENDANT, or the caption's role
    position     integer NOT NULL,        -- order within the record
    anonymised   boolean NOT NULL,        -- the court rendered the name as an initial or a pseudonym; never expanded
    crown        boolean NOT NULL,        -- the Crown or a public prosecutor (R, the King, Police, …): shown even when suppressed
    withheld     boolean NOT NULL,        -- the name is not shown on any surface: the case is suppressed and the party is not the Crown
    from_source  text NOT NULL,           -- 'interface' or 'caption'
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL,
    reader text NOT NULL, profile text NOT NULL, profile_version integer NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE openlaw_private.party_names (
    key   text PRIMARY KEY,               -- the party row's key
    name  text NOT NULL
);

-- the case's title (caseName) as filed: it carries the parties' names, so it sits beside them
CREATE TABLE openlaw_private.case_titles (
    key   text PRIMARY KEY,               -- the case row's key
    title text NOT NULL
);

CREATE TABLE openlaw.citations (
    key            text PRIMARY KEY,      -- citing | cited
    citing_key     text NOT NULL,
    cited_key      text NOT NULL,         -- the interface's id of the cited case (held or not)
    citation_count bigint,
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL,
    reader text NOT NULL, profile text NOT NULL, profile_version integer NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE openlaw.statutes (
    key                   text PRIMARY KEY,   -- case | legislation id | section
    case_key              text NOT NULL,
    legislation_id        text NOT NULL,
    legislation_title     text,
    legislation_year      text,
    section               text NOT NULL,
    mentions              bigint,
    extraction_confidence integer,
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL,
    reader text NOT NULL, profile text NOT NULL, profile_version integer NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE openlaw.read_set_aside (
    document text NOT NULL,
    place    text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL
);
