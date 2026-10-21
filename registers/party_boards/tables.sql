-- registers/party_boards: the tables this lane owns, in `party_boards`. No private twin is needed: the lane
-- reads only a page's board section, and a contact line or a promoter statement is never read into a row.
-- Loaded into a staging or scratch schema by replacing `party_boards.` with that schema's name (load.sql).
-- Every row is read from a captured party page (capture.py) through the profile party-website-board-page (read.py).

-- one row per board role a party declares on a captured page of its own website: the declared tier (ruling 72)
CREATE TABLE IF NOT EXISTS party_boards.roles (
    key               text PRIMARY KEY,                     -- <document>/<shape>/line-<n>[-name-<k>]: the page's hash and the place
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page              integer NOT NULL DEFAULT 1,
    place             text NOT NULL,                        -- line <n> of the page as read (page.py), [name <k> where one line names two]
    party             text NOT NULL,                        -- the party whose website it is, as the capture names it
    url               text NOT NULL,                        -- the party's own page
    captured_on       date NOT NULL,                        -- the first capture of these bytes: the Archive's snapshot day, or the old job's fetch
    last_captured_on  date NOT NULL,                        -- the last capture of the same bytes (the page unchanged between)
    captures          integer NOT NULL,                     -- how many captures held these bytes
    capture_kind      text NOT NULL CHECK (capture_kind IN ('wayback', 'current')),
    archive_url       text,                                 -- the Internet Archive's copy, for a wayback capture
    shape             text NOT NULL,                        -- the profile's shape that read the page
    section           text NOT NULL,                        -- the heading that opens the board section, as printed
    name_as_declared  text NOT NULL,                        -- the line as the page prints it
    name              text NOT NULL,                        -- without an honorific, post-nominals or a trailing bracket
    qualifier         text,                                 -- the trailing bracket: '(Acting)', '(Auckland)', '(Chair)'
    role              text NOT NULL,                        -- as the page declares it; several role lines joined by '; '
    role_basis        text NOT NULL CHECK (role_basis IN ('stated', 'heading')),  -- beside the name, or the heading's for all listed under it
    tier              text NOT NULL CHECK (tier = 'declared'),
    read_from         text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader            text NOT NULL,
    profile           text NOT NULL,
    profile_version   integer NOT NULL,
    loaded_at         timestamptz NOT NULL
);

-- every capture the lane took, and what the reading made of it: items in equal items out plus items set aside
CREATE TABLE IF NOT EXISTS party_boards.pages (
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    ts                text NOT NULL,                        -- the capture's timestamp (yyyymmddhhmmss), '' for the manifest
    url               text NOT NULL,                        -- '' for the manifest
    party             text,
    captured_on       date,
    capture_kind      text,                                 -- wayback | current | manifest
    archive_url       text,
    status            text NOT NULL,                        -- read | board section, no names | drop-note | before the window, not landed | the capture's index
    shape             text,
    reason            text,                                 -- for a drop-note, why
    rows              integer NOT NULL DEFAULT 0,
    set_aside         integer NOT NULL DEFAULT 0,
    reader            text,
    profile           text,
    profile_version   integer,
    loaded_at         timestamptz NOT NULL,
    PRIMARY KEY (document, ts, url)
);

-- the catch log: one line for every name the lane could not take to a row (never the line's text)
CREATE TABLE IF NOT EXISTS party_boards.set_aside (
    item       text NOT NULL,                               -- <document>/<place>
    stage      text NOT NULL,                               -- capture | read
    reason     text NOT NULL,
    at         timestamptz NOT NULL DEFAULT now()
);
