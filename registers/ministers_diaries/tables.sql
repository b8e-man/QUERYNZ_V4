-- registers/ministers_diaries: the tables this lane owns, in its own schema and its private twin. Loaded into a
-- staging or scratch schema by replacing `ministers_diaries.` with that schema's name (in the shared scratch schema,
-- `<schema>.ministers_diaries_<table>`, and `<schema>_private.ministers_diaries_<table>` for the twin).

-- every page of the Beehive this lane read to find the releases: the page as landed, and when
CREATE TABLE IF NOT EXISTS ministers_diaries.pages (
    url          text NOT NULL,
    kind         text NOT NULL,                      -- terms | ministers | minister | listing
    document     text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    read_at      timestamptz NOT NULL,
    PRIMARY KEY (url, read_at)
);

-- every diary release the pages link: the link as the page gives it, and the document once landed
CREATE TABLE IF NOT EXISTS ministers_diaries.files (
    url          text PRIMARY KEY,
    label        text,                               -- the link's words on the page that lists it
    listed_on    text NOT NULL,                      -- the page's URL
    listing      text NOT NULL CHECK (listing ~ '^[0-9a-f]{64}$'),   -- that page's document
    minister_page text,                              -- the minister's page it was found under, if any
    document     text CHECK (document ~ '^[0-9a-f]{64}$'),           -- NULL until landed
    captured_at  timestamptz
);

-- the catch log: one line for every item the lane could not take to a published row, with the stage and the
-- reason (fetch | land | profile | scan | page | line | verbatim | entry)
CREATE TABLE IF NOT EXISTS ministers_diaries.set_aside (
    item     text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);
