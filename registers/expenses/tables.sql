-- registers/expenses: the tables this lane owns, in its own schema. Loaded into a staging or scratch schema by
-- replacing `expenses.` with that schema's name (in the shared scratch schema, `<schema>.expenses_<table>`).
-- Nothing here is a person's home address; the private twin holds nothing (the releases print none).

-- every document the lane holds: its hash, its kind, where the old estate kept it, and the publisher's URL and
-- label for it (from the old job's manifest)
CREATE TABLE IF NOT EXISTS expenses.files (
    document     text PRIMARY KEY CHECK (document ~ '^[0-9a-f]{64}$'),
    kind         text NOT NULL,          -- mp-workbook | executive-workbook | catalogue-listing | dia-listing
    old_path     text NOT NULL,
    url          text,
    label        text,                   -- the publisher's name for it (the catalogue's resource name)
    captured_at  text                    -- when the old job fetched it, by its manifest
);

-- the catch log: one line for every item the lane could not take to a published row, with the stage and the
-- reason (capture | listing | workbook | sheet | release | row | arithmetic)
CREATE TABLE IF NOT EXISTS expenses.set_aside (
    item     text NOT NULL,              -- a document hash, a release, line or cell key, or a URL
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- one table of one release: a quarter (or part of one, where a change of government splits it) as printed
CREATE TABLE IF NOT EXISTS expenses.releases (
    key              text PRIMARY KEY,               -- <sha256>/sheet<n>/r<header row>
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL,               -- the sheet's position, from 1
    place            text NOT NULL,                  -- <sheet>!R<header row>
    sheet            text NOT NULL,
    publisher        text NOT NULL,                  -- parliamentary-service | internal-affairs
    title            text,                           -- the title row as printed
    period_start     date NOT NULL,
    period_end       date NOT NULL,
    period_basis     text NOT NULL,                  -- title | publisher's label
    label            text,                           -- the publisher's label for the workbook
    label_start      date,
    label_end        date,
    label_differs    boolean NOT NULL DEFAULT false, -- the label's quarter is not the title's
    url              text,
    columns          text NOT NULL,                  -- the heading paths and roles, as read
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    read_from        text NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one member's or minister's line in a release table
CREATE TABLE IF NOT EXISTS expenses.lines (
    key              text PRIMARY KEY,               -- <sha256>/sheet<n>/row<r>
    release          text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL,
    place            text NOT NULL,                  -- <sheet>!R<row>
    member           text NOT NULL,                  -- as printed ("Seymour, David", "Rt Hon Christopher Luxon")
    name             text,                           -- given-first, honorifics and footnote marks off (keys.names)
    party_printed    text,                           -- the party cell on this row, where the table has one
    party_label      text,                           -- the party heading or cell the row sits under; NULL where none is stated
    party            text,                           -- the registered party (keys.parties); NULL when unresolved
    party_basis      text NOT NULL,
    marks            text,                           -- footnote markers on the row, space-separated
    categories_sum   numeric(14,2),
    total            numeric(14,2),                  -- the row's own printed total
    "check"          text NOT NULL,                  -- adds | rounding | nothing-to-add (published) | differs | no-total
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    read_from        text NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one figure: a member's line under one column heading
CREATE TABLE IF NOT EXISTS expenses.figures (
    key              text PRIMARY KEY,               -- <sha256>/sheet<n>/<cell>
    line             text NOT NULL,
    release          text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL,
    place            text NOT NULL,                  -- <sheet>!<cell>
    category         text NOT NULL,                  -- the heading path as printed
    role             text NOT NULL,                  -- category | total | outside (held beside the total, never added)
    figure           numeric(14,2),                  -- NULL where the cell prints words ("N/A") or a formula with no result
    printed          text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    read_from        text NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- each printed total against the sum of the member lines it covers, per column (the outside check)
CREATE TABLE IF NOT EXISTS expenses.totals (
    release      text NOT NULL,
    line_place   text NOT NULL,                      -- <sheet>!R<row> of the total line
    label        text NOT NULL,                      -- "Act Total", "Grand Total", "Total All Parties"
    scope        text,                               -- party | since | table | sheet: the rows it was found to cover
    heading      text NOT NULL,
    total_role   text NOT NULL,
    printed      numeric(14,2) NOT NULL,
    rows_sum     numeric(14,2) NOT NULL,
    equal        boolean NOT NULL,
    widest       boolean NOT NULL                    -- the release table's grand total
);

-- the release's own notes, verbatim
CREATE TABLE IF NOT EXISTS expenses.notes (
    key       text PRIMARY KEY,
    release   text NOT NULL,
    document  text NOT NULL,
    page      integer NOT NULL,
    place     text NOT NULL,
    text      text NOT NULL
);
