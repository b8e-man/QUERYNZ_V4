-- registers/mp_interests: the tables this lane owns, in its own schema and its private twin. Loaded into a staging or
-- scratch schema by replacing `mp_interests.` with that schema's name (in the shared scratch schema,
-- `<schema>.mp_interests_<table>`, and `<schema>_private.mp_interests_<table>` for the twin).

-- every edition the lane holds: its hash, the year in its file name, where the old estate kept it
CREATE TABLE IF NOT EXISTS mp_interests.files (
    document     text PRIMARY KEY CHECK (document ~ '^[0-9a-f]{64}$'),
    year_label   integer,
    old_path     text NOT NULL,
    captured_at  text
);

-- the catch log: one line for every item the lane could not take to a published row, with the stage and the
-- reason (capture | edition | page | line | verbatim)
CREATE TABLE IF NOT EXISTS mp_interests.set_aside (
    item     text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- one edition: its date as printed on its title page and its own list of categories
CREATE TABLE IF NOT EXISTS mp_interests.editions (
    key              text PRIMARY KEY,               -- the document's sha256
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL,
    place            text NOT NULL,
    year_label       integer,
    as_at            date,
    as_at_printed    text,
    categories       text NOT NULL,                  -- the introduction's list: "<n> <heading> [<category>]" | …
    members          integer NOT NULL,
    declarations     integer NOT NULL,
    wrapped          integer NOT NULL,               -- declarations joined across a wrapped line
    annex_page       integer,                        -- where the reprinted rules begin (not read)
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    read_from        text NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one member's return in one edition
CREATE TABLE IF NOT EXISTS mp_interests.members (
    key              text PRIMARY KEY,               -- <sha256>/p<page>/l<line> of the header
    edition          text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL,
    place            text NOT NULL,
    as_at            date,
    printed          text NOT NULL,                  -- the header as printed
    member           text NOT NULL,                  -- the name as printed
    name             text,                           -- given-first, honorifics off (keys.names)
    party_label      text,                           -- as printed; NULL where the header states none
    party            text,                           -- the registered party (keys.parties); NULL when unresolved
    party_basis      text NOT NULL,
    electorate       text,                           -- as printed ("List" for a list member)
    statement        text,                           -- printed in place of declarations ("No interests declared …")
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    read_from        text NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one declaration, keyed by its place; filed by its heading, the number kept as printed beside it
CREATE TABLE IF NOT EXISTS mp_interests.declarations (
    key              text PRIMARY KEY,               -- <sha256>/p<page>/l<line>
    edition          text NOT NULL,
    member           text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL,
    place            text NOT NULL,
    as_at            date,
    number_printed   text NOT NULL,                  -- an attribute only: the register renumbered in 2018
    heading          text NOT NULL,                  -- as printed
    category         text NOT NULL,                  -- the slug for the heading (parse.HEADINGS)
    text             text,                           -- verbatim; NULL where withheld
    withheld         boolean NOT NULL,               -- the text is held in the private twin (real property)
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    read_from        text NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- each number the edition uses: its introduction's heading against the headings its returns print (the outside check)
CREATE TABLE IF NOT EXISTS mp_interests.numbering (
    edition         text NOT NULL,
    number          integer NOT NULL,
    intro_heading   text,
    intro_category  text,
    body_headings   text,
    body_category   text,
    agrees          boolean NOT NULL
);

-- the text of a declaration that can place a member's home: never published, never granted to a reader (hard limit 15)
CREATE TABLE IF NOT EXISTS mp_interests_private.declaration_text (
    key   text PRIMARY KEY,                          -- the declaration's key
    text  text NOT NULL
);
