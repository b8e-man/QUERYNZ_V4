-- registers/charities_a: the tables this build owns, in `charities_a` (plan step 4.1: the Fable build of the
-- charities reading; the build kept moves to `charities`). Loaded into a staging or scratch schema by replacing
-- `charities_a.` with that schema's name (load.sql; in the shared sample schema the tables carry the prefix
-- `charities_a_`). Every row comes from one page of the register's feed, landed verbatim by the capture lane
-- (`registers/charities`): `document` is the page's sha256, `place` the row's key field and value in it.
-- No table here holds an officer's address, birth date or contact detail: the feed carries none. There is no
-- `charities_a_private` table: nothing read needs one.

-- one row per organisation on the register, keyed by its charity number (the register's own)
CREATE TABLE IF NOT EXISTS charities_a.charities (
    key                      text PRIMARY KEY,              -- charities/CC12345
    charity_number           text NOT NULL,                 -- CC12345
    organisation_id          bigint NOT NULL,               -- the feed's OrganisationId
    nzbn                     text,                          -- as filed, when it checks as an NZBN
    nzbn_filed               text,                          -- as filed
    companies_office_number  text,
    name                     text NOT NULL,
    other_names              text,
    status                   text,                          -- as filed: Registered | Deregistered | Removed ...
    registered_on            date,
    deregistered_on          date,
    deregistration_reason    text,                          -- the coded reason, as the vOrganisations page names it
    deregistration_note      text,                          -- the free text, as filed
    legal_structure          text,                          -- as filed (the code list's names)
    legal_structure_other    text,
    entity_structure         text,
    main_activity_id         integer,
    main_activity            text,                          -- resolved through the MainActivity list
    main_sector_id           integer,
    main_sector              text,
    main_beneficiary_id      integer,
    main_beneficiary         text,
    activities               text,                          -- the register's list beside the organisation, as published
    sectors                  text,
    beneficiaries            text,
    areas_of_operation       text,
    sources_of_funds         text,
    charitable_purpose       text,
    address_for_service      text,                          -- the organisation's, as the register publishes it (like a registered office)
    postal_address           text,
    year_end_day             integer,
    year_end_month           integer,
    annual_return_due_on     date,
    group_id                 bigint,
    group_key                text,                          -- charities/group/<GroupId>
    group_name               text,
    group_type               integer,
    incorporated             boolean,
    percent_spent_overseas   integer,
    modified_at              timestamptz,                   -- the feed's ModifiedOn
    lists_document           text CHECK (lists_document ~ '^[0-9a-f]{64}$'),   -- the vOrganisations page the lists came from
    document                 text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                     integer NOT NULL DEFAULT 1,
    place                    text NOT NULL,
    read_from                text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader                   text NOT NULL,
    profile                  text NOT NULL,
    profile_version          integer NOT NULL,
    loaded_at                timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS charities_a_charities_org ON charities_a.charities (organisation_id);

-- one row per officer row of the feed, keyed by its OfficerId (the source's own officer identifier). The window is
-- the register's own appointment and last day; never a load day. No address, birth date or contact detail
CREATE TABLE IF NOT EXISTS charities_a.charity_officers (
    key                 text PRIMARY KEY,                   -- charities/officer/<OfficerId>
    officer_id          bigint NOT NULL,
    charity_key         text NOT NULL,
    charity_number      text NOT NULL,
    organisation_id     bigint NOT NULL,
    contact_id          text,                               -- the feed's ContactId, as filed
    first_name          text,
    middle_names        text,
    last_name           text,
    full_name           text NOT NULL,
    body_corporate      boolean NOT NULL DEFAULT false,
    body_corporate_name text,
    name_note           text,                               -- a name field withheld, and why (a date, an address, digits typed into it)
    role                text,                               -- PositioninOrganisation, as filed
    status              text,                               -- OfficerStatus, as filed
    started_on          date,                               -- PositionAppointmentDate
    ended_on            date,                               -- LastDateAsAnOfficer, as the register states it
    ended_on_stated     boolean NOT NULL DEFAULT false,
    disqualified        boolean NOT NULL DEFAULT false,
    disqualification    text,                               -- the grounds the feed flags, by the feed's own names
    appointed_officer   boolean NOT NULL DEFAULT false,
    suppressed          boolean NOT NULL DEFAULT false,
    modified_at         timestamptz,
    document            text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                integer NOT NULL DEFAULT 1,
    place               text NOT NULL,
    read_from           text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader              text NOT NULL,
    profile             text NOT NULL,
    profile_version     integer NOT NULL,
    loaded_at           timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS charities_a_officers_charity ON charities_a.charity_officers (charity_key);

-- one row per annual return, keyed by its AnnualReturnId: the period, tier, currency, audit, and the financial
-- fields (ruling of 14 August 2026). The headline figures take columns; every other numeric field the feed carries,
-- when not null and not zero, is in `figures` under the feed's own name
CREATE TABLE IF NOT EXISTS charities_a.charity_returns (
    key                     text PRIMARY KEY,               -- charities/return/<AnnualReturnId>
    annual_return_id        bigint NOT NULL,
    charity_key             text,                           -- NULL for a group's return
    charity_number          text,
    organisation_id         bigint,
    group_key               text,
    group_id                bigint,
    period_ended_on         date NOT NULL,                  -- YearEnded
    as_at_on                date,
    covers_months           integer,
    status_code             integer,                        -- the feed's Status, as filed
    tier_id                 integer,
    tier                    text,                           -- resolved through the ReportingTier list
    currency                text,                           -- as filed
    audited                 boolean,
    audit_opinion_modified  boolean,
    audit_opinion           text,                           -- the feed's name for the modified opinion
    accounting_method_flag  boolean,                        -- the feed's AccountingMethod, as filed (its meaning is not stated)
    withheld                boolean NOT NULL DEFAULT false,
    first_time_reporting    boolean,
    gst_inclusive           boolean,
    total_gross_income numeric, total_expenditure numeric, net_surplus_deficit numeric, surplus_deficit numeric,
    total_assets numeric, total_liabilities numeric, total_equity numeric, total_assets_less_liabilities numeric,
    total_overall_liabilities numeric, current_assets numeric, non_current_assets numeric, current_liabilities numeric,
    non_current_liabilities numeric, cash_and_bank numeric, investments numeric, inventory numeric, land numeric,
    buildings numeric, land_and_buildings numeric, property_plant_equipment numeric, other_fixed_assets numeric,
    computers_and_office_equipment numeric, vehicles numeric, intangible_assets numeric, investment_property numeric,
    investments_shares_bonds_funds numeric, loans_and_borrowings numeric, amounts_borrowed numeric, amounts_loaned numeric,
    general_accumulated_funds numeric, restricted_purpose_funds numeric, endowment_funds numeric, reserves numeric,
    accumulated_surplus numeric, donations_koha numeric, bequests numeric, membership_fees numeric,
    government_grants_contracts numeric, government_service_delivery_grants numeric, non_government_service_delivery_grants numeric,
    service_delivery_grants numeric, general_grants_received numeric, capital_grants_and_donations numeric,
    other_grants_and_sponsorship numeric, grants_from_government numeric, grants_from_other_sources numeric,
    service_trading_income numeric, commercial_revenue numeric, other_exchange_revenue numeric, other_non_exchange_revenue numeric,
    interest_or_dividends numeric, other_investment_income numeric, new_zealand_dividends numeric, all_other_income numeric,
    grants_paid_within_nz numeric, grants_paid_outside_nz numeric, grants_or_donations_paid numeric, grants_and_donations_made numeric,
    salaries_and_wages numeric, employee_remuneration numeric, volunteer_expenses numeric, fundraising_expenses numeric,
    expenses_related_to_fundraising numeric, cost_of_trading numeric, commercial_expenses numeric, cost_of_service_provision numeric,
    other_service_delivery_expenses numeric, other_objective_delivery_expenses numeric, depreciation numeric, interest_paid numeric,
    all_other_expenditure numeric, total_operating_expenditure numeric, total_comprehensive_revenue_and_expense numeric,
    total_resources numeric, total_commitments numeric, total_resources_less_commitments numeric, guarantees numeric,
    fulltime_employees numeric, parttime_employees numeric, paid_hours_per_week numeric, volunteers_per_week numeric,
    volunteer_hours_per_week numeric,
    figures                 jsonb,                          -- every other non-null, non-zero numeric field, as filed
    modified_at             timestamptz,
    document                text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                    integer NOT NULL DEFAULT 1,
    place                   text NOT NULL,
    read_from               text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader                  text NOT NULL,
    profile                 text NOT NULL,
    profile_version         integer NOT NULL,
    loaded_at               timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS charities_a_returns_charity ON charities_a.charity_returns (charity_key);

-- one row per group (a parent entity reporting for its members), keyed by GroupId
CREATE TABLE IF NOT EXISTS charities_a.charity_groups (
    key                   text PRIMARY KEY,                 -- charities/group/<GroupId>
    group_id              bigint NOT NULL,
    registration_number   text,                             -- the group's own CC number
    name                  text NOT NULL,
    other_names           text,
    group_type            integer,
    status                text,
    registered_on         date,
    deregistered_on       date,
    deregistration_note   text,
    main_activity         text,
    main_sector           text,
    main_beneficiary      text,
    address_for_service   text,
    postal_address        text,
    modified_at           timestamptz,
    document              text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                  integer NOT NULL DEFAULT 1,
    place                 text NOT NULL,
    read_from             text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader                text NOT NULL,
    profile               text NOT NULL,
    profile_version       integer NOT NULL,
    loaded_at             timestamptz NOT NULL
);

-- the code lists as the feed publishes them
CREATE TABLE IF NOT EXISTS charities_a.codes (
    list        text NOT NULL,
    id          integer NOT NULL,
    name        text NOT NULL,
    entity_name text NOT NULL DEFAULT '',                  -- the set a code applies to, where the list says (Groups | Organisations)
    attribute   text,
    document    text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (list, id, entity_name, document)
);

-- every page the load read, and what it did with its rows: rows = typed + set_aside (+ filtered, in a sample)
CREATE TABLE IF NOT EXISTS charities_a.files (
    document    text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    entity_set  text NOT NULL,
    url         text NOT NULL,
    rows        integer NOT NULL,
    typed       integer NOT NULL,
    set_aside   integer NOT NULL,
    filtered    integer NOT NULL DEFAULT 0,
    stated      integer,                                    -- the feed's own count, on the first page of a pass
    ordinal     integer NOT NULL,                           -- the order read: a later page's row replaces an earlier one
    PRIMARY KEY (document, entity_set)
);

-- the catch log: one line for every row the reading could not take to a typed row, with the stage and the reason
CREATE TABLE IF NOT EXISTS charities_a.set_aside (
    item       text NOT NULL,                               -- <page sha>/<key field>=<key>
    stage      text NOT NULL,                               -- the entity set, or `load`
    reason     text NOT NULL,
    count      integer NOT NULL DEFAULT 1,
    at         timestamptz NOT NULL DEFAULT now()
);

-- the run record of each load: which passes it read, the counts, how long it took
CREATE TABLE IF NOT EXISTS charities_a.runs (
    run_id      bigserial PRIMARY KEY,
    signature   text NOT NULL,                              -- sha256 of the ordered page hashes read
    passes      text NOT NULL,                              -- the capture pass ids read, by set
    counts      jsonb NOT NULL,
    seconds     numeric NOT NULL,
    loaded_at   timestamptz NOT NULL
);
