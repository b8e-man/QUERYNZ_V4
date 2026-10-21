-- registers/courts (step 5.4): the court judgments, by caption. Two kinds of table:
--   the reading's (judgments, judgment_parties, paragraphs, files, set_aside, and courts_private.withheld_names):
--     rebuilt from the documents at every load, wiped and refilled in one transaction (load.py);
--   the lane's own records, never wiped: suppression_orders (a ledger a person writes through suppress.py;
--     nothing deletes from it and there is no command that lifts an order), and the capture job's captures,
--     feeds and capture_log.
-- No table here holds an address (hard limit 15). A name a suppression withholds is NULL in judgment_parties and
-- kept only in courts_private.withheld_names, which no published view, export or session login reads (hard limit 16).

-- one row per judgment document read: the caption's facts, never its text
CREATE TABLE IF NOT EXISTS courts.judgments (
    key               text PRIMARY KEY,                -- <document sha256>/judgment
    citation          text,                            -- the neutral citation as printed: [2024] NZSC 161
    court             text,                            -- NZSC | NZCA | NZHC, from the citation
    court_name        text,                            -- as the court line prints it
    registry          text,                            -- the High Court's registry
    case_numbers      text[] NOT NULL DEFAULT '{}',    -- SC 106/2022, CA274/2022, CIV-…, CRI-…: a consolidated appeal has several
    judgment_date     date,
    date_basis        text,                            -- label | running head | delivered
    hearing           text,                            -- the Hearing: label as printed (dates)
    judges            text,                            -- the Court: label, else the heading's OF …
    heading           text,                            -- JUDGMENT, SENTENCING NOTES, …
    caption_shape     text,                            -- between | criminal | matter | none
    outcome           text[] NOT NULL DEFAULT '{}',    -- a closed vocabulary: appeal dismissed, application granted, …
    paragraphs        integer NOT NULL DEFAULT 0,      -- numbered paragraphs found in sequence
    parties           integer NOT NULL DEFAULT 0,
    suppression       boolean NOT NULL,                -- a banner, an order in the text, or an order in the ledger
    suppression_kinds text[] NOT NULL DEFAULT '{}',    -- banner, order in the text, CPA s 203, Family Court Act, until, paragraphs, ledger
    withheld          text,                            -- why its parties' names are withheld; NULL when none is
    status            text NOT NULL,                   -- parsed | partial | unparsed
    missing           text[] NOT NULL DEFAULT '{}',
    unrecognised      integer NOT NULL DEFAULT 0,      -- caption lines no grammar took: a count, never the lines
    notes             text[] NOT NULL DEFAULT '{}',
    source            text NOT NULL,
    source_url        text,
    source_note       text NOT NULL,
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page              integer NOT NULL,
    place             text NOT NULL,
    read_from         text NOT NULL,
    reader            text NOT NULL,
    profile           text NOT NULL,
    profile_version   integer NOT NULL,
    loaded_at         timestamptz NOT NULL DEFAULT now()
);

-- one row per party and role a caption names: a consolidated appeal gives one row per party
CREATE TABLE IF NOT EXISTS courts.judgment_parties (
    key               text PRIMARY KEY,                -- <document sha256>/party/<position>
    judgment          text NOT NULL,                   -- judgments.key
    citation          text,
    position          integer NOT NULL,                -- order in the caption, from 1
    block             integer NOT NULL,                -- BETWEEN = 1, each AND one more
    role              text NOT NULL,                   -- as printed: Appellant, First Respondents, Defendant, Prosecutor
    name              text,                            -- as printed; NULL when withheld
    withheld          boolean NOT NULL,                -- the name is withheld (a suppression); the row and its role stay
    anonymised        boolean NOT NULL,                -- the court printed an initial (W, MR N): kept so, never expanded
    crown             boolean NOT NULL,                -- the Crown or a public prosecutor: no suppression covers it
    confidence        text NOT NULL,                   -- high | low (a wrapped list split or rejoined)
    capacity          text,                            -- "as trustees of …", as printed; NULL when withheld
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page              integer NOT NULL,
    place             text NOT NULL,
    read_from         text NOT NULL,
    reader            text NOT NULL,
    profile           text NOT NULL,
    profile_version   integer NOT NULL,
    loaded_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS judgment_parties_judgment ON courts.judgment_parties (judgment);

-- one row per numbered paragraph, with its page: a citation can say "[2024] NZSC 161 at [45], page 12". No text
CREATE TABLE IF NOT EXISTS courts.paragraphs (
    judgment          text NOT NULL,
    number            integer NOT NULL,
    page              integer NOT NULL,
    document          text NOT NULL,
    PRIMARY KEY (judgment, number)
);

-- one row per document the lane's listing names: what became of it
CREATE TABLE IF NOT EXISTS courts.files (
    document          text NOT NULL,                   -- the listed sha256
    source            text NOT NULL,                   -- courtsofnz.govt.nz | waitangitribunal.govt.nz | capture
    ref               text,                            -- the old estate's ref (court:2026 NZSC 88, waitangi:…)
    url               text,
    profile           text,                            -- the profile recognised, or NULL
    outcome           text NOT NULL,                   -- read | set aside | not held
    pages             integer,
    PRIMARY KEY (document, source)
);

-- the catch log: one line for every item the reading could not take, with the stage and the reason
CREATE TABLE IF NOT EXISTS courts.set_aside (
    item     text NOT NULL,
    stage    text NOT NULL,                            -- capture | recognise | read | parse
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- a name a suppression withholds, and the capacity printed with it: never published, never exported
CREATE TABLE IF NOT EXISTS courts_private.withheld_names (
    key       text PRIMARY KEY,                        -- judgment_parties.key
    name      text NOT NULL,
    capacity  text
);

-- the ledger of suppression orders the lever records (suppress.py): never wiped, never deleted from
CREATE TABLE IF NOT EXISTS courts.suppression_orders (
    order_id    bigserial PRIMARY KEY,
    citation    text,                                  -- every document of the citation
    document    text CHECK (document IS NULL OR document ~ '^[0-9a-f]{64}$'),
    reason      text NOT NULL,                         -- the order and where it is recorded; never a name
    by_whom     text NOT NULL,
    ordered_at  timestamptz NOT NULL DEFAULT now(),
    CHECK (citation IS NOT NULL OR document IS NOT NULL)
);

-- the capture job's record (capture.py): every judgment PDF found, and the document once landed
CREATE TABLE IF NOT EXISTS courts.captures (
    url          text PRIMARY KEY,
    citation     text,
    found_via    text NOT NULL,                        -- rss | listing (an old file that is gone)
    found_at     timestamptz NOT NULL DEFAULT now(),
    document     text CHECK (document IS NULL OR document ~ '^[0-9a-f]{64}$'),
    captured_at  timestamptz
);

-- each RSS feed read: the feed itself is landed (the citation for what it listed)
CREATE TABLE IF NOT EXISTS courts.feeds (
    court     text NOT NULL,
    url       text NOT NULL,
    document  text NOT NULL,
    items     integer NOT NULL,
    read_at   timestamptz NOT NULL DEFAULT now()
);

-- the capture job's catch log
CREATE TABLE IF NOT EXISTS courts.capture_log (
    item     text NOT NULL,
    stage    text NOT NULL,                            -- feed | fetch
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);
