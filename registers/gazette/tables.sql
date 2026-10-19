-- registers/gazette: the tables this lane owns, in `gazette` and `gazette_private`.
-- Loaded into a staging or scratch schema by replacing `gazette.` (and `gazette_private.`) with that schema's
-- name (load.sql). Every row is read from the once-only export of the Gazette notices the old estate holds as
-- text (capture.py): taken from the old estate's tables, original not held.

-- every notice held, typed by the Gazette's own section code and by the format the lane recognises
CREATE TABLE IF NOT EXISTS gazette.notices (
    key              text PRIMARY KEY,                      -- gazette/<notice number>
    notice           text NOT NULL UNIQUE,                  -- the Gazette's own number: <year>-<section><n>
    year             integer NOT NULL,                      -- the number's year
    section          text NOT NULL,                         -- the Gazette's section code (al, go, ba, …)
    number           integer NOT NULL,                      -- its place in the year's one sequence
    family           text NOT NULL,                         -- what the section holds (notices.FAMILY)
    format           text NOT NULL,                         -- the profile a reader recognised, or 'not read'
    status           text NOT NULL,                         -- read | read, part set aside | set aside | not read
    records          integer NOT NULL DEFAULT 0,            -- rows read from it
    supersedes       text,                                  -- the notices it revokes, replaces or varies, by number
    title            text NOT NULL,
    published_on     date,                                  -- as the old classifier held it; NULL where it held none
    url              text NOT NULL,
    old_type         text,                                  -- the old classifier's type, for comparison only
    article          text NOT NULL,                         -- the old article row the text came from
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                         -- notice <number>
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per celebrant a Registrar-General's list names, with the list's own action
CREATE TABLE IF NOT EXISTS gazette.celebrants (
    key              text PRIMARY KEY,                      -- gazette/<notice>/celebrant/<12 hex of the name>[/<n>]
    notice           text NOT NULL,
    published_on     date,
    action           text NOT NULL CHECK (action IN ('appointment', 'removal', 'publication', 'annual list')),
    statute          text,                                  -- the Act and section the notice cites, as printed
    period_from      date,                                  -- the appointment's period where the notice states one
    period_to        date,
    surname          text NOT NULL,
    given_names      text NOT NULL,
    organisation     text,                                  -- the nominating body, as printed; never an address
    list_shape       text NOT NULL,                         -- stops | address | chain | marked
    marks            text,                                  -- a marked list's letters: M (independent marriage), CU (civil union)
    split            text NOT NULL,                         -- delimited | last word | glue: how the name was cut
    ordinal          integer NOT NULL,                      -- its place in the list as read
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                         -- notice <number> record <ordinal>
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per person a notice prohibits from managing companies (profile gazette-director-prohibition)
CREATE TABLE IF NOT EXISTS gazette.prohibitions (
    key              text PRIMARY KEY,                      -- gazette/<notice>/prohibition/<ordinal>
    notice           text NOT NULL,
    published_on     date,
    action           text NOT NULL CHECK (action IN ('prohibition', 'court order', 'banning order', 'substitution', 'variation')),
    name             text NOT NULL,                         -- the `To:` field, aliases taken out
    also_known_as    text,                                  -- the bracketed aliases as printed, '; ' between
    named_twice      boolean NOT NULL,                      -- the operative sentence names the same person
    statute          text,                                  -- the Act and the most specific section cited
    months           integer,                               -- the term; NULL when permanent
    permanent        boolean NOT NULL,
    starts_on        date,
    starts_basis     text CHECK (starts_basis IN ('stated', 'date of the notice')),
    ends_on          date,                                  -- starts_on plus the term; NULL when permanent or unknown
    dated_on         date,                                  -- the notice's own "Dated … this …"
    supersedes       text,                                  -- the notice(s) this one revokes and replaces, or varies
    superseded_by    text,                                  -- a later notice that revokes, replaces or varies this one
    superseded_how   text CHECK (superseded_how IN ('revoked', 'revoked and replaced', 'varied')),
    ordinal          integer NOT NULL,                      -- the person's place in the notice
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                         -- notice <number> person <ordinal>
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- every document the lane took, and what it did with it
CREATE TABLE IF NOT EXISTS gazette.files (
    document   text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    name       text NOT NULL,
    kind       text NOT NULL,                               -- notices
    status     text NOT NULL,                               -- read | held, not read
    PRIMARY KEY (document, name)
);

-- the catch log: one line for every item the lane could not take to a row
CREATE TABLE IF NOT EXISTS gazette.set_aside (
    item       text NOT NULL,                               -- <export sha>/notice <number>[ <place>]
    stage      text NOT NULL,                               -- capture | notices | celebrants | prohibitions | liquidations
    reason     text NOT NULL,
    at         timestamptz NOT NULL DEFAULT now()
);

-- an independent celebrant's address as the list prints it (often a home): never published (hard limit 15)
CREATE TABLE IF NOT EXISTS gazette_private.celebrant_addresses (
    key        text PRIMARY KEY,                            -- the celebrant row's key
    address    text NOT NULL
);

-- a prohibited person's address as the notice prints it (`Of:`, often a home): never published (hard limit 15)
CREATE TABLE IF NOT EXISTS gazette_private.prohibition_addresses (
    key        text PRIMARY KEY,                            -- the prohibition row's key
    address    text NOT NULL,
    formerly   boolean NOT NULL                             -- printed "Formerly of:"
);
