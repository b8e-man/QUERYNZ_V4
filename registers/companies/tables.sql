-- registers/companies: the tables this lane owns, in `companies` and `companies_private`.
-- Loaded into a staging or scratch schema by replacing `companies.` (and `companies_private.`) with that schema's
-- name (load.sql). Every row is read from the once-only export of the old estate's loaded monthly files
-- (capture.py): taken from the old estate's tables, original not held. `document` is the export part's hash and
-- `place` its line.

-- every entity the package names: the five company types and the other incorporated bodies
CREATE TABLE IF NOT EXISTS companies.entities (
    key              text PRIMARY KEY,                      -- companies/<nzbn>, or companies/<register>/<number> where none
    register         text NOT NULL,                         -- companies | other_incorporated | charitable_trust_board | public_sector | retirement_village
    nzbn             text,                                  -- the NZBN as filed
    number           text,                                  -- the register's own number (company number, incorporation number)
    name             text NOT NULL,
    entity_type      text,                                  -- as filed: LTD, ASIC, NON_ASIC, COOP, UNLTD, …
    status           text,                                  -- as filed
    registered_on    date,                                  -- as filed
    removed_on       date,                                  -- as filed: the source's removal or deregistration date
    in_latest        boolean NOT NULL,                      -- in the latest file read
    first_file       text,                                  -- the first file it was seen in, where the old tables say
    last_file        text NOT NULL,
    extra            jsonb,                                 -- the register's other filed fields (society act, charity number)
    old_id           text,                                  -- the old estate's row id, for mapping old decisions by content only
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- an entity's earlier state, as an earlier file had it, where a later file changed it
CREATE TABLE IF NOT EXISTS companies.entity_states (
    key              text PRIMARY KEY,                      -- <entity key>/in/<file>[/<n>]
    entity_key       text NOT NULL,
    file             text NOT NULL,
    name             text NOT NULL,
    entity_type      text,
    status           text,
    registered_on    date,
    removed_on       date,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per director role a file lists. The file gives no role number: the key is the company and the role's
-- filed content (names and start), the same content the old estate keyed on
CREATE TABLE IF NOT EXISTS companies.directors (
    key              text PRIMARY KEY,                      -- companies/<nzbn>/director/<12 hex of the names and start>
    entity_key       text NOT NULL,
    nzbn             text NOT NULL,
    company_number   text,
    first_name       text,
    middle_names     text,
    last_name        text,
    full_name        text NOT NULL,
    role_type        text NOT NULL,
    appointed_on     date,                                  -- as filed (START_DATE)
    ended_on         date,                                  -- as filed; the monthly file states none, so always empty
    in_latest        boolean NOT NULL,
    first_file       text NOT NULL,
    last_file        text NOT NULL,                         -- the window: in every file from first_file to last_file
    suppressed       boolean NOT NULL DEFAULT false,
    old_id           text,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- one row per shareholding a file lists. No allocation number is held: the key is the company and the holding's
-- filed content (name, shares, status), so a change in shares is a new row and the old one leaves the file
CREATE TABLE IF NOT EXISTS companies.shareholders (
    key              text PRIMARY KEY,                      -- companies/<nzbn>/shareholder/<12 hex of name, shares, status>
    entity_key       text NOT NULL,
    nzbn             text NOT NULL,
    company_number   text,
    shareholder_type text,                                  -- individual | company, as filed
    name             text NOT NULL,                         -- as filed
    holder_nzbn      text,                                  -- as filed (empty in every file read so far)
    shares           numeric,
    allocation_status text,
    in_latest        boolean NOT NULL,
    first_file       text NOT NULL,
    last_file        text NOT NULL,
    suppressed       boolean NOT NULL DEFAULT false,
    old_id           text,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- an entity's registered office as the file gives it (a company's registered address is shown: hard limit 15)
CREATE TABLE IF NOT EXISTS companies.registered_offices (
    key              text PRIMARY KEY,                      -- <entity key>/registered-office/<start or undated>/<12 hex of the lines>
    entity_key       text NOT NULL,
    register         text NOT NULL,
    started_on       date,                                  -- as filed
    care_of          text,
    line_1           text,
    line_2           text,
    line_3           text,
    line_4           text,
    postcode         text,
    country          text,
    in_latest        boolean NOT NULL,
    last_file        text NOT NULL,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- every document the lane took, and what it did with it
CREATE TABLE IF NOT EXISTS companies.files (
    document   text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    name       text NOT NULL,
    kind       text NOT NULL,                               -- entities | directors | shareholders | addresses
    status     text NOT NULL,                               -- read
    PRIMARY KEY (document, name)
);

-- the catch log: one line for every item the lane could not take to a row, and every count the old loader lost
CREATE TABLE IF NOT EXISTS companies.set_aside (
    item       text NOT NULL,                               -- <export sha>/line <n>, or <export sha>/<file>
    stage      text NOT NULL,                               -- capture | entities | directors | shareholders | addresses
    reason     text NOT NULL,
    count      integer NOT NULL DEFAULT 1,                  -- items the line stands for (a fold the old loader made)
    at         timestamptz NOT NULL DEFAULT now()
);

-- a person's residential address, keyed by the role's key: never published (hard limit 15). The monthly files
-- read so far carry none, so it is empty; it is here so a later file that does has one place to go
CREATE TABLE IF NOT EXISTS companies_private.residential_addresses (
    key        text PRIMARY KEY,
    address    text NOT NULL
);

-- ── company monitoring (plan 5.5, ruling 19; monitor.py) ─────────────────────────────────────────────────────
-- The queue and the ledger are KEPT: a load's wipe and the monitor's rebuild never touch them (`requests` and
-- `watch` are what a product asked for; `calls` indexes the landed answers, which cannot be regenerated). The
-- lookup tables and `changes` are rebuilt from the ledger's answers (monitor.rebuild).

-- a product's request that the estate check one entity now. Written only through pub.request_company_check
-- (publish.sql), which takes the asker from the database login, never from an argument
CREATE TABLE IF NOT EXISTS companies.requests (
    id               bigserial PRIMARY KEY,
    nzbn             text,                                  -- as the product gave it
    name             text CHECK (length(name) <= 300),     -- as the product gave it
    product          text NOT NULL CHECK (product ~ '^[a-z0-9][a-z0-9_/-]{0,63}$'),
    asked_by         text NOT NULL,                         -- the login that raised it (session_user)
    asked_at         timestamptz NOT NULL DEFAULT now(),
    state            text NOT NULL DEFAULT 'waiting' CHECK (state IN ('waiting', 'answered', 'set_aside')),
    resolved_nzbn    text,
    call_id          bigint,                                -- the call that answered it (companies.calls)
    answered_at      timestamptz,
    reason           text,                                  -- how it was answered, or why it was set aside
    attempts         integer NOT NULL DEFAULT 0,            -- nights a failed read left it waiting
    CHECK (nzbn IS NOT NULL OR name IS NOT NULL),
    CHECK (state <> 'set_aside' OR reason IS NOT NULL),
    CHECK (state <> 'answered' OR call_id IS NOT NULL)
);

-- an entity a product wants checked on a schedule. Written only through pub.watch_company / pub.unwatch_company
CREATE TABLE IF NOT EXISTS companies.watch (
    nzbn             text NOT NULL,
    product          text NOT NULL CHECK (product ~ '^[a-z0-9][a-z0-9_/-]{0,63}$'),
    asked_by         text NOT NULL,                         -- the login that asked (session_user)
    asked_at         timestamptz NOT NULL DEFAULT now(),
    every_days       integer NOT NULL DEFAULT 7 CHECK (every_days BETWEEN 1 AND 366),
    active           boolean NOT NULL DEFAULT true,
    PRIMARY KEY (nzbn, product)
);

-- the ledger: every call made to the interface, answered or not
CREATE TABLE IF NOT EXISTS companies.calls (
    id               bigserial PRIMARY KEY,
    nzbn             text NOT NULL,
    at               timestamptz NOT NULL,
    day              date NOT NULL,                         -- the New Zealand day, for the day's limit
    status           integer NOT NULL,                      -- the HTTP status
    document         text CHECK (document ~ '^[0-9a-f]{64}$'),  -- the landed answer; empty when none
    blocked          text,                                  -- why the read failed (hard limit 6)
    why              text NOT NULL                          -- request <id> | watch
);

-- the entity as the interface answered it: one row per answer (the latest marked). Sole traders, partnerships
-- and trusts, which the monthly reading does not take, are here as kinds of their own
CREATE TABLE IF NOT EXISTS companies.lookups (
    key              text PRIMARY KEY,                      -- companies/<nzbn>/answer/<12 hex of the answer>
    entity_key       text NOT NULL,                         -- companies/<nzbn>, as the monthly rows key it
    nzbn             text NOT NULL,
    kind             text NOT NULL CHECK (kind IN ('company', 'sole_trader', 'partnership', 'trust', 'society', 'other')),
    entity_type      text,                                  -- as answered (entityTypeCode)
    type_description text,
    name             text,                                  -- empty where the register withholds it
    status           text,
    registered_on    date,
    register_updated_on date,                               -- the interface's own lastUpdatedDate
    trading_names    jsonb,
    asked_at         timestamptz NOT NULL,
    call_id          bigint NOT NULL,
    in_monthly       boolean NOT NULL,                      -- the monthly reading holds the entity too
    latest           boolean NOT NULL,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- each role the answer lists (directors; trustees and partners where the register lists them), with the
-- interface's own start and end: the end the monthly file never states
CREATE TABLE IF NOT EXISTS companies.lookup_roles (
    key              text PRIMARY KEY,                      -- companies/<nzbn>/role/<the register's role id>/<answer>
    answer_key       text NOT NULL,
    entity_key       text NOT NULL,
    nzbn             text NOT NULL,
    role_uid         text,                                  -- the register's own role identifier
    role_type        text,
    role_status      text,
    first_name       text,
    middle_names     text,
    last_name        text,
    full_name        text NOT NULL,
    is_body          boolean NOT NULL,
    body_nzbn        text,
    started_on       date,
    ended_on         date,                                  -- as the interface states it
    held_key         text,                                  -- the monthly director row it is (companies.directors.key)
    suppressed       boolean NOT NULL DEFAULT false,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- each holding the answer lists, current and historic; a historic holding carries the interface's end
CREATE TABLE IF NOT EXISTS companies.lookup_holdings (
    key              text PRIMARY KEY,
    answer_key       text NOT NULL,
    entity_key       text NOT NULL,
    nzbn             text NOT NULL,
    holder_type      text,                                  -- as answered: individual | director | entity
    name             text NOT NULL,
    holder_nzbn      text,
    shares           numeric,                               -- the allocation's shares (current holdings)
    allocation       integer,                               -- the allocation's place in the answer
    started_on       date,
    ended_on         date,                                  -- vacationDate, as the interface states it
    current          boolean NOT NULL,
    suppressed       boolean NOT NULL DEFAULT false,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- a company's or society's registered office as answered (shown: hard limit 15). Every other address, and every
-- address of a sole trader, partnership or trust, goes to companies_private.lookup_addresses
CREATE TABLE IF NOT EXISTS companies.lookup_offices (
    key              text PRIMARY KEY,
    answer_key       text NOT NULL,
    entity_key       text NOT NULL,
    nzbn             text NOT NULL,
    started_on       date,
    ended_on         date,
    care_of          text,
    line_1           text,
    line_2           text,
    line_3           text,
    line_4           text,
    postcode         text,
    country          text,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- each difference between an answer and the state held before it (the previous answer, else the monthly
-- file's rows), dated: by the interface's own date where it states one, else by the day it was seen
CREATE TABLE IF NOT EXISTS companies.changes (
    key              text PRIMARY KEY,                      -- companies/<nzbn>/change/<answer>/<kind>/<12 hex>
    entity_key       text NOT NULL,
    nzbn             text NOT NULL,
    kind             text NOT NULL CHECK (kind IN ('name', 'status', 'director_appointed', 'director_ended',
                                                   'director_not_listed', 'holding_started', 'holding_ended',
                                                   'holding_not_listed', 'registered_office')),
    subject          text,                                  -- the person or body the change is about
    before           text,
    after            text,
    effective_on     date,                                  -- the interface's own date, where it states one
    date_basis       text NOT NULL CHECK (date_basis IN ('register', 'seen')),
    seen_on          date NOT NULL,                         -- the New Zealand day of the answer
    register_updated_on date,                               -- the interface's lastUpdatedDate: on or before it
    compared_with    text NOT NULL,                         -- the answer of <day> | the monthly file <file>
    previous_document text NOT NULL CHECK (previous_document ~ '^[0-9a-f]{64}$'),
    held_key         text,                                  -- the monthly row the change ends, where there is one
    suppressed       boolean NOT NULL DEFAULT false,
    call_id          bigint NOT NULL,
    source_note      text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- the monitor's catch log
CREATE TABLE IF NOT EXISTS companies.lookup_set_aside (
    item       text NOT NULL,                               -- <answer sha>/<place>
    stage      text NOT NULL,
    reason     text NOT NULL,
    at         timestamptz NOT NULL DEFAULT now()
);

-- every address an answer carries other than a company's or society's registered office: a role's, a holder's,
-- and every address of a sole trader, partnership or trust. Never published (hard limit 15)
CREATE TABLE IF NOT EXISTS companies_private.lookup_addresses (
    key        text PRIMARY KEY,                            -- <answer key>/<place in the answer>
    owner_key  text NOT NULL,
    kind       text NOT NULL,
    address    jsonb NOT NULL,
    document   text NOT NULL
);
