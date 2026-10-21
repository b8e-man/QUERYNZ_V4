-- registers/charities_b: the tables of the Opus build of the charities reading (plan step 4.1). Built under a
-- session's scratch schema or a staging schema (load.sql rewrites `charities_b.`); the build kept moves into
-- `charities`. Every row is a typed row of one feed row, or a line of the catch log; rows are rebuilt from the
-- pages, never edited. No table holds an address but a charity's own address for service, and no officer's
-- address, birth date, email or phone: the feed's Officers carry no address or birth date, and nothing else
-- is read. So the private twin holds nothing.

-- one row per page read: the reconciliation's ledger (rows in = typed + set aside, page by page)
CREATE TABLE charities_b.pages (
    document     text PRIMARY KEY CHECK (document ~ '^[0-9a-f]{64}$'),
    entity_set   text NOT NULL,
    rows         integer NOT NULL,                  -- rows on the page
    typed        integer NOT NULL,                  -- rows read into a table
    set_aside    integer NOT NULL,                  -- rows in the catch log, superseded ones included
    skipped      integer NOT NULL DEFAULT 0         -- rows a sample fill passed over (always 0 on a full load)
);

-- the code lists' entries, as read: what every resolved name on the tables below came from
CREATE TABLE charities_b.codes (
    code_list  text NOT NULL,                       -- RegistrationStatus, MainSector, ReportingTier, ...
    entity     text NOT NULL DEFAULT '',            -- the list's EntityName (Groups, Organisations, ...), '' where none
    code       integer,
    name       text NOT NULL,
    document   text NOT NULL
);

-- the group registrations (a group files returns for its members)
CREATE TABLE charities_b.groups (
    key              text PRIMARY KEY,              -- charities/<the group's own register number>
    number           text NOT NULL,
    group_id         integer NOT NULL UNIQUE,       -- the feed's GroupId
    name             text,
    status           text,
    registered_on    date,
    deregistered_on  date,
    source_modified_at timestamptz,                 -- the register's own ModifiedOn; never a date of anything
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL,
    reader text NOT NULL, profile text NOT NULL, profile_version integer NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE charities_b.charities (
    key                    text PRIMARY KEY,        -- charities/CC12345: the register's own number, as filed
    number                 text NOT NULL UNIQUE,
    organisation_id        integer NOT NULL UNIQUE, -- the feed's OrganisationId
    name                   text,
    other_names            text,
    status                 text,                    -- Registered, Deregistered, Removed, ... (code list RegistrationStatus)
    registered_on          date,
    deregistered_on        date,
    deregistration_reason  text,
    legal_structure        text,                    -- code list LegalStructure
    legal_structure_other  text,
    charitable_purpose     text,
    main_sector_id         integer, main_sector      text,   -- resolved through MainSector
    main_activity_id       integer, main_activity    text,   -- MainActivity
    main_beneficiary_id    integer, main_beneficiary text,   -- MainBeneficiary
    address_for_service    text,                    -- the register's street address for the charity, as published
    group_key              text,
    group_number           text,
    group_name             text,
    group_type             integer,                 -- the feed's GroupType code, as filed
    nzbn                   text,
    incorporation_number   text,                    -- the feed's CompaniesOfficeNumber, as filed
    year_end_month         integer,
    year_end_day           integer,
    annual_return_due_on   date,
    source_modified_at     timestamptz,
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL,
    reader text NOT NULL, profile text NOT NULL, profile_version integer NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE charities_b.officers (
    key                       text PRIMARY KEY,     -- charities/officers/<OfficerId>
    officer_id                integer NOT NULL UNIQUE,
    charity_key               text NOT NULL,
    organisation_id           integer NOT NULL,
    kind                      text NOT NULL CHECK (kind IN ('person', 'body corporate')),
    full_name                 text NOT NULL,
    first_name                text,
    middle_name               text,
    last_name                 text,
    role                      text,                 -- PositioninOrganisation, as filed
    started_on                date,                 -- PositionAppointmentDate
    ended_on                  date,                 -- LastDateAsAnOfficer: the register's own day, never a load day
    ended_on_stated           boolean NOT NULL,
    status                    text,                 -- code list OfficerStatus: Qualified, Past, Disqualified, ...
    disqualified              boolean NOT NULL,     -- the register's status says Disqualified or Removed as Disqualified
    declared_not_disqualified boolean,              -- the feed's IsNotDisqualified, as filed
    source_modified_at        timestamptz,
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL,
    reader text NOT NULL, profile text NOT NULL, profile_version integer NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX charities_b_officers_charity ON charities_b.officers (charity_key);

CREATE TABLE charities_b.returns (
    key                text PRIMARY KEY,            -- charities/returns/<AnnualReturnId>
    return_id          integer NOT NULL UNIQUE,
    charity_key        text,                        -- the organisation that filed it, or
    group_key          text,                        -- the group (a return may name both)
    organisation_id    integer,
    group_id           integer,
    period_end         date,                        -- YearEnded
    months_covered     integer,                     -- PerformanceReportCovers, where filed
    began_on           date,                        -- DateEntityBegan, where filed
    tier_id            integer,
    tier               text,                        -- code list ReportingTier
    currency           text,                        -- code list ReportingCurrency; empty where the return names none
    audited            boolean,                     -- IsFinancialReportAudited
    modified_opinion   boolean,                     -- IsModifiedAuditOpinionReceived
    opinion            text,                        -- code list AuditModifiedOpinionReceived
    status_code        integer,                     -- the feed's Status, as filed
    total_gross_income numeric, total_expenditure numeric, net_surplus numeric,
    total_assets       numeric, total_liabilities numeric, total_equity numeric,
    figures            jsonb NOT NULL,              -- every financial field the return files: feed name → number
    material_expenses  jsonb,                       -- [{label, amount}]
    source_modified_at timestamptz,
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL,
    reader text NOT NULL, profile text NOT NULL, profile_version integer NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    CHECK (charity_key IS NOT NULL OR group_key IS NOT NULL)
);
CREATE INDEX charities_b_returns_charity ON charities_b.returns (charity_key);

-- the catch log: one line for every feed row not read into a table, with the stage and the reason
CREATE TABLE charities_b.set_aside (
    entity_set  text NOT NULL,
    document    text NOT NULL,
    place       text NOT NULL,                     -- the row's key in the page
    stage       text NOT NULL,                     -- read | key | link | supersede
    reason      text NOT NULL
);

-- what was kept but could not be resolved, counted (an unknown code, a dropped address part)
CREATE TABLE charities_b.notes (
    note   text PRIMARY KEY,
    count  integer NOT NULL
);
