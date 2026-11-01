-- registers/real_estate_authority (track E): what this lane captured, in its own schema, then the reading's tables.
-- No capture table holds a name or an address: the listing's and the abstract's names stay in the landed pages. The
-- reading (2 November 2026) holds the parties' names as the abstract prints them, never an address (hard limit 15).
-- real_estate_authority_private holds nothing.

-- one row per decision the database lists: what the listing said, and the abstract page once it is landed
CREATE TABLE IF NOT EXISTS real_estate_authority.cases (
    case_id        integer PRIMARY KEY,                       -- the database's own case number (abstract.aspx?case=N)
    year           integer NOT NULL,                          -- the year it is listed under (the database's year filter)
    decision_date  date,                                      -- as the listing shows it
    body           text NOT NULL,                             -- the deciding body, as the listing names it
    listing        text NOT NULL CHECK (listing ~ '^[0-9a-f]{64}$'),
    listed_at      timestamptz NOT NULL DEFAULT now(),
    abstract       text CHECK (abstract ~ '^[0-9a-f]{64}$'),  -- the abstract page's sha256 once landed
    captured_at    timestamptz                                -- when the abstract and every PDF it links were landed
);
CREATE INDEX IF NOT EXISTS cases_pending ON real_estate_authority.cases (year, decision_date) WHERE captured_at IS NULL;

-- one row per decision document (PDF) an abstract links
CREATE TABLE IF NOT EXISTS real_estate_authority.documents (
    case_id          integer NOT NULL REFERENCES real_estate_authority.cases (case_id),
    source_url       text NOT NULL,
    complaint_number text,                                    -- from the file name (C62477_Determination.pdf → C62477)
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    captured_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (case_id, source_url)
);

-- one row per listing page read: the source's own count for the year (check.py) and the page's hash
CREATE TABLE IF NOT EXISTS real_estate_authority.listings (
    year       integer NOT NULL,
    page       integer NOT NULL,
    num_found  integer NOT NULL,                              -- "Search Results (N)" for the year, when read
    pages      integer NOT NULL,
    listing    text NOT NULL CHECK (listing ~ '^[0-9a-f]{64}$'),
    url        text NOT NULL,
    read_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (year, page, read_at)
);

-- the catch log: one line for every item the lane could not take, with the stage and the reason
CREATE TABLE IF NOT EXISTS real_estate_authority.set_aside (
    item     text NOT NULL,                                   -- a case number, a year/page, or a URL
    stage    text NOT NULL,                                   -- listing | abstract | pdf | fetch
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- ── the reading (read.py, 2 November 2026): rebuilt whole on every load from the landed abstracts; regenerable ──

-- one row per decision: what its abstract states, never the reasoning text, never the complainant, never an address
CREATE TABLE IF NOT EXISTS real_estate_authority.decisions (
    key                   text PRIMARY KEY,                   -- real_estate_authority/<case_id>
    case_id               integer NOT NULL,
    complaint_number      text,
    listed_body           text,                               -- the deciding body as the listing names it
    decided_by            text,                               -- as the abstract's heading names it
    appeal                boolean NOT NULL,
    citation              text,                               -- "[2024] NZREADT 47" where printed
    decided_on            date,
    year                  integer,
    decision              text,                               -- the finding: Unsatisfactory Conduct, No Further Action …
    decision_note         text,
    penalty               text,                               -- as printed; NULL where a suppression order stands
    penalty_kinds         text[] NOT NULL,
    penalty_names_address boolean NOT NULL,                   -- ruling 102: a flag beside the text, never the address cut out
    complaint_type        text,
    transaction_type      text,
    chairperson           text,
    charge                text,
    act_sections          text[] NOT NULL,
    code_sections         text[] NOT NULL,
    history               jsonb NOT NULL,                     -- [{on, step, pdfs}]
    parties_named         integer NOT NULL,
    suppressed            boolean NOT NULL,
    abstract_url          text NOT NULL,
    document              text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                  integer,
    place                 text NOT NULL,
    read_from             text NOT NULL,
    reader                text NOT NULL,
    profile               text NOT NULL,
    profile_version       integer NOT NULL,
    loaded_at             timestamptz NOT NULL DEFAULT now()
);

-- one row per licensee, agency or defendant a decision names; a suppressed decision's names and numbers are NULL
CREATE TABLE IF NOT EXISTS real_estate_authority.parties (
    key              text PRIMARY KEY,                        -- <decision key>/party/<n>
    decision_key     text NOT NULL,
    case_id          integer NOT NULL,
    seq              integer NOT NULL,
    name             text,
    licence_number   text,
    kind             text NOT NULL CHECK (kind IN ('person', 'agency', 'organisation')),
    role             text NOT NULL CHECK (role IN ('licensee', 'defendant')),
    suppressed       boolean NOT NULL,
    decided_on       date,
    decision         text,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- the reading's catch log: an abstract the reader could not take, with the reason
CREATE TABLE IF NOT EXISTS real_estate_authority.read_set_aside (
    document  text NOT NULL,
    place     text NOT NULL,
    stage     text NOT NULL,
    reason    text NOT NULL,
    at        timestamptz NOT NULL DEFAULT now()
);
