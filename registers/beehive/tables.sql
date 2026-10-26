-- registers/beehive: the tables this lane owns, in `beehive` and `beehive_private`.
-- Loaded into a staging or scratch schema by replacing `beehive.` (and `beehive_private.`) with that schema's
-- name (load.sql). Every row is read from one document: a record of the ingest MCP's `beehive` corpus, landed
-- whole by support/mcpsource (rulings 78, 94, 96). The estate never fetched beehive.govt.nz: Arthur's provider
-- captured and read it off-estate. A record served changed is a second document; a release is read from its
-- newest (the highest `seq`), and every version is in `files`.

-- one row per release, speech or feature: the MCP's fields as columns. A page the MCP does not hold and the
-- old estate's scraper did (its export, capture.OLD_EXPORT_SHA) is a row of origin "old estate"
CREATE TABLE IF NOT EXISTS beehive.releases (
    key              text PRIMARY KEY,                      -- the record's `id` (the page's address)
    url              text NOT NULL,                         -- the record's `url`: the citation
    type             text,                                  -- release | speech | feature | page, as the site types it
    -- the provider's own record of its capture (the `capture` block, or the same fields at the top level)
    final_url        text,                                  -- where the page answered from
    http_status      integer,
    kind             text,                                  -- the capture's kind
    captured_sha256  text,                                  -- the provider's hash of the page as it received it
    captured_at      text,                                  -- when the provider fetched it, as served
    capture_status   text,
    provider_file    text,                                  -- the provider's `source_file`, a name on its box
    provider_path    text,                                  -- the provider's `path`, a name on its box
    -- the provider's model (off-estate) and what it made
    model            text,
    extracted_at     text,
    annotation_fields      text[] NOT NULL DEFAULT '{}',    -- the fields the record names as model-made
    annotation_generator   text,
    annotation_created_at  text,
    updated_at       text,                                  -- the MCP's: moves when the record changes
    title            text,                                  -- NULL where the record's title is empty
    published_at     text,                                  -- as served (ISO, `Z`); never re-zoned
    published_on     date,                                  -- the record's `date`
    word_count       integer,                               -- the record's own count of its body's words
    ministers        integer NOT NULL DEFAULT 0,            -- rows in release_ministers
    portfolios       text[] NOT NULL DEFAULT '{}',          -- as the site tags it, in order
    topics           integer NOT NULL DEFAULT 0,            -- rows in release_topics (model-made by the source)
    quotes           integer NOT NULL DEFAULT 0,            -- rows in release_quotes (model-made by the source)
    fields_unread    text[] NOT NULL DEFAULT '{}',          -- any field of the record this lane has no column for
    versions         integer NOT NULL DEFAULT 1,            -- documents held for this record
    seq              bigint,                                -- the MCP's place for the version read (NULL: no arrival row)
    origin           text NOT NULL CHECK (origin IN ('mcp', 'old estate')),
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

-- one row per minister the site tags a release with, in order
CREATE TABLE IF NOT EXISTS beehive.release_ministers (
    key              text PRIMARY KEY,                      -- <release key>#minister/<n>
    release          text NOT NULL,
    ordinal          integer NOT NULL,
    name             text NOT NULL,                         -- as tagged (`name`)
    slug             text,                                  -- the site's own minister slug
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                         -- ministers[<n>]
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per portfolio the site tags a release with, in order
CREATE TABLE IF NOT EXISTS beehive.release_portfolios (
    key              text PRIMARY KEY,                      -- <release key>#portfolio/<n>
    release          text NOT NULL,
    ordinal          integer NOT NULL,
    portfolio        text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- the source's own annotation: topics and quotes the provider's model made on its box, outside the estate.
-- Kept and shown as theirs; never read into a claim or a link (ruling 96)
CREATE TABLE IF NOT EXISTS beehive.release_topics (
    key              text PRIMARY KEY,                      -- <release key>#topic/<n>
    release          text NOT NULL,
    ordinal          integer NOT NULL,
    topic            text NOT NULL,
    model_made       boolean NOT NULL DEFAULT true CHECK (model_made),
    made_by          text NOT NULL,                         -- whose model: the source's, off-estate
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS beehive.release_quotes (
    key              text PRIMARY KEY,                      -- <release key>#quote/<n>
    release          text NOT NULL,
    ordinal          integer NOT NULL,
    quote            text NOT NULL,                         -- the quote as the source's model cut it
    speaker          text,                                  -- as the source's model named them
    model_made       boolean NOT NULL DEFAULT true CHECK (model_made),
    made_by          text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- every document read: each version of each record, and which one the release is read from
CREATE TABLE IF NOT EXISTS beehive.files (
    sha256      text PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    record_id   text,
    seq         bigint,                                     -- the newest place the MCP served these bytes at
    status      text NOT NULL                              -- read | older version | set aside
);

-- the catch log: one line per item not read (stage, reason)
CREATE TABLE IF NOT EXISTS beehive.set_aside (
    item    text NOT NULL,
    stage   text NOT NULL,
    reason  text NOT NULL
);

-- a release's text as served: never published (a page may print a person's details; the board opens the
-- document whole, ruling 88)
CREATE TABLE IF NOT EXISTS beehive_private.texts (
    key        text PRIMARY KEY,
    body_text  text,                                        -- the record's `body_text`
    text       text                                         -- the record's `text` (title and body as the provider joined them)
);
