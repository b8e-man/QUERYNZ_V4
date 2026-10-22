-- registers/contract_disclosures: every table this lane owns, in `contract_disclosures` and its private twin
-- `contract_disclosures_private` (made and empty: no address, phone or email is read). The capture's record
-- (capture.py makes it; never wiped) and the reading's tables (load.py drops and makes them at every load).

CREATE SCHEMA IF NOT EXISTS contract_disclosures;
CREATE SCHEMA IF NOT EXISTS contract_disclosures_private;

-- ── the capture ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS contract_disclosures.capture_runs (
    run_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mode         text NOT NULL CHECK (mode IN ('copy', 'refresh')),
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz,
    requests     integer,
    landed       integer,
    set_aside    integer,
    stopped      text
);

-- one row per document a run landed or found already held: a package's catalogue description, or one of its files
CREATE TABLE IF NOT EXISTS contract_disclosures.capture_files (
    file_id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id             bigint NOT NULL REFERENCES contract_disclosures.capture_runs,
    package            text NOT NULL,                 -- the catalogue's package name
    agency             text NOT NULL,                 -- the publishing agency, as the catalogue names it
    role               text NOT NULL CHECK (role IN ('catalogue', 'data')),
    url                text NOT NULL,
    sha256             text NOT NULL,
    size               bigint,
    resource_id        text,
    resource_name      text,
    resource_format    text,
    resource_modified  text,                          -- the catalogue's date for the file, as given
    licence_id         text,
    how                text NOT NULL CHECK (how IN ('fetched', 'copied')),
    new                boolean NOT NULL,
    at                 timestamptz NOT NULL DEFAULT now()
);

-- the capture's catch log: a failed read, a licence that does not allow it, an answer that is not the file
CREATE TABLE IF NOT EXISTS contract_disclosures.capture_set_aside (
    run_id   bigint REFERENCES contract_disclosures.capture_runs,
    item     text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
-- (load.py drops and makes these at every load, from the files the capture lists)

-- one row per cell pair an agency's file publishes: claims and costs for a financial year at one level of its
-- breakdown (a region, a territorial authority within it, a contract class within that, or the file's total)
CREATE TABLE contract_disclosures.costs (
    key                          text PRIMARY KEY,
    agency                       text NOT NULL,
    level                        text NOT NULL CHECK (level IN ('region', 'territorial authority', 'class', 'total')),
    region                       text,                -- the accident region, as published
    territorial_authority        text,
    contract_class               text,
    financial_year               text NOT NULL,       -- as published: '2013' is the year ended 30 June 2013
    year_ended                   date NOT NULL,
    active_claims_as_published   text NOT NULL,       -- '<4' where the agency suppressed it
    total_costs_as_published     text NOT NULL,       -- '<$100' where the agency suppressed it
    active_claims                numeric,             -- only where a number is printed
    total_costs_nzd              numeric,
    suppressed                   boolean NOT NULL,
    licence                      text NOT NULL,
    attribution                  text NOT NULL,
    document                     text NOT NULL,       -- the file's sha256
    page                         text NOT NULL,       -- the sheet
    place                        text NOT NULL,       -- the row's first cell
    read_from                    text NOT NULL,
    reader                       text NOT NULL,
    profile                      text NOT NULL,
    profile_version              integer NOT NULL
);
-- the check's sums join each level to the one below
CREATE INDEX ON contract_disclosures.costs (document, financial_year, level, region, territorial_authority);

-- the ledger: one row per file read
CREATE TABLE contract_disclosures.read_files (
    document      text PRIMARY KEY,
    package       text NOT NULL,
    profile       text NOT NULL,
    data_rows     integer NOT NULL,
    cells_read    integer NOT NULL,
    set_aside     integer NOT NULL,
    reference     text,
    period        text,
    extracted_on  date
);

-- the reading's catch log
CREATE TABLE contract_disclosures.read_set_aside (
    document  text NOT NULL,
    place     text NOT NULL,
    stage     text NOT NULL,
    reason    text NOT NULL
);
