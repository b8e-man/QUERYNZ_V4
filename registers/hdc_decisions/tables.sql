-- registers/hdc_decisions: every table this lane owns, in `hdc_decisions` and its private twin, in two parts. The
-- capture's record (capture.py makes it; never wiped): no capture table holds a row of the source, and no heading
-- (a tile's heading describes the consumer's care, so only its hash is kept in the fingerprint); the pages stay in the
-- document store verbatim by sha256. The reading's tables (load.py drops and makes them again at every load). No
-- consumer, family member or anonymised person is read; an individual practitioner is kept as a role.

-- ── the capture ──────────────────────────────────────────────────────────────

-- one row per pass over a listing (a year's decisions, or the case studies): the pages it states and how far it got
CREATE TABLE IF NOT EXISTS hdc_decisions.capture_passes (
    pass_id      bigserial PRIMARY KEY,
    list         text NOT NULL,                     -- decisions-2017 … decisions-<year>, case-studies
    stated       integer,                           -- "Page 1 of N": the listing's own count of its pages
    next_page    integer NOT NULL DEFAULT 1,        -- the pass resumes from this page
    pages        integer NOT NULL DEFAULT 0,
    items        integer NOT NULL DEFAULT 0,
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz
);

-- the listing pages landed, with their hashes and how many tiles each carried
CREATE TABLE IF NOT EXISTS hdc_decisions.capture_pages (
    pass_id   bigint NOT NULL REFERENCES hdc_decisions.capture_passes (pass_id),
    page_no   integer NOT NULL,
    url       text NOT NULL,
    sha256    text NOT NULL,
    items     integer NOT NULL,
    PRIMARY KEY (pass_id, page_no)
);

-- what each pass listed: the entry's slug, address, the tile's date and its fingerprint (the date and a hash of the
-- heading)
CREATE TABLE IF NOT EXISTS hdc_decisions.capture_listed (
    pass_id    bigint NOT NULL REFERENCES hdc_decisions.capture_passes (pass_id),
    list       text NOT NULL,
    slug       text NOT NULL,
    url        text NOT NULL,
    card       text NOT NULL,
    listed_on  date,
    ordinal    integer NOT NULL,
    PRIMARY KEY (pass_id, slug)
);

-- the entries landed: one row per fetch, so an entry fetched again (its tile changed) keeps its older hash too
CREATE TABLE IF NOT EXISTS hdc_decisions.capture_items (
    list      text NOT NULL,
    slug      text NOT NULL,
    url       text NOT NULL,
    card      text NOT NULL,
    sha256    text NOT NULL,
    at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (list, slug, sha256)
);

-- the documents about the source (copyright, terms, privacy statement, the naming policy and its PDF)
CREATE TABLE IF NOT EXISTS hdc_decisions.capture_docs (
    name      text NOT NULL,
    url       text NOT NULL,
    sha256    text NOT NULL,
    new       boolean NOT NULL,
    at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hdc_decisions.capture_set_aside (
    pass_id  bigint,
    item     text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
-- load.py drops these and makes them again at every load. Each row cites the page's sha256, page 1, its place, the
-- reader and the profile.

-- the ledger: one row per entry the newest finished pass of each listing lists, dated from 2017; items in = read +
-- set aside + not captured
CREATE TABLE IF NOT EXISTS hdc_decisions.read_items (
    list       text NOT NULL,
    slug       text NOT NULL,
    pass_id    bigint,
    document   text,                                -- NULL: listed and not yet captured
    state      text NOT NULL CHECK (state IN ('read', 'set aside', 'not captured')),
    providers  integer NOT NULL DEFAULT 0,
    PRIMARY KEY (list, slug)
);

CREATE TABLE IF NOT EXISTS hdc_decisions.decisions (
    key                      text PRIMARY KEY,      -- hdc_decisions/decision/<slug>; a case study's from its slug's hash
    slug                     text,                  -- the page's own address segment; NULL where it describes the case
    kind_of_page             text NOT NULL,         -- 'decision' or 'case study'
    case_number              text,                  -- the Commissioner's file number, 22HDC00991
    case_numbers             text[] NOT NULL,       -- every file number the address carries (a joint decision)
    web_id                   text,                  -- CAS-13928-S0F4B9, where the page carries one
    decided_on               date NOT NULL,         -- the page's own date
    kind                     text NOT NULL,         -- the gravest finding stated, 'case study', or 'not stated'
    findings                 text[] NOT NULL,       -- 'Ultimate Care Oakland — breach', 'Registrar — adverse comment'
    provider_kinds           text[] NOT NULL,       -- as the Commissioner classifies them (the page's Group providers)
    occupations              text[] NOT NULL,       -- the page's Occupations
    rights_tagged            text[] NOT NULL,       -- the Code rights the Commissioner tags the page with
    rights_breached          text[] NOT NULL,       -- the Code rights the page states were breached
    recommendation_headings  text[] NOT NULL,       -- as stated
    recommended_to           text[] NOT NULL,       -- a named provider, 'an unnamed <kind>', or a role
    named_roles              text[] NOT NULL,       -- an individual the Commissioner names, as a role only
    naming_grounds           text[] NOT NULL,       -- beside each named role: the naming policy's ground the page states
    names_removed            boolean NOT NULL,      -- the page carries the Commissioner's notice that names are removed
    providers_named          integer NOT NULL,
    url                      text,                  -- the page's address; NULL where it describes the case (private twin)
    document                 text NOT NULL,
    page                     integer NOT NULL,
    place                    text NOT NULL,
    read_from                text NOT NULL,
    reader                   text NOT NULL,
    profile                  text NOT NULL,
    profile_version          integer NOT NULL,
    loaded_at                timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hdc_decisions.providers (
    key              text PRIMARY KEY,              -- <decision key>/provider/<n>
    decision_key     text NOT NULL,
    ordinal          integer NOT NULL,
    name             text NOT NULL,                 -- as the Commissioner names it
    abbreviation     text,                          -- as the page defines it
    also_called      text[] NOT NULL,               -- other forms the page names it by (the notice's, a trading name)
    found_by         text[] NOT NULL,               -- where on the page it is named
    findings         text[] NOT NULL,               -- its findings, as headed
    rights_breached  text[] NOT NULL,               -- the rights the page says it breached
    recommended      boolean NOT NULL,              -- a recommendation is addressed to it
    company_number   text,                          -- only where the page prints one beside the name; never looked up
    charity_number   text,                          -- likewise
    decided_on       date NOT NULL,
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hdc_decisions.read_set_aside (
    document  text,
    place     text NOT NULL,
    stage     text NOT NULL,
    reason    text NOT NULL                         -- names the field and the kind of detail, never the value
);

-- the page address where it describes the case (a case study's slug is its summary): kept for the lane, never published
CREATE TABLE IF NOT EXISTS hdc_decisions_private.page_addresses (
    key       text PRIMARY KEY,
    slug      text NOT NULL,
    url       text NOT NULL,
    document  text NOT NULL
);
