-- registers/house: the tables this lane owns, in `house` and `house_private`.
-- Loaded into a staging or scratch schema by replacing `house.` with that schema's name (load.sql). Every row is
-- read from the Commission's results pages, its nominations files, or Stats NZ's electorate names (capture.py).
-- Keys are the Commission's own identities (read.py says why); every row cites its document's hash and place.
-- `house_private` holds nothing: no file this lane reads carries a home address.

-- every general election and by-election the results index lists, and a general election announced and not yet polled
CREATE TABLE IF NOT EXISTS house.elections (
    key              text PRIMARY KEY,                      -- ge-<year> | be-<year>-<electorate>
    kind             text NOT NULL CHECK (kind IN ('general', 'by-election')),
    name             text NOT NULL,                         -- as printed
    electorate       text,                                  -- a by-election's electorate, as printed
    polled_on        date,                                  -- the polling day the Commission states; NULL: not yet polled
    polled_basis     text NOT NULL,
    results_href     text,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- each election's electorates, joined to Stats NZ's name where the boundary set it was fought on is held
CREATE TABLE IF NOT EXISTS house.electorates (
    key                  text PRIMARY KEY,                  -- <election>/<electorate>
    election             text NOT NULL,
    name                 text NOT NULL,                     -- the Commission's spelling
    number               integer,                           -- the results site's page number, 1-72
    statsnz_code         text,
    statsnz_name         text,
    layer                text CHECK (layer IN ('general', 'maori')),
    statsnz_document     text CHECK (statsnz_document ~ '^[0-9a-f]{64}$'),
    join_basis           text NOT NULL,                     -- exact | … folded | not joined | boundary set not held | …
    votes_counted        integer,
    candidate_total      integer,                           -- the page's own printed totals
    candidate_informals  integer,
    party_total          integer,
    party_informals      integer,
    poll_cancelled       boolean NOT NULL,
    result_held          boolean NOT NULL,                  -- the electorate's result page was read
    document             text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                 integer NOT NULL DEFAULT 1,
    place                text NOT NULL,
    read_from            text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader               text NOT NULL,
    profile              text NOT NULL,
    profile_version      integer NOT NULL,
    loaded_at            timestamptz NOT NULL
);

-- one row per candidacy: an electorate, a list place, or both (the two files joined, the basis said)
CREATE TABLE IF NOT EXISTS house.candidates (
    key                text PRIMARY KEY,                    -- <election>/<name>/<electorate> | <election>/<name>/list-<party>
    election           text NOT NULL,
    name               text NOT NULL,                       -- as filed: SURNAME, Given
    display_name       text NOT NULL,                       -- keys.names.person_name(...).display
    name_key           text NOT NULL,                       -- keys.names.person_key: for equality only
    party              text,                                -- as printed; NULL: none printed (independent, or not seeking the party vote)
    party_registered   text,                                -- keys.parties.party_name
    party_basis        text,
    electorate         text,                                -- the electorate's key; NULL: list only
    list_place         integer,                             -- NULL: not on a list held
    list_document      text CHECK (list_document ~ '^[0-9a-f]{64}$'),
    list_place_cite    text,
    votes              integer,                             -- candidate votes at the official count; NULL: not polled
    poll_cancelled     boolean NOT NULL,
    joined_basis       text,                                -- how the electorate row and the list place were joined
    document           text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page               integer NOT NULL DEFAULT 1,
    place              text NOT NULL,
    read_from          text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader             text NOT NULL,
    profile            text NOT NULL,
    profile_version    integer NOT NULL,
    loaded_at          timestamptz NOT NULL
);

-- who the official result returned, and the by-election winners, with a window per seat
CREATE TABLE IF NOT EXISTS house.members (
    key                text PRIMARY KEY,                    -- <election>/seat/<electorate> | <election>/seat/list/<party>/<name>
    election           text NOT NULL,
    name               text NOT NULL,
    display_name       text NOT NULL,
    name_key           text NOT NULL,
    party              text NOT NULL,
    party_registered   text,
    party_basis        text,
    route              text NOT NULL CHECK (route IN ('electorate', 'list', 'by-election')),
    electorate         text,                                -- NULL for a list seat
    candidate          text,                                -- the candidacy's key, where its result page is held
    from_on            date,                                -- the polling day that returned the member
    from_basis         text,
    to_by              date,                                -- the latest the seat can have ended: the next poll that filled it
    to_basis           text,
    ended_on           date,                                -- the day it ended, as a document states it: none held does
    document           text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page               integer NOT NULL DEFAULT 1,
    place              text NOT NULL,
    read_from          text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader             text NOT NULL,
    profile            text NOT NULL,
    profile_version    integer NOT NULL,
    loaded_at          timestamptz NOT NULL
);

-- the Commission's own printed figures, which the outside check counts again (check.py)
CREATE TABLE IF NOT EXISTS house.figures (
    key                text PRIMARY KEY,
    election           text NOT NULL,
    what               text NOT NULL,
    party              text,
    value              integer NOT NULL,
    document           text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page               integer NOT NULL DEFAULT 1,
    place              text NOT NULL,
    read_from          text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader             text NOT NULL,
    profile            text NOT NULL,
    profile_version    integer NOT NULL,
    loaded_at          timestamptz NOT NULL
);

-- every file the lane took, and what it did with it
CREATE TABLE IF NOT EXISTS house.files (
    document   text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    name       text NOT NULL,                               -- <old folder>/<file>
    kind       text NOT NULL,                               -- the profile, or what the file was
    status     text NOT NULL CHECK (status IN ('read', 'held, not read', 'failed read', 'not recognised')),
    PRIMARY KEY (document, name)
);

-- the catch log: one line for every item the lane could not take to a row
CREATE TABLE IF NOT EXISTS house.set_aside (
    item       text NOT NULL,
    stage      text NOT NULL,                               -- capture | elections | results | electorates | by-elections | nominations | members | …
    reason     text NOT NULL,
    at         timestamptz NOT NULL DEFAULT now()
);
