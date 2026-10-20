-- registers/parties: the tables this lane owns, in `parties` and `parties_private`.
-- Loaded into a staging or scratch schema by replacing `parties.` (and `parties_private.`) with that schema's
-- name (load.sql). Every row is read from the Commission's register page or from the export of its Gazette
-- notices (capture.py); a registration is the party (lifecycle.py).

CREATE TABLE IF NOT EXISTS parties.registrations (
    key                     text PRIMARY KEY,               -- ec-party/<registered on, by the notice where held>/<12 hex of the first name's key>
    document                text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),  -- the registration notice's export, else the page
    page                    integer NOT NULL DEFAULT 1,
    place                   text NOT NULL,                  -- notice <id> resolution <n> | party <n>
    name                    text NOT NULL,                  -- the name it carries now (the page's spelling), or last carried
    first_name              text NOT NULL,                  -- the earliest name held
    registered_on           date,                           -- the register's date where the page lists it, else the notice's
    notice_registered_on    date,                           -- the day the registration notice says the Commission decided
    registered_by           date,                           -- the latest day it was registered by, where no day is stated
    registered_basis        text NOT NULL,                  -- registered | register page | registered before the notices' reach | listed as registered during the year
    cancelled_on            date,
    status                  text NOT NULL,                  -- on the register | cancelled | not on the register page; no cancellation held
    on_register             boolean NOT NULL,               -- listed on the page as captured
    register_seen_on        date NOT NULL,                  -- the day that page was captured
    off_register_by         date,                           -- not listed on that day and no cancellation notice held
    page_basis              text,                           -- how the page's party was joined: name | former name | window | page only
    "window"                text,                           -- the page's date against the notice's: same day | within the gazettal lag | differs | no notice date
    abbreviation            text,
    abbreviation_on_ballot  boolean NOT NULL,
    components              text,
    logo_registered_on      date,
    statement_deadline      text,
    audit                   text,
    website                 text,
    rules_title             text,
    rules_href              text,
    secretary               text,                           -- the party secretary's name, a public role; the contact lines are private
    register_document       text CHECK (register_document ~ '^[0-9a-f]{64}$'),
    register_place          text,
    cancelled_document      text CHECK (cancelled_document ~ '^[0-9a-f]{64}$'),
    cancelled_place         text,
    same_name_as            text,                           -- the other registrations that carried one of its names, comma-separated
    same_name_note          text,                           -- said so: the windows, and that a party registered again is a new registration
    read_from               text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader                  text NOT NULL,
    profile                 text NOT NULL,
    profile_version         integer NOT NULL,
    loaded_at               timestamptz NOT NULL
);

-- every name, abbreviation and printing a registration has carried, with the window the documents give it
CREATE TABLE IF NOT EXISTS parties.names (
    key              text PRIMARY KEY,                      -- <registration key>/<kind>/<12 hex>[/<n>]
    party            text NOT NULL,                         -- the registration
    name             text NOT NULL,                         -- as printed
    name_key         text NOT NULL,                         -- lifecycle.name_key: the comparison key
    kind             text NOT NULL CHECK (kind IN ('name', 'abbreviation', 'printed')),
    from_on          date,                                  -- NULL: before the documents' reach, or the page gives no day
    to_on            date,                                  -- NULL: still carried, or the page shows it ended without a day
    basis            text NOT NULL,                         -- registered | stated | window | register page | printed | …
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- every resolution read from a notice; taken from the old estate's tables, original not held
CREATE TABLE IF NOT EXISTS parties.events (
    key               text PRIMARY KEY,                     -- gazette/<notice id>/<n>
    notice            text NOT NULL,                        -- the Gazette's own notice number
    published_on      date NOT NULL,
    decided_on        date,                                 -- the day the Commission decided; NULL where the notice states none
    kind              text NOT NULL,                        -- registered | cancelled | renamed | abbreviation | logo | components
    party_label       text,                                 -- the party as printed (the old name, for a rename)
    new_name          text,
    abbreviation      text,
    old_abbreviation  text,
    ref               text,
    party             text,                                 -- the registration it was resolved to; NULL for logo and components
    url               text,
    title             text,
    clause            text NOT NULL,                        -- the resolution's own words, as held
    source_note       text NOT NULL,
    gazette_key       text,                                 -- the notice's row in pub.gazette_notices, where the Gazette lane holds it
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),  -- the Gazette lane's export where it holds the same text, else the parties export
    page              integer NOT NULL DEFAULT 1,
    place             text NOT NULL,
    read_from         text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader            text NOT NULL,
    profile           text NOT NULL,
    profile_version   integer NOT NULL,
    loaded_at         timestamptz NOT NULL
);

-- every party label the other lanes publish, one row per (label, on), resolved by name and window (labels.py)
CREATE TABLE IF NOT EXISTS parties.labels (
    key              text PRIMARY KEY,                      -- label/<12 hex of the label>/<on>
    label            text NOT NULL,                         -- as the other lane publishes it
    "on"             text NOT NULL,                         -- the day the filing speaks for (YYYY-MM-DD), else its year (YYYY); '' none
    grain            text NOT NULL CHECK (grain IN ('day', 'year')),
    party            text,                                  -- the registration (pub.parties.key); NULL unresolved
    party_name       text,                                  -- that registration's name now, or last carried
    basis            text NOT NULL,                         -- exact | variant | core | fuzzy:0.NN | before its bracket … | not a party | unresolved
    why              text,                                  -- for a label that joins no registration: why
    same_name        text,                                  -- where two registrations carried the name: both, with their windows
    sources          text NOT NULL,                         -- <lane>.<table> <rows>; …
    rows             integer NOT NULL,
    resolver         text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),  -- the name row the registration carried that day
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- every document the lane took, and what it did with it
CREATE TABLE IF NOT EXISTS parties.files (
    document   text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    name       text NOT NULL,
    kind       text NOT NULL,                               -- register | applications | notices | gazette notices
    status     text NOT NULL,                               -- read | held, not read | read, compared, not cited
    PRIMARY KEY (document, name)
);

-- the catch log: one line for every item the lane could not take to a row
CREATE TABLE IF NOT EXISTS parties.set_aside (
    item       text NOT NULL,
    stage      text NOT NULL,                               -- capture | page | notices | lifecycle | labels
    reason     text NOT NULL,
    at         timestamptz NOT NULL DEFAULT now()
);

-- the party secretary's contact lines as the page prints them (a postal address that is sometimes a home): never published
CREATE TABLE IF NOT EXISTS parties_private.secretary_contacts (
    key        text PRIMARY KEY,                            -- the registration's key
    contact    text NOT NULL
);
