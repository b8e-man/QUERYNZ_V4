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
