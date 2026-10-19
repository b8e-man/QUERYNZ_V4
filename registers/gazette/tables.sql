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

-- one row per company a liquidator's appointment names (profile gazette-liquidator-appointment, section al)
CREATE TABLE IF NOT EXISTS gazette.liquidations (
    key              text PRIMARY KEY,                      -- gazette/<notice>/company/<ordinal>
    notice           text NOT NULL,
    published_on     date,
    company          text NOT NULL,                         -- as printed, a status or former name in brackets taken out
    company_number   text,                                  -- where the notice prints one for its one company
    shape            text NOT NULL CHECK (shape IN ('notice', 'list')),
    appointed_by     text CHECK (appointed_by IN ('shareholders', 'board', 'court', 'creditors')),
    statute          text,                                  -- the first Act and section cited
    appointed_on     date,                                  -- the appointment's date, or the Official Assignee's list date
    appointed_at     text,                                  -- the time printed with it: "10.30am"
    date_basis       text CHECK (date_basis IN ('appointment', 'list date')),
    dated_on         date,
    corrigendum      boolean NOT NULL,
    liquidators      integer NOT NULL,                      -- how many the notice names
    register_key     text,                                  -- the companies lane's entity (pub.companies.key); none where unmatched
    register_match   text,                                  -- how (register.py); NULL where the register was not in the database
    ordinal          integer NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                         -- notice <number> company <ordinal>
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per liquidator a liquidator's appointment names (from its signature, else its operative sentence)
CREATE TABLE IF NOT EXISTS gazette.liquidators (
    key              text PRIMARY KEY,                      -- gazette/<notice>/liquidator/<ordinal>
    notice           text NOT NULL,
    published_on     date,
    name             text NOT NULL,                         -- as signed; no address, telephone or email is read
    role             text NOT NULL,                         -- as signed (Liquidator, Joint Liquidators, …) or 'named as appointed'
    named_in_body    text NOT NULL CHECK (named_in_body IN ('full', 'surname', 'no')),
    companies        integer NOT NULL,                      -- how many companies the notice names
    ordinal          integer NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per company a removal notice (ds), a winding-up application (aw), a receivership (ar), a notice to creditors (md)
-- or an administration (aa) names
CREATE TABLE IF NOT EXISTS gazette.company_notices (
    key              text PRIMARY KEY,                      -- gazette/<notice>/company/<ordinal>
    notice           text NOT NULL,
    published_on     date,
    kind             text NOT NULL CHECK (kind IN ('removal', 'winding-up application', 'receivership', 'notice to creditors',
                                                     'administration')),
    action           text,                                  -- the notice's own words: intention to remove, application to put into liquidation, …
    company          text NOT NULL,                         -- as printed, a status or former name in brackets taken out
    company_number   text,                                  -- where printed for this company
    shape            text NOT NULL CHECK (shape IN ('notice', 'list')),
    statute          text,                                  -- the first Act and section cited
    ground           text,                                  -- removal: liquidation completed | ceased business
    by_whom          text,                                  -- who gives notice or appointed: liquidator, Registrar, director, …
    party            text,                                  -- the plaintiff (aw) as printed; never its address
    event_on         date,                                  -- what event_basis says: objections by, hearing, appointment, ceased to act
    event_at         text,                                  -- the time printed with it
    event_basis      text,
    filed_on         date,                                  -- the application's filing (aw)
    court            text,                                  -- High Court at <place> (aw)
    reference        text,                                  -- the court's file number (aw)
    dated_on         date,
    corrigendum      boolean NOT NULL,
    people           integer NOT NULL,                      -- receivers or administrators the notice names (ar, aa)
    register_key     text,                                  -- the companies lane's entity (pub.companies.key); none where unmatched
    register_match   text,                                  -- how (register.py); NULL where the register was not in the database
    ordinal          integer NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                         -- notice <number> company <ordinal>
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per receiver or administrator a receivership or administration names (from its signature, else its
-- operative sentence)
CREATE TABLE IF NOT EXISTS gazette.practitioners (
    key              text PRIMARY KEY,                      -- gazette/<notice>/practitioner/<ordinal>
    notice           text NOT NULL,
    published_on     date,
    name             text NOT NULL,                         -- as signed; no address, telephone or email is read
    role             text NOT NULL,
    named_in_body    text NOT NULL CHECK (named_in_body IN ('full', 'surname', 'no')),
    companies        integer NOT NULL,
    ordinal          integer NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per person a bankruptcy notice names: the Official Assignee's adjudication and no-asset-procedure lists,
-- and single notices (annulment, discharge, adjudication, meeting, dividend). The address is in gazette_private only
CREATE TABLE IF NOT EXISTS gazette.bankruptcies (
    key              text PRIMARY KEY,                      -- gazette/<notice>/person/<ordinal>
    notice           text NOT NULL,
    published_on     date,
    kind             text NOT NULL,                         -- adjudication | no asset procedure | annulment | discharge | meeting | dividend | other
    shape            text NOT NULL CHECK (shape IN ('notice', 'list')),
    surname          text NOT NULL,
    given_names      text NOT NULL,
    also_known_as    text,
    occupation       text,                                  -- as printed (the older lists)
    event_on         date,                                  -- the adjudication or procedure's day; a single notice's first date after the name
    event_at         text,                                  -- the time printed with it
    court            text,
    statute          text,
    dated_on         date,
    withheld_by      text,                                  -- the annulment notice that names this person: the published view withholds the name
    ordinal          integer NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                         -- notice <number> person <ordinal>
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per person an appointment to public office names: the office as the notice states it, never where they live
CREATE TABLE IF NOT EXISTS gazette.appointments (
    key              text PRIMARY KEY,                      -- gazette/<notice>/appointee/<ordinal>
    notice           text NOT NULL,
    published_on     date,
    body             text,                                  -- from the title: the board, court or office
    name             text NOT NULL,                         -- as printed, with any honorific ("The Honourable", "Dr")
    role             text,                                  -- as printed: "a member and Deputy Chairperson", "a Judge of …"
    statute          text,
    by_whom          text,                                  -- Governor-General | the Sovereign | a Minister | a Chief Justice or Chief Judge
    starts_on        date,
    ends_on          date,
    dated_on         date,
    corrigendum      boolean NOT NULL,
    ordinal          integer NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,                         -- notice <number> appointee <ordinal>
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
    stage      text NOT NULL,                               -- capture | notices | celebrants | prohibitions | liquidations | register | …
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

-- a bankrupt's address as printed, and a "formerly of" address: never published, never granted to the session reader
CREATE TABLE IF NOT EXISTS gazette_private.bankruptcy_addresses (
    key        text PRIMARY KEY,                            -- the bankruptcy row's key
    address    text,
    formerly   text
);
