-- registers/real_estate_authority (track E): what this lane captured, in its own schema. Capture and hold: the
-- reading comes in step 5. No table here holds a name or an address: the listing's and the abstract's names stay
-- in the landed pages in the document store. real_estate_authority_private holds nothing yet; an address, if a
-- reader ever extracts one, goes there (hard limit 15).

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
