-- registers/tenders: every table the lane owns (contract: the lane). Two parts. The capture's record comes first and
-- is never wiped: the runs, the listing of every file held (`capture_files`) and its catch log. The reading's tables
-- follow the marker line below; load.py drops and makes them again at every load, inside one transaction. No table
-- here, and none in `tenders_private`, holds an address: the supplier file's `Full Address` column is never read
-- (hard limit 15), so the private twin is empty and made only so the lane has the contract's shape.

CREATE SCHEMA IF NOT EXISTS tenders;
CREATE SCHEMA IF NOT EXISTS tenders_private;

-- one run of the capture: `copy` (the old estate's raw files, by hash) or `refresh` (the ministry's files through the
-- fetch gate)
CREATE TABLE IF NOT EXISTS tenders.capture_runs (
    run_id      bigserial PRIMARY KEY,
    mode        text NOT NULL CHECK (mode IN ('copy', 'refresh')),
    started_at  timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    requests    integer NOT NULL DEFAULT 0,
    landed      integer NOT NULL DEFAULT 0,
    set_aside   integer NOT NULL DEFAULT 0,
    stopped     text
);

-- the listing: one line per file a run holds. `set_name` and `era` are the publisher's, from the file's name
-- (`-historic` is the July 2014 to June 2019 file); `how` says which case of plan 1.10 brought it
CREATE TABLE IF NOT EXISTS tenders.capture_files (
    file_id     bigserial PRIMARY KEY,
    run_id      bigint NOT NULL REFERENCES tenders.capture_runs (run_id),
    name        text NOT NULL,
    url         text,
    sha256      text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    size        bigint NOT NULL,
    role        text NOT NULL CHECK (role IN ('data', 'dictionary', 'catalogue')),
    set_name    text CHECK (set_name IN ('notices', 'suppliers', 'regions', 'categories')),
    era         text CHECK (era IN ('historic', 'current')),
    how         text NOT NULL CHECK (how IN ('old-raw', 'fetched')),
    held_from   text NOT NULL,
    acquired_at timestamptz NOT NULL,
    new         boolean NOT NULL,
    landed_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS tenders_capture_files_set ON tenders.capture_files (set_name, era, run_id);

-- the capture's catch log: a failed read, a block, a file no profile recognises
CREATE TABLE IF NOT EXISTS tenders.capture_set_aside (
    run_id  bigint REFERENCES tenders.capture_runs (run_id),
    item    text NOT NULL,
    stage   text NOT NULL,
    reason  text NOT NULL,
    at      timestamptz NOT NULL DEFAULT now()
);

-- ── the reading: rebuilt from the listed files at every load (load.py)

-- one per award notice: a row of a notices file. The key is the notice's own identifier (GETS's RFx ID) within its
-- file's era: eleven RFx IDs appear in both files with different dates, and each row is a notice as published
CREATE TABLE tenders.notices (
    key                       text PRIMARY KEY,
    rfx_id                    text NOT NULL,
    era                       text NOT NULL,
    posting_agency            text,
    department                text,
    rfx_type                  text,
    competition_type          text,
    tender_coverage           text,
    prequalification_required text,
    title                     text,
    reference_number          text,
    opened_on                 date,
    closed_on                 date,
    awarded_on                date,
    award_type                text,
    awarded_amount_as_published text,
    value_nzd                 numeric,
    value_note                text NOT NULL,
    regions                   text[] NOT NULL DEFAULT '{}',
    categories                jsonb NOT NULL DEFAULT '[]',
    suppliers_named           integer NOT NULL DEFAULT 0,
    report_date               date,
    document                  text NOT NULL,
    page                      integer NOT NULL,
    place                     text NOT NULL,
    read_from                 text NOT NULL,
    reader                    text NOT NULL,
    profile                   text NOT NULL,
    profile_version           integer NOT NULL,
    loaded_at                 timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX tenders_notices_rfx ON tenders.notices (rfx_id);

-- one per supplier a supplier file names on a notice: the name as published, the file's business-number field as
-- published, and the NZBN only where that field is a valid 13-digit one. No address, no website (hard limit 15:
-- a sole trader's name is kept and nothing finer)
CREATE TABLE tenders.suppliers (
    key                 text PRIMARY KEY,
    notice_key          text NOT NULL,
    rfx_id              text NOT NULL,
    era                 text NOT NULL,
    business_name       text,
    nzbn_as_published   text,
    nzbn                text,
    nzbn_form           text NOT NULL,
    country             text,
    report_date         date,
    document            text NOT NULL,
    page                integer NOT NULL,
    place               text NOT NULL,
    read_from           text NOT NULL,
    reader              text NOT NULL,
    profile             text NOT NULL,
    profile_version     integer NOT NULL,
    loaded_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX tenders_suppliers_notice ON tenders.suppliers (notice_key);

-- the ledger: every listed file read, its records, and how many became rows or catch-log lines
CREATE TABLE tenders.read_files (
    document   text NOT NULL,
    set_name   text NOT NULL,
    era        text NOT NULL,
    profile    text,
    records    integer NOT NULL,
    typed      integer NOT NULL,
    set_aside  integer NOT NULL,
    skipped    integer NOT NULL,
    report_date date
);

-- the reading's catch log: one line per record it could not make a row of, with the stage and the reason
CREATE TABLE tenders.read_set_aside (
    set_name  text NOT NULL,
    era       text NOT NULL,
    document  text NOT NULL,
    place     text NOT NULL,
    stage     text NOT NULL,
    reason    text NOT NULL
);

-- counted notes about rows that were kept (a date that is not a real day, a field read as Windows-1252)
CREATE TABLE tenders.read_notes (
    note   text NOT NULL,
    count  integer NOT NULL
);
